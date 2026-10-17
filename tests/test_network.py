"""Test against the real services (Nominatim, BRouter, Overpass). Disabled by default.

Run with:  uv run pytest -m network
"""

import pytest

from bicycle_routes.config import Config
from bicycle_routes.core.models import RouteRequest
from bicycle_routes.service import RouteService


@pytest.mark.network
def test_real_route_from_el_papiol(tmp_path):
    config = Config.from_env({"BIKE_GPX_DIR": str(tmp_path)})
    service = RouteService(config)
    try:
        result = service.generate_and_save(RouteRequest("El Papiol", 15, seed=2026))
    finally:
        service.close()
    s = result.route.summary
    assert 12 <= s.distance_km <= 19
    assert s.ascent_m > 0
    assert result.route.gpx_file and result.route.gpx_file.exists()
