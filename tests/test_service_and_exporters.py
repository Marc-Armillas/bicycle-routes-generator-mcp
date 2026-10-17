import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pytest

from mtb_routes import mcp_server
from mtb_routes.config import Config
from mtb_routes.core.gpx import build_gpx
from mtb_routes.core.loop import offset
from mtb_routes.core.models import ProtectedAreaCrossing, RouteRequest
from mtb_routes.engines.base import EngineError
from mtb_routes.exporters import available_exporters, get_exporter
from mtb_routes.exporters.disk import file_name, safe_path
from mtb_routes.geo.nominatim import Place
from mtb_routes.service import RouteService

from .conftest import PAPIOL, FakeEngine, FakeGeocoder, FakeProtectedAreas

NS = {"g": "http://www.topografix.com/GPX/1/1"}


def make_service(config, areas=None) -> RouteService:
    return RouteService(config, engine=FakeEngine(), geocoder=FakeGeocoder(), protected_areas=areas or FakeProtectedAreas())


def test_config_from_env(tmp_path):
    c = Config.from_env({"MTB_GPX_DIR": str(tmp_path), "MTB_CONTACT": "a@b.c", "MTB_PROTECTED_AREAS": "0"})
    assert c.gpx_dir == tmp_path.resolve()
    assert c.data_dir == tmp_path.resolve() / ".mtb-routes"
    assert c.engine == "brouter" and not c.protected_areas
    assert "a@b.c" in c.user_agent and c.user_agent.isascii()
    assert Config.from_env({}).gpx_dir == Path("/tmp/mtb-routes").resolve()
    unsubstituted = Config.from_env({"ORS_API_KEY": "${user_config.ors_api_key}", "MTB_ENGINE": "${user_config.engine}"})
    assert unsubstituted.ors_api_key is None and unsubstituted.engine == "brouter"


def test_request_validation():
    with pytest.raises(ValueError):
        RouteRequest("x", 25, trail_type="motorway")
    with pytest.raises(ValueError):
        RouteRequest("x", 25, loop=False)
    with pytest.raises(ValueError):
        RouteRequest("x", 1000)
    with pytest.raises(ValueError):
        RouteRequest("x", 25, via=("A", "  "))
    with pytest.raises(ValueError):
        RouteRequest("x", 25, via=tuple(f"P{i}" for i in range(11)))
    assert RouteRequest("x", 25, via=[" A ", "B"]).via == ("A", "B")


def test_generate_and_save_full_route(config):
    service = make_service(config, FakeProtectedAreas([ProtectedAreaCrossing("Parc Natural de Collserola", 2.0, 5.0)]))
    result = service.generate_and_save(RouteRequest("el papiol", 25, trail_type="tracks", seed=1))
    d = result.to_dict()
    assert d["name"] == "MTB El Papiol 25 km loop"
    assert abs(d["summary"]["distance_km"] - 25) <= 2.5
    assert result.candidates_evaluated == 6
    assert any(w["kind"] == "protected_area" for w in d["summary"]["warnings"])
    assert d["summary"]["warnings"][-1]["kind"] == "general"
    assert "OpenStreetMap" in d["attribution"]

    gpx = result.route.gpx_file
    assert gpx and gpx.parent == config.gpx_dir.resolve() and gpx.suffix == ".gpx"
    root = ET.parse(gpx).getroot()
    assert root.find("g:metadata/g:copyright", NS).get("author") == "OpenStreetMap contributors"
    pts = root.findall(".//g:trkpt", NS)
    assert len(pts) > 100 and pts[0].find("g:ele", NS) is not None

    listing = service.list_routes()
    assert listing[0]["file"] == str(gpx) and listing[0]["exists"]


def test_road_route(config):
    result = make_service(config).generate_and_save(RouteRequest("el papiol", 40, trail_type="road", seed=1))
    d = result.to_dict()
    assert d["name"].startswith("Road El Papiol ") and d["activity_type"] == "road_biking"
    assert ET.parse(result.route.gpx_file).getroot().find("g:trk/g:type", NS).text == "road_biking"
    mtb = make_service(config).generate_and_save(RouteRequest("el papiol", 20, seed=1)).to_dict()
    assert mtb["activity_type"] == "mountain_biking"


def test_point_to_point_route(config):
    route, n = make_service(config).generate(RouteRequest("A", 10, loop=False, end="B"))
    assert n == 1 and "point-to-point" in route.name


class ViaGeocoder(FakeGeocoder):
    """Each place name maps to a distinct point east of El Papiol."""

    def search(self, text: str) -> Place:
        self.queries.append(text)
        return Place(offset(PAPIOL, 1000 * len(self.queries), 90), text)


def test_loop_through_via_points_in_order(config):
    engine, geocoder = FakeEngine(), ViaGeocoder()
    service = RouteService(config, engine=engine, geocoder=geocoder, protected_areas=FakeProtectedAreas())
    result = service.generate_and_save(RouteRequest("Start", 20, via=("A", "B")))
    assert geocoder.queries == ["Start", "A", "B"]
    start, a, b = (offset(PAPIOL, 1000 * k, 90) for k in (1, 2, 3))
    assert engine.calls == [[start, a, b, start]]
    d = result.to_dict()
    assert [v["name"] for v in d["via"]] == ["A", "B"]
    assert result.candidates_evaluated == 1
    distance = next(w for w in d["summary"]["warnings"] if w["kind"] == "distance")
    assert "via points" in distance["message"]


def test_point_to_point_through_via_points(config):
    engine = FakeEngine()
    service = RouteService(config, engine=engine, geocoder=ViaGeocoder(), protected_areas=FakeProtectedAreas())
    route, _ = service.generate(RouteRequest("A", 10, loop=False, end="C", via=("B",)))
    assert len(engine.calls[0]) == 3 and engine.calls[0][0] != engine.calls[0][-1]
    assert [n for n, _ in route.via] == ["B"]


def test_via_point_far_from_trails_explains_error(config):
    service = RouteService(config, engine=FakeEngine(initial_failures=1), geocoder=ViaGeocoder(),
                           protected_areas=FakeProtectedAreas())
    with pytest.raises(EngineError, match="via points"):
        service.generate(RouteRequest("A", 10, via=("B",)))


def test_safe_file_name(tmp_path):
    n = file_name("MTB Sant Cugat · route/../../etc", datetime(2026, 10, 17, 9, 30))
    assert n == "mtb-sant-cugat-route-etc-20261017-093000.gpx"
    with pytest.raises(ValueError):
        safe_path(tmp_path, "../outside.gpx")


def test_registered_exporters_and_pending_wahoo(config):
    assert {"disk", "garmin", "wahoo"} <= set(available_exporters())
    route, _ = make_service(config).generate(RouteRequest("x", 10, seed=2))
    assert not get_exporter("wahoo").export(route, config).ok
    with pytest.raises(ValueError):
        get_exporter("komoot")


def test_unconfigured_garmin_explains_alternative(config):
    service = make_service(config)
    route, _ = service.generate(RouteRequest("x", 10, seed=2))
    results = service.export(route, ["garmin"])
    assert [r.exporter for r in results] == ["disk", "garmin"]
    assert results[0].ok and not results[1].ok and "upload_course" in results[1].message


def test_gpx_escapes_characters(config):
    route, _ = make_service(config).generate(RouteRequest("x", 10, seed=2, name="Route <A & B>"))
    xml = build_gpx(route)
    assert "Route &lt;A &amp; B&gt;" in xml
    ET.fromstring(xml.encode())


def test_mcp_tools(config, monkeypatch):
    monkeypatch.setattr(mcp_server, "_service", make_service(config))
    d = asyncio.run(mcp_server.generate_route("El Papiol", 15, trail_type="mixed", seed=5))
    assert d["gpx_file"].endswith(".gpx") and "summary" in d
    error = asyncio.run(mcp_server.generate_route("El Papiol", 15, loop=False))
    assert "error" in error
    via = asyncio.run(mcp_server.generate_route("El Papiol", 15, via=["Castellbisbal"]))
    assert [v["name"] for v in via["via"]] == ["El Papiol, Baix Llobregat, Barcelona, Catalonia, Spain"]
    road = asyncio.run(mcp_server.generate_route("El Papiol", 40, trail_type="road", seed=5))
    assert road["activity_type"] == "road_biking"
    listing = asyncio.run(mcp_server.list_routes())
    assert len(listing["routes"]) == 3 and "garmin" in listing["available_exporters"]


def test_mcp_server_exposes_tools():
    async def names():
        return {t.name for t in await mcp_server.mcp.list_tools()}

    assert {"generate_route", "list_routes"} <= asyncio.run(names())
