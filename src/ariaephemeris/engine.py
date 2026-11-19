# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Public API orchestrating independent numerical and astrology modules."""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import numpy as np

from . import astrology, datasets
from .errors import AriaError
from .models import (
    BODY_IDS,
    PHYSICAL_BODY_IDS,
    Aspect,
    AspectRule,
    BodyPosition,
    ChartResult,
    Event,
    EventRequest,
    Observer,
    PositionRequest,
    PositionsResult,
    TimeInput,
)
from .positions import coordinates
from .sources import Kernel
from .sources.centres import CENTRE_IDS, PhysicalCentreKernel
from .time import ResolvedTime, resolve


class Ephemeris:
    def __init__(
        self,
        kernel: str | Path,
        *,
        centre_kernels: Mapping[str, str | Path] | None = None,
    ) -> None:
        self._manifest = datasets.verify(kernel)
        self.kernel = Kernel(Path(kernel))
        self._centre_kernel: PhysicalCentreKernel | None = None
        if centre_kernels:
            try:
                records = datasets.verify_centre_sources(centre_kernels)
                sources = datasets.centres_manifest()
                self._centre_kernel = PhysicalCentreKernel(
                    self.kernel,
                    centre_kernels,
                    records,
                    tuple(sources["qualified_interval_jd_tdb"]),
                )
            except Exception:
                self.kernel.close()
                raise
        # Detect missing centre dependencies up front, rather than on a chart request.
        for target in BODY_IDS.values():
            self.kernel.state(
                target,
                np.array(
                    [
                        2451545.0,
                        self._manifest["operating_interval_tt"][0] - 1,
                        self._manifest["operating_interval_tt"][1] + 1,
                    ]
                ),
            )

    @property
    def manifest(self) -> dict[str, Any]:
        """A detached manifest; callers cannot mutate the active dataset identity."""
        return deepcopy(self._manifest)

    def __enter__(self) -> "Ephemeris":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def close(self) -> None:
        if self._centre_kernel is not None:
            self._centre_kernel.close()
        self.kernel.close()

    def dataset_info(self, dataset_id: str | None = None) -> dict[str, Any]:
        if dataset_id is not None and dataset_id != self._manifest["dataset_id"]:
            raise AriaError("DATA_UNAVAILABLE", "Requested dataset is not installed")
        result = {**deepcopy(self._manifest), "segments": self.kernel.segments()}
        if self._centre_kernel is not None:
            result["physical_centres"] = self._centre_kernel.provenance(
                tuple(self._centre_kernel._sources)
            )
        return result

    def _profile_kernel(
        self, profile: str
    ) -> tuple[Kernel | PhysicalCentreKernel, dict[str, int]]:
        if profile == "reference":
            return self.kernel, BODY_IDS
        if profile == "planet-centres-v1":
            if self._centre_kernel is None:
                raise AriaError(
                    "DATA_UNAVAILABLE", "Physical planet-centre sources are not installed"
                )
            return self._centre_kernel, PHYSICAL_BODY_IDS
        raise AriaError("UNSUPPORTED_PROFILE", f"Unknown calculation profile: {profile}")

    def raw_state(
        self, body: str, time: TimeInput, *, profile: str = "reference"
    ) -> dict[str, Any]:
        if body not in BODY_IDS:
            raise AriaError("UNSUPPORTED_BODY", body)
        active, ids = self._profile_kernel(profile)
        t = resolve(time)
        self._coverage([t])
        p, v = active.state(ids[body], t.tdb1, t.tdb2)
        result: dict[str, Any] = {
            "position_km": p.tolist(),
            "velocity_km_day": v.tolist(),
            "target_id": ids[body],
            "centre_id": 0,
            "time": t.metadata(),
            "dataset_id": self._manifest["dataset_id"],
            "dataset_sha256": self._manifest["sha256"],
        }
        if profile != "reference":
            result["profile"] = profile
            result["physical_centre_sources"] = active.provenance((body,))
            result["qualification"] = "not-qualified-for-commercial-release"
        return result

    def _coverage(self, times: list[ResolvedTime]) -> None:
        lo, hi = self._manifest["operating_interval_tt"]
        if any(not lo <= t.tt1 + t.tt2 < hi for t in times):
            raise AriaError("OUT_OF_RANGE", "Operating interval: 1900-01-01 through 2100-12-31 TT")

    def _validate(self, r: PositionRequest) -> None:
        self._profile_kernel(r.profile)
        if r.zodiac != "tropical":
            raise AriaError("UNSUPPORTED_ZODIAC", "Sidereal models are not implemented")
        if r.dataset_id not in (None, self._manifest["dataset_id"]):
            raise AriaError("DATA_UNAVAILABLE", "Dataset identity mismatch")
        if not np.isfinite(r.stationary_band_deg_day) or r.stationary_band_deg_day < 0:
            raise AriaError("INVALID_REQUEST", "Stationary band must be finite and nonnegative")
        if not r.bodies or len(set(r.bodies)) != len(r.bodies):
            raise AriaError("INVALID_REQUEST", "Bodies must be nonempty and unique")
        for body in r.bodies:
            if body not in BODY_IDS:
                raise AriaError("UNSUPPORTED_BODY", body)
        if (
            r.origin == "heliocentric"
            and "sun" in r.bodies
            or r.origin == "geocentric"
            and "earth" in r.bodies
        ):
            raise AriaError("UNDEFINED_POSITION", "Target at origin has no angular coordinates")

    def _positions(
        self, request: PositionRequest, times: list[ResolvedTime]
    ) -> tuple[PositionsResult, ...]:
        self._validate(request)
        self._coverage(times)
        active, target_ids = self._profile_kernel(request.profile)
        rows: list[list[BodyPosition]] = [[] for _ in times]
        notes = []
        for body in request.bodies:
            lon, lat, dist, ra, dec, (vec, rate), ns = coordinates(
                active,
                body,
                times,
                request.origin,
                request.position_mode,
                request.frame,
                request.observer,
                request.strict,
                target_ids[body],
            )
            notes.extend(ns)
            if rate is None:
                # Five-point differentiation of the *complete* corrected pipeline.
                # This includes light time, deflection, aberration and frame motion.
                h = 0.001
                ls = []
                for shift in (-2 * h, -h, h, 2 * h):
                    ll, *_ = coordinates(
                        active,
                        body,
                        [t.shift(shift) for t in times],
                        request.origin,
                        request.position_mode,
                        request.frame,
                        request.observer,
                        request.strict,
                        target_ids[body],
                    )
                    ls.append((ll - lon + 180) % 360 - 180)
                rate = (ls[0] - 8 * ls[1] + 8 * ls[2] - ls[3]) / (12 * h)
            for i in range(len(times)):
                rr = float(rate[i])
                motion = (
                    "stationary"
                    if abs(rr) <= request.stationary_band_deg_day
                    else ("retrograde" if rr < 0 else "direct")
                )
                tid = target_ids[body]
                rows[i].append(
                    BodyPosition(
                        body,
                        tid,
                        10 if request.origin == "heliocentric" else 399,
                        "planetary-system-barycentre" if tid in range(4, 10) else "body-centre",
                        float(lon[i]),
                        float(lat[i]),
                        float(dist[i]),
                        float(ra[i]),
                        float(dec[i]),
                        rr,
                        motion,
                        (float(vec[i, 0]), float(vec[i, 1]), float(vec[i, 2])),
                    )
                )
        return tuple(
            PositionsResult(
                {
                    "engine_version": "0.1.0",
                    "dataset_id": self._manifest["dataset_id"],
                    "dataset_sha256": self._manifest["sha256"],
                    "profile": request.profile,
                    "operating_interval_tt": self._manifest["operating_interval_tt"][:],
                    "qualification": self._manifest["qualification"]["status"]
                    if request.profile == "reference"
                    else "not-qualified-for-commercial-release",
                    "origin": request.origin,
                    "observer": None if request.observer is None else asdict(request.observer),
                    "frame": request.frame,
                    "equatorial_frame": "true_equator_equinox_of_date",
                    "position_mode": request.position_mode,
                    "zodiac": "tropical",
                    "corrections": []
                    if request.position_mode == "geometric"
                    else [
                        "iterated-light-time",
                        "Sun-Jupiter-Saturn-deflection",
                        "ERFA-aberration",
                    ],
                    "rate_method": "five-point-complete-pipeline-86.4s"
                    if request.position_mode == "apparent"
                    else "state-velocity-plus-frame-derivative",
                    "standards": "IAU-2006/2000A",
                    "deflection_limiter": {"Sun": 1e-6, "Jupiter": 3e-9, "Saturn": 3e-10},
                    "qualification_scope": self._manifest["qualification"].get("scope", "not-run")
                    if request.profile == "reference"
                    else "same-kernel centre-source/CSPICE evaluator agreement only",
                    **(
                        {
                            "physical_centre_sources": active.provenance(request.bodies),
                            "physical_centre_dataset_id": datasets.centres_manifest()["dataset_id"],
                        }
                        if request.profile == "planet-centres-v1"
                        else {}
                    ),
                    "time": t.metadata(),
                    "warnings": sorted(set(notes + t.quality["warnings"])),
                },
                tuple(row),
            )
            for t, row in zip(times, rows, strict=True)
        )

    def positions(self, request: PositionRequest | dict[str, Any]) -> PositionsResult:
        r = PositionRequest.parse(request)
        t = resolve(r.time, r.strict, r.origin == "topocentric")
        return self._positions(r, [t])[0]

    def positions_batch(
        self,
        request: PositionRequest | dict[str, Any],
        times: Sequence[TimeInput | str | dict[str, Any]],
    ) -> tuple[PositionsResult, ...]:
        r = PositionRequest.parse(request)
        if not times:
            return ()
        if len(times) > 100000:
            raise AriaError("REQUEST_LIMIT", "At most 100,000 epochs per batch")
        tt = [resolve(TimeInput.parse(t), r.strict, r.origin == "topocentric") for t in times]
        return self._positions(r, tt)

    def aspects(
        self, positions: PositionsResult, rules: tuple[AspectRule, ...] = astrology.DEFAULT_ASPECTS
    ) -> tuple[Aspect, ...]:
        return astrology.aspects(positions.bodies, rules)

    def chart(
        self,
        request: PositionRequest | dict[str, Any],
        observer: Observer,
        house_system: str = "equal",
        aspect_rules: tuple[AspectRule, ...] = astrology.DEFAULT_ASPECTS,
    ) -> ChartResult:
        r = PositionRequest.parse(request)
        t = resolve(r.time, r.strict, True)
        if r.origin not in ("geocentric", "topocentric"):
            raise AriaError("INVALID_REQUEST", "A natal chart requires a terrestrial observer")
        if r.origin == "topocentric":
            r = replace(r, observer=observer)
        ps = self._positions(r, [t])[0]
        aa = astrology.angles(observer, t)
        cc = astrology.cusps(aa["ASC"], house_system)
        return ChartResult(
            ps,
            aa,
            cc,
            house_system,
            {b.body: astrology.membership(b.longitude_deg, cc) for b in ps.bodies},
            {b.body: astrology.sign(b.longitude_deg) for b in ps.bodies},
            self.aspects(ps, aspect_rules),
            {
                "angle_algorithm": "horizon-ecliptic-intersection-v1",
                "house_algorithm": house_system + "-v1",
                "boundaries": "start-inclusive-end-exclusive",
                "observer": asdict(observer),
                "time": t.metadata(),
            },
        )

    def find_events(
        self, request: EventRequest, cancelled: Callable[[], bool] | None = None
    ) -> tuple[Event, ...]:
        from .events import find_events

        return find_events(self, request, cancelled)
