# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Check physical planet centres against CSPICE with a verified DE442s base.

Runs ONE satellite source per process to bound memory and avoid kernel priority
interference. Evaluator agreement is NOT physical source-model qualification.
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
from audit_planet_centres import TARGETS, WINDOW_JD_TDB, inspect_segments, sha256
from jplephem.spk import SPK

from ariaephemeris.datasets import verify
from ariaephemeris.sources import Kernel

POSITION_GATE_M = 1.0
VELOCITY_GATE_MM_S = 1.0
BASE_EPOCHS = (
    WINDOW_JD_TDB[0],
    2415021.5,
    2433282.5,
    2451545.0,
    2458849.5,
    2461041.5,
    2469807.5,
    2487704.5,
    WINDOW_JD_TDB[1],
)


def md5(path: Path) -> str:
    """MD5 is the published NAIF transport checksum, not a security primitive."""
    digest = hashlib.md5()  # noqa: S324 -- compatibility with NAIF's official digest list
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sample_epochs(
    direct_segments: list[dict[str, Any]],
    window: tuple[float, float] = WINDOW_JD_TDB,
) -> list[float]:
    """Include operating boundaries and a bounded sample around in-range joins."""
    lo, hi = window
    epochs = set(BASE_EPOCHS if window == WINDOW_JD_TDB else (lo, hi))
    seams = {
        float(row["start_jd_tdb"])
        for row in direct_segments
        if lo + 0.5 < float(row["start_jd_tdb"]) < hi - 0.5
    }
    # Spread samples across the range, not only the first four joins.
    ordered = sorted(seams)
    if len(ordered) > 4:
        indices = (0, (len(ordered) - 1) // 3, 2 * (len(ordered) - 1) // 3, -1)
        ordered = sorted({ordered[index] for index in indices})
    for seam in ordered:
        for offset in (-1.0 / 24.0, 1.0 / 24.0):
            jd = seam + offset
            if lo <= jd <= hi:
                epochs.add(jd)
    return sorted(jd for jd in epochs if lo <= jd <= hi)


def choose_segment(rows: list[dict[str, Any]], jd: float) -> dict[str, Any]:
    """Match Aria's highest-index precedence, never use an unsupported segment."""
    candidates = [
        row
        for row in rows
        if row["supported_by_current_reader"] and row["start_jd_tdb"] <= jd <= row["end_jd_tdb"]
    ]
    if not candidates:
        raise ValueError(f"No supported direct centre offset covering JD TDB {jd}")
    return max(candidates, key=lambda row: row["segment_index"])


def load_manifest(path: Path, planet: str) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ValueError("Unexpected centre source manifest version")
    record = manifest["sources"][planet]
    target, parent = TARGETS[planet]
    if record.get("target_id") != target or record.get("centre_id") != parent:
        raise ValueError(f"{planet}: manifest target/parent is inconsistent with Aria")
    checksum = record.get("published_md5")
    if not isinstance(checksum, str) or len(checksum) != 32:
        raise ValueError(f"{planet}: no published 32-character MD5")
    pinned = record.get("observed_sha256_pinned")
    if pinned is not None and (not isinstance(pinned, str) or len(pinned) != 64):
        raise ValueError(f"{planet}: SHA-256 pin is malformed")
    return record


def qualify(
    planet: str, base: Path, satellite: Path, source_record: dict[str, Any]
) -> dict[str, Any]:
    target, parent = TARGETS[planet]
    if satellite.name != source_record["source_file"]:
        raise ValueError(f"{planet}: supplied file is not the selected NAIF candidate")
    expected_md5 = source_record["published_md5"]
    observed_md5 = md5(satellite)
    if observed_md5.lower() != expected_md5.lower():
        raise ValueError(f"{planet}: NAIF published MD5 mismatch ({observed_md5})")
    observed_sha = sha256(satellite)
    expected_sha = source_record.get("observed_sha256_pinned")
    if expected_sha is not None and observed_sha.lower() != expected_sha.lower():
        raise ValueError(f"{planet}: SHA-256 differs from committed source manifest")
    base_manifest = verify(base)
    if source_record.get("composition_base_sha256") != base_manifest["sha256"]:
        raise ValueError(f"{planet}: base DE442s hash mismatch with source record")

    report: dict[str, Any] = {
        "body": planet,
        "source": {
            "file": satellite.name,
            "size_bytes": satellite.stat().st_size,
            "published_md5": expected_md5,
            "observed_md5": observed_md5,
            "observed_sha256": observed_sha,
            "expected_sha256": expected_sha,
            "sha256_precommitted": expected_sha is not None,
            "base_sha256": base_manifest["sha256"],
            "target_id": target,
            "centre_id": parent,
        },
        "independent_evaluator": "CSPICE/SpiceyPy (same JPL source files)",
        "semantics": "barycentric geometric state in J2000/ICRF-compatible frame at TDB JD",
        "thresholds": {"position_m": POSITION_GATE_M, "velocity_mm_s": VELOCITY_GATE_MM_S},
        "physical_model_accuracy": "NOT ASSESSED",
        "commercial_release_approval": "NOT APPROVED",
    }

    satellite_spk = SPK.open(str(satellite))
    try:
        coverage = inspect_segments(list(satellite_spk.segments), planet)
        report["coverage"] = coverage
        if not coverage["reader_and_coverage_pass"]:
            raise ValueError(f"{planet}: direct centre coverage/type/frame gate failed")
        epochs = sample_epochs(coverage["direct_segments"])
        base_spk = Kernel(base)
        try:
            spice.kclear()
            try:
                # Last loaded kernel wins for duplicate targets. Load DE442s LAST
                # so each barycentre is from the controlled Aria base dataset.
                spice.furnsh(str(satellite.resolve()))
                spice.furnsh(str(base.resolve()))
                samples: list[dict[str, Any]] = []
                for jd in epochs:
                    row = choose_segment(coverage["direct_segments"], jd)
                    segment = satellite_spk.segments[row["segment_index"]]
                    offset_p, offset_v = segment.compute_and_differentiate(jd)
                    if segment.data_type == 3:
                        offset_p, offset_v = offset_p[:3], offset_v[3:] * 86400.0
                    base_p, base_v = base_spk.state(parent, jd)
                    proposed_p = np.asarray(base_p) + np.asarray(offset_p)
                    proposed_v = np.asarray(base_v) + np.asarray(offset_v)
                    et = (jd - 2451545.0) * 86400.0
                    offset_ref, _ = spice.spkgeo(target, et, "J2000", parent)
                    base_ref, _ = spice.spkgeo(parent, et, "J2000", 0)
                    physical_ref, _ = spice.spkgeo(target, et, "J2000", 0)
                    offset_ref = np.asarray(offset_ref)
                    base_ref = np.asarray(base_ref)
                    physical_ref = np.asarray(physical_ref)
                    position_m = float(np.linalg.norm(proposed_p - physical_ref[:3]) * 1000)
                    velocity_mm_s = float(
                        np.linalg.norm(proposed_v / 86400.0 - physical_ref[3:]) * 1e6
                    )
                    base_m = float(np.linalg.norm(base_p - base_ref[:3]) * 1000)
                    offset_m = float(np.linalg.norm(offset_p - offset_ref[:3]) * 1000)
                    composition_m = float(
                        np.linalg.norm(base_ref[:3] + offset_ref[:3] - physical_ref[:3]) * 1000
                    )
                    if not all(
                        math.isfinite(x)
                        for x in (position_m, velocity_mm_s, base_m, offset_m, composition_m)
                    ):
                        raise ValueError(f"{planet}: non-finite residual at JD {jd}")
                    samples.append(
                        {
                            "jd_tdb": jd,
                            "direct_segment_index": row["segment_index"],
                            "position_residual_m": position_m,
                            "velocity_residual_mm_s": velocity_mm_s,
                            "base_residual_m": base_m,
                            "offset_residual_m": offset_m,
                            "spice_composition_residual_m": composition_m,
                            "aria_position_km": proposed_p.tolist(),
                            "aria_velocity_km_day": proposed_v.tolist(),
                        }
                    )
            finally:
                spice.kclear()
        finally:
            base_spk.close()
    finally:
        satellite_spk.close()

    report["samples"] = samples
    report["max_position_residual_m"] = max(x["position_residual_m"] for x in samples)
    report["max_velocity_residual_mm_s"] = max(x["velocity_residual_mm_s"] for x in samples)
    report["evaluator_agreement_pass"] = (
        report["max_position_residual_m"] <= POSITION_GATE_M
        and report["max_velocity_residual_mm_s"] <= VELOCITY_GATE_MM_S
    )
    report["source_identity_approved"] = expected_sha is not None
    report["source_gate_pass"] = (
        coverage["reader_and_coverage_pass"]
        and report["evaluator_agreement_pass"]
        and report["source_identity_approved"]
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--planet", required=True, choices=sorted(TARGETS))
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--satellite", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result: dict[str, Any]
    try:
        record = load_manifest(args.manifest, args.planet)
        result = qualify(args.planet, args.base, args.satellite, record)
        code = 0 if result["evaluator_agreement_pass"] else 1
    except Exception as error:
        result = {
            "body": args.planet,
            "source": str(args.satellite),
            "error": f"{type(error).__name__}: {error}",
            "source_gate_pass": False,
            "evaluator_agreement_pass": False,
            "commercial_release_approval": "NOT APPROVED",
        }
        code = 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if code == 0:
        print(
            f"{args.planet}: evaluator pass; max position "
            f"{result['max_position_residual_m']:.6g} m; velocity "
            f"{result['max_velocity_residual_mm_s']:.6g} mm/s; "
            f"SHA-256 {result['source']['observed_sha256']}; "
            f"source pinned: {result['source_identity_approved']}"
        )
    else:
        print(f"{args.planet}: qualification failed; {result.get('error', result)}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
