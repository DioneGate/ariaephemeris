# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import json
from pathlib import Path

import jsonschema
import pytest

from ariaephemeris.cli import main

pytestmark = pytest.mark.kernel
ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("command", ["positions", "batch", "chart", "aspects", "events"])
def test_documented_cli_examples(engine, capsys, command):
    kernel = engine.kernel._spk.daf.file.name
    assert (
        main([command, "--kernel", kernel, "--request", str(ROOT / "examples" / f"{command}.json")])
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    schema_name = (
        "positions" if command == "positions" else ("events" if command == "events" else command)
    )
    if command != "batch":
        jsonschema.validate(
            output, json.loads((ROOT / "schemas" / f"{schema_name}-result-v1.json").read_text())
        )
    if command == "positions":
        jsonschema.validate(
            output, json.loads((ROOT / "schemas/positions-result-v1.json").read_text())
        )
        expected = engine.positions(json.loads((ROOT / "examples/positions.json").read_text()))
        assert output == json.loads(json.dumps(expected.to_dict()))
    elif command == "chart":
        assert len(output["house_cusps_deg"]) == 12
    else:
        assert output


def test_manifest_detached_and_thread_safe_reads(engine):
    from concurrent.futures import ThreadPoolExecutor

    from ariaephemeris import PositionRequest, TimeInput

    m = engine.manifest
    m["sha256"] = "broken"
    assert engine.manifest["sha256"] != "broken"
    request = PositionRequest(TimeInput(jd=(2451545, 0), scale="TT"), bodies=("moon",))
    expected = engine.positions(request).bodies
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(p.bodies == expected for p in pool.map(engine.positions, [request] * 12))
