# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""One-shot, source-preserving Horizons vectors to attribute Jupiter/Pluto residuals.

Acquire each physical centre, system barycentre and Earth against the SSB, and
the same system barycentre directly relative to Earth. No Aria predictions are
used to acquire the independent reference. Responses must be frozen; refresh
only under a new reviewed dataset identifier.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from acquire_horizons_fixtures import (
    API,
    DOC,
    epochs,
    fetch,
    parse_table,
    query,
    quoted,
    sha256,
    source_header,
)

PARENTS = {"jupiter": 5, "pluto": 9}
CENTRES = {"jupiter": 599, "pluto": 999}
ROLES = ("parent_geo", "parent_ssb", "earth_ssb", "centre_ssb")


def specification(body: str, role: str) -> dict[str, str]:
    """Explicit JPL source target/observer, TDB, reference frame and units."""
    if body not in PARENTS or role not in ROLES:
        raise ValueError("Unsupported source-decomposition body or target role")
    params = query(body, "geometric", epochs(body))
    target = (
        PARENTS[body]
        if role.startswith("parent")
        else 399
        if role == "earth_ssb"
        else CENTRES[body]
    )
    params["COMMAND"] = quoted(str(target))
    params["CENTER"] = quoted("500@399" if role == "parent_geo" else "500@0")
    return params


def acquire(root: Path) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "jpl-model-components-v1.json"
    if destination.exists():
        raise FileExistsError(
            "Frozen JPL model components already exist; refuse silent refresh"
        )
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    responses: list[dict[str, Any]] = []
    cases: list[dict[str, Any]] = []
    tasks = [(body, role) for body in PARENTS for role in ROLES]
    for index, (body, role) in enumerate(tasks):
        source = specification(body, role)
        target = int(source["COMMAND"].strip("'"))
        points = epochs(body)
        result, url = fetch(source)
        original = result["result"]
        lines = parse_table(original, target, "geometric", points)
        headers = source_header(original)
        payload = original.encode("utf-8")
        filename = f"{body}-{role}.txt"
        (raw_dir / filename).write_bytes(payload)
        responses.append(
            {
                "body": body,
                "role": role,
                "target_id": target,
                "center_id": 399 if role == "parent_geo" else 0,
                "reference_url": url,
                "reference_parameters": source,
                "source_header": headers,
                "response_signature": result["signature"],
                "raw_file": "raw/" + filename,
                "raw_sha256": sha256(payload),
                "rows": len(lines),
            }
        )
        cases.extend(
            {
                "id": f"ARIA-SOURCE-{body.upper()}-{role.upper()}-{i + 1:02d}",
                "body": body,
                "role": role,
                "jd_tdb": row["jd_tdb"],
                "position_km": row["position_km"],
                "velocity_km_s": row["velocity_km_s"],
                "raw_file": "raw/" + filename,
            }
            for i, row in enumerate(lines)
        )
        print(f"Verified {body}/{role}: {len(lines)} JPL rows; source {headers}", flush=True)
        if index + 1 < len(tasks):
            time.sleep(3)
    metadata = {
        "schema_version": 1,
        "dataset_id": "aria-jpl-model-decomposition-horizons-v1",
        "authority": "NASA/JPL Horizons external reference (not Aria engine output)",
        "api_docs": DOC,
        "api": API,
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Jupiter and Pluto; 25 TDB JDs each; parent vs Earth, parent vs SSB, Earth vs SSB, centre vs SSB",
        "purpose": "Algebraic attribution of WP5.2 geocentric vector differences, including Horizons path consistency",
        "model_matching_claim": False,
        "numerical_commercial_qualification": False,
        "refresh_policy": "new version and separate review only",
        "responses": responses,
        "cases": cases,
        "sample_count": len(cases),
    }
    destination.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if len(responses) != 8 or len(cases) != 200:
        raise ValueError("Incomplete independent source decomposition dataset")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("data/fixtures/horizons/model-components")
    )
    args = parser.parse_args()
    result = acquire(args.output_dir)
    print(f"Archived {result['sample_count']} independent JPL source-component states")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
