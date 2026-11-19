# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Acquire JPL-only fine-time observations bracketing 22 existing JPL roots.

The 22 nominal root times are the independent JPL cubic roots in the already
frozen WP5.5 report, NOT Aria event times. New original NASA/JPL observations
are sampled at +/-15 and +/-30 TT seconds. Stations are *independently*
differentiated using five JPL directions at every fine-time observation.
This is a one-shot source operation and cannot run during normal tests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import TARGETS, fetch, parse_table, query, sha256, source_header
from verify_wp55_events import validate as validate_wp55
from wp55_event_math import BODY_ORDER, SECONDS_PER_DAY, stamp, station_stencil

OFFSETS_SECONDS = (-30, -15, 15, 30)
CHUNK = 45


def sample_days(jd: float) -> list[float]:
    times = [stamp(jd + delta / SECONDS_PER_DAY) for delta in OFFSETS_SECONDS]
    if len(set(times)) != len(times):
        raise ValueError("Refinement TT epochs collapse onto each other")
    return times


def acquire(source: Path, wp54: Path, measured: Path, output: Path) -> dict[str, Any]:
    file = output / "wp55-jpl-fine-root-brackets-v1.json"
    if file.exists():
        raise FileExistsError("Original fine-root JPL dataset already frozen")
    if validate_wp55(source, wp54)["verified_events"] != 22:
        raise ValueError("Upstream 22 original JPL reference event grids not valid")
    measured_bytes = measured.read_bytes()
    old = json.loads(measured_bytes)
    if old["event_case_count"] != 22 or old["commercial_event_timing_qualified"]:
        raise ValueError("Missing/incorrect original independent JPL event-root report")
    cases = []
    wanted: dict[str, set[float]] = {body: set() for body in BODY_ORDER}
    for row in old["rows"]:
        jd = row["jpl_reference"]["jd_tt"]
        times = sample_days(jd)
        stencils = [station_stencil(t) for t in times] if row["kind"] == "station" else []
        item = {
            "event_id": row["event_id"],
            "kind": row["kind"],
            "body": row["body"],
            "other_body": row["other_body"],
            "goal_deg": row["goal_deg"],
            "jpl_original_interpolated_jd_tt": jd,
            "fine_offsets_tt_seconds": list(OFFSETS_SECONDS),
            "fine_jd_tt": times,
            "station_rate_stencils_jd_tt": stencils,
            "origin": "independently solved source-only JPL root; NOT Aria event time",
        }
        for body in (row["body"], row["other_body"]):
            if body is None:
                continue
            wanted[body].update(times)
            if item["kind"] == "station":
                for stencil in stencils:
                    wanted[body].update(stencil)
        cases.append(item)
    if len(cases) != 22 or len({x["event_id"] for x in cases}) != 22:
        raise ValueError("Expected 22 independent JPL fine-root cases")
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    requests: list[dict[str, Any]] = []
    rays: list[dict[str, Any]] = []
    for body in BODY_ORDER:
        dates = sorted(wanted[body])
        for index, start in enumerate(range(0, len(dates), CHUNK), 1):
            chunk = dates[start : start + CHUNK]
            params = query(body, "apparent", chunk)
            payload, url = fetch(params)
            raw_text = payload["result"]
            records = parse_table(raw_text, TARGETS[body], "apparent", chunk)
            original_bytes = raw_text.encode("utf-8")
            filename = f"raw/{body}-fine-{index:02d}.txt"
            (output / filename).write_bytes(original_bytes)
            requests.append(
                {
                    "body": body,
                    "target_id": TARGETS[body],
                    "centre_id": 399,
                    "parameters": params,
                    "reference_url": url,
                    "source_header": source_header(raw_text),
                    "response_signature": payload["signature"],
                    "original_raw_file": filename,
                    "original_raw_sha256": sha256(original_bytes),
                    "rows": len(records),
                }
            )
            rays.extend({"body": body, "raw_file": filename, **row} for row in records)
            print(f"JPL fine-root {body}: {len(records)} new independently sampled directions", flush=True)
            if body != BODY_ORDER[-1] or start + CHUNK < len(dates):
                time.sleep(3)
    expected = sum(len(v) for v in wanted.values())
    if len(rays) != expected or len({(x["body"], x["jd_tt"]) for x in rays}) != expected:
        raise ValueError("JPL source fine-root reference incomplete or duplicated")
    result = {
        "schema_version": 1,
        "dataset_id": "aria-jpl-planetary-event-fine-root-bracketing-v1",
        "parent_event_source_dataset_id": old["source_fixture_id"],
        "parent_event_comparison_sha256": hashlib.sha256(measured_bytes).hexdigest(),
        "independent_selection": "JPL-only interpolated reference roots; no Aria event estimates used",
        "source": "NASA/JPL Horizons OBSERVER quantity 45 airless apparent geocentric ICRF RA/Dec at TT",
        "frame_standard_dependency": "IAU2006/2000A direct SOFA/ERFA; shared ERFA implementation with Aria",
        "fine_offsets_tt_seconds": list(OFFSETS_SECONDS),
        "station_rate_stencil_step_tt_days": 0.0125,
        "original_response_count": len(requests),
        "ray_count": len(rays),
        "event_count": len(cases),
        "requests": requests,
        "rays": rays,
        "cases": cases,
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "absolute_root_accuracy_certified": False,
        "unique_root_completeness_certified": False,
        "commercial_release_qualified": False,
    }
    file.write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("data/fixtures/horizons/wp55-events"))
    p.add_argument("--wp54", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    p.add_argument("--comparison", type=Path, default=Path("docs/validation/wp55-independent-event-roots.json"))
    p.add_argument("--output", type=Path, default=Path("data/fixtures/horizons/wp55-root-refinement"))
    a = p.parse_args()
    result = acquire(a.source, a.wp54, a.comparison, a.output)
    print(f"New original JPL fine-root directions: {result['ray_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
