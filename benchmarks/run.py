# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Reproducible baseline; targets are reported separately from measurements."""

import argparse
import importlib.metadata
import json
import platform
import resource
import time
from pathlib import Path

import numpy as np

from ariaephemeris import Ephemeris, PositionRequest, TimeInput


def run(kernel, output, count=10000):
    started = time.perf_counter()
    engine = Ephemeris(kernel)
    request = PositionRequest(TimeInput(jd=(2451545, 0), scale="TT"))
    engine.positions(request)
    cold = time.perf_counter() - started
    samples = []
    for _ in range(20):
        t = time.perf_counter()
        engine.positions(request)
        samples.append(time.perf_counter() - t)
    times = [
        TimeInput(jd=(float(j), 0), scale="TT") for j in np.linspace(2451545, 2451545 + 365, count)
    ]
    t = time.perf_counter()
    # Chunking avoids retaining a hundred thousand Python body records at once.
    for off in range(0, count, 512):
        engine.positions_batch(request, times[off : off + 512])
    batch = time.perf_counter() - t
    cpu = platform.processor()
    if Path("/proc/cpuinfo").exists():
        cpu = next(
            (
                s.split(":", 1)[1].strip()
                for s in Path("/proc/cpuinfo").read_text().splitlines()
                if s.startswith("model name")
            ),
            cpu,
        )
    report = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": cpu,
        "dataset_sha256": engine.manifest["sha256"],
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pyerfa", "jplephem"]},
        "cold_open_and_first_positions_seconds": cold,
        "cold_policy": "new engine; OS page cache not purged",
        "warm_positions_median_seconds": float(np.median(samples)),
        "warm_positions_max_seconds": max(samples),
        "batch_epochs": count,
        "bodies_per_epoch": 10,
        "batch_seconds": batch,
        "chunk_size": 512,
        "process_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "provisional_warm_latency_target_met": bool(np.median(samples) < 0.1),
        "provisional_10000_epoch_2s_target_met": bool(count == 10000 and batch < 2),
    }
    engine.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kernel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.kernel, args.output)
