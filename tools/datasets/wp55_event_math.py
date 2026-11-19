# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Bounded, offline reference-root interpolation. No Aria predictions in roots.

The inputs must be independently acquired JPL Horizons apparent angles/rates
at a predeclared uniform TT grid. A local four-node cubic is used only within
a directly observed sign-change bracket. Its accuracy is NOT a rigorous error
bound: the cubic-vs-linear difference and original sample bracket are reported.
"""

from __future__ import annotations

import math
from typing import Any

SECONDS_PER_DAY = 86400.0
GRID_STEP_DAYS = 0.03125
GRID_RADIUS = 4
RATE_STEP_DAYS = 0.0125
RATE_STENCIL = (-2, -1, 0, 1, 2)
CANDIDATE_TIMING_SECONDS = 60.0
BODY_ORDER = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
PAIRS = tuple(("mars", other) for other in BODY_ORDER if other != "mars")


def stamp(jd: float) -> float:
    if not math.isfinite(jd):
        raise ValueError("Nonfinite TT epoch")
    return round(jd, 7)


def signed_angle(a: float, b: float) -> float:
    return (a - b + 180) % 360 - 180


def grid(jd: float) -> list[float]:
    """Nine independent TT observation times around an Aria-nominated epoch."""
    return [stamp(jd + k * GRID_STEP_DAYS) for k in range(-GRID_RADIUS, GRID_RADIUS + 1)]


def station_stencil(jd: float) -> list[float]:
    return [stamp(jd + k * RATE_STEP_DAYS) for k in RATE_STENCIL]


def _cubic(xs: list[float], ys: list[float], jd: float) -> float:
    """Four-point Lagrange interpolation, using local epoch offsets."""
    if len(xs) != 4 or len(set(xs)) != 4:
        raise ValueError("Exactly four distinct cubic epochs required")
    origin = xs[1]
    x = jd - origin
    local = [k - origin for k in xs]
    total = 0.0
    for i in range(4):
        weight = 1.0
        for j in range(4):
            if i != j:
                weight *= (x - local[j]) / (local[i] - local[j])
        total += ys[i] * weight
    return total


def locate_reference_root(times: list[float], values: list[float]) -> dict[str, Any]:
    """One unambiguous sign-change JPL root; no invented exact source truth."""
    if (
        len(times) != 2 * GRID_RADIUS + 1
        or len(values) != len(times)
        or any(not math.isfinite(x) for x in times + values)
        or any(b <= a for a, b in zip(times[:-1], times[1:], strict=True))
    ):
        raise ValueError("Nine complete, monotone finite independent Horizons samples required")
    if any(
        abs((b - a) - GRID_STEP_DAYS) > 2e-7 for a, b in zip(times[:-1], times[1:], strict=True)
    ):
        raise ValueError("Reference observation grid has missing or shifted TT samples")
    crossings = []
    for i in range(len(values) - 1):
        left, right = values[i], values[i + 1]
        if abs(right - left) > 90:
            raise ValueError("Wrapped phase discontinuity must not be used as event root")
        if left == 0 or right == 0 or left * right < 0:
            crossings.append(i)
    if len(crossings) != 1:
        raise ValueError(
            f"Expected exactly one independent JPL root bracket, found {len(crossings)}"
        )
    idx = crossings[0]
    lo, hi = times[idx], times[idx + 1]
    y0, y1 = values[idx], values[idx + 1]
    if y0 == 0:
        root = lo
    elif y1 == 0:
        root = hi
    else:
        first = min(max(idx - 1, 0), len(times) - 4)
        xs, ys = times[first : first + 4], values[first : first + 4]
        fl = _cubic(xs, ys, lo)
        fr = _cubic(xs, ys, hi)
        if fl * fr > 0:
            raise ValueError("Cubic and independently observed JPL root brackets disagree")
        a, b = lo, hi
        for _ in range(45):
            mid = (a + b) / 2
            fm = _cubic(xs, ys, mid)
            if fm == 0 or a == mid or b == mid:
                a = b = mid
                break
            if (fl <= 0 <= fm) or (fm <= 0 <= fl):
                b, fr = mid, fm
            else:
                a, fl = mid, fm
        root = (a + b) / 2
    linear = lo if y0 == 0 else hi if y1 == 0 else lo - y0 * (hi - lo) / (y1 - y0)
    if root < lo - 1e-9 or root > hi + 1e-9:
        raise ValueError("Interpolated root escaped independent observed reference bracket")
    # Local slope of the independently sourced cubic (or two-point slope at an exact node).
    index0 = min(max(idx - 1, 0), len(times) - 4)
    xx, yy = times[index0 : index0 + 4], values[index0 : index0 + 4]
    d = 1e-4
    slope = (_cubic(xx, yy, root + d) - _cubic(xx, yy, root - d)) / (2 * d)
    return {
        "jd_tt": root,
        "reference_bracket_jd_tt": [lo, hi],
        "reference_bracket_width_seconds": (hi - lo) * SECONDS_PER_DAY,
        "linear_root_jd_tt": linear,
        "cubic_minus_linear_seconds": (root - linear) * SECONDS_PER_DAY,
        "local_signed_slope_per_tt_day": slope,
        "interpolation_method": "four-point local cubic inside observed JPL sign-change bracket",
        "interpolation_error_bound_established": False,
        "sampled_reference_root_unique_in_grid": True,
    }
