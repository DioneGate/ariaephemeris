# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Hermetic, synthetic tests for WP5.2 numerical comparison (NO JPL requests)."""

import importlib.util
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("compare_horizons_fixtures", TOOLS / "compare_horizons_fixtures.py")
assert SPEC is not None and SPEC.loader is not None
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def test_angular_separation_handles_ra_wrap_and_poles():
    assert c.separation_arcsec(0.0, 0.0, 0.0, 0.0) == pytest.approx(0)
    assert c.separation_arcsec(359.9999, 0, 0.0001, 0) == pytest.approx(0.72, abs=1e-7)
    assert c.circular_delta_deg(359.9999, 0.0001) == pytest.approx(-0.0002)
    assert c.separation_arcsec(30, 90, 270, 90) == pytest.approx(0.0, abs=1e-9)
    assert c.separation_arcsec(0, 0, 180, 0) == pytest.approx(648000)


def test_vector_units_and_statistics_are_explicit():
    magnitude, components = c.vector_difference([1.0, 2.0, 3.0], [0.0, 2.0, 2.5])
    assert components == [1.0, 0.0, 0.5]
    assert magnitude == pytest.approx(math.sqrt(1.25))
    speed, _ = c.vector_difference([1.001, 0, 0], [1.0, 0, 0], scale=1000)
    assert speed == pytest.approx(1.0)
    stats = c._stats([0, 1, 2, 3])
    assert stats["count"] == 4
    assert stats["max"] == 3
    assert stats["rms"] == pytest.approx(math.sqrt(3.5))
    assert stats["p95"] == pytest.approx(2.85)
    with pytest.raises(ValueError, match="finite"):
        c.vector_difference([1, float("nan"), 0], [1, 2, 3])
    with pytest.raises(ValueError, match="nonnegative"):
        c._stats([-1])


def test_model_labels_alone_never_certify_source_match():
    manifest = {
        "filename": "mar099.bsp", "sha256": "b" * 64, "target_id": 499
    }
    raw = {
        "source_header": {
            "target": "Target body name: Mars (499) {source: mar099}",
            "centre": "Center body name: Earth (399) {source: DE441}",
            "source_solution_labels": "DE441, mar099",
        }
    }
    result = c.model_provenance(raw, manifest)
    assert result["target_labels_identical"]
    assert not result["observer_labels_identical"]
    assert not result["matched_physical_model_demonstrated"]
    assert result["reconciliation_status"] == "unreconciled-model-and-correction-differences"
    with pytest.raises(ValueError, match="source identity"):
        c.source_label("Earth (399)")


class FakeEngine:
    def __init__(self):
        self.geometric_scales = []
        self.apparent_frames = []

    def raw_state(self, body, time, *, profile="reference"):
        self.geometric_scales.append((time.scale, profile, body))
        return {
            "target_id": 399 if body == "earth" else c.centres_manifest()["sources"][body]["target_id"],
            "time": {"jd_tdb": list(time.jd)},
            "position_km": [0, 0, 0] if body == "earth" else [1, 2, 3],
            "velocity_km_day": [0, 0, 0] if body == "earth" else [86400, 0, 0],
        }

    def positions(self, request):
        self.apparent_frames.append((request.frame, request.time.scale, request.profile))
        return SimpleNamespace(
            metadata={"frame": request.frame, "profile": request.profile},
            bodies=(SimpleNamespace(
                target_id=c.centres_manifest()["sources"][request.bodies[0]]["target_id"],
                longitude_deg=359.9999,
                latitude_deg=0.0,
                right_ascension_deg=180.0,  # wrong frame deliberately
            ),),
        )


def fake_source_manifest():
    m = c.centres_manifest()
    return m


def fake_fixtures():
    manifest = fake_source_manifest()
    cases = []
    queries = []
    for body in c.REQUIRED_BODIES:
        target_id = manifest["sources"][body]["target_id"]
        for kind in ("geometric", "apparent"):
            queries.append({
                "body": body,
                "kind": kind,
                "source_header": {
                    "target": f"Target body name: {body} ({target_id}) {{source: {manifest['sources'][body]['filename'].removesuffix('.bsp')}}}",
                    "centre": "Center body name: Earth (399) {source: DE441}",
                    "source_solution_labels": "DE441, test",
                }
            })
            for k in range(25):
                ref = (
                    {
                        "jd_tdb": 2451545.0 + k,
                        "position_km": [1, 2, 3],
                        "velocity_km_s": [1, 0, 0],
                    }
                    if kind == "geometric"
                    else {
                        "jd_tt": 2451545.0 + k,
                        "inertial_apparent_ra_deg": 0.0001,
                        "inertial_apparent_dec_deg": 0.0,
                    }
                )
                cases.append({
                    "id": f"{body}-{kind}-{k}",
                    "kind": kind,
                    "body": body,
                    "target_id": target_id,
                    "source_raw_file": f"raw/{body}-{kind}.txt",
                    "reference": ref,
                })
    return {"dataset_id": "synthetic-reference", "raw_queries": queries, "cases": cases}


def test_all_300_results_are_computed_not_artificially_qualified():
    engine = FakeEngine()
    out = c.evaluate(engine, fake_fixtures(), fake_source_manifest())
    assert len(out["rows"]) == 300
    assert out["sample_count"] == 300
    assert out["physically_qualified_for_commercial_release"] is False
    assert out["independent_chart_accuracy_pass"] is None
    assert out["scientific_status"] == "MEASURED_WITH_UNRECONCILED_SOURCE_MODELS"
    assert out["per_body"]["mars"]["geometric_position_km"]["max"] == 0
    assert out["per_body"]["mars"]["apparent_direction_arcsec"]["max"] == pytest.approx(0.72)
    assert all(scale == "TDB" for scale, _, _ in engine.geometric_scales)
    assert all(frame == "icrs" and scale == "TT" and profile == "planet-centres-v1"
               for frame, scale, profile in engine.apparent_frames)
    assert all(not row["provenance"]["matched_physical_model_demonstrated"]
               for row in out["rows"])


def test_missing_reference_row_is_not_accepted():
    f = fake_fixtures()
    f["cases"].pop()
    with pytest.raises(ValueError, match="300 required"):
        c.evaluate(FakeEngine(), f, fake_source_manifest())


def test_incorrect_physical_target_is_not_accepted():
    f = fake_fixtures()
    f["cases"][0]["target_id"] = 5
    with pytest.raises(ValueError, match="physical-centre"):
        c.evaluate(FakeEngine(), f, fake_source_manifest())
