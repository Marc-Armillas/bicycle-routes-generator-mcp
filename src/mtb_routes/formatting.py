"""Plain-text rendering of a result (for the CLI and reports)."""

from __future__ import annotations

from typing import Any


def format_result(d: dict[str, Any]) -> str:
    s = d["summary"]
    surface = s["surface_pct"]
    lines = [
        f"{d['name']}",
        f"  Start: {d['start']['name']}",
        f"  Distance: {s['distance_km']} km · Climbing: +{s['ascent_m']} m / -{s['descent_m']} m"
        f" · Elevation {s['min_elevation_m']}–{s['max_elevation_m']} m",
        f"  Max grade: {s['max_uphill_grade_pct']} % uphill, {s['max_downhill_grade_pct']} % downhill",
        f"  Surface: paved {surface['paved']} % · track {surface['track']} % · singletrack {surface['path']} %"
        + (f" · unknown {surface['unknown']} %" if surface.get("unknown") else ""),
        f"  Engine: {d['engine']} · candidates evaluated: {d['candidates_evaluated']}",
    ]
    if d.get("gpx_file"):
        lines.append(f"  GPX: {d['gpx_file']}")
    for e in d.get("exports", []):
        if e["exporter"] != "disk":
            lines.append(f"  {e['exporter']}: {'OK' if e['ok'] else 'ERROR'} — {e['message']}")
    lines.append("  Warnings:")
    lines += [f"   - [{w['kind']}] {w['message']}" for w in s["warnings"]]
    lines.append(f"  {d['attribution']}")
    return "\n".join(lines)
