# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Public API orchestrating independent numerical and astrology modules."""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

import erfa
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
from .sources.centres import PhysicalCentreKernel
from .time import DAY, LEAP_EXPIRY_JD, ResolvedTime, resolve
from .time.eop import EarthOrientation


class Ephemeris:
    def __init__(
        self,
        kernel: str | Path,
        *,
        centre_kernels: Mapping[str, str | Path] | None = None,
        eop_path: str | Path | None = None,
        allow_predicted_eop: bool = False,
    ) -> None:
        if not isinstance(allow_predicted_eop, bool):
            raise AriaError("INVALID_REQUEST", "allow_predicted_eop must be boolean")
        if allow_predicted_eop and eop_path is None:
            raise AriaError(
                "INVALID_REQUEST", "Prediction opt-in requires an explicit EOP snapshot"
            )
        self._eop = (
            EarthOrientation(eop_path, allow_predictions=allow_predicted_eop)
            if eop_path is not None
            else None
        )
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
                tuple(datasets.centres_manifest()["sources"])
            )
        if self._eop is not None:
            result["earth_orientation"] = self._eop.info()
        return result

    def _resolve_time(
        self,
        ti: TimeInput,
        strict: bool,
        require_ut1: bool = False,
        observer: Observer | None = None,
        require_polar: bool = False,
    ) -> ResolvedTime:
        manual_rotation = ti.dut1_seconds is not None or ti.delta_t_seconds is not None
        managed_rotation = (
            require_ut1
            and not manual_rotation
            and self._eop is not None
            and ti.scale.upper() == "UTC"
            and ti.civil_policy == "strict"
        )
        managed_polar = (
            require_polar
            and self._eop is not None
            and observer is not None
            and (observer.xp_arcsec is None or observer.yp_arcsec is None)
        )
        # Preserve 011 guards even when managed UT1 is added after initial scale conversion.
        if require_ut1 and ti.time_accuracy != "specified":
            return resolve(ti, strict, True)
        t = resolve(ti, strict, require_ut1 and not managed_rotation)
        if not managed_rotation and not managed_polar:
            return t
        assert self._eop is not None
        return self._eop.apply(
            t,
            dut1=managed_rotation,
            xp=bool(managed_polar and observer is not None and observer.xp_arcsec is None),
            yp=bool(managed_polar and observer is not None and observer.yp_arcsec is None),
        )

    def _physical_provenance(self, bodies: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        if self._centre_kernel is None:
            raise AriaError("DATA_UNAVAILABLE", "Physical planet-centre sources are not installed")
        return self._centre_kernel.provenance(bodies)

    def _profile_kernel(self, profile: str) -> tuple[Kernel | PhysicalCentreKernel, dict[str, int]]:
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
            result["physical_centre_sources"] = self._physical_provenance((body,))
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
                        [
                            t.shift(shift, earth_rotation=request.origin == "topocentric")
                            for t in times
                        ],
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
                            "physical_centre_sources": self._physical_provenance(request.bodies),
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
        t = self._resolve_time(
            r.time, r.strict, r.origin == "topocentric", r.observer, r.origin == "topocentric"
        )
        return self._positions(r, [t])[0]

    def birth_time_analysis(
        self, request: PositionRequest | dict[str, Any], *, samples: int = 9
    ) -> dict[str, Any]:
        """Sample an explicit symmetric TT interval; never claim continuous bounds.

        Civil input resolves once (including fold/offset); uncertainty describes
        elapsed SI seconds about that instant, not ambiguous local clock labels.
        """
        r = PositionRequest.parse(request)
        if type(samples) is not int or not 3 <= samples <= 1001 or samples % 2 != 1:
            raise AriaError("REQUEST_LIMIT", "samples must be an odd integer from 3 to 1001")
        ti = r.time
        width = ti.uncertainty_seconds
        if ti.time_accuracy != "approximate" or width is None:
            raise AriaError(
                "TIME_DATA_UNAVAILABLE", "Analysis requires an explicit approximate-time bound"
            )
        if width > DAY:
            raise AriaError("REQUEST_LIMIT", "Maximum uncertainty is plus/minus 86400 SI seconds")
        if r.origin != "geocentric" or r.observer is not None:
            raise AriaError(
                "INVALID_REQUEST", "V1 birth-time analysis supports geocentric positions only"
            )
        self._validate(r)
        centre = resolve(ti, r.strict)
        offsets = np.linspace(-width, width, samples)
        times = [centre.shift(float(x) / DAY, earth_rotation=False) for x in offsets]
        self._coverage(times)
        # TT shifts must not bypass the civil policy's validity at either edge.
        for t in (times[0], times[-1]):
            if ti.civil_policy == "historical-ut1-v1":
                assert t.ut11 is not None and t.ut12 is not None
                if not 2415020.5 <= t.ut11 + t.ut12 < 2441317.5:
                    raise AriaError(
                        "TIME_DATA_UNAVAILABLE", "Interval crosses historical policy coverage"
                    )
            elif ti.scale.upper() == "UTC":
                a, b = erfa.tttai(t.tt1, t.tt2)
                u1, u2 = erfa.taiutc(a, b)
                if u1 + u2 < 2441317.5 or (r.strict and u1 + u2 >= LEAP_EXPIRY_JD):
                    raise AriaError("TIME_DATA_UNAVAILABLE", "Interval crosses strict UTC coverage")
        rows = self._positions(r, times)
        ranges = {}
        for i, body in enumerate(r.bodies):
            anchor = rows[samples // 2].bodies[i].longitude_deg
            delta = [(row.bodies[i].longitude_deg - anchor + 180) % 360 - 180 for row in rows]
            # A relative arc avoids a false 359-to-0 almost-full-circle range.
            ranges[body] = {
                "anchor_longitude_deg": anchor,
                "sampled_offset_min_deg": min(delta),
                "sampled_offset_max_deg": max(delta),
                "sampled_rate_min_deg_day": min(
                    row.bodies[i].longitude_rate_deg_day for row in rows
                ),
                "sampled_rate_max_deg_day": max(
                    row.bodies[i].longitude_rate_deg_day for row in rows
                ),
            }
        return {
            "analysis": "birth-time-sampling-v1",
            "coverage": "all-requested-samples-evaluated",
            "interval_scale": "TT",
            "uncertainty_seconds": width,
            "input_time": centre.metadata(),
            "sample_count": samples,
            "step_seconds": 2 * width / (samples - 1),
            "continuous_bounds": False,
            "physical_uncertainty": None,
            "warnings": [
                "Sampled extrema only; between-sample extrema and sign changes may be missed",
                "No houses, angles, aspects, probabilities or physical error bounds are inferred",
                "Civil interval resolves once; supplied rotation values are not re-estimated",
            ],
            "ranges": ranges,
            "samples": [
                {"offset_seconds": float(offset), "positions": row.to_dict()}
                for offset, row in zip(offsets, rows, strict=True)
            ],
        }

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
        tt = [
            self._resolve_time(
                TimeInput.parse(t),
                r.strict,
                r.origin == "topocentric",
                r.observer,
                r.origin == "topocentric",
            )
            for t in times
        ]
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
        t = self._resolve_time(r.time, r.strict, True, observer, r.origin == "topocentric")
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
