# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Acquire independent Horizons physical-centre references, never Aria outputs.

Network access is an EXPLICIT acquisition operation, not a test/runtime
dependency. Serialize requests to respect NASA/JPL's public API fair-use rules.
All original Horizons responses are archived with SHA-256 and exact queries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API = "https://ssd.jpl.nasa.gov/api/horizons.api"
DOC = "https://ssd-api.jpl.nasa.gov/doc/horizons.html"
USER_AGENT = (
    "AriaEphemeris-ReferenceFixtures/0.1 "
    "(contact: https://github.com/DioneGate/ariaephemeris/issues)"
)
TARGETS = {"mars": 499, "jupiter": 599, "saturn": 699, "uranus": 799, "neptune": 899, "pluto": 999}
SEAMS_TDB_JD = {
    "mars": 2447575.5,
    "jupiter": 2450464.5,
    "saturn": 2456928.5,
    "uranus": 2446278.5,
    "neptune": 2447830.5,
    "pluto": 2456293.5,
}
START = 2415021.5
STOP = 2488433.5
NUM_EPOCHS = 25


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def epochs(body: str) -> list[float]:
    """18 stratified dates plus the seam, two seam neighbours and four anchors."""
    seam = SEAMS_TDB_JD[body]
    values = [START + (STOP - START) * i / 17 for i in range(18)]
    values.extend([seam - 0.04, seam, seam + 0.04, 2451545.0, 2461041.5, 2469807.5, 2487704.5])
    ordered = sorted(round(x, 7) for x in values)
    assert len(ordered) == NUM_EPOCHS and len(set(ordered)) == NUM_EPOCHS
    return ordered


def quoted(text: str) -> str:
    return f"'{text}'"


def query(body: str, kind: str, points: list[float]) -> dict[str, str]:
    if body not in TARGETS or kind not in ("geometric", "apparent"):
        raise ValueError("Unrecognised physical body or Horizons query kind")
    if len(points) == 0 or len(points) > 50:
        raise ValueError("One to fifty explicit epochs required per request")
    base = {
        "format": "json",
        "COMMAND": quoted(str(TARGETS[body])),
        "OBJ_DATA": "NO",
        "MAKE_EPHEM": "YES",
        "CENTER": quoted("500@399"),
        "REF_SYSTEM": quoted("ICRF"),
        "TLIST_TYPE": quoted("JD"),
        "TLIST": " ".join(quoted(f"{value:.7f}") for value in points),
        "CSV_FORMAT": "YES",
    }
    if kind == "geometric":
        base.update(
            {
                "EPHEM_TYPE": "VECTORS",
                "TIME_TYPE": "TDB",
                "REF_PLANE": "FRAME",
                "VEC_TABLE": "2",
                "VEC_LABELS": "NO",
                "VEC_CORR": "NONE",
                "OUT_UNITS": "KM-S",
            }
        )
    else:
        base.update(
            {
                "EPHEM_TYPE": "OBSERVER",
                "TIME_TYPE": "TT",
                "QUANTITIES": quoted("45"),
                "CAL_FORMAT": "JD",
                "ANG_FORMAT": "DEG",
                "EXTRA_PREC": "YES",
                "APPARENT": "AIRLESS",
            }
        )
    return base


def _numeric(token: str) -> float | None:
    text = token.strip()
    try:
        value = float(text.replace("D", "E"))
    except ValueError:
        return None
    if not math.isfinite(value):
        raise ValueError("Non-finite Horizons output token")
    return value


def parse_table(raw: str, target: int, kind: str, times: list[float]) -> list[dict[str, Any]]:
    if raw.count("$$SOE") != 1 or raw.count("$$EOE") != 1:
        raise ValueError("No unique complete Horizons ephemeris table")
    header = raw[: raw.index("$$SOE")]
    if not re.search(r"Target body name:.*?\(" + str(target) + r"\)", header):
        raise ValueError("Horizons resolved a different physical-centre target")
    block = raw.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    output: list[dict[str, Any]] = []
    for line in block.splitlines():
        if not line.strip():
            continue
        row = next(csv.reader([line]))
        values = [_numeric(item) for item in row]
        numbers = [x for x in values if x is not None]
        if not numbers:
            continue
        if len(numbers) < 3:
            raise ValueError(f"Horizons ephemeris row missing numbers: {line[:100]}")
        jd = numbers[0]
        assert jd is not None
        if kind == "geometric":
            if len(numbers) != 7:
                raise ValueError(f"Expected JD + six geometric vector components: {line[:110]}")
            xyzv = numbers[1:]
            record = {"jd_tdb": jd, "position_km": xyzv[:3], "velocity_km_s": xyzv[3:]}
        else:
            if len(numbers) != 3:
                raise ValueError(f"Expected JD + inertial RA/Dec degrees: {line[:110]}")
            ra, dec = numbers[1:]
            if not (0 <= ra < 360 and -90 <= dec <= 90):
                raise ValueError("Out-of-range Horizons inertial RA/Dec")
            record = {"jd_tt": jd, "inertial_apparent_ra_deg": ra, "inertial_apparent_dec_deg": dec}
        output.append(record)
    if len(output) != len(times):
        raise ValueError(f"Horizons returned {len(output)} rows, expected {len(times)}")
    for expected, actual in zip(times, output, strict=True):
        key = "jd_tdb" if kind == "geometric" else "jd_tt"
        if abs(actual[key] - expected) > 3e-6:
            raise ValueError(f"Time mismatch: {actual[key]} versus {expected}")
    return output


def source_header(raw: str) -> dict[str, str]:
    header = raw.split("$$SOE", 1)[0]
    fields: dict[str, str] = {}
    for key, label in (("target", "Target body name:"), ("centre", "Center body name:")):
        rows = [line.strip() for line in header.splitlines() if label in line]
        if len(rows) != 1:
            raise ValueError(f"Missing or ambiguous Horizons {label} header")
        fields[key] = rows[0]
    labels = sorted(set(re.findall(r"\{source:\s*([^}]+)\}", header)))
    fields["source_solution_labels"] = ", ".join(labels) if labels else "NOT STATED"
    return fields


def fetch(params: dict[str, str], timeout: int = 150) -> tuple[dict[str, Any], str]:
    url = API + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read(2_000_001)
                if len(data) > 2_000_000:
                    raise ValueError("Horizons response exceeds 2 MB safety limit")
            payload = json.loads(data.decode("utf-8"))
            signature = payload.get("signature", {})
            if str(signature.get("version")) not in ("1.0", "1.1", "1.2", "1.3"):
                raise ValueError("Unreviewed Horizons API signature version")
            if "Horizons" not in str(signature.get("source", "")):
                raise ValueError("Unexpected Horizons API source")
            raw = payload.get("result")
            if not isinstance(raw, str) or "$$SOE" not in raw:
                raise ValueError(f"Horizons failed to produce ephemeris: {str(raw)[:280]}")
            return payload, url
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            transient = not isinstance(error, urllib.error.HTTPError) or error.code in (
                429,
                500,
                502,
                503,
                504,
            )
            if not transient or attempt == 2:
                raise
            time.sleep(6 * (attempt + 1))
    raise RuntimeError("Horizons API could not be reached")


def acquire(directory: Path, *, probe: bool = False) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    raw_dir = directory / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    bodies = ("jupiter",) if probe else tuple(TARGETS)
    cases: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for body in bodies:
        points = epochs(body)[:2] if probe else epochs(body)
        for kind in ("geometric", "apparent"):
            params = query(body, kind, points)
            payload, url = fetch(params)
            raw = payload["result"]
            records = parse_table(raw, TARGETS[body], kind, points)
            header = source_header(raw)
            filename = f"{body}-{kind}.txt"
            path = raw_dir / filename
            encoded = raw.encode("utf-8")
            path.write_bytes(encoded)
            evidence.append(
                {
                    "body": body,
                    "target_id": TARGETS[body],
                    "kind": kind,
                    "request_url": url,
                    "request_parameters": params,
                    "response_signature": payload["signature"],
                    "raw_file": f"raw/{filename}",
                    "raw_sha256": sha256(encoded),
                    "source_header": header,
                    "row_count": len(records),
                }
            )
            for index, item in enumerate(records):
                cases.append(
                    {
                        "id": f"ARIA-PC-{body.upper()}-{kind.upper()}-{index + 1:02d}",
                        "body": body,
                        "target_id": TARGETS[body],
                        "kind": kind,
                        "reference": item,
                        "source_raw_file": f"raw/{filename}",
                    }
                )
            print(
                f"{body} {kind}: {len(records)} parsed Horizons rows, {len(encoded)} raw bytes",
                flush=True,
            )
            if not (body == bodies[-1] and kind == "apparent"):
                time.sleep(3)  # NASA/JPL requests are serial, not parallel.
    output = {
        "schema_version": 1,
        "dataset_id": "aria-horizons-physical-centre-reference-v1",
        "authority": "NASA/JPL Horizons independently executed public API",
        "api_docs": DOC,
        "acquired_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "reference_model": "Horizons-selected source solutions, not necessarily Aria DE442s + satellite source combination",
            "geometry": "geocentric (399), physical target centres, ICRF, TDB geometric km/km-s",
            "apparent": "geocentric (399), ICRF inertial airless apparent RA/Dec, TT observer times",
            "comparison_status": "NOT COMPARED: WP5.2 forthcoming",
            "commercial_accuracy_qualified": False,
            "time_domains": "Geometric vector TLIST is TDB; observer apparent TLIST is TT; equal numeric JDs are NOT the same instant",
        },
        "epoch_policy": "18 stratified dates 1900–2100 plus 7 anchored/segment-seam tests per planet",
        "raw_queries": evidence,
        "cases": cases,
        "case_count": len(cases),
    }
    name = "probe.json" if probe else "horizons-reference-v1.json"
    (directory / name).write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/fixtures/horizons"))
    parser.add_argument(
        "--probe", action="store_true", help="Only one body, two epochs of each mode"
    )
    args = parser.parse_args()
    data = acquire(args.output_dir, probe=args.probe)
    print(f"Horizons fixture acquisition complete: {data['case_count']} records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
