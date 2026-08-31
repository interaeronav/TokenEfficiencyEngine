"""Image lane (7.3): local EXIF/GPS, phash dedupe, labeled contact sheets,
token-budget-first crops. Claude never receives EXIF and bills images purely
by rendered dimensions (ceil(w/28) x ceil(h/28) tokens), so serving
parameters are token budgets and pixel sizes are derived (research 12/14).
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.imaging import open_image

IMAGE_EXTRACTOR = ("image", "1")
PATCH = 28
STANDARD_EDGE_CAP = 1568  # safe on every model tier
DEDUPE_HAMMING = 5
SIMILAR_HAMMING = 10


def image_tokens(width: int, height: int) -> int:
    return math.ceil(width / PATCH) * math.ceil(height / PATCH)


def size_for_budget(width: int, height: int, token_budget: int) -> tuple[int, int]:
    """Largest (w, h) preserving aspect whose patch cost fits the budget and
    the standard-tier edge cap."""
    token_budget = max(4, token_budget)
    scale = min(
        1.0,
        math.sqrt(token_budget * PATCH * PATCH / (width * height)),
        STANDARD_EDGE_CAP / max(width, height),
    )
    w, h = max(PATCH, int(width * scale)), max(PATCH, int(height * scale))
    while image_tokens(w, h) > token_budget and (w > PATCH or h > PATCH):
        w, h = max(PATCH, int(w * 0.95)), max(PATCH, int(h * 0.95))
    return w, h


def extract_image(path: Path) -> list[dict[str, Any]]:
    import imagehash
    from PIL import ExifTags, ImageOps

    facts: list[dict[str, Any]] = []
    with open_image(path) as img:
        img = ImageOps.exif_transpose(img)
        fact: dict[str, Any] = {
            "kind": "photo",
            "width": img.width,
            "height": img.height,
            "phash": str(imagehash.phash(img)),
            "full_view_tokens": image_tokens(*size_for_budget(img.width, img.height, 10**9)),
        }
        exif = img.getexif()
        taken = exif.get(306) or exif.get(36867)  # DateTime / DateTimeOriginal
        if taken:
            fact["taken_at"] = str(taken)
        gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
        coords = _parse_gps(gps) if gps else None
        if coords:
            facts.append(
                {
                    "kind": "gps",
                    "tier": "gps_prior",
                    "lat": coords[0],
                    "lon": coords[1],
                    "alt": coords[2],
                    "note": "EXIF GPS ~5m horizontal; locates the parcel, never scales the model",
                }
            )
            fact["gps"] = True
        facts.append(fact)
    return facts


def _parse_gps(gps) -> tuple[float, float, float | None] | None:
    def to_deg(values, ref, negative_refs):
        try:
            d, m, s = (float(v) for v in values)
        except (TypeError, ValueError):
            return None
        deg = d + m / 60 + s / 3600
        return -deg if ref in negative_refs else deg

    lat = to_deg(gps.get(2), gps.get(1), ("S",))
    lon = to_deg(gps.get(4), gps.get(3), ("W",))
    if lat is None or lon is None:
        return None
    alt = gps.get(6)
    return lat, lon, float(alt) if alt is not None else None


def dedupe_photos(photos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group by phash: hamming <= 5 collapses, 6-10 flags similar. Input
    entries need `hash` (source) and `phash`; returns group facts."""
    import imagehash

    hashes = [(p["hash"], imagehash.hex_to_hash(p["phash"])) for p in photos]
    groups: list[dict[str, Any]] = []
    assigned: set[str] = set()
    for i, (h1, p1) in enumerate(hashes):
        if h1 in assigned:
            continue
        duplicates, similar = [], []
        for h2, p2 in hashes[i + 1 :]:
            if h2 in assigned:
                continue
            distance = p1 - p2
            if distance <= DEDUPE_HAMMING:
                duplicates.append(h2[:8])
                assigned.add(h2)
            elif distance <= SIMILAR_HAMMING:
                similar.append(h2[:8])
        assigned.add(h1)
        groups.append(
            {
                "kind": "photo_group",
                "representative": h1[:8],
                "duplicates": duplicates,
                "similar": similar,
            }
        )
    return groups


def contact_sheet(
    entries: list[dict[str, Any]], out_path: Path, *, cols: int = 3, cell: int = 400
) -> dict[str, Any]:
    """Labeled thumbnail grid: one bounded image instead of N photos. Each
    entry: {'path': file, 'label': short id}. Returns sheet fact."""
    from PIL import Image, ImageDraw

    entries = entries[: cols * cols * 2]
    rows = math.ceil(len(entries) / cols)
    pad, label_h = 6, 22
    sheet = Image.new(
        "RGB",
        (cols * (cell + pad) + pad, rows * (cell + label_h + pad) + pad),
        (24, 24, 24),
    )
    draw = ImageDraw.Draw(sheet)
    manifest = []
    for index, entry in enumerate(entries):
        r, c = divmod(index, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + label_h + pad)
        try:
            with open_image(entry["path"]) as img:
                img.thumbnail((cell, cell))
                sheet.paste(img, (x, y + label_h))
        except OSError:
            continue
        draw.text((x + 2, y + 3), f"[{index + 1}] {entry['label']}", fill=(255, 255, 90))
        manifest.append({"cell": index + 1, "label": entry["label"]})
    sheet.save(out_path, "JPEG", quality=80)
    return {
        "kind": "contact_sheet",
        "path": str(out_path),
        "cells": manifest,
        "tokens": image_tokens(sheet.width, sheet.height),
    }


def budgeted_jpeg(
    path: Path, token_budget: int, region: list[int] | None = None
) -> tuple[bytes, dict[str, Any]]:
    """Crop (optional, source pixels [x, y, w, h]) + resize to the token
    budget; returns (jpeg bytes, info)."""
    import io

    from PIL import ImageOps

    with open_image(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        if region:
            if len(region) != 4:
                raise TeeError("bad_region", "region must be [x, y, w, h] in source pixels.")
            x, y, w, h = region
            img = img.crop((x, y, x + w, y + h))
        w, h = size_for_budget(img.width, img.height, token_budget)
        img = img.resize((w, h))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        return buf.getvalue(), {"width": w, "height": h, "tokens": image_tokens(w, h)}


def ground_resolution_m_per_px(lat_deg: float, zoom: int) -> float:
    """Web-mercator ground resolution; EPSG:3857 is fetch-only (A10)."""
    return 40_075_016.686 * math.cos(math.radians(lat_deg)) / (2 ** (zoom + 8))
