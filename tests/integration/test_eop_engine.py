# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import json
from dataclasses import replace

import pytest

from ariaephemeris import AriaError, Ephemeris, Observer, PositionRequest, TimeInput
from ariaephemeris.cli import main

pytestmark = pytest.mark.kernel


@pytest.fixture
def oriented(engine, eop_excerpt):
    with Ephemeris(engine.kernel._spk.daf.file.name, eop_path=eop_excerpt) as e:
        yield e


def test_chart_matches_manual_source_values_and_preserves_user_override(engine, oriented):
    r = PositionRequest(TimeInput("2000-01-01T12:00:00Z"), bodies=("sun", "moon"))
    observer = Observer(51.5, 0)
    auto = oriented.chart(r, observer)
    manual = engine.chart(
        replace(r, time=replace(r.time, dut1_seconds=(0.3554779 + 0.3546013) / 2)), observer
    )
    assert auto.angles_deg == pytest.approx(manual.angles_deg, abs=1e-10)
    assert auto.positions.bodies == manual.positions.bodies
    q = auto.metadata["time"]["quality"]
    assert q["ut1_status"] == "managed-EOP-observed"
    assert q["earth_orientation"]["applied"] == {"dut1": True, "xp": False, "yp": False}
    # An explicit caller value works outside the installed EOP coverage; no unrelated lookup.
    explicit = PositionRequest(TimeInput("2001-01-01T12:00:00Z", dut1_seconds=0.1), bodies=("sun",))
    assert (
        oriented.chart(explicit, observer).metadata["time"]["quality"]["ut1_status"]
        == "user-supplied-DUT1"
    )


def test_topocentric_scalar_batch_and_time_dependent_rates(oriented, engine):
    r = PositionRequest(
        TimeInput("2000-01-01T12:00:00Z"),
        bodies=("moon",),
        origin="topocentric",
        observer=Observer(51.5, 0),
    )
    a = oriented.positions(r)
    times = [r.time, replace(r.time, value="2000-01-01T18:00:00Z")]
    batch = oriented.positions_batch(r, times)
    assert a == batch[0]
    assert batch[1] == oriented.positions(replace(r, time=times[1]))
    manual = replace(
        r,
        time=replace(r.time, dut1_seconds=(0.3554779 + 0.3546013) / 2),
        observer=Observer(51.5, 0, 0, (0.043301 + 0.043541) / 2, (0.377867 + 0.377638) / 2),
    )
    b = engine.positions(manual)
    assert a.bodies[0].longitude_deg == pytest.approx(b.bodies[0].longitude_deg, abs=1e-9)
    # Independently evaluate complete scalar requests at ±2/±1 minute stencils.
    from datetime import datetime, timedelta, timezone

    base = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
    longs = []
    for seconds in [-120, -60, 60, 120]:
        t = replace(r.time, value=(base + timedelta(seconds=seconds)).isoformat())
        lon = oriented.positions(replace(r, time=t)).bodies[0].longitude_deg
        longs.append((lon - a.bodies[0].longitude_deg + 180) % 360 - 180)
    independent = (longs[0] - 8 * longs[1] + 8 * longs[2] - longs[3]) / (12 * (60 / 86400))
    assert a.bodies[0].longitude_rate_deg_day == pytest.approx(independent, abs=2e-7)
    # Caller-supplied one polar coordinate wins; only the missing component is managed.
    q = oriented.positions(replace(r, observer=Observer(51.5, 0, xp_arcsec=0))).metadata["time"][
        "quality"
    ]
    assert q["earth_orientation"]["applied"] == {"dut1": True, "xp": False, "yp": True}


def test_missing_and_unknown_do_not_fall_back(oriented):
    r = PositionRequest(TimeInput("2001-01-01T12:00:00Z"), bodies=("moon",))
    with pytest.raises(AriaError, match="missing day"):
        oriented.chart(r, Observer(51.5, 0))
    # Geocentric positions do not require or implicitly look up Earth orientation.
    assert oriented.positions(r)
    with pytest.raises(AriaError, match="specified time"):
        oriented.chart(replace(r, time=replace(r.time, time_accuracy="unknown")), Observer(51.5, 0))


def test_cli_explicit_source_and_structured_errors(oriented, eop_excerpt, tmp_path, capsys):
    request = {
        "time": {"value": "2000-01-01T12:00:00Z"},
        "bodies": ["moon"],
        "origin": "topocentric",
        "observer": {"latitude_deg": 51.5, "longitude_deg": 0},
    }
    f = tmp_path / "chart.json"
    f.write_text(json.dumps(request))
    args = [
        "chart",
        "--kernel",
        oriented.kernel._spk.daf.file.name,
        "--eop",
        str(eop_excerpt),
        "--request",
        str(f),
    ]
    assert main(args) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["metadata"]["time"]["quality"]["earth_orientation"]["applied"]["xp"]
    assert main(["install-eop", str(tmp_path / "data"), "--source", str(eop_excerpt)]) == 0
    assert "earth_orientation" in json.loads(capsys.readouterr().out)


def test_observed_boundary_chart_does_not_require_unneeded_eop_rate_stencils(oriented):
    r = PositionRequest(TimeInput("2026-11-19T00:00:00Z"), bodies=("sun",))
    assert (
        oriented.chart(r, Observer(51.5, 0)).metadata["time"]["quality"]["ut1_status"]
        == "managed-EOP-observed"
    )
    with pytest.raises(AriaError, match="opt-in"):
        oriented.positions(replace(r, origin="topocentric", observer=Observer(51.5, 0)))
