# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Independent CSPICE evaluator comparison for JUP349 physical Jupiter centres.

The JPL source file is checked against the official, published MD5 value.
An observed SHA-256 is recorded for subsequent independent approval/pinning.
This script does not alter Aria's operational calculation API.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import spiceypy as spice
from audit_planet_centres import WINDOW_JD_TDB, inspect_segments, sha256
from jplephem.spk import SPK

from ariaephemeris.datasets import verify
from ariaephemeris.sources import Kernel

JUPITER_MD5 = "c7ef9d1829bb39bbbc2ba30d4a5a8a05"
MAX_POSITION_RESIDUAL_M = 1.0  # Initial evaluator-agreement gate, NOT physical model accuracy.
MAX_VELOCITY_RESIDUAL_MM_S = 1.0
SAMPLE_JD_TDB = (
    WINDOW_JD_TDB[0],
    2415020.5 + 1,
    2433282.5,  # 1950
    2451545.0,  # J2000
    2458849.5,  # 2020
    2461041.5,  # 2026
    2469807.5,  # 2050
    2487704.5,  # 2100
    WINDOW_JD_TDB[1],
)


def md5(path: Path) -> str:
    result = hashlib.md5()  # noqa: S324 -- published JPL transport digest only
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def run(base: Path, satellite: Path, expected_sha256: str | None = None) -> dict[str, Any]:
    manifest = verify(base)
    observed_md5 = md5(satellite)
    if observed_md5 != JUPITER_MD5:
        raise ValueError(
            f"JUP349 published MD5 mismatch: expected {JUPITER_MD5}, observed {observed_md5}"
        )
    observed_sha = sha256(satellite)
    if expected_sha256 is not None and observed_sha != expected_sha256:
        raise ValueError("JUP349 does not match independently pinned SHA-256")

    source = SPK.open(str(satellite))
    try:
        audit = inspect_segments(list(source.segments), "jupiter")
        if not audit["reader_and_coverage_pass"]:
            raise ValueError("JUP349 lacks continuous supported 599 wrt 5 segments")
        samples: list[dict[str, Any]] = []
        base_source = Kernel(base)
        try:
            spice.kclear()
            # Load satellite FIRST, base planetary DE442s SECOND. CSPICE chooses
            # the latest loaded file for shared barycentre targets: avoid using
            # JUP349's embedded barycentre solution instead of Aria DE442s.
            spice.furnsh(str(satellite.resolve()))
            spice.furnsh(str(base.resolve()))
            try:
                for jd in SAMPLE_JD_TDB:
                    matching = [
                        row
                        for row in audit["direct_segments"]
                        if row["supported_by_current_reader"]
                        and row["start_jd_tdb"] <= jd <= row["end_jd_tdb"]
                    ]
                    if not matching:
                        raise ValueError(f"JUP349 has no direct 599/5 segment at JD {jd}")
                    chosen = max(matching, key=lambda row: row["segment_index"])
                    segment = source.segments[chosen["segment_index"]]
                    offset_p, offset_v = segment.compute_and_differentiate(jd)
                    if segment.data_type == 3:
                        offset_p, offset_v = offset_p[:3], offset_v[3:] * 86400
                    base_p, base_v = base_source.state(5, jd)
                    proposed_p = np.asarray(base_p, dtype=float) + np.asarray(offset_p, dtype=float)
                    proposed_v = np.asarray(base_v, dtype=float) + np.asarray(offset_v, dtype=float)

                    et = (jd - 2451545.0) * 86400.0
                    direct_spice, _ = spice.spkgeo(599, et, "J2000", 5)
                    base_spice, _ = spice.spkgeo(5, et, "J2000", 0)
                    centre_spice, _ = spice.spkgeo(599, et, "J2000", 0)
                    direct_spice = np.asarray(direct_spice, dtype=float)
                    base_spice = np.asarray(base_spice, dtype=float)
                    centre_spice = np.asarray(centre_spice, dtype=float)
                    expected_from_components = base_spice + direct_spice
                    pos_residual_m = float(np.linalg.norm(proposed_p - centre_spice[:3]) * 1000)
                    vel_residual_mm_s = float(
                        np.linalg.norm(proposed_v / 86400 - centre_spice[3:]) * 1e6
                    )
                    base_residual_m = float(np.linalg.norm(base_p - base_spice[:3]) * 1000)
                    offset_residual_m = float(np.linalg.norm(offset_p - direct_spice[:3]) * 1000)
                    compose_residual_m = float(
                        np.linalg.norm(expected_from_components - centre_spice) * 1000
                    )
                    if not all(
                        math.isfinite(x)
                        for x in (
                            pos_residual_m,
                            vel_residual_mm_s,
                            base_residual_m,
                            offset_residual_m,
                            compose_residual_m,
                        )
                    ):
                        raise ValueError(f"Non-finite Jupiter state residual at JD {jd}")
                    samples.append(
                        {
                            "jd_tdb": jd,
                            "segment_index": chosen["segment_index"],
                            "aria_centre_position_km": proposed_p.tolist(),
                            "aria_centre_velocity_km_day": proposed_v.tolist(),
                            "cspice_centre_position_km": centre_spice[:3].tolist(),
                            "cspice_centre_velocity_km_day": (centre_spice[3:] * 86400).tolist(),
                            "position_residual_m": pos_residual_m,
                            "velocity_residual_mm_s": vel_residual_mm_s,
                            "base_barycentre_residual_m": base_residual_m,
                            "direct_offset_residual_m": offset_residual_m,
                            "cspice_internal_composition_residual_m": compose_residual_m,
                        }
                    )
            finally:
                spice.kclear()
        finally:
            base_source.close()
    finally:
        source.close()

    max_pos = max(row["position_residual_m"] for row in samples)
    max_vel = max(row["velocity_residual_mm_s"] for row in samples)
    passed = max_pos <= MAX_POSITION_RESIDUAL_M and max_vel <= MAX_VELOCITY_RESIDUAL_MM_S
    return {
        "source": {
            "satellite_file": satellite.name,
            "satellite_published_md5": JUPITER_MD5,
            "satellite_md5_checked": observed_md5,
            "satellite_sha256_observed": observed_sha,
            "satellite_sha256_pinned_independently": expected_sha256 is not None,
            "base_dataset_id": manifest["dataset_id"],
            "base_sha256_verified": manifest["sha256"],
        },
        "source_coverage": audit,
        "cspice_load_order": ["satellite_spk", "aria_de442s_base"],
        "evaluation": "J2000/ICRF-compatible barycentric geometric TDB km and km/day",
        "independent_evaluator": "CSPICE via SpiceyPy, using the same JPL source files",
        "thresholds": {
            "max_position_residual_m": MAX_POSITION_RESIDUAL_M,
            "max_velocity_residual_mm_s": MAX_VELOCITY_RESIDUAL_MM_S,
        },
        "samples": samples,
        "observed_max_position_residual_m": max_pos,
        "observed_max_velocity_residual_mm_s": max_vel,
        "evaluator_agreement_pass": passed,
        "commercial_qualification": "NOT APPROVED: limited samples, source pin and owner review",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--jupiter", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = run(args.base, args.jupiter, args.expected_sha256)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(
            f"JUP349 J2000/ICRF CSPICE agreement: {report['evaluator_agreement_pass']}; "
            f"max position {report['observed_max_position_residual_m']:.6g} m; "
            f"velocity {report['observed_max_velocity_residual_mm_s']:.6g} mm/s; "
            f"JUP349 SHA256 {report['source']['satellite_sha256_observed']}"
        )
        return 0 if report["evaluator_agreement_pass"] else 1
    except Exception as error:
        print(f"Jupiter centre qualification failed: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
