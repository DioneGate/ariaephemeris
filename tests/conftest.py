# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import os
from pathlib import Path

import pytest

from ariaephemeris import Ephemeris


@pytest.fixture(scope="session")
def engine():
    path = os.environ.get("ARIA_KERNEL")
    if not path:
        pytest.skip("Set ARIA_KERNEL to run real-kernel tests; this is NOT qualification")
    with Ephemeris(Path(path)) as e:
        yield e


@pytest.fixture
def eop_excerpt(tmp_path, monkeypatch):
    """Pin unchanged official excerpt bytes for hermetic unit/integration tests only."""
    import hashlib
    import json

    from ariaephemeris.time import eop

    root = Path(__file__).resolve().parents[1]
    data = (root / "data/fixtures/iers/finals2000A-excerpt.txt").read_bytes()
    provenance = json.loads((root / "data/fixtures/iers/provenance.json").read_text())
    assert hashlib.sha256(data).hexdigest() == provenance["excerpt_sha256"]
    m = eop.manifest()
    assert m["sha256"] == provenance["source_sha256"]
    m.update(size_bytes=len(data), sha256=provenance["excerpt_sha256"])
    monkeypatch.setattr(eop, "manifest", lambda: dict(m))
    path = tmp_path / "finals-excerpt.all"
    path.write_bytes(data)
    return path
