# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Verify immutable JPL fine-time roots and independently observed sign brackets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_horizons_fixtures import TARGETS, parse_table, query, sha256, source_header
from acquire_wp55_root_brackets import OFFSETS_SECONDS, sample_days
from compare_wp54_tropical import reference_rate, true_tropical_from_icrf
from verify_wp55_events import validate as validate_wp55
from wp55_event_math import BODY_ORDER, signed_angle, station_stencil


def verify(root: Path, original: Path, wp54: Path, comparison: Path) -> dict[str, Any]:
    if validate_wp55(original, wp54)["verified_events"] != 22:
        raise ValueError("Original Horizons 22-event sample failed source verification")
    measured_bytes = comparison.read_bytes()
    measured = json.loads(measured_bytes)
    manifest = json.loads(
        (root / "wp55-jpl-fine-root-brackets-v1.json").read_text(encoding="utf-8")
    )
    if (
        manifest.get("schema_version") != 1
        or manifest.get("event_count") != 22
        or manifest["parent_event_comparison_sha256"] != hashlib.sha256(measured_bytes).hexdigest()
        or manifest["fine_offsets_tt_seconds"] != list(OFFSETS_SECONDS)
        or any(
            manifest[label] is not False
            for label in (
                "absolute_root_accuracy_certified",
                "unique_root_completeness_certified",
                "commercial_release_qualified",
            )
        )
    ):
        raise ValueError("Wrong original JPL fine-time evidence/parent version")
    requests = manifest["requests"]
    rays = manifest["rays"]
    if len(requests) != manifest["original_response_count"] or not requests:
        raise ValueError("Incomplete original JPL source request list")
    mapping: dict[tuple[str, float], tuple[float, float]] = {}
    original_files: dict[tuple[str, float], str] = {}
    for item in rays:
        key = (item["body"], item["jd_tt"])
        ra, dec = item["inertial_apparent_ra_deg"], item["inertial_apparent_dec_deg"]
        if (
            item["body"] not in TARGETS
            or key in mapping
            or not all(math.isfinite(x) for x in (item["jd_tt"], ra, dec))
            or not 0 <= ra < 360
            or not -90 <= dec <= 90
        ):
            raise ValueError("Nonfinite/missing/duplicate JPL fine-time ray")
        mapping[key] = (ra, dec)
        original_files[key] = item["raw_file"]
    if len(mapping) != manifest["ray_count"]:
        raise ValueError("Missing original JPL fine-time directions")
    witnessed: set[tuple[str, float]] = set()
    for req in requests:
        body = req["body"]
        params = req["parameters"]
        if body not in TARGETS or req["target_id"] != TARGETS[body] or req["centre_id"] != 399:
            raise ValueError("Wrong JPL physical body or Earth observer")
        epochs = [float(x) for x in re.findall(r"'([0-9]+\.[0-9]+)'", params["TLIST"])]
        if not (1 <= len(epochs) <= 45) or params != query(body, "apparent", epochs):
            raise ValueError("Wrong Horizons airless ICRF observer and TT request conventions")
        if req["rows"] != len(epochs):
            raise ValueError("Truncated Horizons fine time list")
        if not req["reference_url"].startswith("https://ssd.jpl.nasa.gov/api/horizons.api?"):
            raise ValueError("Unrecognised NASA/JPL source endpoint")
        path = (root / req["original_raw_file"]).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Raw source path outside dataset")
        raw_bytes = path.read_bytes()
        if sha256(raw_bytes) != req["original_raw_sha256"]:
            raise ValueError("Modified original JPL response SHA-256")
        raw = raw_bytes.decode("utf-8")
        if source_header(raw) != req["source_header"]:
            raise ValueError("Changed JPL planetary source provenance")
        rows = parse_table(raw, TARGETS[body], "apparent", epochs)
        for item in rows:
            key = (body, item["jd_tt"])
            if key not in mapping or key in witnessed:
                raise ValueError("Missing or repeated JPL sample in original text")
            if (
                mapping[key]
                != (item["inertial_apparent_ra_deg"], item["inertial_apparent_dec_deg"])
                or original_files[key] != req["original_raw_file"]
            ):
                raise ValueError("Original JPL fine-time observations differ from manifest")
            witnessed.add(key)
    if witnessed != set(mapping):
        raise ValueError("Some JPL samples have no independently archived response")
    measured_by_id = {row["event_id"]: row for row in measured["rows"]}
    if len(measured_by_id) != 22 or len(manifest["cases"]) != 22:
        raise ValueError("Incomplete original event fixture ID set")
    source_uses: set[tuple[str, float]] = set()
    brackets = []
    for case in manifest["cases"]:
        event_id = case["event_id"]
        if event_id not in measured_by_id:
            raise ValueError("Unknown independently measured event ID")
        previous = measured_by_id[event_id]
        if (
            case["kind"] != previous["kind"]
            or case["body"] != previous["body"]
            or case["other_body"] != previous["other_body"]
            or case["goal_deg"] != previous["goal_deg"]
            or case["jpl_original_interpolated_jd_tt"] != previous["jpl_reference"]["jd_tt"]
            or case["fine_offsets_tt_seconds"] != list(OFFSETS_SECONDS)
            or case["fine_jd_tt"] != sample_days(previous["jpl_reference"]["jd_tt"])
        ):
            raise ValueError("Fine-root source timing inferred from a different event")
        if case["kind"] == "station":
            if case["station_rate_stencils_jd_tt"] != [
                station_stencil(t) for t in case["fine_jd_tt"]
            ]:
                raise ValueError("Missing independently computed JPL rate stencil")
        elif case["station_rate_stencils_jd_tt"]:
            raise ValueError("Unexpected derivative stencil for angle event")
        values = []
        original_rows = []
        for index, jd in enumerate(case["fine_jd_tt"]):
            body = case["body"]
            if case["kind"] == "station":
                dates = case["station_rate_stencils_jd_tt"][index]
                reference = [
                    true_tropical_from_icrf(*mapping[(body, t)], t) for t in dates
                ]
                rate = reference_rate(reference)
                value = rate
                source_uses.update((body, t) for t in dates)
            else:
                lon, _ = true_tropical_from_icrf(*mapping[(body, jd)], jd)
                value = signed_angle(lon, case["goal_deg"])
                source_uses.add((body, jd))
                if case["other_body"] is not None:
                    other = case["other_body"]
                    lon_other, _ = true_tropical_from_icrf(*mapping[(other, jd)], jd)
                    value = signed_angle(signed_angle(lon, lon_other), case["goal_deg"])
                    source_uses.add((other, jd))
            if not math.isfinite(value):
                raise ValueError("Nonfinite source-derived JPL root equation")
            values.append(value)
            original_rows.append({"tt_jd": jd, "source_equation": value})
        left_30, left_15, right_15, right_30 = values
        if abs(right_30 - left_30) >= 90:
            raise ValueError("False event phase jump across source refinement samples")
        observed_inner = left_15 * right_15 <= 0 and abs(left_15 - right_15) < 90
        observed_outer = left_30 * right_30 <= 0 and abs(left_30 - right_30) < 90
        aria = previous["aria_nearest_event"]
        # This is not the event root's rigorous timing uncertainty. A sign
        # change only demonstrates at least one zero under continuity.
        brackets.append(
            {
                "event_id": event_id,
                "kind": case["kind"],
                "body": case["body"],
                "other_body": case["other_body"],
                "original_jpl_interpolated_jd_tt": case["jpl_original_interpolated_jd_tt"],
                "original_aria_minus_jpl_seconds": previous[
                    "aria_minus_independently_interpolated_jpl_seconds"
                ],
                "original_source_grid_bracket_seconds": previous["jpl_reference"][
                    "reference_bracket_width_seconds"
                ],
                "fine_sampled_equation": original_rows,
                "observed_sign_change_within_plus_minus_15_seconds": observed_inner,
                "observed_sign_change_within_plus_minus_30_seconds": observed_outer,
                "independent_local_sign_change_bracket_seconds": (
                    30 if observed_inner else 60 if observed_outer else None
                ),
                "aria_root_within_verified_15_second_source_bracket": (
                    bool(aria) and case["fine_jd_tt"][1] <= aria["jd_tt"] <= case["fine_jd_tt"][2]
                    if observed_inner
                    else False
                ),
                "continuous_unique_root_not_proven": True,
                "model_physical_accuracy_not_proven": True,
            }
        )
    if source_uses != set(mapping):
        raise ValueError("Unreferenced or fabricated JPL fine-root sample")
    return {
        "schema_version": 1,
        "report_id": "aria-wp55-independent-jpl-fine-source-root-bracket-check-v1",
        "dataset_id": manifest["dataset_id"],
        "original_event_report_sha256": hashlib.sha256(measured_bytes).hexdigest(),
        "event_count": len(brackets),
        "new_independent_jpl_rays": len(mapping),
        "verified_original_jpl_source_responses": len(requests),
        "inner_30_second_sign_bracket_count": sum(
            x["observed_sign_change_within_plus_minus_15_seconds"] for x in brackets
        ),
        "outer_60_second_sign_bracket_count": sum(
            x["observed_sign_change_within_plus_minus_30_seconds"] for x in brackets
        ),
        "aria_within_verified_inner_bracket_count": sum(
            x["aria_root_within_verified_15_second_source_bracket"] for x in brackets
        ),
        "independent_full_interval_root_completeness_certified": False,
        "rigorous_root_uniqueness_or_continuous_error_bound_certified": False,
        "absolute_astronomical_accuracy_certified": False,
        "commercial_release_qualified": False,
        "events": brackets,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("data/fixtures/horizons/wp55-root-refinement"))
    p.add_argument("--original", type=Path, default=Path("data/fixtures/horizons/wp55-events"))
    p.add_argument("--wp54", type=Path, default=Path("data/fixtures/horizons/wp54-tropical"))
    p.add_argument("--comparison", type=Path, default=Path("docs/validation/wp55-independent-event-roots.json"))
    p.add_argument("--output", type=Path, default=Path("docs/validation/wp55-jpl-fine-root-brackets.json"))
    a = p.parse_args()
    report = verify(a.source, a.original, a.wp54, a.comparison)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(
        f"Independent JPL fine 30-sec sign brackets: {report['inner_30_second_sign_bracket_count']}/22; "
        f"outer 60-sec brackets: {report['outer_60_second_sign_bracket_count']}/22; "
        f"Aria roots inside verified inner bracket: "
        f"{report['aria_within_verified_inner_bracket_count']}/22",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
