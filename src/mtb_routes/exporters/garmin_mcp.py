"""Garmin exporter: delegates to an already installed Garmin MCP server (`upload_course`).

Two ways to use it:

(a) From Claude (recommended): mtb-routes never talks to Garmin. `generate_route` returns
    the GPX path and Claude calls the Garmin MCP server's `upload_course` tool.
    Nothing needs configuring here.

(b) From the CLI: this exporter starts the Garmin MCP server over stdio with the command in
    MTB_GARMIN_MCP_COMMAND and calls `upload_course`. Garmin credentials are handled by
    that server, never by this application.

Note: community Garmin MCP servers use Garmin Connect's unofficial web API and may break
if Garmin changes it. The official Courses API is only available to approved businesses.
"""

from __future__ import annotations

import asyncio
import shlex

from ..config import Config
from ..core.gpx import short_description
from ..core.models import Route
from .base import ExportResult, register

ACTIVITY_TYPE = "mountain_biking"


async def _upload(command: list[str], arguments: dict) -> str:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=command[0], args=command[1:])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("upload_course", arguments)
            text = " ".join(getattr(c, "text", "") for c in getattr(result, "content", [])).strip()
            if getattr(result, "is_error", False):
                raise RuntimeError(text or "upload_course returned an error")
            return text


@register
class GarminMCPExporter:
    name = "garmin"

    def export(self, route: Route, config: Config) -> ExportResult:
        if route.gpx_file is None:
            return ExportResult(self.name, False, "The GPX must be saved to disk first")
        if not config.garmin_mcp_command:
            return ExportResult(self.name, False, (
                "MTB_GARMIN_MCP_COMMAND is not set. From Claude it is not needed: ask it to upload the GPX "
                "with the Garmin MCP server's upload_course tool."))
        arguments = {
            "gpx_path": str(route.gpx_file),
            "course_name": route.name[:128],
            "activity_type": ACTIVITY_TYPE,
            "description": short_description(route, 512),
        }
        try:
            text = asyncio.run(_upload(shlex.split(config.garmin_mcp_command), arguments))
        except Exception as e:  # noqa: BLE001 — any failure of the external server is reported
            return ExportResult(self.name, False, f"Could not upload to Garmin Connect: {e}")
        return ExportResult(self.name, True, text or "Route sent to Garmin Connect")
