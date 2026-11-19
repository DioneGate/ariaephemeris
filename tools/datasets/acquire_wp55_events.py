# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Acquire independent JPL Horizons rays at selected event-root neighbourhoods.

The existing Aria engine nominates only *test windows*. Every independent
reference longitude/rate and all final reference event roots use exclusively
original Horizons quantity-45 apparent ICRF RA/Dec at TT. No live API call is
part of normal qualification; this is an explicit one-shot source acquisition.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ariaephemeris import Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import TARGETS, fetch, parse_table, query, sha256, source_header
from verify_wp54_tropical import verify as verify_wp54
from wp55_event_math import (
    BODY_ORDER,
    PAIRS,
    grid,
    signed_angle,
    stamp,
    station_stencil,
)

SCAN_START = 2459945.5  # explicit TT, 2023-01-01
SCAN_STOP = 2461040.5  # explicit TT, 2025-12-31
SCAN_STEP = 2.0
CHUNK = 45
EXPECTED_CASES = 22


def _position(engine: Ephemeris, body: str, other: str, jd: float) -> tuple[float, float]:
    r = engine.positions(
        PositionRequest(
            TimeInput(jd=(jd, 0.0), scale="TT"),
            bodies=(body, other),
            frame="true_ecliptic_of_date",
            profile="planet-centres-v1",
        )
    )
    return r.bodies[0].longitude_deg, r.bodies[1].longitude_deg


def _bisect_pair(engine: Ephemeris, other: str, kind: str, left: float, right: float) -> float:
    target = 0 if kind == "conjunction" else 180

    def residual(jd: float) -> float:
        a, b = _position(engine, "mars", other, jd)
        return signed_angle(signed_angle(a, b), target)

    fleft, fright = residual(left), residual(right)
    if fleft * fright > 0 or abs(fleft - fright) >= 90:
        raise ValueError(f"No valid pair event bracket for Mars/{other}/{kind}")
    for _ in range(38):
        mid = (left + right) / 2
        if mid == left or mid == right:
            break
        fmid = residual(mid)
        if (fleft <= 0 <= fmid) or (fmid <= 0 <= fleft):
            right, fright = mid, fmid
        else:
            left, fleft = mid, fmid
    return stamp((left + right) / 2)


def select_pair_events(engine: Ephemeris) -> list[dict[str, Any]]:
    """Use an Aria-only coarse phase scan to nominate, not validate, 10 windows."""
    dates = [
        stamp(SCAN_START + i * SCAN_STEP)
        for i in range(int((SCAN_STOP - SCAN_START) / SCAN_STEP) + 1)
    ]
    request = PositionRequest(
        TimeInput(jd=(dates[0], 0.0), scale="TT"),
        bodies=BODY_ORDER,
        profile="planet-centres-v1",
        frame="true_ecliptic_of_date",
        position_mode="apparent",
        origin="geocentric",
    )
    observed = engine.positions_batch(
        request, [TimeInput(jd=(jd, 0.0), scale="TT") for jd in dates]
    )
    if len(observed) != len(dates):
        raise ValueError("Candidate date scan did not complete")
    result = []
    for first, second in PAIRS:
        i1, i2 = BODY_ORDER.index(first), BODY_ORDER.index(second)
        for kind, target in (("conjunction", 0), ("opposition", 180)):
            pairs = []
            for i in range(len(dates) - 1):
                va = signed_angle(
                    signed_angle(
                        observed[i].bodies[i1].longitude_deg, observed[i].bodies[i2].longitude_deg
                    ),
                    target,
                )
                vb = signed_angle(
                    signed_angle(
                        observed[i + 1].bodies[i1].longitude_deg,
                        observed[i + 1].bodies[i2].longitude_deg,
                    ),
                    target,
                )
                if va * vb <= 0 and abs(va - vb) < 90:
                    pairs.append((i, va, vb))
            if not pairs:
                raise ValueError(f"No {kind} candidate for {first}/{second} in 2023–2025")
            i, _, _ = pairs[0]
            root = _bisect_pair(engine, second, kind, dates[i], dates[i + 1])
            result.append(
                {
                    "event_id": f"{kind}-mars-{second}",
                    "kind": kind,
                    "body": "mars",
                    "other_body": second,
                    "goal_deg": target,
                    "nominated_jd_tt": root,
                    "nomination_window_jd_tt": [dates[i], dates[i + 1]],
                    "nomination_method": "Aria physical-centre phase sign-change scan and bisection ONLY",
                    "reference_source": "independent JPL rays only; no Aria expected position or root",
                }
            )
    if len(result) != 10:
        raise ValueError("Exactly five conjunctions and five oppositions required")
    return result


def select_cases(engine: Ephemeris, wp54: dict[str, Any]) -> list[dict[str, Any]]:
    cases = []
    for body in BODY_ORDER:
        nominations = wp54["critical_candidates"][body]
        if len(nominations) != 2 or {x["kind"] for x in nominations} != {"station", "ingress"}:
            raise ValueError("Missing independently measured WP5.4 stress date anchors")
        for item in nominations:
            kind = item["kind"]
            cases.append(
                {
                    "event_id": f"{kind}-{body}",
                    "kind": kind,
                    "body": body,
                    "other_body": None,
                    "goal_deg": item.get("boundary_deg") if kind == "ingress" else None,
                    "nominated_jd_tt": stamp(item["jd_tt"]),
                    "nomination_window_jd_tt": item["selection_window_jd_tt"],
                    "nomination_method": "Aria-nominated WP5.4 critical date; no independently timed root",
                    "reference_source": "independent JPL rays only; no Aria expected position or root",
                }
            )
    cases.extend(select_pair_events(engine))
    if len(cases) != EXPECTED_CASES or len({x["event_id"] for x in cases}) != EXPECTED_CASES:
        raise ValueError("Missing or repeated planetary event types")
    for case in cases:
        case["jd_tt_grid"] = grid(case["nominated_jd_tt"])
        if case["kind"] == "station":
            case["reference_rate_stencils"] = [station_stencil(jd) for jd in case["jd_tt_grid"]]
        else:
            case["reference_rate_stencils"] = []
    return cases


def acquire(base: Path, centres: Path, wp54_root: Path, output: Path) -> dict[str, Any]:
    file = output / "wp55-horizons-event-roots-v1.json"
    if file.exists():
        raise FileExistsError("Frozen WP5.5 original JPL event source must not be refreshed")
    if (
        verify_wp54(wp54_root, wp54_root.parent)["verified_critical_and_baseline_chart_cases"]
        != 186
    ):
        raise ValueError("Upstream independent JPL source WP5.4 integrity failed")
    wp54 = json.loads((wp54_root / "wp54-horizons-tropical-stencils-v1.json").read_text())
    manifest = centres_manifest()
    sources = {body: centres / data["filename"] for body, data in manifest["sources"].items()}
    with Ephemeris(base, centre_kernels=sources) as engine:
        cases = select_cases(engine, wp54)
    wanted: dict[str, set[float]] = {body: set() for body in BODY_ORDER}
    for event in cases:
        for body in (event["body"], event["other_body"]):
            if body is None:
                continue
            wanted[body].update(event["jd_tt_grid"])
            if event["kind"] == "station":
                for stencil in event["reference_rate_stencils"]:
                    wanted[body].update(stencil)
    original = []
    rays = []
    raw_dir = output / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for body in BODY_ORDER:
        all_epochs = sorted(wanted[body])
        if len(all_epochs) < 18:
            raise ValueError(f"Incomplete independent JPL source event coverage: {body}")
        for part, start in enumerate(range(0, len(all_epochs), CHUNK), 1):
            dates = all_epochs[start : start + CHUNK]
            params = query(body, "apparent", dates)
            reply, url = fetch(params)
            raw = reply["result"]
            parsed = parse_table(raw, TARGETS[body], "apparent", dates)
            header = source_header(raw)
            raw_file = f"raw/{body}-event-{part:02d}.txt"
            encoded = raw.encode("utf-8")
            (output / raw_file).write_bytes(encoded)
            original.append(
                {
                    "body": body,
                    "target_id": TARGETS[body],
                    "centre_id": 399,
                    "source_url": url,
                    "parameters": params,
                    "source_header": header,
                    "response_signature": reply["signature"],
                    "raw_file": raw_file,
                    "raw_sha256": sha256(encoded),
                    "row_count": len(parsed),
                }
            )
            rays.extend({"body": body, "raw_file": raw_file, **value} for value in parsed)
            print(
                f"Archived JPL {body} original raw response {part}: {len(parsed)} rows", flush=True
            )
            if body != BODY_ORDER[-1] or start + CHUNK < len(all_epochs):
                time.sleep(3)
    count = sum(len(v) for v in wanted.values())
    if len(rays) != count or len({(r["body"], r["jd_tt"]) for r in rays}) != count:
        raise ValueError("Independent Horizons event source incomplete or duplicated")
    result = {
        "schema_version": 1,
        "dataset_id": "aria-horizons-planet-centres-event-time-reference-v1",
        "source_authority": "NASA/JPL Horizons geocentric airless apparent ICRF RA/Dec, quantity45 TT",
        "wp54_source_dataset_id": wp54["dataset_id"],
        "aria_source_manifest_id": manifest["dataset_id"],
        "aria_base_sha256": manifest["base_sha256"],
        "original_evaluation": "No Aria prediction, state or longitude enters any reference value or JPL-root interpolation",
        "selection_bias": "22 candidate events nominated by Aria; this is NOT a blind event discovery or completeness test",
        "frame_convention": "IAU 2006/2000A true ecliptic-of-date; shared ERFA standard implementation",
        "sampling": {
            "grid_step_tt_days": 0.03125,
            "grid_half_width_days": 0.125,
            "station_rate_step_tt_days": 0.0125,
            "station_rate_stencil": [-2, -1, 0, 1, 2],
            "source_tt_jd_precision_days": 1e-7,
            "reference_interpolation": "four-point cubic inside independently observed JPL root bracket",
            "interpolation_accuracy_not_proven": True,
        },
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "source_requests": original,
        "original_response_count": len(original),
        "ray_count": len(rays),
        "case_count": len(cases),
        "cases": cases,
        "rays": rays,
        "absolute_event_timing_qualified": False,
        "commercial_release_qualified": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(f"Frozen {len(cases)} event cases and {len(rays)} independent JPL source rays")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--centres-dir", type=Path, required=True)
    p.add_argument("--wp54", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    p.add_argument("--output", type=Path, default=Path("data/fixtures/horizons/wp55-events"))
    args = p.parse_args()
    acquire(args.base, args.centres_dir, args.wp54, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
