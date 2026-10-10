# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Check recorded legal/provenance inputs rather than inferring permissions."""

import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
tracked = None
if (root / ".git").exists():
    tracked = set(subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0"))
manifest = json.loads((root / "data/manifests/de442s.json").read_text())
assert manifest == json.loads((root / "src/ariaephemeris/resources/de442s.json").read_text())
assert (
    hashlib.sha256((root / "LICENSE").read_bytes()).hexdigest()
    == "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
)
assert (
    hashlib.sha256((root / "docs/licenses/NAIF-rules.html").read_bytes()).hexdigest()
    == manifest["source_terms_sha256"]
)
for item in json.loads((root / "docs/licenses/dependency-inventory.json").read_text()):
    assert item["notices"], item["name"]
    for notice in item["notices"]:
        if tracked is not None:
            assert notice in tracked, f"Notice is absent from Git: {notice}"
        assert (root / notice).is_file(), notice
        assert (
            hashlib.sha256((root / notice).read_bytes()).hexdigest()
            == item["notice_sha256"][notice]
        )
for path in (root / "src").rglob("*.py"):
    assert "SPDX-License-Identifier: Apache-2.0" in path.read_text(), path
print("Licence text, notice inventory, SPDX and source-term hashes verified.")
