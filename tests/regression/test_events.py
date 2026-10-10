# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Independent analytic functions reproduce wrap, recrossing and grazing bugs."""

from types import SimpleNamespace

import pytest

from ariaephemeris import EventRequest, TimeInput
from ariaephemeris.events import find_events


class Synthetic:
    manifest = {"dataset_id": "synthetic", "sha256": "0" * 64}

    def __init__(self, phase, rate):
        self.phase, self.rate = phase, rate

    def _coverage(self, times):
        pass

    def positions(self, request):
        x = sum(request.time.jd) - 2451545
        a = SimpleNamespace(longitude_deg=self.phase(x) % 360, longitude_rate_deg_day=self.rate(x))
        return SimpleNamespace(
            bodies=(a, SimpleNamespace(longitude_deg=0, longitude_rate_deg_day=0))
        )

    def positions_batch(self, request, times):
        return [self.positions(SimpleNamespace(time=t)) for t in times]


def search(engine, kind="conjunction"):
    return find_events(
        engine,
        EventRequest(
            TimeInput(jd=(2451545, 0), scale="TT"),
            TimeInput(jd=(2451545, 1), scale="TT"),
            kind,
            "moon",
            "sun",
            tolerance_seconds=0.001,
        ),
    )


def test_two_crossings_inside_one_original_step():
    # Same-sign endpoint residuals; the rate extremum must split the bracket.
    e = Synthetic(lambda x: ((x - 0.3) ** 2 - 0.0001) * 100, lambda x: 200 * (x - 0.3))
    roots = [sum(r.jd_tt) - 2451545 for r in search(e)]
    assert roots == pytest.approx([0.29, 0.31], abs=2e-8)


def test_grazing_contact_is_explicitly_ill_conditioned():
    e = Synthetic(lambda x: (x - 0.3) ** 2, lambda x: 2 * (x - 0.3))
    roots = search(e)
    assert len(roots) == 1
    assert sum(roots[0].jd_tt) - 2451545 == pytest.approx(0.3, abs=2e-8)
    assert roots[0].conditioning == "ill-conditioned"


def test_wrapped_perfection_and_both_endpoints():
    e = Synthetic(lambda x: 360 * x, lambda x: 360)
    roots = search(e)
    assert [sum(r.jd_tt) - 2451545 for r in roots] == pytest.approx([0, 1], abs=2e-8)


def test_tangential_station_is_reported_without_direction_reversal():
    e = Synthetic(lambda x: (x - 0.3) ** 3 / 3, lambda x: (x - 0.3) ** 2)
    roots = search(e, "station")
    assert len(roots) == 1
    assert sum(roots[0].jd_tt) - 2451545 == pytest.approx(0.3, abs=2e-8)
    assert roots[0].conditioning == "ill-conditioned"


def test_subnormal_scan_step_fails_before_allocation():
    from ariaephemeris import AriaError

    e = Synthetic(lambda x: x, lambda x: 1)
    r = EventRequest(
        TimeInput(jd=(2451545, 0), scale="TT"),
        TimeInput(jd=(2451546, 0), scale="TT"),
        "station",
        "moon",
        max_step_days=1e-320,
    )
    with pytest.raises(AriaError, match="budget"):
        find_events(e, r)
