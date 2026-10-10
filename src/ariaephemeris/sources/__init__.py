# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Immutable adapter for SPK segment precedence and centre chains."""

from pathlib import Path
from typing import Any

import numpy as np
from jplephem.spk import SPK

from ..errors import AriaError


class Kernel:
    def __init__(self, path: Path) -> None:
        try:
            self._spk = SPK.open(str(path))
            self._segments: dict[int, tuple[Any, ...]] = {}
            for s in self._spk.segments:
                if s.data_type not in (2, 3):
                    raise AriaError("UNSUPPORTED_KERNEL", f"Unsupported SPK type {s.data_type}")
                if s.frame != 1:
                    raise AriaError("UNSUPPORTED_FRAME", f"Unsupported SPK frame {s.frame}")
                s.load_array()  # Resolve lazy memory-map state before concurrent reads.
                self._segments[s.target] = self._segments.get(s.target, ()) + (s,)
        except AriaError:
            self._spk.close()
            raise
        except Exception as e:
            raise AriaError("DATA_INTEGRITY_ERROR", f"Cannot read SPK: {e}") from e

    def state(
        self, target: int, jd1: Any, jd2: Any = 0.0, visited: frozenset[int] = frozenset()
    ) -> tuple[Any, Any]:
        j1, j2 = np.broadcast_arrays(np.asarray(jd1, dtype=float), np.asarray(jd2, dtype=float))
        shape = j1.shape
        p = np.zeros((3,) + shape)
        v = np.zeros_like(p)
        if target == 0:
            return p, v
        if target in visited:
            raise AriaError("DATA_INTEGRITY_ERROR", "Cyclic SPK centre chain")
        candidates = self._segments.get(target)
        if not candidates:
            raise AriaError("UNSUPPORTED_BODY", f"No SPK target {target}")
        todo = np.ones(shape, dtype=bool)
        for s in reversed(candidates):
            mask = todo & ((j1 + j2) >= s.start_jd) & ((j1 + j2) <= s.end_jd)
            if not np.any(mask):
                continue
            pp, vv = s.compute_and_differentiate(j1[mask], j2[mask])
            if s.data_type == 3:
                pp, vv = pp[:3], pp[3:] * 86400.0
            cp, cv = self.state(s.center, j1[mask], j2[mask], visited | {target})
            p[:, mask], v[:, mask] = pp + cp, vv + cv
            todo[mask] = False
        if np.any(todo):
            raise AriaError("OUT_OF_RANGE", f"No segment chain covering target {target}")
        return p, v

    def segments(self) -> list[dict[str, Any]]:
        return [
            {
                "target": s.target,
                "centre": s.center,
                "frame": s.frame,
                "type": s.data_type,
                "start_jd_tdb": s.start_jd,
                "end_jd_tdb": s.end_jd,
            }
            for s in self._spk.segments
        ]

    def close(self) -> None:
        self._spk.close()
