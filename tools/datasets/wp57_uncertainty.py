# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Pure unit-aware sensitivity and independently sourced station refinement.

Empirical convergence and model disagreement are never physical error bounds.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.interpolate import CubicSpline
from wp56_discovery import SECONDS, match_catalogues, tropical_longitudes


def signed_rate(longitudes: list[float], step_days: float) -> float:
    if (
        len(longitudes) != 5
        or not math.isfinite(step_days)
        or step_days <= 0
        or not np.isfinite(longitudes).all()
    ):
        raise ValueError("Five finite longitudes and a positive TT-day step required")
    residual = [(value - longitudes[2] + 180) % 360 - 180 for value in longitudes]
    if any(abs(x) > 90 for x in residual):
        raise ValueError("Unresolved circular differentiation stencil")
    return (residual[0] - 8 * residual[1] + 8 * residual[3] - residual[4]) / (12 * step_days)


def sensitivity_seconds(residual: float, slope_per_tt_day: float) -> float | None:
    """First-order |delta f/f'|, NOT a bound; returns unknown at a zero slope.

    For station f is deg/TT day and f' is deg/TT day². For angular crossings
    f is deg and f' is deg/TT day. Never mix these two input unit families.
    """
    if not math.isfinite(residual) or not math.isfinite(slope_per_tt_day):
        raise ValueError("Finite residual and equation slope required")
    if slope_per_tt_day == 0:
        return None
    value = abs(residual / slope_per_tt_day) * SECONDS
    return value if math.isfinite(value) else None


def continuous_station_roots(
    times: np.ndarray, longitudes: np.ndarray, body: str, interval: tuple[float, float]
) -> list[dict[str, Any]]:
    """All stationary roots of a C2 source spline; no derivative jumps at knots.

    Piecewise independent four-node cubics are only C0 and can produce double or
    missing derivative roots around a knot. The original failed evidence remains
    frozen; this is a separately identified continuous reference interpolant.
    """
    if (
        len(times) < 6
        or times.shape != longitudes.shape
        or not np.isfinite([times, longitudes]).all()
    ):
        raise ValueError("Complete finite source station grid required")
    differences = np.diff(times)
    if np.any(differences <= 0) or not np.allclose(differences, differences[0], atol=1e-9, rtol=0):
        raise ValueError("Missing or nonuniform station samples")
    if not times[1] <= interval[0] < interval[1] <= times[-2]:
        raise ValueError("Insufficient station source padding")
    changes = (np.diff(longitudes) + 180) % 360 - 180
    if np.any(np.abs(changes) >= 90):
        raise ValueError("Unresolved circular station jump")
    y = np.degrees(np.unwrap(np.radians(longitudes)))
    origin = float(times[len(times) // 2])
    spline = CubicSpline(
        times - origin, y - y[len(y) // 2], bc_type="not-a-knot", extrapolate=False
    )
    derivative = spline.derivative()
    roots = derivative.roots(extrapolate=False)
    if not np.isfinite(roots).all():
        raise ValueError("Unresolved stationary plateau")
    output = []
    for local in sorted(roots):
        jd = origin + float(local)
        if not interval[0] <= jd < interval[1]:
            continue
        acceleration = float(spline(float(local), 2))
        ambiguous = abs(acceleration) < 1e-7
        i = int(np.clip(np.searchsorted(times, jd) - 1, 0, len(times) - 2))
        event = dict(
            kind="station",
            body=body,
            other=None,
            goal_deg=None,
            jd_tt=jd,
            direction="grazing"
            if ambiguous
            else "retrograde-to-direct"
            if acceleration > 0
            else "direct-to-retrograde",
            equation_slope_per_tt_day=acceleration,
            source_panel_jd_tt=[float(times[i]), float(times[i + 1])],
            ambiguous=ambiguous,
            interpolation_error_bound_established=False,
            interpolant="C2 not-a-knot cubic spline of original JPL tropical longitudes",
        )
        if not output or abs(output[-1]["jd_tt"] - jd) > 1e-8:
            output.append(event)
    return output


def refine_stations(
    spec: dict[str, Any], sources: dict[tuple[str, float], dict[str, Any]], previous: dict[str, Any]
) -> list[dict[str, Any]]:
    old = {r["workload"]["id"]: r for r in previous["records"]}
    records = []
    for case in spec["station_centres"]:
        # These epochs depend ONLY on the original JPL catalogue, not Aria times.
        times = np.array(
            [round(case["jd_tt"] + i * spec["station_source_step_days"], 7) for i in range(-32, 33)]
        )
        rays = [sources[(case["body"], t)] for t in times]
        lon = tropical_longitudes(rays)
        original = old[case["workload_id"]]
        radius = spec["station_search_radius_days"]
        interval = case["jd_tt"] - radius, case["jd_tt"] + radius
        grids = {}
        for grid in spec["station_grids"]:
            sl = slice(grid["offset"], None, grid["stride"])
            grids[grid["name"]] = continuous_station_roots(
                times[sl], lon[sl], case["body"], interval
            )
        fine = grids["45-minute"]
        comparisons = {
            name: match_catalogues(fine, roots, spec["reference_convergence_seconds"])
            for name, roots in grids.items()
            if name != "45-minute"
        }
        actual = [e for e in original["aria_events"] if interval[0] <= e["jd_tt"] < interval[1]]
        agreement = match_catalogues(fine, actual, spec["aria_association_seconds"])
        rates = {}
        for h in (0.03125, 0.0625, 0.125):
            wanted = [round(case["jd_tt"] + k * h, 7) for k in (-2, -1, 0, 1, 2)]
            indexes = [int(np.where(times == t)[0][0]) for t in wanted]
            rates[str(h)] = signed_rate([float(lon[i]) for i in indexes], h)
        slope = fine[0]["equation_slope_per_tt_day"] if len(fine) == 1 else None
        spread = max(rates.values()) - min(rates.values())
        resolved = (
            len(fine) == 1
            and not fine[0]["ambiguous"]
            and all(c["passed"] for c in comparisons.values())
        )
        records.append(
            dict(
                id=case["id"],
                body=case["body"],
                jpl_only_anchor_jd_tt=case["jd_tt"],
                original_workload=case["workload_id"],
                original_reference_converged=original["reference_resolved"],
                roots_by_grid=grids,
                grid_comparisons=comparisons,
                aria_events_from_frozen_009=actual,
                aria_comparison=agreement,
                reference_resolved=resolved,
                source_rates_deg_tt_day=rates,
                source_rate_step_spread_deg_tt_day=spread,
                source_rate_spread_timing_proxy_seconds=sensitivity_seconds(spread, slope)
                if slope is not None
                else None,
                equation_acceleration_deg_tt_day2=slope,
                hypothetical_1e_minus4_rate_timing_proxy_seconds=sensitivity_seconds(0.0001, slope)
                if slope is not None
                else None,
                physical_time_uncertainty_seconds=None,
                interpolation_error_bound_established=False,
                passed=resolved and agreement["passed"],
            )
        )
    return records


def uncertainty_register() -> list[dict[str, Any]]:
    entries = [
        (
            "U01",
            "Implementation agreement",
            "sampled same-source agreement",
            "Pinned SPKs, evaluator and full regression checks; not physical truth",
            "Qualified evaluator residuals and source hashes",
        ),
        (
            "U02",
            "Planetary/observer/centre models",
            "measured model disagreement",
            "Component attribution includes differing correlated trajectories; no sigma or model ranking",
            "Applicable observational covariance or validated physical bounds per body/epoch",
        ),
        (
            "U03",
            "Horizons query paths",
            "measured context gaps",
            "Direct centre, parent and SSB paths may select different chains; retain signed closure",
            "Independently matched chain and frame/source identity",
        ),
        (
            "U04",
            "Reference interpolation and rates",
            "empirical refinement",
            "Finite cubic/derivative step agreement is not a rigorous continuous bound",
            "Validated interpolation/quantisation bounds or direct source brackets for each claim",
        ),
        (
            "U05",
            "Frames and apparent corrections",
            "shared standard dependency",
            "Separate code paths share ERFA IAU 2006/2000A; source correction conventions remain explicit",
            "Independent convention-matched transform/correction qualification",
        ),
        (
            "U06",
            "Source decimal precision",
            "format precision only",
            "Printed RA/Dec digits do not establish physical accuracy; differentiation can amplify quantisation",
            "Independent numerical quantisation analysis with declared source formatting",
        ),
        (
            "U07",
            "Civil time and Earth orientation",
            "outside TT scope",
            "Geocentric TT station evidence does not qualify UTC, UT1, EOP or birth-time uncertainty",
            "P2 civil-time/EOP evidence and per-request assumptions",
        ),
        (
            "U08",
            "Commercial accuracy decision",
            "open",
            "D07 comparison criteria are distinct from absolute physical uncertainty",
            "Owner approval of metrics, conventions, intervals and claim wording",
        ),
    ]
    return [
        dict(
            id=i,
            quantity=q,
            status=s,
            evidence_interpretation=e,
            absolute_physical_bound=None,
            closure_requirement=c,
        )
        for i, q, s, e, c in entries
    ]
