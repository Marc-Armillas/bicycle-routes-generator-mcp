"""Generate icon.png (512×512) for the extension, with no external dependencies.

Usage:  python scripts/make_icon.py
"""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

SIZE = 512
SUPERSAMPLING = 2  # smooths the edges

BACKGROUND = (31, 92, 64)
FAR_MOUNTAIN = (74, 140, 100)
MOUNTAIN = (236, 240, 232)
TRAIL = (232, 141, 52)


def inside_polygon(x: float, y: float, pts: list[tuple[float, float]]) -> bool:
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def color(x: float, y: float) -> tuple[int, int, int, int]:
    # Rounded square
    r = 96
    cx = min(max(x, r), SIZE - r)
    cy = min(max(y, r), SIZE - r)
    if math.hypot(x - cx, y - cy) > r:
        return (0, 0, 0, 0)
    c = BACKGROUND
    if inside_polygon(x, y, [(40, 400), (190, 190), (300, 330), (360, 260), (480, 400)]):
        c = FAR_MOUNTAIN
    if inside_polygon(x, y, [(60, 420), (250, 150), (450, 420)]):
        c = MOUNTAIN
    # Zigzag trail climbing the mountain
    for (x0, y0), (x1, y1) in [((140, 420), (300, 360)), ((300, 360), (210, 300)), ((210, 300), (270, 230))]:
        dx, dy = x1 - x0, y1 - y0
        t = max(0.0, min(1.0, ((x - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy)))
        if math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)) < 11:
            c = TRAIL
    # Dark green base under the mountains
    if y > 420 and c != TRAIL:
        c = BACKGROUND
    return (*c, 255)


def build(target: Path) -> None:
    rows = []
    for py in range(SIZE):
        row = bytearray([0])
        for px in range(SIZE):
            acc = [0, 0, 0, 0]
            for sy in range(SUPERSAMPLING):
                for sx in range(SUPERSAMPLING):
                    rgba = color(px + (sx + 0.5) / SUPERSAMPLING, py + (sy + 0.5) / SUPERSAMPLING)
                    for k in range(4):
                        acc[k] += rgba[k]
            row += bytes(v // (SUPERSAMPLING * SUPERSAMPLING) for v in acc)
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    png += chunk(b"IEND", b"")
    target.write_bytes(png)


if __name__ == "__main__":
    build(Path(__file__).resolve().parent.parent / "icon.png")
