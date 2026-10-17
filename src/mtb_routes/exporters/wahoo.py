"""Wahoo exporter — NOT IMPLEMENTED. Notes for a future implementation.

- API: Wahoo Cloud API (https://developers.wahooligan.com/cloud), OAuth 2.0.
- Endpoint: POST /v1/routes (multipart/form-data) with the `routes_write` scope;
  GET /v1/routes to list them. Routes reach the ELEMNT when the app syncs.
- Access: you must request an app in the developer portal and wait for approval.
  Sandbox and Production apps are separate (a Sandbox app cannot become Production).
  Sandbox limits reported by third parties: 25 requests/5 min, 100/hour, 250/day.
- Format: the API works with FIT files; a GPX → FIT conversion is probably needed
  (e.g. with the `fit-tool` library). Check the documentation after approval.
- Planned configuration: WAHOO_CLIENT_ID, WAHOO_CLIENT_SECRET and a user token stored
  outside the code (system keychain).
"""

from __future__ import annotations

from ..config import Config
from ..core.models import Route
from .base import ExportResult, register


@register
class WahooExporter:
    name = "wahoo"

    def export(self, route: Route, config: Config) -> ExportResult:
        return ExportResult(
            self.name, False,
            "The Wahoo exporter is not implemented yet. Import the GPX manually in the ELEMNT app.",
        )
