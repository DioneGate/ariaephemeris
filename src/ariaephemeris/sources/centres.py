# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Opt-in, checksum-pinned centre offsets added to the existing DE442s base.

Satellite kernels are ONLY used for direct physical centre -> barycentre
segments. Their unrelated planetary chains never override Aria's base kernel.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
from jplephem.spk import SPK

from ..errors import AriaError
from . import Kernel

CENTRE_IDS = {
    "mars": (499, 4),
    "jupiter": (599, 5),
    "saturn": (699, 6),
    "uranus": (799, 7),
    "neptune": (899, 8),
    "pluto": (999, 9),
}
CENTRE_BY_TARGET = {target: (name, parent) for name, (target, parent) in CENTRE_IDS.items()}


class PhysicalCentreKernel:
    """Read-only resolver. Base kernel remains owned by Ephemeris."""

    def __init__(
        self,
        base: Kernel,
        paths: Mapping[str, str | Path],
        checked_sources: Mapping[str, dict[str, Any]],
        interval: tuple[float, float],
    ) -> None:
        self._base = base
        self._spks: dict[str, Any] = {}
        self._segments: dict[str, tuple[Any, ...]] = {}
        self._sources = {body: dict(record) for body, record in checked_sources.items()}
        try:
            for body, value in paths.items():
                target, parent = CENTRE_IDS[body]
                spk = SPK.open(str(value))
                self._spks[body] = spk
                chosen = []
                for segment in spk.segments:
                    if segment.target != target or segment.center != parent:
                        continue
                    if segment.data_type not in (2, 3):
                        raise AriaError(
                            "UNSUPPORTED_KERNEL",
                            f"{body}: physical-centre SPK type {segment.data_type} unsupported",
                        )
                    if segment.frame != 1:
                        raise AriaError(
                            "UNSUPPORTED_FRAME",
                            f"{body}: physical-centre SPK frame {segment.frame} unsupported",
                        )
                    segment.load_array()  # Only the direct centre records; safe concurrent reads.
                    chosen.append(segment)
                if not chosen:
                    raise AriaError(
                        "DATA_INTEGRITY_ERROR", f"{body}: no direct {target}/{parent} offset"
                    )
                # Inspect all direct segment spans; avoid eager-loading unrelated satellite data.
                lo, hi = interval
                cursor = lo
                for s in sorted(chosen, key=lambda x: (x.start_jd, x.end_jd)):
                    if s.start_jd > cursor:
                        raise AriaError(
                            "OUT_OF_RANGE", f"{body}: missing centre segment near JD {cursor}"
                        )
                    cursor = max(cursor, s.end_jd)
                    if cursor >= hi:
                        break
                if cursor < hi:
                    raise AriaError("OUT_OF_RANGE", f"{body}: physical-centre source ends early")
                self._segments[body] = tuple(chosen)
        except AriaError:
            self.close()
            raise
        except Exception as error:
            self.close()
            raise AriaError(
                "DATA_INTEGRITY_ERROR", f"Cannot initialise centre SPK: {error}"
            ) from error

    def state(
        self, target: int, jd1: Any, jd2: Any = 0.0, visited: frozenset[int] = frozenset()
    ) -> tuple[Any, Any]:
        if target not in CENTRE_BY_TARGET:
            return self._base.state(target, jd1, jd2, visited)
        body, parent = CENTRE_BY_TARGET[target]
        segments = self._segments.get(body)
        if segments is None:
            raise AriaError("DATA_UNAVAILABLE", f"Physical-centre SPK not installed: {body}")
        if target in visited:
            raise AriaError("DATA_INTEGRITY_ERROR", "Cyclic physical-centre chain")
        j1, j2 = np.broadcast_arrays(np.asarray(jd1, dtype=float), np.asarray(jd2, dtype=float))
        shape = j1.shape
        result_p = np.zeros((3,) + shape)
        result_v = np.zeros_like(result_p)
        todo = np.ones(shape, dtype=bool)
        for segment in reversed(segments):
            mask = todo & ((j1 + j2) >= segment.start_jd) & ((j1 + j2) <= segment.end_jd)
            if not np.any(mask):
                continue
            offset_p, offset_v = segment.compute_and_differentiate(j1[mask], j2[mask])
            if segment.data_type == 3:
                offset_p, offset_v = offset_p[:3], offset_p[3:] * 86400.0
            # Crucially resolve the planetary system barycentre via Aria's DE442s.
            base_p, base_v = self._base.state(parent, j1[mask], j2[mask])
            result_p[:, mask] = offset_p + base_p
            result_v[:, mask] = offset_v + base_v
            todo[mask] = False
        if np.any(todo):
            raise AriaError("OUT_OF_RANGE", f"{body}: physical-centre offset unavailable at epoch")
        return result_p, result_v

    def provenance(self, bodies: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        return {
            body: {
                "target_id": self._sources[body]["target_id"],
                "offset_parent_id": self._sources[body]["centre_id"],
                "source_file": self._sources[body]["filename"],
                "source_sha256": self._sources[body]["sha256"],
            }
            for body in bodies
            if body in self._sources
        }

    def close(self) -> None:
        for spk in self._spks.values():
            spk.close()
        self._spks.clear()
