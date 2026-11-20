# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Pinned Bulletin A data, explicit installation and leap-safe offline interpolation."""

import hashlib
import json
import os
import tempfile
import urllib.request
import warnings
from bisect import bisect_left
from copy import deepcopy
from dataclasses import dataclass, replace
from importlib.resources import files
from pathlib import Path
from typing import Any

import erfa
import numpy as np

from ..errors import AriaError
from . import DAY, LEAP_HASH, ResolvedTime


def manifest() -> dict[str, Any]:
    return json.loads(files("ariaephemeris.resources").joinpath("eop-v1.json").read_text())


@dataclass(frozen=True)
class EOPRow:
    mjd: float
    xp: float
    yp: float
    dut1: float
    xp_error: float
    yp_error: float
    dut1_error: float
    polar_flag: str
    ut1_flag: str
    tai_minus_utc: float


def parse(data: bytes) -> tuple[EOPRow, ...]:
    """Parse original daily A columns; trailing unavailable rows are not extrapolated."""
    records = []
    previous = None
    try:
        text = data.decode("ascii")
        for line in text.splitlines():
            if not line.strip():
                continue
            if len(line) < 78:
                raise ValueError("Truncated finals2000A record")
            mjd = float(line[7:15])
            if not np.isfinite(mjd) or mjd != int(mjd):
                raise ValueError("Expected a finite daily midnight MJD")
            if previous is not None and mjd <= previous:
                raise ValueError("EOP dates are duplicated or unordered")
            previous = mjd
            year = int(line[:2]) + (1900 if mjd <= 51543 else 2000)
            month, day = int(line[2:4]), int(line[4:6])
            if float(erfa.cal2jd(year, month, day)[1]) != mjd:
                raise ValueError("Calendar and MJD disagree")
            if not line[16:78].strip():
                # Source includes date-only placeholders beyond its prediction horizon.
                continue
            pf, uf = line[16], line[57]
            if pf not in ("I", "P") or uf not in ("I", "P"):
                raise ValueError("Missing/unknown Bulletin A quality flags")
            x, xe, y, ye, u, ue = [
                float(line[a:b])
                for a, b in ((18, 27), (27, 36), (37, 46), (46, 55), (58, 68), (68, 78))
            ]
            if not np.isfinite([x, xe, y, ye, u, ue]).all() or min(xe, ye, ue) < 0:
                raise ValueError("Nonfinite EOP value or invalid formal error")
            if max(abs(x), abs(y)) > 5 or abs(u) > 1:
                raise ValueError("EOP values exceed supported arcsecond/second ranges")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", erfa.ErfaWarning)
                dat = float(erfa.dat(year, month, day, 0))
            records.append(EOPRow(mjd, x, y, u, xe, ye, ue, pf, uf, dat))
    except (ValueError, UnicodeError, erfa.ErfaError) as e:
        raise AriaError("DATA_INTEGRITY_ERROR", f"Invalid finals2000A data: {e}") from e
    if len(records) < 2:
        raise AriaError("DATA_INTEGRITY_ERROR", "At least two complete EOP records are required")
    return tuple(records)


def verify(path: str | Path) -> tuple[dict[str, Any], tuple[EOPRow, ...]]:
    m = manifest()
    try:
        source = Path(path)
        if source.stat().st_size != m["size_bytes"]:
            raise AriaError("DATA_INTEGRITY_ERROR", "EOP snapshot size/checksum mismatch")
        data = source.read_bytes()
    except OSError as e:
        raise AriaError(
            "TIME_DATA_UNAVAILABLE", "Install the pinned EOP snapshot explicitly"
        ) from e
    if len(data) != m["size_bytes"] or hashlib.sha256(data).hexdigest() != m["sha256"]:
        raise AriaError("DATA_INTEGRITY_ERROR", "EOP snapshot size/checksum mismatch")
    if m["leap_table_sha256"] != LEAP_HASH:
        raise AriaError("DATA_INTEGRITY_ERROR", "EOP interpolation leap-table identity mismatch")
    rows = parse(data)
    if (rows[0].mjd, rows[-1].mjd) != (m["first_mjd_utc"], m["last_mjd_utc"]):
        raise AriaError("DATA_INTEGRITY_ERROR", "EOP manifest coverage mismatch")
    return m, rows


def install(directory: str | Path, source: str | Path | None = None) -> Path:
    """Only this explicit operation may download; never replace an installed snapshot."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    m = manifest()
    destination = directory / f"{m['dataset_id']}.all"
    if destination.exists():
        verify(destination)
        return destination
    fd, name = tempfile.mkstemp(prefix="aria-eop-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            stream = (
                Path(source).open("rb")
                if source is not None
                else urllib.request.urlopen(m["source_url"], timeout=60)
            )
            with stream:
                total = 0
                for block in iter(lambda: stream.read(65536), b""):
                    total += len(block)
                    if total > m["size_bytes"]:
                        raise AriaError("DATA_INTEGRITY_ERROR", "EOP download exceeds pinned size")
                    out.write(block)
        verify(name)
        os.replace(name, destination)
        return destination
    finally:
        Path(name).unlink(missing_ok=True)


class EarthOrientation:
    """Immutable source rows for one verified snapshot; no network or implicit updates."""

    def __init__(self, path: str | Path, *, allow_predictions: bool = False) -> None:
        if not isinstance(allow_predictions, bool):
            raise AriaError("INVALID_REQUEST", "allow_predictions must be boolean")
        self._manifest, self._rows = verify(path)
        self._epochs = tuple(r.mjd for r in self._rows)
        self._allow_predictions = allow_predictions

    def info(self) -> dict[str, Any]:
        return {
            **deepcopy(self._manifest),
            "allow_predictions": self._allow_predictions,
            "interpolation": "linear-UT1-minus-TAI-and-polar-motion-in-TAI-v1",
            "celestial_pole_offsets_applied": False,
        }

    def lookup(
        self, time: ResolvedTime, *, require_ut1: bool = True, require_polar: bool = True
    ) -> dict[str, Any]:
        if time.utc1 is None or time.utc2 is None:
            raise AriaError(
                "TIME_DATA_UNAVAILABLE", "Managed EOP requires explicit modern UTC input"
            )
        # UTC quasi-JD is nonuniform on leap days. Interpolate on continuous TAI instead.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", erfa.ErfaWarning)
            a, b = erfa.utctai(time.utc1, time.utc2)
            y, m, d, fraction_utc = erfa.jd2cal(time.utc1, time.utc2)
            dat = float(erfa.dat(y, m, d, 0))
            day = float(erfa.cal2jd(y, m, d)[1])
        # Keep the two-part epoch precision, including sub-microsecond boundaries.
        # Searching on a collapsed float MJD can round an out-of-range epoch onto a node.
        i = bisect_left(self._epochs, day)
        on_day = i < len(self._epochs) and self._epochs[i] == day
        rows: tuple[EOPRow, ...]
        if on_day and fraction_utc == 0:
            rows = (self._rows[i],)
            fraction = 0.0
        else:
            if on_day:
                i += 1
            if i == 0 or i == len(self._epochs):
                raise AriaError("TIME_DATA_UNAVAILABLE", "EOP date outside installed coverage")
            rows = (self._rows[i - 1], self._rows[i])
            if rows[1].mjd - rows[0].mjd != 1:
                raise AriaError("TIME_DATA_UNAVAILABLE", "EOP interpolation crosses a missing day")
            elapsed = ((a - (2400000.5 + rows[0].mjd)) + b) * DAY - rows[0].tai_minus_utc
            duration = (
                (rows[1].mjd - rows[0].mjd) * DAY + rows[1].tai_minus_utc - rows[0].tai_minus_utc
            )
            fraction = float(elapsed / duration)
        predicted = any(
            (require_polar and r.polar_flag == "P") or (require_ut1 and r.ut1_flag == "P")
            for r in rows
        )
        if predicted and not self._allow_predictions:
            raise AriaError("TIME_DATA_UNAVAILABLE", "Predicted EOP requires explicit opt-in")
        if predicted and day >= self._manifest["prediction_valid_until_mjd_utc"]:
            raise AriaError(
                "TIME_DATA_UNAVAILABLE", "EOP prediction validity expired for this epoch"
            )

        def interpolate(values: list[float]) -> float:
            return values[0] if len(values) == 1 else values[0] + fraction * (values[1] - values[0])

        dut1 = interpolate([r.dut1 - r.tai_minus_utc for r in rows]) + dat
        polar_status = "predicted" if any(r.polar_flag == "P" for r in rows) else "observed"
        ut1_status = "predicted" if any(r.ut1_flag == "P" for r in rows) else "observed"
        return {
            "dataset_id": self._manifest["dataset_id"],
            "sha256": self._manifest["sha256"],
            "interpolation": self.info()["interpolation"],
            "mjd_utc_nodes": [r.mjd for r in rows],
            "fraction_tai": fraction,
            "dut1_seconds": dut1,
            "xp_arcsec": interpolate([r.xp for r in rows]),
            "yp_arcsec": interpolate([r.yp for r in rows]),
            "ut1_status": ut1_status,
            "polar_motion_status": polar_status,
            "source_series": "Bulletin A IERS rapid values (provisional), not final Bulletin B",
            "formal_errors_at_nodes": [
                {"dut1_seconds": r.dut1_error, "xp_arcsec": r.xp_error, "yp_arcsec": r.yp_error}
                for r in rows
            ],
            "physical_uncertainty_seconds": None,
            "celestial_pole_offsets_applied": False,
            "prediction_valid_until_mjd_utc": self._manifest["prediction_valid_until_mjd_utc"],
        }

    def apply(self, time: ResolvedTime, *, dut1: bool, xp: bool, yp: bool) -> ResolvedTime:
        """Attach source values and a shifted-epoch resolver for topocentric rates."""
        record = self.lookup(time, require_ut1=dut1, require_polar=xp or yp)
        quality = deepcopy(time.quality)
        record["applied"] = {"dut1": dut1, "xp": xp, "yp": yp}
        quality["earth_orientation"] = record
        if dut1:
            a, b = erfa.utcut1(time.utc1, time.utc2, record["dut1_seconds"])
            time = replace(time, ut11=float(a), ut12=float(b))
            quality["ut1_status"] = "managed-EOP-" + record["ut1_status"]
            quality["dut1_seconds"] = record["dut1_seconds"]
        warning = "Predicted Earth orientation used by explicit opt-in"
        if (dut1 and record["ut1_status"] == "predicted") or (
            (xp or yp) and record["polar_motion_status"] == "predicted"
        ):
            if warning not in quality["warnings"]:
                quality["warnings"].append(warning)

        def shifted(t: ResolvedTime) -> ResolvedTime:
            # The originating UTC request passed the pinned leap policy. Convert the
            # nearby TT derivative epoch back through TAI; lookup enforces its coverage.
            a, b = erfa.tttai(t.tt1, t.tt2)
            c, d = erfa.taiutc(a, b)
            return self.apply(replace(t, utc1=float(c), utc2=float(d)), dut1=dut1, xp=xp, yp=yp)

        return replace(time, quality=quality, _eop_shift=shifted)
