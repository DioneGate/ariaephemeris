# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Launch-policy boundary replay against the original pinned EOP snapshot."""

import os
from dataclasses import replace

import pytest

from ariaephemeris import AriaError, Ephemeris, Observer, PositionRequest, TimeInput

pytestmark = pytest.mark.kernel


@pytest.fixture(scope="module")
def managed():
    kernel = os.getenv("ARIA_KERNEL")
    eop = os.getenv("ARIA_CIVIL_EOP")
    if not kernel or not eop:
        pytest.skip("Set ARIA_KERNEL and ARIA_CIVIL_EOP for original-source launch coverage")
    with (
        Ephemeris(kernel, eop_path=eop) as observed,
        Ephemeris(kernel, eop_path=eop, allow_predicted_eop=True) as predicted,
    ):
        yield observed, predicted


@pytest.mark.parametrize(
    ("value", "predictions", "available"),
    [
        ("1973-01-01T23:59:59Z", False, False),
        ("1973-01-02T00:00:00Z", False, True),
        ("2026-11-19T00:00:00Z", False, True),
        ("2026-11-19T00:00:01Z", False, False),
        ("2026-11-19T00:00:01Z", True, True),
        ("2026-12-19T23:59:59Z", True, True),
        ("2026-12-20T00:00:00Z", True, False),
    ],
)
def test_managed_chart_coverage(managed, value, predictions, available):
    engine = managed[predictions]
    request = PositionRequest(TimeInput(value), bodies=("sun",))
    observer = Observer(51.5, 0)
    assert len(engine.positions(request).bodies) == 1
    if available:
        assert len(engine.chart(request, observer).house_cusps_deg) == 12
    else:
        with pytest.raises(AriaError) as exc:
            engine.chart(request, observer)
        assert exc.value.code == "TIME_DATA_UNAVAILABLE"


@pytest.mark.parametrize(
    ("value", "available"),
    [
        ("1971-12-31T23:59:59Z", False),
        ("1972-01-01T00:00:00Z", True),
        ("2027-06-27T23:59:59Z", True),
        ("2027-06-28T00:00:00Z", False),
    ],
)
def test_strict_utc_planetary_coverage(engine, value, available):
    request = PositionRequest(TimeInput(value), bodies=("sun",))
    if available:
        assert len(engine.positions(request).bodies) == 1
    else:
        with pytest.raises(AriaError) as exc:
            engine.positions(request)
        assert exc.value.code == "TIME_DATA_UNAVAILABLE"


@pytest.mark.parametrize("accuracy", ["approximate", "unknown"])
def test_uncertain_time_policy(engine, accuracy):
    time = TimeInput("2020-01-01T12:00:00Z", time_accuracy=accuracy)
    request = PositionRequest(time, bodies=("moon",))
    assert len(engine.positions(request).bodies) == 1
    with pytest.raises(AriaError, match="specified time"):
        engine.chart(request, Observer(51.5, 0))
    with pytest.raises(AriaError, match="explicit approximate-time bound"):
        engine.birth_time_analysis(request)
    if accuracy == "approximate":
        bounded = replace(request, time=replace(time, uncertainty_seconds=900))
        assert engine.birth_time_analysis(bounded)["continuous_bounds"] is False
