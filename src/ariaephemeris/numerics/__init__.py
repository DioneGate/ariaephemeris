# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Circular arithmetic and a bounded, bracket-preserving root solver."""

from collections.abc import Callable

import numpy as np

from ..errors import AriaError


def circular_difference(a: float, b: float) -> float:
    return float((a - b + 180.0) % 360.0 - 180.0)


def bisect_root(
    f: Callable[[float], float],
    a: float,
    b: float,
    tolerance_days: float,
    max_iterations: int = 80,
) -> tuple[float, int, float]:
    fa, fb = f(a), f(b)
    if fa == 0:
        return a, 0, 0.0
    if fb == 0:
        return b, 0, 0.0
    if not np.isfinite([fa, fb]).all() or fa * fb > 0:
        raise AriaError("NON_CONVERGENCE", "Root is not bracketed")
    for i in range(max_iterations):
        m = a + (b - a) / 2
        fm = f(m)
        if not np.isfinite(fm):
            raise AriaError("NON_CONVERGENCE", "Non-finite event residual")
        if fm == 0 or b - a <= tolerance_days:
            return m, i + 1, b - a
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    raise AriaError("NON_CONVERGENCE", "Root solver iteration limit")
