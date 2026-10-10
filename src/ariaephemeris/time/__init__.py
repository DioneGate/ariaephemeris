# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Explicit time scales, civil ambiguity handling and model-quality records."""

import hashlib
import re
import warnings
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from importlib.resources import files
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import erfa
import numpy as np

from ..errors import AriaError
from ..models import TimeInput

DAY = 86400.0
_LEAP_TEXT = files("ariaephemeris.resources").joinpath("Leap_Second.dat").read_text()
LEAP_HASH = hashlib.sha256(_LEAP_TEXT.encode()).hexdigest()
# Validate the actual conversion table, not just a provenance filename.
_rows = np.array(
    [
        [float(x) for x in line.split()]
        for line in _LEAP_TEXT.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
)
_expected = np.array(
    [(int(row[3]), int(row[2]), row[4]) for row in _rows], dtype=erfa.leap_seconds.get().dtype
)
_actual = erfa.leap_seconds.get()
_actual = _actual[_actual["year"] >= 1972]
if not np.array_equal(_actual, _expected):
    raise RuntimeError("ERFA leap-second history differs from the pinned IERS table")
_match = re.search(r"expires on (.+)", _LEAP_TEXT)
if _match is None:
    raise RuntimeError("Bundled leap table has no expiry")
_EXPIRY = datetime.strptime(_match.group(1).strip(), "%d %B %Y")
LEAP_EXPIRY_JD = float(erfa.cal2jd(_EXPIRY.year, _EXPIRY.month, _EXPIRY.day)[1] + 2400000.5)


@dataclass(frozen=True)
class ResolvedTime:
    tt1: float
    tt2: float
    tdb1: float
    tdb2: float
    ut11: float | None
    ut12: float | None
    utc1: float | None
    utc2: float | None
    quality: dict[str, Any]

    def shift(self, days: float) -> "ResolvedTime":
        # A TT increment has no civil-day/leap ambiguity.
        tt2 = self.tt2 + days
        dtr = erfa.dtdb(self.tt1, tt2, 0, 0, 0, 0)
        a, b = erfa.tttdb(self.tt1, tt2, dtr)
        return replace(
            self,
            tt2=tt2,
            tdb1=float(a),
            tdb2=float(b),
            ut12=None if self.ut12 is None else self.ut12 + days,
            utc1=None,
            utc2=None,
        )

    def metadata(self) -> dict[str, Any]:
        return {
            "jd_tt": [self.tt1, self.tt2],
            "jd_tdb": [self.tdb1, self.tdb2],
            "jd_ut1": None if self.ut11 is None else [self.ut11, self.ut12],
            "quality": self.quality,
        }


def delta_t_model(year: float) -> float:
    """Espenak/Meeus published piecewise polynomials; explicit model, not EOP."""
    if year < 1900 or year >= 2150:
        raise AriaError("OUT_OF_RANGE", "Delta-T model is restricted to 1900-2149")
    if year < 1920:
        t = year - 1900
        return -2.79 + 1.494119 * t - 0.0598939 * t * t + 0.0061966 * t**3 - 0.000197 * t**4
    if year < 1941:
        t = year - 1920
        return 21.20 + 0.84493 * t - 0.076100 * t * t + 0.0020936 * t**3
    if year < 1961:
        t = year - 1950
        return 29.07 + 0.407 * t - t * t / 233 + t**3 / 2547
    if year < 1986:
        t = year - 1975
        return 45.45 + 1.067 * t - t * t / 260 - t**3 / 718
    if year < 2005:
        t = year - 2000
        return (
            63.86
            + 0.3345 * t
            - 0.060374 * t * t
            + 0.0017275 * t**3
            + 0.000651814 * t**4
            + 0.00002373599 * t**5
        )
    if year < 2050:
        t = year - 2000
        return 62.92 + 0.32217 * t + 0.005589 * t * t
    return -20 + 32 * ((year - 1820) / 100) ** 2 - 0.5628 * (2150 - year)


def _civil(value: str, ti: TimeInput) -> tuple[int, int, int, int, int, float]:
    # Leap second notation is handled separately from datetime's 0..59 seconds.
    leap = bool(re.search(r":60(?:[.]\d+)?(?:Z|[+]00:00)$", value))
    if leap:
        value = re.sub(r":60", ":59", value, count=1)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise AriaError("INVALID_REQUEST", "Invalid ISO date/time") from e
    if ti.scale.upper() != "UTC":
        if dt.utcoffset() not in (None, datetime.min.replace(tzinfo=timezone.utc).utcoffset()):
            raise AriaError("INVALID_REQUEST", "Non-UTC scale cannot have a timezone offset")
        if ti.timezone:
            raise AriaError("INVALID_REQUEST", "Timezone only applies to UTC civil input")
    elif dt.tzinfo is None:
        if not ti.timezone:
            raise AriaError("AMBIGUOUS_LOCAL_TIME", "Supply a timezone or UTC offset")
        try:
            zone = ZoneInfo(ti.timezone)
        except ZoneInfoNotFoundError as e:
            raise AriaError("INVALID_REQUEST", "Unknown IANA timezone") from e
        candidates = []
        for fold in (0, 1):
            aware = dt.replace(tzinfo=zone, fold=fold)
            back = aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
            if back == dt:
                candidates.append(aware)
        if not candidates:
            raise AriaError("NONEXISTENT_LOCAL_TIME", "Local time falls in a DST gap")
        if len(candidates) == 2 and candidates[0].utcoffset() != candidates[1].utcoffset():
            if ti.fold not in (0, 1):
                raise AriaError("AMBIGUOUS_LOCAL_TIME", "Supply fold=0 or fold=1")
            dt = candidates[ti.fold]
        else:
            dt = candidates[0]
    if ti.scale.upper() == "UTC":
        dt = dt.astimezone(timezone.utc)
    return (
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1e6 + int(leap),
    )


def resolve(ti: TimeInput, strict: bool = True, require_ut1: bool = False) -> ResolvedTime:
    ti = TimeInput.parse(ti)
    scale = ti.scale.upper()
    if scale not in ("UTC", "TT", "TDB", "UT1"):
        raise AriaError("INVALID_REQUEST", "Supported scales: UTC, TT, TDB, UT1")
    if (ti.value is None) == (ti.jd is None):
        raise AriaError("INVALID_REQUEST", "Supply exactly one of value or jd")
    quality: dict[str, Any] = {
        "leap_table_sha256": LEAP_HASH,
        "leap_table_expires": _EXPIRY.date().isoformat(),
        "time_model": "ERFA-2.0.1.5",
        "input_scale": scale,
        "warnings": [],
    }
    if ti.jd is not None:
        j1, j2 = map(float, ti.jd)
        if not np.isfinite([j1, j2]).all():
            raise AriaError("INVALID_REQUEST", "Julian date must be finite")
    else:
        assert ti.value is not None
        y, mo, d, h, mi, se = _civil(ti.value, ti)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", erfa.ErfaWarning)
            j1, j2 = map(float, erfa.dtf2d(scale, y, mo, d, h, mi, se))
        if se >= 60:
            if scale != "UTC":
                raise AriaError("INVALID_REQUEST", "Leap seconds apply only to UTC")
            # ERFA reports invalid 60s on non-leap days; enforce rather than ignoring.
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                erfa.dtf2d("UTC", y, mo, d, h, mi, se)
            if caught:
                raise AriaError("INVALID_REQUEST", "Not a valid recorded leap second")
    u1 = u2 = None
    utc1 = utc2 = None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", erfa.ErfaWarning)
        if scale == "UTC":
            if j1 + j2 < 2441317.5:  # Explicitly no invented pre-1972 UTC policy.
                raise AriaError(
                    "TIME_DATA_UNAVAILABLE", "Pre-1972 civil input requires explicit TT or UT1"
                )
            if j1 + j2 >= LEAP_EXPIRY_JD:
                if strict:
                    raise AriaError("TIME_DATA_UNAVAILABLE", "UTC date exceeds leap-table validity")
                quality["warnings"].append("Future UTC assumes no additional leap seconds")
                quality["utc_status"] = "assumed"
            else:
                quality["utc_status"] = "recorded-table"
            utc1, utc2 = j1, j2
            a, b = erfa.utctai(j1, j2)
            t1, t2 = map(float, erfa.taitt(a, b))
            if ti.dut1_seconds is not None:
                u1, u2 = map(float, erfa.utcut1(j1, j2, ti.dut1_seconds))
                quality["ut1_status"] = "user-supplied-DUT1"
        elif scale == "TT":
            t1, t2 = j1, j2
        elif scale == "TDB":
            t1, t2 = j1, j2
            for _ in range(3):
                dtr = erfa.dtdb(t1, t2, 0, 0, 0, 0)
                t1, t2 = map(float, erfa.tdbtt(j1, j2, dtr))
        else:
            u1, u2 = j1, j2
            if ti.delta_t_seconds is None:
                if strict:
                    raise AriaError(
                        "TIME_DATA_UNAVAILABLE", "UT1 input requires delta_t_seconds in strict mode"
                    )
                y, mo, _, _ = erfa.jd2cal(j1, j2)
                dt = delta_t_model(float(y) + (float(mo) - 0.5) / 12)
                quality["warnings"].append("TT derived from modelled delta-T")
            else:
                dt = ti.delta_t_seconds
            t1, t2 = j1, j2 + dt / DAY
            quality["ut1_status"] = "explicit-UT1"
        if require_ut1 and u1 is None:
            dt_input = ti.delta_t_seconds
            if dt_input is None:
                if strict:
                    raise AriaError(
                        "TIME_DATA_UNAVAILABLE", "Supply DUT1 or delta-T for Earth rotation"
                    )
                y, mo, _, _ = erfa.jd2cal(t1, t2)
                dt = delta_t_model(float(y) + (float(mo) - 0.5) / 12)
                quality["ut1_status"] = "Espenak-Meeus-2006-polynomial"
                quality["warnings"].append(
                    "UT1 modelled; absolute chart-angle accuracy is not guaranteed"
                )
            else:
                dt = dt_input
                quality["ut1_status"] = "user-supplied-delta-T"
            u1, u2 = t1, t2 - dt / DAY
        dtr = erfa.dtdb(t1, t2, 0, 0, 0, 0)
        b1, b2 = map(float, erfa.tttdb(t1, t2, dtr))
    if not np.isfinite([t1, t2, b1, b2]).all():
        raise AriaError("INVALID_REQUEST", "Time conversion produced non-finite values")
    return ResolvedTime(t1, t2, b1, b2, u1, u2, utc1, utc2, quality)
