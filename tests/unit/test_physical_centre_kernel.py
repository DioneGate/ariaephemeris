# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Kernel-free contracts for the opt-in, direct-centre SPK resolver."""

from types import SimpleNamespace

import numpy as np
import pytest

from ariaephemeris import AriaError
from ariaephemeris.sources.centres import PhysicalCentreKernel


class FakeBase:
    def __init__(self):
        self.calls = []

    def state(self, target, jd1, jd2=0.0, visited=frozenset()):
        self.calls.append(target)
        j1, j2 = np.broadcast_arrays(np.asarray(jd1), np.asarray(jd2))
        shape = (3,) + j1.shape
        return np.full(shape, 100.0), np.full(shape, 200.0)


class FakeSegment:
    target = 599
    center = 5
    data_type = 2
    frame = 1
    start_jd = 10.0
    end_jd = 20.0

    def __init__(self, position, velocity, *, start=10, end=20, dtype=2, frame=1):
        self.position = position
        self.velocity = velocity
        self.start_jd = float(start)
        self.end_jd = float(end)
        self.data_type = dtype
        self.frame = frame

    def compute_and_differentiate(self, jd1, jd2=0):
        shape = (3,) + np.asarray(jd1).shape
        p = np.full(shape, self.position)
        v = np.full(shape, self.velocity)
        if self.data_type == 3:
            return np.concatenate((p, v / 86400), axis=0), None
        return p, v


class FakeSPK:
    def __init__(self, segments):
        self.segments = segments
        self.closed = False

    def close(self):
        self.closed = True


def configured(monkeypatch, segments, interval=(11.0, 19.0)):
    fake = FakeSPK(segments)
    monkeypatch.setattr("ariaephemeris.sources.centres.SPK.open", lambda path: fake)
    base = FakeBase()
    paths = {"jupiter": "dummy-jup349.bsp"}
    records = {
        "jupiter": {
            "target_id": 599,
            "centre_id": 5,
            "filename": "jup349.bsp",
            "sha256": "a" * 64,
        }
    }
    return PhysicalCentreKernel(base, paths, records, interval), base, fake


def test_centre_offset_uses_only_de442s_parent_and_preserves_shape(monkeypatch):
    kernel, base, fake = configured(monkeypatch, [FakeSegment(2, 3)])
    p, v = kernel.state(599, np.array([12.0, 15.0]))
    assert p.shape == (3, 2)
    assert np.all(p == 102.0)
    assert np.all(v == 203.0)
    assert base.calls == [5]
    p0, v0 = kernel.state(599, 12.0)
    assert p0.shape == v0.shape == (3,)
    assert np.all(p0 == 102.0)
    assert base.calls == [5, 5]
    p5, _ = kernel.state(5, 12.0)
    assert np.all(p5 == 100.0)
    assert base.calls == [5, 5, 5]
    assert kernel.provenance(("jupiter",))["jupiter"]["target_id"] == 599
    kernel.close()
    assert fake.closed


def test_silent_missing_centre_fallback_is_prohibited(monkeypatch):
    kernel, base, _ = configured(monkeypatch, [FakeSegment(2, 3)])
    with pytest.raises(AriaError, match="not installed"):
        kernel.state(499, 12.0)
    assert not base.calls


def test_last_segment_wins_at_overlapping_epoch(monkeypatch):
    kernel, _, _ = configured(monkeypatch, [FakeSegment(1, 1), FakeSegment(8, 9)])
    p, v = kernel.state(599, 15.0)
    assert np.all(p == 108.0)
    assert np.all(v == 209.0)


@pytest.mark.parametrize("dtype,frame,error", [(20, 1, "type"), (2, 17, "frame")])
def test_unsupported_direct_segment_rejected(monkeypatch, dtype, frame, error):
    fake = FakeSPK([FakeSegment(1, 1, dtype=dtype, frame=frame)])
    monkeypatch.setattr("ariaephemeris.sources.centres.SPK.open", lambda path: fake)
    with pytest.raises(AriaError, match=error):
        PhysicalCentreKernel(
            FakeBase(),
            {"jupiter": "unused"},
            {"jupiter": {"target_id": 599, "centre_id": 5, "sha256": "a" * 64}},
            (11.0, 19.0),
        )
    assert fake.closed


def test_direct_segment_coverage_gap_is_rejected(monkeypatch):
    with pytest.raises(AriaError, match="missing centre segment"):
        configured(
            monkeypatch, [FakeSegment(2, 3, start=10, end=13), FakeSegment(2, 3, start=15, end=20)]
        )


def test_type_three_velocity_unit_conversion(monkeypatch):
    kernel, _, _ = configured(monkeypatch, [FakeSegment(2, 3, dtype=3)])
    _, v = kernel.state(599, 15.0)
    assert np.allclose(v, 203.0)


def test_closed_source_is_not_used_after_failure(monkeypatch):
    fake = FakeSPK([FakeSegment(2, 3, start=0, end=10)])
    monkeypatch.setattr("ariaephemeris.sources.centres.SPK.open", lambda path: fake)
    with pytest.raises(AriaError, match="missing centre segment"):
        PhysicalCentreKernel(
            FakeBase(),
            {"jupiter": "unused"},
            {"jupiter": {"target_id": 599, "centre_id": 5, "sha256": "a" * 64}},
            (11.0, 19.0),
        )
    assert fake.closed
