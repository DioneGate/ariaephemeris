# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline original-source semantic, identity and full-grid integrity gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import sha256
from acquire_wp56_discovery import load_spec, source_times, validate_response


def verify(root: Path) -> tuple[dict[str, Any], dict[tuple[str, str], list[dict[str, Any]]]]:
    spec_path = root / "specification.json"
    spec = load_spec(spec_path)
    data = json.loads((root / "source.json").read_text())
    if (
        data.get("schema_version") != 1
        or data.get("dataset_id") != "aria-blind-jpl-event-discovery-source-v1"
    ):
        raise ValueError("Unknown frozen source dataset")
    if data["specification_sha256"] != sha256(spec_path.read_bytes()):
        raise ValueError("Source is not bound to the predeclared specification")
    if data["aria_candidate_selection"] or data["physical_accuracy_certified"]:
        raise ValueError("Invalid independence or physical accuracy declaration")
    expected = {(w["id"], b): source_times(spec, w) for w in spec["windows"] for b in w["bodies"]}
    records = data["source_requests"]
    if len(records) != data["original_response_count"] or len(records) != len(expected):
        raise ValueError("Incomplete independent source request list")
    rows = {}
    for record in records:
        key = record["window"], record["body"]
        if key not in expected or key in rows:
            raise ValueError("Duplicate or unexpected source request")
        rows[key] = validate_response(root, record, key[1], expected[key])
    if set(rows) != set(expected) or sum(map(len, rows.values())) != data["ray_count"]:
        raise ValueError("Incomplete original reference sample coverage")
    proof = dict(
        specification_sha256=data["specification_sha256"],
        source_sha256=sha256((root / "source.json").read_bytes()),
        original_response_count=len(records),
        verified_rays=data["ray_count"],
        workload_count=len(spec["workloads"]),
        aria_candidate_selection=False,
    )
    return proof, rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("data/fixtures/horizons/wp56-discovery")
    )
    print(json.dumps(verify(parser.parse_args().source)[0], indent=2, sort_keys=True))
