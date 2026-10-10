# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
import os
from pathlib import Path

import pytest

from ariaephemeris import Ephemeris


@pytest.fixture(scope="session")
def engine():
    path = os.environ.get("ARIA_KERNEL")
    if not path:
        pytest.skip("Set ARIA_KERNEL to run real-kernel tests; this is NOT qualification")
    with Ephemeris(Path(path)) as e:
        yield e
