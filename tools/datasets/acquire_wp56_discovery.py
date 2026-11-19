# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Explicit, serial acquisition of predeclared blind JPL event-search grids.

No Aria imports or candidate event selection. Resumes only SHA-verified archived
responses; an existing completed source manifest is immutable and cannot refresh.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import API, TARGETS, fetch, parse_table, query, sha256, source_header
from wp56_discovery import workloads


def load_spec(path: Path) -> dict[str, Any]:
    spec = json.loads(path.read_text())
    if (
        spec.get("schema_version") != 1
        or spec.get("specification_id") != "aria-independent-event-discovery-v1"
    ):
        raise ValueError("Unknown discovery specification")
    if spec["source_step_days"] != 0.25 or spec["source_padding_days"] != 2:
        raise ValueError("Unreviewed source spacing/padding")
    if spec["workloads"] != workloads(spec):
        raise ValueError("Incomplete or altered declared workload list")
    if spec["physical_accuracy_certified"] or spec["continuous_completeness_proven"]:
        raise ValueError("Specification must not imply physical/continuous certification")
    for window in spec["windows"]:
        if not window["start_jd_tt"] < window["end_jd_tt"]:
            raise ValueError("Invalid benchmark window")
        if not set(window["bodies"]) <= set(TARGETS):
            raise ValueError("Unknown physical target")
    if len({w["id"] for w in spec["windows"]}) != len(spec["windows"]):
        raise ValueError("Duplicate benchmark window")
    return spec


def source_times(spec: dict[str, Any], window: dict[str, Any]) -> list[float]:
    lo = window["start_jd_tt"] - spec["source_padding_days"]
    hi = window["end_jd_tt"] + spec["source_padding_days"]
    n = round((hi - lo) / spec["source_step_days"])
    if not 1 <= n < 10000 or abs(lo + n * spec["source_step_days"] - hi) > 1e-9:
        raise ValueError("Reference range exceeds budget or does not align with grid")
    return [lo + i * spec["source_step_days"] for i in range(n + 1)]


def range_query(body: str, times: list[float]) -> dict[str, str]:
    params = query(body, "apparent", [times[0]])
    for key in ("TLIST", "TLIST_TYPE"):
        del params[key]
    params.update(
        START_TIME=f"'JD{times[0]:.7f}'", STOP_TIME=f"'JD{times[-1]:.7f}'", STEP_SIZE="'6 h'"
    )
    return params


def validate_response(
    root: Path, record: dict[str, Any], body: str, times: list[float]
) -> list[dict[str, Any]]:
    params = range_query(body, times)
    if record["parameters"] != params or record["source_url"] != API + "?" + urllib.parse.urlencode(
        params
    ):
        raise ValueError("Changed geocentric quantity45 ICRF/TT source semantics")
    signature = record["response_signature"]
    if str(signature.get("version")) not in (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
    ) or "Horizons" not in signature.get("source", ""):
        raise ValueError("Unexpected external source signature")
    path = (root / record["raw_file"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Raw response outside fixture directory")
    raw_bytes = path.read_bytes()
    if sha256(raw_bytes) != record["raw_sha256"]:
        raise ValueError("Original JPL response SHA-256 mismatch")
    raw = raw_bytes.decode("utf-8")
    header = source_header(raw)
    if header != record["source_header"] or "(399)" not in header["centre"]:
        raise ValueError("Changed target/observer/source labels")
    if not header["source_solution_labels"] or header["source_solution_labels"] == "NOT STATED":
        raise ValueError("Missing source model identity")
    rows = parse_table(raw, TARGETS[body], "apparent", times)
    if record["row_count"] != len(rows) or [r["jd_tt"] for r in rows] != times:
        raise ValueError("Missing, duplicated or shifted source epochs")
    return rows


def acquire(root: Path) -> dict[str, Any]:
    file = root / "source.json"
    if file.exists():
        raise FileExistsError("Frozen source manifest exists; refuse live refresh")
    spec_path = root / "specification.json"
    spec = load_spec(spec_path)
    (root / "raw").mkdir(parents=True, exist_ok=True)
    requests = []
    for window in spec["windows"]:
        times = source_times(spec, window)
        for body in window["bodies"]:
            stem = f"{window['id']}-{body}"
            receipt = root / "raw" / f"{stem}.json"
            if receipt.exists():
                record = json.loads(receipt.read_text())
                validate_response(root, record, body, times)
            else:
                params = range_query(body, times)
                payload, url = fetch(params)
                raw = payload["result"].encode("utf-8")
                raw_file = f"raw/{stem}.txt"
                (root / raw_file).write_bytes(raw)
                record = dict(
                    window=window["id"],
                    body=body,
                    parameters=params,
                    source_url=url,
                    response_signature=payload["signature"],
                    source_header=source_header(raw.decode()),
                    raw_file=raw_file,
                    raw_sha256=sha256(raw),
                    row_count=len(times),
                )
                validate_response(root, record, body, times)
                receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
                time.sleep(1)  # Serial fair use; never parallel public API calls.
            if record["window"] != window["id"] or record["body"] != body:
                raise ValueError("Changed resumed source identity")
            requests.append(record)
            print(f"Archived {stem}: {len(times)} original JPL rays", flush=True)
    result = dict(
        schema_version=1,
        dataset_id="aria-blind-jpl-event-discovery-source-v1",
        specification_sha256=sha256(spec_path.read_bytes()),
        source_requests=requests,
        original_response_count=len(requests),
        ray_count=sum(r["row_count"] for r in requests),
        aria_candidate_selection=False,
        physical_accuracy_certified=False,
    )
    file.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("data/fixtures/horizons/wp56-discovery")
    )
    acquire(parser.parse_args().source)
