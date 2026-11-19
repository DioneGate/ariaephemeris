# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Quantitatively attribute WP5.2 Jupiter/Pluto discrepancies to source components.

All calculations are on identical frozen TDB JDs and ICRF geometric vectors.
This is an **algebraic decomposition** of observed model differences; it does
NOT establish physical truth or a commercial ephemeris uncertainty bound.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_horizons_fixtures import validate as verify_original_reference  # noqa: E402
from verify_horizons_model_components import verify as verify_components  # noqa: E402

SELECTED = {"jupiter": 5, "pluto": 9}
ROLES = ("parent_geo", "parent_ssb", "earth_ssb", "centre_ssb")
KM_DAY = 86400.0


def vec(value: Any) -> list[float]:
    if len(value) != 3 or any(not math.isfinite(x) for x in value):
        raise ValueError("Every physical source vector must contain three finite components")
    return [float(v) for v in value]


def sub(a: Any, b: Any) -> list[float]:
    return [x - y for x, y in zip(vec(a), vec(b), strict=True)]


def add(a: Any, b: Any) -> list[float]:
    return [x + y for x, y in zip(vec(a), vec(b), strict=True)]


def norm(a: Any) -> float:
    return math.sqrt(sum(x * x for x in vec(a)))


def scale(a: Any, scalar: float) -> list[float]:
    return [x * scalar for x in vec(a)]


def direction_projection(component: Any, total: Any) -> float:
    t = vec(total)
    mag = norm(t)
    return sum(x * y for x, y in zip(vec(component), t, strict=True)) / mag if mag else 0.0


def stats(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Expected nonempty nonnegative finite source component values")
    ordered = sorted(values)
    x = (len(ordered) - 1) * 0.95
    n = int(x)
    p95 = ordered[n] + (ordered[min(n + 1, len(ordered) - 1)] - ordered[n]) * (x - n)
    return {
        "count": len(values),
        "max": ordered[-1],
        "rms": math.sqrt(sum(v * v for v in values) / len(values)),
        "p95": p95,
    }


def attribute(aria: dict[str, list[float]], horizon: dict[str, list[float]]) -> dict[str, Any]:
    """Full, non-overlapping exact arithmetic decomposition (ICRF, km).

    A physical centre relative to Earth = AparentSSB - AearthSSB + Aoffset;
    HparentGeo is queried directly. The effective Hoffset is HtargetGeo -
    HparentGeo, including any Horizons source-context differences.
    """
    required_a = {"centre_ssb", "parent_ssb", "earth_ssb"}
    required_h = {"target_geo", "centre_ssb", "parent_ssb", "earth_ssb", "parent_geo"}
    if set(aria) != required_a or set(horizon) != required_h:
        raise ValueError("Missing exact source decomposition component")
    a_target_geo = sub(aria["centre_ssb"], aria["earth_ssb"])
    a_parent_geo = sub(aria["parent_ssb"], aria["earth_ssb"])
    a_offset = sub(aria["centre_ssb"], aria["parent_ssb"])

    h_parent_chain = sub(sub(horizon["parent_ssb"], horizon["earth_ssb"]), horizon["parent_geo"])
    h_centre_chain = sub(sub(horizon["centre_ssb"], horizon["earth_ssb"]), horizon["target_geo"])
    h_effective_offset = sub(horizon["target_geo"], horizon["parent_geo"])
    h_ssb_offset = sub(horizon["centre_ssb"], horizon["parent_ssb"])

    total = sub(a_target_geo, horizon["target_geo"])
    parent_geo = sub(a_parent_geo, horizon["parent_geo"])
    offset_effective = sub(a_offset, h_effective_offset)
    parent_ssb_model = sub(aria["parent_ssb"], horizon["parent_ssb"])
    earth_ssb_model = sub(aria["earth_ssb"], horizon["earth_ssb"])
    centre_ssb_model = sub(aria["centre_ssb"], horizon["centre_ssb"])
    offset_from_ssb = sub(a_offset, h_ssb_offset)

    # H parent and centre may follow different SPK paths on different queries.
    # Their non-zero context gaps are not silently labelled "planet-offset error".
    residual = sub(total, add(parent_geo, offset_effective))
    parent_residual = sub(parent_geo, add(sub(parent_ssb_model, earth_ssb_model), h_parent_chain))
    centre_residual = sub(total, add(sub(centre_ssb_model, earth_ssb_model), h_centre_chain))
    if any(norm(x) > 2e-4 for x in (residual, parent_residual, centre_residual)):
        raise ValueError("Source decomposition failed identity reconstruction")

    return {
        "total_difference": total,
        "parent_geocentric_difference": parent_geo,
        "effective_offset_difference": offset_effective,
        "planet_parent_ssb_model_difference": parent_ssb_model,
        "earth_ssb_model_difference": earth_ssb_model,
        "planet_centre_ssb_model_difference": centre_ssb_model,
        "direct_ssb_offset_difference": offset_from_ssb,
        "horizons_parent_query_context_gap": h_parent_chain,
        "horizons_centre_query_context_gap": h_centre_chain,
        "total_reconstruction_error_km": norm(residual),
        "parent_reconstruction_error_km": norm(parent_residual),
        "centre_reconstruction_error_km": norm(centre_residual),
        "parent_projected_along_total_km": direction_projection(parent_geo, total),
        "effective_offset_projected_along_total_km": direction_projection(offset_effective, total),
    }


def _case_lookup(source: dict[str, Any]) -> dict[tuple[str, str, float], dict[str, Any]]:
    return {(case["body"], case["role"], case["jd_tdb"]): case for case in source["cases"]}


def _reference_lookup(source: dict[str, Any]) -> dict[tuple[str, float], dict[str, Any]]:
    return {
        (case["body"], case["metrics"]["jd_tdb"]): case
        for case in source["rows"]
        if case["body"] in SELECTED and case["kind"] == "geometric"
    }


def evaluate(engine: Ephemeris, original: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    observed = _case_lookup(source)
    frozen = _reference_lookup(original)
    meta = {(r["body"], r["role"]): r for r in source["responses"]}
    if len(observed) != 200 or len(frozen) != 50 or len(meta) != 8:
        raise ValueError("Incomplete or ambiguous independently sourced model evidence")

    rows: list[dict[str, Any]] = []
    per_body: dict[str, Any] = {}
    for body, parent in SELECTED.items():
        for jd in sorted(jd for b, jd in frozen if b == body):
            original_case = frozen[(body, jd)]["metrics"]
            time = TimeInput(jd=(jd, 0.0), scale="TDB")
            a_target = engine.raw_state(body, time, profile="planet-centres-v1")
            a_parent = engine.raw_state(body, time, profile="reference")
            a_earth = engine.raw_state("earth", time, profile="reference")
            if (a_target["target_id"], a_parent["target_id"], a_earth["target_id"]) != (
                parent * 100 + 99,
                parent,
                399,
            ):
                raise ValueError("Wrong physical-centre or barycentre target identity")
            actual_tdb = sum(a_target["time"]["jd_tdb"])
            if abs(actual_tdb - jd) > 1e-9:
                raise ValueError("Different physical TDB instants")

            pos_a = {
                "centre_ssb": a_target["position_km"],
                "parent_ssb": a_parent["position_km"],
                "earth_ssb": a_earth["position_km"],
            }
            vel_a = {
                "centre_ssb": scale(a_target["velocity_km_day"], 1 / KM_DAY),
                "parent_ssb": scale(a_parent["velocity_km_day"], 1 / KM_DAY),
                "earth_ssb": scale(a_earth["velocity_km_day"], 1 / KM_DAY),
            }
            parts = {role: observed[(body, role, jd)] for role in ROLES}
            pos_h = {
                "target_geo": original_case["reference_position_km"],
                **{role: parts[role]["position_km"] for role in ROLES},
            }
            vel_h = {
                "target_geo": original_case["reference_velocity_km_s"],
                **{role: parts[role]["velocity_km_s"] for role in ROLES},
            }
            position = attribute(pos_a, pos_h)
            velocity = attribute(vel_a, vel_h)
            reported_delta = sub(
                original_case["aria_position_km"], original_case["reference_position_km"]
            )
            if norm(sub(reported_delta, position["total_difference"])) > 2e-4:
                raise ValueError("Re-evaluation changed the previously frozen WP5.2 state")
            if (
                abs(norm(position["total_difference"]) - original_case["position_residual_km"])
                > 2e-4
            ):
                raise ValueError("New measurement disagrees with prior WP5.2 norm")
            rows.append(
                {
                    "fixture_id": frozen[(body, jd)]["fixture_id"],
                    "body": body,
                    "target_id": parent * 100 + 99,
                    "parent_id": parent,
                    "jd_tdb": jd,
                    "measured_original_total_difference_km": norm(position["total_difference"]),
                    "model_component_position": position,
                    "model_component_velocity_km_s": velocity,
                    "horizons_sources": {
                        role: {
                            "target": meta[(body, role)]["source_header"]["target"],
                            "centre": meta[(body, role)]["source_header"]["centre"],
                            "labels": meta[(body, role)]["source_header"]["source_solution_labels"],
                            "raw_sha256": meta[(body, role)]["raw_sha256"],
                        }
                        for role in ROLES
                    },
                }
            )
        selected = [r for r in rows if r["body"] == body]
        if len(selected) != 25:
            raise ValueError("Incomplete source diagnostic for body")
        categories = {
            "total_geocentric_km": "total_difference",
            "parent_geocentric_km": "parent_geocentric_difference",
            "effective_centre_offset_km": "effective_offset_difference",
            "planet_parent_ssb_model_km": "planet_parent_ssb_model_difference",
            "earth_ssb_model_km": "earth_ssb_model_difference",
            "planet_centre_ssb_model_km": "planet_centre_ssb_model_difference",
            "direct_ssb_offset_km": "direct_ssb_offset_difference",
            "horizons_parent_query_context_gap_km": "horizons_parent_query_context_gap",
            "horizons_centre_query_context_gap_km": "horizons_centre_query_context_gap",
        }
        fields = {
            key: stats([norm(r["model_component_position"][name]) for r in selected])
            for key, name in categories.items()
        }
        fields["total_geocentric_velocity_m_s"] = stats(
            [norm(r["model_component_velocity_km_s"]["total_difference"]) * 1000 for r in selected]
        )
        fields["parent_geocentric_velocity_m_s"] = stats(
            [
                norm(r["model_component_velocity_km_s"]["parent_geocentric_difference"]) * 1000
                for r in selected
            ]
        )
        fields["effective_offset_velocity_m_s"] = stats(
            [
                norm(r["model_component_velocity_km_s"]["effective_offset_difference"]) * 1000
                for r in selected
            ]
        )
        fields["max_reconstruction_error_km"] = max(
            r["model_component_position"]["total_reconstruction_error_km"] for r in selected
        )
        fields["source_labels_by_role"] = {
            role: meta[(body, role)]["source_header"]["source_solution_labels"] for role in ROLES
        }
        fields["largest_total_fixture_id"] = max(
            selected, key=lambda r: r["measured_original_total_difference_km"]
        )["fixture_id"]
        per_body[body] = fields
    return {
        "schema_version": 1,
        "report_id": "aria-jpl-source-model-attribution-v1",
        "based_on_wp5_2": original["report_id"],
        "source_dataset_id": source["dataset_id"],
        "source_verified_offline": True,
        "number_of_components": len(source["cases"]),
        "sample_count": len(rows),
        "per_body": per_body,
        "samples": rows,
        "identity": (
            "Aria centre minus Horizons centre = "
            "(Aria parent geocentric minus Horizons parent geocentric) + "
            "(Aria direct offset minus Horizons effective offset), at identical TDB epoch"
        ),
        "horizons_context_warning": (
            "Horizon direct centre/parent/SSB queries may select differing SPK chains. "
            "Measured query-context gaps are explicitly retained rather than assigned to centre-offset error."
        ),
        "model_accuracy_status": "SOURCE_DISCREPANCY_ATTRIBUTED_BUT_ABSOLUTE_ACCURACY_UNCERTIFIED",
        "commercial_release_accuracy_certified": False,
        "source_model_fully_matched": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--original", type=Path, default=Path("docs/validation/wp5-2-horizons-comparison.json")
    )
    parser.add_argument("--original-fixtures", type=Path, default=Path("data/fixtures/horizons"))
    parser.add_argument(
        "--components", type=Path, default=Path("data/fixtures/horizons/model-components")
    )
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--centres-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if verify_original_reference(args.original_fixtures)["fixture_rows_verified"] != 300:
        raise ValueError("Original Horizons fixture data integrity mismatch")
    if verify_components(args.components)["verified_states"] != 200:
        raise ValueError("New Horizons model-component data integrity mismatch")
    original = json.loads(args.original.read_text(encoding="utf-8"))
    source = json.loads(
        (args.components / "jpl-model-components-v1.json").read_text(encoding="utf-8")
    )
    if original["sample_count"] != 300:
        raise ValueError("WP5.2 data report missing or incomplete")
    source_manifest = centres_manifest()
    if source_manifest["base_sha256"] != original["engine_base_sha256"]:
        raise ValueError("Different Aria planetary base than WP5.2")
    with Ephemeris(
        args.base,
        centre_kernels={
            body: args.centres_dir / source_manifest["sources"][body]["filename"]
            for body in SELECTED
        },
    ) as engine:
        report = evaluate(engine, original, source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print("Quantitative source-model differences: these are NOT absolute accuracy limits.")
    for body, result in report["per_body"].items():
        print(
            f"{body}: total={result['total_geocentric_km']['max']:.6f} km; "
            f"parent={result['parent_geocentric_km']['max']:.6f} km; "
            f"effective centre offset={result['effective_centre_offset_km']['max']:.6f} km; "
            f"Earth SSB={result['earth_ssb_model_km']['max']:.6f} km; "
            f"Horizons centre path gap={result['horizons_centre_query_context_gap_km']['max']:.6f} km"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
