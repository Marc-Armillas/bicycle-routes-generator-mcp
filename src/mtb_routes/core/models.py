"""Core data models. They do not depend on any routing engine or platform."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

TRAIL_TYPES = ("tracks", "mixed", "singletrack")


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float

    def __post_init__(self) -> None:
        if not (-90 <= self.lat <= 90 and -180 <= self.lon <= 180):
            raise ValueError(f"Coordinate out of range: {self.lat}, {self.lon}")


@dataclass(frozen=True)
class TrackPoint:
    lat: float
    lon: float
    ele: float | None = None


@dataclass(frozen=True)
class Segment:
    """Consecutive stretch sharing the same OSM tags (highway, surface, ...)."""

    distance_m: float
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class Track:
    """What a routing engine returns: geometry with elevation plus tagged segments."""

    points: list[TrackPoint]
    segments: list[Segment]
    distance_m: float
    engine: str
    profile: str
    waypoints: list[Coordinate] = field(default_factory=list)


@dataclass(frozen=True)
class RouteRequest:
    start: str
    distance_km: float
    max_climb_m: float | None = None
    trail_type: str = "mixed"
    loop: bool = True
    end: str | None = None
    name: str | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        if self.trail_type not in TRAIL_TYPES:
            raise ValueError(f"trail_type must be one of {TRAIL_TYPES}")
        if not 2 <= self.distance_km <= 200:
            raise ValueError("distance_km must be between 2 and 200")
        if not self.loop and not self.end:
            raise ValueError("A non-loop route needs an end point")
        if self.max_climb_m is not None and self.max_climb_m <= 0:
            raise ValueError("max_climb_m must be positive")


@dataclass(frozen=True)
class ProtectedAreaCrossing:
    """Protected area crossed by the route, with the stretch (km) spent inside it."""

    name: str
    start_km: float
    end_km: float


@dataclass(frozen=True)
class RouteWarning:
    kind: str  # traffic | grade | protected_area | access | technical | distance | climb | general
    message: str
    start_km: float | None = None
    end_km: float | None = None

    def to_dict(self) -> dict:
        d: dict = {"kind": self.kind, "message": self.message}
        if self.start_km is not None:
            d["start_km"] = round(self.start_km, 2)
        if self.end_km is not None:
            d["end_km"] = round(self.end_km, 2)
        return d


@dataclass
class Summary:
    distance_km: float
    ascent_m: float
    descent_m: float
    min_elevation_m: float | None
    max_elevation_m: float | None
    max_uphill_grade_pct: float
    max_downhill_grade_pct: float
    surface_pct: dict[str, float]  # paved / track / path / unknown
    warnings: list[RouteWarning] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "distance_km": round(self.distance_km, 1),
            "ascent_m": round(self.ascent_m),
            "descent_m": round(self.descent_m),
            "min_elevation_m": None if self.min_elevation_m is None else round(self.min_elevation_m),
            "max_elevation_m": None if self.max_elevation_m is None else round(self.max_elevation_m),
            "max_uphill_grade_pct": round(self.max_uphill_grade_pct, 1),
            "max_downhill_grade_pct": round(self.max_downhill_grade_pct, 1),
            "surface_pct": {k: round(v, 1) for k, v in self.surface_pct.items()},
            "warnings": [w.to_dict() for w in self.warnings],
        }


@dataclass
class Route:
    name: str
    start: Coordinate
    start_name: str
    track: Track
    summary: Summary
    request: RouteRequest
    gpx_file: Path | None = None
