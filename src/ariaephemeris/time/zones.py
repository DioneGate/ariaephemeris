# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Load checksum-pinned TZif resources without consulting host TZPATH or its cache."""

import hashlib
import io
import json
from functools import lru_cache
from importlib.resources import files
from typing import Any
from zoneinfo import ZoneInfo

import tzdata

from ..errors import AriaError

_MANIFEST = json.loads(files("ariaephemeris.resources").joinpath("tzdata-v1.json").read_text())


@lru_cache(maxsize=128)
def load_zone(key: str) -> tuple[ZoneInfo, dict[str, Any]]:
    if tzdata.__version__ != _MANIFEST["package_version"]:
        raise AriaError("TIME_DATA_UNAVAILABLE", "Timezone package differs from pinned version")
    # Lookup first: absolute paths, traversal, non-TZif resources and unknown keys fail closed.
    expected = _MANIFEST["zones"].get(key)
    if expected is None:
        raise AriaError("INVALID_REQUEST", "Unknown IANA timezone")
    try:
        data = files("tzdata.zoneinfo").joinpath(*key.split("/")).read_bytes()
    except OSError as e:
        raise AriaError("TIME_DATA_UNAVAILABLE", "Pinned timezone resource is unavailable") from e
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise AriaError("TIME_DATA_UNAVAILABLE", "Timezone resource checksum mismatch")
    return ZoneInfo.from_file(io.BytesIO(data), key=key), {
        "key": key,
        "package": "tzdata",
        "package_version": _MANIFEST["package_version"],
        "iana_version": _MANIFEST["iana_version"],
        "tzif_sha256": digest,
    }
