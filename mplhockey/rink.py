from mplhockey.base import Rink, get_rotated_bounds
from pathlib import Path


def rink_dims_path() -> Path:
    """Path to rink dimensions directory in the package."""
    return Path(__file__).resolve().parent / "rink_dims"


def NHLRink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "nhl.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )


def NCAARink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "ncaa.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )


def IIHFRink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "iihf.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )


def KHLRink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "khl.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )


def PWHLRink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "pwhl.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )


def NRLRink(theme=None, fallback="light", linewidth=None, **kwargs):
    return Rink.from_yaml(
        rink_dims_path() / "nrl.yaml",
        theme=theme,
        fallback=fallback,
        linewidth=linewidth,
        **kwargs,
    )
