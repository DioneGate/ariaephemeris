# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Fast, kernel-independent contract tests for the RM-001/002 source audit."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "tools/datasets/audit_planet_centres.py"
SPEC = importlib.util.spec_from_file_location("audit_planet_centres", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def segment(
    target: int,
    centre: int,
    start: float,
    end: float,
    *,
    dtype: int = 2,
    frame: int = 1,
) -> SimpleNamespace:
    return SimpleNamespace(
        target=target,
        center=centre,
        start_jd=start,
        end_jd=end,
        data_type=dtype,
        frame=frame,
    )


@pytest.mark.parametrize(
    "name,identity",
    [
        ("mars", (499, 4)),
        ("jupiter", (599, 5)),
        ("saturn", (699, 6)),
        ("uranus", (799, 7)),
        ("neptune", (899, 8)),
        ("pluto", (999, 9)),
    ],
)
def test_expected_direct_centre_identities(name, identity):
    assert audit.TARGETS[name] == identity


def test_contiguous_spans_cover_entire_window():
    rows = [segment(599, 5, 0, 50), segment(599, 5, 50, 100)]
    result = audit.inspect_segments(rows, "jupiter", (10, 90))
    assert result["reader_and_coverage_pass"]
    assert not result["supported_coverage_gaps_jd_tdb"]
    assert len(result["direct_segments"]) == 2


def test_gap_between_segments_fails_closed():
    rows = [segment(599, 5, 0, 45), segment(599, 5, 55, 100)]
    result = audit.inspect_segments(rows, "jupiter", (10, 90))
    assert not result["reader_and_coverage_pass"]
    assert result["supported_coverage_gaps_jd_tdb"] == [[45, 55]]


def test_wrong_centre_does_not_count_as_offset():
    rows = [segment(599, 0, 0, 100), segment(599, 5, 0, 100)]
    result = audit.inspect_segments(rows, "jupiter", (10, 90))
    assert result["reader_and_coverage_pass"]
    assert len(result["direct_segments"]) == 1
    assert result["direct_segments"][0]["centre"] == 5


@pytest.mark.parametrize("dtype,frame", [(20, 1), (2, 17), (3, 2)])
def test_unsupported_spk_type_or_frame_does_not_qualify(dtype, frame):
    rows = [segment(599, 5, 0, 100, dtype=dtype, frame=frame)]
    result = audit.inspect_segments(rows, "jupiter", (10, 90))
    assert not result["reader_and_coverage_pass"]
    assert result["direct_segments"][0]["supported_by_current_reader"] is False


def test_spans_outside_interval_cannot_create_duplicate_or_false_gaps():
    assert audit.coverage_gaps([(100, 200)], (10, 90)) == [[10, 90]]
    assert audit.coverage_gaps([(0, 100), (200, 300)], (10, 90)) == []
    assert audit.coverage_gaps([], (10, 90)) == [[10, 90]]


def test_missing_kernel_is_explicit_error(capsys, tmp_path):
    code = audit.main(["--kernel", f"jupiter={tmp_path / 'none.bsp'}"])
    assert code == 2
    assert "does not exist" in capsys.readouterr().err


def test_rejects_duplicate_kernels():
    with pytest.raises(SystemExit, match="2"):
        audit.main(["--kernel", "jupiter=a", "--kernel", "jupiter=b"])


def test_require_all_rejects_partial_set():
    with pytest.raises(SystemExit, match="2"):
        audit.main(["--kernel", "jupiter=a", "--require-all"])
