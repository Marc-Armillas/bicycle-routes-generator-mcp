"""Orchestration: geocode → generate candidates → analyze → pick → export.

This is the layer reused by the CLI, the local MCP server and a future remote server.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import OSM_ATTRIBUTION
from .config import Config
from .core.analysis import analyze, overlap_ratio, score
from .core.loop import generate_candidates
from .core.models import ProtectedAreaCrossing, Route, RouteRequest, RouteWarning, Track
from .engines.base import RoutingEngine
from .engines.brouter import BRouterEngine
from .engines.ors import ORSEngine
from .exporters import ExportResult, get_exporter
from .exporters.disk import read_index
from .geo.nominatim import Geocoder, Nominatim
from .geo.protected_areas import OverpassProtectedAreas, ProtectedAreaProvider
from .net import HttpClient, NetworkError

Progress = Callable[[str], None]


@dataclass
class GenerationResult:
    route: Route
    exports: list[ExportResult] = field(default_factory=list)
    candidates_evaluated: int = 1

    def to_dict(self) -> dict[str, Any]:
        r = self.route
        return {
            "name": r.name,
            "gpx_file": str(r.gpx_file) if r.gpx_file else None,
            "start": {"name": r.start_name, "lat": r.start.lat, "lon": r.start.lon},
            "summary": r.summary.to_dict(),
            "engine": f"{r.track.engine} ({r.track.profile})",
            "candidates_evaluated": self.candidates_evaluated,
            "exports": [e.to_dict() for e in self.exports],
            "attribution": OSM_ATTRIBUTION,
        }


def create_engine(config: Config, client: HttpClient) -> RoutingEngine:
    if config.engine == "brouter":
        return BRouterEngine(client, config.brouter_url)
    if config.engine == "ors":
        return ORSEngine(client, config.ors_api_key or "")
    raise ValueError(f"Unknown engine «{config.engine}» (use brouter or ors)")


class RouteService:
    def __init__(
        self,
        config: Config,
        engine: RoutingEngine | None = None,
        geocoder: Geocoder | None = None,
        protected_areas: ProtectedAreaProvider | None = None,
        client: HttpClient | None = None,
    ) -> None:
        self.config = config
        needs_client = engine is None or geocoder is None or (protected_areas is None and config.protected_areas)
        self.client = client or (HttpClient(config.user_agent, config.data_dir) if needs_client else None)
        self.engine = engine or create_engine(config, self.client)  # type: ignore[arg-type]
        self.geocoder = geocoder or Nominatim(self.client, config.nominatim_url)  # type: ignore[arg-type]
        if protected_areas is None and config.protected_areas:
            protected_areas = OverpassProtectedAreas(self.client, config.overpass_url)  # type: ignore[arg-type]
        self.protected_areas = protected_areas

    def _areas(self, track: Track) -> tuple[list[ProtectedAreaCrossing], list[RouteWarning]]:
        if self.protected_areas is None:
            return [], []
        try:
            return self.protected_areas.areas_along(track.points), []
        except (NetworkError, OSError, ValueError) as e:
            return [], [RouteWarning("protected_area", f"Could not check whether the route crosses protected areas ({e}).")]

    def generate(self, request: RouteRequest, progress: Progress | None = None, n_candidates: int = 6) -> tuple[Route, int]:
        report = progress or (lambda _m: None)
        report(f"Looking up «{request.start}»…")
        place = self.geocoder.search(request.start)
        target_m = request.distance_km * 1000

        if request.loop:
            seed = request.seed if request.seed is not None else random.randrange(1_000_000)
            candidates = generate_candidates(
                self.engine, place.coordinate, target_m, request.trail_type, seed, n_candidates,
                progress=lambda i, n: report(f"Computing candidate route {i}/{n}…"),
            )
        else:
            end = self.geocoder.search(request.end or "")
            candidates = [self.engine.route([place.coordinate, end.coordinate], request.trail_type)]

        # Candidates are ranked without protected areas (one Overpass query per candidate would
        # be abusive); areas are only checked for the winner.
        ranked = sorted(
            ((score(t, s := analyze(t, request), request), t, s) for t in candidates),
            key=lambda x: x[0],
        )
        _, track, _ = ranked[0]
        report("Checking protected areas…" if self.protected_areas else "Analyzing the route…")
        areas, extra_warnings = self._areas(track)
        summary = analyze(track, request, areas)
        if overlap_ratio(track.points) > 0.25:
            extra_warnings.append(RouteWarning("general", "Part of the route repeats the same trail out and back."))
        summary.warnings[-2:-2] = extra_warnings  # before the general warnings

        name = request.name or self._default_name(request, place.name, track)
        return Route(name, place.coordinate, place.name, track, summary, request), len(candidates)

    @staticmethod
    def _default_name(request: RouteRequest, place_name: str, track: Track) -> str:
        short = request.start.split(",")[0].strip() if not place_name[:1].isdigit() else place_name
        if short.islower():
            short = short.title()
        kind = "loop" if request.loop else "point-to-point"
        return f"MTB {short} {track.distance_m / 1000:.0f} km {kind}"

    def export(self, route: Route, exporters: Sequence[str] = ("disk",)) -> list[ExportResult]:
        names = list(dict.fromkeys(["disk", *exporters]))  # always save to disk first
        return [get_exporter(n).export(route, self.config) for n in names]

    def generate_and_save(
        self, request: RouteRequest, exporters: Sequence[str] = ("disk",), progress: Progress | None = None
    ) -> GenerationResult:
        route, n = self.generate(request, progress)
        return GenerationResult(route, self.export(route, exporters), n)

    def list_routes(self) -> list[dict]:
        routes = read_index(self.config)
        for r in routes:
            r["exists"] = Path(r["file"]).exists()
        return sorted(routes, key=lambda r: r.get("created", ""), reverse=True)

    def close(self) -> None:
        if self.client:
            self.client.close()
