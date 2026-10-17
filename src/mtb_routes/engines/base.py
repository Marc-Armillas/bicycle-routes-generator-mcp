"""Common interface for routing engines."""

from __future__ import annotations

from typing import Protocol

from ..core.models import Coordinate, Track


class EngineError(RuntimeError):
    """The engine could not compute the route (point far from any trail, server down...)."""


class RoutingEngine(Protocol):
    name: str

    def route(self, points: list[Coordinate], trail_type: str) -> Track:
        """Compute a route through `points` in order, with elevation and per-segment tags."""
        ...
