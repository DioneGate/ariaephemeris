# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Supplementary independent opposition-completeness check for release evidence."""

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path

import erfa
import numpy as np
from scipy.optimize import brentq
from skyfield.api import load, load_file

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference.skyfield_match import apparent
from skyfield.framelib import ecliptic_frame

from ariaephemeris import Ephemeris, EventRequest, TimeInput


def run(kernel, output):
    ts = load.timescale(builtin=True)
    sk = load_file(str(kernel))
    cases = []
    with Ephemeris(kernel) as engine:
        for year in [1900, 2000, 2099]:
            start = float(sum(erfa.cal2jd(year, 1, 1)))
            end = start + 365

            def phase(j):
                observer = sk["earth"].at(ts.tt_jd(j))
                moon = apparent(observer.observe(sk[301])).frame_latlon(ecliptic_frame)[1].degrees
                sun = apparent(observer.observe(sk[10])).frame_latlon(ecliptic_frame)[1].degrees
                return (moon - sun) % 360

            grid = np.linspace(start, end, 365 * 128 + 1)
            residual = (phase(grid) - 180 + 180) % 360 - 180
            refs = []
            for i in np.where(
                (residual[:-1] * residual[1:] <= 0) & (np.abs(np.diff(residual)) < 180)
            )[0]:
                refs.append(
                    brentq(
                        lambda j: float((phase(j) - 180 + 180) % 360 - 180),
                        grid[i],
                        grid[i + 1],
                        xtol=1e-9,
                    )
                )
            events = engine.find_events(
                EventRequest(
                    TimeInput(jd=(start, 0), scale="TT"),
                    TimeInput(jd=(end, 0), scale="TT"),
                    "opposition",
                    "moon",
                    "sun",
                )
            )
            assert len(events) == len(refs), (year, len(events), len(refs))
            error = max(abs(sum(a.jd_tt) - b) * 86400 for a, b in zip(events, refs, strict=True))
            assert error <= 10, error
            cases.append(
                {
                    "year": year,
                    "kind": "opposition",
                    "body": "moon",
                    "other": "sun",
                    "angle": 180,
                    "count": len(refs),
                    "max_timing_error_seconds": error,
                    "reference_scan_days": 1 / 128,
                    "station_seed_policy": None,
                }
            )
            print(year, len(refs), error, flush=True)
        report = {
            "status": "passed",
            "dataset_sha256": engine.manifest["sha256"],
            "events": cases,
            "reference_convention": "Skyfield with independently implemented matched deflection limiter",
            "versions": {
                x: importlib.metadata.version(x)
                for x in ["numpy", "jplephem", "pyerfa", "skyfield", "spiceypy", "scipy"]
            },
        }
    sk.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        run(args.kernel, args.output)
    except Exception as exc:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"status": "failed", "error": str(exc)}, indent=2) + "\n")
        raise
