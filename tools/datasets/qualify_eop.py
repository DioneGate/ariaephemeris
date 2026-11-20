# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Explicit pinned-source and independent Skyfield interpolation/geometry checks."""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from qualify import diff, geometry_angles
from skyfield.api import wgs84
from skyfield.data.iers import (
    build_timescale_arrays,
    install_polar_motion_table,
    parse_x_y_dut1_from_finals_all,
)
from skyfield.timelib import Timescale

from ariaephemeris import Ephemeris, Observer, PositionRequest, TimeInput
from ariaephemeris.frames import observer_state
from ariaephemeris.time import resolve
from ariaephemeris.time.eop import EarthOrientation, verify


def run(kernel: Path, source: Path, output: Path) -> dict:
    manifest, rows = verify(source)
    with source.open("rb") as f:
        independent = parse_x_y_dut1_from_finals_all(f)
    ours = np.array([[r.mjd, r.xp, r.yp, r.dut1] for r in rows])
    theirs = np.column_stack(
        [independent[k] for k in ["utc_mjd", "x_arcseconds", "y_arcseconds", "dut1"]]
    )
    parser_matches = ours.shape == theirs.shape and np.array_equal(ours, theirs)
    if not parser_matches:
        raise AssertionError("Independent source parsers disagree")
    daily_tt, delta_t, leaps, offsets = build_timescale_arrays(
        independent["utc_mjd"], independent["dut1"]
    )
    ts = Timescale((daily_tt, delta_t), leaps, offsets)
    install_polar_motion_table(ts, independent)
    # Deterministic off-grid dates throughout actual observed coverage, plus exact leap neighbours.
    dates = [
        datetime(1973, 1, 2, tzinfo=timezone.utc)
        + timedelta(days=float(m - 41684), seconds=43111.25)
        for m in np.linspace(41685, manifest["first_prediction_mjd_utc"] - 2, 80)
    ]
    dates += [
        datetime(2016, 12, 31, 12, tzinfo=timezone.utc),
        datetime(2017, 1, 1, 12, tzinfo=timezone.utc),
    ]
    maxima = {
        "dut1_seconds": 0.0,
        "polar_motion_arcsec": 0.0,
        "angles_arcsec": 0.0,
        "observer_position_m": 0.0,
        "observer_velocity_m_s": 0.0,
    }
    observed = EarthOrientation(source)
    with Ephemeris(kernel, eop_path=source) as engine:
        for stamp in dates:
            ti = TimeInput(stamp.isoformat())
            rt = resolve(ti)
            data = observed.lookup(rt)
            sky = ts.from_datetime(stamp)
            _, x, y = sky.polar_motion_angles()
            maxima["dut1_seconds"] = max(
                maxima["dut1_seconds"], abs(data["dut1_seconds"] - float(sky.dut1))
            )
            maxima["polar_motion_arcsec"] = max(
                maxima["polar_motion_arcsec"],
                abs(data["xp_arcsec"] - x),
                abs(data["yp_arcsec"] - y),
            )
            for lat, lon in [(51.5, 0), (-33.9, 151.2), (70, 25)]:
                observer = Observer(lat, lon)
                chart = engine.chart(PositionRequest(ti, bodies=("sun",)), observer)
                angles = [chart.angles_deg["ASC"], chart.angles_deg["MC"]]
                maxima["angles_arcsec"] = max(
                    maxima["angles_arcsec"],
                    float(np.max(np.abs(diff(angles, geometry_angles(lat, lon, sky))))) * 3600,
                )
                t = observed.apply(rt, dut1=True, xp=True, yp=True)
                ap, av, _ = observer_state(observer, t, True)
                reference = wgs84.latlon(lat, lon).at(sky)
                maxima["observer_position_m"] = max(
                    maxima["observer_position_m"],
                    float(np.linalg.norm(ap - reference.position.km)) * 1000,
                )
                maxima["observer_velocity_m_s"] = max(
                    maxima["observer_velocity_m_s"],
                    float(np.linalg.norm(av - reference.velocity.km_per_s * 86400)) * 1000 / 86400,
                )
        source_hash = engine.manifest["sha256"]
    limits = {
        "dut1_seconds": 1e-7,
        "polar_motion_arcsec": 1e-8,
        "angles_arcsec": 0.01,
        "observer_position_m": 0.1,
        "observer_velocity_m_s": 0.01,
    }
    gates = {k: bool(maxima[k] <= v) for k, v in limits.items()}
    report = {
        "schema_version": 1,
        "status": "passed" if all(gates.values()) else "failed",
        "eop_sha256": manifest["sha256"],
        "dataset_sha256": source_hash,
        "independent_parser_records": len(rows),
        "independent_parser_exact_match": parser_matches,
        "observed_off_grid_instants": len(dates),
        "observer_cases": len(dates) * 3,
        "maxima": maxima,
        "diagnostic_limits": limits,
        "gates": gates,
        "reference": "Skyfield 1.55 independent finals parser, TT-based delta-T/polar interpolation, vector-plane chart angles and WGS84 observer state",
        "limitations": [
            "Shared original IERS source; finite sample, not absolute physical accuracy",
            "Diagnostic limits measure implementation/convention agreement, not approved commercial tolerances",
            "Skyfield observer velocity omits some small EOP derivative terms; residual retained",
            "Rapid Bulletin A values are provisional; formal errors are not absolute bounds",
            "Celestial pole dX/dY corrections are not applied in this stage",
            "ASC/MC retain v1 GST/geodetic geometry without polar-motion corrections; reference matches that convention",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kernel", type=Path, required=True)
    p.add_argument("--eop", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    r = run(args.kernel, args.eop, args.output)
    print(r["status"], r["maxima"])
    raise SystemExit(0 if r["status"] == "passed" else 1)
