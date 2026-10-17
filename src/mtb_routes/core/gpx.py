"""GPX 1.1 writer with elevation and OpenStreetMap attribution."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from .. import OSM_ATTRIBUTION, __version__
from .models import Route, activity_type

NS = "http://www.topografix.com/GPX/1/1"
SCHEMA = "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd"


def short_description(route: Route, max_len: int = 500) -> str:
    s = route.summary
    surface = s.surface_pct
    text = (
        f"{s.distance_km:.1f} km, +{s.ascent_m:.0f} m, max grade {s.max_uphill_grade_pct:.0f} %. "
        f"Paved {surface['paved']:.0f} %, track {surface['track']:.0f} %, singletrack {surface['path']:.0f} %. "
        "Check the route before riding. © OpenStreetMap contributors (ODbL)."
    )
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def build_gpx(route: Route, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    ET.register_namespace("", NS)
    q = lambda tag: f"{{{NS}}}{tag}"  # noqa: E731

    gpx = ET.Element(q("gpx"), {
        "version": "1.1",
        "creator": f"mtb-routes {__version__}",
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": SCHEMA,
    })
    meta = ET.SubElement(gpx, q("metadata"))
    ET.SubElement(meta, q("name")).text = route.name
    ET.SubElement(meta, q("desc")).text = short_description(route)
    copyright_ = ET.SubElement(meta, q("copyright"), {"author": "OpenStreetMap contributors"})
    ET.SubElement(copyright_, q("license")).text = "https://opendatacommons.org/licenses/odbl/"
    link = ET.SubElement(meta, q("link"), {"href": "https://www.openstreetmap.org/copyright"})
    ET.SubElement(link, q("text")).text = OSM_ATTRIBUTION
    ET.SubElement(meta, q("time")).text = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    trk = ET.SubElement(gpx, q("trk"))
    ET.SubElement(trk, q("name")).text = route.name
    ET.SubElement(trk, q("desc")).text = short_description(route)
    ET.SubElement(trk, q("type")).text = activity_type(route.request.trail_type)
    seg = ET.SubElement(trk, q("trkseg"))
    for p in route.track.points:
        pt = ET.SubElement(seg, q("trkpt"), {"lat": f"{p.lat:.6f}", "lon": f"{p.lon:.6f}"})
        if p.ele is not None:
            ET.SubElement(pt, q("ele")).text = f"{p.ele:.1f}"

    ET.indent(gpx, space=" ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(gpx, encoding="unicode") + "\n"
