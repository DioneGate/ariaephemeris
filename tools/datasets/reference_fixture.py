# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Generate small reference fixtures using independent evaluators only."""

import argparse
import importlib.metadata
import json
from pathlib import Path

import spiceypy as spice
from skyfield.api import load, load_file

from ariaephemeris.datasets import verify
from ariaephemeris.models import BODY_IDS

parser = argparse.ArgumentParser()
parser.add_argument("--kernel", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
manifest = verify(args.kernel)
ts = load.timescale(builtin=True)
sk = load_file(str(args.kernel))
spice.furnsh(str(args.kernel))
report = {
    "kernel_sha256": manifest["sha256"],
    "generator": "tools/datasets/reference_fixture.py",
    "evaluators": {p: importlib.metadata.version(p) for p in ["spiceypy", "skyfield"]},
    "raw_frame": "J2000",
    "raw_origin": 0,
    "raw_units": ["km", "km/s"],
    "apparent_frame": "ICRS",
    "apparent_origin": 399,
    "apparent_corrections": "Skyfield light-time/Sun-Jupiter-Saturn deflection/aberration",
    "cases": [],
}
try:
    for jd in [2415020.5, 2451545.123456789, 2462502.75, 2488434.49]:
        t = ts.tt_jd(jd)
        et = ((t.whole - 2451545) + t.tdb_fraction) * 86400
        for body, target in BODY_IDS.items():
            state = spice.spkgeo(target, float(et), "J2000", 0)[0]
            row = {
                "body": body,
                "target_id": target,
                "jd_tt": [jd, 0.0],
                "jd_tdb": [float(t.whole), float(t.tdb_fraction)],
                "raw_state": state.tolist(),
            }
            if body != "earth":
                row["apparent_vector_au"] = (
                    sk["earth"].at(t).observe(sk[target]).apparent().xyz.au.tolist()
                )
            report["cases"].append(row)
finally:
    spice.kclear()
    sk.close()
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(len(report["cases"]), "reference cases")
