# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Generate tiny Aria-owned analytic SPK fixtures; contains no JPL trajectory data."""

from pathlib import Path

import numpy as np
import spiceypy as spice

path = Path(__file__).resolve().parents[2] / "tests/data/linear.bsp"
path.unlink(missing_ok=True)
handle = spice.spkopn(str(path), "ARIA ANALYTIC TEST DATA", 0)
try:

    def type2(target, center, first, last, constant, slope, name):
        coefficients = np.array([constant, slope, 0, 0, 0, 0], dtype=float)
        spice.spkw02(
            handle,
            target,
            center,
            "J2000",
            first,
            last,
            name,
            last - first,
            1,
            1,
            coefficients,
            first,
        )

    type2(399, 0, 0, 172800, 1000, 1, "EARTH TEST")
    type2(42, 399, 0, 172800, 20, 1, "OLD")
    type2(42, 399, 86400, 172800, 50, 1, "NEW")
    # Stored velocity intentionally differs from the derivative of position,
    # demonstrating that Type 3 uses its own velocity coefficients.
    coefficients = np.array([100, 2, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0], dtype=float)
    spice.spkw03(handle, 43, 0, "J2000", 0, 172800, "TYPE3", 172800, 1, 1, coefficients, 0)
finally:
    spice.spkcls(handle)
print(path.name, path.stat().st_size)
