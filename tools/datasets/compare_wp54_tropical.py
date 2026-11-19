# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""WP5.4: independent-source tropical chart coordinate and motion comparison.

Reference R.A./Dec comes exclusively from pinned NASA/JPL Horizons OBSERVER
quantity 45; IAU 2006/2000A true-of-date rotation is implemented separately
here with direct ERFA standard primitives, not by calling Aria frames.
**This is NOT an independent implementation of the IAU precession model**:
both sides use ERFA, which is identified as a shared mathematical dependency.

Longitude rates derive from five Horizons evaluations at distinct TT instants,
NOT from Aria velocity, longitude samples or its differentiation routine.
Critical ingress and station epochs were nominated by Aria for coverage only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import erfa

from ariaephemeris import Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_wp54_tropical import verify as verify_wp54

ARCSEC_PER_DEG = 3600.0
RATE_STEP_DAYS = 0.0125
CANDIDATE_ANGLE_ARCSEC = 0.05
CANDIDATE_RATE_DEG_DAY = 0.0001
AMBIGUOUS_MOTION_BAND = 0.0002
BOUNDARY_MARGIN_ARCSEC = 0.05
BODY_ORDER = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")


def signed_angle(first: float, second: float) -> float:
    return (first - second + 180.0) % 360.0 - 180.0


def true_tropical_from_icrf(ra_deg: float, dec_deg: float, jd_tt: float) -> tuple[float, float]:
    """Direct independent coordinate conversion using reference SOFA/ERFA primitives.

    Separate closed-form Euler x-rotation from true equatorial basis. Never
    import ariaephemeris.frames.rotation or evaluate an Aria reference position.
    """
    if not all(math.isfinite(x) for x in (ra_deg, dec_deg, jd_tt)):
        raise ValueError("Nonfinite external astronomical direction or epoch")
    if not (0 <= ra_deg < 360 and -90 <= dec_deg <= 90):
        raise ValueError("External direction outside valid ICRF range")
    alpha, delta = math.radians(ra_deg), math.radians(dec_deg)
    xyz = [
        math.cos(delta) * math.cos(alpha),
        math.cos(delta) * math.sin(alpha),
        math.sin(delta),
    ]
    tt1, tt2 = 2451545.0, jd_tt - 2451545.0
    equator_matrix = erfa.pnm06a(tt1, tt2)
    x, y, z = (float(v) for v in equator_matrix @ xyz)
    eps = float(erfa.obl06(tt1, tt2) + erfa.nut06a(tt1, tt2)[1])
    y_ecl = math.cos(eps) * y + math.sin(eps) * z
    z_ecl = -math.sin(eps) * y + math.cos(eps) * z
    longitude = math.degrees(math.atan2(y_ecl, x)) % 360.0
    latitude = math.degrees(math.atan2(z_ecl, math.hypot(x, y_ecl)))
    if not (-90 <= latitude <= 90):
        raise ValueError("Invalid IAU 2006 ecliptic latitude")
    return longitude, latitude


def reference_rate(stencil: list[tuple[float, float]], step: float = RATE_STEP_DAYS) -> float:
    """Five-point differentiated *moving* true ecliptic longitude, deg/TT day."""
    if len(stencil) != 5 or not step > 0 or not math.isfinite(step):
        raise ValueError("Five independent longitudinal samples and valid step required")
    if any(not math.isfinite(v) for v, _ in stencil):
        raise ValueError("Nonfinite independent reference longitude")
    longitude = stencil[2][0]
    changes = [signed_angle(v[0], longitude) for v in stencil]
    if any(abs(x) > 90 for x in changes):
        raise ValueError("Unresolved longitude wrap or discontinuity in rate reference")
    return (changes[0] - 8 * changes[1] + 8 * changes[3] - changes[4]) / (12 * step)


def nearest_sign_boundary_arcsec(longitude: float) -> float:
    remainder = longitude % 30.0
    return min(remainder, 30.0 - remainder) * ARCSEC_PER_DEG


def _stats(values: list[float]) -> dict[str, float | int]:
    if not values or any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("Nonfinite or missing independent comparison residual")
    ordered = sorted(values)
    n = len(ordered)
    p = (n - 1) * 0.95
    k = int(p)
    return {
        "count": n,
        "max": ordered[-1],
        "rms": math.sqrt(sum(v * v for v in ordered) / n),
        "p95": ordered[k] + (ordered[min(k + 1, n - 1)] - ordered[k]) * (p - k),
    }


def calculate(engine: Ephemeris, refs: dict[str, Any], fixture_sha256: str) -> dict[str, Any]:
    source_rows = {(row["body"], row["jd_tt"]): row for row in refs["rays"]}
    if len(source_rows) != 930 or len(refs["cases"]) != 186:
        raise ValueError("Incomplete source of independent JPL chart directions")
    rows = []
    for body in BODY_ORDER:
        selected = [case for case in refs["cases"] if case["body"] == body]
        if len(selected) != 31:
            raise ValueError("Missing stress/baseline epochs")
        first = PositionRequest(
            TimeInput(jd=(selected[0]["jd_tt"], 0.0), scale="TT"),
            bodies=(body,),
            origin="geocentric",
            position_mode="apparent",
            profile="planet-centres-v1",
            frame="true_ecliptic_of_date",
            zodiac="tropical",
        )
        engine_results = engine.positions_batch(
            first,
            [TimeInput(jd=(case["jd_tt"], 0.0), scale="TT") for case in selected],
        )
        if len(engine_results) != len(selected):
            raise ValueError("Aria chart output count does not match reference epochs")
        for case, output in zip(selected, engine_results, strict=True):
            if (
                output.metadata["profile"] != "planet-centres-v1"
                or output.metadata["frame"] != "true_ecliptic_of_date"
                or output.metadata["origin"] != "geocentric"
                or output.metadata["position_mode"] != "apparent"
                or output.metadata["zodiac"] != "tropical"
            ):
                raise ValueError("Aria chart result uses a different astronomical convention")
            planet = output.bodies[0]
            if planet.target_id != case["target_id"] or planet.centre_id != 399:
                raise ValueError("Planet-centre or Earth target identity mismatch")
            if abs(sum(output.metadata["time"]["jd_tt"]) - case["jd_tt"]) > 1e-9:
                raise ValueError("Independent reference and Aria use different TT instants")
            ref_points = [
                true_tropical_from_icrf(
                    source_rows[(body, jd)]["inertial_apparent_ra_deg"],
                    source_rows[(body, jd)]["inertial_apparent_dec_deg"],
                    jd,
                )
                for jd in case["stencil_jd_tt"]
            ]
            ref_lon, ref_lat = ref_points[2]
            ref_rate = reference_rate(ref_points, refs["tt_rate_step_days"])
            lon_arcsec = signed_angle(planet.longitude_deg, ref_lon) * ARCSEC_PER_DEG
            lat_arcsec = (planet.latitude_deg - ref_lat) * ARCSEC_PER_DEG
            rate_residual = planet.longitude_rate_deg_day - ref_rate
            if not all(math.isfinite(x) for x in (lon_arcsec, lat_arcsec, rate_residual)):
                raise ValueError("Nonfinite astrological reference comparison")
            ref_motion = (
                "stationary"
                if abs(ref_rate) <= first.stationary_band_deg_day
                else ("retrograde" if ref_rate < 0 else "direct")
            )
            both_significant = (
                abs(ref_rate) > AMBIGUOUS_MOTION_BAND
                and abs(planet.longitude_rate_deg_day) > AMBIGUOUS_MOTION_BAND
            )
            delta_to_cusp = nearest_sign_boundary_arcsec(ref_lon)
            robust_sign = delta_to_cusp > BOUNDARY_MARGIN_ARCSEC and (
                nearest_sign_boundary_arcsec(planet.longitude_deg) > BOUNDARY_MARGIN_ARCSEC
            )
            rows.append(
                {
                    "fixture_id": case["id"],
                    "body": body,
                    "target_id": case["target_id"],
                    "jd_tt": case["jd_tt"],
                    "sample_category": case["category"],
                    "stress_nomination": case["nomination"],
                    "reference": {
                        "tropical_longitude_deg": ref_lon,
                        "tropical_latitude_deg": ref_lat,
                        "signed_longitude_rate_deg_tt_day": ref_rate,
                        "motion_classification": ref_motion,
                        "sign_index_0_11": int(ref_lon // 30) % 12,
                        "stencil_jd_tt": case["stencil_jd_tt"],
                        "source_icu": "Horizons quantity45 ICRF RA/Dec; IAU2006 true ecliptic-of-date",
                    },
                    "aria": {
                        "tropical_longitude_deg": planet.longitude_deg,
                        "tropical_latitude_deg": planet.latitude_deg,
                        "signed_longitude_rate_deg_tt_day": planet.longitude_rate_deg_day,
                        "motion_classification": planet.motion,
                        "sign_index_0_11": int(planet.longitude_deg // 30) % 12,
                    },
                    "residual": {
                        "longitude_arcsec_signed": lon_arcsec,
                        "latitude_arcsec_signed": lat_arcsec,
                        "longitude_rate_deg_tt_day_signed": rate_residual,
                        "candidate_longitude_0p05_arcsec_exceeded": abs(lon_arcsec)
                        > CANDIDATE_ANGLE_ARCSEC,
                        "candidate_latitude_0p05_arcsec_exceeded": abs(lat_arcsec)
                        > CANDIDATE_ANGLE_ARCSEC,
                        "candidate_rate_1e_minus_4_deg_day_exceeded": abs(rate_residual)
                        > CANDIDATE_RATE_DEG_DAY,
                        "motion_sign_mismatch_outside_station_band": both_significant
                        and ((ref_rate < 0) != (planet.longitude_rate_deg_day < 0)),
                        "sign_mismatch_away_from_boundary": robust_sign
                        and (int(ref_lon // 30) % 12 != int(planet.longitude_deg // 30) % 12),
                        "near_cusp_ambiguous": not robust_sign,
                        "near_station_ambiguous": not both_significant,
                    },
                }
            )
    if len(rows) != 186 or len({r["fixture_id"] for r in rows}) != 186:
        raise ValueError("Incomplete independent astrological coordinate comparison")
    per_planet = {}
    for body in BODY_ORDER:
        samples = [row for row in rows if row["body"] == body]
        if len(samples) != 31:
            raise ValueError("Missing planet comparative records")
        residuals = [row["residual"] for row in samples]
        per_planet[body] = {
            "longitude_arcsec": _stats([abs(x["longitude_arcsec_signed"]) for x in residuals]),
            "latitude_arcsec": _stats([abs(x["latitude_arcsec_signed"]) for x in residuals]),
            "signed_longitude_rate_deg_tt_day": _stats(
                [abs(x["longitude_rate_deg_tt_day_signed"]) for x in residuals]
            ),
            "motion_mismatches_outside_station_band": sum(
                x["motion_sign_mismatch_outside_station_band"] for x in residuals
            ),
            "sign_mismatches_away_from_cusps": sum(
                x["sign_mismatch_away_from_boundary"] for x in residuals
            ),
            "rate_candidate_exceedances": sum(
                x["candidate_rate_1e_minus_4_deg_day_exceeded"] for x in residuals
            ),
            "angle_candidate_exceedances": sum(
                x["candidate_longitude_0p05_arcsec_exceeded"]
                or x["candidate_latitude_0p05_arcsec_exceeded"]
                for x in residuals
            ),
            "stress_categories": {
                category: sum(r["sample_category"] == category for r in samples)
                for category in ("baseline", "station", "ingress")
            },
        }
    return {
        "schema_version": 1,
        "report_id": "aria-wp54-tropical-coordinates-and-signed-rate-v1",
        "reference_dataset_id": refs["dataset_id"],
        "reference_data_sha256": fixture_sha256,
        "profile": "planet-centres-v1",
        "source_fixtures_verified_offline": True,
        "sample_count": len(rows),
        "per_planet": per_planet,
        "compared": {
            "origin": "Earth geocentre (399)",
            "position_mode": "airless apparent with light time, deflection and aberration",
            "frame": "IAU 2006/2000A true ecliptic/equinox-of-date",
            "zodiac": "tropical",
            "source": "external JPL Horizons inertial ICRF RA/Dec quantity45, TT",
            "independent_rate": "five-point Horizons source directions +/-0.0125 and +/-0.025 TT days; full moving ecliptic",
            "aria_rate": "five-point complete Aria pipeline +/-0.001 TT days; different stencils and source ephemerides",
            "transform_qualification": "independent path, SHARED ERFA 2.0.1.5 precession-nutation dependency",
            "stress_selection": "Aria-nominated 2023-2025 station and ingress; JPL independently supplies all expected reference coordinates",
        },
        "provisional_engineering_diagnostics": {
            "longitude_latitude_arcsec": CANDIDATE_ANGLE_ARCSEC,
            "signed_rate_deg_tt_day": CANDIDATE_RATE_DEG_DAY,
            "acceptance_status": "NOT APPROVED; observed excursions must be reported, never ignored",
        },
        "scientific_status": "SAMPLED_CHART_COORDINATE_AGREEMENT; MODEL_AND_RATE_SOURCE_UNCERTAINTY_OPEN",
        "absolute_astronomical_accuracy_certified": False,
        "commercial_release_qualified": False,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures", type=Path, default=Path("data/fixtures/horizons/wp54-tropical")
    )
    parser.add_argument("--wp51", type=Path, default=Path("data/fixtures/horizons"))
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--centres-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    integrity = verify_wp54(args.fixtures, args.wp51)
    if integrity["verified_critical_and_baseline_chart_cases"] != 186:
        raise ValueError("Unverified independent astronomical chart reference")
    path = args.fixtures / "wp54-horizons-tropical-stencils-v1.json"
    original_bytes = path.read_bytes()
    refs = json.loads(original_bytes.decode("utf-8"))
    manifest = centres_manifest()
    if manifest["base_sha256"] != refs["aria_base_sha256"]:
        raise ValueError("Aria model base source has changed since fixture acquisition")
    sources = {
        body: args.centres_dir / record["filename"] for body, record in manifest["sources"].items()
    }
    with Ephemeris(args.base, centre_kernels=sources) as engine:
        report = calculate(engine, refs, hashlib.sha256(original_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"WP5.4: {report['sample_count']} apparent tropical chart positions/rates measured.")
    for body, r in report["per_planet"].items():
        print(
            f"{body:8} | lon max {r['longitude_arcsec']['max']:.6g} arcsec"
            f" | lat max {r['latitude_arcsec']['max']:.6g} arcsec"
            f" | rate max {r['signed_longitude_rate_deg_tt_day']['max']:.6g} deg/day"
            f" | motion mismatches {r['motion_mismatches_outside_station_band']}"
            f" | sign mismatches {r['sign_mismatches_away_from_cusps']}"
        )
    print("Scientific physical-model/event certification NOT claimed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
