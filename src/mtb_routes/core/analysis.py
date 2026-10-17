"""Track analysis: distance, climbing, grades, surfaces, warnings and scoring.

Pure functions: no network requests and no disk writes.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from .models import ProtectedAreaCrossing, RouteRequest, RouteWarning, Segment, Summary, Track, TrackPoint

EARTH_RADIUS_M = 6_371_008.8
STEEP_GRADE_PCT = 12.0
CLIMB_THRESHOLD_M = 4.0  # hysteresis so the elevation model's noise is not summed up
PROFILE_STEP_M = 20.0
SMOOTHING_SAMPLES = 5  # 5 × 20 m ≈ 100 m
GRADE_WINDOW_M = 100.0
MAX_WARNINGS_PER_KIND = 6

GENERAL_WARNINGS = (
    "Climbing and grades come from a digital elevation model (~90 m resolution) and may differ "
    "from what a barometric watch or bike computer records (often by 10-20 %); short ramps may "
    "be smoothed out.",
    "Route generated automatically from OpenStreetMap: check it on a map before riding (trail "
    "condition, access, temporary closures and local regulations).",
)

PAVED = {
    "asphalt", "paved", "concrete", "concrete:plates", "concrete:lanes", "paving_stones",
    "sett", "cobblestone", "metal", "wood", "chipseal",
}
UNPAVED = {
    "unpaved", "gravel", "fine_gravel", "compacted", "dirt", "earth", "ground", "grass",
    "sand", "mud", "pebblestone", "rock", "woodchips", "grass_paver", "stone",
}
TRAFFIC_ROADS = {"motorway", "trunk", "primary", "secondary", "tertiary"}
PATH_WAYS = {"path", "footway", "bridleway", "steps", "pedestrian"}
PAVED_WAYS = {
    "residential", "unclassified", "service", "living_street", "cycleway", "road",
    *TRAFFIC_ROADS,
}


# --------------------------------------------------------------------------- geometry

def distance_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp, dl = p2 - p1, math.radians(b_lon - a_lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(h)))


def cumulative_distances(points: Sequence[TrackPoint]) -> list[float]:
    cumulative, total = [0.0], 0.0
    for a, b in zip(points, points[1:]):
        total += distance_m(a.lat, a.lon, b.lat, b.lon)
        cumulative.append(total)
    return cumulative


# --------------------------------------------------------------------------- elevation

def elevation_gain(elevations: Sequence[float], threshold: float = CLIMB_THRESHOLD_M) -> tuple[float, float]:
    """Total ascent and descent with hysteresis.

    Finds the turning points (peaks and valleys) ignoring oscillations smaller than
    `threshold` and sums the differences between them.
    """
    if not elevations:
        return 0.0, 0.0
    extremes = [elevations[0]]
    direction, candidate = 0, elevations[0]
    for e in elevations[1:]:
        if direction == 0:
            if abs(e - extremes[-1]) >= threshold:
                direction, candidate = (1 if e > extremes[-1] else -1), e
        elif direction * (e - candidate) > 0:  # still going the same way
            candidate = e
        elif abs(candidate - e) >= threshold:  # confirmed turn
            extremes.append(candidate)
            direction, candidate = -direction, e
    if direction:
        extremes.append(candidate)
    diffs = [b - a for a, b in zip(extremes, extremes[1:])]
    return sum(d for d in diffs if d > 0), -sum(d for d in diffs if d < 0)


def profile(points: Sequence[TrackPoint], step: float = PROFILE_STEP_M) -> list[tuple[float, float]]:
    """(distance, elevation) profile resampled at a fixed step and smoothed (~100 m moving average)."""
    with_ele = [(d, p.ele) for d, p in zip(cumulative_distances(points), points) if p.ele is not None]
    if len(with_ele) < 2:
        return []
    result: list[tuple[float, float]] = []
    j, d, end = 0, 0.0, with_ele[-1][0]
    while d <= end:
        while j < len(with_ele) - 2 and with_ele[j + 1][0] < d:
            j += 1
        (d0, e0), (d1, e1) = with_ele[j], with_ele[j + 1]
        t = 0.0 if d1 == d0 else min(1.0, max(0.0, (d - d0) / (d1 - d0)))
        result.append((d, e0 + t * (e1 - e0)))
        d += step
    # Centered moving average: the 90 m model adds fake steps on trails that traverse slopes.
    elevations = [e for _, e in result]
    k = SMOOTHING_SAMPLES // 2
    smoothed = []
    for i in range(len(elevations)):
        window = elevations[max(0, i - k) : i + k + 1]
        smoothed.append(sum(window) / len(window))
    return [(d, e) for (d, _), e in zip(result, smoothed)]


def grades(profile_: Sequence[tuple[float, float]], window: float = GRADE_WINDOW_M) -> list[tuple[float, float, float]]:
    """Average grade (%) over sliding windows of `window` metres: (from_m, to_m, pct)."""
    result = []
    j = 0
    for i, (d0, e0) in enumerate(profile_):
        j = max(j, i + 1)
        while j < len(profile_) and profile_[j][0] - d0 < window:
            j += 1
        if j >= len(profile_):
            break
        d1, e1 = profile_[j]
        result.append((d0, d1, (e1 - e0) / (d1 - d0) * 100))
    return result


def steep_sections(grade_windows: Sequence[tuple[float, float, float]], threshold: float = STEEP_GRADE_PCT) -> list[tuple[float, float, float]]:
    """Merge windows with |grade| > threshold into sections (from_m, to_m, signed_max_grade)."""
    sections: list[list[float]] = []
    for d0, d1, pct in grade_windows:
        if abs(pct) <= threshold:
            continue
        if sections and d0 <= sections[-1][1] and math.copysign(1, pct) == math.copysign(1, sections[-1][2]):
            sections[-1][1] = max(sections[-1][1], d1)
            if abs(pct) > abs(sections[-1][2]):
                sections[-1][2] = pct
        else:
            sections.append([d0, d1, pct])
    return [tuple(s) for s in sections]  # type: ignore[misc]


# --------------------------------------------------------------------------- OSM tags

def classify(tags: dict[str, str]) -> str:
    """Classify a segment as paved / track / path / unknown from its OSM tags."""
    highway = tags.get("highway", "")
    surface = tags.get("surface", "")
    if highway == "track":
        grade1 = tags.get("tracktype") == "grade1"
        return "paved" if surface in PAVED or (grade1 and not surface) else "track"
    if highway in PATH_WAYS:
        if surface in PAVED and highway != "path":
            return "paved"
        return "path"
    if surface in UNPAVED:
        return "track"
    if highway in PAVED_WAYS or highway.endswith("_link") or surface in PAVED:
        return "paved"
    return "unknown"


def has_traffic(tags: dict[str, str]) -> bool:
    highway = tags.get("highway", "").removesuffix("_link")
    if highway in TRAFFIC_ROADS:
        return True
    try:
        return int(tags.get("estimated_traffic_class", "0")) >= 4
    except ValueError:
        return False


def bike_forbidden(tags: dict[str, str]) -> bool:
    bicycle = tags.get("bicycle", "")
    if bicycle in {"no", "dismount", "use_sidepath"}:
        return True
    access = tags.get("access", "")
    return access in {"no", "private"} and bicycle not in {"yes", "designated", "permissive"}


def is_technical(tags: dict[str, str]) -> bool:
    try:
        scale = int(tags.get("mtb:scale", "0").rstrip("+-"))
    except ValueError:
        scale = 0
    return scale >= 3 or tags.get("highway") == "steps"


def matching_sections(
    segments: Sequence[Segment],
    predicate: Callable[[dict[str, str]], bool],
    max_gap_m: float = 50.0,
    min_length_m: float = 0.0,
) -> list[tuple[float, float]]:
    """Sections (from_m, to_m) where the predicate holds, merging small gaps."""
    sections: list[list[float]] = []
    d = 0.0
    for s in segments:
        if predicate(s.tags):
            if sections and d - sections[-1][1] <= max_gap_m:
                sections[-1][1] = d + s.distance_m
            else:
                sections.append([d, d + s.distance_m])
        d += s.distance_m
    return [(a, b) for a, b in sections if b - a >= min_length_m]


def surface_breakdown(segments: Sequence[Segment]) -> dict[str, float]:
    total = sum(s.distance_m for s in segments) or 1.0
    result = {"paved": 0.0, "track": 0.0, "path": 0.0, "unknown": 0.0}
    for s in segments:
        result[classify(s.tags)] += s.distance_m
    return {k: v / total * 100 for k, v in result.items()}


def overlap_ratio(points: Sequence[TrackPoint], min_separation_m: float = 400.0) -> float:
    """Share of the route that repeats a stretch already ridden (out-and-back sections)."""
    if len(points) < 2:
        return 0.0
    cumulative = cumulative_distances(points)
    seen: dict[tuple[int, int], float] = {}
    repeated = samples = 0
    next_sample = 0.0
    lon_scale = math.cos(math.radians(points[0].lat))
    for p, d in zip(points, cumulative):
        cell = (round(p.lat / 0.00025), round(p.lon * lon_scale / 0.00025))
        first = seen.setdefault(cell, d)
        if d >= next_sample:  # count samples every 25 m, but mark every cell
            next_sample = d + 25.0
            samples += 1
            if d - first > min_separation_m:
                repeated += 1
    return repeated / samples if samples else 0.0


# --------------------------------------------------------------------------- summary

def _km(m: float) -> float:
    return m / 1000


def _range(a: float, b: float) -> str:
    return f"km {a / 1000:.1f}–{b / 1000:.1f}"


def analyze(track: Track, request: RouteRequest, areas: Sequence[ProtectedAreaCrossing] = ()) -> Summary:
    points, segments = track.points, track.segments
    elevations = [p.ele for p in points if p.ele is not None]
    prof = profile(points)
    ascent, descent = elevation_gain([e for _, e in prof]) if prof else (0.0, 0.0)
    windows = grades(prof)
    max_up = max((g for _, _, g in windows), default=0.0)
    max_down = -min((g for _, _, g in windows), default=0.0)

    warnings: list[RouteWarning] = []
    target_m = request.distance_km * 1000
    if request.loop and abs(track.distance_m - target_m) / target_m > 0.15:
        warnings.append(RouteWarning("distance", (
            f"The route is {track.distance_m / 1000:.1f} km instead of the requested {request.distance_km:g} km: "
            "the local trail network did not allow a closer fit.")))
    if request.max_climb_m and ascent > request.max_climb_m * 1.1:
        warnings.append(RouteWarning("climb", (
            f"Estimated climbing ({ascent:.0f} m) exceeds the requested maximum ({request.max_climb_m:g} m).")))

    traffic = matching_sections(segments, has_traffic, min_length_m=40)
    if traffic:
        total = sum(b - a for a, b in traffic)
        warnings.append(RouteWarning("traffic", (
            f"{total / 1000:.1f} km on roads with motor traffic in {len(traffic)} section(s); ride carefully.")))
        warnings += [RouteWarning("traffic", f"Road with traffic ({_range(a, b)}).", _km(a), _km(b)) for a, b in traffic[:8]]

    steep = steep_sections(windows)
    if len(steep) > MAX_WARNINGS_PER_KIND:
        total = sum(b - a for a, b, _ in steep)
        warnings.append(RouteWarning("grade", (
            f"{len(steep)} sections (about {total / 1000:.1f} km) are steeper than {STEEP_GRADE_PCT:g} %; "
            f"listing the {MAX_WARNINGS_PER_KIND} steepest.")))
    for a, b, pct in sorted(sorted(steep, key=lambda s: -abs(s[2]))[:MAX_WARNINGS_PER_KIND]):
        direction = "climb" if pct > 0 else "descent"
        warnings.append(RouteWarning("grade", (
            f"Steep {direction} over {STEEP_GRADE_PCT:g} % (max ~{abs(pct):.0f} %, {_range(a, b)})."), _km(a), _km(b)))

    for a, b in matching_sections(segments, bike_forbidden, max_gap_m=10):
        warnings.append(RouteWarning("access", (
            f"According to OpenStreetMap bikes are not allowed or you must dismount ({_range(a, b)}, "
            f"{b - a:.0f} m); look for an alternative or push the bike."), _km(a), _km(b)))

    for a, b in matching_sections(segments, is_technical, max_gap_m=10):
        warnings.append(RouteWarning("technical", f"Technical section or steps ({_range(a, b)}).", _km(a), _km(b)))

    paths = matching_sections(segments, lambda t: classify(t) == "path", max_gap_m=10)
    for area in areas:
        msg = (f"The route crosses the protected area «{area.name}» (km {area.start_km:.1f}–{area.end_km:.1f}). "
               "Follow its regulations.")
        path_inside = sum(
            max(0.0, min(b, area.end_km * 1000) - max(a, area.start_km * 1000)) for a, b in paths
        )
        if "collserola" in area.name.lower():
            msg += (" In Collserola bikes are only allowed on the park's cycling network "
                    "(tracks wider than 3 m), at 20 km/h maximum.")
        if path_inside >= 50:
            msg += f" It includes about {path_inside / 1000:.1f} km of singletrack inside the area: check it is allowed."
        warnings.append(RouteWarning("protected_area", msg, area.start_km, area.end_km))

    warnings += [RouteWarning("general", m) for m in GENERAL_WARNINGS]

    return Summary(
        distance_km=track.distance_m / 1000,
        ascent_m=ascent,
        descent_m=descent,
        min_elevation_m=min(elevations) if elevations else None,
        max_elevation_m=max(elevations) if elevations else None,
        max_uphill_grade_pct=max(0.0, max_up),
        max_downhill_grade_pct=max(0.0, max_down),
        surface_pct=surface_breakdown(segments),
        warnings=warnings,
    )


def score(track: Track, summary: Summary, request: RouteRequest) -> float:
    """Score of a candidate route (lower is better)."""
    target = request.distance_km * 1000
    deviation = abs(track.distance_m - target) / target
    total = sum(s.distance_m for s in track.segments) or 1.0
    traffic = sum(s.distance_m for s in track.segments if has_traffic(s.tags)) / total
    forbidden = sum(s.distance_m for s in track.segments if bike_forbidden(s.tags)) / total
    forbidden_count = len(matching_sections(track.segments, bike_forbidden, max_gap_m=10))
    surface = {k: v / 100 for k, v in summary.surface_pct.items()}

    paved_weight = {"tracks": 2.0, "mixed": 1.2, "singletrack": 2.0}
    points = (
        4.0 * max(0.0, deviation - 0.05)
        + 3.0 * overlap_ratio(track.points)
        + 6.0 * traffic
        + 25.0 * forbidden + 0.15 * forbidden_count
        + paved_weight[request.trail_type] * surface["paved"]
    )
    if request.trail_type == "tracks":
        # "Tracks" usually means non-technical: penalise singletrack and very steep ramps.
        points += 3.0 * surface["path"]
        points += 0.03 * max(0.0, max(summary.max_uphill_grade_pct, summary.max_downhill_grade_pct) - 15)
    elif request.trail_type == "singletrack":
        points -= 0.8 * surface["path"]
    if request.max_climb_m:
        points += 3.0 * max(0.0, summary.ascent_m - request.max_climb_m) / request.max_climb_m
    return points
