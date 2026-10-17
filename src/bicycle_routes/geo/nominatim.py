"""Geocoding with Nominatim (OpenStreetMap).

Usage policy: https://operations.osmfoundation.org/policies/nominatim/
- At most 1 request per second, single thread (enforced by HttpClient).
- A User-Agent that identifies the application (BIKE_CONTACT).
- Results cached on disk: the same search is never repeated.
- Attribution to OpenStreetMap (ODbL).
- No autocomplete or bulk queries. For heavy use, run your own instance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from ..core.models import Coordinate
from ..net import HttpClient, NetworkError

POLICY_URL = "https://operations.osmfoundation.org/policies/nominatim/"
_COORD_PATTERN = re.compile(r"^\s*(-?\d{1,2}(?:\.\d+)?)\s*[,; ]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


class GeocodingError(RuntimeError):
    pass


@dataclass(frozen=True)
class Place:
    coordinate: Coordinate
    name: str


class Geocoder(Protocol):
    def search(self, text: str) -> Place: ...


def parse_coordinates(text: str) -> Coordinate | None:
    """Accept 'lat,lon' (e.g. '40.4242, -3.7559'). Return None if it is not a coordinate pair."""
    m = _COORD_PATTERN.match(text)
    if not m:
        return None
    return Coordinate(float(m.group(1)), float(m.group(2)))


class Nominatim:
    def __init__(self, client: HttpClient, url: str) -> None:
        self.client = client
        self.url = url.rstrip("/")

    def search(self, text: str) -> Place:
        coord = parse_coordinates(text)
        if coord:
            return Place(coord, f"{coord.lat:.5f}, {coord.lon:.5f}")
        query = " ".join(text.split())
        if not query:
            raise GeocodingError("Empty place name")
        try:
            results = self.client.request_json(
                "GET", f"{self.url}/search",
                params={"q": query, "format": "jsonv2", "limit": "1"},
                cache_namespace="nominatim", ttl_s=90 * 24 * 3600,
            )
        except NetworkError as e:
            raise GeocodingError(f"Nominatim: {e}") from e
        if not results:
            raise GeocodingError(
                f"Could not find «{query}». Try adding more detail (town, region) or use 'lat,lon' coordinates."
            )
        r = results[0]
        return Place(Coordinate(float(r["lat"]), float(r["lon"])), r.get("display_name", query))
