# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Adversarial analytic discovery, catalogue matching and original-source checks."""

import ast
import hashlib
import json
import sys
import urllib.parse
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "datasets"))
from acquire_horizons_fixtures import API, source_header
from acquire_wp56_discovery import load_spec, range_query, validate_response
from compare_wp56_discovery import actual_catalogue
from wp56_discovery import discover, match_catalogues, tropical_longitudes

ROOT = Path(__file__).resolve().parents[2]
JD = 2451545.0


def work(kind="conjunction", angle=0):
    return dict(
        kind=kind,
        body="mars",
        other="jupiter" if kind in ("conjunction", "opposition", "aspect") else None,
        angle=angle,
    )


def scan(fn, kind="conjunction", angle=0, step=0.25):
    t = np.arange(-2, 3.01, step)
    return discover(JD + t, np.asarray(fn(t)) % 360, work(kind, angle), (JD, JD + 1))


def test_hidden_recrossings_inside_same_sign_panel():
    roots = scan(lambda x: (x - 0.31) * (x - 0.34))
    assert [e["jd_tt"] - JD for e in roots] == pytest.approx([0.31, 0.34], abs=1e-8)
    assert [e["direction"] for e in roots] == ["retrograde", "direct"]


def test_tangency_is_explicit_not_invented_precise_crossing():
    roots = scan(lambda x: (x - 0.32) ** 2)
    assert roots and all(r["ambiguous"] for r in roots)
    assert all(r["direction"] == "grazing" for r in roots)


def test_station_and_tangential_station():
    simple = scan(lambda x: (x - 0.32) ** 2 + 10, "station")
    assert len(simple) == 1
    assert simple[0]["direction"] == "retrograde-to-direct"
    tangent = scan(lambda x: (x - 0.32) ** 3 + 10, "station")
    assert tangent and all(r["ambiguous"] for r in tangent)


def test_aries_wrap_and_half_open_endpoints():
    roots = scan(lambda x: x * 30, "ingress")
    assert len(roots) == 1
    assert roots[0]["jd_tt"] == JD
    assert roots[0]["goal_deg"] == 0


def test_opposition_does_not_confuse_angular_branch_cut_with_conjunction():
    assert scan(lambda x: 180 + x - 0.5) == []
    roots = scan(lambda x: 180 + x - 0.5, "opposition", 180)
    assert len(roots) == 1 and roots[0]["goal_deg"] == 180


def test_both_aspect_branches_and_close_distinct_roots_retained():
    assert scan(lambda x: 60 + x - 0.5, "aspect", 60)[0]["goal_deg"] == 60
    assert scan(lambda x: 300 + x - 0.5, "aspect", 60)[0]["goal_deg"] == 300
    roots = scan(lambda x: (x - 0.31) * (x - 0.3101))
    assert len(roots) == 2  # 8.64-second separation is not one deduplicated event.


def test_convergence_against_exact_analytic_roots_and_grid_shifts():
    for offset in (0, 0.125):
        t = np.arange(-2 + offset, 3.01, 0.25)
        roots = discover(JD + t, ((t - 0.31) * (t - 0.34)) % 360, work(), (JD, JD + 1))
        assert [e["jd_tt"] - JD for e in roots] == pytest.approx([0.31, 0.34], abs=1e-8)


def test_invalid_grid_missing_data_plateau_and_phase_jump_fail():
    t = np.arange(-2, 3.01, 0.25)
    for dates, values in [
        (JD + t[:-1], t),
        (JD + np.delete(t, 7), np.delete(t, 7)),
        (JD + t, np.full_like(t, np.nan)),
        (JD + t, t * 500),
    ]:
        with pytest.raises(ValueError):
            discover(dates, values, work(), (JD, JD + 1))
    with pytest.raises(ValueError, match="plateau"):
        scan(lambda x: np.zeros_like(x), "station")


def event(jd, goal=0, direction="direct"):
    return dict(
        kind="conjunction",
        body="mars",
        other="jupiter",
        goal_deg=goal,
        direction=direction,
        jd_tt=jd,
    )


def test_full_list_matching_cannot_hide_missing_extra_duplicate_or_ambiguity():
    assert match_catalogues([], [], 60)["passed"]
    r = match_catalogues([event(JD), event(JD + 1)], [event(JD), event(JD + 2)], 60)
    assert (
        not r["passed"]
        and r["missing_reference_indices"] == [1]
        and r["additional_actual_indices"] == [1]
    )
    duplicate = match_catalogues([event(JD)], [event(JD), event(JD)], 60)
    assert (
        not duplicate["passed"]
        and duplicate["duplicate_actual_pairs"]
        and duplicate["ambiguous_edges"]
    )
    ambiguous = match_catalogues([event(JD), event(JD + 30 / 86400)], [event(JD + 15 / 86400)], 60)
    assert len(ambiguous["ambiguous_edges"]) == 2 and not ambiguous["matches"]
    assert not match_catalogues([event(JD)], [event(JD, direction="retrograde")], 60)["passed"]
    assert not match_catalogues([event(JD)], [event(JD, goal=180)], 60)["passed"]


def test_reference_discovery_has_no_engine_or_runtime_imports():
    tree = ast.parse((ROOT / "tools/datasets/wp56_discovery.py").read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(s and ("ariaephemeris" in s or "compare_wp" in s) for s in imports)
    spec = load_spec(ROOT / "data/fixtures/horizons/wp56-discovery/specification.json")
    assert len(spec["workloads"]) == 237
    assert len(spec["windows"]) == 11


def test_original_source_semantics_and_digest(tmp_path):
    times = [JD, JD + 0.25]
    raw = f"Target body name: Mars (499) {{source:DE441}}\nCenter body name: Earth (399) {{source:DE441}}\n$$SOE\n{JD},,,1,2,\n{JD + 0.25},,,3,4,\n$$EOE\n"
    (tmp_path / "raw.txt").write_text(raw)
    params = range_query("mars", times)
    record = dict(
        parameters=params,
        source_url=API + "?" + urllib.parse.urlencode(params),
        response_signature=dict(version="1.2", source="NASA/JPL Horizons API"),
        raw_file="raw.txt",
        raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        row_count=2,
        source_header=source_header(raw),
    )
    assert len(validate_response(tmp_path, record, "mars", times)) == 2
    for key, value in [("raw_sha256", "0" * 64), ("raw_file", "../outside.txt"), ("row_count", 3)]:
        altered = dict(record, **{key: value})
        with pytest.raises((ValueError, FileNotFoundError)):
            validate_response(tmp_path, altered, "mars", times)
    altered = json.loads(json.dumps(record))
    altered["parameters"]["TIME_TYPE"] = "UTC"
    with pytest.raises(ValueError, match="semantics"):
        validate_response(tmp_path, altered, "mars", times)
    (tmp_path / "raw.txt").write_text(raw.replace(",,,1,2,", ",,,1,3,"))
    with pytest.raises(ValueError, match="SHA"):
        validate_response(tmp_path, record, "mars", times)


def test_search_budget_failure_is_not_successful_empty_catalogue():
    def fail(request):
        raise RuntimeError("evaluation budget exhausted")

    fake = SimpleNamespace(find_events=fail)
    spec = dict(aria_tolerance_seconds=0.1, aria_max_step_days=0.25)
    row = dict(workload=work(), interval_jd_tt=[JD, JD + 1])
    with pytest.raises(RuntimeError, match="budget"):
        actual_catalogue(fake, spec, row)


def test_true_tropical_transform_matches_independent_scalar_reference():
    from compare_wp54_tropical import true_tropical_from_icrf

    rows = [
        dict(jd_tt=JD + t, inertial_apparent_ra_deg=ra, inertial_apparent_dec_deg=dec)
        for t, ra, dec in [(0, 359.5, -20), (365, 20, 40)]
    ]
    actual = tropical_longitudes(rows)
    expected = [
        true_tropical_from_icrf(
            r["inertial_apparent_ra_deg"], r["inertial_apparent_dec_deg"], r["jd_tt"]
        )[0]
        for r in rows
    ]
    assert actual == pytest.approx(expected, abs=1e-12)
