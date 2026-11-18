# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline source qualification probe for six physical planet-centre SPK offsets.

This audits supplied, local JPL files; it DOES NOT download kernels or certify
numerical accuracy. The centre offset must be combined with the barycentre
state from the verified Aria DE442s base kernel, not from the satellite file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

# Inclusive 1900-01-01 through 2100-12-31, expressed as a half-open
# numerical window. These are TDB-style SPK JDs, NOT civil UTC input limits.
# TDB minus TT is < 2 ms; live source auditing must retain a boundary margin.
# Enlarge both endpoints by one second: a conservative margin for TT/TDB.
WINDOW_JD_TDB = (2415020.5 - 1 / 86400, 2488434.5 + 1 / 86400)
TARGETS = {
    "mars": (499, 4),
    "jupiter": (599, 5),
    "saturn": (699, 6),
    "uranus": (799, 7),
    "neptune": (899, 8),
    "pluto": (999, 9),
}
SUPPORTED_TYPES = {2, 3}
SUPPORTED_FRAMES = {1}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def coverage_gaps(
    intervals: list[tuple[float, float]],
    window: tuple[float, float] = WINDOW_JD_TDB,
) -> list[list[float]]:
    """Return missing intervals; touching SPK spans provide continuous coverage."""
    start, stop = window
    cursor = start
    missing: list[list[float]] = []
    for lo, hi in sorted(intervals):
        if hi < cursor:
            continue
        if lo > cursor:
            missing.append([cursor, min(lo, stop)])
        cursor = max(cursor, min(hi, stop))
        if cursor >= stop:
            break
    if cursor < stop:
        missing.append([cursor, stop])
    return missing


def inspect_segments(
    segments: list[Any],
    name: str,
    window: tuple[float, float] = WINDOW_JD_TDB,
) -> dict[str, Any]:
    """Inspect direct centre->barycentre segments only; no inferred coverage."""
    target, centre = TARGETS[name]
    rows: list[dict[str, Any]] = []
    valid_intervals: list[tuple[float, float]] = []
    for index, segment in enumerate(segments):
        if segment.target != target or segment.center != centre:
            continue
        row = {
            "segment_index": index,
            "target": segment.target,
            "centre": segment.center,
            "type": segment.data_type,
            "frame": segment.frame,
            "start_jd_tdb": float(segment.start_jd),
            "end_jd_tdb": float(segment.end_jd),
        }
        row["supported_by_current_reader"] = (
            row["type"] in SUPPORTED_TYPES and row["frame"] in SUPPORTED_FRAMES
        )
        rows.append(row)
        if row["supported_by_current_reader"]:
            valid_intervals.append((row["start_jd_tdb"], row["end_jd_tdb"]))
    gaps = coverage_gaps(valid_intervals, window)
    return {
        "body": name,
        "target_id": target,
        "required_centre_id": centre,
        "window_jd_tdb": list(window),
        "direct_segments": rows,
        "supported_coverage_gaps_jd_tdb": gaps,
        "reader_and_coverage_pass": bool(rows) and not gaps,
    }


def sample_state(
    spk: Any, name: str, report: dict[str, Any], base_kernel: Path, jd: float
) -> dict[str, Any]:
    """Combine one selected offset with DE442s; not an independent validation."""
    from ariaephemeris.datasets import verify
    from ariaephemeris.sources import Kernel

    base_manifest = verify(base_kernel)  # Exact DE442s manifest SHA and size.
    rows = [
        row
        for row in report["direct_segments"]
        if row["supported_by_current_reader"]
        and row["start_jd_tdb"] <= jd <= row["end_jd_tdb"]
    ]
    if not rows:
        raise ValueError("No supported direct centre offset covers the sample TDB JD")
    # Match the existing in-file last-segment precedence, while documenting it.
    selected = max(rows, key=lambda r: r["segment_index"])
    seg = spk.segments[selected["segment_index"]]
    off_p, off_v = seg.compute_and_differentiate(jd)
    if seg.data_type == 3:
        off_p, off_v = off_p[:3], off_p[3:] * 86400.0
    with_base = Kernel(base_kernel)
    try:
        bar_p, bar_v = with_base.state(TARGETS[name][1], jd)
    finally:
        with_base.close()
    offset_p = [float(x) for x in off_p]
    offset_v = [float(x) for x in off_v]
    barycentre_p = [float(x) for x in bar_p]
    barycentre_v = [float(x) for x in bar_v]
    return {
        "jd_tdb": jd,
        "selected_segment_index": selected["segment_index"],
        "base_kernel": str(base_kernel),
        "base_dataset_id": base_manifest["dataset_id"],
        "base_sha256_verified": base_manifest["sha256"],
        "offset_position_km": offset_p,
        "offset_velocity_km_day": offset_v,
        "base_barycentre_position_km": barycentre_p,
        "base_barycentre_velocity_km_day": barycentre_v,
        "assembled_centre_position_km": [
            x + y for x, y in zip(offset_p, barycentre_p, strict=True)
        ],
        "assembled_centre_velocity_km_day": [
            x + y for x, y in zip(offset_v, barycentre_v, strict=True)
        ],
        "qualification": "NOT QUALIFIED: sample not compared with independent reference",
    }


def key_value(text: str) -> tuple[str, str]:
    if "=" not in text:
        raise argparse.ArgumentTypeError("Expected body=value")
    name, value = text.split("=", 1)
    if name not in TARGETS or not value:
        raise argparse.ArgumentTypeError(
            "Expected mars|jupiter|saturn|uranus|neptune|pluto=value"
        )
    return name, value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kernel",
        metavar="BODY=FILE",
        action="append",
        required=True,
        type=key_value,
        help="Local satellite SPK file; supply once per planet",
    )
    parser.add_argument(
        "--expected-sha256",
        metavar="BODY=SHA256",
        action="append",
        type=key_value,
        default=[],
        help="Optional independently pinned SHA256 (required for source identity gate)",
    )
    parser.add_argument("--base", type=Path, help="Verified DE442s for sample state")
    parser.add_argument(
        "--sample-jd-tdb",
        type=float,
        default=2451545.0,
        help="Numerical TDB Julian Date, not civil UTC (default J2000)",
    )
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON")
    args = parser.parse_args(argv)

    kernels = dict(args.kernel)
    expected_hashes = dict(args.expected_sha256)
    if len(kernels) != len(args.kernel) or len(expected_hashes) != len(args.expected_sha256):
        parser.error("Duplicate BODY argument; supply one kernel and hash per body")
    if any(name not in kernels for name in expected_hashes):
        parser.error("Expected hash supplied for a body without a kernel")
    if args.require_all and set(kernels) != set(TARGETS):
        parser.error("--require-all requires exactly one kernel for each of six planets")
    if args.base is not None and not args.base.is_file():
        parser.error("Supplied --base does not exist")

    try:
        from jplephem.spk import SPK

        reports: dict[str, Any] = {}
        for name in sorted(kernels):
            path = Path(kernels[name])
            if not path.is_file():
                raise ValueError(f"{name}: file does not exist: {path}")
            observed = sha256(path)
            expected = expected_hashes.get(name)
            spk = SPK.open(str(path))
            try:
                report = inspect_segments(list(spk.segments), name)
                report["source_file"] = str(path)
                report["source_bytes"] = path.stat().st_size
                report["source_sha256_observed"] = observed
                report["source_sha256_expected"] = expected
                report["source_sha256_matches_pinned"] = (
                    expected is not None and observed.lower() == expected.lower()
                )
                if args.base is not None:
                    report["sample"] = sample_state(
                        spk, name, report, args.base, args.sample_jd_tdb
                    )
                reports[name] = report
            finally:
                spk.close()
        evidence = {
            "tool": "tools/datasets/audit_planet_centres.py",
            "authority": "local SPK segment inspection; not numerical release qualification",
            "requested_window_jd_tdb": list(WINDOW_JD_TDB),
            "source_checks": reports,
            "coverage_pass": bool(reports)
            and all(row["reader_and_coverage_pass"] for row in reports.values()),
            "source_identity_pinned": bool(reports)
            and all(row["source_sha256_matches_pinned"] for row in reports.values()),
            "all_six_present": len(reports) == len(TARGETS),
            "independent_reference_comparison": "NOT RUN",
        }
        rendered = json.dumps(evidence, indent=2, sort_keys=True)
        if args.output is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        if not evidence["coverage_pass"] or not evidence["source_identity_pinned"]:
            return 1
        return 0
    except Exception as error:  # CLI boundary: report missing/invalid kernels cleanly.
        print(f"Planet-centre audit failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
