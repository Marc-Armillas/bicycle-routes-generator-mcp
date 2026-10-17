"""Local MCP server (stdio) for Claude Desktop and Claude Code."""

from __future__ import annotations

import logging
from typing import Annotated, Any, Literal

import anyio
from mcp.server.mcpserver import MCPServer
from pydantic import Field

from . import __version__
from .config import load_config
from .core.models import MAX_VIA_POINTS, RouteRequest
from .engines.base import EngineError
from .exporters import available_exporters
from .geo.nominatim import POLICY_URL, GeocodingError
from .service import RouteService

INSTRUCTIONS = f"""\
mtb-routes generates mountain bike routes on real OpenStreetMap trails (BRouter or
OpenRouteService engine) and saves them as GPX with elevation.

Rules:
- Never invent coordinates or tracks: always use generate_route. Pass the place as the user
  says it (or 'lat,lon' if they give coordinates).
- If the user names places the route must pass through, pass them in `via`, in the order
  they will be ridden. With via points the distance comes from them, not from distance_km.
- Show the user the summary and ALL warnings (traffic, grades >12 %, protected areas,
  access), remind them that the elevation model's climbing may differ from a barometric
  watch and that they must check the route before riding.
- To send the route to Garmin Connect, if the Garmin MCP server is available, call its
  upload_course tool with gpx_path = gpx_file, activity_type = "mountain_biking",
  course_name = the route name (max 128 characters) and a short description (max 512).
- Place lookup uses Nominatim (OpenStreetMap), limited to 1 request per second and no bulk
  queries: {POLICY_URL}
- Data © OpenStreetMap contributors (ODbL).
"""

mcp = MCPServer("mtb-routes", instructions=INSTRUCTIONS, version=__version__)
_service: RouteService | None = None


def _get_service() -> RouteService:
    global _service
    if _service is None:
        _service = RouteService(load_config())
    return _service


@mcp.tool()
async def generate_route(
    start: Annotated[str, Field(description="Start location: place name ('El Papiol, Barcelona') or 'lat,lon'")],
    distance_km: Annotated[float, Field(ge=2, le=200, description="Approximate distance in km")],
    max_climb_m: Annotated[float | None, Field(gt=0, description="Maximum desired climbing in metres")] = None,
    trail_type: Annotated[
        Literal["tracks", "mixed", "singletrack"],
        Field(description="tracks = wide, non-technical dirt tracks; mixed = general MTB; singletrack = more singletrack"),
    ] = "mixed",
    loop: Annotated[bool, Field(description="Return to the start point")] = True,
    end: Annotated[str | None, Field(description="End point if the route is not a loop")] = None,
    name: Annotated[str | None, Field(description="Route name (optional)")] = None,
    seed: Annotated[int | None, Field(description="Seed to repeat the same route; change it for an alternative")] = None,
    via: Annotated[
        list[str] | None,
        Field(max_length=MAX_VIA_POINTS, description="Places the route must pass through, in order (names or 'lat,lon')"),
    ] = None,
) -> dict[str, Any]:
    """Generate an MTB route on real trails, save it as GPX and return the summary and warnings.

    Takes 10 to 60 seconds (it evaluates several candidates and picks the best one).
    """
    try:
        request = RouteRequest(
            start=start, distance_km=distance_km, max_climb_m=max_climb_m, trail_type=trail_type,
            loop=loop, end=end, name=name, seed=seed, via=tuple(via or ()),
        )
        service = _get_service()
        result = await anyio.to_thread.run_sync(lambda: service.generate_and_save(request))
        return result.to_dict()
    except (ValueError, EngineError, GeocodingError) as e:
        return {"error": str(e)}


@mcp.tool()
async def list_routes() -> dict[str, Any]:
    """List the saved GPX routes (most recent first) with their summary."""
    service = _get_service()
    return {
        "folder": str(service.config.gpx_dir),
        "routes": service.list_routes(),
        "available_exporters": available_exporters(),
    }


def main() -> None:
    logging.getLogger("httpx").setLevel(logging.WARNING)  # do not log every HTTP request
    mcp.run()


if __name__ == "__main__":
    main()
