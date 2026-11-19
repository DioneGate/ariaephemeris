# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Explicit, atomic installation and verification. No runtime network access."""

import hashlib
import json
import os
import tempfile
import urllib.request
from importlib.resources import files
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from ..errors import AriaError


def centres_manifest() -> dict[str, Any]:
    """Pinned package metadata for six official, unmodified JPL satellite kernels."""
    return json.loads(files("ariaephemeris.resources").joinpath("planet-centres.json").read_text())


def verify_centre_sources(paths: Mapping[str, str | Path]) -> dict[str, dict[str, Any]]:
    """Verify explicit local centre sources. No network, approximation or fallback."""
    m = centres_manifest()
    if m["base_sha256"] != manifest()["sha256"]:
        raise AriaError("DATA_INTEGRITY_ERROR", "Centre manifest base DE442s identity mismatch")
    selected: dict[str, dict[str, Any]] = {}
    for body, value in paths.items():
        expected = m["sources"].get(body)
        if expected is None:
            raise AriaError("INVALID_REQUEST", f"Unrecognised physical-centre source: {body}")
        path = Path(value)
        if not path.is_file():
            raise AriaError("DATA_UNAVAILABLE", f"Physical-centre source missing: {body}")
        if path.stat().st_size != expected["size_bytes"] or sha256(path) != expected["sha256"]:
            raise AriaError("DATA_INTEGRITY_ERROR", f"Physical-centre checksum mismatch: {body}")
        selected[body] = dict(expected)
    return selected


def manifest() -> dict[str, Any]:
    return json.loads(files("ariaephemeris.resources").joinpath("de442s.json").read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    m = manifest()
    if not path.is_file():
        raise AriaError("DATA_UNAVAILABLE", "Install the JPL kernel explicitly first")
    if path.stat().st_size != m["size_bytes"] or sha256(path) != m["sha256"]:
        raise AriaError("DATA_INTEGRITY_ERROR", "JPL kernel size/checksum mismatch")
    return m


def install(directory: str | Path, source: str | Path | None = None) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    m = manifest()
    destination = directory / m["filename"]
    if destination.exists():
        verify(destination)
        return destination
    fd, tmp = tempfile.mkstemp(prefix="aria-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as out:
            if source is None:
                stream = urllib.request.urlopen(m["source_url"], timeout=60)
            else:
                stream = Path(source).open("rb")
            with stream:
                total = 0
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    total += len(block)
                    if total > m["size_bytes"]:
                        raise AriaError("DATA_INTEGRITY_ERROR", "Download exceeds expected size")
                    out.write(block)
        verify(tmp)
        os.replace(tmp, destination)
        return destination
    finally:
        Path(tmp).unlink(missing_ok=True)
