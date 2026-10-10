# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 DioneGate
"""Immutable, serialisable requests and results."""

import math
from dataclasses import asdict, dataclass, field
from typing import Any

from .errors import AriaError

BODY_IDS = {
    "sun": 10,
    "moon": 301,
    "mercury": 199,
    "venus": 299,
    "earth": 399,
    "mars": 4,
    "jupiter": 5,
    "saturn": 6,
    "uranus": 7,
    "neptune": 8,
    "pluto": 9,
}
DEFAULT_BODIES = tuple(b for b in BODY_IDS if b != "earth")


@dataclass(frozen=True)
class TimeInput:
    value: str | None = None
    scale: str = "UTC"
    jd: tuple[float, float] | None = None
    timezone: str | None = None
    fold: int | None = None
    dut1_seconds: float | None = None
    delta_t_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.jd is not None:
            if len(self.jd) != 2 or not all(math.isfinite(float(x)) for x in self.jd):
                raise AriaError("INVALID_REQUEST", "jd requires two finite components")
            object.__setattr__(self, "jd", tuple(float(x) for x in self.jd))
        for x in (self.dut1_seconds, self.delta_t_seconds):
            if x is not None and not math.isfinite(x):
                raise AriaError("INVALID_REQUEST", "Time offsets must be finite")
        if self.dut1_seconds is not None and self.delta_t_seconds is not None:
            raise AriaError("INVALID_REQUEST", "Supply DUT1 or delta-T, not both")

    @classmethod
    def parse(cls, value: Any) -> "TimeInput":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(value=value)
        if isinstance(value, dict):
            d = dict(value)
            if d.get("jd") is not None:
                if len(d["jd"]) != 2:
                    raise AriaError("INVALID_REQUEST", "jd requires two components")
                d["jd"] = tuple(d["jd"])
            return cls(**d)
        raise AriaError("INVALID_REQUEST", "time must be a TimeInput, ISO string or mapping")


@dataclass(frozen=True)
class Observer:
    latitude_deg: float
    longitude_deg: float
    elevation_m: float = 0.0
    xp_arcsec: float | None = None
    yp_arcsec: float | None = None

    def __post_init__(self) -> None:
        for x in (
            self.latitude_deg,
            self.longitude_deg,
            self.elevation_m,
            self.xp_arcsec,
            self.yp_arcsec,
        ):
            if x is not None and not math.isfinite(x):
                raise AriaError("INVALID_REQUEST", "Observer values must be finite")
        if not -90 <= self.latitude_deg <= 90 or not -180 <= self.longitude_deg <= 180:
            raise AriaError("INVALID_REQUEST", "Observer latitude/longitude out of range")


@dataclass(frozen=True)
class PositionRequest:
    time: TimeInput
    bodies: tuple[str, ...] = DEFAULT_BODIES
    origin: str = "geocentric"
    frame: str = "true_ecliptic_of_date"
    position_mode: str = "apparent"
    observer: Observer | None = None
    strict: bool = True
    stationary_band_deg_day: float = 0.0001
    zodiac: str = "tropical"
    dataset_id: str | None = None
    profile: str = "reference"

    def __post_init__(self) -> None:
        if not isinstance(self.strict, bool):
            raise AriaError("INVALID_REQUEST", "strict must be boolean")
        object.__setattr__(self, "time", TimeInput.parse(self.time))
        object.__setattr__(self, "bodies", tuple(self.bodies))

    @classmethod
    def parse(cls, value: Any) -> "PositionRequest":
        if isinstance(value, cls):
            return value
        d = dict(value)
        if d.get("observer") is not None and not isinstance(d["observer"], Observer):
            d["observer"] = Observer(**d["observer"])
        if isinstance(d.get("zodiac"), dict):
            d["zodiac"] = d["zodiac"]["type"]
        return cls(**d)


@dataclass(frozen=True)
class BodyPosition:
    body: str
    target_id: int
    centre_id: int
    target_kind: str
    longitude_deg: float
    latitude_deg: float
    distance_au: float
    right_ascension_deg: float
    declination_deg: float
    longitude_rate_deg_day: float
    motion: str
    vector_icrs_au: tuple[float, float, float]


@dataclass(frozen=True)
class PositionsResult:
    metadata: dict[str, Any]
    bodies: tuple[BodyPosition, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AspectRule:
    angle_deg: float
    orb_deg: float = 6.0


@dataclass(frozen=True)
class Aspect:
    body_a: str
    body_b: str
    angle_deg: float
    separation_deg: float
    residual_deg: float
    status: str


@dataclass(frozen=True)
class ChartResult:
    positions: PositionsResult
    angles_deg: dict[str, float]
    house_cusps_deg: tuple[float, ...]
    house_system: str
    houses: dict[str, int]
    signs: dict[str, dict[str, Any]]
    aspects: tuple[Aspect, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventRequest:
    start: TimeInput
    end: TimeInput
    kind: str
    body: str
    other_body: str | None = None
    angle_deg: float = 0.0
    tolerance_seconds: float = 0.1
    max_step_days: float = 0.25
    max_evaluations: int = 200000
    strict: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.strict, bool):
            raise AriaError("INVALID_REQUEST", "strict must be boolean")
        object.__setattr__(self, "start", TimeInput.parse(self.start))
        object.__setattr__(self, "end", TimeInput.parse(self.end))


@dataclass(frozen=True)
class Event:
    kind: str
    body: str
    other_body: str | None
    jd_tt: tuple[float, float]
    residual: float
    iterations: int
    time_bracket_seconds: float
    conditioning: str
    metadata: dict[str, Any]
