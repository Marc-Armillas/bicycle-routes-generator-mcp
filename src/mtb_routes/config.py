"""Configuration read from environment variables. No keys or personal data in the code."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from . import __version__

PUBLIC_BROUTER = "https://brouter.de"
PUBLIC_NOMINATIM = "https://nominatim.openstreetmap.org"
PUBLIC_OVERPASS = "https://overpass-api.de/api/interpreter"


def default_gpx_dir() -> Path:
    """/tmp/mtb-routes (the system temp folder on Windows). The OS may clean it up: copy routes you want to keep."""
    base = Path(tempfile.gettempdir()) if os.name == "nt" else Path("/tmp")
    return base / "mtb-routes"


def _path(value: str) -> Path:
    return Path(os.path.expandvars(value)).expanduser().resolve()


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    gpx_dir: Path
    data_dir: Path
    engine: str = "brouter"
    brouter_url: str = PUBLIC_BROUTER
    ors_api_key: str | None = None
    contact: str | None = None
    nominatim_url: str = PUBLIC_NOMINATIM
    overpass_url: str = PUBLIC_OVERPASS
    protected_areas: bool = True
    garmin_mcp_command: str | None = None

    @property
    def user_agent(self) -> str:
        # HTTP headers must be ASCII.
        base = f"mtb-routes/{__version__} (open-source MTB route planner"
        return f"{base}; contact: {self.contact})" if self.contact else f"{base})"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Config:
        env = os.environ if env is None else env
        # The MCPB extension may pass "${user_config.x}" unsubstituted when an optional field is empty.
        env = {k: v for k, v in env.items() if not v.strip().startswith("${")}
        gpx_dir = _path(env.get("MTB_GPX_DIR") or str(default_gpx_dir()))
        data_dir = env.get("MTB_DATA_DIR")
        return cls(
            gpx_dir=gpx_dir,
            # Cache and index live next to the GPX files so nothing is written anywhere else.
            data_dir=_path(data_dir) if data_dir else gpx_dir / ".mtb-routes",
            engine=(env.get("MTB_ENGINE") or "brouter").strip().lower(),
            brouter_url=(env.get("MTB_BROUTER_URL") or PUBLIC_BROUTER).rstrip("/"),
            ors_api_key=env.get("ORS_API_KEY") or None,
            contact=env.get("MTB_CONTACT") or None,
            nominatim_url=(env.get("MTB_NOMINATIM_URL") or PUBLIC_NOMINATIM).rstrip("/"),
            overpass_url=env.get("MTB_OVERPASS_URL") or PUBLIC_OVERPASS,
            protected_areas=_bool(env.get("MTB_PROTECTED_AREAS"), True),
            garmin_mcp_command=env.get("MTB_GARMIN_MCP_COMMAND") or None,
        )


def load_config() -> Config:
    """Load .env from the current directory (if any) and return the configuration."""
    from dotenv import load_dotenv

    load_dotenv(override=False)
    return Config.from_env()
