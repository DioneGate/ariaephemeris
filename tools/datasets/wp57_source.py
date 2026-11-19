# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Explicit original-source capture and offline integrity for RM-001/010.

All dates originate in the predeclared WP5.1 policy or JPL-only WP5.6 catalogue.
No Aria calculation or event time is used to choose external reference dates.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import (
    API,
    TARGETS,
    epochs,
    fetch,
    parse_table,
    query,
    sha256,
    source_header,
)
from acquire_horizons_model_components import ROLES, specification
from verify_horizons_model_components import verify as verify_components
from verify_wp56_discovery import verify as verify_wp56

REMAINING = {"mars": 4, "saturn": 6, "uranus": 7, "neptune": 8}
WP56_REPORT = Path("docs/validation/wp56-independent-event-discovery.json")
DEFAULT_ROOT = Path("data/fixtures/horizons/wp57-uncertainty")


def load_spec(root: Path) -> dict[str, Any]:
    spec = json.loads((root / "specification.json").read_text())
    if (
        spec.get("schema_version") != 1
        or spec.get("specification_id") != "aria-model-uncertainty-v1"
    ):
        raise ValueError("Unknown uncertainty specification")
    if spec["remaining_parents"] != REMAINING or spec["physical_accuracy_certified"]:
        raise ValueError("Incorrect source scope or physical accuracy claim")
    if sha256(WP56_REPORT.read_bytes()) != spec["wp56_report_sha256"]:
        raise ValueError("Original 009 report changed")
    previous = json.loads(WP56_REPORT.read_text())
    expected = []
    for row in previous["records"]:
        if row["workload"]["kind"] == "station":
            for i, event in enumerate(row["reference_events"]):
                expected.append(
                    dict(
                        id=f"{row['workload']['id']}:{i}",
                        body=event["body"],
                        direction=event["direction"],
                        jd_tt=round(event["jd_tt"], 7),
                        workload_id=row["workload"]["id"],
                        reference_index=i,
                    )
                )
    if spec["station_centres"] != expected or len(expected) != 36:
        raise ValueError("Station centres must come only from the original JPL discovery catalogue")
    if spec["station_source_step_days"] != 0.015625 or spec["station_radius_days"] != 0.5:
        raise ValueError("Changed independent station sampling policy")
    return spec


def station_times(spec: dict[str, Any], case: dict[str, Any]) -> list[float]:
    return [round(case["jd_tt"] + i * spec["station_source_step_days"], 7) for i in range(-32, 33)]


def wanted_stations(spec: dict[str, Any]) -> dict[str, list[float]]:
    dates: dict[str, set[float]] = {b: set() for b in TARGETS}
    for case in spec["station_centres"]:
        dates[case["body"]].update(station_times(spec, case))
    return {b: sorted(values) for b, values in dates.items()}


def validate_receipt(
    root: Path,
    record: dict[str, Any],
    params: dict[str, str],
    target: int,
    kind: str,
    dates: list[float],
) -> list[dict[str, Any]]:
    if record["parameters"] != params or record["url"] != API + "?" + urllib.parse.urlencode(
        params
    ):
        raise ValueError("Changed original source request semantics")
    path = (root / record["raw_file"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Original source path escapes fixture root")
    payload = path.read_bytes()
    if sha256(payload) != record["raw_sha256"]:
        raise ValueError("Original source checksum mismatch")
    raw = payload.decode("utf-8")
    signature = record["response_signature"]
    if str(signature.get("version")) not in (
        "1.0",
        "1.1",
        "1.2",
        "1.3",
    ) or "Horizons" not in signature.get("source", ""):
        raise ValueError("Unrecognised original source signature")
    header = raw.split("$$SOE", 1)[0]
    provenance = source_header(raw)
    centre = int(params["CENTER"].strip("'").split("@")[-1])
    if provenance != record["source_header"] or not re.search(
        r"\(" + str(centre) + r"\)", provenance["centre"]
    ):
        raise ValueError("Changed target/observer/model source identity")
    if kind == "geometric":
        if not all(
            text in header for text in ("JDTDB", "GEOMETRIC cartesian states", "ICRF", "KM-S")
        ):
            raise ValueError("Geometric ICRF/TDB/km-s source convention mismatch")
    elif not all(
        text in header
        for text in ("JDTT", "RA_(ICRF-a-app)", "DEC_(ICRF-a-app)", "NO (AIRLESS)", "GEOCENTRIC")
    ):
        raise ValueError("Apparent ICRF/TT/airless geocentric source convention mismatch")
    rows = parse_table(raw, target, kind, dates)
    key = "jd_tdb" if kind == "geometric" else "jd_tt"
    if len(rows) != record["row_count"] or [r[key] for r in rows] != dates:
        raise ValueError("Incomplete, duplicate or shifted original source epochs")
    return rows


def capture(
    root: Path, stem: str, params: dict[str, str], target: int, kind: str, dates: list[float]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    receipt = root / "raw" / f"{stem}.json"
    if receipt.exists():
        record = json.loads(receipt.read_text())
    else:
        payload, url = fetch(params)
        raw = payload["result"].encode("utf-8")
        filename = f"raw/{stem}.txt"
        (root / filename).write_bytes(raw)
        record = dict(
            parameters=params,
            url=url,
            raw_file=filename,
            raw_sha256=sha256(raw),
            source_header=source_header(raw.decode()),
            response_signature=payload["signature"],
            row_count=len(dates),
        )
        validate_receipt(root, record, params, target, kind, dates)
        receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        time.sleep(1)
    rows = validate_receipt(root, record, params, target, kind, dates)
    print(f"Original JPL {stem}: {len(rows)} source rows verified", flush=True)
    return record, rows


def acquire(root: Path) -> None:
    if (root / "source.json").exists():
        raise FileExistsError("Frozen uncertainty dataset exists; refuse refresh")
    spec = load_spec(root)
    verify_wp56(Path("data/fixtures/horizons/wp56-discovery"))
    (root / "raw").mkdir(parents=True, exist_ok=True)
    responses, cases = [], []
    for body in REMAINING:
        for role in ROLES:
            params = specification(body, role, REMAINING)
            target = int(params["COMMAND"].strip("'"))
            record, rows = capture(
                root, f"{body}-{role}", params, target, "geometric", epochs(body)
            )
            responses.append(
                dict(
                    body=body,
                    role=role,
                    target_id=target,
                    center_id=399 if role == "parent_geo" else 0,
                    reference_url=record["url"],
                    reference_parameters=params,
                    source_header=record["source_header"],
                    response_signature=record["response_signature"],
                    raw_file=record["raw_file"],
                    raw_sha256=record["raw_sha256"],
                    rows=len(rows),
                )
            )
            cases.extend(
                dict(
                    id=f"WP57-{body}-{role}-{i}",
                    body=body,
                    role=role,
                    raw_file=record["raw_file"],
                    **r,
                )
                for i, r in enumerate(rows)
            )
    components = dict(
        schema_version=1,
        dataset_id="aria-four-remaining-model-components-v1",
        model_matching_claim=False,
        numerical_commercial_qualification=False,
        responses=responses,
        cases=cases,
        sample_count=len(cases),
    )
    (root / "components.json").write_text(json.dumps(components, indent=2, sort_keys=True) + "\n")
    station_requests = []
    for body, dates in wanted_stations(spec).items():
        for first in range(0, len(dates), 45):
            subset = dates[first : first + 45]
            params = query(body, "apparent", subset)
            record, _ = capture(
                root, f"{body}-station-{first // 45:02d}", params, TARGETS[body], "apparent", subset
            )
            station_requests.append(dict(body=body, **record))
    source = dict(
        schema_version=1,
        dataset_id="aria-model-uncertainty-original-source-v1",
        specification_sha256=sha256((root / "specification.json").read_bytes()),
        components_sha256=sha256((root / "components.json").read_bytes()),
        station_requests=station_requests,
        station_ray_count=sum(r["row_count"] for r in station_requests),
        aria_station_nomination=False,
        absolute_physical_uncertainty_bound=None,
    )
    (root / "source.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n")
    verify(root)


def verify(root: Path) -> tuple[dict[str, Any], dict[tuple[str, float], dict[str, Any]]]:
    spec = load_spec(root)
    data = json.loads((root / "source.json").read_text())
    if (
        data.get("schema_version") != 1
        or data.get("dataset_id") != "aria-model-uncertainty-original-source-v1"
    ):
        raise ValueError("Wrong uncertainty source identity")
    if data["aria_station_nomination"] or data["absolute_physical_uncertainty_bound"] is not None:
        raise ValueError("Unsafe independence or absolute uncertainty declaration")
    if data["specification_sha256"] != sha256((root / "specification.json").read_bytes()) or data[
        "components_sha256"
    ] != sha256((root / "components.json").read_bytes()):
        raise ValueError("Changed frozen source/specification identity")
    verify_wp56(Path("data/fixtures/horizons/wp56-discovery"))
    proof = verify_components(root, REMAINING, "components.json")
    components = json.loads((root / "components.json").read_text())
    if components["dataset_id"] != "aria-four-remaining-model-components-v1":
        raise ValueError("Incorrect remaining-body component dataset")
    for record in components["responses"]:
        body, role = record["body"], record["role"]
        params = specification(body, role, REMAINING)
        receipt = dict(
            parameters=record["reference_parameters"],
            url=record["reference_url"],
            row_count=record["rows"],
            **{
                k: record[k]
                for k in ("raw_file", "raw_sha256", "source_header", "response_signature")
            },
        )
        validate_receipt(root, receipt, params, record["target_id"], "geometric", epochs(body))
    expected = wanted_stations(spec)
    mapping = {}
    for record in data["station_requests"]:
        body = record["body"]
        if body not in expected:
            raise ValueError("Unknown station target")
        params = record["parameters"]
        dates = [float(t) for t in re.findall(r"'([0-9]+\.[0-9]+)'", params["TLIST"])]
        rows = validate_receipt(
            root, record, query(body, "apparent", dates), TARGETS[body], "apparent", dates
        )
        for row in rows:
            key = body, row["jd_tt"]
            if key in mapping:
                raise ValueError("Duplicate station reference sample")
            mapping[key] = row
    if (
        set(mapping) != {(b, t) for b, dates in expected.items() for t in dates}
        or len(mapping) != data["station_ray_count"]
    ):
        raise ValueError("Missing or additional station reference dates")
    return dict(
        component_states=proof["verified_states"],
        component_responses=proof["verified_source_responses"],
        station_rays=len(mapping),
        station_count=len(spec["station_centres"]),
        station_responses=len(data["station_requests"]),
        source_sha256=sha256((root / "source.json").read_bytes()),
        specification_sha256=data["specification_sha256"],
    ), mapping


def load_offset_spec(root: Path) -> dict[str, Any]:
    spec = json.loads((root / "direct-offset-specification.json").read_text())
    expected = [
        dict(body=b, target=p * 100 + 99, observer=p, epochs_jd_tdb=epochs(b))
        for b, p in REMAINING.items()
    ]
    if (
        spec.get("schema_version") != 1
        or spec.get("specification_id") != "aria-four-planet-direct-offsets-v1"
        or spec["queries"] != expected
    ):
        raise ValueError("Changed direct-offset source specification")
    if spec["original_specification_sha256"] != sha256(
        (root / "specification.json").read_bytes()
    ) or spec["original_source_sha256"] != sha256((root / "source.json").read_bytes()):
        raise ValueError("Direct-offset study is not bound to original evidence")
    if spec["absolute_physical_uncertainty_bound"] is not None:
        raise ValueError("Unsupported physical uncertainty bound")
    return spec


def offset_query(body: str) -> dict[str, str]:
    params = specification(body, "centre_ssb", REMAINING)
    params["CENTER"] = f"'500@{REMAINING[body]}'"
    return params


def acquire_offsets(root: Path) -> None:
    if (root / "direct-offset-source.json").exists():
        raise FileExistsError("Direct-offset source is immutable; refuse refresh")
    verify(root)
    spec = load_offset_spec(root)
    records = []
    for item in spec["queries"]:
        body = item["body"]
        record, _ = capture(
            root,
            f"{body}-direct-offset",
            offset_query(body),
            item["target"],
            "geometric",
            item["epochs_jd_tdb"],
        )
        records.append(dict(body=body, **record))
    data = dict(
        schema_version=1,
        dataset_id="aria-four-planet-direct-offset-reference-v1",
        specification_sha256=sha256((root / "direct-offset-specification.json").read_bytes()),
        responses=records,
        absolute_physical_uncertainty_bound=None,
    )
    (root / "direct-offset-source.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n"
    )
    verify_offsets(root)


def verify_offsets(root: Path) -> tuple[dict[str, Any], dict[tuple[str, float], dict[str, Any]]]:
    spec = load_offset_spec(root)
    data = json.loads((root / "direct-offset-source.json").read_text())
    if (
        data.get("schema_version") != 1
        or data.get("dataset_id") != "aria-four-planet-direct-offset-reference-v1"
    ):
        raise ValueError("Unknown direct-offset source identity")
    if (
        data["specification_sha256"]
        != sha256((root / "direct-offset-specification.json").read_bytes())
        or data["absolute_physical_uncertainty_bound"] is not None
    ):
        raise ValueError("Changed direct-offset specification or uncertainty claim")
    wanted = {q["body"]: q for q in spec["queries"]}
    seen = set()
    mapping = {}
    for record in data["responses"]:
        body = record["body"]
        if body not in wanted or body in seen:
            raise ValueError("Duplicate or unexpected direct-offset request")
        seen.add(body)
        rows = validate_receipt(
            root,
            record,
            offset_query(body),
            wanted[body]["target"],
            "geometric",
            wanted[body]["epochs_jd_tdb"],
        )
        for row in rows:
            mapping[(body, row["jd_tdb"])] = dict(
                **row, raw_file=record["raw_file"], raw_sha256=record["raw_sha256"]
            )
    if seen != set(REMAINING) or len(mapping) != 100:
        raise ValueError("Missing direct-offset source rows")
    return dict(
        direct_offset_states=len(mapping),
        direct_offset_responses=len(seen),
        direct_offset_source_sha256=sha256((root / "direct-offset-source.json").read_bytes()),
        direct_offset_specification_sha256=data["specification_sha256"],
    ), mapping


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("acquire", "verify", "acquire-offsets", "verify-offsets")
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    if args.action == "acquire":
        acquire(args.source)
    elif args.action == "acquire-offsets":
        acquire_offsets(args.source)
    elif args.action == "verify-offsets":
        print(json.dumps(verify_offsets(args.source)[0], indent=2, sort_keys=True))
    else:
        print(json.dumps(verify(args.source)[0], indent=2, sort_keys=True))
