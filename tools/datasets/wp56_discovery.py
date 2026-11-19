# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Independent, finite-grid JPL catalogue discovery; never imports Aria's engine.

Local cubic roots are roots of interpolants, not a continuous completeness proof.
IAU primitives are shared ERFA standards, not independently reimplemented models.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import erfa
import numpy as np

BODIES = ("mars", "jupiter", "saturn", "uranus", "neptune", "pluto")
SECONDS = 86400.0
# Lagrange coefficients for nodes [-1, 0, 1, 2], in increasing powers of x.
COEFFICIENTS = np.linalg.inv(np.vander([-1.0, 0.0, 1.0, 2.0], 4, increasing=True))


def workloads(spec: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for window in spec["windows"]:
        for body in window["bodies"]:
            for kind in ("station", "ingress"):
                output.append(dict(window=window["id"], body=body, other=None, kind=kind, angle=0))
        for body, other in combinations(window["bodies"], 2):
            events = [("conjunction", 0), ("opposition", 180)]
            if window["id"] == "2023-2025" and body == "mars":
                events += [("aspect", angle) for angle in (60, 90, 120)]
            for kind, angle in events:
                output.append(
                    dict(window=window["id"], body=body, other=other, kind=kind, angle=angle)
                )
    for row in output:
        row["id"] = ":".join(str(row[k]) for k in ("window", "kind", "body", "other", "angle"))
    return output


def tropical_longitudes(rows: list[dict[str, Any]]) -> np.ndarray:
    """Vectorised independent ICRF ray -> true ecliptic of each exact TT epoch."""
    times = np.array([r["jd_tt"] for r in rows])
    ra = np.radians([r["inertial_apparent_ra_deg"] for r in rows])
    dec = np.radians([r["inertial_apparent_dec_deg"] for r in rows])
    if not np.isfinite([times, ra, dec]).all() or np.any((ra < 0) | (ra >= 2 * np.pi)):
        raise ValueError("Nonfinite or out-of-range source ray")
    if np.any(np.abs(dec) > np.pi / 2):
        raise ValueError("Out-of-range source declination")
    rays = np.stack((np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)), axis=-1)
    tt2 = times - 2451545.0
    equatorial = np.einsum("ijk,ik->ij", erfa.pnm06a(2451545.0, tt2), rays)
    eps = erfa.obl06(2451545.0, tt2) + erfa.nut06a(2451545.0, tt2)[1]
    y = np.cos(eps) * equatorial[:, 1] + np.sin(eps) * equatorial[:, 2]
    return np.degrees(np.arctan2(y, equatorial[:, 0])) % 360.0


def identity(event: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(event[k] for k in ("kind", "body", "other", "goal_deg", "direction"))


def match_catalogues(
    reference: list[dict[str, Any]], actual: list[dict[str, Any]], tolerance_seconds: float
) -> dict[str, Any]:
    """Complete bipartite association: ambiguous edges never greedily disappear."""
    if not math.isfinite(tolerance_seconds) or tolerance_seconds <= 0:
        raise ValueError("Positive finite association tolerance required")
    if any(not math.isfinite(e["jd_tt"]) for e in reference + actual):
        raise ValueError("Nonfinite event time")
    edges = [
        (i, j)
        for i, a in enumerate(reference)
        for j, b in enumerate(actual)
        if identity(a) == identity(b)
        and abs(a["jd_tt"] - b["jd_tt"]) * SECONDS <= tolerance_seconds
    ]
    left = [[j for i0, j in edges if i0 == i] for i in range(len(reference))]
    right = [[i for i, j0 in edges if j0 == j] for j in range(len(actual))]
    pairs = [(i, j) for i, j in edges if len(left[i]) == len(right[j]) == 1]
    duplicate_pairs = [
        [i, j]
        for i, a in enumerate(actual)
        for j, b in enumerate(actual[:i])
        if identity(a) == identity(b) and abs(a["jd_tt"] - b["jd_tt"]) * SECONDS < 0.01
    ]
    return {
        "reference_count": len(reference),
        "actual_count": len(actual),
        "matches": [
            {
                "reference_index": i,
                "actual_index": j,
                "actual_minus_reference_seconds": (actual[j]["jd_tt"] - reference[i]["jd_tt"])
                * SECONDS,
            }
            for i, j in pairs
        ],
        "missing_reference_indices": [i for i, js in enumerate(left) if not js],
        "additional_actual_indices": [j for j, ii in enumerate(right) if not ii],
        "ambiguous_edges": [[i, j] for i, j in edges if len(left[i]) > 1 or len(right[j]) > 1],
        "duplicate_actual_pairs": duplicate_pairs,
        "passed": len(pairs) == len(reference) == len(actual) and not duplicate_pairs,
    }


def _real_roots(coefficients: np.ndarray) -> list[float]:
    scale = float(np.max(np.abs(coefficients)))
    if scale == 0:
        raise ValueError("Unresolved identically zero event panel")
    # A double real root may acquire a tiny imaginary part from roundoff.
    normalised = coefficients / scale
    while len(normalised) > 1 and abs(normalised[-1]) < 1e-12:
        normalised = normalised[:-1]
    roots = np.polynomial.polynomial.polyroots(normalised)
    return sorted(float(r.real) for r in roots if abs(r.imag) < 1e-5)


def discover(
    times: np.ndarray,
    longitudes: np.ndarray,
    workload: dict[str, Any],
    interval: tuple[float, float],
    other: np.ndarray | None = None,
) -> list[dict[str, Any]]:
    """Enumerate all real local cubic (or cubic derivative) roots per panel.

    Four independent source nodes surround each panel. Sample padding is mandatory.
    Step/grid convergence tests the interpolant dependency empirically.
    """
    times, longitudes = np.asarray(times), np.asarray(longitudes)
    if len(times) < 6 or times.shape != longitudes.shape:
        raise ValueError("Complete padded source grid required")
    if not np.isfinite(times).all() or not np.isfinite(longitudes).all():
        raise ValueError("Nonfinite independent source grid")
    step = float(times[1] - times[0])
    if step <= 0 or not np.allclose(np.diff(times), step, rtol=0, atol=1e-9):
        raise ValueError("Missing or nonuniform reference source grid")
    if not times[1] <= interval[0] < interval[1] <= times[-2]:
        raise ValueError("Insufficient source padding or invalid window")
    changes = (np.diff(longitudes) + 180) % 360 - 180
    if np.any(np.abs(changes) >= 90):
        raise ValueError("Unresolved circular jump in reference source")
    phase = np.degrees(np.unwrap(np.radians(longitudes)))
    if other is not None:
        other = np.asarray(other)
        if other.shape != times.shape or not np.isfinite(other).all():
            raise ValueError("Incomplete second-body reference source")
        delta = (np.diff(other) + 180) % 360 - 180
        if np.any(np.abs(delta) >= 90):
            raise ValueError("Unresolved second-body circular jump")
        phase -= np.degrees(np.unwrap(np.radians(other)))
    nodes = np.lib.stride_tricks.sliding_window_view(phase, 4)
    coefficients = nodes @ COEFFICIENTS.T
    events: list[dict[str, Any]] = []
    station = workload["kind"] == "station"
    for panel, c in enumerate(coefficients):
        left = float(times[panel + 1])
        if left + step < interval[0] or left > interval[1]:
            continue
        derivative = np.array([c[1], 2 * c[2], 3 * c[3]])
        extrema = [] if np.max(np.abs(derivative)) == 0 else _real_roots(derivative)
        if station:
            if np.max(np.abs(derivative)) == 0:
                raise ValueError("Unresolved stationary plateau")
            targets: list[float | None] = [None]
        else:
            values = [
                float(np.polynomial.polynomial.polyval(x, c))
                for x in [0, 1] + [r for r in extrema if 0 < r < 1]
            ]
            lo, hi = min(values) - 1e-10, max(values) + 1e-10
            if workload["kind"] == "ingress":
                targets = [30.0 * k for k in range(math.ceil(lo / 30), math.floor(hi / 30) + 1)]
            else:
                angle = workload["angle"]
                goals = [angle] if angle in (0, 180) else [angle, 360 - angle]
                targets = [
                    g + 360.0 * k
                    for g in goals
                    for k in range(math.ceil((lo - g) / 360), math.floor((hi - g) / 360) + 1)
                ]
        for goal in targets:
            equation = derivative.copy() if station else c.copy()
            if not station:
                equation[0] -= goal
            roots = _real_roots(equation)
            for x in roots:
                if not -1e-7 <= x <= 1 + 1e-7:
                    continue
                x = min(max(x, 0), 1)
                jd = left + step * x
                # Snap numerical endpoint roots before half-open ownership.
                for endpoint in interval:
                    if abs(jd - endpoint) < 1e-8:
                        jd = endpoint
                if not interval[0] <= jd < interval[1]:
                    continue
                slope = float(
                    (2 * c[2] + 6 * c[3] * x) / step**2
                    if station
                    else np.polynomial.polynomial.polyval(x, derivative) / step
                )
                direction = (
                    ("retrograde-to-direct" if slope > 0 else "direct-to-retrograde")
                    if station
                    else ("direct" if slope > 0 else "retrograde")
                )
                ambiguous = abs(slope) < 1e-7
                if ambiguous:
                    direction = "grazing"
                event = {
                    "kind": workload["kind"],
                    "body": workload["body"],
                    "other": workload["other"],
                    "goal_deg": None if station else round(float(goal) % 360, 8),
                    "direction": direction,
                    "jd_tt": jd,
                    "source_panel_jd_tt": [left, left + step],
                    "equation_slope_per_tt_day": slope,
                    "ambiguous": ambiguous,
                    "interpolation_error_bound_established": False,
                }
                if not any(
                    identity(e) == identity(event) and abs(e["jd_tt"] - jd) < 1e-7
                    for e in events[-4:]
                ):
                    events.append(event)
    return sorted(events, key=lambda e: (e["jd_tt"], str(identity(e))))
