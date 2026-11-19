# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Blind source-only catalogue followed by complete real-Aria catalogue comparison.

Source discovery is completed before opening any Aria kernel. No runtime code is
replaced, monkeypatched or used in the reference catalogue. Failures are evidence,
never successful empty event lists. Frozen reports replay offline byte for byte.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from ariaephemeris import Ephemeris, EventRequest, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_wp56_discovery import load_spec
from verify_wp56_discovery import verify
from wp56_discovery import discover, match_catalogues, tropical_longitudes


def reference_catalogue(
    spec: dict[str, Any], rows: dict[tuple[str, str], list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    longitudes = {key: tropical_longitudes(series) for key, series in rows.items()}
    windows = {w["id"]: w for w in spec["windows"]}
    output = []
    for workload in spec["workloads"]:
        window = windows[workload["window"]]
        key = workload["window"], workload["body"]
        times = np.array([r["jd_tt"] for r in rows[key]])
        other = longitudes[(workload["window"], workload["other"])] if workload["other"] else None
        catalogues = {}
        for grid in spec["reference_grids"]:
            sl = slice(grid["offset"], None, grid["stride"])
            catalogues[grid["name"]] = discover(
                times[sl],
                longitudes[key][sl],
                workload,
                (window["start_jd_tt"], window["end_jd_tt"]),
                other[sl] if other is not None else None,
            )
        fine = catalogues["fine"]
        convergence = {
            name: match_catalogues(fine, events, spec["reference_convergence_seconds"])
            for name, events in catalogues.items()
            if name != "fine"
        }
        ambiguous = [i for i, event in enumerate(fine) if event["ambiguous"]]
        output.append(
            dict(
                workload=workload,
                interval_jd_tt=[window["start_jd_tt"], window["end_jd_tt"]],
                reference_events=fine,
                reference_grids=catalogues,
                grid_comparisons=convergence,
                ambiguous_reference_indices=ambiguous,
                reference_resolved=not ambiguous and all(c["passed"] for c in convergence.values()),
            )
        )
    return output


def actual_catalogue(
    engine: Ephemeris, spec: dict[str, Any], row: dict[str, Any]
) -> list[dict[str, Any]]:
    w = row["workload"]
    start, stop = row["interval_jd_tt"]
    request = EventRequest(
        start=TimeInput(jd=(start, 0), scale="TT"),
        end=TimeInput(jd=(stop, 0), scale="TT"),
        kind=w["kind"],
        body=w["body"],
        other_body=w["other"],
        angle_deg=w["angle"],
        tolerance_seconds=spec["aria_tolerance_seconds"],
        max_step_days=spec["aria_max_step_days"],
        max_evaluations=100000,
        profile="planet-centres-v1",
    )
    returned = engine.find_events(request)
    result = []
    for event in returned:
        jd = sum(event.jd_tt)
        if not start <= jd <= stop:
            raise ValueError("Aria returned an event outside its request")
        if jd == stop:  # Explicit benchmark half-open ownership, runtime stays closed.
            continue
        bodies = (w["body"],) if w["other"] is None else (w["body"], w["other"])
        positions = engine.positions(
            PositionRequest(
                TimeInput(jd=(jd, 0), scale="TT"), bodies=bodies, profile="planet-centres-v1"
            )
        )
        phase = positions.bodies[0].longitude_deg
        direction = event.metadata["event_direction"]
        if w["kind"] == "station":
            h = 0.01
            samples = engine.positions_batch(
                PositionRequest(
                    TimeInput(jd=(jd, 0), scale="TT"), bodies=bodies, profile="planet-centres-v1"
                ),
                [TimeInput(jd=(jd - h, 0), scale="TT"), TimeInput(jd=(jd + h, 0), scale="TT")],
            )
            rates = [p.bodies[0].longitude_rate_deg_day for p in samples]
            direction = "retrograde-to-direct" if rates[1] > rates[0] else "direct-to-retrograde"
            goal = None
        elif w["kind"] == "ingress":
            goal = float(round(phase / 30) * 30 % 360)
        elif w["kind"] in ("conjunction", "opposition"):
            goal = float(w["angle"])
        else:
            phase = (phase - positions.bodies[1].longitude_deg) % 360
            goal = float(w["angle"] if phase < 180 else 360 - w["angle"])
        result.append(
            dict(
                kind=w["kind"],
                body=w["body"],
                other=w["other"],
                goal_deg=goal,
                direction=direction,
                jd_tt=jd,
                conditioning=event.conditioning,
                residual=event.residual,
                bracket_width_seconds=event.time_bracket_seconds,
            )
        )
    return result


def compare(root: Path, base: Path, centres: Path, output: Path) -> dict[str, Any]:
    proof, sources = verify(root)
    spec = load_spec(root / "specification.json")
    records = reference_catalogue(spec, sources)
    print(
        f"Discovered independent source-only catalogues for {len(records)} workloads before opening Aria",
        flush=True,
    )
    manifest = centres_manifest()
    with Ephemeris(
        base, centre_kernels={b: centres / r["filename"] for b, r in manifest["sources"].items()}
    ) as engine:
        for n, row in enumerate(records, 1):
            try:
                actual = actual_catalogue(engine, spec, row)
            except Exception as exc:
                row["aria_search_error"] = dict(
                    type=type(exc).__name__, code=getattr(exc, "code", None), message=str(exc)
                )
                row["passed"] = False
            else:
                row["aria_events"] = actual
                row["comparison"] = match_catalogues(
                    row["reference_events"], actual, spec["association_seconds"]
                )
                row["passed"] = row["reference_resolved"] and row["comparison"]["passed"]
            print(
                f"{n}/{len(records)} {row['workload']['id']}: reference={len(row['reference_events'])}, pass={row['passed']}",
                flush=True,
            )
    per_kind = {}
    for kind in ("station", "ingress", "conjunction", "opposition", "aspect"):
        selected = [r for r in records if r["workload"]["kind"] == kind]
        per_kind[kind] = dict(
            workloads=len(selected),
            reference_events=sum(len(r["reference_events"]) for r in selected),
            aria_events=sum(len(r.get("aria_events", [])) for r in selected),
            passed_workloads=sum(r["passed"] for r in selected),
        )
    result = dict(
        schema_version=1,
        report_id="aria-wp56-blind-event-discovery-v1",
        source_integrity=proof,
        kernel_manifest=manifest,
        reference_selection="predeclared windows; JPL-only cubic discovery; no Aria nominations",
        reference_root_semantics="local cubic interpolant roots; empirical grid convergence, not rigorous root isolation",
        shared_dependency="ERFA IAU 2006/2000A; not independently reimplemented precession/nutation",
        model_uncertainty="Horizons-selected source paths differ from DE442s plus pinned centre offsets; RM-001/010 open",
        workload_count=len(records),
        empty_reference_workloads=sum(not r["reference_events"] for r in records),
        per_kind=per_kind,
        passed=all(r["passed"] for r in records),
        unresolved_reference_workloads=sum(not r["reference_resolved"] for r in records),
        search_error_workloads=sum("aria_search_error" in r for r in records),
        missed_events=sum(
            len(r.get("comparison", {}).get("missing_reference_indices", [])) for r in records
        ),
        additional_events=sum(
            len(r.get("comparison", {}).get("additional_actual_indices", [])) for r in records
        ),
        duplicate_pairs=sum(
            len(r.get("comparison", {}).get("duplicate_actual_pairs", [])) for r in records
        ),
        ambiguous_edges=sum(
            len(r.get("comparison", {}).get("ambiguous_edges", [])) for r in records
        ),
        continuous_completeness_proven=False,
        absolute_physical_accuracy_certified=False,
        commercial_release_qualified=False,
        records=records,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("records", "kernel_manifest")}, indent=2
        ),
        flush=True,
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=Path("data/fixtures/horizons/wp56-discovery")
    )
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--centres-dir", type=Path, required=True)
    parser.add_argument(
        "--output", type=Path, default=Path("docs/validation/wp56-independent-event-discovery.json")
    )
    args = parser.parse_args()
    report = compare(args.source, args.base, args.centres_dir, args.output)
    raise SystemExit(0 if report["passed"] else 1)
