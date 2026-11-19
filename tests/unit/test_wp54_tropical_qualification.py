# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Offline WP5.4 mathematical, independent-source and candidate-selection tests."""

import math
import sys
from pathlib import Path
from types import SimpleNamespace

import erfa
import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
import acquire_wp54_tropical as acquire  # noqa: E402
import compare_wp54_tropical as compare  # noqa: E402


def test_true_tropical_projection_with_independently_constructed_inertial_vector():
    """Round-trip a known true-of-date ecliptic vector via the IAU matrix."""
    jd = 2460000.5
    ecl_lon, ecl_lat = math.radians(123.456789), math.radians(-7.25)
    ecl = [
        math.cos(ecl_lat) * math.cos(ecl_lon),
        math.cos(ecl_lat) * math.sin(ecl_lon),
        math.sin(ecl_lat),
    ]
    tt1, tt2 = 2451545.0, jd - 2451545.0
    eps = erfa.obl06(tt1, tt2) + erfa.nut06a(tt1, tt2)[1]
    true_eq = [
        ecl[0],
        math.cos(eps) * ecl[1] - math.sin(eps) * ecl[2],
        math.sin(eps) * ecl[1] + math.cos(eps) * ecl[2],
    ]
    inertial = erfa.pnm06a(tt1, tt2).T @ true_eq
    ra = math.degrees(math.atan2(inertial[1], inertial[0])) % 360.0
    dec = math.degrees(math.atan2(inertial[2], math.hypot(inertial[0], inertial[1])))
    actual = compare.true_tropical_from_icrf(ra, dec, jd)
    assert compare.signed_angle(actual[0], math.degrees(ecl_lon)) == pytest.approx(0.0, abs=1e-11)
    assert actual[1] == pytest.approx(math.degrees(ecl_lat), abs=1e-11)


def test_rate_stencil_wrap_and_signed_retrograde():
    jd = 2451545.0
    step = compare.RATE_STEP_DAYS
    # Analytic circular motion of -0.25 degrees/day around 0 Aries.
    five = [((0.0001 - 0.25 * step * k) % 360, 0.0) for k in (-2, -1, 0, 1, 2)]
    assert compare.reference_rate(five) == pytest.approx(-0.25, abs=1e-11)
    assert compare.signed_angle(359.9999, 0.0001) == pytest.approx(-0.0002)
    assert compare.nearest_sign_boundary_arcsec(359.9999) == pytest.approx(0.36, abs=1e-7)
    assert jd != 0
    with pytest.raises(ValueError, match="Five"):
        compare.reference_rate(five[:3])
    with pytest.raises(ValueError, match="nonfinite|Nonfinite"):
        compare.true_tropical_from_icrf(0, 0, math.nan)


def test_reference_stencil_accounts_for_moving_ecliptic_frame():
    jd = 2460000.5
    # Constant ICRF ray: changing TT rotates the true-of-date ecliptic.
    five = [
        compare.true_tropical_from_icrf(145.0, 12.0, jd + k * compare.RATE_STEP_DAYS)
        for k in (-2, -1, 0, 1, 2)
    ]
    observed = compare.reference_rate(five)
    assert math.isfinite(observed)
    assert 1e-6 < abs(observed) < 1e-3


class NominatedSource:
    def __init__(self, station: float, ingress: float):
        self.station = station
        self.ingress = ingress

    def formula(self, jd):
        # An artificial longitude crossing 30 degrees, with an unrelated
        # signed rate zero; used to validate candidate NOMINATION only.
        return SimpleNamespace(
            longitude_deg=(30.0 + 0.15 * (jd - self.ingress)) % 360,
            longitude_rate_deg_day=jd - self.station,
            target_id=599,
        )

    def positions(self, request):
        return SimpleNamespace(bodies=(self.formula(sum(request.time.jd)),))

    def positions_batch(self, request, times):
        return tuple(SimpleNamespace(bodies=(self.formula(sum(x.jd)),)) for x in times)


def test_critical_station_and_ingress_selection_without_external_reference_values():
    origin = acquire.SCAN_START
    engine = NominatedSource(origin + 12.7, origin + 45.25)
    saved = acquire.TARGETS["jupiter"]
    assert saved == 599
    station, ingress = acquire.select_critical(engine, "jupiter")
    assert station["jd_tt"] == pytest.approx(engine.station, abs=0.0002)
    assert ingress["jd_tt"] == pytest.approx(engine.ingress, abs=0.0002)
    stress, nominated = acquire.stress_centres(engine, "jupiter")
    assert len(stress) == 6 and len(nominated) == 2
    assert {x["label"] for x in stress} == {
        "station-before",
        "station-root",
        "station-after",
        "ingress-before",
        "ingress-root",
        "ingress-after",
    }
    assert all(
        x["nomination"]["candidate_source"].endswith("not independent reference)") for x in stress
    )


def test_motion_and_sign_limits_are_never_claimed_as_physical_truth():
    assert compare.CANDIDATE_ANGLE_ARCSEC == 0.05
    assert compare.CANDIDATE_RATE_DEG_DAY == 1e-4
    assert compare.AMBIGUOUS_MOTION_BAND > 0
    assert compare.BOUNDARY_MARGIN_ARCSEC > 0
    assert compare._stats([0, 1, 2, 3])["p95"] == pytest.approx(2.85)
    with pytest.raises(ValueError, match="Nonfinite or missing"):
        compare._stats([-1])
