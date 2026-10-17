"""Command-line interface to use mtb-routes without AI.

Examples:
    mtb-routes generate "El Papiol" --km 25 --type tracks --max-climb 600
    mtb-routes generate "41.4386,2.0108" --km 15 --garmin
    mtb-routes generate "El Papiol" --km 30 --via "Castellbisbal" --via "Molins de Rei"
    mtb-routes list
"""

from __future__ import annotations

import argparse
import json
import sys

from .config import load_config
from .core.models import TRAIL_TYPES, RouteRequest
from .engines.base import EngineError
from .formatting import format_result
from .geo.nominatim import GeocodingError
from .service import RouteService


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="mtb-routes", description="Generate MTB routes and save them as GPX.")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="Generate a route and save it as GPX")
    g.add_argument("start", help="Start location (place name or 'lat,lon')")
    g.add_argument("--km", type=float, required=True, help="Approximate distance in km")
    g.add_argument("--type", choices=TRAIL_TYPES, default="mixed", help="Preferred trail type")
    g.add_argument("--max-climb", type=float, help="Maximum desired climbing (m)")
    g.add_argument("--end", help="End point for a point-to-point route (disables the loop)")
    g.add_argument("--via", action="append", default=[], help="Place to pass through (repeat it, in order)")
    g.add_argument("--name", help="Route name")
    g.add_argument("--seed", type=int, help="Seed to always get the same route")
    g.add_argument("--garmin", action="store_true", help="Also send to Garmin Connect (see README)")
    g.add_argument("--json", action="store_true", help="JSON output")

    sub.add_parser("list", help="List saved routes")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = load_config()
    service = RouteService(config)
    try:
        if args.command == "list":
            routes = service.list_routes()
            if not routes:
                print(f"No saved routes in {config.gpx_dir}")
            for r in routes:
                s = r["summary"]
                missing = "" if r["exists"] else "  (file deleted)"
                print(f"{r['created']}  {r['name']}  {s['distance_km']} km  +{s['ascent_m']} m\n    {r['file']}{missing}")
            return 0

        request = RouteRequest(
            start=args.start, distance_km=args.km, max_climb_m=args.max_climb,
            trail_type=args.type, loop=args.end is None, end=args.end,
            name=args.name, seed=args.seed, via=tuple(args.via),
        )
        exporters = ["disk"] + (["garmin"] if args.garmin else [])
        progress = None if args.json else (lambda m: print(m, file=sys.stderr))
        result = service.generate_and_save(request, exporters, progress).to_dict()
        print(json.dumps(result, ensure_ascii=False, indent=1) if args.json else format_result(result))
        return 0
    except (ValueError, EngineError, GeocodingError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        service.close()


if __name__ == "__main__":
    raise SystemExit(main())
