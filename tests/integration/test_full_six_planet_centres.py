# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Full six-kernel smoke: one instance must compose all physical centres safely."""

import os
from pathlib import Path

import pytest

from ariaephemeris import Ephemeris, Observer, PositionRequest, TimeInput
from ariaephemeris.datasets import centres_manifest

pytestmark = pytest.mark.kernel


def test_all_six_sources_in_one_complete_chart_and_batch():
    base = os.environ.get("ARIA_KERNEL")
    root = os.environ.get("ARIA_CENTRES_DIR")
    if not base or not root:
        pytest.skip("Provide verified ARIA_KERNEL and ARIA_CENTRES_DIR")
    sources = {
        body: Path(root) / row["filename"] for body, row in centres_manifest()["sources"].items()
    }
    t = TimeInput(jd=(2451545.0, 0.0), scale="TT", delta_t_seconds=64.0)
    physical = PositionRequest(t, profile="planet-centres-v1")
    reference = PositionRequest(t)

    with Ephemeris(base, centre_kernels=sources) as engine:
        physical_result = engine.positions(physical)
        assert len(physical_result.bodies) == 10
        assert physical_result.metadata["profile"] == "planet-centres-v1"
        assert len(physical_result.metadata["physical_centre_sources"]) == 6
        targets = {body.body: body.target_id for body in physical_result.bodies}
        for body, source in centres_manifest()["sources"].items():
            assert targets[body] == source["target_id"]
        assert all(x.target_kind == "body-centre" for x in physical_result.bodies)
        assert all(x.distance_au > 0 for x in physical_result.bodies)

        chart = engine.chart(physical, Observer(51.5, -0.1), house_system="whole_sign")
        assert chart.positions.metadata["profile"] == "planet-centres-v1"
        assert len(chart.houses) == 10
        assert len(chart.house_cusps_deg) == 12
        assert chart.aspects

        times = (t, TimeInput(jd=(2451565.0, 0), scale="TT", delta_t_seconds=64.0))
        batch = engine.positions_batch(physical, times)
        assert len(batch) == 2
        assert {b.body: b.target_id for b in batch[0].bodies} == targets

        legacy = engine.positions(reference)
        assert legacy.metadata["profile"] == "reference"
        assert all(
            b.target_kind == "planetary-system-barycentre"
            for b in legacy.bodies
            if b.body in sources
        )
        info = engine.dataset_info()
        assert len(info["physical_centres"]) == 6
        assert len({x["source_sha256"] for x in info["physical_centres"].values()}) == 6
