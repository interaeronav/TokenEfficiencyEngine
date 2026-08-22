"""Reference-table loaders + the benchmark query API (A16, A18).

Every answer carries value + source + as_of - never a folk target. The
tables are versioned data files; changing a figure means editing data
with a new source, not editing code.
"""

from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

from tee.kernel.errors import TeeError

_FILES = (
    "benchmarks",
    "dark_patterns",
    "ux_params",
    "genres",
    "motivations",
    "economy_archetypes",
)


@cache
def load(name: str) -> dict[str, Any]:
    if name not in _FILES:
        raise TeeError(
            "unknown_table", f"No reference table '{name}'.",
            fix=f"Tables: {', '.join(_FILES)}.",
        )
    text = resources.files("tee.design").joinpath(f"data/{name}.json").read_text()
    return json.loads(text)


def as_of(name: str) -> str:
    return load(name).get("_meta", {}).get("as_of", "unknown")


def benchmark(
    metric: str, platform: str = "mobile", genre: str | None = None
) -> dict[str, Any]:
    """Answer 'what is a good D7 for mobile puzzle' with the grid value +
    source + year - the percentile grid, never folklore."""
    data = load("benchmarks")
    metric = metric.lower()
    platform = platform.lower()
    out: dict[str, Any] = {"metric": metric, "platform": platform, "as_of": as_of("benchmarks")}
    if metric in ("d1", "d7", "d30"):
        grid = data["retention"].get(platform)
        if grid is None:
            raise TeeError(
                "unknown_platform", f"No retention grid for '{platform}'.",
                fix="Platforms: mobile, pc.",
            )
        out["grid"] = grid[metric]
        if platform == "mobile":
            out["note"] = data["retention"]["mobile"]["note"]
        if genre:
            genre_grid = data["retention"].get("genre_d30_mobile", {})
            key = genre.lower().replace(" ", "_").replace("-", "_")
            for candidate in (key, f"{key}_puzzle", "match_puzzle" if "match" in key else None):
                if candidate and candidate in genre_grid:
                    out["genre_d30"] = {**genre_grid[candidate], "genre": candidate}
                    break
    elif metric in ("session", "sessions"):
        out["grid"] = data["sessions"].get(platform, data["sessions"])
    elif metric in ("wishlist", "funnel", "steam"):
        out["grid"] = data["steam_funnel"]
    elif metric in ("ftue", "tutorial"):
        out["grid"] = data["ftue"]
    elif metric in ("liveops", "season", "streak"):
        out["grid"] = data["liveops"]
    else:
        raise TeeError(
            "unknown_metric", f"No benchmark metric '{metric}'.",
            fix="Metrics: d1, d7, d30, session, funnel, ftue, liveops.",
        )
    if genre and "genre_d30" not in out:
        genres = load("genres")["genres"]
        key = genre.lower().replace(" ", "_").replace("-", "_")
        if key in genres:
            out["genre"] = {k: v for k, v in genres[key].items() if k != "label"}
    return out


def genre_conventions(genre: str) -> dict[str, Any]:
    genres = load("genres")["genres"]
    key = genre.lower().replace(" ", "_").replace("-", "_")
    if key not in genres:
        raise TeeError(
            "unknown_genre", f"No convention template for '{genre}'.",
            fix=f"Templates: {', '.join(sorted(genres))}.",
        )
    return {**genres[key], "as_of": as_of("genres")}


def opportunity_map() -> list[dict[str, Any]]:
    return load("genres")["opportunity_map"]


def scope_weights() -> dict[str, Any]:
    return load("economy_archetypes")["scope_weights"]


def archetype(name: str) -> dict[str, Any]:
    archetypes = load("economy_archetypes")["archetypes"]
    if name not in archetypes:
        raise TeeError(
            "unknown_archetype", f"No economy archetype '{name}'.",
            fix=f"Archetypes: {', '.join(sorted(archetypes))}.",
        )
    return archetypes[name]


def personas_default() -> dict[str, Any]:
    return load("motivations")["personas_default"]
