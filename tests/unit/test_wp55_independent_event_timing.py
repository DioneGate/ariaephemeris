# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline synthetic WP5.5 independent JPL-root and event-selection tests."""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

import erfa
import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
import acquire_wp55_events as acquisition  # noqa: E402
import compare_wp55_events as comparison  # noqa: E402
import wp55_event_math as m  # noqa: E402


def test_cubic_finds_independent_station_and_ingress_roots_inside_observed_brackets():
    origin = 2460100.0
    times = m.grid(origin)
    root = origin + 0.0075
    vals = [(t - root) * (1.0 + 0.15 * (t - root) ** 2) for t in times]
    observed = m.locate_reference_root(times, vals)
    assert abs(observed["jd_tt"] - root) * m.SECONDS_PER_DAY < 0.01
    assert observed["reference_bracket_jd_tt"][0] <= root <= observed["reference_bracket_jd_tt"][1]
    assert observed["reference_bracket_width_seconds"] == pytest.approx(2700, abs=0.01)
    assert not observed["interpolation_error_bound_established"]


def test_multiple_roots_and_wrapped_false_discontinuities_fail_closed():
    epochs = m.grid(2460100.0)
    with pytest.raises(ValueError, match="exactly one"):
        m.locate_reference_root(epochs, [(-1) ** i for i in range(9)])
    with pytest.raises(ValueError, match="discontinuity"):
        m.locate_reference_root(epochs, [-179] * 4 + [179] * 5)
    with pytest.raises(ValueError, match="Nine"):
        m.locate_reference_root(epochs[:3], [-1, 0, 1])
    with pytest.raises(ValueError, match="shifted"):
        m.locate_reference_root(epochs[:-1] + [epochs[-1] + 1], list(range(-4, 5)))


def test_station_tt_rate_stencil_does_not_confuse_scale_or_motion_sign():
    assert m.station_stencil(2451545.0) == [
        2451544.975,
        2451544.9875,
        2451545.0,
        2451545.0125,
        2451545.025,
    ]
    assert m.signed_angle(359.999, 0.001) == pytest.approx(-0.002)
    assert m.signed_angle(180.001, 0.0) == pytest.approx(-179.999)
    assert m.CANDIDATE_TIMING_SECONDS == 60.0


def _as_icrf_ecliptic_lon(lon_deg: float, jd_tt: float) -> tuple[float, float]:
    """Invert the *named IAU* true-of-date reference transform synthetically."""
    a = math.radians(lon_deg)
    ecl = [math.cos(a), math.sin(a), 0.0]
    t1, t2 = 2451545.0, jd_tt - 2451545.0
    eps = float(erfa.obl06(t1, t2) + erfa.nut06a(t1, t2)[1])
    equator = [
        ecl[0],
        math.cos(eps) * ecl[1],
        math.sin(eps) * ecl[1],
    ]
    v = erfa.pnm06a(t1, t2).T @ equator
    ra = math.degrees(math.atan2(v[1], v[0])) % 360
    dec = math.degrees(math.atan2(v[2], math.hypot(v[0], v[1])))
    return ra, dec


def test_horizons_root_equations_cover_station_ingress_conjunction_opposition():
    origin = 2460100.0
    times = m.grid(origin)
    goal = 0.0
    rays = {
        (body, jd): _as_icrf_ecliptic_lon(
            (15 if body == "mars" else 15.1) + (jd - origin) * (2 if body == "mars" else 1),
            jd,
        )
        for body in ("mars", "jupiter")
        for jd in times
    }
    common = {"body": "mars", "jd_tt_grid": times, "reference_rate_stencils": []}
    case = {**common, "kind": "conjunction", "other_body": "jupiter", "goal_deg": goal}
    observed, _ = comparison.reference_function(case, rays)
    assert m.locate_reference_root(times, observed)["jd_tt"] == pytest.approx(
        origin + 0.1, abs=1e-7
    )
    case = {**common, "kind": "opposition", "other_body": "jupiter", "goal_deg": 180}
    rays = {
        (body, jd): _as_icrf_ecliptic_lon(
            (15 if body == "mars" else 195.1) + (jd - origin) * (2 if body == "mars" else 1),
            jd,
        )
        for body in ("mars", "jupiter")
        for jd in times
    }
    observed, _ = comparison.reference_function(case, rays)
    assert m.locate_reference_root(times, observed)["jd_tt"] == pytest.approx(
        origin + 0.1, abs=1e-7
    )
    case = {**common, "kind": "ingress", "other_body": None, "goal_deg": 30}
    rays = {("mars", jd): _as_icrf_ecliptic_lon(30 + 2 * (jd - origin - 0.031), jd) for jd in times}
    observed, _ = comparison.reference_function(case, rays)
    assert m.locate_reference_root(times, observed)["jd_tt"] == pytest.approx(
        origin + 0.031, abs=1e-7
    )


def test_station_reference_uses_external_symmetric_direction_stencils():
    origin = 2460100.0
    times = m.grid(origin)
    case = {
        "kind": "station",
        "body": "mars",
        "other_body": None,
        "goal_deg": None,
        "jd_tt_grid": times,
        "reference_rate_stencils": [m.station_stencil(t) for t in times],
    }
    # An exact quadratic longitude gives linear signed rate crossing at +0.02d.
    rays = {
        ("mars", jd): _as_icrf_ecliptic_lon(19 + 0.4 * (jd - origin - 0.02) ** 2, jd)
        for stencil in case["reference_rate_stencils"]
        for jd in stencil
    }
    observed, records = comparison.reference_function(case, rays)
    root = m.locate_reference_root(times, observed)
    assert abs(root["jd_tt"] - (origin + 0.02)) * m.SECONDS_PER_DAY < 0.5
    assert len(records) == 9


class FakePositionsEngine:
    def __init__(self, epoch: float):
        self.epoch = epoch

    def positions(self, request):
        jd = sum(request.time.jd)
        bodies = request.bodies
        return SimpleNamespace(bodies=tuple(self._body(b, jd) for b in bodies))

    def _body(self, name, jd):
        if name == "mars":
            lon = 50 + (jd - self.epoch) * 2
        else:
            lon = 50.4 + (jd - self.epoch)
        return SimpleNamespace(longitude_deg=lon % 360, target_id=499)

    def positions_batch(self, request, times):
        return tuple(
            SimpleNamespace(bodies=tuple(self._body(b, sum(t.jd)) for b in request.bodies))
            for t in times
        )


def test_pair_candidate_nomination_does_not_supply_reference_answer():
    origin = 2460000.0
    engine = FakePositionsEngine(origin)
    bracket = acquisition._bisect_pair(engine, "jupiter", "conjunction", origin, origin + 1)
    assert bracket == pytest.approx(origin + 0.4, abs=1e-7)
    assert set(acquisition.TARGETS) == set(m.BODY_ORDER)
    assert len(m.PAIRS) == 5


def test_stats_and_release_scope_are_diagnostic_not_scientific_certification():
    assert comparison.distribution([0, 1, 2, 3])["p95"] == pytest.approx(2.85)
    with pytest.raises(ValueError, match="Nonfinite"):
        comparison.distribution([])
