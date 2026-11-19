# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""WP5.2: offline geometric and apparent comparisons to frozen external Horizons data.

This compares the *physical-centre* profile against independent Horizons
responses from WP5.1. Horizons may use different planetary models; numerical
residuals are diagnostics, not evidence of an independently matched model or
commercial accuracy qualification. No source reference is silently regenerated.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_horizons_fixtures import validate as validate_frozen_source  # noqa: E402

ARCSEC_PER_RAD = 180.0 * 3600.0 / math.pi
SECONDS_PER_DAY = 86400.0
CANDIDATE_APPARENT_ARCSEC = 1.0  # Diagnostic threshold; never auto-approved.
REQUIRED_BODIES = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")


def unit_direction(ra_deg: float, dec_deg: float) -> tuple[float, float, float]:
    if not all(math.isfinite(v) for v in (ra_deg, dec_deg)):
        raise ValueError("Non-finite celestial direction")
    if not 0 <= ra_deg < 360 or not -90 <= dec_deg <= 90:
        raise ValueError("Out-of-range ICRF RA or Dec")
    a, d = math.radians(ra_deg), math.radians(dec_deg)
    return math.cos(d) * math.cos(a), math.cos(d) * math.sin(a), math.sin(d)


def separation_arcsec(ra_a: float, dec_a: float, ra_b: float, dec_b: float) -> float:
    """Spherical angular separation, stable at the RA=0/360 discontinuity."""
    v, w = unit_direction(ra_a, dec_a), unit_direction(ra_b, dec_b)
    cross = (
        v[1] * w[2] - v[2] * w[1],
        v[2] * w[0] - v[0] * w[2],
        v[0] * w[1] - v[1] * w[0],
    )
    dot = sum(x * y for x, y in zip(v, w, strict=True))
    return math.atan2(math.sqrt(sum(x * x for x in cross)), dot) * ARCSEC_PER_RAD


def circular_delta_deg(first: float, second: float) -> float:
    return (first - second + 180.0) % 360.0 - 180.0


def source_label(header_line: str) -> str:
    prefix = "{source:"
    if prefix not in header_line or "}" not in header_line.split(prefix, 1)[1]:
        raise ValueError("Horizons source identity header unavailable")
    label = header_line.split(prefix, 1)[1].split("}", 1)[0].strip()
    if not label:
        raise ValueError("Empty Horizons source label")
    return label


def model_provenance(record: dict[str, Any], installed: dict[str, Any]) -> dict[str, Any]:
    header = record["source_header"]
    target_model = source_label(header["target"])
    observer_model = source_label(header["centre"])
    local_model = installed["filename"].removesuffix(".bsp")
    # Matching names alone does not prove a matched solution; Earth model can
    # differ (e.g. Horizons DE441 vs Aria's DE442s).
    same_target_label = target_model == local_model
    same_observer_label = observer_model == "DE442s"
    return {
        "horizons_target_source": target_model,
        "horizons_observer_source": observer_model,
        "horizons_all_reported_sources": header["source_solution_labels"],
        "aria_target_offset_source": local_model,
        "aria_target_offset_sha256": installed["sha256"],
        "aria_base": "DE442s",
        "aria_base_sha256": centres_manifest()["base_sha256"],
        "target_labels_identical": same_target_label,
        "observer_labels_identical": same_observer_label,
        "matched_physical_model_demonstrated": False,
        "reconciliation_status": "unreconciled-model-and-correction-differences",
    }


def vector_difference(
    a: list[float], b: list[float], scale: float = 1.0
) -> tuple[float, list[float]]:
    if len(a) != 3 or len(b) != 3 or not all(math.isfinite(x) for x in a + b):
        raise ValueError("Vectors must contain exactly three finite components")
    difference = [(x - y) * scale for x, y in zip(a, b, strict=True)]
    return math.sqrt(sum(x * x for x in difference)), difference


def _stats(values: list[float]) -> dict[str, float | int]:
    if not values or not all(math.isfinite(x) and x >= 0 for x in values):
        raise ValueError("No complete finite nonnegative comparison sample")
    ordered = sorted(values)
    pos = 0.95 * (len(values) - 1)
    j = int(pos)
    p95 = ordered[j] + (ordered[min(j + 1, len(values) - 1)] - ordered[j]) * (pos - j)
    return {
        "count": len(values),
        "max": max(values),
        "rms": math.sqrt(sum(v * v for v in values) / len(values)),
        "p95": p95,
    }


def _metadata_by_query(fixtures: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    queries = {(r["body"], r["kind"]): r for r in fixtures["raw_queries"]}
    if len(queries) != 12:
        raise ValueError("Missing or duplicate frozen reference queries")
    return queries


def evaluate(
    engine: Ephemeris, fixtures: dict[str, Any], source_manifest: dict[str, Any]
) -> dict[str, Any]:
    """Strictly evaluates every archived reference row with no network access."""
    lookup = _metadata_by_query(fixtures)
    records: list[dict[str, Any]] = []
    for case in fixtures["cases"]:
        body, kind = case["body"], case["kind"]
        reference = case["reference"]
        if body not in REQUIRED_BODIES or kind not in ("geometric", "apparent"):
            raise ValueError("Unapproved reference fixture body/kind")
        source = source_manifest["sources"][body]
        if case["target_id"] != source["target_id"]:
            raise ValueError("Horizons reference target differs from physical-centre target")
        provenance = model_provenance(lookup[(body, kind)], source)
        if kind == "geometric":
            jd_tdb = float(reference["jd_tdb"])
            time_input = TimeInput(jd=(jd_tdb, 0.0), scale="TDB")
            planet = engine.raw_state(body, time_input, profile="planet-centres-v1")
            earth = engine.raw_state("earth", time_input, profile="reference")
            if planet["target_id"] != source["target_id"] or earth["target_id"] != 399:
                raise ValueError("Engine returned incorrect planet/observer centre identity")
            actual_tdb = sum(planet["time"]["jd_tdb"])
            if abs(actual_tdb - jd_tdb) > 1e-9:
                raise ValueError("Geometric source/engine TDB epochs differ")
            geometric_position = [
                x - y for x, y in zip(planet["position_km"], earth["position_km"], strict=True)
            ]
            geometric_velocity = [
                (x - y) / SECONDS_PER_DAY
                for x, y in zip(planet["velocity_km_day"], earth["velocity_km_day"], strict=True)
            ]
            pos, pos_components = vector_difference(
                geometric_position, reference["position_km"]
            )
            speed, vel_components = vector_difference(
                geometric_velocity, reference["velocity_km_s"], scale=1000.0
            )
            metrics: dict[str, Any] = {
                "position_residual_km": pos,
                "velocity_residual_m_s": speed,
                "position_residual_components_km": pos_components,
                "velocity_residual_components_m_s": vel_components,
                "aria_position_km": geometric_position,
                "aria_velocity_km_s": geometric_velocity,
                "reference_position_km": reference["position_km"],
                "reference_velocity_km_s": reference["velocity_km_s"],
                "jd_tdb": jd_tdb,
                "computed_jd_tdb": actual_tdb,
            }
        else:
            jd_tt = float(reference["jd_tt"])
            t = TimeInput(jd=(jd_tt, 0.0), scale="TT")
            req = PositionRequest(
                t,
                bodies=(body,),
                profile="planet-centres-v1",
                origin="geocentric",
                position_mode="apparent",
                frame="icrs",
            )
            actual = engine.positions(req)
            if actual.metadata["frame"] != "icrs" or actual.metadata["profile"] != req.profile:
                raise ValueError("Apparent engine frame/profile mismatch")
            body_position = actual.bodies[0]
            if body_position.target_id != source["target_id"]:
                raise ValueError("Wrong apparent physical-centre target")
            # IMPORTANT: frame=icrs longitude/latitude are the inertial RA/Dec.
            # BodyPosition.right_ascension_deg is *true-of-date*, not compatible
            # with Horizons quantity 45.
            ra, dec = body_position.longitude_deg, body_position.latitude_deg
            expected_ra = reference["inertial_apparent_ra_deg"]
            expected_dec = reference["inertial_apparent_dec_deg"]
            angular_arcsec = separation_arcsec(ra, dec, expected_ra, expected_dec)
            metrics = {
                "angular_separation_arcsec": angular_arcsec,
                "circular_ra_residual_arcsec": circular_delta_deg(ra, expected_ra) * 3600,
                "dec_residual_arcsec": (dec - expected_dec) * 3600,
                "aria_inertial_ra_deg": ra,
                "aria_inertial_dec_deg": dec,
                "reference_inertial_ra_deg": expected_ra,
                "reference_inertial_dec_deg": expected_dec,
                "jd_tt": jd_tt,
                "candidate_1_arcsec_threshold_exceeded": angular_arcsec > CANDIDATE_APPARENT_ARCSEC,
            }
        records.append(
            {
                "fixture_id": case["id"],
                "body": body,
                "target_id": case["target_id"],
                "kind": kind,
                "comparison_result": "measured; model provenance unresolved",
                "reference_raw_file": case["source_raw_file"],
                "provenance": provenance,
                "metrics": metrics,
            }
        )
    if len(records) != 300 or len({r["fixture_id"] for r in records}) != 300:
        raise ValueError("Missing or duplicate comparison results; 300 required")

    per_body: dict[str, Any] = {}
    for body in REQUIRED_BODIES:
        geo = [r["metrics"] for r in records if r["body"] == body and r["kind"] == "geometric"]
        app = [r["metrics"] for r in records if r["body"] == body and r["kind"] == "apparent"]
        if len(geo) != 25 or len(app) != 25:
            raise ValueError("Incomplete per-planet geometrical or apparent sample")
        per_body[body] = {
            "geometric_position_km": _stats([r["position_residual_km"] for r in geo]),
            "geometric_velocity_m_s": _stats([r["velocity_residual_m_s"] for r in geo]),
            "apparent_direction_arcsec": _stats([r["angular_separation_arcsec"] for r in app]),
            "apparent_over_candidate_1_arcsec": sum(
                bool(r["candidate_1_arcsec_threshold_exceeded"]) for r in app
            ),
            "reference_target_model": model_provenance(lookup[(body, "geometric")], source_manifest["sources"][body])["horizons_target_source"],
            "reference_observer_model": model_provenance(lookup[(body, "geometric")], source_manifest["sources"][body])["horizons_observer_source"],
            "aria_offset_filename": source_manifest["sources"][body]["filename"],
        }
    return {
        "schema_version": 1,
        "report_id": "aria-wp5-2-external-horizons-comparison-v1",
        "reference_dataset_id": fixtures["dataset_id"],
        "reference_manifest_sha256": hashlib.sha256(
            json.dumps(fixtures, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "source_fixtures_verified_offline": True,
        "requested_profile": "planet-centres-v1",
        "engine_base_dataset_id": source_manifest["base_dataset_id"],
        "engine_base_sha256": source_manifest["base_sha256"],
        "comparison_conventions": {
            "geometric": "geocentric ICRF vector at TDB JD; Aria centre minus Earth, km and km/s",
            "apparent": "geocentric ICRF airless apparent RA/Dec at TT JD; compare Aria frame=icrs longitude/latitude to Horizons quantity 45",
            "right_ascension_warning": "Aria BodyPosition.right_ascension_deg is true-of-date; do not compare directly to Horizons inertial quantity 45",
            "model_differences": "Horizons dynamically selects its own source kernels, not the Aria DE442s-plus-offset stack; differences are unresolved diagnostics",
        },
        "sample_count": len(records),
        "per_body": per_body,
        "candidate_limits": {
            "apparent_arcsec": CANDIDATE_APPARENT_ARCSEC,
            "status": "diagnostic only: not an acceptance bound with differing models",
        },
        "scientific_status": "MEASURED_WITH_UNRECONCILED_SOURCE_MODELS",
        "physically_qualified_for_commercial_release": False,
        "independent_chart_accuracy_pass": None,
        "failure_policy": "Source integrity, matching times/frames, target identity, finite results and all 300 records are mandatory; observed model-dependent residuals are retained, never adjusted to manufacture a pass",
        "rows": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=Path("data/fixtures/horizons"))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--centres-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    validated = validate_frozen_source(args.fixtures)
    if validated["fixture_rows_verified"] != 300 or validated["raw_responses_verified"] != 12:
        raise ValueError("Horizons source verification did not pass")
    fixtures = json.loads(
        (args.fixtures / "horizons-reference-v1.json").read_text(encoding="utf-8")
    )
    sources = centres_manifest()
    paths = {
        body: args.centres_dir / record["filename"]
        for body, record in sources["sources"].items()
    }
    if set(paths) != set(REQUIRED_BODIES):
        raise ValueError("Source manifest does not contain the six required physical centres")
    with Ephemeris(args.base, centre_kernels=paths) as engine:
        report = evaluate(engine, fixtures, sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    print(f"WP5.2: {report['sample_count']} external comparisons, scientific acceptance not claimed.")
    for body, item in report["per_body"].items():
        print(
            f"{body:8} geometric max {item['geometric_position_km']['max']:.6g} km; "
            f"velocity {item['geometric_velocity_m_s']['max']:.6g} m/s; "
            f"apparent max {item['apparent_direction_arcsec']['max']:.6g} arcsec; "
            f">1 arcsec: {item['apparent_over_candidate_1_arcsec']}/25"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
