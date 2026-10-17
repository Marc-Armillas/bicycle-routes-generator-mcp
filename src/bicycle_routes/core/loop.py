"""Engine-independent loop route generator.

The track itself is always computed by the engine on real trails; this module only
picks waypoints around the start and scales them until the requested distance is met:

1. Draw a circle passing through the start, oriented along a random bearing.
2. Spread N waypoints over that circle (with some jitter).
3. The engine routes start → P1 → … → PN → start.
4. Scale the radius by the distance obtained and repeat (a few iterations).
"""

from __future__ import annotations

import math
import random
from collections.abc import Callable

from ..engines.base import EngineError, RoutingEngine
from .models import Coordinate, Track

INITIAL_DETOUR_FACTOR = 1.45  # real trails are longer than the ideal circle (measured with BRouter)
MAX_ITERATIONS = 4


def offset(origin: Coordinate, distance_m: float, bearing_deg: float) -> Coordinate:
    """Point `distance_m` away from `origin` along the given bearing (spherical approximation)."""
    r = 6_371_008.8
    angle = distance_m / r
    bearing = math.radians(bearing_deg)
    lat1, lon1 = math.radians(origin.lat), math.radians(origin.lon)
    lat2 = math.asin(math.sin(lat1) * math.cos(angle) + math.cos(lat1) * math.sin(angle) * math.cos(bearing))
    lon2 = lon1 + math.atan2(
        math.sin(bearing) * math.sin(angle) * math.cos(lat1), math.cos(angle) - math.sin(lat1) * math.sin(lat2)
    )
    return Coordinate(math.degrees(lat2), (math.degrees(lon2) + 540) % 360 - 180)


def circle_waypoints(start: Coordinate, radius_m: float, bearing: float, n: int, rng: random.Random) -> list[Coordinate]:
    """Waypoints on a circle of radius `radius_m` that passes through the start."""
    center = offset(start, radius_m, bearing)
    start_angle = (bearing + 180) % 360  # the start as seen from the center
    waypoints = []
    for k in range(1, n + 1):
        angle = start_angle + 360 * k / (n + 1) + rng.uniform(-12, 12)
        r = radius_m * rng.uniform(0.85, 1.15)
        waypoints.append(offset(center, r, angle))
    return waypoints


def generate_candidate(
    engine: RoutingEngine,
    start: Coordinate,
    distance_m: float,
    trail_type: str,
    seed: int,
    tolerance: float = 0.08,
    n_waypoints: int | None = None,
) -> Track:
    rng = random.Random(seed)
    bearing = rng.uniform(0, 360)
    n = n_waypoints or (3 if distance_m < 20_000 else 4)
    radius = distance_m / (2 * math.pi * INITIAL_DETOUR_FACTOR)
    jitter = rng.random()

    best: Track | None = None
    last_error: Exception | None = None
    for attempt in range(MAX_ITERATIONS + 2):
        waypoints = circle_waypoints(start, radius, bearing, n, random.Random(f"{seed}-{jitter}"))
        try:
            track = engine.route([start, *waypoints, start], trail_type)
        except EngineError as e:
            # A waypoint fell far from any trail (reservoir, private land...): rotate and retry.
            last_error = e
            bearing = (bearing + 35) % 360
            jitter = rng.random()
            continue
        if best is None or abs(track.distance_m - distance_m) < abs(best.distance_m - distance_m):
            best = track
        ratio = track.distance_m / distance_m
        if abs(ratio - 1) <= tolerance or attempt >= MAX_ITERATIONS:
            break
        # Damped scaling: distance grows slightly less than linearly with the radius.
        radius *= max(0.4, min(2.5, (1 / ratio) ** 0.9))
    if best is None:
        raise EngineError(f"Could not generate the loop route: {last_error}")
    return best


def generate_candidates(
    engine: RoutingEngine,
    start: Coordinate,
    distance_m: float,
    trail_type: str,
    base_seed: int,
    n_candidates: int = 4,
    progress: Callable[[int, int], None] | None = None,
) -> list[Track]:
    candidates: list[Track] = []
    errors: list[str] = []
    for i in range(n_candidates):
        if progress:
            progress(i + 1, n_candidates)
        try:
            candidates.append(generate_candidate(engine, start, distance_m, trail_type, base_seed + i * 7919))
        except EngineError as e:
            errors.append(str(e))
    if not candidates:
        raise EngineError("; ".join(dict.fromkeys(errors)) or "Could not generate any route")
    return candidates
