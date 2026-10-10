# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Install built wheel and sdist in clean environments; inspect notices and CLI."""

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
wheel = next((root / "dist").glob("*.whl"))
with zipfile.ZipFile(wheel) as archive:
    names = archive.namelist()
    for suffix in [
        "licenses/LICENSE",
        "licenses/NOTICE",
        "licenses/THIRD_PARTY_NOTICES",
        "licenses/docs/licenses/ERFA.txt",
        "licenses/docs/licenses/dependencies/jplephem/0-LICENSE.txt",
        "licenses/docs/licenses/dependencies/numpy/0-LICENSE.txt",
        "licenses/docs/licenses/dependencies/pyerfa/0-LICENSE.rst",
        "ariaephemeris/resources/Leap_Second.dat",
        "ariaephemeris/resources/de442s.json",
    ]:
        assert any(n.endswith(suffix) for n in names), suffix
for artifact in [wheel, next((root / "dist").glob("*.tar.gz"))]:
    with tempfile.TemporaryDirectory(prefix="aria-smoke-") as temp:
        env = Path(temp) / "env"
        subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
        python = env / "bin/python"
        subprocess.run(
            [str(python), "-m", "pip", "install", str(artifact)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        subprocess.run(
            [str(env / "bin/ariaephemeris"), "--help"],
            check=True,
            stdout=subprocess.DEVNULL,
            cwd=temp,
        )
        info = subprocess.run(
            [
                str(python),
                "-c",
                "from ariaephemeris.datasets import manifest; import json; print(json.dumps(manifest()))",
            ],
            check=True,
            capture_output=True,
            text=True,
            cwd=temp,
        )
        assert (
            json.loads(info.stdout)["sha256"]
            == "54d97562a5b094d298b1b8eafa5a2e17e3e010ce85e1a366d07f003ad159323c"
        )
        kernel = os.environ.get("ARIA_KERNEL")
        if kernel:
            kernel = str(Path(kernel).resolve())
            for command in ["positions", "batch", "chart", "aspects", "events"]:
                result = subprocess.run(
                    [
                        str(env / "bin/ariaephemeris"),
                        command,
                        "--kernel",
                        kernel,
                        "--request",
                        str(root / "examples" / f"{command}.json"),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    cwd=temp,
                )
                assert json.loads(result.stdout)
print("Clean wheel and sdist installations, legal payload and CLI smoke checks passed.")
