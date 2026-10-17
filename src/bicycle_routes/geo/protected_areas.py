"""Detection of protected areas crossed by the route, using the Overpass API (OSM data).

The route is sampled every ~300 m and Overpass is asked which protected areas
(`boundary=protected_area`, `leisure=nature_reserve`, `boundary=national_park`) each
sample falls in. One query per block of points, with cached results.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from ..core.analysis import cumulative_distances
from ..core.models import ProtectedAreaCrossing, TrackPoint
from ..net import HttpClient

SAMPLE_STEP_M = 300.0
POINTS_PER_QUERY = 60


class ProtectedAreaProvider(Protocol):
    def areas_along(self, points: Sequence[TrackPoint]) -> list[ProtectedAreaCrossing]: ...


def sample(points: Sequence[TrackPoint], step: float = SAMPLE_STEP_M) -> list[tuple[float, TrackPoint]]:
    cumulative = cumulative_distances(points)
    samples, next_at = [], 0.0
    for d, p in zip(cumulative, points):
        if d >= next_at:
            samples.append((d, p))
            next_at = d + step
    if points and samples[-1][1] is not points[-1]:
        samples.append((cumulative[-1], points[-1]))
    return samples


def overpass_query(samples: Sequence[tuple[float, TrackPoint]]) -> str:
    parts = ["[out:json][timeout:90];"]
    for i, (_, p) in enumerate(samples):
        parts.append(
            f"make p i={i};out;"
            f"is_in({p.lat:.5f},{p.lon:.5f})->.a;"
            '(area.a["boundary"="protected_area"];area.a["leisure"="nature_reserve"];'
            'area.a["boundary"="national_park"];);out tags;'
        )
    return "".join(parts)


def parse_elements(elements: list[dict], n_samples: int) -> list[set[str]]:
    """Turn the response into, for each sample, the set of area names it falls in."""
    per_sample: list[set[str]] = [set() for _ in range(n_samples)]
    current = -1
    for e in elements:
        tags = e.get("tags", {})
        if e.get("type") == "p":
            current = int(tags.get("i", -1))
        elif e.get("type") == "area" and 0 <= current < n_samples:
            name = tags.get("name:en") or tags.get("name") or tags.get("protection_title") or "unnamed protected area"
            per_sample[current].add(name)
    return per_sample


def group(
    distances: Sequence[float], per_sample: Sequence[set[str]], max_gap_km: float = 1.0
) -> list[ProtectedAreaCrossing]:
    """Stretches inside each area; joins exits and re-entries of the same area less than max_gap_km apart."""
    merged: list[ProtectedAreaCrossing] = []
    for c in _crossings(distances, per_sample):
        previous = next((m for m in reversed(merged) if m.name == c.name), None)
        if previous and c.start_km - previous.end_km <= max_gap_km:
            merged[merged.index(previous)] = ProtectedAreaCrossing(c.name, previous.start_km, c.end_km)
        else:
            merged.append(c)
    return merged


def _crossings(distances: Sequence[float], per_sample: Sequence[set[str]]) -> list[ProtectedAreaCrossing]:
    crossings: list[ProtectedAreaCrossing] = []
    open_areas: dict[str, float] = {}
    previous = 0.0
    for d, names in zip(distances, per_sample):
        for n in list(open_areas):
            if n not in names:
                crossings.append(ProtectedAreaCrossing(n, open_areas.pop(n) / 1000, previous / 1000))
        for n in names:
            open_areas.setdefault(n, d)
        previous = d
    crossings += [ProtectedAreaCrossing(n, start / 1000, previous / 1000) for n, start in open_areas.items()]
    return sorted(crossings, key=lambda c: c.start_km)


class OverpassProtectedAreas:
    def __init__(self, client: HttpClient, url: str) -> None:
        self.client = client
        self.url = url

    def areas_along(self, points: Sequence[TrackPoint]) -> list[ProtectedAreaCrossing]:
        samples = sample(points)
        per_sample: list[set[str]] = []
        for i in range(0, len(samples), POINTS_PER_QUERY):
            block = samples[i : i + POINTS_PER_QUERY]
            data = self.client.request_json(
                "POST", self.url, data={"data": overpass_query(block)},
                cache_namespace="overpass", ttl_s=30 * 24 * 3600,
            )
            per_sample += parse_elements(data.get("elements", []), len(block))
        return group([d for d, _ in samples], per_sample)
