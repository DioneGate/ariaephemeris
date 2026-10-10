# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Thin JSON command-line adapters; no implicit network activity."""

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..astrology import DEFAULT_ASPECTS
from ..datasets import install
from ..engine import Ephemeris
from ..errors import AriaError
from ..models import AspectRule, EventRequest, Observer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ariaephemeris")
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("install-data")
    acquire.add_argument("directory")
    acquire.add_argument(
        "--source", help="Install from an existing local kernel instead of downloading"
    )
    for name in ("dataset-info", "positions", "batch", "chart", "aspects", "events"):
        p = sub.add_parser(name)
        p.add_argument("--kernel", required=True)
        if name != "dataset-info":
            p.add_argument("--request", required=True, help="JSON file path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        if args.command == "install-data":
            output: Any = {"kernel": str(install(args.directory, args.source))}
        else:
            request = {}
            if args.command != "dataset-info":
                request = json.loads(
                    sys.stdin.read() if args.request == "-" else Path(args.request).read_text()
                )
            with Ephemeris(args.kernel) as engine:
                if args.command == "dataset-info":
                    output = engine.dataset_info()
                elif args.command == "positions":
                    output = engine.positions(request).to_dict()
                elif args.command == "batch":
                    times = request.pop("times")
                    output = [p.to_dict() for p in engine.positions_batch(request, times)]
                elif args.command == "chart":
                    rules = (
                        tuple(AspectRule(**x) for x in request.pop("aspect_rules", []))
                        or DEFAULT_ASPECTS
                    )
                    observer = Observer(**request.pop("observer"))
                    house_system = request.pop("house_system", "equal")
                    output = engine.chart(request, observer, house_system, rules).to_dict()
                elif args.command == "aspects":
                    rules = (
                        tuple(AspectRule(**x) for x in request.pop("aspect_rules", []))
                        or DEFAULT_ASPECTS
                    )
                    output = [asdict(a) for a in engine.aspects(engine.positions(request), rules)]
                else:
                    output = [asdict(e) for e in engine.find_events(EventRequest(**request))]
        print(json.dumps(output, indent=2, allow_nan=False))
        return 0
    except AriaError as e:
        print(json.dumps({"error": e.to_dict()}), file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError, OSError) as e:
        print(
            json.dumps({"error": {"code": "INVALID_REQUEST", "message": str(e)}}), file=sys.stderr
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
