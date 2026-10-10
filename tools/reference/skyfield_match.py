# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Independent finite-source deflection equation matched to Aria's limiter.

Only a reference adapter: never imported by the calculation engine. Skyfield
provides independent observer/light-time/aberration/frame calculations. This
explicit vector equation replaces its different alignment-cutoff convention;
it does not call ERFA ld or any Aria positional/numerical routine.
"""

import numpy as np
import skyfield.positionlib
from skyfield.constants import AU_M, GS, C


def limited_deflection(position, pe, rmass):
    # p: observer->source; e: deflector->observer; q: deflector->source.
    length = np.linalg.norm(position, axis=0)
    q = position + pe
    qlength = np.linalg.norm(q, axis=0)
    elength = np.linalg.norm(pe, axis=0)
    p = position / np.where(length, length, 1)
    e = pe / np.where(elength, elength, 1)
    q = q / np.where(qlength, qlength, 1)
    pq = np.sum(p * q, axis=0)
    ep = np.sum(e * p, axis=0)
    qe = np.sum(q * (q + e), axis=0)
    limit = 1e-6 if rmass == 1 else (3e-9 if rmass < 2000 else 3e-10)
    factor = 2 * GS / (C * C * AU_M * rmass * np.where(elength, elength, 1) * np.maximum(qe, limit))
    return factor * (pq * e - ep * q) * length


def apparent(astrometric, deflectors=(10, 599, 699)):
    # A source must not deflect its own ray. Targets here are explicit centres
    # or system barycentres, matching the same kernel IDs as the implementation.
    self_deflector = {10: 10, 5: 599, 6: 699}.get(astrometric.target)
    selected = tuple(x for x in deflectors if x != self_deflector)
    original = skyfield.positionlib._compute_deflection
    try:
        skyfield.positionlib._compute_deflection = limited_deflection
        return astrometric.apparent(deflectors=selected)
    finally:
        skyfield.positionlib._compute_deflection = original
