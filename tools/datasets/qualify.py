# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Independent, explicitly invoked real-kernel qualification. Missing data is a failure."""

import argparse
import importlib.metadata
import json
import platform
import sys
import time
from pathlib import Path

import erfa
import numpy as np
import spiceypy as spice
from scipy.optimize import brentq
from skyfield.api import load, load_file
from skyfield.framelib import ecliptic_frame

from ariaephemeris import Ephemeris, EventRequest, Observer, PositionRequest, TimeInput
from ariaephemeris.models import BODY_IDS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference.skyfield_match import apparent as matched_apparent


def diff(a, b):
    return (np.asarray(a) - np.asarray(b) + 180) % 360 - 180


def direction_error(a, b):
    a = a / np.linalg.norm(a, axis=-1)[:, None]
    b = b / np.linalg.norm(b, axis=-1)[:, None]
    return (
        np.degrees(np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), np.sum(a * b, axis=-1)))
        * 3600
    )


def geometry_angles(latitude, longitude, t):
    """Independent vector-plane intersection, not the Aria atan2 house equations."""
    theta = float(t.gast) / 12 * np.pi + np.radians(longitude)
    phi = np.radians(latitude)
    eps = float(t._mean_obliquity_radians + t._nutation_angles_radians[1])
    normal = np.array([0, -np.sin(eps), np.cos(eps)])
    zenith = np.array([np.cos(phi) * np.cos(theta), np.cos(phi) * np.sin(theta), np.sin(phi)])
    east = np.array([-np.sin(theta), np.cos(theta), 0])
    asc = np.cross(zenith, normal)
    asc /= np.linalg.norm(asc)
    if asc @ east < 0:
        asc = -asc
    mc = np.cross(east, normal)
    mc /= np.linalg.norm(mc)
    if mc @ np.array([np.cos(theta), np.sin(theta), 0]) < 0:
        mc = -mc
    # Project equatorial vectors onto the ecliptic basis.
    return [
        np.degrees(np.arctan2(v[1] * np.cos(eps) + v[2] * np.sin(eps), v[0])) % 360
        for v in (asc, mc)
    ]


def run(kernel, output, quick=False):
    started = time.perf_counter()
    rng = np.random.default_rng(20261010)
    ts = load.timescale(builtin=True)
    sk = load_file(str(kernel))
    spice.furnsh(str(kernel))
    report = {
        "status": "running",
        "sampling_seed": 20261010,
        "scope": "quick diagnostic" if quick else "empirical reference qualification",
        "release_qualification": not quick,
        "runtime": platform.python_version(),
        "versions": {
            x: importlib.metadata.version(x)
            for x in ["numpy", "jplephem", "pyerfa", "skyfield", "spiceypy", "scipy"]
        },
        "per_body": {},
        "gates": {},
        "reference_convention": "Skyfield independent pipeline with separately implemented finite-source deflection and Aria-matched limiter",
        "deflection_limits": {"Sun": 1e-6, "Jupiter": 3e-9, "Saturn": 3e-10},
    }
    with Ephemeris(kernel) as engine:
        report["dataset_sha256"] = engine.manifest["sha256"]
        lo, hi = engine.manifest["operating_interval_tt"]
        epochs = np.concatenate(
            [
                np.arange(lo, hi, 32.0 if not quick else 365.0),
                rng.uniform(lo, hi - 0.01, 2048 if not quick else 50),
                [lo, hi - 1e-6],
            ]
        )
        # Off-grid epochs close to real polynomial boundaries, within operating coverage.
        boundaries = []
        for seg in engine.kernel._spk.segments:
            initial, length, _ = seg.load_array()
            interval = length
            first = initial
            bb = np.arange(first, seg.end_jd, interval)
            bb = bb[(bb > lo + 0.01) & (bb < hi - 0.01)][:: 100 if not quick else 1000]
            boundaries.extend(bb - 1e-6)
            boundaries.extend(bb + 1e-6)
        epochs = np.unique(np.concatenate([epochs, boundaries]))
        report["operating_interval_tt"] = [lo, hi]
        report["epoch_count"] = len(epochs)
        print("Epochs:", len(epochs), flush=True)
        metrics = {
            b: {
                "raw_position_m": 0.0,
                "raw_velocity_mm_s": 0.0,
                "direction_arcsec": 0.0,
                "longitude_rate_deg_day": 0.0,
            }
            for b in BODY_IDS
            if b != "earth"
        }
        unmatched = {b: 0.0 for b in metrics}
        errors = {b: {k: [] for k in m} for b, m in metrics.items()}
        request = PositionRequest(TimeInput(jd=(lo, 0), scale="TT"))
        for off in range(0, len(epochs), 128):
            jj = epochs[off : off + 128]
            inputs = [TimeInput(jd=(float(j), 0), scale="TT") for j in jj]
            positions = engine.positions_batch(request, inputs)
            times = ts.tt_jd(jj)
            for index, body in enumerate(metrics):
                tid = BODY_IDS[body]
                m = metrics[body]
                # Separate CSPICE evaluation at explicitly identical TDB epochs.
                rawp, rawv = engine.kernel.state(tid, jj)
                reference = np.array(
                    [spice.spkgeo(tid, float((j - 2451545) * 86400), "J2000", 0)[0] for j in jj]
                )
                m["raw_position_m"] = max(
                    m["raw_position_m"],
                    float(np.max(np.linalg.norm(rawp.T - reference[:, :3], axis=1)) * 1000),
                )
                m["raw_velocity_mm_s"] = max(
                    m["raw_velocity_mm_s"],
                    float(np.max(np.linalg.norm(rawv.T / 86400 - reference[:, 3:], axis=1)) * 1e6),
                )
                astro = sk["earth"].at(times).observe(sk[tid])
                apparent = matched_apparent(astro)
                vv = np.array([p.bodies[index].vector_icrs_au for p in positions])
                unmatched[body] = max(
                    unmatched[body], float(np.max(direction_error(vv, astro.apparent().xyz.au.T)))
                )
                m["direction_arcsec"] = max(
                    m["direction_arcsec"], float(np.max(direction_error(vv, apparent.xyz.au.T)))
                )
                # Finite differencing of an independent complete position pipeline.
                h = 0.002
                longs = []
                centre = apparent.frame_latlon(ecliptic_frame)[1].degrees
                for shift in [-2 * h, -h, h, 2 * h]:
                    ll = (
                        matched_apparent(sk["earth"].at(ts.tt_jd(jj, shift)).observe(sk[tid]))
                        .frame_latlon(ecliptic_frame)[1]
                        .degrees
                    )
                    longs.append(diff(ll, centre))
                rates = (longs[0] - 8 * longs[1] + 8 * longs[2] - longs[3]) / (12 * h)
                aria = np.array([p.bodies[index].longitude_rate_deg_day for p in positions])
                m["longitude_rate_deg_day"] = max(
                    m["longitude_rate_deg_day"], float(np.max(np.abs(aria - rates)))
                )
                errors[body]["raw_position_m"].extend(
                    (np.linalg.norm(rawp.T - reference[:, :3], axis=1) * 1000).tolist()
                )
                errors[body]["raw_velocity_mm_s"].extend(
                    (np.linalg.norm(rawv.T / 86400 - reference[:, 3:], axis=1) * 1e6).tolist()
                )
                errors[body]["direction_arcsec"].extend(
                    direction_error(vv, apparent.xyz.au.T).tolist()
                )
                errors[body]["longitude_rate_deg_day"].extend(np.abs(aria - rates).tolist())
            if off % 1024 == 0:
                print("Validated", off + len(jj), "epochs", flush=True)
        report["per_body"] = metrics
        report["unmatched_skyfield_direction_max_arcsec"] = unmatched
        report["distributions"] = {
            b: {
                k: {
                    "rms": float(np.sqrt(np.mean(np.square(v)))),
                    "p95": float(np.percentile(v, 95)),
                }
                for k, v in es.items()
            }
            for b, es in errors.items()
        }
        # Independent geometry at both hemispheres and high but non-degenerate latitudes.
        angle_max = 0
        for jd in epochs[:: max(1, len(epochs) // 40)]:
            tt = ts.tt_jd(jd)
            tt.ut1_fraction = tt.tt_fraction - 64 / 86400
            for lat, lon in [(0, 0), (51.5, -0.1), (-33.9, 151.2), (70, 25), (-70, -25)]:
                ti = TimeInput(jd=(float(jd), 0), scale="TT", delta_t_seconds=64)
                chart = engine.chart(PositionRequest(ti, bodies=("sun",)), Observer(lat, lon))
                aa = geometry_angles(lat, lon, tt)
                angle_max = max(
                    angle_max,
                    float(
                        np.max(np.abs(diff([chart.angles_deg["ASC"], chart.angles_deg["MC"]], aa)))
                        * 3600
                    ),
                )
        report["angles_max_arcsec"] = angle_max
        report["events"] = []
        cases = [
            ("ingress", "moon", None, 0),
            ("ingress", "sun", None, 0),
            ("conjunction", "moon", "sun", 0),
            ("aspect", "mercury", "sun", 15),
            ("station", "mercury", None, 0),
            ("station", "venus", None, 0),
            ("station", "mars", None, 0),
            ("station", "jupiter", None, 0),
            ("station", "saturn", None, 0),
            ("station", "uranus", None, 0),
            ("station", "neptune", None, 0),
            ("station", "pluto", None, 0),
        ]
        for year in [2000] if quick else [1900, 2000, 2099]:
            start = float(sum(erfa.cal2jd(year, 1, 1)))
            duration = 90 if quick else 365
            for kind, body, other, angle in cases:
                if quick and body not in ("moon", "sun", "mercury"):
                    continue
                end = start + duration
                req = EventRequest(
                    TimeInput(jd=(start, 0), scale="TT"),
                    TimeInput(jd=(end, 0), scale="TT"),
                    kind,
                    body,
                    other,
                    angle,
                )
                aria = engine.find_events(req)

                def phase(j):
                    ll = (
                        matched_apparent(sk["earth"].at(ts.tt_jd(j)).observe(sk[BODY_IDS[body]]))
                        .frame_latlon(ecliptic_frame)[1]
                        .degrees
                    )
                    if other:
                        rr = (
                            matched_apparent(
                                sk["earth"].at(ts.tt_jd(j)).observe(sk[BODY_IDS[other]])
                            )
                            .frame_latlon(ecliptic_frame)[1]
                            .degrees
                        )
                        ll = diff(ll, rr)
                    return ll

                def speed(j):
                    h = 0.002
                    return diff(phase(np.asarray(j) + h), phase(np.asarray(j) - h)) / (2 * h)

                # Independent scan is 8x denser, refined by SciPy Brent's method.
                grid = np.linspace(start, end, int(duration * 128) + 1)
                rr = (
                    speed(grid)
                    if kind == "station"
                    else np.degrees(np.unwrap(np.radians(phase(grid))))
                )
                refs = []
                if kind == "station":
                    spans = np.where(rr[:-1] * rr[1:] < 0)[0]
                    for i in spans:
                        refs.append(brentq(speed, grid[i], grid[i + 1], xtol=1e-9))
                else:
                    if kind == "ingress":
                        goals = np.arange(np.ceil(rr.min() / 30) * 30, rr.max() + 1e-8, 30)
                    else:
                        a = 0 if kind == "conjunction" else angle
                        bases = [a] if a in (0, 180) else [a, 360 - a]
                        goals = [
                            g + 360 * k
                            for g in bases
                            for k in range(
                                int(np.ceil((rr.min() - g) / 360)),
                                int(np.floor((rr.max() - g) / 360)) + 1,
                            )
                        ]
                    for goal in goals:
                        spans = np.where((rr[:-1] - goal) * (rr[1:] - goal) <= 0)[0]
                        for i in spans:
                            refs.append(
                                brentq(
                                    lambda j, g=goal: float(diff(phase(j), g)),
                                    grid[i],
                                    grid[i + 1],
                                    xtol=1e-9,
                                )
                            )
                refs = sorted(set(refs))
                if len(aria) != len(refs):
                    raise RuntimeError(
                        f"Completeness mismatch {year} {kind} {body}: {len(aria)} != {len(refs)}"
                    )
                timing = max(
                    [abs(sum(a.jd_tt) - b) * 86400 for a, b in zip(aria, refs, strict=True)],
                    default=0,
                )
                report["events"].append(
                    {
                        "year": year,
                        "kind": kind,
                        "body": body,
                        "other": other,
                        "angle": angle,
                        "count": len(refs),
                        "max_timing_error_seconds": timing,
                        "reference_scan_days": 1 / 128,
                        "station_seed_policy": "full matched apparent rate"
                        if kind == "station"
                        else None,
                    }
                )
                print(
                    "Events",
                    year,
                    kind,
                    body,
                    len(refs),
                    "error seconds",
                    round(timing, 5),
                    flush=True,
                )
        report["gates"] = {
            "raw_position": max(x["raw_position_m"] for x in metrics.values()) <= 1,
            "raw_velocity": max(x["raw_velocity_mm_s"] for x in metrics.values()) <= 1,
            "apparent_direction": max(x["direction_arcsec"] for x in metrics.values()) <= 1,
            "longitude_rate": max(x["longitude_rate_deg_day"] for x in metrics.values()) <= 0.0001,
            "angles_houses": angle_max <= 1,
            "event_timing": max(x["max_timing_error_seconds"] for x in report["events"]) <= 10,
            "event_completeness": True,
        }
        report["status"] = "passed" if all(report["gates"].values()) else "failed"
        report["elapsed_seconds"] = time.perf_counter() - started
        report["limitations"] = [
            "Empirical samples do not establish a continuous mathematical bound.",
            "Absolute Earth rotation depends on supplied time inputs.",
            "Planetary barycentres are explicitly exposed; minor bodies/compact packs are not implemented.",
            "Event completeness qualified on reported year/type windows, not every possible interval.",
            "Unmodified Skyfield has a different near-alignment deflection convention; those differences are recorded separately, not accepted as convention-matched error.",
        ]
    spice.kclear()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(report["status"], report["gates"], flush=True)
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--kernel", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--quick", action="store_true")
    a = p.parse_args()
    try:
        run(a.kernel, a.output, a.quick)
    except Exception as exc:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(
            json.dumps(
                {"status": "failed", "release_qualification": False, "error": str(exc)}, indent=2
            )
            + "\n"
        )
        raise
