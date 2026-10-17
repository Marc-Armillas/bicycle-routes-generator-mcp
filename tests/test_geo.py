import time

import httpx
import pytest

from mtb_routes.core.models import TrackPoint
from mtb_routes.geo.nominatim import GeocodingError, Nominatim, parse_coordinates
from mtb_routes.geo.protected_areas import OverpassProtectedAreas, group, overpass_query, parse_elements, sample
from mtb_routes.net import HttpClient


def test_parse_coordinates():
    c = parse_coordinates("41.4386, 2.0108")
    assert c and c.lat == 41.4386 and c.lon == 2.0108
    assert parse_coordinates("41.4386 2.0108")
    assert parse_coordinates("El Papiol") is None


def test_nominatim_caches_and_follows_policy(tmp_path):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, json=[{"lat": "41.4386", "lon": "2.0108", "display_name": "el Papiol, Barcelona"}])

    client = HttpClient("mtb-routes/test (contact: x@y.z)", tmp_path, intervals={}, transport=httpx.MockTransport(handler))
    geocoder = Nominatim(client, "https://nominatim.example")
    place = geocoder.search("El  Papiol")
    geocoder.search("El Papiol")
    assert place.coordinate.lat == 41.4386
    assert len(calls) == 1
    assert calls[0].headers["user-agent"].startswith("mtb-routes/")
    assert calls[0].url.params["limit"] == "1"


def test_nominatim_skips_request_for_coordinates():
    client = HttpClient("t", None, intervals={}, transport=httpx.MockTransport(lambda r: pytest.fail("no network")))
    assert Nominatim(client, "https://n.example").search("41.5,2.1").coordinate.lon == 2.1


def test_nominatim_no_results():
    client = HttpClient("t", None, intervals={}, transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[])))
    with pytest.raises(GeocodingError, match="Could not find"):
        Nominatim(client, "https://n.example").search("Nowhere at all")


def test_per_server_rate_limit():
    client = HttpClient("t", None, intervals={"n.example": 0.3},
                        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[])))
    start = time.monotonic()
    for i in range(3):
        client.request_json("GET", "https://n.example/search", params={"q": str(i)})
    assert time.monotonic() - start >= 0.6


def test_retries_transient_errors(monkeypatch):
    monkeypatch.setattr("mtb_routes.net.RETRY_DELAYS", (0.0, 0.0))
    responses = iter([httpx.Response(502), httpx.Response(200, json={"ok": True})])
    client = HttpClient("t", None, intervals={}, transport=httpx.MockTransport(lambda r: next(responses)))
    assert client.request_json("GET", "https://o.example/api") == {"ok": True}
    assert client.request_count == 2


def straight_points(n: int) -> list[TrackPoint]:
    return [TrackPoint(41.0 + i * 0.001, 2.0) for i in range(n)]  # ~111 m apart


def test_sampling_and_query():
    samples = sample(straight_points(30))
    assert samples[0][0] == 0 and samples[-1][1] == straight_points(30)[-1]
    q = overpass_query(samples[:2])
    assert q.count("is_in(") == 2 and "protected_area" in q and "make p i=1" in q


def test_parse_and_group_areas():
    elements = [
        {"type": "p", "tags": {"i": "0"}},
        {"type": "p", "tags": {"i": "1"}},
        {"type": "area", "tags": {"name": "Parc Natural de Collserola"}},
        {"type": "p", "tags": {"i": "2"}},
        {"type": "area", "tags": {"name": "Parc Natural de Collserola"}},
        {"type": "p", "tags": {"i": "3"}},
    ]
    per_sample = parse_elements(elements, 4)
    assert per_sample == [set(), {"Parc Natural de Collserola"}, {"Parc Natural de Collserola"}, set()]
    areas = group([0, 300, 600, 900], per_sample)
    assert len(areas) == 1 and areas[0].start_km == 0.3 and areas[0].end_km == 0.6


def test_group_joins_nearby_reentries_of_the_same_area():
    c, r = "Collserola", "Reserve"
    per_sample = [{c}, {c}, set(), {c, r}, set(), set(), set(), set(), set(), {c}]
    areas = group([i * 300 for i in range(10)], per_sample)
    assert [(x.name, x.start_km, x.end_km) for x in areas] == [
        (c, 0.0, 0.9), (r, 0.9, 0.9), (c, 2.7, 2.7)]


def test_overpass_end_to_end():
    def handler(req):
        assert b"is_in" in req.content
        return httpx.Response(200, json={"elements": [
            {"type": "p", "tags": {"i": "0"}},
            {"type": "area", "tags": {"name": "Reserve"}},
        ]})

    client = HttpClient("t", None, intervals={}, transport=httpx.MockTransport(handler))
    areas = OverpassProtectedAreas(client, "https://overpass.example/api/interpreter").areas_along(straight_points(5))
    assert [a.name for a in areas] == ["Reserve"]
