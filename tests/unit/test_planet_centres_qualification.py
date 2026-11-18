# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Kernel-free numerical source contract tests for RM-001/002 WP3."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(SOURCE))
SPEC = importlib.util.spec_from_file_location(
    "qualify_planet_centres", SOURCE / "qualify_planet_centres.py"
)
assert SPEC is not None and SPEC.loader is not None
qualify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qualify)


def test_selection_uses_supported_segment_and_last_priority():
    segments = [
        {
            "segment_index": 2,
            "start_jd_tdb": 10,
            "end_jd_tdb": 20,
            "supported_by_current_reader": True,
        },
        {
            "segment_index": 9,
            "start_jd_tdb": 10,
            "end_jd_tdb": 20,
            "supported_by_current_reader": True,
        },
        {
            "segment_index": 10,
            "start_jd_tdb": 10,
            "end_jd_tdb": 20,
            "supported_by_current_reader": False,
        },
    ]
    assert qualify.choose_segment(segments, 15)["segment_index"] == 9
    with pytest.raises(ValueError, match="No supported direct"):
        qualify.choose_segment(segments, 21)


def test_samples_include_window_limits_and_both_sides_of_seam():
    rows = [{"start_jd_tdb": 15.0}, {"start_jd_tdb": 18.0}]
    epochs = qualify.sample_epochs(rows, (10.0, 20.0))
    assert epochs[0] == 10.0
    assert epochs[-1] == 20.0
    assert 15.0 - 1 / 24 in epochs
    assert 15.0 + 1 / 24 in epochs
    assert len(epochs) == len(set(epochs))


def test_many_seams_are_bounded():
    rows = [{"start_jd_tdb": float(j)} for j in range(11, 80)]
    epochs = qualify.sample_epochs(rows, (10.0, 100.0))
    assert len(epochs) <= 10


def test_manifest_must_match_naif_target_identity(tmp_path):
    path = tmp_path / "manifest.json"
    record = {
        "schema_version": 1,
        "sources": {
            "mars": {
                "target_id": 4,
                "centre_id": 499,
                "published_md5": "0" * 32,
            }
        },
    }
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="manifest target/parent"):
        qualify.load_manifest(path, "mars")
    record["sources"]["mars"].update({"target_id": 499, "centre_id": 4})
    path.write_text(json.dumps(record))
    assert qualify.load_manifest(path, "mars")["target_id"] == 499


def test_unpinned_candidate_is_explicit(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": {
                    "pluto": {
                        "target_id": 999,
                        "centre_id": 9,
                        "published_md5": "a" * 32,
                        "observed_sha256_pinned": None,
                    }
                },
            }
        )
    )
    assert qualify.load_manifest(path, "pluto")["observed_sha256_pinned"] is None
