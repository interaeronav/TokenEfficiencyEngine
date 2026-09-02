"""The flag of Namibia, drawn rather than downloaded.

From the 1990 specification: ratio 2:3; a red diagonal band from the lower
hoist to the upper fly, edged in white; the upper-hoist triangle blue, the
lower-fly triangle green; a gold sun with twelve triangular rays in the blue.
Drawn at 2:3 and stretched onto the cape's own UV rectangle, so the
proportions are the flag's and the fit is the cape's.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from examples._common import write_png

BLUE, RED, GREEN, GOLD, WHITE = (
    (0x00, 0x35, 0x80),
    (0xD2, 0x10, 0x34),
    (0x00, 0x95, 0x43),
    (0xFF, 0xCE, 0x00),
    (0xFF, 0xFF, 0xFF),
)


def namibia(width: int = 1536) -> np.ndarray:
    height = width * 2 // 3
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    u, v = xx / width, yy / height  # v: 0 at the top

    img = np.zeros((height, width, 3), dtype=np.uint8)
    # The diagonal runs lower-hoist -> upper-fly: the line v = 1 - u. Above it
    # (smaller v) is the blue hoist triangle; below it, green.
    d = (v - (1.0 - u)) / np.sqrt(2.0)
    img[...] = np.where((d < 0)[..., None], np.array(BLUE), np.array(GREEN))
    band, edge = 0.145, 0.185  # red band half-width, then the white edge
    img[np.abs(d) < edge] = WHITE
    img[np.abs(d) < band] = RED

    # the sun: centred in the blue triangle, a disc plus twelve rays
    cx, cy = 0.25 * width, 0.28 * height
    r = 0.105 * height
    dx, dy = xx - cx, yy - cy
    dist = np.hypot(dx, dy)
    angle = np.arctan2(dy, dx)
    disc = dist <= r * 0.62
    k = 12
    phase = (angle * k / (2 * np.pi)) % 1.0
    spike = np.minimum(phase, 1.0 - phase) * 2.0  # 0 at a ray's centre line
    reach = (dist - r * 0.62) / (r * 0.55)  # 0 at the disc, 1 at the tip
    ray = (reach >= 0) & (reach <= 1.0) & (spike <= (1.0 - reach) * 0.42)
    img[disc | ray] = GOLD
    return img


def write(path: str | Path, width: int = 1536) -> Path:
    return write_png(namibia(width), path)
