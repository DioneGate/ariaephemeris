# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Original IERS columns, leap-safe interpolation and fail-closed source policies."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from ariaephemeris import AriaError, TimeInput
from ariaephemeris.time import eop, resolve


def test_original_a_columns_and_manifest_identity(eop_excerpt):
    s = eop.EarthOrientation(eop_excerpt)
    x = s.lookup(resolve(TimeInput("2000-01-01T00:00:00Z")))
    assert x["xp_arcsec"] == 0.043301  # A column, not the distinct final B .043190.
    assert x["yp_arcsec"] == 0.377867
    assert x["dut1_seconds"] == pytest.approx(0.3554779, abs=4e-15)
    assert x["mjd_utc_nodes"] == [51544]
    assert x["ut1_status"] == "observed"
    assert x["formal_errors_at_nodes"][0]["dut1_seconds"] == 0.0000099
    assert x["physical_uncertainty_seconds"] is None
    assert not x["celestial_pole_offsets_applied"]
    info = s.info()
    info["sha256"] = "changed"
    assert s.info()["sha256"] != "changed"


def test_ordinary_noon_interpolation(eop_excerpt):
    s = eop.EarthOrientation(eop_excerpt)
    x = s.lookup(resolve(TimeInput("2000-01-01T12:00:00Z")))
    assert x["fraction_tai"] == 0.5
    assert x["dut1_seconds"] == pytest.approx((0.3554779 + 0.3546013) / 2, abs=4e-15)
    assert x["xp_arcsec"] == pytest.approx((0.043301 + 0.043541) / 2, abs=1e-15)


def test_leap_interpolation_uses_continuous_ut1_minus_tai(eop_excerpt):
    s = eop.EarthOrientation(eop_excerpt)
    # 86401 elapsed SI seconds in this UTC day; UT1−UTC jumps +1 s at midnight.
    u0, u1 = -0.4077601, 0.5912821
    for stamp, elapsed, dat in [
        ("2016-12-31T12:00:00Z", 43200, 36),
        ("2016-12-31T23:59:60Z", 86400, 36),
        ("2016-12-31T23:59:60.5Z", 86400.5, 36),
        ("2017-01-01T00:00:00Z", 86401, 37),
    ]:
        expected = (u0 - 36) + elapsed / 86401 * ((u1 - 37) - (u0 - 36)) + dat
        actual = s.lookup(resolve(TimeInput(stamp)))
        assert actual["dut1_seconds"] == pytest.approx(expected, abs=2e-12)
    before = s.apply(resolve(TimeInput("2016-12-31T23:59:60Z")), dut1=True, xp=True, yp=True)
    after = before.shift(1 / 86400)
    delta = (after.ut11 - before.ut11 + after.ut12 - before.ut12) * 86400
    assert delta == pytest.approx(1, abs=2e-7)
    assert after.quality["dut1_seconds"] > 0.5


def test_predictions_require_opt_in_and_last_observed_node_is_usable(eop_excerpt, monkeypatch):
    s = eop.EarthOrientation(eop_excerpt)
    assert s.lookup(resolve(TimeInput("2026-11-19T00:00:00Z")))["ut1_status"] == "observed"
    with pytest.raises(AriaError, match="opt-in"):
        s.lookup(resolve(TimeInput("2026-11-19T12:00:00Z")))
    m = eop.manifest()
    m["prediction_valid_until_mjd_utc"] = 61365
    monkeypatch.setattr(eop, "manifest", lambda: m)
    s = eop.EarthOrientation(eop_excerpt, allow_predictions=True)
    x = s.lookup(resolve(TimeInput("2026-11-20T12:00:00Z")))
    assert x["ut1_status"] == "predicted"
    with pytest.raises(AriaError, match="expired"):
        s.lookup(resolve(TimeInput("2026-11-21T00:00:00Z")))


@pytest.mark.parametrize("stamp", ["1973-01-01T00:00:00Z", "2001-01-01T12:00:00Z"])
def test_outside_coverage_or_missing_days_never_clamp(eop_excerpt, stamp):
    with pytest.raises(AriaError, match="coverage|missing day"):
        eop.EarthOrientation(eop_excerpt).lookup(resolve(TimeInput(stamp)))


def test_non_utc_and_uncertain_inputs_cannot_bypass_engine_guards(eop_excerpt):
    s = eop.EarthOrientation(eop_excerpt)
    with pytest.raises(AriaError, match="UTC"):
        s.lookup(resolve(TimeInput("2000-01-01T12:00:00", scale="TT")))


def test_integrity_missing_corrupt_and_atomic_install(eop_excerpt, tmp_path, monkeypatch):
    with pytest.raises(AriaError, match="explicitly"):
        eop.EarthOrientation(tmp_path / "missing")
    bad = tmp_path / "bad"
    bad.write_bytes(eop_excerpt.read_bytes() + b"x")
    with pytest.raises(AriaError, match="checksum|pinned size"):
        eop.EarthOrientation(bad)
    with pytest.raises(AriaError, match="checksum|pinned size"):
        eop.install(tmp_path / "install", bad)
    assert not list((tmp_path / "install").iterdir())
    installed = eop.install(tmp_path / "install", eop_excerpt)
    monkeypatch.setattr(
        eop.urllib.request, "urlopen", lambda *a, **k: pytest.fail("runtime network")
    )
    assert eop.install(tmp_path / "install") == installed
    assert eop.EarthOrientation(installed).lookup(resolve(TimeInput("2000-01-01T12:00:00Z")))
    installed.write_bytes(b"corrupt")
    with pytest.raises(AriaError, match="checksum|pinned size"):
        eop.install(tmp_path / "install", eop_excerpt)


@pytest.mark.parametrize(
    "change", ["duplicate", "reverse", "truncated", "nan", "bad-date", "flag", "blank-value"]
)
def test_malformed_source_is_not_silently_accepted(eop_excerpt, change):
    lines = eop_excerpt.read_text().splitlines()[:2]
    if change == "duplicate":
        lines[1] = lines[0]
    elif change == "reverse":
        lines.reverse()
    elif change == "truncated":
        lines[0] = lines[0][:70]
    elif change == "nan":
        lines[0] = lines[0][:18] + "      nan" + lines[0][27:]
    elif change == "bad-date":
        lines[0] = "74" + lines[0][2:]
    elif change == "flag":
        lines[0] = lines[0][:16] + "X" + lines[0][17:]
    else:
        lines[0] = lines[0][:58] + " " * 10 + lines[0][68:]
    with pytest.raises(AriaError, match="Invalid"):
        eop.parse(("\n".join(lines) + "\n").encode())


def test_packaged_and_source_manifest_agree():
    root = Path(__file__).resolve().parents[2]
    assert eop.manifest() == json.loads((root / "data/manifests/eop-v1.json").read_text())


@pytest.mark.parametrize(
    "polar,ut1,need_polar,need_ut1", [("P", "I", False, True), ("I", "P", True, False)]
)
def test_unused_predicted_fields_do_not_override_needed_observed_values(
    eop_excerpt, polar, ut1, need_polar, need_ut1
):
    s = eop.EarthOrientation(eop_excerpt)
    s._rows = tuple(
        replace(r, polar_flag=polar, ut1_flag=ut1) if r.mjd == 51544 else r for r in s._rows
    )
    t = resolve(TimeInput("2000-01-01T00:00:00Z"))
    assert s.lookup(t, require_ut1=need_ut1, require_polar=need_polar)
    with pytest.raises(AriaError, match="opt-in"):
        s.lookup(t)


def test_two_part_utc_does_not_round_outside_epoch_onto_first_source_node(eop_excerpt):
    s = eop.EarthOrientation(eop_excerpt)
    with pytest.raises(AriaError, match="coverage"):
        s.lookup(resolve(TimeInput(jd=(2441684.5, -1e-12))))
    # An instant just after a node is genuinely interpolated, not rounded onto that node.
    x = s.lookup(resolve(TimeInput(jd=(2451544.5, 1e-12))))
    assert x["mjd_utc_nodes"] == [51544, 51545]
    assert 0 < x["fraction_tai"] < 1e-10
