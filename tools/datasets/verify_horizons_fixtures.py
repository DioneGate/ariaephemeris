# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline integrity and semantic validation for immutable Horizons WP5.1 fixtures."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from acquire_horizons_fixtures import TARGETS, epochs, parse_table, sha256, source_header


def validate(root: Path, *, expected_count: int = 300) -> dict[str, object]:
    manifest = json.loads((root / "horizons-reference-v1.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("case_count") != expected_count:
        raise ValueError("Fixture manifest version or case count incorrect")
    if manifest["scope"]["commercial_accuracy_qualified"] is not False:
        raise ValueError("Reference acquisition must not imply numerical qualification")
    if manifest["scope"]["comparison_status"] != "NOT COMPARED: WP5.2 forthcoming":
        raise ValueError("Reference acquisition is not a comparison/acceptance test")
    queries = manifest["raw_queries"]
    cases = manifest["cases"]
    if len(queries) * 25 != len(cases) or len(queries) != 12:
        raise ValueError("Expected exactly 12 queries and 300 fixture rows")
    ids = [case["id"] for case in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate astronomical fixture identifiers")
    counts = Counter((case["body"], case["kind"]) for case in cases)
    if set(counts) != {(body, kind) for body in TARGETS for kind in ("geometric", "apparent")}:
        raise ValueError("One or more required body/mode combinations absent")
    if any(n != 25 for n in counts.values()):
        raise ValueError("Every body/mode must contain exactly 25 samples")
    for record in queries:
        body, kind = record["body"], record["kind"]
        if body not in TARGETS or kind not in ("geometric", "apparent"):
            raise ValueError("Unexpected body or query type")
        if record["target_id"] != TARGETS[body] or record["row_count"] != 25:
            raise ValueError("Incorrect target identity or row count")
        raw_path = root / record["raw_file"]
        if not raw_path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Invalid fixture path")
        data = raw_path.read_bytes()
        if sha256(data) != record["raw_sha256"]:
            raise ValueError("Raw JPL response has been changed")
        raw = data.decode("utf-8")
        if source_header(raw) != record["source_header"]:
            raise ValueError("Horizons header has been changed")
        if not record["request_url"].startswith("https://ssd.jpl.nasa.gov/api/horizons.api?"):
            raise ValueError("Unexpected API endpoint")
        params = record["request_parameters"]
        if params.get("CENTER") != "'500@399'" or params.get("COMMAND") != f"'{TARGETS[body]}'":
            raise ValueError("Unexpected query target or origin")
        if params.get("REF_SYSTEM") != "'ICRF'" or params.get("TLIST_TYPE") != "'JD'":
            raise ValueError("Unspecified coordinate reference")
        if kind == "geometric":
            if not (
                params.get("EPHEM_TYPE") == "VECTORS"
                and params.get("TIME_TYPE") == "TDB"
                and params.get("VEC_CORR") == "NONE"
                and params.get("REF_PLANE") == "FRAME"
                and params.get("VEC_TABLE") == "2"
                and params.get("OUT_UNITS") == "KM-S"
            ):
                raise ValueError("Geometric reference query parameters drifted")
        else:
            if not (
                params.get("EPHEM_TYPE") == "OBSERVER"
                and params.get("TIME_TYPE") == "TT"
                and params.get("QUANTITIES") == "'45'"
                and params.get("APPARENT") == "AIRLESS"
                and params.get("ANG_FORMAT") == "DEG"
            ):
                raise ValueError("Apparent reference query parameters drifted")
        original = parse_table(raw, TARGETS[body], kind, epochs(body))
        selected = [case["reference"] for case in cases if (case["body"], case["kind"]) == (body, kind)]
        if original != selected:
            raise ValueError("Structured fixture values differ from raw source")
        if kind == "geometric":
            if any(
                any(not math.isfinite(x) for x in row["position_km"] + row["velocity_km_s"])
                for row in original
            ):
                raise ValueError("Non-finite geometric state")
        else:
            if any(not 0 <= row["inertial_apparent_ra_deg"] < 360 for row in original):
                raise ValueError("Invalid inertial apparent RA")
    return {
        "dataset_id": manifest["dataset_id"],
        "raw_responses_verified": len(queries),
        "fixture_rows_verified": len(cases),
        "source_labels": {
            f"{row['body']}/{row['kind']}": row["source_header"]["source_solution_labels"]
            for row in queries
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("data/fixtures/horizons"))
    args = parser.parse_args()
    result = validate(args.directory)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
