import json

import httpx
import pytest

from bicycle_routes.core.analysis import analyze
from bicycle_routes.core.models import Coordinate, RouteRequest
from bicycle_routes.engines.base import EngineError
from bicycle_routes.engines.brouter import BRouterEngine, parse_tags
from bicycle_routes.engines.ors import ORSEngine
from bicycle_routes.net import HttpClient

from .conftest import FIXTURES, MADRID

END = Coordinate(40.44, -3.74)


def client_with(handler, tmp_path=None) -> HttpClient:
    return HttpClient("test", tmp_path, intervals={}, transport=httpx.MockTransport(handler))


def test_parse_tags_drops_reversedirection():
    assert parse_tags("reversedirection=yes highway=track surface=gravel") == {
        "highway": "track", "surface": "gravel"}


def test_brouter_parses_real_response():
    requests = []

    def handler(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        return httpx.Response(200, content=(FIXTURES / "brouter_sample.json").read_bytes())

    t = BRouterEngine(client_with(handler), "https://brouter.example").route([MADRID, END], "mixed")
    q = requests[0].url.params
    assert q["profile"] == "mtb" and q["format"] == "geojson" and q["lonlats"].startswith("-3.755900,40.424200|")
    assert q["profile:StrictNOBicycleaccess"] == "1" and "profile:path_preference" not in q
    assert requests[0].headers["user-agent"] == "test"
    assert t.distance_m == 2983
    assert all(p.ele is not None for p in t.points)
    assert abs(sum(s.distance_m for s in t.segments) - 2983) < 1
    s = analyze(t, RouteRequest("x", 3))
    assert s.surface_pct["path"] > 30 and s.surface_pct["track"] > 30
    assert any(w.kind == "access" for w in s.warnings)   # bicycle=no stretches in the fixture
    assert any(w.kind == "traffic" for w in s.warnings)  # tertiary road stretch


def test_brouter_road_uses_fastbike_without_mtb_variables():
    requests = []

    def handler(req: httpx.Request) -> httpx.Response:
        requests.append(req)
        return httpx.Response(200, content=(FIXTURES / "brouter_sample.json").read_bytes())

    t = BRouterEngine(client_with(handler), "https://brouter.example").route([MADRID, END], "road")
    q = requests[0].url.params
    assert q["profile"] == "fastbike" and q["profile:consider_traffic"] == "1"
    assert "profile:StrictNOBicycleaccess" not in q and "profile:avoid_unsafe" not in q
    assert t.profile == "fastbike"


def test_brouter_server_error():
    def handler(req):
        return httpx.Response(500, text="from-position not mapped in existing datafile")

    with pytest.raises(EngineError, match="not mapped"):
        BRouterEngine(client_with(handler), "https://b.example").route([MADRID, END], "tracks")


def test_brouter_uses_disk_cache(tmp_path):
    calls = []

    def handler(req):
        calls.append(req)
        return httpx.Response(200, content=(FIXTURES / "brouter_sample.json").read_bytes())

    engine = BRouterEngine(client_with(handler, tmp_path), "https://b.example")
    engine.route([MADRID, END], "mixed")
    engine.route([MADRID, END], "mixed")
    assert len(calls) == 1


def ors_response() -> dict:
    coords = [[-3.7559 + i * 0.001, 40.4242, 100 + i] for i in range(11)]
    return {"features": [{
        "geometry": {"coordinates": coords},
        "properties": {
            "summary": {"distance": 835.0},
            "extras": {
                "waytype": {"values": [[0, 3, 3], [3, 10, 5]]},
                "surface": {"values": [[0, 3, 3], [3, 7, 10], [7, 10, 11]]},
                "traildifficulty": {"values": [[0, 10, 0]]},
            },
        },
    }]}


def test_ors_translates_extras_to_osm_tags():
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json=ors_response())

    t = ORSEngine(client_with(handler), "fake-key").route([MADRID, END], "tracks")
    body = json.loads(seen[0].content)
    assert seen[0].headers["authorization"] == "fake-key"
    assert "cycling-mountain" in str(seen[0].url) and body["elevation"] is True
    assert t.distance_m == 835.0
    assert [s.tags for s in t.segments] == [
        {"highway": "residential", "surface": "asphalt"},
        {"highway": "track", "surface": "gravel"},
        {"highway": "track", "surface": "dirt"},
    ]


def test_ors_road_profile():
    seen = []

    def handler(req):
        seen.append(req)
        return httpx.Response(200, json=ors_response())

    t = ORSEngine(client_with(handler), "fake-key").route([MADRID, END], "road")
    assert "/cycling-road/" in str(seen[0].url) and t.profile == "cycling-road"
    assert "profile_params" not in json.loads(seen[0].content)["options"]


def test_ors_requires_key():
    with pytest.raises(EngineError, match="ORS_API_KEY"):
        ORSEngine(client_with(lambda r: httpx.Response(200)), "")
