# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import json
from pathlib import Path

import jsonschema
import pytest

from ariaephemeris import AriaError, Observer, TimeInput
from ariaephemeris.datasets import manifest

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_nonfinite_eop_rejected(value):
    with pytest.raises(AriaError):
        TimeInput(jd=(2451545, 0), delta_t_seconds=value)
    with pytest.raises(AriaError):
        Observer(0, 0, xp_arcsec=value)


def test_manifest_schema_and_duplicate_agree():
    schema = json.loads((ROOT / "schemas/dataset-manifest-v1.json").read_text())
    jsonschema.validate(manifest(), schema)
    assert manifest() == json.loads((ROOT / "data/manifests/de442s.json").read_text())


def test_position_example_schema():
    jsonschema.validate(
        json.loads((ROOT / "examples/positions.json").read_text()),
        json.loads((ROOT / "schemas/position-request-v1.json").read_text()),
    )


@pytest.mark.parametrize("command", ["positions", "batch", "chart", "aspects", "events"])
def test_all_example_request_schemas(command):
    prefix = "position" if command == "positions" else ("event" if command == "events" else command)
    jsonschema.validate(
        json.loads((ROOT / "examples" / f"{command}.json").read_text()),
        json.loads((ROOT / "schemas" / f"{prefix}-request-v1.json").read_text()),
    )
