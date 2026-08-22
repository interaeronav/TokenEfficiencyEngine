"""Color science for style matching (A15, research 25 R5-R9): sRGB→CIELAB,
CIEDE2000 (Sharma 2005 formulation, tested against the reference pairs),
a small k-means for palette extraction, and color NAMING - names are the
in-context form (a palette costs ~6 tokens as names, hundreds as numbers).
Pure Python; images are sampled down before clustering so no numpy needed.
"""

from __future__ import annotations

import math
from pathlib import Path

# -- sRGB -> CIELAB (D65) ---------------------------------------------------


def srgb_to_lab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """rgb in 0..1 (or 0..255, auto-detected)."""
    r, g, b = rgb
    if max(r, g, b) > 1.0:
        r, g, b = r / 255.0, g / 255.0, b / 255.0

    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linear(r), linear(g), linear(b)
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


# -- CIEDE2000 --------------------------------------------------------------


def delta_e2000(
    lab1: tuple[float, float, float], lab2: tuple[float, float, float]
) -> float:
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1 = math.hypot(a1, b1)
    c2 = math.hypot(a2, b2)
    c_bar = (c1 + c2) / 2
    g = 0.5 * (1 - math.sqrt(c_bar**7 / (c_bar**7 + 25**7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)

    def hue(ap: float, b: float) -> float:
        if ap == 0 and b == 0:
            return 0.0
        h = math.degrees(math.atan2(b, ap))
        return h + 360 if h < 0 else h

    h1p, h2p = hue(a1p, b1), hue(a2p, b2)
    dl = l2 - l1
    dc = c2p - c1p
    if c1p * c2p == 0:
        dh_deg = 0.0
    elif abs(h2p - h1p) <= 180:
        dh_deg = h2p - h1p
    elif h2p - h1p > 180:
        dh_deg = h2p - h1p - 360
    else:
        dh_deg = h2p - h1p + 360
    dh = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh_deg) / 2)

    l_bar = (l1 + l2) / 2
    c_bar_p = (c1p + c2p) / 2
    if c1p * c2p == 0:
        h_bar = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        h_bar = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        h_bar = (h1p + h2p + 360) / 2
    else:
        h_bar = (h1p + h2p - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(h_bar - 30))
        + 0.24 * math.cos(math.radians(2 * h_bar))
        + 0.32 * math.cos(math.radians(3 * h_bar + 6))
        - 0.20 * math.cos(math.radians(4 * h_bar - 63))
    )
    d_theta = 30 * math.exp(-(((h_bar - 275) / 25) ** 2))
    r_c = 2 * math.sqrt(c_bar_p**7 / (c_bar_p**7 + 25**7))
    s_l = 1 + 0.015 * (l_bar - 50) ** 2 / math.sqrt(20 + (l_bar - 50) ** 2)
    s_c = 1 + 0.045 * c_bar_p
    s_h = 1 + 0.015 * c_bar_p * t
    r_t = -math.sin(math.radians(2 * d_theta)) * r_c
    return math.sqrt(
        (dl / s_l) ** 2
        + (dc / s_c) ** 2
        + (dh / s_h) ** 2
        + r_t * (dc / s_c) * (dh / s_h)
    )


# -- k-means palette --------------------------------------------------------


def kmeans_palette(
    pixels: list[tuple[float, float, float]], k: int = 6, iterations: int = 12
) -> list[tuple[tuple[float, float, float], float]]:
    """K-means in CIELAB over pre-sampled pixels; returns [(lab, weight)]
    sorted by weight. Deterministic (seeded by spread) - no RNG."""
    if not pixels:
        return []
    labs = [srgb_to_lab(p) for p in pixels]
    k = min(k, len(labs))
    # deterministic init: sort by L and take evenly spaced seeds
    ordered = sorted(labs)
    centers = [ordered[int(i * (len(ordered) - 1) / max(1, k - 1))] for i in range(k)]
    assign = [0] * len(labs)
    for _ in range(iterations):
        changed = False
        for i, lab in enumerate(labs):
            best = min(
                range(k),
                key=lambda c: (lab[0] - centers[c][0]) ** 2
                + (lab[1] - centers[c][1]) ** 2
                + (lab[2] - centers[c][2]) ** 2,
            )
            if best != assign[i]:
                assign[i] = best
                changed = True
        for c in range(k):
            members = [labs[i] for i in range(len(labs)) if assign[i] == c]
            if members:
                centers[c] = (
                    sum(m[0] for m in members) / len(members),
                    sum(m[1] for m in members) / len(members),
                    sum(m[2] for m in members) / len(members),
                )
        if not changed:
            break
    weights = [assign.count(c) / len(labs) for c in range(k)]
    palette = sorted(zip(centers, weights, strict=True), key=lambda cw: -cw[1])
    return [(c, w) for c, w in palette if w > 0]


def image_palette(path: Path, k: int = 6, sample: int = 48) -> list[dict]:
    """Palette of one image as compact facts: [{name, lab, weight}]."""
    from PIL import Image

    with Image.open(path) as img:
        img = img.convert("RGB")
        img.thumbnail((sample, sample))
        pixels = list(img.getdata())
    palette = kmeans_palette(pixels, k=k)
    return [
        {
            "name": name_lab(lab),
            "lab": [round(v, 1) for v in lab],
            "weight": round(weight, 3),
        }
        for lab, weight in palette
    ]


# -- color naming -----------------------------------------------------------

# Compact reference anchors (name -> sRGB). Chosen for interior/architecture
# vocabulary; nearest-ΔE00 wins.
_NAMED = {
    "black": (20, 20, 20),
    "charcoal": (54, 57, 59),
    "gray": (128, 128, 128),
    "light gray": (190, 190, 190),
    "white": (245, 245, 245),
    "cream": (245, 237, 215),
    "beige": (222, 205, 175),
    "tan": (195, 165, 125),
    "brown": (120, 85, 55),
    "dark brown": (72, 50, 35),
    "terracotta": (190, 105, 75),
    "red": (190, 45, 45),
    "burgundy": (110, 30, 45),
    "orange": (225, 130, 50),
    "amber": (230, 175, 65),
    "yellow": (235, 210, 80),
    "olive": (125, 125, 60),
    "green": (80, 140, 75),
    "dark green": (40, 85, 55),
    "sage": (155, 170, 140),
    "teal": (45, 125, 125),
    "sky blue": (135, 185, 225),
    "blue": (60, 105, 175),
    "navy": (35, 50, 90),
    "purple": (115, 75, 145),
    "pink": (225, 160, 175),
}

_NAMED_LAB = {name: srgb_to_lab(rgb) for name, rgb in _NAMED.items()}


def name_lab(lab: tuple[float, float, float]) -> str:
    return min(_NAMED_LAB, key=lambda n: delta_e2000(lab, _NAMED_LAB[n]))


def name_rgb(rgb: tuple[float, float, float]) -> str:
    return name_lab(srgb_to_lab(rgb))


def palette_distance(
    palette_a: list[tuple[float, float, float]],
    palette_b: list[tuple[float, float, float]],
) -> float:
    """Asymmetric palette match: mean over A of the nearest ΔE00 in B.
    Used to rank candidate assets (A) against the style brief (B)."""
    if not palette_a or not palette_b:
        return 100.0
    total = 0.0
    for lab in palette_a:
        total += min(delta_e2000(lab, other) for other in palette_b)
    return total / len(palette_a)
