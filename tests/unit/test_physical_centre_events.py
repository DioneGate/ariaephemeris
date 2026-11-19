# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Ensure physical-centre search profiles cannot inherit reference timing claims."""

from types import SimpleNamespace

from ariaephemeris import EventRequest, TimeInput
from ariaephemeris.events import find_events


class SyntheticCentreEngine:
    manifest = {
        "dataset_id": "synthetic-de442s",
        "sha256": "a" * 64,
        "qualification": {
            "status": "passed",
            "event_windows": [
                {
                    "kind": "conjunction",
                    "body": "jupiter",
                    "other": "sun",
                    "angle": 0,
                    "interval_tt": [2451545.0, 2451546.0],
                }
            ],
        },
    }

    def __init__(self):
        self.profiles = []

    def _coverage(self, times):
        return None

    def _physical_provenance(self, bodies):
        return {
            "jupiter": {
                "target_id": 599,
                "offset_parent_id": 5,
                "source_file": "jup349.bsp",
                "source_sha256": "b" * 64,
            }
        }

    def positions(self, request):
        self.profiles.append(request.profile)
        phase = (sum(request.time.jd) - 2451545.0) * 10 - 4
        return SimpleNamespace(
            bodies=(
                SimpleNamespace(longitude_deg=phase % 360, longitude_rate_deg_day=10),
                SimpleNamespace(longitude_deg=0, longitude_rate_deg_day=0),
            )
        )

    def positions_batch(self, request, times):
        return [self.positions(SimpleNamespace(time=t, profile=request.profile)) for t in times]


def test_centre_event_profile_propagates_and_timing_is_not_certified():
    engine = SyntheticCentreEngine()
    request = EventRequest(
        TimeInput(jd=(2451545.0, 0), scale="TT"),
        TimeInput(jd=(2451546.0, 0), scale="TT"),
        "conjunction",
        "jupiter",
        "sun",
        profile="planet-centres-v1",
    )
    events = find_events(engine, request)
    assert events
    assert set(engine.profiles) == {"planet-centres-v1"}
    assert all(e.metadata["profile"] == "planet-centres-v1" for e in events)
    assert all(e.metadata["physical_centre_sources"]["jupiter"]["target_id"] == 599 for e in events)
    assert all(not e.metadata["timing_qualified"] for e in events)
    assert all("not qualified" in e.metadata["timing_qualification_basis"] for e in events)
