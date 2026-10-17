"""Common exporter interface: export(route, config) -> ExportResult."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from ..config import Config
from ..core.models import Route


@dataclass
class ExportResult:
    exporter: str
    ok: bool
    message: str
    file: Path | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"exporter": self.exporter, "ok": self.ok, "message": self.message}
        if self.file:
            d["file"] = str(self.file)
        if self.data:
            d["data"] = self.data
        return d


class Exporter(Protocol):
    name: str

    def export(self, route: Route, config: Config) -> ExportResult: ...


_REGISTRY: dict[str, type] = {}


def register(cls: type) -> type:
    _REGISTRY[cls.name] = cls
    return cls


def get_exporter(name: str) -> Exporter:
    try:
        return _REGISTRY[name]()
    except KeyError:
        raise ValueError(f"Unknown exporter «{name}». Available: {', '.join(sorted(_REGISTRY))}") from None


def available_exporters() -> list[str]:
    return sorted(_REGISTRY)
