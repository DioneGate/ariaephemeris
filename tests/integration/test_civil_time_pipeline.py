# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Civil input -> real source positions and houses, with no inferred time certainty."""

import json
from dataclasses import replace

import pytest

from ariaephemeris import AriaError, Observer, PositionRequest, TimeInput
from ariaephemeris.cli import main

pytestmark = pytest.mark.kernel


def test_historical_chart_matches_explicit_ut1_and_batch(engine):
    local = TimeInput(
        "1901-01-01T12:00:00",
        timezone="Europe/Paris",
        civil_policy="historical-ut1-v1",
        delta_t_seconds=0,
    )
    ut1 = TimeInput("1901-01-01T11:50:39", scale="UT1", delta_t_seconds=0)
    observer = Observer(48.8, 2.3)
    r = PositionRequest(local, bodies=("sun", "moon"))
    a = engine.chart(r, observer)
    b = engine.chart(replace(r, time=ut1), observer)
    assert a.angles_deg == b.angles_deg
    assert a.house_cusps_deg == b.house_cusps_deg
    assert a.positions.bodies == b.positions.bodies
    assert a.metadata["time"]["quality"]["effective_input_scale"] == "UT1"
    batch = engine.positions_batch(r, [local, ut1])
    assert batch[0].bodies == batch[1].bodies
    assert batch[0].metadata["time"]["quality"]["timezone"]["iana_version"] == "2026f"


def test_unknown_time_positions_allowed_but_chart_and_topocentre_rejected(engine):
    r = PositionRequest(
        TimeInput("2020-01-01T12:00:00Z", time_accuracy="unknown", delta_t_seconds=70),
        bodies=("moon",),
    )
    p = engine.positions(r)
    assert p.metadata["time"]["quality"]["input_uncertainty_seconds"] is None
    assert p.metadata["warnings"]
    with pytest.raises(AriaError, match="specified time"):
        engine.chart(r, Observer(51.5, 0))
    with pytest.raises(AriaError, match="specified time"):
        engine.positions(replace(r, origin="topocentric", observer=Observer(51.5, 0, 0, 0, 0)))


def test_historical_chart_cli_and_structured_unknown_time_error(engine, tmp_path, capsys):
    request = {
        "time": {
            "value": "1901-01-01T12:00:00+00:00",
            "civil_policy": "historical-ut1-v1",
            "delta_t_seconds": 0,
        },
        "bodies": ["sun"],
        "observer": {"latitude_deg": 51.5, "longitude_deg": 0},
    }
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request))
    argv = ["chart", "--kernel", engine.kernel._spk.daf.file.name, "--request", str(path)]
    assert main(argv) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result["house_cusps_deg"]) == 12
    assert result["metadata"]["time"]["quality"]["utc_status"] == "not-applicable"
    request["time"]["time_accuracy"] = "unknown"
    path.write_text(json.dumps(request))
    assert main(argv) == 2
    assert json.loads(capsys.readouterr().err)["error"]["code"] == "TIME_DATA_UNAVAILABLE"
