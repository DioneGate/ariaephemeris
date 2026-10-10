# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Bounded searches with extrema-aware subdivision and wrapped-phase handling."""

import math
from collections.abc import Callable
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

import numpy as np

from ..errors import AriaError
from ..models import Event, EventRequest, PositionRequest, TimeInput
from ..numerics import bisect_root, circular_difference
from ..time import resolve

if TYPE_CHECKING:
    from ..engine import Ephemeris


def find_events(
    engine: "Ephemeris", request: EventRequest, cancelled: Callable[[], bool] | None = None
) -> tuple[Event, ...]:
    r = request
    if r.kind not in ("ingress", "aspect", "conjunction", "opposition", "station"):
        raise AriaError("INVALID_REQUEST", "Unknown event kind")
    if r.kind in ("aspect", "conjunction", "opposition") and not r.other_body:
        raise AriaError("INVALID_REQUEST", "Aspect events require other_body")
    if r.body == r.other_body:
        raise AriaError("INVALID_REQUEST", "Aspect bodies must differ")
    if not np.isfinite([r.tolerance_seconds, r.max_step_days, r.angle_deg]).all():
        raise AriaError("INVALID_REQUEST", "Event parameters must be finite")
    if not isinstance(r.max_evaluations, int) or isinstance(r.max_evaluations, bool):
        raise AriaError("INVALID_REQUEST", "Event work budget must be an integer")
    if r.tolerance_seconds <= 0 or r.max_step_days <= 0 or r.max_evaluations < 1:
        raise AriaError("INVALID_REQUEST", "Event tolerances and budgets must be positive")
    if not 0 <= r.angle_deg <= 180:
        raise AriaError("INVALID_REQUEST", "Aspect angle must be in 0..180")
    t0, t1 = resolve(r.start, r.strict), resolve(r.end, r.strict)
    engine._coverage([t0, t1])
    start, end = t0.tt1 + t0.tt2, t1.tt1 + t1.tt2
    if start >= end:
        raise AriaError("INVALID_REQUEST", "Event start must precede end")
    # Four sub-samples per bounded scan interval. Adaptive extrema subdivision below.
    step = min(r.max_step_days, 0.25) / 4
    ratio = (end - start) / step if step else float("inf")
    if not math.isfinite(ratio) or ratio + 1 > r.max_evaluations:
        raise AriaError("REQUEST_LIMIT", "Event interval exceeds evaluation budget")
    n = int(math.ceil(ratio)) + 1
    if n > r.max_evaluations:
        raise AriaError("REQUEST_LIMIT", "Event interval exceeds evaluation budget")
    bodies = (r.body,) if not r.other_body else (r.body, r.other_body)
    base = PositionRequest(TimeInput(jd=(start, 0), scale="TT"), bodies=bodies, strict=r.strict)
    cache: dict[float, tuple[float, float]] = {}
    evaluations = 0

    def guard(count: int = 1) -> None:
        nonlocal evaluations
        if cancelled is not None and cancelled():
            raise AriaError("CANCELLED", "Event search cancelled")
        evaluations += count
        if evaluations > r.max_evaluations:
            raise AriaError("REQUEST_LIMIT", "Event evaluation budget exhausted")

    def extract(result: Any) -> tuple[float, float]:
        a = result.bodies[0]
        if len(result.bodies) == 1:
            return a.longitude_deg, a.longitude_rate_deg_day
        b = result.bodies[1]
        return circular_difference(
            a.longitude_deg, b.longitude_deg
        ), a.longitude_rate_deg_day - b.longitude_rate_deg_day

    grid = np.linspace(start, end, n)
    for i in range(0, n, 512):
        gg = grid[i : i + 512]
        guard(len(gg))
        results = engine.positions_batch(
            base, [TimeInput(jd=(float(j), 0), scale="TT") for j in gg]
        )
        cache.update((float(j), extract(p)) for j, p in zip(gg, results, strict=True))

    def evaluate(j: float) -> tuple[float, float]:
        if j not in cache:
            guard()
            cache[j] = extract(
                engine.positions(
                    PositionRequest(
                        TimeInput(jd=(j, 0), scale="TT"), bodies=bodies, strict=r.strict
                    )
                )
            )
        return cache[j]

    tolerance = r.tolerance_seconds / 86400
    candidates: list[tuple[float, int, float, str, Callable[[float], float]]] = []

    def add_root(fn: Callable[[float], float], a: float, b: float, label: str) -> None:
        root, it, width = bisect_root(fn, a, b, tolerance)
        candidates.append((root, it, width, label, fn))

    refined = [float(grid[0])]
    # Split at a rate extremum even if a longitude event has identical endpoint signs.
    for aa, bb in zip(grid[:-1], grid[1:], strict=True):
        a, b = float(aa), float(bb)
        va, vb = evaluate(a)[1], evaluate(b)[1]
        if va * vb < 0:

            def rate_residual(j: float) -> float:
                return evaluate(j)[1]

            root, it, width = bisect_root(rate_residual, a, b, tolerance)
            if r.kind == "station":
                candidates.append((root, it, width, "station", rate_residual))
            else:
                refined.append(root)
        elif r.kind == "station":
            if va == 0:
                candidates.append((a, 0, 0, "station", lambda j: evaluate(j)[1]))
            if vb == 0:
                candidates.append((b, 0, 0, "station", lambda j: evaluate(j)[1]))
        refined.append(b)
    if r.kind == "station":
        # A rate can touch zero without reversing sign. Refine sampled local
        # minima of |rate|, then accept only a numerically resolved zero.
        for i in range(1, len(grid) - 1):
            left, middle, right = map(float, grid[i - 1 : i + 2])
            vl, vm, vr = (evaluate(x)[1] for x in (left, middle, right))
            if vl * vr <= 0 or abs(vm) >= min(abs(vl), abs(vr)):
                continue
            a, b = left, right
            for _ in range(60):
                if b - a <= tolerance:
                    break
                x, y = a + (b - a) / 3, b - (b - a) / 3
                if abs(evaluate(x)[1]) < abs(evaluate(y)[1]):
                    b = y
                else:
                    a = x
            x = (a + b) / 2
            if abs(evaluate(x)[1]) <= 1e-10:
                candidates.append((x, 0, b - a, "grazing", lambda j: evaluate(j)[1]))
    if r.kind != "station":
        angle = 0 if r.kind == "conjunction" else (180 if r.kind == "opposition" else r.angle_deg)
        goals = (angle,) if angle in (0, 180) else (angle, 360 - angle)
        for a, b in zip(refined[:-1], refined[1:], strict=True):
            pa = evaluate(a)[0]
            pb = pa + circular_difference(evaluate(b)[0], pa)
            lo, hi = sorted((pa, pb))
            eps = max(abs(evaluate(a)[1]), abs(evaluate(b)[1])) * tolerance + 1e-10
            lo -= eps
            hi += eps
            targets: list[float]
            if r.kind == "ingress":
                targets = [30.0 * k for k in range(math.ceil(lo / 30), math.floor(hi / 30) + 1)]
            else:
                targets = [
                    g + 360 * k
                    for g in goals
                    for k in range(math.ceil((lo - g) / 360), math.floor((hi - g) / 360) + 1)
                ]
            for goal in targets:

                def phase_residual(j: float, g: float = goal) -> float:
                    return circular_difference(evaluate(j)[0], g)

                fa, fb = phase_residual(a), phase_residual(b)
                if fa * fb <= 0:
                    add_root(phase_residual, a, b, r.kind)
                elif abs(fa) <= eps:
                    candidates.append((a, 0, tolerance, r.kind, phase_residual))
                elif abs(fb) <= eps:
                    candidates.append((b, 0, tolerance, r.kind, phase_residual))
            # Grazing aspect at a solved extremum has no sign change.
            if r.kind != "ingress":
                for x in (a, b):
                    if abs(evaluate(x)[1]) < 1e-6:
                        for g in goals:

                            def grazing_residual(j: float, g: float = g) -> float:
                                return circular_difference(evaluate(j)[0], g)

                            if abs(grazing_residual(x)) <= 1e-7:
                                candidates.append((x, 0, 0, "grazing", grazing_residual))
    result: list[Event] = []
    for j, it, width, label, event_residual in sorted(candidates, key=lambda x: x[0]):
        if result and abs(j - sum(result[-1].jd_tt)) * 86400 <= max(r.tolerance_seconds, 0.001) * 2:
            continue
        h = 0.001
        if r.kind == "station":
            slope = (evaluate(min(end, j + h))[1] - evaluate(max(start, j - h))[1]) / (
                min(end, j + h) - max(start, j - h)
            )
        else:
            slope = evaluate(j)[1]
        condition = (
            "ill-conditioned" if label == "grazing" or abs(slope) < 1e-5 else "well-conditioned"
        )
        event_angle = (
            180
            if r.kind == "opposition"
            else (0 if r.kind in ("conjunction", "station", "ingress") else r.angle_deg)
        )
        qualification = engine.manifest.get("qualification", {})
        timing_qualified = (
            condition == "well-conditioned"
            and qualification.get("status") == "passed"
            and any(
                w["kind"] == r.kind
                and w["body"] == r.body
                and w.get("other") == r.other_body
                and w["angle"] == event_angle
                and w["interval_tt"][0] <= start
                and end <= w["interval_tt"][1]
                for w in qualification.get("event_windows", [])
            )
        )
        meta = {
            "dataset_id": engine.manifest["dataset_id"],
            "dataset_sha256": engine.manifest["sha256"],
            "engine_version": "0.1.0",
            "profile": "reference",
            "algorithm": "extrema-aware-bracket-v1",
            "scale": "TT",
            "origin": "geocentric",
            "frame": "true_ecliptic_of_date",
            "position_mode": "apparent",
            "time_quality": [t0.quality, t1.quality],
            "evaluations": evaluations,
            "scan_substep_days": step,
            "timing_qualified": timing_qualified,
            "timing_qualification_basis": "empirical matching-window reference agreement"
            if timing_qualified
            else "unqualified interval or conditioning",
            "residual_units": "deg/day" if r.kind == "station" else "deg",
            "coverage_claim": "empirical physical-body scan; not a formal root-completeness proof",
            "event_direction": "stationary"
            if r.kind == "station"
            else ("retrograde" if evaluate(j)[1] < 0 else "direct"),
        }
        integer = float(math.floor(j))
        result.append(
            Event(
                r.kind,
                r.body,
                r.other_body,
                (integer, j - integer),
                float(event_residual(j)),
                it,
                width * 86400,
                condition,
                meta,
            )
        )
    return tuple(result)


def serialise(events: tuple[Event, ...]) -> list[dict[str, Any]]:
    return [asdict(e) for e in events]
