# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Aria-owned observer, light-time, deflection and aberration pipeline."""

from typing import Any

import erfa
import numpy as np

from ..errors import AriaError
from ..frames import AU_KM, observer_state, rotation, spherical
from ..models import BODY_IDS, Observer
from ..sources import Kernel
from ..time import ResolvedTime

C_KM_DAY = 299792.458 * 86400
# Masses relative to the Sun, from the DE442 technical comments.
DEFLECTORS = ((10, 1.0, 1e-6), (5, 1 / 1047.348631, 3e-9), (6, 1 / 3497.901801, 3e-10))


def vectors(
    kernel: Kernel,
    body: str,
    times: list[ResolvedTime],
    origin: str,
    mode: str,
    observer: Observer | None,
    strict: bool,
) -> tuple[Any, Any, list[str]]:
    t1 = np.array([t.tdb1 for t in times])
    t2 = np.array([t.tdb2 for t in times])
    target = BODY_IDS[body]
    if origin in ("geocentric", "topocentric"):
        op, ov = kernel.state(399, t1, t2)
    elif origin == "heliocentric":
        op, ov = kernel.state(10, t1, t2)
    else:
        raise AriaError("INVALID_REQUEST", "Unknown origin")
    notes = []
    if origin == "topocentric":
        if observer is None:
            raise AriaError("INVALID_REQUEST", "Topocentric mode requires observer")
        for i, t in enumerate(times):
            p, v, ns = observer_state(observer, t, strict)
            op[:, i] += p
            ov[:, i] += v
            notes.extend(ns)
    if mode == "geometric":
        p, v = kernel.state(target, t1, t2)
        return ((p - op) / AU_KM).T, ((v - ov) / AU_KM).T, sorted(set(notes))
    if mode != "apparent":
        raise AriaError("INVALID_REQUEST", "Unknown position_mode")
    if origin == "heliocentric":
        raise AriaError(
            "INVALID_REQUEST", "Apparent heliocentric positions are undefined; select geometric"
        )
    lt = np.zeros(len(times))
    for _ in range(12):
        tp, _ = kernel.state(target, t1, t2 - lt)
        ray = tp - op
        distance = np.linalg.norm(ray, axis=0)
        next_lt = distance / C_KM_DAY
        if np.max(np.abs(next_lt - lt)) < 1e-12:
            lt = next_lt
            break
        lt = next_lt
    else:
        raise AriaError("NON_CONVERGENCE", "Light-time iteration failed")
    if np.any(distance == 0):
        raise AriaError("UNDEFINED_POSITION", "Target coincides with observer")
    unit = (ray / distance).T
    # Bodies at closest approach along the finite source-observer light ray.
    for bid, mass, limit in DEFLECTORS:
        if target == bid:
            continue
        bp, _ = kernel.state(bid, t1, t2)
        travel = np.sum((bp - op).T * unit, axis=1) / C_KM_DAY
        travel = np.clip(travel, 0, lt)
        bp, _ = kernel.state(bid, t1, t2 - travel)
        q = (tp - bp).T
        e = (op - bp).T
        qnorm = np.linalg.norm(q, axis=1)
        em = np.linalg.norm(e, axis=1) / AU_KM
        good = (qnorm > 0) & (em > 0)
        unit[good] = erfa.ld(
            mass,
            unit[good],
            q[good] / qnorm[good, None],
            e[good] / (em[good, None] * AU_KM),
            em[good],
            limit,
        )
    sp, _ = kernel.state(10, t1, t2)
    em = np.linalg.norm(op - sp, axis=0) / AU_KM
    beta = ov.T / C_KM_DAY
    unit = erfa.ab(unit, beta, em, np.sqrt(1 - np.sum(beta * beta, axis=1)))
    return unit * (distance / AU_KM)[:, None], None, sorted(set(notes))


def coordinates(
    kernel: Kernel,
    body: str,
    times: list[ResolvedTime],
    origin: str,
    mode: str,
    frame: str,
    observer: Observer | None,
    strict: bool,
) -> tuple[Any, Any, Any, Any, Any, Any, list[str]]:
    v, vel, notes = vectors(kernel, body, times, origin, mode, observer, strict)
    tt1 = np.array([t.tt1 for t in times])
    tt2 = np.array([t.tt2 for t in times])
    r = rotation(frame, tt1, tt2)
    rv = np.einsum("nij,nj->ni", r, v)
    lon, lat, distance = spherical(rv)
    eq = np.einsum("nij,nj->ni", erfa.pnm06a(tt1, tt2), v)
    ra, dec, _ = spherical(eq)
    rate = None
    if vel is not None:
        h = 0.001
        dr = (rotation(frame, tt1, tt2 + h) - rotation(frame, tt1, tt2 - h)) / (2 * h)
        vv = np.einsum("nij,nj->ni", r, vel) + np.einsum("nij,nj->ni", dr, v)
        rate = np.degrees(
            (rv[:, 0] * vv[:, 1] - rv[:, 1] * vv[:, 0]) / (rv[:, 0] ** 2 + rv[:, 1] ** 2)
        )
    return lon, lat, distance, ra, dec, (v, rate), notes
