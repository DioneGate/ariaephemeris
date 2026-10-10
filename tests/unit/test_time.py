# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import pytest

from ariaephemeris import AriaError, TimeInput
from ariaephemeris.time import delta_t_model, resolve


def test_j2000_tt():
    t = resolve(TimeInput(jd=(2451545.0, 0.0), scale="TT"))
    assert t.tt1 + t.tt2 == 2451545.0
    assert abs(t.tdb1 + t.tdb2 - 2451545.0) < 1e-7


def test_tt_tdb_round_trip():
    t = resolve(TimeInput(jd=(2451545.0, 0.123456789), scale="TT"))
    back = resolve(TimeInput(jd=(t.tdb1, t.tdb2), scale="TDB"))
    assert abs((back.tt1 - t.tt1) + (back.tt2 - t.tt2)) < 1e-13


def test_leap_seconds_are_uniform_in_tt():
    tt = [
        resolve(TimeInput(t))
        for t in ["2016-12-31T23:59:59Z", "2016-12-31T23:59:60Z", "2017-01-01T00:00:00Z"]
    ]
    for a, b in zip(tt[:-1], tt[1:]):
        assert ((b.tt1 - a.tt1) + (b.tt2 - a.tt2)) * 86400 == pytest.approx(1, abs=1e-9)


def test_invalid_leap_second():
    with pytest.raises(AriaError):
        resolve(TimeInput("2016-12-30T23:59:60Z"))


def test_dst_gap_and_fold():
    with pytest.raises(AriaError, match="DST gap"):
        resolve(TimeInput("2026-03-29T01:30:00", timezone="Europe/London"))
    with pytest.raises(AriaError, match="fold"):
        resolve(TimeInput("2026-10-25T01:30:00", timezone="Europe/London"))
    a = resolve(TimeInput("2026-10-25T01:30:00", timezone="Europe/London", fold=0))
    b = resolve(TimeInput("2026-10-25T01:30:00", timezone="Europe/London", fold=1))
    assert ((b.tt1 - a.tt1) + (b.tt2 - a.tt2)) * 86400 == pytest.approx(3600, abs=1e-8)


def test_historical_and_future_inputs_do_not_invent_utc():
    with pytest.raises(AriaError, match="Pre-1972"):
        resolve(TimeInput("1900-01-01T00:00:00Z"))
    with pytest.raises(AriaError, match="validity"):
        resolve(TimeInput("2100-01-01T00:00:00Z"))
    t = resolve(TimeInput("2100-01-01T00:00:00Z"), strict=False)
    assert t.quality["utc_status"] == "assumed"


def test_rotation_requires_data_in_strict_mode():
    with pytest.raises(AriaError):
        resolve(TimeInput("2000-01-01T00:00:00Z"), require_ut1=True)
    t = resolve(TimeInput("2000-01-01T00:00:00Z"), strict=False, require_ut1=True)
    assert t.ut11 is not None and t.quality["warnings"]


def test_delta_t_published_values():
    assert delta_t_model(1900) == pytest.approx(-2.79)
    assert delta_t_model(2000) == pytest.approx(63.86)
    assert delta_t_model(2050) == pytest.approx(93.0)
