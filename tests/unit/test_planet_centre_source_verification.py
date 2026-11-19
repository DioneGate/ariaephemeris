# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Integrity and fail-closed contracts for explicitly supplied centre SPK files."""

import hashlib

import pytest

from ariaephemeris import AriaError
from ariaephemeris import datasets


def test_centre_source_verification_checks_identity_size_and_hash(tmp_path, monkeypatch):
    good = tmp_path / "jup349.bsp"
    good.write_bytes(b"original SPK identity fixture")
    checksum = hashlib.sha256(good.read_bytes()).hexdigest()
    base_sha = datasets.manifest()["sha256"]
    fake_manifest = {
        "base_sha256": base_sha,
        "sources": {
            "jupiter": {
                "filename": "jup349.bsp",
                "target_id": 599,
                "centre_id": 5,
                "size_bytes": good.stat().st_size,
                "sha256": checksum,
            }
        },
    }
    monkeypatch.setattr(datasets, "centres_manifest", lambda: fake_manifest)
    checked = datasets.verify_centre_sources({"jupiter": good})
    assert checked["jupiter"]["sha256"] == checksum

    good.write_bytes(b"changed wrong identity fixture")
    with pytest.raises(AriaError, match="checksum"):
        datasets.verify_centre_sources({"jupiter": good})
    with pytest.raises(AriaError, match="missing"):
        datasets.verify_centre_sources({"jupiter": tmp_path / "missing.bsp"})
    with pytest.raises(AriaError, match="Unrecognised"):
        datasets.verify_centre_sources({"unknown": good})


def test_bundled_six_source_manifest_is_complete():
    m = datasets.centres_manifest()
    assert m["base_sha256"] == datasets.manifest()["sha256"]
    assert set(m["sources"]) == {"mars", "jupiter", "saturn", "uranus", "neptune", "pluto"}
    assert len({s["target_id"] for s in m["sources"].values()}) == 6
    assert all(len(s["sha256"]) == 64 for s in m["sources"].values())
