"""BRouter engine (https://github.com/abrensch/brouter, MIT). No key needed; public or local server."""

from __future__ import annotations

from typing import Any

from ..core.analysis import cumulative_distances
from ..core.models import Coordinate, Segment, Track, TrackPoint
from ..net import HttpClient, NetworkError
from .base import EngineError

# Standard BRouter profile per trail type. Compared on real loops near Barcelona, `mtb`
# gives clearly less pavement and traffic than `gravel`, `trekking` or `MTB_SB_light`;
# the differences between trail types come from its variables. For road, `fastbike` gives
# 87-100 % pavement (`mtb`: 28-49 %).
PROFILES = {
    "tracks": "mtb",
    "mixed": "mtb",
    "singletrack": "mtb",
    "road": "fastbike",
}

# Variables of the mtb profile shared by all MTB trail types. See mtb.brf.
MTB_VARIABLES = {
    "StrictNOBicycleaccess": "1",  # never use ways tagged bicycle=no
    "avoid_unsafe": "1",           # penalise main roads without cycling infrastructure
}

# Profile variables overridden per request, by trail type.
VARIABLES: dict[str, dict[str, str]] = {
    "tracks": {**MTB_VARIABLES, "hills": "1"},                  # penalise climbs >3 %: a bit less singletrack and climbing
    "mixed": MTB_VARIABLES,
    "singletrack": {**MTB_VARIABLES, "path_preference": "80"},  # more singletrack, less pavement (default 20)
    # fastbike.brf: avoiding roads that usually have traffic is "very important" (same routes as
    # fastbike-lowtraffic; on real loops it halved the km on busy roads in one case out of two).
    "road": {"consider_traffic": "1"},
}

IGNORED_TAGS = {"reversedirection"}


def parse_tags(text: str) -> dict[str, str]:
    tags = {}
    for pair in text.split():
        key, _, value = pair.partition("=")
        if key and key not in IGNORED_TAGS:
            tags[key] = value
    return tags


def parse_geojson(data: dict[str, Any], profile: str, waypoints: list[Coordinate]) -> Track:
    try:
        feature = data["features"][0]
        coords = feature["geometry"]["coordinates"]
        props = feature["properties"]
    except (KeyError, IndexError, TypeError) as e:
        raise EngineError(f"Unexpected BRouter response: {e}") from e

    points = [TrackPoint(lat=c[1], lon=c[0], ele=c[2] if len(c) > 2 else None) for c in coords]
    messages = props.get("messages") or []
    segments: list[Segment] = []
    if messages:
        header = messages[0]
        i_dist, i_tags = header.index("Distance"), header.index("WayTags")
        for row in messages[1:]:
            segments.append(Segment(float(row[i_dist]), parse_tags(row[i_tags])))
    distance = float(props.get("track-length") or 0) or cumulative_distances(points)[-1]
    if not segments:
        segments = [Segment(distance, {})]
    return Track(points, segments, distance, engine="brouter", profile=profile, waypoints=list(waypoints))


class BRouterEngine:
    name = "brouter"

    def __init__(
        self,
        client: HttpClient,
        url: str,
        profiles: dict[str, str] | None = None,
        variables: dict[str, dict[str, str]] | None = None,
    ) -> None:
        self.client = client
        self.url = url.rstrip("/")
        self.profiles = profiles or PROFILES
        self.variables = VARIABLES if variables is None else variables

    def route(self, points: list[Coordinate], trail_type: str) -> Track:
        if len(points) < 2:
            raise EngineError("At least two points are needed")
        profile = self.profiles[trail_type]
        params = {
            "lonlats": "|".join(f"{p.lon:.6f},{p.lat:.6f}" for p in points),
            "profile": profile,
            "alternativeidx": "0",
            "format": "geojson",
        }
        # Profile variables overridden in the URL (e.g. profile:StrictNOBicycleaccess=1).
        for key, value in self.variables.get(trail_type, {}).items():
            params[f"profile:{key}"] = value
        try:
            data = self.client.request_json("GET", f"{self.url}/brouter", params=params, cache_namespace="brouter")
        except NetworkError as e:
            raise EngineError(f"BRouter: {e}") from e
        return parse_geojson(data, profile, points)
