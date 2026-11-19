# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Fully offline authenticity/semantics check of frozen Horizons source vectors."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from acquire_horizons_fixtures import epochs, parse_table, sha256, source_header
from acquire_horizons_model_components import PARENTS, ROLES, specification


def verify(
    root: Path,
    parents: dict[str, int] | None = None,
    filename: str = "jpl-model-components-v1.json",
) -> dict[str, Any]:
    parents = PARENTS if parents is None else parents
    count = len(parents) * len(ROLES) * 25
    requests_count = len(parents) * len(ROLES)
    dataset = json.loads((root / filename).read_text(encoding="utf-8"))
    if dataset.get("schema_version") != 1 or dataset.get("sample_count") != count:
        raise ValueError("Unexpected or incomplete JPL model component dataset")
    if dataset.get("model_matching_claim") is not False:
        raise ValueError("Source acquisition cannot certify a matched physical model")
    if dataset.get("numerical_commercial_qualification") is not False:
        raise ValueError("Source acquisition cannot certify commercial accuracy")
    expected = {(body, role) for body in parents for role in ROLES}
    requests = dataset["responses"]
    if (
        len(requests) != requests_count
        or len({(x["body"], x["role"]) for x in requests}) != requests_count
    ):
        raise ValueError("Missing or duplicate Horizons component query")
    cases = dataset["cases"]
    counts = Counter((case["body"], case["role"]) for case in cases)
    if set(counts) != expected or any(x != 25 for x in counts.values()):
        raise ValueError("Expected exactly 25 independently obtained epochs per component")
    if len({x["id"] for x in cases}) != count:
        raise ValueError("Duplicate component fixture IDs")
    for record in requests:
        body, role = record["body"], record["role"]
        if (body, role) not in expected:
            raise ValueError("Unknown source component request")
        params = specification(body, role, parents)
        if record["reference_parameters"] != params:
            raise ValueError("Requested JPL source vector convention has changed")
        if not record["reference_url"].startswith("https://ssd.jpl.nasa.gov/api/horizons.api?"):
            raise ValueError("Non-JPL external reference URL")
        target = int(params["COMMAND"].strip("'"))
        centre = 399 if role == "parent_geo" else 0
        if target != record["target_id"] or centre != record["center_id"]:
            raise ValueError("Wrong physical target or reference origin")
        raw_path = root / record["raw_file"]
        if not raw_path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unexpected raw source file path")
        raw_bytes = raw_path.read_bytes()
        if sha256(raw_bytes) != record["raw_sha256"]:
            raise ValueError("JPL original response checksum mismatch")
        raw = raw_bytes.decode("utf-8")
        if source_header(raw) != record["source_header"]:
            raise ValueError("Horizons source provenance changed")
        reconstructed = parse_table(raw, target, "geometric", epochs(body))
        selected = [case for case in cases if case["body"] == body and case["role"] == role]
        if len(selected) != 25 or record["rows"] != 25:
            raise ValueError("Incomplete source component rows")
        for original, case in zip(reconstructed, selected, strict=True):
            if (
                original["jd_tdb"] != case["jd_tdb"]
                or original["position_km"] != case["position_km"]
                or original["velocity_km_s"] != case["velocity_km_s"]
                or case["raw_file"] != record["raw_file"]
            ):
                raise ValueError("Derived component state differs from original JPL response")
    return {
        "dataset_id": dataset["dataset_id"],
        "verified_source_responses": len(requests),
        "verified_states": len(cases),
        "source_models": {
            f"{r['body']}/{r['role']}": r["source_header"]["source_solution_labels"]
            for r in requests
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=Path("data/fixtures/horizons/model-components")
    )
    args = parser.parse_args()
    print(json.dumps(verify(args.directory), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
