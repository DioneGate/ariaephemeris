# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""WP5.5 compare exact Aria event searches to JPL-only tabulated event roots.

Each reference root derives solely from independent JPL Horizons airless
apparent ICRF RA/Dec at TT, transformed to true tropical ecliptic of date.
No Aria expected longitude, rate or event time enters the JPL interpolation.
Aria nominates selection windows only; the JPL root bracket is observed from
nine independently measured event residuals. An interpolated root is not a
rigorous root-time uncertainty certificate or an event completeness proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, EventRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_wp54_tropical import reference_rate, true_tropical_from_icrf
from verify_wp55_events import validate as validate_wp55
from wp55_event_math import (
    CANDIDATE_TIMING_SECONDS,
    SECONDS_PER_DAY,
    locate_reference_root,
    signed_angle,
)


def distribution(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("Nonfinite or missing event-time residual")
    ordered = sorted(values)
    n = len(ordered)
    at = 0.95 * (n - 1)
    p = int(at)
    return {
        "count": n,
        "max": ordered[-1],
        "rms": math.sqrt(sum(x * x for x in ordered) / n),
        "p95": ordered[p] + (ordered[min(p + 1, n - 1)] - ordered[p]) * (at - p),
    }


def reference_function(
    event: dict[str, Any],
    sources: dict[tuple[str, float], tuple[float, float]],
) -> tuple[list[float], list[dict[str, Any]]]:
    """Return original-source chart event residuals; no Aria position evaluation."""
    values: list[float] = []
    records: list[dict[str, Any]] = []
    for i, jd in enumerate(event["jd_tt_grid"]):
        body = event["body"]
        kind = event["kind"]
        if kind == "station":
            stencil = event["reference_rate_stencils"][i]
            reference_values = [true_tropical_from_icrf(*sources[(body, t)], t) for t in stencil]
            rate = reference_rate(reference_values)
            value = rate
            memo = {
                "independent_rate_deg_tt_day": rate,
                "rate_stencil_tt": stencil,
            }
        else:
            lon, lat = true_tropical_from_icrf(*sources[(body, jd)], jd)
            if kind in ("conjunction", "opposition"):
                other_lon, other_lat = true_tropical_from_icrf(
                    *sources[(event["other_body"], jd)], jd
                )
                phase = signed_angle(lon, other_lon)
                value = signed_angle(phase, event["goal_deg"])
                memo = {
                    "longitude_a_deg": lon,
                    "longitude_b_deg": other_lon,
                    "ecliptic_latitude_a_deg": lat,
                    "ecliptic_latitude_b_deg": other_lat,
                    "pair_phase_residual_deg": value,
                }
            elif kind == "ingress":
                value = signed_angle(lon, event["goal_deg"])
                memo = {
                    "independent_longitude_deg": lon,
                    "independent_latitude_deg": lat,
                    "cusp_residual_deg": value,
                }
            else:
                raise ValueError("Unknown planetary event kind")
        if not math.isfinite(value):
            raise ValueError("Nonfinite independent JPL event equation")
        values.append(value)
        records.append({"jd_tt": jd, "event_equation": value, "reference": memo})
    return values, records


def compare(engine: Ephemeris, originals: dict[str, Any], original_sha256: str) -> dict[str, Any]:
    source_map = {
        (row["body"], row["jd_tt"]): (
            row["inertial_apparent_ra_deg"],
            row["inertial_apparent_dec_deg"],
        )
        for row in originals["rays"]
    }
    if len(originals["cases"]) != 22 or len(source_map) != originals["ray_count"]:
        raise ValueError("Missing archived independent celestial source data")
    records = []
    for case in originals["cases"]:
        values, original_values = reference_function(case, source_map)
        independent = locate_reference_root(case["jd_tt_grid"], values)
        # Search around the independently selected stress window using the
        # existing product API, never by rewriting the event implementation.
        start = case["nominated_jd_tt"] - 0.25
        stop = case["nominated_jd_tt"] + 0.25
        request = EventRequest(
            start=TimeInput(jd=(start, 0.0), scale="TT"),
            end=TimeInput(jd=(stop, 0.0), scale="TT"),
            kind=case["kind"],
            body=case["body"],
            other_body=case["other_body"],
            tolerance_seconds=0.1,
            max_step_days=0.25,
            max_evaluations=10000,
            profile="planet-centres-v1",
            strict=True,
        )
        aria_events = engine.find_events(request)
        candidates = [
            {
                "jd_tt": sum(result.jd_tt),
                "condition": result.conditioning,
                "time_bracket_seconds": result.time_bracket_seconds,
                "timing_qualified": result.metadata["timing_qualified"],
                "event_direction": result.metadata["event_direction"],
            }
            for result in aria_events
        ]
        candidate = (
            min(candidates, key=lambda x: abs(x["jd_tt"] - independent["jd_tt"]))
            if candidates
            else None
        )
        residual_s = (
            (candidate["jd_tt"] - independent["jd_tt"]) * SECONDS_PER_DAY
            if candidate is not None
            else None
        )
        slope = abs(independent["local_signed_slope_per_tt_day"])
        # Diagnostic, NOT an error bound. 0.05 arcsec for angular events and
        # 0.0001 deg/day for a station are candidate comparative envelopes.
        product_error_proxy_s = (
            (0.0001 if case["kind"] == "station" else 0.05 / 3600.0) / slope * SECONDS_PER_DAY
            if slope > 1e-12
            else None
        )
        records.append(
            {
                "event_id": case["event_id"],
                "kind": case["kind"],
                "body": case["body"],
                "other_body": case["other_body"],
                "goal_deg": case["goal_deg"],
                "nominated_jd_tt": case["nominated_jd_tt"],
                "selection": {
                    "nomination_method": case["nomination_method"],
                    "nomination_window_jd_tt": case["nomination_window_jd_tt"],
                    "blind_independent_discovery": False,
                },
                "jpl_reference": independent,
                "jpl_sampled_equation": original_values,
                "aria_events_in_half_day": candidates,
                "aria_nearest_event": candidate,
                "aria_minus_independently_interpolated_jpl_seconds": residual_s,
                "candidate_60_seconds_exceeded": (
                    abs(residual_s) > CANDIDATE_TIMING_SECONDS if residual_s is not None else None
                ),
                "conditioning": {
                    "jpl_equation_slope_abs_per_tt_day": slope,
                    "max_position_or_rate_difference_time_proxy_seconds": product_error_proxy_s,
                    "proxy_is_not_certified_error_bound": True,
                    "source_model_uncertainty_unresolved": True,
                    "interpolation_is_not_certified_exact_event_time": True,
                },
            }
        )
    if len(records) != 22 or len({r["event_id"] for r in records}) != 22:
        raise ValueError("Incomplete independent event-root comparison")
    per_kind: dict[str, Any] = {}
    for kind in ("station", "ingress", "conjunction", "opposition"):
        selected = [r for r in records if r["kind"] == kind]
        finite = [
            abs(r["aria_minus_independently_interpolated_jpl_seconds"])
            for r in selected
            if r["aria_minus_independently_interpolated_jpl_seconds"] is not None
        ]
        per_kind[kind] = {
            "sample_count": len(selected),
            "compared_count": len(finite),
            "missing_aria_event_search_count": len(selected) - len(finite),
            "abs_timing_difference_seconds": distribution(finite) if finite else None,
            "candidate_60_seconds_exceedances": sum(
                x["candidate_60_seconds_exceeded"] is True for x in selected
            ),
            "max_abs_cubic_vs_linear_seconds": max(
                abs(r["jpl_reference"]["cubic_minus_linear_seconds"]) for r in selected
            ),
            "reference_interpolation_error_bound_derived": False,
            "individual_event_brackets_not_continuous_completeness": True,
        }
    return {
        "schema_version": 1,
        "report_id": "aria-wp55-independent-jpl-event-root-comparison-v1",
        "source_fixture_id": originals["dataset_id"],
        "source_fixture_sha256": original_sha256,
        "physical_profile": "planet-centres-v1",
        "external_rays_verified_offline": True,
        "event_case_count": len(records),
        "per_kind": per_kind,
        "reference_models": {
            "observer": "Earth (399), JPL Horizons-selected source (usually DE441)",
            "physical_target": "Mars–Pluto original Horizons physical planet centres",
            "frame": "true tropical ecliptic/equinox of date IAU 2006/2000A",
            "time": "TT Julian Date; signed error in seconds",
            "source_independence": "external original Horizons ICRF directions",
            "shared_standard_dependency": "PyERFA 2.0.1.5 (both sides IAU 2006/2000A)",
            "reference_rate": "five-point Horizons ±0.0125 and ±0.025 TT-day stencil",
            "reference_root": "four-point cubic within nine independent JPL time samples",
        },
        "diagnostic_limits": {
            "event_timing_candidate_seconds": CANDIDATE_TIMING_SECONDS,
            "not_an_approved_reliable_timing_bound": True,
            "interpolation_vs_linear_diagnostic_is_not_error_certificate": True,
        },
        "independently_verified_root_completeness": False,
        "reference_interpolation_error_bound_established": False,
        "commercial_event_timing_qualified": False,
        "absolute_astronomical_accuracy_certified": False,
        "rows": records,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("data/fixtures/horizons/wp55-events"))
    p.add_argument("--wp54", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--centres-dir", type=Path, required=True)
    p.add_argument(
        "--output", type=Path, default=Path("docs/validation/wp55-independent-event-roots.json")
    )
    args = p.parse_args()
    verified = validate_wp55(args.source, args.wp54)
    if verified["verified_events"] != 22:
        raise ValueError("Incomplete independent external event source")
    path = args.source / "wp55-horizons-event-roots-v1.json"
    raw_bytes = path.read_bytes()
    originals = json.loads(raw_bytes)
    manifest = centres_manifest()
    if originals["aria_base_sha256"] != manifest["base_sha256"]:
        raise ValueError("JPL source manifest version drift")
    kernels = {
        body: args.centres_dir / info["filename"] for body, info in manifest["sources"].items()
    }
    with Ephemeris(args.base, centre_kernels=kernels) as engine:
        report = compare(engine, originals, hashlib.sha256(raw_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    for name, stats in report["per_kind"].items():
        print(
            f"{name}: {stats['compared_count']}/{stats['sample_count']} comparisons; "
            f"max |Δt| {stats['abs_timing_difference_seconds']['max'] if stats['abs_timing_difference_seconds'] else None} seconds; "
            f"60s provisional exceedances {stats['candidate_60_seconds_exceedances']}",
            flush=True,
        )
    print("No commercial event-timing or root-completeness certification is claimed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
