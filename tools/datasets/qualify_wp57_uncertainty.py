# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Real-kernel remaining source attribution plus model-aware station uncertainty."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import sha256
from attribute_jpl_source_models import evaluate, norm, stats
from verify_horizons_fixtures import validate as verify_wp51
from wp57_source import DEFAULT_ROOT, REMAINING, WP56_REPORT, load_spec, verify, verify_offsets
from wp57_uncertainty import (
    refine_stations,
    sensitivity_seconds,
    separate_offset_context,
    signed_rate,
    uncertainty_register,
)


def qualify(root: Path, base: Path, centres: Path, output: Path) -> dict[str, Any]:
    proof, sources = verify(root)
    offset_proof, direct_offsets = verify_offsets(root)
    proof.update(offset_proof)
    spec = load_spec(root)
    if verify_wp51(Path("data/fixtures/horizons"))["fixture_rows_verified"] != 300:
        raise ValueError("Original WP5.1 source unverified")
    original_path = Path("docs/validation/wp5-2-horizons-comparison.json")
    original = json.loads(original_path.read_text())
    components = json.loads((root / "components.json").read_text())
    previous = json.loads(WP56_REPORT.read_text())
    # Complete source-only refinement BEFORE opening any Aria calculation engine.
    stations = refine_stations(spec, sources, previous)
    manifest = centres_manifest()
    if manifest["base_sha256"] != original["engine_base_sha256"]:
        raise ValueError("Wrong planetary base for frozen discrepancy reconstruction")
    with Ephemeris(
        base, centre_kernels={b: centres / r["filename"] for b, r in manifest["sources"].items()}
    ) as engine:
        attribution = evaluate(engine, original, components, REMAINING)
        attribution["report_id"] = "aria-four-remaining-source-attribution-v1"
        for sample in attribution["samples"]:
            # The shared helper historically uses _km suffixes for both vector
            # families. New evidence explicitly corrects velocity labels/units.
            v = sample["model_component_velocity_km_s"]
            sample["model_component_velocity_km_s"] = {
                k + "_s" if k.endswith("_km") else k: value for k, value in v.items()
            }
            if any(
                v[k] > 1e-10
                for k in (
                    "total_reconstruction_error_km",
                    "parent_reconstruction_error_km",
                    "centre_reconstruction_error_km",
                )
            ):
                raise ValueError("Velocity component closure exceeds 1e-10 km/s")
        previous_vectors = {
            (r["body"], r["metrics"]["jd_tdb"]): r["metrics"]
            for r in original["rows"]
            if r["kind"] == "geometric"
        }
        parents = {
            (r["body"], r["jd_tdb"]): r for r in components["cases"] if r["role"] == "parent_geo"
        }
        for sample in attribution["samples"]:
            key = sample["body"], sample["jd_tdb"]
            original_vector = previous_vectors[key]
            parent = parents[key]
            direct = direct_offsets[key]
            position = separate_offset_context(
                sample["model_component_position"],
                original_vector["reference_position_km"],
                parent["position_km"],
                direct["position_km"],
            )
            velocity = separate_offset_context(
                sample["model_component_velocity_km_s"],
                original_vector["reference_velocity_km_s"],
                parent["velocity_km_s"],
                direct["velocity_km_s"],
            )
            if position["reconstruction_error"] > 2e-4 or velocity["reconstruction_error"] > 1e-10:
                raise ValueError("Direct-offset/context vector decomposition failed closure")
            sample["direct_offset_attribution"] = dict(
                position_km=position,
                velocity_km_s=velocity,
                direct_source_sha256=direct["raw_sha256"],
            )
        for body, metrics in attribution["per_body"].items():
            selected = [
                r["direct_offset_attribution"] for r in attribution["samples"] if r["body"] == body
            ]
            for name in ("direct_physical_offset_difference", "reference_chain_offset_mixing"):
                metrics[name + "_km"] = stats([norm(r["position_km"][name]) for r in selected])
                metrics[name + "_velocity_m_s"] = stats(
                    [norm(r["velocity_km_s"][name]) * 1000 for r in selected]
                )
        attribution["direct_offset_interpretation"] = (
            "Total = parent geocentric difference + direct physical-offset difference - reference-chain offset mixing; component maxima are not additive uncertainty bounds"
        )
        for case, row in zip(spec["station_centres"], stations, strict=True):
            t = case["jd_tt"]
            rates = {}
            for h in spec["aria_derivative_steps_days"]:
                points = [TimeInput(jd=(t + k * h, 0), scale="TT") for k in (-2, -1, 0, 1, 2)]
                positions = engine.positions_batch(
                    PositionRequest(points[2], bodies=(case["body"],), profile="planet-centres-v1"),
                    points,
                )
                if any(
                    p.bodies[0].target_id != manifest["sources"][case["body"]]["target_id"]
                    for p in positions
                ):
                    raise ValueError("Wrong physical target in numerical rate sensitivity")
                rates[str(h)] = signed_rate([p.bodies[0].longitude_deg for p in positions], h)
            row["aria_recomputed_rates_deg_tt_day"] = rates
            row["aria_derivative_step_spread_deg_tt_day"] = max(rates.values()) - min(
                rates.values()
            )
            row["aria_derivative_spread_timing_proxy_seconds"] = (
                sensitivity_seconds(
                    row["aria_derivative_step_spread_deg_tt_day"],
                    row["equation_acceleration_deg_tt_day2"],
                )
                if row["equation_acceleration_deg_tt_day2"] is not None
                else None
            )
            delta = rates["0.001"] - row["source_rates_deg_tt_day"]["0.03125"]
            row["aria_minus_jpl_rate_deg_tt_day"] = delta
            row["model_plus_stencil_time_proxy_seconds"] = (
                sensitivity_seconds(delta, row["equation_acceleration_deg_tt_day2"])
                if row["equation_acceleration_deg_tt_day2"] is not None
                else None
            )
    per_body = {}
    for body in manifest["sources"]:
        selected = [r for r in stations if r["body"] == body]
        residuals = [
            abs(m["actual_minus_reference_seconds"])
            for r in selected
            for m in r["aria_comparison"]["matches"]
        ]
        per_body[body] = dict(
            station_count=len(selected),
            resolved=sum(r["reference_resolved"] for r in selected),
            aria_vs_refined_jpl_seconds=stats(residuals) if residuals else None,
            max_aria_derivative_step_spread_deg_tt_day=max(
                r["aria_derivative_step_spread_deg_tt_day"] for r in selected
            ),
            absolute_physical_time_uncertainty_seconds=None,
        )
    matches = [m for row in stations for m in row["aria_comparison"]["matches"]]
    old_failure_ids = [
        r["workload"]["id"] for r in previous["records"] if not r["reference_resolved"]
    ]
    if len(old_failure_ids) != 6 or previous["passed"] is not False:
        raise ValueError("Original 009 reference failures must remain preserved")
    result = dict(
        schema_version=1,
        report_id="aria-model-uncertainty-qualification-v1",
        reference_interpolant="C2 not-a-knot cubic spline; continuous first/second derivatives",
        initial_local_cubic_diagnostic_sha256=sha256(
            Path("docs/validation/wp57-initial-local-cubic-diagnostic.json").read_bytes()
        ),
        source_integrity=proof,
        original_wp52_sha256=sha256(original_path.read_bytes()),
        original_wp56_sha256=sha256(WP56_REPORT.read_bytes()),
        numerical_conventions=dict(
            vectors="geometric ICRF TDB km and km/s",
            stations="geocentric airless apparent tropical true-ecliptic/equinox of date, TT",
            profile="planet-centres-v1",
            shared_standard="ERFA IAU 2006/2000A",
        ),
        kernel_manifest=manifest,
        source_attribution=attribution,
        station_refinement=stations,
        station_per_body=per_body,
        original_wp56_failed_reference_workloads=old_failure_ids,
        original_wp56_passed=False,
        refined_station_count=len(stations),
        resolved_station_count=sum(r["reference_resolved"] for r in stations),
        matched_station_count=len(matches),
        station_timing_difference_seconds=stats(
            [abs(m["actual_minus_reference_seconds"]) for m in matches]
        )
        if matches
        else None,
        uncertainty_register=uncertainty_register(),
        passed=len(attribution["samples"]) == 100
        and len(stations) == 36
        and all(r["passed"] for r in stations),
        absolute_physical_uncertainty_bound=None,
        absolute_accuracy_certified=False,
        commercial_release_qualified=False,
        continuous_completeness_proven=False,
        model_default_changed=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k
                not in (
                    "source_attribution",
                    "station_refinement",
                    "kernel_manifest",
                    "uncertainty_register",
                )
            },
            indent=2,
        ),
        flush=True,
    )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--centres-dir", type=Path, required=True)
    p.add_argument(
        "--output", type=Path, default=Path("docs/validation/wp57-model-uncertainty.json")
    )
    args = p.parse_args()
    result = qualify(args.source, args.base, args.centres_dir, args.output)
    raise SystemExit(0 if result["passed"] else 1)
