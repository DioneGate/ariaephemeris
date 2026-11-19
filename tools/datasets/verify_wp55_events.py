# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Fully offline authenticity and coverage gate for independent WP5.5 JPL events."""

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
from acquire_horizons_fixtures import TARGETS, parse_table, query, sha256, source_header
from verify_wp54_tropical import verify as verify_wp54
from wp55_event_math import BODY_ORDER, GRID_STEP_DAYS, PAIRS, grid, station_stencil


def validate(root: Path, wp54_root: Path) -> dict[str, Any]:
    if verify_wp54(wp54_root, wp54_root.parent)["verified_critical_and_baseline_chart_cases"] != 186:
        raise ValueError("Upstream WP5.4 independent source not verified")
    data = json.loads((root / "wp55-horizons-event-roots-v1.json").read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("case_count") != 22:
        raise ValueError("Wrong independent JPL event source identity/count")
    if data["absolute_event_timing_qualified"] or data["commercial_release_qualified"]:
        raise ValueError("External source data must never assert physical release acceptance")
    if data["sampling"]["grid_step_tt_days"] != GRID_STEP_DAYS:
        raise ValueError("Changed event sampling conventions")
    if data["sampling"]["interpolation_accuracy_not_proven"] is not True:
        raise ValueError("Unsafe implied numerical interpolation error bound")
    wp54 = json.loads(
        (wp54_root / "wp54-horizons-tropical-stencils-v1.json").read_text(encoding="utf-8")
    )
    if data["wp54_source_dataset_id"] != wp54["dataset_id"]:
        raise ValueError("Mismatched independent JPL source version")
    samples = data["rays"]
    mapping: dict[tuple[str, float], dict[str, Any]] = {}
    for value in samples:
        body = value["body"]
        key = (body, value["jd_tt"])
        if (
            body not in TARGETS
            or key in mapping
            or not all(
                math.isfinite(value[z])
                for z in ("jd_tt", "inertial_apparent_ra_deg", "inertial_apparent_dec_deg")
            )
            or not (0 <= value["inertial_apparent_ra_deg"] < 360)
            or not (-90 <= value["inertial_apparent_dec_deg"] <= 90)
        ):
            raise ValueError("Missing/duplicate/nonfinite original JPL apparent direction")
        mapping[key] = value
    if len(mapping) != data["ray_count"]:
        raise ValueError("JPL independent direction count mismatch")
    requests = data["source_requests"]
    if len(requests) != data["original_response_count"]:
        raise ValueError("Original source request count mismatch")
    requested: set[tuple[str, float]] = set()
    for response in requests:
        body = response["body"]
        if body not in TARGETS or response["target_id"] != TARGETS[body]:
            raise ValueError("Incorrect physical planet centre source")
        if response["centre_id"] != 399:
            raise ValueError("Reference query must be Earth geocentric")
        params = response["parameters"]
        epochs = [float(x) for x in re.findall(r"'([0-9]+\.[0-9]+)'", params["TLIST"])]
        if not (1 <= len(epochs) <= 45) or params != query(body, "apparent", epochs):
            raise ValueError("Changed JPL airless apparent quantity45 ICRF TT convention")
        if response["row_count"] != len(epochs):
            raise ValueError("Incomplete Horizons date list")
        if not response["source_url"].startswith("https://ssd.jpl.nasa.gov/api/horizons.api?"):
            raise ValueError("Unrecognised JPL external source host")
        path = (root / response["raw_file"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Source raw text path outside data root")
        payload = path.read_bytes()
        if sha256(payload) != response["raw_sha256"]:
            raise ValueError("Original NASA/JPL source byte digest changed")
        raw = payload.decode("utf-8")
        if source_header(raw) != response["source_header"]:
            raise ValueError("Original source target/observer model provenance altered")
        original = parse_table(raw, TARGETS[body], "apparent", epochs)
        for row in original:
            key = (body, row["jd_tt"])
            if key not in mapping or key in requested:
                raise ValueError("Missing/duplicated original JPL response row")
            entry = mapping[key]
            if (
                row["inertial_apparent_ra_deg"] != entry["inertial_apparent_ra_deg"]
                or row["inertial_apparent_dec_deg"] != entry["inertial_apparent_dec_deg"]
                or entry["raw_file"] != response["raw_file"]
            ):
                raise ValueError("Independent JPL observer ray differs from source text")
            requested.add(key)
    if requested != set(mapping):
        raise ValueError("Some numerical direction records lack original JPL provenance")

    cases = data["cases"]
    counts = Counter(row["kind"] for row in cases)
    if counts != {"station": 6, "ingress": 6, "conjunction": 5, "opposition": 5}:
        raise ValueError("Required 22 event kinds/physical centres are incomplete")
    expected = {
        (kind, body, None) for kind in ("station", "ingress") for body in BODY_ORDER
    } | {
        (kind, first, second) for kind in ("conjunction", "opposition") for first, second in PAIRS
    }
    actual = {(row["kind"], row["body"], row["other_body"]) for row in cases}
    if actual != expected or len({row["event_id"] for row in cases}) != len(cases):
        raise ValueError("Missing or duplicate physical-centre event identity")
    consumed: set[tuple[str, float]] = set()
    for case in cases:
        if not (2459945.5 <= case["nominated_jd_tt"] <= 2461040.5):
            raise ValueError("Event time nominated outside declared 2023-2025 scope")
        if case["jd_tt_grid"] != grid(case["nominated_jd_tt"]):
            raise ValueError("Wrong nine-node TT root time grid")
        if len(case["jd_tt_grid"]) != 9:
            raise ValueError("Missing independently sampled root bracket")
        if case["kind"] == "ingress":
            if case["goal_deg"] not in range(0, 360, 30):
                raise ValueError("Ingress requires explicit 30-degree tropical cusp")
        elif case["kind"] in ("conjunction", "opposition"):
            if case["goal_deg"] != (0 if case["kind"] == "conjunction" else 180):
                raise ValueError("Incorrect astronomical pair-event angular goal")
        elif case["goal_deg"] is not None:
            raise ValueError("Station has no zodiac phase goal")
        for body in (case["body"], case["other_body"]):
            if body is None:
                continue
            for jd in case["jd_tt_grid"]:
                consumed.add((body, jd))
                if (body, jd) not in mapping:
                    raise ValueError("Missing JPL event root reference date")
            if case["kind"] == "station":
                expected_stencils = [station_stencil(t) for t in case["jd_tt_grid"]]
                if case["reference_rate_stencils"] != expected_stencils:
                    raise ValueError("Incorrect independent signed longitude-rate stencil")
                for stencil in expected_stencils:
                    for jd in stencil:
                        if (body, jd) not in mapping:
                            raise ValueError("Missing independent JPL station rate input")
                        consumed.add((body, jd))
            elif case["reference_rate_stencils"]:
                raise ValueError("Nonstation event must not add rate stencil")
    if consumed != set(mapping):
        raise ValueError("Unreferenced/missing original JPL source rays in event grid")
    return {
        "source_dataset_id": data["dataset_id"],
        "verified_events": len(cases),
        "verified_original_responses": len(requests),
        "verified_reference_rays": len(mapping),
        "per_kind": dict(counts),
        "commercial_release_qualified": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("data/fixtures/horizons/wp55-events"))
    p.add_argument("--wp54", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    a = p.parse_args()
    print(json.dumps(validate(a.source, a.wp54), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
