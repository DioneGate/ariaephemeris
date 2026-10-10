# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
from pathlib import Path

import numpy as np
import pytest

from ariaephemeris import AriaError, Observer, TimeInput
from ariaephemeris.astrology import angles, cusps, membership, sign
from ariaephemeris.frames import rotation
from ariaephemeris.numerics import bisect_root, circular_difference
from ariaephemeris.sources import Kernel
from ariaephemeris.time import resolve


def test_circular_wrap():
    assert circular_difference(1, 359) == 2
    assert circular_difference(359, 1) == -2


def test_solver_checks_bracket_and_converges():
    root, _, width = bisect_root(lambda x: x * x - 2, 1, 2, 1e-12)
    assert root == pytest.approx(np.sqrt(2), abs=1e-12)
    assert width <= 1e-12
    with pytest.raises(AriaError):
        bisect_root(lambda x: x * x + 1, -1, 1, 1e-6)


def test_rotation_is_orthonormal():
    for frame in ["icrs", "ecliptic_j2000", "mean_ecliptic_of_date", "true_ecliptic_of_date"]:
        r = rotation(frame, 2451545, 0.2)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-14)
        assert np.linalg.det(r) == pytest.approx(1, abs=1e-14)


def test_equal_and_whole_sign_boundaries():
    assert cusps(359, "whole_sign")[0] == 330
    cc = cusps(350, "equal")
    assert membership(350, cc) == 1
    assert membership(20, cc) == 2
    assert membership(349.999, cc) == 12
    assert sign(360)["name"] == "Aries"
    assert sign(359)["name"] == "Pisces"


def test_polar_ascendant_is_not_fabricated():
    t = resolve(TimeInput(jd=(2451545, 0), scale="TT", delta_t_seconds=64), require_ut1=True)
    with pytest.raises(AriaError, match="pole"):
        angles(Observer(90, 0), t)


def test_spk_precedence_fallback_and_centre_chain():
    k = Kernel(Path(__file__).parents[1] / "data" / "linear.bsp")
    try:
        p, v = k.state(42, np.array([2451545.5, 2451546.5]))
        # Earlier segment applies before the later segment's start.
        np.testing.assert_allclose(p[0], [1019, 1050.5])
        np.testing.assert_allclose(v[0], [2, 3])
        with pytest.raises(AriaError):
            k.state(42, 2451548)
    finally:
        k.close()


def test_type3_uses_stored_velocity_coefficients():
    k = Kernel(Path(__file__).parents[1] / "data" / "linear.bsp")
    try:
        p, v = k.state(43, 2451545.5)
        assert p[0] == pytest.approx(99)
        assert v[0] == pytest.approx(7 * 86400)
    finally:
        k.close()


def test_independent_limited_deflection_equation_matches_standard():
    import sys

    import erfa

    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
    from reference.skyfield_match import limited_deflection

    for theta in [1e-6, 0.01, 1, 3.13]:
        p = np.array([np.cos(theta), np.sin(theta), 0.0]) * 10
        e = np.array([-1.0, 0, 0])
        q = p + e
        # Independent adapter must reproduce the finite-source equation even
        # inside the alignment-limited domain that unmodified Skyfield treats differently.
        expected = erfa.ld(1, p / 10, q / np.linalg.norm(q), e, 1, 1e-6) * 10
        actual = p + limited_deflection(p, e, 1)
        np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-13)
