import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import pytest

from mtb_routes import mcp_server
from mtb_routes.config import Config
from mtb_routes.core.gpx import build_gpx
from mtb_routes.core.models import ProtectedAreaCrossing, RouteRequest
from mtb_routes.exporters import available_exporters, get_exporter
from mtb_routes.exporters.disk import file_name, safe_path
from mtb_routes.service import RouteService

from .conftest import FakeEngine, FakeGeocoder, FakeProtectedAreas

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


def test_point_to_point_route(config):
    route, n = make_service(config).generate(RouteRequest("A", 10, loop=False, end="B"))
    assert n == 1 and "point-to-point" in route.name


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
    listing = asyncio.run(mcp_server.list_routes())
    assert len(listing["routes"]) == 1 and "garmin" in listing["available_exporters"]


def test_mcp_server_exposes_tools():
    async def names():
        return {t.name for t in await mcp_server.mcp.list_tools()}

    assert {"generate_route", "list_routes"} <= asyncio.run(names())
