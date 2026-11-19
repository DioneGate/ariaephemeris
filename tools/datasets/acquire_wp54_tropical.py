# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""WP5.4: acquire independent Horizons inertial rays for tropical chart tests.

The baseline 25 apparent positions per body come from the frozen WP5.1 JPL
responses. Additional RA/Dec rays are independently queried at +/-0.0125 and
+/-0.025 TT days, and at six stress epochs (a station and an ingress +/-0.25d)
per body. Aria ONLY NOMINATES stress times; it NEVER supplies reference values.
Live acquisition is one-shot, serial, provenance-pinned and not part of tests.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import (
    TARGETS,
    fetch,
    parse_table,
    query,
    sha256,
    source_header,
)
from verify_horizons_fixtures import validate as verify_wp51

STEP = 0.0125
STENCIL = (-2, -1, 0, 1, 2)
BODIES = tuple(TARGETS)
SCAN_START = 2459945.5  # TT 2023-01-01, includes Pluto's 2023 Aquarius ingress.
SCAN_STOP = 2461040.5  # TT 2025-12-31.
SCAN_STEP = 4.0
NUM_BASE = 25
NUM_STRESS = 6
CHUNK = 45


def stamp(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("Epoch must be finite")
    return round(value, 7)


def wrap_delta(a: float, b: float) -> float:
    return (a - b + 180.0) % 360.0 - 180.0


def _position(engine: Ephemeris, body: str, jd: float) -> Any:
    req = PositionRequest(
        TimeInput(jd=(jd, 0.0), scale="TT"),
        bodies=(body,),
        origin="geocentric",
        position_mode="apparent",
        profile="planet-centres-v1",
        frame="true_ecliptic_of_date",
    )
    result = engine.positions(req)
    if result.bodies[0].target_id != TARGETS[body]:
        raise ValueError("Stress selection used wrong planet-centre profile")
    return result.bodies[0]


def _refine(
    engine: Ephemeris, body: str, left: float, right: float, kind: str, boundary: float
) -> float:
    def value(jd: float) -> float:
        p = _position(engine, body, jd)
        if kind == "station":
            return p.longitude_rate_deg_day
        if kind == "ingress":
            return wrap_delta(p.longitude_deg, boundary)
        raise ValueError("Unsupported critical epoch kind")

    vleft, vright = value(left), value(right)
    if vleft * vright > 0:
        raise ValueError("Critical event is not bracketed in 2023-2025")
    for _ in range(16):
        mid = (left + right) / 2
        v = value(mid)
        if (vleft <= 0 <= v) or (v <= 0 <= vleft):
            right, vright = mid, v
        else:
            left, vleft = mid, v
    return stamp((left + right) / 2)


def select_critical(engine: Ephemeris, body: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Choose first 2023-2025 station and sign ingress, then refine their brackets.

    Time nomination by the Aria candidate is explicit. The independent numerical
    reference for each selected time comes exclusively from JPL Horizons.
    """
    epochs = [
        stamp(SCAN_START + SCAN_STEP * index)
        for index in range(int((SCAN_STOP - SCAN_START) / SCAN_STEP) + 1)
    ]
    first = PositionRequest(
        TimeInput(jd=(epochs[0], 0.0), scale="TT"),
        bodies=(body,),
        origin="geocentric",
        position_mode="apparent",
        frame="true_ecliptic_of_date",
        profile="planet-centres-v1",
    )
    values = engine.positions_batch(
        first, [TimeInput(jd=(epoch, 0.0), scale="TT") for epoch in epochs]
    )
    if len(values) != len(epochs):
        raise ValueError("Incomplete critical-epoch selection scan")
    station: dict[str, Any] | None = None
    ingress: dict[str, Any] | None = None
    for index in range(len(epochs) - 1):
        left, right = values[index].bodies[0], values[index + 1].bodies[0]
        if station is None and left.longitude_rate_deg_day * right.longitude_rate_deg_day < 0:
            root = _refine(engine, body, epochs[index], epochs[index + 1], "station", 0)
            station = {
                "kind": "station",
                "jd_tt": root,
                "candidate_source": "Aria nominated only (not independent reference)",
                "selection_window_jd_tt": [epochs[index], epochs[index + 1]],
            }
        motion = wrap_delta(right.longitude_deg, left.longitude_deg)
        if ingress is None and abs(motion) < 15:
            sign_left = int(left.longitude_deg // 30)
            sign_right = int(right.longitude_deg // 30)
            if sign_left != sign_right:
                boundary = ((sign_left + (1 if motion > 0 else 0)) * 30) % 360
                root = _refine(
                    engine, body, epochs[index], epochs[index + 1], "ingress", boundary
                )
                ingress = {
                    "kind": "ingress",
                    "jd_tt": root,
                    "boundary_deg": boundary,
                    "candidate_source": "Aria nominated only (not independent reference)",
                    "selection_window_jd_tt": [epochs[index], epochs[index + 1]],
                }
        if station is not None and ingress is not None:
            break
    if station is None or ingress is None:
        raise ValueError(f"No well-bracketed station/ingress in selection window: {body}")
    return station, ingress


def stress_centres(
    engine: Ephemeris, body: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    station, ingress = select_critical(engine, body)
    records = []
    for candidate in (station, ingress):
        for label, shift in (("before", -0.25), ("root", 0.0), ("after", 0.25)):
            records.append(
                {
                    "label": f"{candidate['kind']}-{label}",
                    "kind": candidate["kind"],
                    "jd_tt": stamp(candidate["jd_tt"] + shift),
                    "nomination": candidate,
                }
            )
    if len({r["jd_tt"] for r in records}) != NUM_STRESS:
        raise ValueError("Non-unique critical times")
    return records, [station, ingress]


def _wp51_centres(root: Path, body: str) -> list[dict[str, Any]]:
    data = json.loads((root / "horizons-reference-v1.json").read_text(encoding="utf-8"))
    relevant = [
        case
        for case in data["cases"]
        if case["body"] == body and case["kind"] == "apparent"
    ]
    if len(relevant) != NUM_BASE:
        raise ValueError("WP5.1 baseline apparent time samples missing")
    return [
        {
            "label": f"baseline-{index + 1:02d}",
            "kind": "baseline",
            "jd_tt": case["reference"]["jd_tt"],
            "nomination": {"candidate_source": "pre-existing independent WP5.1 dates"},
        }
        for index, case in enumerate(relevant)
    ]


def acquire(
    base: Path, centres_dir: Path, wp51: Path, output: Path
) -> dict[str, Any]:
    if (output / "wp54-horizons-tropical-stencils-v1.json").exists():
        raise FileExistsError("Frozen Horizons WP5.4 fixtures must not be silently refreshed")
    if verify_wp51(wp51)["fixture_rows_verified"] != 300:
        raise ValueError("Frozen original external source validation did not pass")
    manifest = centres_manifest()
    sources = {
        body: centres_dir / entry["filename"]
        for body, entry in manifest["sources"].items()
    }
    raw = output / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    cases: list[dict[str, Any]] = []
    requests: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    candidates: dict[str, Any] = {}
    wp51_data = json.loads((wp51 / "horizons-reference-v1.json").read_text(encoding="utf-8"))
    with Ephemeris(base, centre_kernels=sources) as engine:
        for body in BODIES:
            selected, found = stress_centres(engine, body)
            candidates[body] = found
            anchors = _wp51_centres(wp51, body) + selected
            if len(anchors) != NUM_BASE + NUM_STRESS:
                raise ValueError("Missing mandatory 31 centre epochs")
            existing = {
                case["reference"]["jd_tt"]: {
                    "jd_tt": case["reference"]["jd_tt"],
                    "inertial_apparent_ra_deg": case["reference"]["inertial_apparent_ra_deg"],
                    "inertial_apparent_dec_deg": case["reference"]["inertial_apparent_dec_deg"],
                    "source_raw_file": "wp51/" + case["source_raw_file"],
                }
                for case in wp51_data["cases"]
                if case["body"] == body and case["kind"] == "apparent"
            }
            wanted = {
                stamp(anchor["jd_tt"] + STEP * k)
                for anchor in anchors
                for k in STENCIL
            }
            new_points = sorted(wanted - set(existing))
            for chunk_no, start in enumerate(range(0, len(new_points), CHUNK), 1):
                dates = new_points[start : start + CHUNK]
                params = query(body, "apparent", dates)
                response, url = fetch(params)
                original = response["result"]
                parsed = parse_table(original, TARGETS[body], "apparent", dates)
                header = source_header(original)
                filename = f"{body}-stencil-{chunk_no:02d}.txt"
                encoded = original.encode("utf-8")
                (raw / filename).write_bytes(encoded)
                requests.append(
                    {
                        "body": body,
                        "target_id": TARGETS[body],
                        "raw_file": "raw/" + filename,
                        "sha256": sha256(encoded),
                        "query": params,
                        "query_url": url,
                        "signature": response["signature"],
                        "header": header,
                        "rows": len(parsed),
                    }
                )
                for value in parsed:
                    jd = value["jd_tt"]
                    if jd in existing:
                        raise ValueError("Overlapping Horizons reference epochs")
                    existing[jd] = {
                        **value,
                        "source_raw_file": "raw/" + filename,
                    }
                if start + CHUNK < len(new_points) or body != BODIES[-1]:
                    time.sleep(3)
            if set(existing) != wanted:
                raise ValueError("Incomplete new Horizons five-point stencils")
            source_rows.extend(
                {"body": body, **existing[jd]} for jd in sorted(existing)
            )
            for anchor in anchors:
                values = [stamp(anchor["jd_tt"] + k * STEP) for k in STENCIL]
                if len(set(values)) != len(values):
                    raise ValueError("Duplicate finite derivative stencil epoch")
                cases.append(
                    {
                        "id": f"ARIA-WP54-{body.upper()}-{anchor['label'].upper()}",
                        "body": body,
                        "target_id": TARGETS[body],
                        "category": anchor["kind"],
                        "sample_label": anchor["label"],
                        "jd_tt": anchor["jd_tt"],
                        "stencil_jd_tt": values,
                        "nomination": anchor["nomination"],
                    }
                )
            print(
                f"{body}: {len(anchors)} chart cases, {len(new_points)} new JPL ray samples; "
                f"nominated station {found[0]['jd_tt']}, ingress {found[1]['jd_tt']}",
                flush=True,
            )
    result = {
        "schema_version": 1,
        "dataset_id": "aria-wp54-jpl-iau2006-tropical-ray-stencils-v1",
        "source": "NASA/JPL Horizons OBSERVER quantity 45 ICRF airless apparent RA/Dec, TT",
        "frame_conversion": "IAU 2006/2000A true equator/ecliptic-of-date; performed offline from inertial JPL rays",
        "frame_library": "ERFA 2.0.1.5, also used by Aria: transformation is a shared standards dependency",
        "epoch_nomination": "Critical dates selected by Aria only, all reference sky coordinates supplied by JPL",
        "data_policy": "Frozen source references; manual acquisition only, no refresh without new version",
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "source_wp51_id": wp51_data["dataset_id"],
        "aria_source_manifest_id": manifest["dataset_id"],
        "aria_base_sha256": manifest["base_sha256"],
        "tt_rate_step_days": STEP,
        "stencil_offsets": list(STENCIL),
        "cases_per_body": NUM_BASE + NUM_STRESS,
        "new_jpl_reference_rows": sum(req["rows"] for req in requests),
        "case_count": len(cases),
        "ray_count": len(source_rows),
        "source_requests": requests,
        "critical_candidates": candidates,
        "cases": cases,
        "rays": source_rows,
        "scientific_status": "INDEPENDENT_INERTIAL_RAYS_WITH_SHARED_IAU_STANDARD_TRANSFORM",
        "commercial_accuracy_certified": False,
    }
    if result["case_count"] != 186 or result["ray_count"] != 930:
        raise ValueError("WP5.4 independent position/rate reference coverage incomplete")
    output.mkdir(parents=True, exist_ok=True)
    (output / "wp54-horizons-tropical-stencils-v1.json").write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--centres-dir", type=Path, required=True)
    parser.add_argument("--wp51", type=Path, default=Path("data/fixtures/horizons"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/fixtures/horizons/wp54-tropical")
    )
    a = parser.parse_args()
    out = acquire(a.base, a.centres_dir, a.wp51, a.output)
    print(f"Acquired {out['new_jpl_reference_rows']} new inertial JPL direction records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
