"""Test doubles: simulated routing engine, geocoder and protected areas (no network)."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from mtb_routes.config import Config
from mtb_routes.core.analysis import distance_m
from mtb_routes.core.models import Coordinate, ProtectedAreaCrossing, Segment, Track, TrackPoint
from mtb_routes.engines.base import EngineError
from mtb_routes.geo.nominatim import Place

FIXTURES = Path(__file__).parent / "fixtures"
PAPIOL = Coordinate(41.4386, 2.0108)


class FakeEngine:
    """Joins the points with straight lines every ~50 m, plus 25 % simulated detour.

    Sinusoidal elevation; the first 10 % of each leg is a paved street and the rest a track.
    """

    name = "fake"

    def __init__(self, initial_failures: int = 0, detour: float = 1.25) -> None:
        self.calls: list[list[Coordinate]] = []
        self.pending_failures = initial_failures
        self.detour = detour

    def route(self, points: list[Coordinate], trail_type: str) -> Track:
        self.calls.append(list(points))
        if self.pending_failures > 0:
            self.pending_failures -= 1
            raise EngineError("point far from any trail")
        pts: list[TrackPoint] = []
        segments: list[Segment] = []
        travelled = 0.0
        for a, b in zip(points, points[1:]):
            d = distance_m(a.lat, a.lon, b.lat, b.lon)
            n = max(1, int(d / 50))
            for k in range(n):
                t = k / n
                pts.append(TrackPoint(a.lat + t * (b.lat - a.lat), a.lon + t * (b.lon - a.lon),
                                      150 + 40 * math.sin((travelled + t * d) / 800)))
            travelled += d
            real = d * self.detour
            segments += [
                Segment(real * 0.1, {"highway": "residential", "surface": "asphalt"}),
                Segment(real * 0.9, {"highway": "track", "tracktype": "grade3"}),
            ]
        last = points[-1]
        pts.append(TrackPoint(last.lat, last.lon, 150 + 40 * math.sin(travelled / 800)))
        return Track(pts, segments, travelled * self.detour, "fake", trail_type, list(points))


class FakeGeocoder:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, text: str) -> Place:
        self.queries.append(text)
        return Place(PAPIOL, "El Papiol, Baix Llobregat, Barcelona, Catalonia, Spain")


class FakeProtectedAreas:
    def __init__(self, areas: list[ProtectedAreaCrossing] | None = None) -> None:
        self.areas = areas or []

    def areas_along(self, points):
        return self.areas


@pytest.fixture
def config(tmp_path: Path) -> Config:
    return Config(gpx_dir=tmp_path / "gpx", data_dir=tmp_path / "gpx" / ".mtb-routes", contact="test@example.com")


@pytest.fixture
def engine() -> FakeEngine:
    return FakeEngine()
