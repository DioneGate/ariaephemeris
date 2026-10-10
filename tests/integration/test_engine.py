# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
from dataclasses import replace

import pytest

from ariaephemeris import AriaError, EventRequest, Observer, PositionRequest, TimeInput
from ariaephemeris.datasets import install, verify

pytestmark = pytest.mark.kernel


def test_batch_scalar_agreement_and_metadata(engine):
    r = PositionRequest(TimeInput(jd=(2451545, 0), scale="TT"))
    times = [TimeInput(jd=(2451545 + d, 0), scale="TT") for d in [0, 20, 100]]
    batch = engine.positions_batch(r, times)
    for t, p in zip(times, batch):
        scalar = engine.positions(replace(r, time=t))
        assert [b.longitude_deg for b in p.bodies] == pytest.approx(
            [b.longitude_deg for b in scalar.bodies], abs=1e-10
        )
        assert p.metadata["dataset_sha256"] == engine.manifest["sha256"]


def test_local_install_and_corruption(engine, tmp_path):
    import os
    from pathlib import Path

    p = install(tmp_path, os.environ["ARIA_KERNEL"])
    verify(p)
    corrupt = tmp_path / "bad.bsp"
    corrupt.write_bytes(Path(p).read_bytes()[:100])
    with pytest.raises(AriaError, match="checksum"):
        verify(corrupt)


def test_unsupported_and_outside_interval(engine):
    t = TimeInput(jd=(2451545, 0), scale="TT")
    with pytest.raises(AriaError):
        engine.positions(PositionRequest(t, bodies=("chiron",)))
    with pytest.raises(AriaError):
        engine.positions(PositionRequest(t, zodiac="sidereal"))
    with pytest.raises(AriaError):
        engine.positions(PositionRequest(TimeInput(jd=(2400000, 0), scale="TT")))


def test_topocentric_and_heliocentric(engine):
    t = TimeInput(jd=(2451545, 0), scale="TT", delta_t_seconds=64)
    r = PositionRequest(
        t, bodies=("moon",), origin="topocentric", observer=Observer(51.5, 0, 0, 0, 0)
    )
    top = engine.positions(r).bodies[0]
    geo = engine.positions(replace(r, origin="geocentric")).bodies[0]
    assert abs(top.longitude_deg - geo.longitude_deg) > 0.01
    helio = engine.positions(
        PositionRequest(t, bodies=("earth",), origin="heliocentric", position_mode="geometric")
    )
    assert 0.98 < helio.bodies[0].distance_au < 1.02


def test_chart_sect_and_house_contract(engine):
    r = PositionRequest(TimeInput(jd=(2451545, 0), scale="TT", delta_t_seconds=64))
    result = engine.chart(r, Observer(51.5, 0), "whole_sign")
    assert len(result.house_cusps_deg) == 12
    assert result.house_cusps_deg[0] % 30 == 0
    assert result.angles_deg["DSC"] == (result.angles_deg["ASC"] + 180) % 360
    assert all(1 <= x <= 12 for x in result.houses.values())
    assert result.aspects


def test_search_budget_and_cancellation(engine):
    r = EventRequest(
        TimeInput(jd=(2451545, 0), scale="TT"),
        TimeInput(jd=(2451575, 0), scale="TT"),
        "ingress",
        "moon",
    )
    with pytest.raises(AriaError, match="budget"):
        engine.find_events(replace(r, max_evaluations=10))
    with pytest.raises(AriaError, match="cancelled"):
        engine.find_events(r, cancelled=lambda: True)


def test_event_wrapping_recrossings_and_endpoint_inclusion(engine):
    r = EventRequest(
        TimeInput(jd=(2451545, 0), scale="TT"),
        TimeInput(jd=(2451605, 0), scale="TT"),
        "ingress",
        "moon",
    )
    events = engine.find_events(r)
    assert len(events) >= 24
    for e in events:
        assert abs(e.residual) < 0.00001
    epoch = events[0].jd_tt
    again = engine.find_events(replace(r, start=TimeInput(jd=epoch, scale="TT")))
    assert abs(sum(again[0].jd_tt) - sum(epoch)) * 86400 < 0.2


def test_qualification_metadata_is_scoped_to_measured_windows(engine):
    if engine.manifest["qualification"]["status"] != "passed":
        pytest.skip("Release qualification metadata is not installed yet")
    events = engine.find_events(
        EventRequest(
            TimeInput(jd=(2451545, 0), scale="TT"),
            TimeInput(jd=(2451576, 0), scale="TT"),
            "conjunction",
            "moon",
            "sun",
        )
    )
    assert events and all(e.metadata["timing_qualified"] for e in events)
    outside = engine.find_events(
        EventRequest(
            TimeInput(jd=(2451911, 0), scale="TT"),
            TimeInput(jd=(2451942, 0), scale="TT"),
            "conjunction",
            "moon",
            "sun",
        )
    )
    assert outside and all(not e.metadata["timing_qualified"] for e in outside)
