# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline fail-closed authenticity verification of external Horizons WP5.4 rays."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import (
    TARGETS,
    parse_table,
    query,
    sha256,
    source_header,
)
from acquire_wp54_tropical import (
    BODIES,
    NUM_BASE,
    STENCIL,
    STEP,
    stamp,
)
from verify_horizons_fixtures import validate as validate_wp51


def verify(root: Path, wp51_root: Path) -> dict[str, Any]:
    original = validate_wp51(wp51_root)
    if original["fixture_rows_verified"] != 300:
        raise ValueError("WP5.1 external reference must be valid")
    source = json.loads(
        (root / "wp54-horizons-tropical-stencils-v1.json").read_text(encoding="utf-8")
    )
    if (
        source.get("schema_version") != 1
        or source.get("case_count") != 186
        or source.get("ray_count") != 930
        or source.get("new_jpl_reference_rows") != 780
        or source.get("cases_per_body") != 31
    ):
        raise ValueError("Incorrect WP5.4 source schema/sample coverage")
    if source["commercial_accuracy_certified"] is not False:
        raise ValueError("Raw source acquisition cannot certify physical accuracy")
    if source["tt_rate_step_days"] != STEP or source["stencil_offsets"] != list(STENCIL):
        raise ValueError("Independent longitude-rate finite difference conventions changed")
    if source["source_wp51_id"] != "aria-horizons-physical-centre-reference-v1":
        raise ValueError("Different original source dataset")
    if (
        source["scientific_status"]
        != "INDEPENDENT_INERTIAL_RAYS_WITH_SHARED_IAU_STANDARD_TRANSFORM"
    ):
        raise ValueError("Scientific independence scope is missing")
    manifest = json.loads((wp51_root / "horizons-reference-v1.json").read_text(encoding="utf-8"))
    original_rays = {
        (case["body"], case["reference"]["jd_tt"]): (
            case["reference"]["inertial_apparent_ra_deg"],
            case["reference"]["inertial_apparent_dec_deg"],
            "wp51/" + case["source_raw_file"],
        )
        for case in manifest["cases"]
        if case["kind"] == "apparent"
    }
    if len(original_rays) != 150:
        raise ValueError("Original independent Horizons baseline incomplete")
    ray_map: dict[tuple[str, float], dict[str, Any]] = {}
    for row in source["rays"]:
        key = (row["body"], row["jd_tt"])
        if row["body"] not in TARGETS or key in ray_map:
            raise ValueError("Duplicate or unrecognised JPL ray sample")
        ra = row["inertial_apparent_ra_deg"]
        dec = row["inertial_apparent_dec_deg"]
        if not all(math.isfinite(x) for x in (row["jd_tt"], ra, dec)):
            raise ValueError("Non-finite celestial source ray")
        if not 0 <= ra < 360 or not -90 <= dec <= 90:
            raise ValueError("Invalid ICRF celestial coordinates")
        ray_map[key] = row
    if len(ray_map) != 930:
        raise ValueError("Exactly 930 celestial directions required")

    matched: set[tuple[str, float]] = set()
    for (body, jd), (ra, dec, file) in original_rays.items():
        if (body, jd) not in ray_map:
            raise ValueError("Original WP5.1 source directions missing")
        entry = ray_map[(body, jd)]
        if (entry["inertial_apparent_ra_deg"], entry["inertial_apparent_dec_deg"]) != (
            ra,
            dec,
        ) or entry["source_raw_file"] != file:
            raise ValueError("Original JPL source numerical value was changed")
        matched.add((body, jd))

    requests = source["source_requests"]
    if len(requests) != 18 or set(r["body"] for r in requests) != set(BODIES):
        raise ValueError("Expected exactly 18 serial JPL reference queries")
    declared: set[tuple[str, float]] = set()
    for record in requests:
        body = record["body"]
        if record["target_id"] != TARGETS[body] or record["rows"] > 45:
            raise ValueError("Wrong JPL target or oversized request")
        if not record["query_url"].startswith("https://ssd.jpl.nasa.gov/api/horizons.api?"):
            raise ValueError("Unrecognised independent source endpoint")
        q = record["query"]
        epochs = [float(x) for x in re.findall(r"'([0-9]+\.[0-9]+)'", q["TLIST"])]
        if not epochs or record["rows"] != len(epochs):
            raise ValueError("Wrong number of explicit reference epochs")
        if query(body, "apparent", epochs) != q:
            raise ValueError("Horizons ICRF/TT/quantity-45 correction convention changed")
        file = root / record["raw_file"]
        if not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("External reference path escapes dataset")
        payload = file.read_bytes()
        if sha256(payload) != record["sha256"]:
            raise ValueError("Original JPL source SHA-256 mismatch")
        raw = payload.decode("utf-8")
        if source_header(raw) != record["header"]:
            raise ValueError("Original JPL physical model/observer headers altered")
        points = parse_table(raw, TARGETS[body], "apparent", epochs)
        for item in points:
            key = (body, item["jd_tt"])
            if key in declared or key in matched:
                raise ValueError("Repeated or substituted independent Horizons sample")
            row = ray_map[key]
            if (
                row["inertial_apparent_ra_deg"] != item["inertial_apparent_ra_deg"]
                or row["inertial_apparent_dec_deg"] != item["inertial_apparent_dec_deg"]
                or row["source_raw_file"] != record["raw_file"]
            ):
                raise ValueError("Reference vector differs from archived JPL original")
            declared.add(key)
    if len(declared) != 780 or declared | matched != set(ray_map):
        raise ValueError("Some celestial source samples lack raw independent provenance")

    counts = Counter((case["body"], case["category"]) for case in source["cases"])
    if len({x["id"] for x in source["cases"]}) != 186:
        raise ValueError("Duplicate chart fixture ID")
    coverage: set[tuple[str, float]] = set()
    for body in BODIES:
        if (
            counts[(body, "baseline")] != NUM_BASE
            or counts[(body, "station")] != 3
            or counts[(body, "ingress")] != 3
            or len(source["critical_candidates"][body]) != 2
        ):
            raise ValueError("Every planet needs base, station and ingress stress tests")
    for case in source["cases"]:
        body = case["body"]
        if case["target_id"] != TARGETS[body]:
            raise ValueError("Not a physical planet-centre chart")
        stencil = [stamp(case["jd_tt"] + k * STEP) for k in STENCIL]
        if stencil != case["stencil_jd_tt"]:
            raise ValueError("Missing or distorted TT derivative stencil")
        if not all((body, x) in ray_map for x in stencil):
            raise ValueError("No independent JPL coordinate for a rate derivative time")
        coverage.update((body, x) for x in stencil)
        if case["category"] != "baseline":
            nomination = case["nomination"]
            if nomination["candidate_source"] != "Aria nominated only (not independent reference)":
                raise ValueError("Station/ingress selection independence mislabelled")
            if not (2459945.5 <= nomination["jd_tt"] <= 2461040.5):
                raise ValueError("Critical sample not within declared stress scan")
    if coverage != set(ray_map):
        raise ValueError("Unreferenced Horizons data in qualification source")

    return {
        "dataset_id": source["dataset_id"],
        "verified_existing_wp51_rays": len(matched),
        "verified_new_jpl_rays": len(declared),
        "verified_critical_and_baseline_chart_cases": len(source["cases"]),
        "verified_original_jpl_responses": len(requests),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    parser.add_argument("--wp51", type=Path, default=Path("data/fixtures/horizons"))
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.wp51), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
