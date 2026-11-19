# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Hermetic Horizons reference acquisition contracts: never query JPL in tests."""

import importlib.util
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "acquire_horizons_fixtures", TOOLS / "acquire_horizons_fixtures.py"
)
assert SPEC is not None and SPEC.loader is not None
h = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(h)


@pytest.mark.parametrize("body", sorted(h.TARGETS))
def test_25_independently_specified_epochs_with_boundary_and_seam(body):
    days = h.epochs(body)
    assert len(days) == len(set(days)) == 25
    assert days == sorted(days)
    assert days[0] == h.START
    assert days[-1] == h.STOP
    assert h.SEAMS_TDB_JD[body] in days
    assert any(abs(d - (h.SEAMS_TDB_JD[body] - 0.04)) < 1e-6 for d in days)
    assert any(abs(d - (h.SEAMS_TDB_JD[body] + 0.04)) < 1e-6 for d in days)


def test_geometric_and_apparent_reference_queries_are_explicitly_distinct():
    times = h.epochs("jupiter")
    g = h.query("jupiter", "geometric", times)
    a = h.query("jupiter", "apparent", times)
    assert g["COMMAND"] == a["COMMAND"] == "'599'"
    assert g["CENTER"] == a["CENTER"] == "'500@399'"
    assert g["REF_SYSTEM"] == a["REF_SYSTEM"] == "'ICRF'"
    assert g["TLIST_TYPE"] == a["TLIST_TYPE"] == "'JD'"
    assert g["TIME_TYPE"] == "TDB"
    assert g["VEC_CORR"] == "NONE"
    assert g["VEC_TABLE"] == "2"
    assert g["OUT_UNITS"] == "KM-S"
    assert a["TIME_TYPE"] == "TT"
    assert a["QUANTITIES"] == "'45'"
    assert a["APPARENT"] == "AIRLESS"
    assert "VEC_CORR" not in a


def test_source_parser_accepts_only_resolved_physical_target_and_complete_rows():
    hdr = "Target body name: Mars (499) {source: mar099}\nCenter body name: Earth (399)\n"
    geo = hdr + "$$SOE\n2451545.0000000, A.D. 2000-Jan-01, 1,2,3,4,5,6,\n$$EOE\n"
    records = h.parse_table(geo, 499, "geometric", [2451545.0])
    assert records == [
        {"jd_tdb": 2451545.0, "position_km": [1.0, 2.0, 3.0], "velocity_km_s": [4.0, 5.0, 6.0]}
    ]
    observer = hdr + "$$SOE\n2451545.0000000, 125.125, -23.5,\n$$EOE\n"
    parsed = h.parse_table(observer, 499, "apparent", [2451545.0])
    assert parsed[0]["inertial_apparent_ra_deg"] == 125.125
    assert parsed[0]["inertial_apparent_dec_deg"] == -23.5
    with pytest.raises(ValueError, match="different physical-centre"):
        h.parse_table(
            geo.replace("Mars (499)", "Mars Barycentre (4)"), 499, "geometric", [2451545.0]
        )
    with pytest.raises(ValueError, match="returned 1 rows"):
        h.parse_table(geo, 499, "geometric", [2451545.0, 2451546.0])
    with pytest.raises(ValueError, match="No unique complete"):
        h.parse_table(geo.replace("$$EOE", ""), 499, "geometric", [2451545.0])


def test_acquisition_sha_provenance_stable():
    assert (
        h.sha256(b"JPL reference fixture")
        == __import__("hashlib").sha256(b"JPL reference fixture").hexdigest()
    )


def test_reject_unsupported_requests_before_api():
    with pytest.raises(ValueError):
        h.query("venus", "geometric", [2451545.0])
    with pytest.raises(ValueError):
        h.query("mars", "corrected", [2451545.0])
    with pytest.raises(ValueError):
        h.query("mars", "apparent", [])
