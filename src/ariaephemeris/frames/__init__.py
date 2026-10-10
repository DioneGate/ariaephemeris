# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""IAU 2006 / 2000A frames, with explicit ecliptic/equinox definitions."""

from typing import Any

import erfa
import numpy as np

from ..errors import AriaError
from ..models import Observer
from ..time import ResolvedTime

AU_KM = 149597870.700


def rotation(frame: str, tt1: Any, tt2: Any) -> Any:
    if frame == "icrs":
        return np.broadcast_to(np.eye(3), np.broadcast(tt1, tt2).shape + (3, 3))
    if frame == "ecliptic_j2000":
        return np.broadcast_to(erfa.ecm06(2451545.0, 0.0), np.broadcast(tt1, tt2).shape + (3, 3))
    if frame == "mean_ecliptic_of_date":
        return erfa.ecm06(tt1, tt2)
    if frame == "true_ecliptic_of_date":
        eps = erfa.obl06(tt1, tt2) + erfa.nut06a(tt1, tt2)[1]
        # ICRS -> true equator/equinox -> ecliptic: R_x(+true obliquity).
        c, s = np.cos(eps), np.sin(eps)
        rx = np.zeros(np.shape(eps) + (3, 3))
        rx[..., 0, 0] = 1
        rx[..., 1, 1] = c
        rx[..., 1, 2] = s
        rx[..., 2, 1] = -s
        rx[..., 2, 2] = c
        return rx @ erfa.pnm06a(tt1, tt2)
    raise AriaError("UNSUPPORTED_FRAME", frame)


def spherical(v: Any) -> tuple[Any, Any, Any]:
    r = np.linalg.norm(v, axis=-1)
    if np.any(r == 0):
        raise AriaError("UNDEFINED_POSITION", "Target coincides with observer")
    lon = np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360
    lat = np.degrees(np.arctan2(v[..., 2], np.hypot(v[..., 0], v[..., 1])))
    return lon, lat, r


def observer_state(o: Observer, t: ResolvedTime, strict: bool) -> tuple[Any, Any, list[str]]:
    if t.ut11 is None:
        raise AriaError("TIME_DATA_UNAVAILABLE", "Topocentric position requires UT1")
    if not np.isfinite([o.latitude_deg, o.longitude_deg, o.elevation_m]).all():
        raise AriaError("INVALID_REQUEST", "Observer coordinates must be finite")
    if not -90 <= o.latitude_deg <= 90 or not -180 <= o.longitude_deg <= 180:
        raise AriaError("INVALID_REQUEST", "Observer latitude/longitude out of range")
    notes = []
    if o.xp_arcsec is None or o.yp_arcsec is None:
        if strict:
            raise AriaError(
                "TIME_DATA_UNAVAILABLE", "Strict topocentric mode requires polar motion"
            )
        notes.append("Polar motion set to zero")
    xp = (o.xp_arcsec or 0) * erfa.DAS2R
    yp = (o.yp_arcsec or 0) * erfa.DAS2R
    fixed = (
        erfa.gd2gc(1, np.radians(o.longitude_deg), np.radians(o.latitude_deg), o.elevation_m) / 1000
    )

    assert t.ut12 is not None
    ut12 = t.ut12

    def orientation(dt: float) -> Any:
        return erfa.c2t06a(t.tt1, t.tt2 + dt, t.ut11, ut12 + dt, xp, yp).T

    pos = orientation(0) @ fixed
    h = 0.5 / 86400
    vel = (orientation(h) @ fixed - orientation(-h) @ fixed) / (2 * h)
    return pos, vel, notes
