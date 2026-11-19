# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Source independence, numerical sensitivity and unknown physical uncertainty."""

import hashlib
import json
import math
import sys
import urllib.parse
from pathlib import Path

import erfa
import numpy as np
import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
from acquire_horizons_fixtures import API, source_header  # noqa: E402
from acquire_horizons_model_components import PARENTS, specification  # noqa: E402
from wp57_source import DEFAULT_ROOT, REMAINING, load_spec, station_times, validate_receipt  # noqa: E402
from wp57_uncertainty import refine_stations, sensitivity_seconds, signed_rate, uncertainty_register  # noqa: E402

JD = 2451545.0


def test_remaining_source_roles_use_exact_targets_and_origins():
    for body, parent in REMAINING.items():
        for role, target, origin in [
            ("parent_geo", parent, 399),
            ("parent_ssb", parent, 0),
            ("earth_ssb", 399, 0),
            ("centre_ssb", parent * 100 + 99, 0),
        ]:
            params = specification(body, role, REMAINING)
            assert params["COMMAND"] == f"'{target}'"
            assert params["CENTER"] == f"'500@{origin}'"
            assert params["TIME_TYPE"] == "TDB" and params["VEC_CORR"] == "NONE"
    assert PARENTS == {"jupiter": 5, "pluto": 9}
    assert specification("jupiter", "centre_ssb")["COMMAND"] == "'599'"
    with pytest.raises(ValueError):
        specification("neptune", "centre_ssb")


def test_rate_wrap_and_first_order_conditioning_have_explicit_limits():
    h = 0.001
    assert signed_rate([(359.999 - k * h) % 360 for k in (-2, -1, 0, 1, 2)], h) == pytest.approx(
        -1, abs=1e-10
    )
    assert sensitivity_seconds(0.0001, 0.00001) == pytest.approx(864000)
    assert sensitivity_seconds(0, 0) is None
    assert sensitivity_seconds(1, 0) is None
    assert sensitivity_seconds(-2, -4) == 43200
    for bad in (math.nan, math.inf):
        with pytest.raises(ValueError):
            sensitivity_seconds(bad, 1)
    with pytest.raises(ValueError):
        signed_rate([0] * 5, 0)


def ray(jd, longitude):
    eps = erfa.obl06(2451545.0, jd - 2451545.0) + erfa.nut06a(2451545.0, jd - 2451545.0)[1]
    x, y = math.cos(math.radians(longitude)), math.sin(math.radians(longitude))
    equatorial = np.array([x, math.cos(eps) * y, math.sin(eps) * y])
    inertial = erfa.pnm06a(2451545.0, jd - 2451545.0).T @ equatorial
    return dict(
        jd_tt=jd,
        inertial_apparent_ra_deg=math.degrees(math.atan2(inertial[1], inertial[0])) % 360,
        inertial_apparent_dec_deg=math.degrees(math.atan2(inertial[2], math.hypot(*inertial[:2]))),
    )


def refinement_fixture(fn=lambda x: 100 + 100 * (x - 0.01) ** 2):
    spec = json.loads((DEFAULT_ROOT / "specification.json").read_text())
    case = dict(
        id="JPL-only-test",
        body="neptune",
        jd_tt=JD,
        workload_id="test",
        reference_index=0,
        direction="retrograde-to-direct",
    )
    spec["station_centres"] = [case]
    work = dict(kind="station", body="neptune", other=None, angle=0, id="test")
    actual = dict(
        kind="station",
        body="neptune",
        other=None,
        goal_deg=None,
        direction="retrograde-to-direct",
        jd_tt=JD + 0.01 + 0.5 / 86400,
    )
    previous = dict(records=[dict(workload=work, reference_resolved=False, aria_events=[actual])])
    sources = {("neptune", t): ray(t, fn(t - JD)) for t in station_times(spec, case)}
    return spec, sources, previous


def test_refinement_uses_only_source_rays_and_keeps_old_failure():
    spec, sources, previous = refinement_fixture()
    row = refine_stations(spec, sources, previous)[0]
    assert row["passed"] and row["reference_resolved"]
    assert row["original_reference_converged"] is False
    assert row["roots_by_grid"]["45-minute"][0]["jd_tt"] - JD == pytest.approx(0.01, abs=1e-8)
    assert row["aria_comparison"]["matches"][0]["actual_minus_reference_seconds"] == pytest.approx(
        0.5, abs=0.002
    )
    expected = row["roots_by_grid"]
    previous["records"][0]["aria_events"][0]["jd_tt"] += 10
    changed = refine_stations(spec, sources, previous)[0]
    assert changed["roots_by_grid"] == expected
    assert not changed["passed"]
    assert row["physical_time_uncertainty_seconds"] is None


def test_multiple_source_station_roots_and_missing_data_are_not_discarded():
    spec, sources, previous = refinement_fixture(lambda x: 100 + x**3 / 3 - 0.01 * x)
    row = refine_stations(spec, sources, previous)[0]
    assert len(row["roots_by_grid"]["45-minute"]) == 2
    assert not row["reference_resolved"] and not row["passed"]
    del sources[next(iter(sources))]
    with pytest.raises(KeyError):
        refine_stations(spec, sources, previous)


def test_spec_centres_are_from_frozen_jpl_catalogue_and_changed_dates_fail(tmp_path):
    spec = load_spec(DEFAULT_ROOT)
    assert len(spec["station_centres"]) == 36
    assert len(station_times(spec, spec["station_centres"][0])) == 65
    spec["station_centres"][0]["jd_tt"] += 1
    (tmp_path / "specification.json").write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="JPL discovery"):
        load_spec(tmp_path)


def test_unknown_physical_uncertainty_never_becomes_zero_or_sigma():
    rows = uncertainty_register()
    assert len(rows) == 8 and len({r["id"] for r in rows}) == 8
    assert all(r["absolute_physical_bound"] is None for r in rows)
    assert all(r["closure_requirement"] for r in rows)
    assert "sigma" in rows[1]["evidence_interpretation"]


def test_corrupt_or_mislabelled_original_source_fails(tmp_path):
    dates = [JD]
    params = specification("neptune", "parent_ssb", REMAINING)
    raw = f"Target body name: Neptune Barycenter (8) {{source:DE441}}\nCenter body name: Solar System Barycenter (0) {{source:DE441}}\nOutput units: KM-S\nOutput type: GEOMETRIC cartesian states\nReference frame: ICRF\nJDTDB\n$$SOE\n{JD},,1,2,3,4,5,6,\n$$EOE"
    (tmp_path / "raw.txt").write_text(raw)
    record = dict(
        parameters=params,
        url=API + "?" + urllib.parse.urlencode(params),
        raw_file="raw.txt",
        raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
        source_header=source_header(raw),
        row_count=1,
        response_signature=dict(source="NASA/JPL Horizons API", version="1.2"),
    )
    assert len(validate_receipt(tmp_path, record, params, 8, "geometric", dates)) == 1
    bad = raw.replace("JDTDB", "JDUTC")
    (tmp_path / "raw.txt").write_text(bad)
    record["raw_sha256"] = hashlib.sha256(bad.encode()).hexdigest()
    with pytest.raises(ValueError, match="convention"):
        validate_receipt(tmp_path, record, params, 8, "geometric", dates)


def test_reference_chain_mixing_is_separated_before_offset_interpretation():
    from wp57_uncertainty import separate_offset_context

    components = dict(
        total_difference=[0.1, 0, 0],
        parent_geocentric_difference=[4000, 0, 0],
        effective_offset_difference=[-3999.9, 0, 0],
    )
    result = separate_offset_context(components, [5000.2, 0, 0], [1000.1, 0, 0], [0.1, 0, 0])
    assert result["reference_chain_offset_mixing"] == pytest.approx([4000, 0, 0])
    assert result["direct_physical_offset_difference"] == pytest.approx([0.1, 0, 0])
    assert result["reconstruction_error"] < 1e-9
    from wp57_source import offset_query

    assert offset_query("uranus")["CENTER"] == "'500@7'"
    assert offset_query("uranus")["COMMAND"] == "'799'"


def test_continuous_reference_resolves_the_recorded_knot_artifacts():
    from wp57_source import WP56_REPORT, verify

    _, rays = verify(DEFAULT_ROOT)
    previous = json.loads(WP56_REPORT.read_text())
    initial = json.loads(
        (
            Path(__file__).resolve().parents[2]
            / "docs/validation/wp57-initial-local-cubic-diagnostic.json"
        ).read_text()
    )
    assert initial["passed"] is False and initial["resolved_station_count"] == 17
    rows = refine_stations(load_spec(DEFAULT_ROOT), rays, previous)
    assert len(rows) == 36 and all(r["passed"] for r in rows)
    assert all(len(r["roots_by_grid"]["45-minute"]) == 1 for r in rows)
    assert previous["passed"] is False and previous["unresolved_reference_workloads"] == 6
    assert all(r["physical_time_uncertainty_seconds"] is None for r in rows)


def test_continuous_reference_refuses_a_plateau_and_missing_epochs():
    from wp57_uncertainty import continuous_station_roots

    times = JD + np.arange(-1, 1.01, 0.125)
    with pytest.raises(ValueError, match="plateau"):
        continuous_station_roots(times, np.full_like(times, 100), "mars", (JD - 0.25, JD + 0.25))
    with pytest.raises(ValueError, match="nonuniform"):
        continuous_station_roots(
            np.delete(times, 3), np.delete(times - JD, 3), "mars", (JD - 0.25, JD + 0.25)
        )


def test_replay_precision_is_narrow_unit_aware_and_preserves_scientific_flags():
    from wp57_replay import assert_replay_equal

    frozen = dict(
        station_refinement=[
            dict(
                jd_tt=JD,
                source_rates_deg_tt_day={"0.03125": 0.1},
                passed=True,
                physical_time_uncertainty_seconds=None,
            )
        ],
        source_integrity=dict(sha="original"),
    )
    import copy

    tiny = copy.deepcopy(frozen)
    tiny["station_refinement"][0]["jd_tt"] += 1e-9
    assert assert_replay_equal(tiny, frozen)["nonidentical_floats"] == 1
    wrong = copy.deepcopy(frozen)
    wrong["station_refinement"][0]["jd_tt"] += 1 / 86400
    with pytest.raises(AssertionError, match="numerical"):
        assert_replay_equal(wrong, frozen)
    for key, value in [("passed", False), ("physical_time_uncertainty_seconds", 0)]:
        wrong = copy.deepcopy(frozen)
        wrong["station_refinement"][0][key] = value
        with pytest.raises(AssertionError, match="identity/flag"):
            assert_replay_equal(wrong, frozen)
    wrong = copy.deepcopy(frozen)
    wrong["source_integrity"]["sha"] = "changed"
    with pytest.raises(AssertionError):
        assert_replay_equal(wrong, frozen)
    with pytest.raises(AssertionError, match="numerical"):
        assert_replay_equal(dict(position_km=1.0000000001), dict(position_km=1.0))


def test_replay_conditioning_proxies_must_reconstruct_from_their_primitives():
    import copy

    from wp57_replay import assert_replay_equal

    row = dict(
        equation_acceleration_deg_tt_day2=0.001,
        aria_derivative_step_spread_deg_tt_day=1e-11,
        aria_derivative_spread_timing_proxy_seconds=abs(1e-11 / 0.001) * 86400,
    )
    frozen = dict(station_refinement=[row])
    changed = copy.deepcopy(frozen)
    changed["station_refinement"][0]["aria_derivative_step_spread_deg_tt_day"] = 2e-11
    changed["station_refinement"][0]["aria_derivative_spread_timing_proxy_seconds"] = (
        abs(2e-11 / 0.001) * 86400
    )
    assert assert_replay_equal(changed, frozen)["nonidentical_floats"] == 2
    changed["station_refinement"][0]["aria_derivative_spread_timing_proxy_seconds"] += 1e-6
    with pytest.raises(AssertionError, match="proxy is inconsistent"):
        assert_replay_equal(changed, frozen)
