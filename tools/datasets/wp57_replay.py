# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Strict structured replay with explicit numerical precision for station fields.

Source bytes/hashes, vector attribution, topology, counts, flags, unknown bounds
and schemas remain exact. Derived station floating values have narrow unit-aware
replay tolerances, separate from the unchanged 30/60-second scientific gates.
TT source queries are printed to 1e-7 day (8.64 ms); solved-root replay uses that
precision and timing aggregates 10 ms. These are NOT physical error bounds.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

JD_TOLERANCE_DAYS = 1e-7
TIME_TOLERANCE_SECONDS = 0.01
RATE_TOLERANCE_DEG_TT_DAY = 1e-10
ACCELERATION_TOLERANCE_DEG_TT_DAY2 = 1e-9


def assert_replay_equal(actual: Any, frozen: Any, path: str = "") -> dict[str, float | int]:
    metrics: dict[str, float | int] = dict(
        float_checks=0, nonidentical_floats=0, max_solved_time_delta_seconds=0
    )

    validated_proxy_paths: set[str] = set()
    proxy_residuals = {
        "source_rate_spread_timing_proxy_seconds": "source_rate_step_spread_deg_tt_day",
        "aria_derivative_spread_timing_proxy_seconds": "aria_derivative_step_spread_deg_tt_day",
        "model_plus_stencil_time_proxy_seconds": "aria_minus_jpl_rate_deg_tt_day",
        "hypothetical_1e_minus4_rate_timing_proxy_seconds": None,
    }

    def visit(a: Any, b: Any, p: str) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            if set(a) != set(b):
                raise AssertionError(f"Replay schema mismatch: {p}")
            if "station_" in p and "equation_acceleration_deg_tt_day2" in a:
                for field, residual_key in proxy_residuals.items():
                    if field not in a:
                        continue
                    for record in (a, b):
                        slope = record["equation_acceleration_deg_tt_day2"]
                        residual = record[residual_key] if residual_key is not None else 0.0001
                        expected = abs(residual / slope) * 86400 if slope not in (None, 0) else None
                        if record[field] != expected:
                            raise AssertionError(
                                f"Replay proxy is inconsistent with its primitive inputs: {p}.{field}"
                            )
                    validated_proxy_paths.add(p + "." + field)
            for key in a:
                visit(a[key], b[key], p + "." + key)
            return
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                raise AssertionError(f"Replay count/topology mismatch: {p}")
            for i, (x, y) in enumerate(zip(a, b, strict=True)):
                visit(x, y, f"{p}[{i}]")
            return
        if isinstance(a, float) and isinstance(b, float):
            metrics["float_checks"] += 1
            if not math.isfinite(a) or not math.isfinite(b):
                raise AssertionError(f"Nonfinite replay value: {p}")
            if a == b:
                return
            metrics["nonidentical_floats"] += 1
            # No blanket allclose: only declared derived station quantities vary.
            tolerance = 0.0
            if "station_" in p:
                if p.endswith(".jd_tt"):
                    tolerance = JD_TOLERANCE_DAYS
                    metrics["max_solved_time_delta_seconds"] = max(
                        metrics["max_solved_time_delta_seconds"], abs(a - b) * 86400
                    )
                elif p.endswith("actual_minus_reference_seconds") or any(
                    name in p
                    for name in (
                        "aria_vs_refined_jpl_seconds.",
                        "station_timing_difference_seconds.",
                    )
                ):
                    tolerance = TIME_TOLERANCE_SECONDS
                elif any(
                    name in p
                    for name in (".source_rates_deg_tt_day.", ".aria_recomputed_rates_deg_tt_day.")
                ) or p.endswith("aria_minus_jpl_rate_deg_tt_day"):
                    tolerance = RATE_TOLERANCE_DEG_TT_DAY
                elif "step_spread_deg_tt_day" in p:
                    tolerance = 2 * RATE_TOLERANCE_DEG_TT_DAY
                elif p.endswith(("equation_slope_per_tt_day", "equation_acceleration_deg_tt_day2")):
                    tolerance = ACCELERATION_TOLERANCE_DEG_TT_DAY2
                elif p in validated_proxy_paths:
                    # Both proxies exactly reconstruct from separately checked
                    # rates/acceleration. Do not impose an unrelated time bound
                    # on a conditioning illustration.
                    return
            if abs(a - b) > tolerance:
                raise AssertionError(
                    f"Replay numerical mismatch {p}: {a!r} vs {b!r}; tolerance={tolerance}"
                )
            return
        if type(a) is not type(b) or a != b:
            raise AssertionError(f"Replay identity/flag mismatch: {p}")

    visit(actual, frozen, path)
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument(
        "--frozen", type=Path, default=Path("docs/validation/wp57-model-uncertainty.json")
    )
    args = parser.parse_args()
    print(
        json.dumps(
            assert_replay_equal(
                json.loads(args.actual.read_text()), json.loads(args.frozen.read_text())
            ),
            indent=2,
            sort_keys=True,
        )
    )
