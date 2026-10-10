# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Angles, equal/whole-sign houses and explicitly defined longitude aspects."""

import math
from itertools import combinations
from typing import Any

import erfa
import numpy as np

from ..errors import AriaError
from ..models import Aspect, AspectRule, BodyPosition, Observer
from ..numerics import circular_difference
from ..time import ResolvedTime

SIGNS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)
DEFAULT_ASPECTS = tuple(AspectRule(a) for a in (0, 60, 90, 120, 180))


def angles(observer: Observer, t: ResolvedTime) -> dict[str, float]:
    if t.ut11 is None:
        raise AriaError("TIME_DATA_UNAVAILABLE", "Chart angles require UT1")
    lat, lon = observer.latitude_deg, observer.longitude_deg
    if not np.isfinite([lat, lon]).all() or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise AriaError("INVALID_REQUEST", "Invalid geographic coordinates")
    if abs(lat) > 89.999999:
        raise AriaError("HOUSE_UNDEFINED", "Ascendant undefined at a geographic pole")
    theta = float(erfa.gst06a(t.ut11, t.ut12, t.tt1, t.tt2)) + math.radians(lon)
    eps = float(erfa.obl06(t.tt1, t.tt2) + erfa.nut06a(t.tt1, t.tt2)[1])
    phi = math.radians(lat)
    a = math.cos(phi) * math.cos(theta)
    b = math.cos(phi) * math.sin(theta) * math.cos(eps) + math.sin(phi) * math.sin(eps)
    if math.hypot(a, b) < 1e-8:
        raise AriaError("HOUSE_UNDEFINED", "Horizon/ecliptic intersection is degenerate")
    asc = math.atan2(-a, b)
    east = -math.sin(theta) * math.cos(asc) + math.cos(theta) * math.sin(asc) * math.cos(eps)
    if abs(east) < 1e-8:
        raise AriaError("HOUSE_UNDEFINED", "Rising/setting classification is ill-conditioned")
    if east < 0:
        asc += math.pi
    mc = math.atan2(math.sin(theta), math.cos(theta) * math.cos(eps))
    aa, mm = math.degrees(asc) % 360, math.degrees(mc) % 360
    return {"ASC": aa, "DSC": (aa + 180) % 360, "MC": mm, "IC": (mm + 180) % 360}


def cusps(asc: float, system: str) -> tuple[float, ...]:
    if system == "equal":
        first = asc
    elif system == "whole_sign":
        first = math.floor(asc / 30) * 30
    else:
        raise AriaError("UNSUPPORTED_HOUSE_SYSTEM", system)
    return tuple((first + 30 * i) % 360 for i in range(12))


def membership(longitude: float, house_cusps: tuple[float, ...]) -> int:
    # All implemented systems have equal widths; start-inclusive, end-exclusive.
    return int(((longitude - house_cusps[0]) % 360) // 30) + 1


def sign(longitude: float) -> dict[str, Any]:
    index = int((longitude % 360) // 30)
    return {"index": index, "name": SIGNS[index], "longitude_deg": longitude % 30}


def aspects(
    positions: tuple[BodyPosition, ...], rules: tuple[AspectRule, ...] = DEFAULT_ASPECTS
) -> tuple[Aspect, ...]:
    out = []
    for rule in rules:
        if (
            not np.isfinite([rule.angle_deg, rule.orb_deg]).all()
            or not 0 <= rule.angle_deg <= 180
            or not 0 <= rule.orb_deg < 90
        ):
            raise AriaError("INVALID_REQUEST", "Invalid aspect rule")
    for a, b in combinations(positions, 2):
        d = circular_difference(a.longitude_deg, b.longitude_deg)
        separation = abs(d)
        speed = (a.longitude_rate_deg_day - b.longitude_rate_deg_day) * (1 if d >= 0 else -1)
        for rule in rules:
            residual = separation - rule.angle_deg
            if abs(residual) > rule.orb_deg:
                continue
            if abs(residual) < 1e-7 or abs(speed) < 1e-7 or abs(abs(d) - 180) < 1e-7:
                status = "indeterminate"
            else:
                status = "applying" if residual * speed < 0 else "separating"
            out.append(Aspect(a.body, b.body, rule.angle_deg, separation, residual, status))
    return tuple(out)
