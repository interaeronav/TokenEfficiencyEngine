"""Context awareness (9.5, A15): the style brief and sun-true lighting.

Style brief: auto-derived from what TEE already extracted - CIELAB k-means
palette from site photos (color NAMES are the in-context form), style/
material terms from the caption pass, avoid-list from the audio brief.

Sun: azimuth/elevation computed server-side from the GPS datum and
date/time - astral (Apache-2.0) as the default engine; pvlib SPA is the
optional precision upgrade; pysolar is GPL and BANNED (CI-linted).
Drives Blender sun/Nishita sky and the UE directional light through the
normal adapters; HDRIs are picked by elevation band + weather, with each
HDRI's in-image sun azimuth detected once (brightest pixel) and cached.
"""

from __future__ import annotations

import math
from datetime import datetime
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# -- style brief ------------------------------------------------------------


def style_brief(store, extract_store=None, *, max_photos: int = 6) -> dict[str, Any]:
    """Compact style facts from the extract store (photos + captions +
    transcripts). Degrades gracefully: with nothing ingested, returns an
    empty brief the caller can fill by hand."""
    from tee.assets.color import image_palette

    brief: dict[str, Any] = {"palette": [], "terms": [], "avoid": []}
    if extract_store is None:
        return brief
    photos = 0
    weights: dict[str, float] = {}
    labs: dict[str, list[float]] = {}
    for source in extract_store.sources():
        if source.get("media_type") != "image" or photos >= max_photos:
            continue
        path = Path(source["paths"][0])
        if not path.exists():
            continue
        try:
            palette = image_palette(path, k=5)
        except Exception:
            continue
        photos += 1
        for color in palette:
            weights[color["name"]] = weights.get(color["name"], 0.0) + color["weight"]
            labs.setdefault(color["name"], color["lab"])
        for fact in extract_store.facts(source["hash"], kind="caption"):
            for term in _style_terms(str(fact.get("text", ""))):
                if term not in brief["terms"]:
                    brief["terms"].append(term)
    top = sorted(weights.items(), key=lambda pair: -pair[1])[:6]
    brief["palette"] = [
        {"name": name, "lab": labs[name], "weight": round(w / max(photos, 1), 3)} for name, w in top
    ]
    for source in extract_store.sources():
        for fact in extract_store.facts(source["hash"], kind="transcript"):
            brief["avoid"].extend(_avoid_terms(str(fact.get("text", ""))))
    brief["avoid"] = sorted(set(brief["avoid"]))[:8]
    if photos:
        brief["photos_sampled"] = photos
    return brief


_STYLE_WORDS = {
    "modern",
    "minimal",
    "minimalist",
    "rustic",
    "industrial",
    "scandinavian",
    "vintage",
    "victorian",
    "contemporary",
    "traditional",
    "bohemian",
    "wood",
    "wooden",
    "concrete",
    "brick",
    "marble",
    "stone",
    "steel",
    "brass",
    "linen",
    "leather",
    "thatch",
    "warm",
    "cozy",
    "bright",
    "dark",
}


def _style_terms(text: str) -> list[str]:
    words = [w.strip(".,;:!?").lower() for w in text.split()]
    return [w for w in words if w in _STYLE_WORDS]


def _avoid_terms(text: str) -> list[str]:
    """Phrases after 'no X' / 'avoid X' / "don't want X" in the brief."""
    out = []
    words = [w.strip(".,;:!?").lower() for w in text.split()]
    for i, word in enumerate(words):
        if word in ("no", "avoid") and i + 1 < len(words):
            candidate = words[i + 1]
            if candidate.isalpha() and candidate not in ("one", "more", "the", "a", "an"):
                out.append(candidate)
        if word in ("don't", "dont") and i + 2 < len(words) and words[i + 1] == "want":
            out.append(words[i + 2])
    return out


# -- sun position -----------------------------------------------------------


def sun_position(lat: float, lon: float, when_iso: str, *, tz: str | None = None) -> dict[str, Any]:
    """Solar azimuth (deg from north, CW) + elevation (deg) via astral.
    `when_iso` may carry an offset; else `tz` (IANA name) applies; else UTC.
    """
    try:
        from astral import Observer
        from astral.sun import azimuth as sun_azimuth
        from astral.sun import elevation as sun_elevation
    except ImportError as exc:
        raise TeeError(
            "assets_extra_missing",
            "Sun positioning needs astral (the [assets] extra).",
            fix="uv sync --extra assets",
        ) from exc
    try:
        when = datetime.fromisoformat(when_iso)
    except ValueError as exc:
        raise TeeError(
            "bad_datetime",
            f"'{when_iso}' is not ISO-8601.",
            fix="Example: 2026-06-21T14:30:00+02:00 (offset optional).",
        ) from exc
    if when.tzinfo is None:
        from zoneinfo import ZoneInfo

        when = when.replace(tzinfo=ZoneInfo(tz) if tz else ZoneInfo("UTC"))
    observer = Observer(latitude=lat, longitude=lon)
    az = sun_azimuth(observer, when)
    el = sun_elevation(observer, when)
    out = {
        "azimuth_deg": round(az, 2),
        "elevation_deg": round(el, 2),
        "when": when.isoformat(),
        "engine": "astral",
    }
    if el < -0.833:
        out["note"] = "sun below horizon - night scene"
    return out


def sun_ops(
    adapter_name: str, position: dict[str, Any], *, energy: float = 3.0
) -> list[dict[str, Any]]:
    """Typed batch ops that realize a sun position in the DCC. Blender sun
    lights point along -Z; rotate X by (90 - elevation) then Z by -azimuth
    (Blender +Y is north here, matching the site ENU frame convention)."""
    el = float(position["elevation_deg"])
    az = float(position["azimuth_deg"])
    rot = [math.radians(90.0 - el), 0.0, math.radians(-az)]
    return [
        {
            "op": "create",
            "kind": "light",
            "name": "TEE_Sun",
            "props": {
                "light_type": "SUN",
                "energy": energy,
                "rotation_euler": [round(v, 5) for v in rot],
                "sun_azimuth_deg": az,
                "sun_elevation_deg": el,
            }
            if adapter_name == "fake"
            else {
                "light_type": "SUN",
                "energy": energy,
                "rotation_euler": [round(v, 5) for v in rot],
            },
        }
    ]


# -- HDRI selection ---------------------------------------------------------

_HDRI_BANDS = [
    (-90.0, 0.0, "night"),
    (0.0, 10.0, "sunrise-sunset"),
    (10.0, 35.0, "morning-evening"),
    (35.0, 90.0, "midday"),
]


def hdri_query(elevation_deg: float, weather: str = "clear") -> dict[str, Any]:
    """Poly Haven search facets for a sun-matched HDRI + the world-rotation
    recipe (computed azimuth minus the HDRI's own detected sun azimuth)."""
    band = next((name for lo, hi, name in _HDRI_BANDS if lo <= elevation_deg < hi), "midday")
    keywords = {
        "night": "night sky",
        "sunrise-sunset": "sunset golden hour",
        "morning-evening": "morning outdoor",
        "midday": "midday clear outdoor",
    }[band]
    if weather != "clear":
        keywords = f"{keywords} {weather}"
    return {
        "band": band,
        "search": keywords,
        "note": "world rotation = computed azimuth - HDRI sun azimuth "
        "(detected once via brightest pixel, cached as a fact)",
    }


def detect_hdri_sun_azimuth(path: Path) -> dict[str, Any]:
    """Brightest-pixel azimuth in an equirectangular HDRI (0 = +X seam,
    degrees CW when viewed from above). Cached by callers as a fact."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise TeeError(
            "extract_extra_missing",
            "HDRI analysis needs Pillow (the [extract] extra).",
            fix="uv sync --extra extract",
        ) from exc
    with Image.open(path) as img:
        img = img.convert("L")
        img.thumbnail((512, 256))
        width, _height = img.size
        pixels = list(img.getdata())
    index = max(range(len(pixels)), key=pixels.__getitem__)
    x = index % width
    azimuth = (x / width) * 360.0
    return {"azimuth_deg": round(azimuth, 1), "method": "brightest-pixel"}
