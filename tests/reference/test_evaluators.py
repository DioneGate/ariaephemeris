# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Small independent reference checks; release gates use qualify.py's wider sample."""

import numpy as np
import pytest

from ariaephemeris import PositionRequest, TimeInput
from ariaephemeris.models import BODY_IDS

pytestmark = [pytest.mark.kernel, pytest.mark.reference]


def test_cspice_same_tdb_states(engine):
    spice = pytest.importorskip("spiceypy")
    spice.furnsh(str(engine.kernel._spk.daf.file.name))
    try:
        for body, target in BODY_IDS.items():
            time = TimeInput(jd=(2451545, 0.123456789), scale="TDB")
            state = engine.raw_state(body, time)
            jd = state["time"]["jd_tdb"]
            et = ((jd[0] - 2451545) + jd[1]) * 86400
            reference = spice.spkgeo(target, et, "J2000", 0)[0]
            np.testing.assert_allclose(state["position_km"], reference[:3], rtol=0, atol=0.001)
            np.testing.assert_allclose(
                np.asarray(state["velocity_km_day"]) / 86400, reference[3:], rtol=0, atol=1e-6
            )
    finally:
        spice.kclear()


def test_skyfield_topocentric_direction(engine):
    from skyfield.api import load, load_file, wgs84

    sk = load_file(engine.kernel._spk.daf.file.name)
    ts = load.timescale(builtin=True)
    tt = ts.tt_jd(2451545)
    tt.ut1_fraction = tt.tt_fraction - 64 / 86400
    site = sk["earth"] + wgs84.latlon(51.5, -0.1, elevation_m=20)
    request = PositionRequest.parse(
        {
            "time": {"jd": [2451545, 0], "scale": "TT", "delta_t_seconds": 64},
            "origin": "topocentric",
            "observer": {
                "latitude_deg": 51.5,
                "longitude_deg": -0.1,
                "elevation_m": 20,
                "xp_arcsec": 0,
                "yp_arcsec": 0,
            },
        }
    )
    for actual in engine.positions(request).bodies:
        expected = site.at(tt).observe(sk[actual.target_id]).apparent().xyz.au
        a = np.array(actual.vector_icrs_au)
        a /= np.linalg.norm(a)
        b = expected / np.linalg.norm(expected)
        error = np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b)) * 3600
        assert error < 1
    sk.close()


def test_recorded_reference_fixtures(engine):
    import json
    from pathlib import Path

    fixture = json.loads((Path(__file__).parents[1] / "data/reference-de442.json").read_text())
    assert fixture["kernel_sha256"] == engine.manifest["sha256"]
    for case in fixture["cases"]:
        p, v = engine.kernel.state(case["target_id"], *case["jd_tdb"])
        np.testing.assert_allclose(p, case["raw_state"][:3], rtol=0, atol=0.001)
        np.testing.assert_allclose(v / 86400, case["raw_state"][3:], rtol=0, atol=1e-6)
        if "apparent_vector_au" in case:
            result = engine.positions(
                PositionRequest(TimeInput(jd=case["jd_tt"], scale="TT"), bodies=(case["body"],))
            ).bodies[0]
            a = np.array(result.vector_icrs_au)
            b = np.array(case["apparent_vector_au"])
            a /= np.linalg.norm(a)
            b /= np.linalg.norm(b)
            assert np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b)), a @ b)) * 3600 < 1
