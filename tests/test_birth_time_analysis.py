# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Bounded uncertain-time semantics and real-source regressions."""

import json
from dataclasses import replace

import pytest

from ariaephemeris import AriaError, Observer, PositionRequest, TimeInput
from ariaephemeris.time import resolve


def request(value="2000-01-01T12:00:00Z", **kw):
    return PositionRequest(
        TimeInput(value=value, time_accuracy="approximate", uncertainty_seconds=900, **kw),
        bodies=("sun", "moon"),
    )


@pytest.mark.kernel
def test_samples_match_independent_scalar_calls(engine):
    r = request()
    result = engine.birth_time_analysis(r, samples=5)
    centre = resolve(r.time)
    assert result["continuous_bounds"] is False
    assert result["physical_uncertainty"] is None
    assert len(result["samples"]) == 5
    for sample in result["samples"]:
        t = centre.shift(sample["offset_seconds"] / 86400, earth_rotation=False)
        scalar = engine.positions(replace(r, time=TimeInput(scale="TT", jd=(t.tt1, t.tt2))))
        for a, b in zip(sample["positions"]["bodies"], scalar.bodies, strict=True):
            assert a["longitude_deg"] == b.longitude_deg
            assert a["longitude_rate_deg_day"] == b.longitude_rate_deg_day
    json.dumps(result, allow_nan=False)


@pytest.mark.kernel
def test_wrap_and_moon_range(engine):
    r = request("2000-03-20T07:35:00Z")
    result = engine.birth_time_analysis(r)
    sun = result["ranges"]["sun"]
    assert sun["sampled_offset_min_deg"] < 0 < sun["sampled_offset_max_deg"]
    assert sun["sampled_offset_max_deg"] - sun["sampled_offset_min_deg"] < 1
    assert result["ranges"]["moon"]["sampled_offset_max_deg"] > sun["sampled_offset_max_deg"]


@pytest.mark.kernel
@pytest.mark.parametrize("count", [True, 2, 4, 1003, 3.0])
def test_budget(engine, count):
    with pytest.raises(AriaError, match="samples"):
        engine.birth_time_analysis(request(), samples=count)


@pytest.mark.kernel
@pytest.mark.parametrize(
    "time",
    [
        TimeInput(value="2000-01-01T12:00:00Z", time_accuracy="unknown"),
        TimeInput(value="2000-01-01T12:00:00Z", time_accuracy="approximate"),
        TimeInput(value="2000-01-01T12:00:00Z"),
    ],
)
def test_unbounded_time_never_assumed(engine, time):
    with pytest.raises(AriaError, match="bound"):
        engine.birth_time_analysis(PositionRequest(time))


@pytest.mark.kernel
@pytest.mark.parametrize("value", ["1972-01-01T00:01:00Z", "2027-06-27T23:59:00Z"])
def test_interval_cannot_bypass_utc_limits(engine, value):
    with pytest.raises(AriaError, match="UTC coverage"):
        engine.birth_time_analysis(request(value))


@pytest.mark.kernel
def test_leap_interval_elapsed_seconds(engine):
    result = engine.birth_time_analysis(request("2016-12-31T23:59:60Z"), samples=3)
    a, _, b = result["samples"]
    ta = a["positions"]["metadata"]["time"]["jd_tt"]
    tb = b["positions"]["metadata"]["time"]["jd_tt"]
    assert ((tb[0] - ta[0]) + (tb[1] - ta[1])) * 86400 == pytest.approx(1800, abs=1e-8)


@pytest.mark.kernel
def test_historical_and_guards(engine):
    result = engine.birth_time_analysis(
        request("1950-01-01T12:00:00Z", civil_policy="historical-ut1-v1", delta_t_seconds=29)
    )
    assert result["input_time"]["quality"]["effective_input_scale"] == "UT1"
    with pytest.raises(AriaError, match="historical policy"):
        engine.birth_time_analysis(
            request("1971-12-31T23:59:00Z", civil_policy="historical-ut1-v1", delta_t_seconds=42)
        )
    with pytest.raises(AriaError):
        engine.chart(request(), Observer(51, 0))
    with pytest.raises(AriaError, match="geocentric"):
        engine.birth_time_analysis(replace(request(), origin="topocentric"))
    with pytest.raises(AriaError, match="Maximum uncertainty"):
        engine.birth_time_analysis(
            replace(request(), time=replace(request().time, uncertainty_seconds=86401))
        )


@pytest.mark.kernel
def test_coverage_and_civil_failures(engine):
    with pytest.raises(AriaError, match="Operating interval"):
        engine.birth_time_analysis(
            PositionRequest(
                TimeInput(
                    value="1900-01-01T00:01:00",
                    scale="TT",
                    time_accuracy="approximate",
                    uncertainty_seconds=900,
                )
            )
        )
    with pytest.raises(AriaError) as e:
        engine.birth_time_analysis(request("2000-10-29T01:30:00", timezone="Europe/London"))
    assert e.value.code == "AMBIGUOUS_LOCAL_TIME"
    with pytest.raises(AriaError) as e:
        engine.birth_time_analysis(request("2000-03-26T01:30:00", timezone="Europe/London"))
    assert e.value.code == "NONEXISTENT_LOCAL_TIME"


@pytest.mark.kernel
def test_cli(engine, tmp_path, capsys):
    from dataclasses import asdict

    from ariaephemeris.cli import main

    path = tmp_path / "analysis.json"
    path.write_text(json.dumps({**asdict(request()), "samples": 3}))
    assert (
        main(
            [
                "birth-time-analysis",
                "--kernel",
                __import__("os").environ["ARIA_KERNEL"],
                "--request",
                str(path),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["sample_count"] == 3


@pytest.mark.kernel
@pytest.mark.parametrize(
    "change",
    [
        {"origin": "topocentric", "observer": Observer(51, 0)},
        {
            "time": TimeInput(
                value="2000-01-01T12:00:00Z", time_accuracy="approximate", uncertainty_seconds=86401
            )
        },
    ],
)
def test_unsupported_interval(engine, change):
    with pytest.raises(AriaError):
        engine.birth_time_analysis(replace(request(), **change))


@pytest.mark.kernel
def test_local_time_ambiguity_and_offset_equivalence(engine):
    local = request("2020-10-25T01:30:00", timezone="Europe/London")
    with pytest.raises(AriaError, match="fold"):
        engine.birth_time_analysis(local)
    a = engine.birth_time_analysis(replace(local, time=replace(local.time, fold=0)))
    b = engine.birth_time_analysis(request("2020-10-25T01:30:00+01:00"))
    assert a["ranges"] == b["ranges"]
    with pytest.raises(AriaError, match="gap"):
        engine.birth_time_analysis(request("2020-03-29T01:30:00", timezone="Europe/London"))


@pytest.mark.kernel
def test_whole_interval_kernel_coverage(engine):
    t = TimeInput(
        value="1900-01-01T00:01:00",
        scale="TT",
        time_accuracy="approximate",
        uncertainty_seconds=900,
    )
    with pytest.raises(AriaError, match="Operating interval"):
        engine.birth_time_analysis(PositionRequest(t, bodies=("sun",)))


def test_input_rejection_without_source():
    from ariaephemeris import Ephemeris

    # Invalid budgets and absent bounds fail before accessing installed sources.
    engine = Ephemeris.__new__(Ephemeris)
    with pytest.raises(AriaError, match="samples"):
        engine.birth_time_analysis(request(), samples=True)
    with pytest.raises(AriaError, match="bound"):
        engine.birth_time_analysis(PositionRequest(TimeInput(value="2000-01-01T12:00:00Z")))
