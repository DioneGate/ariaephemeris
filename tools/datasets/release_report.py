# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Combine independently completed qualification stages, then update release metadata."""

import argparse
import json
from pathlib import Path

import erfa

parser = argparse.ArgumentParser()
parser.add_argument("--primary", type=Path, required=True)
parser.add_argument("--oppositions", type=Path, required=True)
args = parser.parse_args()
report = json.loads(args.primary.read_text())
supplement = json.loads(args.oppositions.read_text())
assert report["status"] == "passed" and report["release_qualification"], (
    "Full primary qualification must pass"
)
assert supplement["status"] == "passed", "Opposition qualification must pass"
assert report["dataset_sha256"] == supplement["dataset_sha256"]
assert report["versions"] == supplement["versions"]
report["events"].extend(supplement["events"])
report["evidence_commands"] = [
    "ruff check .",
    "ruff format --check .",
    "mypy",
    "python tools/audit.py",
    "ARIA_KERNEL=.artifacts/de442s.bsp pytest -q",
    "python tools/datasets/qualify.py --kernel .artifacts/de442s.bsp --output .artifacts/release-qualification.json",
    "python tools/datasets/qualify_oppositions.py --kernel .artifacts/de442s.bsp --output .artifacts/oppositions.json",
    "python -m build",
    "ARIA_KERNEL=.artifacts/de442s.bsp python tools/package_smoke.py",
    "python benchmarks/run.py --kernel .artifacts/de442s.bsp --output .artifacts/benchmark.json",
]
report["combined_stages"] = [
    "primary grid/off-grid/source-boundaries/charts/events",
    "supplementary whole-year oppositions",
]
root = Path(__file__).resolve().parents[2]
output = root / "docs/validation/qualification-0.1.0.json"
output.write_text(json.dumps(report, indent=2) + "\n")
manifest = json.loads((root / "data/manifests/de442s.json").read_text())
manifest["qualification"] = {
    "status": "passed",
    "report": "docs/validation/qualification-0.1.0.json",
    "scope": "Empirical geocentric apparent ICRS direction/true-of-date longitude-rate sampling, CSPICE raw states and terrestrial chart geometry; event timing only in declared windows.",
    "event_windows": [
        {
            **{k: e[k] for k in ["kind", "body", "other", "angle"]},
            "interval_tt": [
                float(sum(erfa.cal2jd(e["year"], 1, 1))),
                float(sum(erfa.cal2jd(e["year"], 1, 1))) + 365,
            ],
        }
        for e in report["events"]
    ],
}
for path in ["data/manifests/de442s.json", "src/ariaephemeris/resources/de442s.json"]:
    (root / path).write_text(json.dumps(manifest, indent=2) + "\n")
print(
    report["status"],
    len(report["events"]),
    "event windows",
    sum(e["count"] for e in report["events"]),
    "events",
)
