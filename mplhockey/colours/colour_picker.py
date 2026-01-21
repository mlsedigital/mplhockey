# mplhockey/colours/pickers.py
from __future__ import annotations
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, Optional
import yaml

# ---------- core cached loader ----------


def _default_schemes_path() -> Path:
    # points at mplhockey/colours/schemes.yaml inside the package
    return files("mplhockey.colours").joinpath("schemes.yaml")


@lru_cache(maxsize=1)
def get_colour_schemes(path: Optional[str | Path] = None) -> dict:
    """
    Load and cache the colour schemes file. If no path is provided, uses the
    packaged mplhockey/colours/schemes.yaml. Cached across calls.
    """
    target = Path(path) if path else _default_schemes_path()
    with target.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, Mapping) or "schemes" not in data or not isinstance(data["schemes"], Mapping):
        raise ValueError("schemes.yaml must have a top-level 'schemes' mapping")

    return dict(data["schemes"])  # shallow copy to decouple from YAML internals


def clear_colour_scheme_cache() -> None:
    """For dev/hot-reload: clear the cached result so next call re-reads the file."""
    get_colour_schemes.cache_clear()


# ---------- helpers & pickers ----------


def _extract_colors_block(scheme: Mapping[str, Any]) -> dict:
    if "colours" in scheme and isinstance(scheme["colours"], Mapping):
        return dict(scheme["colours"])
    if "colors" in scheme and isinstance(scheme["colors"], Mapping):
        return dict(scheme["colors"])
    raise ValueError("Scheme is missing a 'colours' (or 'colors') mapping")


def pick_scheme(name: str, default: str | None = None, *, path: Optional[str | Path] = None) -> dict:
    """
    Return the color dict for `name`. Falls back to `default` if provided.
    """
    schemes = get_colour_schemes(path)
    if name in schemes:
        return _extract_colors_block(schemes[name])
    if default and default in schemes:
        return _extract_colors_block(schemes[default])
    raise KeyError(f"Color scheme '{name}' not found")


def resolve_colour_theme(theme: Any, *, fallback: str = "light", path: Optional[str | Path] = None) -> dict:
    """
    Accepts:
      - a scheme name (str) -> looks up in cached schemes.yaml
      - a dict of direct colour values -> returned as-is
      - anything else -> falls back to `fallback`
    """
    if isinstance(theme, dict):
        return pick_scheme(fallback) | theme
    if isinstance(theme, str):
        try:
            return pick_scheme(theme, default=fallback, path=path)
        except KeyError:
            return pick_scheme(fallback, path=path)
    return pick_scheme(fallback, path=path)
