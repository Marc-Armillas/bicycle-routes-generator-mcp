"""Default exporter: saves the GPX in the configured folder and records it in an index."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from ..config import Config
from ..core.gpx import build_gpx
from ..core.models import Route
from .base import ExportResult, register

INDEX_FILE = "routes.json"


def file_name(name: str, now: datetime) -> str:
    base = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()[:60] or "route"
    return f"{base}-{now:%Y%m%d-%H%M%S}.gpx"


def safe_path(directory: Path, name: str) -> Path:
    """Return directory/name, guaranteeing it does not escape the directory."""
    directory = directory.resolve()
    target = (directory / name).resolve()
    if target.parent != directory:
        raise ValueError(f"File name not allowed: {name}")
    return target


def read_index(config: Config) -> list[dict]:
    path = config.data_dir / INDEX_FILE
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _record(config: Config, entry: dict) -> None:
    config.data_dir.mkdir(parents=True, exist_ok=True)
    routes = [r for r in read_index(config) if r.get("file") != entry["file"]]
    routes.append(entry)
    path = config.data_dir / INDEX_FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(routes, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


@register
class DiskExporter:
    name = "disk"

    def export(self, route: Route, config: Config) -> ExportResult:
        now = datetime.now()
        config.gpx_dir.mkdir(parents=True, exist_ok=True)
        target = safe_path(config.gpx_dir, file_name(route.name, now))
        target.write_text(build_gpx(route), encoding="utf-8")
        route.gpx_file = target
        _record(config, {
            "file": str(target),
            "name": route.name,
            "start": route.start_name,
            "created": now.isoformat(timespec="seconds"),
            "engine": route.track.engine,
            "profile": route.track.profile,
            "summary": {k: v for k, v in route.summary.to_dict().items() if k != "warnings"},
        })
        return ExportResult(self.name, True, f"GPX saved to {target}", file=target)
