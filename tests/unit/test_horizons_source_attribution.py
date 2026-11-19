# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Synthetic decomposition regressions: source context never silently disappears."""

import importlib.util
import math
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools/datasets"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "attribute_jpl_source_models", TOOLS / "attribute_jpl_source_models.py"
)
assert SPEC is not None and SPEC.loader is not None
a = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(a)


def test_source_decomposition_exactly_reconstructs_total_residual():
    aria = {
        "centre_ssb": [130.0, 2.0, 3.0],
        "parent_ssb": [100.0, 2.0, 3.0],
        "earth_ssb": [10.0, 0.0, 0.0],
    }
    horizons = {
        "target_geo": [117.0, 2.0, 3.0],
        "parent_geo": [90.0, 2.0, 3.0],
        "parent_ssb": [98.0, 2.0, 3.0],
        "earth_ssb": [8.0, 0.0, 0.0],
        "centre_ssb": [125.0, 2.0, 3.0],
    }
    result = a.attribute(aria, horizons)
    assert result["total_difference"] == pytest.approx([3.0, 0.0, 0.0])
    assert result["parent_geocentric_difference"] == pytest.approx([0.0, 0.0, 0.0])
    assert result["effective_offset_difference"] == pytest.approx([3.0, 0.0, 0.0])
    assert result["planet_parent_ssb_model_difference"] == pytest.approx([2.0, 0.0, 0.0])
    assert result["earth_ssb_model_difference"] == pytest.approx([2.0, 0.0, 0.0])
    assert result["horizons_parent_query_context_gap"] == pytest.approx([0.0] * 3)
    assert result["total_reconstruction_error_km"] == pytest.approx(0)


def test_jpl_query_context_gap_is_retained_not_mislabelled_as_offset_error():
    aria = {
        "centre_ssb": [130, 0, 0],
        "parent_ssb": [100, 0, 0],
        "earth_ssb": [10, 0, 0],
    }
    horizons = {
        "target_geo": [116, 0, 0],
        "parent_geo": [88, 0, 0],
        "parent_ssb": [98, 0, 0],
        "earth_ssb": [8, 0, 0],
        "centre_ssb": [125, 0, 0],
    }
    result = a.attribute(aria, horizons)
    assert result["total_difference"] == [4, 0, 0]
    assert result["parent_geocentric_difference"] == [2, 0, 0]
    assert result["effective_offset_difference"] == [2, 0, 0]
    assert result["horizons_parent_query_context_gap"] == [2, 0, 0]
    assert result["horizons_centre_query_context_gap"] == [1, 0, 0]
    assert result["total_reconstruction_error_km"] == pytest.approx(0)


def test_projection_accounts_for_cancelled_residual_components():
    t = [3.0, 4.0, 0.0]
    parent = [5.0, 0.0, 0.0]
    offset = a.sub(t, parent)
    assert a.direction_projection(parent, t) == pytest.approx(3)
    assert (
        a.direction_projection(parent, t) + a.direction_projection(offset, t)
    ) == pytest.approx(5)
    assert a.stats([0.0, 1.0, 2.0, 3.0])["p95"] == pytest.approx(2.85)


def test_missing_and_nonfinite_source_components_are_strict_failures():
    aria = {"centre_ssb": [1, 2, 3], "parent_ssb": [0, 0, 0], "earth_ssb": [0, 0, 0]}
    with pytest.raises(ValueError, match="Missing exact"):
        a.attribute(aria, {"target_geo": [1, 2, 3]})
    with pytest.raises(ValueError, match="three finite"):
        a.norm([1, math.nan, 3])
    with pytest.raises(ValueError, match="nonempty"):
        a.stats([])


def test_horizons_comparison_claim_is_bounded():
    assert set(a.SELECTED) == {"jupiter", "pluto"}
    assert a.SELECTED["jupiter"] == 5
    assert a.SELECTED["pluto"] == 9
