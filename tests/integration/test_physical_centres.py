# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""True multi-kernel calculation path, one verified satellite source per matrix job."""

import os
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from ariaephemeris import AriaError, Ephemeris, PositionRequest, TimeInput
from ariaephemeris.datasets import verify_centre_sources
from ariaephemeris.sources.centres import CENTRE_IDS

pytestmark = pytest.mark.kernel


def installed_source():
    name = os.environ.get("ARIA_CENTRE_BODY")
    filename = os.environ.get("ARIA_CENTRE_KERNEL")
    base = os.environ.get("ARIA_KERNEL")
    if not (name and filename and base):
        pytest.skip("ARIA_KERNEL, ARIA_CENTRE_BODY and ARIA_CENTRE_KERNEL required")
    return name, Path(filename), Path(base)


def test_physical_centres_opt_in_end_to_end():
    name, satellite, base = installed_source()
    assert name in CENTRE_IDS
    verify_centre_sources({name: satellite})

    t = TimeInput(jd=(2451545.0, 0.0), scale="TT")
    r = PositionRequest(t, bodies=(name,))
    with Ephemeris(base) as reference, Ephemeris(
        base, centre_kernels={name: satellite}
    ) as physical:
        regular = reference.positions(r)
        regular_with_satellite = physical.positions(r)
        # Supplying an SPK must never alter the default 'reference' profile.
        assert regular.to_dict() == regular_with_satellite.to_dict()
        assert regular.bodies[0].target_id == CENTRE_IDS[name][1]
        assert regular.bodies[0].target_kind == "planetary-system-barycentre"

        request = replace(r, profile="planet-centres-v1")
        result = physical.positions(request)
        actual = result.bodies[0]
        assert actual.target_id == CENTRE_IDS[name][0]
        assert actual.target_kind == "body-centre"
        assert result.metadata["profile"] == "planet-centres-v1"
        assert result.metadata["qualification"] == "not-qualified-for-commercial-release"
        assert result.metadata["physical_centre_sources"][name]["source_sha256"]
        assert result.metadata["physical_centre_sources"][name]["offset_parent_id"] == (
            CENTRE_IDS[name][1]
        )
        raw = physical.raw_state(name, t, profile="planet-centres-v1")
        barycentre = physical.raw_state(name, t)
        assert raw["target_id"] == CENTRE_IDS[name][0]
        assert barycentre["target_id"] == CENTRE_IDS[name][1]
        assert np.isfinite(raw["position_km"]).all()
        assert np.isfinite(raw["velocity_km_day"]).all()
        assert np.linalg.norm(
            np.asarray(raw["position_km"]) - np.asarray(barycentre["position_km"])
        ) > 0.0

        batch = physical.positions_batch(
            request,
            [t, TimeInput(jd=(2451565.0, 0.0), scale="TT")],
        )
        assert len(batch) == 2
        assert batch[0].to_dict() == result.to_dict()
        for sample, time in zip(batch, (t, TimeInput(jd=(2451565.0, 0.0), scale="TT"))):
            scalar = physical.positions(replace(request, time=time))
            assert [x.longitude_deg for x in sample.bodies] == pytest.approx(
                [x.longitude_deg for x in scalar.bodies], abs=1e-11
            )

        geometric = physical.positions(replace(request, position_mode="geometric"))
        assert geometric.bodies[0].target_id == actual.target_id
        assert np.isfinite(geometric.bodies[0].longitude_rate_deg_day)
        assert np.isfinite(actual.longitude_rate_deg_day)
        assert actual.distance_au > 0

        # A partial source installation must not silently supply a barycentre
        # when a different physical centre is requested.
        other = next(b for b in CENTRE_IDS if b != name)
        with pytest.raises(AriaError, match="not installed"):
            physical.positions(replace(request, bodies=(other,)))

        info = physical.dataset_info()
        assert info["physical_centres"][name]["target_id"] == CENTRE_IDS[name][0]

    with Ephemeris(base) as no_centres:
        with pytest.raises(AriaError, match="not installed"):
            no_centres.positions(replace(r, profile="planet-centres-v1"))


def test_invalid_profile_and_missing_source_fail_explicitly():
    _, _, base = installed_source()
    t = TimeInput(jd=(2451545.0, 0.0), scale="TT")
    with Ephemeris(base) as e:
        with pytest.raises(AriaError, match="Unknown calculation profile"):
            e.positions(PositionRequest(t, bodies=("jupiter",), profile="invented-profile"))
