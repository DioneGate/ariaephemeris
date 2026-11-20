# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Civil semantics against published timezone examples, algebra and explicit policy."""

import hashlib
import json
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import jsonschema
import pytest

from ariaephemeris import AriaError, Observer, TimeInput
from ariaephemeris.astrology import angles
from ariaephemeris.time import LEAP_EXPIRY_JD, resolve, zones


def seconds(a, b):
    return ((b.tt1 - a.tt1) + (b.tt2 - a.tt2)) * 86400


def test_historical_policy_requires_opt_in_and_supplied_delta_t_in_strict_mode():
    original = TimeInput("1900-01-01T12:00:00+00:00", delta_t_seconds=-2.79)
    with pytest.raises(AriaError, match="Pre-1972"):
        resolve(original, require_ut1=True)
    historic = replace(original, civil_policy="historical-ut1-v1")
    t = resolve(historic, require_ut1=True)
    assert t.utc1 is None and t.utc2 is None
    assert t.ut11 + t.ut12 == 2415021.0
    assert (t.tt1 - t.ut11 + t.tt2 - t.ut12) * 86400 == pytest.approx(-2.79, abs=1e-9)
    assert t.quality["effective_input_scale"] == "UT1"
    assert t.quality["utc_status"] == "not-applicable"
    assert t.quality["delta_t_status"] == "user-supplied"
    assert t.quality["earth_rotation_uncertainty_seconds"] is None
    with pytest.raises(AriaError, match="delta_t_seconds"):
        resolve(replace(historic, delta_t_seconds=None))
    modelled = resolve(replace(historic, delta_t_seconds=None), strict=False)
    assert modelled.quality["delta_t_status"] == "Espenak-Meeus-2006-polynomial"
    assert modelled.quality["warnings"]


def test_historical_iana_second_offset_is_preserved_and_labelled():
    # tzdb Paris local mean time is +00:09:21 here; not a claim about every birth record.
    local = TimeInput(
        "1901-01-01T12:00:00",
        timezone="Europe/Paris",
        civil_policy="historical-ut1-v1",
        delta_t_seconds=0,
    )
    reference = TimeInput("1901-01-01T11:50:39", scale="UT1", delta_t_seconds=0)
    t = resolve(local)
    assert seconds(t, resolve(reference)) == pytest.approx(0, abs=1e-9)
    assert t.quality["civil_offset_seconds"] == 561
    assert t.quality["timezone"]["iana_version"] == "2026f"
    assert "not recorded UTC" in " ".join(t.quality["warnings"])


@pytest.mark.parametrize(
    "value", ["1899-12-31T12:00:00Z", "1972-01-01T00:00:00Z", "1969-12-31T23:59:60Z"]
)
def test_historical_policy_is_bounded(value):
    with pytest.raises(AriaError):
        resolve(TimeInput(value, civil_policy="historical-ut1-v1", delta_t_seconds=40))


def test_pinned_timezone_ignores_host_tzpath_and_cache(monkeypatch):
    import zoneinfo

    zones.load_zone.cache_clear()
    old = zoneinfo.TZPATH
    try:
        zoneinfo.reset_tzpath(())
        # Poisoning the usual constructor does not affect from_file on pinned resources.
        monkeypatch.setattr(zoneinfo, "ZoneInfo", lambda key: pytest.fail("Host timezone used"))
        local = resolve(TimeInput("2020-11-01T01:30:00", timezone="America/Los_Angeles", fold=0))
        utc = resolve(TimeInput("2020-11-01T08:30:00Z"))
        assert seconds(local, utc) == pytest.approx(0, abs=1e-9)
        second = resolve(TimeInput("2020-11-01T01:30:00", timezone="America/Los_Angeles", fold=1))
        assert seconds(local, second) == pytest.approx(3600, abs=1e-8)
    finally:
        zoneinfo.reset_tzpath(old)
        zones.load_zone.cache_clear()


def test_timezone_identity_and_fail_closed_on_data_changes(monkeypatch):
    zones.load_zone.cache_clear()
    zone = zones._MANIFEST["zones"]["Europe/London"]
    monkeypatch.setitem(zones._MANIFEST["zones"], "Europe/London", "0" * 64)
    with pytest.raises(AriaError, match="checksum"):
        resolve(TimeInput("2020-01-01T00:00:00", timezone="Europe/London"))
    monkeypatch.setitem(zones._MANIFEST["zones"], "Europe/London", zone)
    monkeypatch.setattr(zones.tzdata, "__version__", "other")
    with pytest.raises(AriaError, match="pinned version"):
        resolve(TimeInput("2020-01-01T00:00:00", timezone="Europe/London"))
    zones.load_zone.cache_clear()


@pytest.mark.parametrize("zone", ["../UTC", "/etc/passwd", "tzdata.zi", "Europe/Unknown"])
def test_zone_keys_cannot_read_unpinned_resources(zone):
    with pytest.raises(AriaError, match="Unknown IANA"):
        resolve(TimeInput("2020-01-01T00:00:00", timezone=zone))


def test_every_packaged_zone_matches_frozen_manifest():
    manifest = json.loads(files("ariaephemeris.resources").joinpath("tzdata-v1.json").read_text())
    assert len(manifest["zones"]) == 598
    for key, expected in manifest["zones"].items():
        data = files("tzdata.zoneinfo").joinpath(*key.split("/")).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, key


@pytest.mark.parametrize(
    "value,zone",
    [
        ("2026-03-29T01:30:00", "Europe/London"),
        ("2020-10-04T02:15:00", "Australia/Lord_Howe"),
        ("2011-12-30T12:00:00", "Pacific/Apia"),
    ],
)
def test_hour_half_hour_and_whole_day_gaps(value, zone):
    with pytest.raises(AriaError, match="DST gap"):
        resolve(TimeInput(value, timezone=zone))


def test_half_hour_fold_and_fractional_leap_second():
    a = resolve(TimeInput("2020-04-05T01:45:00", timezone="Australia/Lord_Howe", fold=0))
    b = resolve(TimeInput("2020-04-05T01:45:00", timezone="Australia/Lord_Howe", fold=1))
    assert seconds(a, b) == pytest.approx(1800, abs=1e-8)
    a = resolve(TimeInput("2016-12-31T23:59:60.5Z"))
    b = resolve(TimeInput("2017-01-01T00:00:00Z"))
    assert seconds(a, b) == pytest.approx(0.5, abs=1e-9)


def test_leap_validity_boundary_and_rotation_sources():
    with pytest.raises(AriaError, match="validity"):
        resolve(TimeInput(jd=(LEAP_EXPIRY_JD, 0)))
    future = resolve(TimeInput(jd=(LEAP_EXPIRY_JD, 0)), strict=False)
    assert future.quality["utc_status"] == "assumed"
    modern = resolve(TimeInput("2020-01-01T00:00:00Z", dut1_seconds=0.2), require_ut1=True)
    assert modern.quality["dut1_seconds"] == 0.2
    assert modern.quality["ut1_status"] == "user-supplied-DUT1"
    assert modern.quality["earth_rotation_uncertainty_seconds"] is None


@pytest.mark.parametrize(
    "accuracy,bound", [("unknown", None), ("approximate", None), ("approximate", 60)]
)
def test_uncertain_times_have_metadata_and_cannot_produce_precise_angles(accuracy, bound):
    ti = TimeInput(
        "2020-01-01T12:00:00Z",
        delta_t_seconds=70,
        time_accuracy=accuracy,
        uncertainty_seconds=bound,
    )
    t = resolve(ti)
    assert t.quality["input_uncertainty_seconds"] == bound
    assert t.quality["warnings"]
    with pytest.raises(AriaError, match="specified time"):
        resolve(ti, require_ut1=True)
    with pytest.raises(AriaError, match="specified time"):
        angles(Observer(51.5, 0), t)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"fold": 2},
        {"fold": True},
        {"dut1_seconds": True},
        {"jd": "ab"},
        {"scale": None},
        {"value": 3},
        {"uncertainty_seconds": 0},
        {"time_accuracy": "approximate", "uncertainty_seconds": -1},
        {"time_accuracy": "unknown", "uncertainty_seconds": 60},
        {"time_accuracy": "approximate", "uncertainty_seconds": float("inf")},
        {"value": "2020-01-01T00:00:00Z", "timezone": "Europe/London"},
        {"value": "2020-01-01T00:00:00Z", "fold": 0},
        {"jd": (2451545, 0), "timezone": "Europe/London"},
        {"scale": "TT", "dut1_seconds": 1},
        {"value": "2020-01-01"},
        {"value": "2020-01-01T00:00:00Z", "civil_policy": "other"},
    ],
)
def test_invalid_and_ignored_fields_are_rejected(kwargs):
    with pytest.raises(AriaError):
        ti = TimeInput.parse({"value": "2020-01-01T00:00:00Z", **kwargs})
        resolve(ti)


def test_schema_copies_accept_new_fields():
    root = Path(__file__).resolve().parents[2]
    time = {
        "value": "1901-01-01T12:00:00+00:00",
        "civil_policy": "historical-ut1-v1",
        "delta_t_seconds": 1,
        "time_accuracy": "approximate",
        "uncertainty_seconds": 60,
    }
    jsonschema.validate(time, json.loads((root / "schemas/time-input-v1.json").read_text()))
    jsonschema.validate(
        {"time": time}, json.loads((root / "schemas/position-request-v1.json").read_text())
    )


def test_sofa_published_utc_tt_example():
    # SOFA Time Scale and Calendar Tools, UTC->TT example (2010-07-24).
    utc = resolve(TimeInput("2010-07-24T11:18:07.318Z"))
    tt = resolve(TimeInput("2010-07-24T11:19:13.502", scale="TT"))
    assert seconds(utc, tt) == pytest.approx(0, abs=1e-9)


def test_event_boundaries_do_not_treat_unknown_birth_times_as_exact():
    from ariaephemeris import EventRequest
    from ariaephemeris.events import find_events

    with pytest.raises(AriaError, match="specified times"):
        find_events(
            None,
            EventRequest(
                TimeInput("2020-01-01T12:00:00Z", time_accuracy="unknown"),
                TimeInput("2020-01-02T12:00:00Z"),
                "ingress",
                "moon",
            ),
        )
