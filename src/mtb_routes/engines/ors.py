"""OpenRouteService engine (optional). Requires ORS_API_KEY (free: 2,000 routes/day)."""

from __future__ import annotations

from typing import Any

from ..core.analysis import cumulative_distances
from ..core.models import Coordinate, Segment, Track, TrackPoint
from ..net import HttpClient, NetworkError
from .base import EngineError

ORS_URL = "https://api.openrouteservice.org"
PROFILE = "cycling-mountain"

# ORS `extra_info` codes translated into equivalent OSM tags, so the analysis is the
# same whatever the engine.
WAYTYPE = {
    1: {"highway": "primary"},      # State Road
    2: {"highway": "tertiary"},     # Road (secondary/tertiary/unclassified): warned about to be safe
    3: {"highway": "residential"},  # Street
    4: {"highway": "path"},
    5: {"highway": "track"},
    6: {"highway": "cycleway"},
    7: {"highway": "footway"},
    8: {"highway": "steps"},
    9: {"route": "ferry"},
}
SURFACE = {
    1: "paved", 2: "unpaved", 3: "asphalt", 4: "concrete", 5: "cobblestone", 6: "metal",
    7: "wood", 8: "compacted", 9: "fine_gravel", 10: "gravel", 11: "dirt", 12: "ground",
    13: "ice", 14: "paving_stones", 15: "sand", 16: "woodchips", 17: "grass", 18: "grass_paver",
}
DIFFICULTY_OFFSET = 1  # traildifficulty on bike profiles: 1 = mtb:scale 0, 2 = mtb:scale 1...


def _tags(extras: dict[str, Any], index: int) -> dict[str, str]:
    tags: dict[str, str] = {}
    for name, info in extras.items():
        for start, end, value in info.get("values", []):
            if start <= index < end:
                if name == "waytype":
                    tags.update(WAYTYPE.get(value, {}))
                elif name == "surface" and value in SURFACE:
                    tags["surface"] = SURFACE[value]
                elif name == "traildifficulty" and value >= DIFFICULTY_OFFSET:
                    tags["mtb:scale"] = str(value - DIFFICULTY_OFFSET)
                break
    return tags


def parse_geojson(data: dict[str, Any], waypoints: list[Coordinate]) -> Track:
    try:
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        props = feature["properties"]
    except (KeyError, IndexError, TypeError) as e:
        raise EngineError(f"Unexpected OpenRouteService response: {e}") from e

    points = [TrackPoint(lat=c[1], lon=c[0], ele=c[2] if len(c) > 2 else None) for c in coords]
    cumulative = cumulative_distances(points)
    extras = props.get("extras") or {}
    breaks = sorted({0, len(points) - 1} | {
        i for info in extras.values() for start, end, _ in info.get("values", []) for i in (start, end)
    })
    segments: list[Segment] = []
    for a, b in zip(breaks, breaks[1:]):
        if b <= a:
            continue
        tags = _tags(extras, a)
        dist = cumulative[b] - cumulative[a]
        if segments and segments[-1].tags == tags:
            segments[-1] = Segment(segments[-1].distance_m + dist, tags)
        else:
            segments.append(Segment(dist, tags))
    distance = float(props.get("summary", {}).get("distance") or cumulative[-1])
    return Track(points, segments or [Segment(distance, {})], distance, "ors", PROFILE, list(waypoints))


class ORSEngine:
    name = "ors"

    def __init__(self, client: HttpClient, api_key: str, url: str = ORS_URL) -> None:
        if not api_key:
            raise EngineError("ORS_API_KEY is required to use OpenRouteService")
        self.client = client
        self.api_key = api_key
        self.url = url.rstrip("/")

    def route(self, points: list[Coordinate], trail_type: str) -> Track:
        body: dict[str, Any] = {
            "coordinates": [[p.lon, p.lat] for p in points],
            "elevation": True,
            "instructions": False,
            "extra_info": ["surface", "waytype", "traildifficulty"],
            "options": {"avoid_features": ["ferries"]},
        }
        if trail_type == "tracks":
            body["options"]["profile_params"] = {"weightings": {"steepness_difficulty": 1}}
        try:
            data = self.client.request_json(
                "POST", f"{self.url}/v2/directions/{PROFILE}/geojson",
                json_body=body, headers={"Authorization": self.api_key}, cache_namespace="ors",
            )
        except NetworkError as e:
            raise EngineError(f"OpenRouteService: {e}") from e
        return parse_geojson(data, points)
