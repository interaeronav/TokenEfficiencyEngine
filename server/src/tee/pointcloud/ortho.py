"""Rectified orthographic images of a facade, to trace elevations from.

A photograph of a wall cannot be traced: it carries perspective, so a window
2 m away and one 6 m away are drawn at different scales. An orthographic
projection of the cloud has no vanishing point, so a millimetre is the same
length everywhere on the image and a ruler laid on the print means something.

The scale bar and the origin marker are burned INTO the pixels rather than
drawn alongside. An image is cropped, pasted and re-scaled by people who never
saw the tool that made it, and a scale printed outside the frame does not
survive that; one inside it does.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tee.kernel.errors import TeeError

MAX_PIXELS = 40_000_000
BAR_METRES = 1.0


def rectify(points: np.ndarray, azimuth_deg: float) -> np.ndarray:
    """Rotate about Z so the named facade faces the viewer; return (u, z, depth)."""
    rad = np.deg2rad(float(azimuth_deg))
    across = np.array([np.cos(rad), np.sin(rad)])
    into = np.array([-np.sin(rad), np.cos(rad)])
    return np.c_[points[:, :2] @ across, points[:, 2], points[:, :2] @ into]


def render(
    points: np.ndarray,
    out: Path,
    *,
    azimuth_deg: float,
    px_per_m: float = 100.0,
    colors: np.ndarray | None = None,
    depth_m: float | None = None,
    spacing_m: float | None = None,
) -> dict:
    """Write a rectified PNG of one facade and report what it covers."""
    from PIL import Image

    if px_per_m <= 0:
        raise TeeError(
            "pc_bad_resolution", "px_per_m must be positive.", fix="Try 100 for 10 mm pixels."
        )
    rect = rectify(points, azimuth_deg)
    if depth_m is not None:
        near = rect[:, 2] <= rect[:, 2].min() + float(depth_m)
        rect = rect[near]
        colors = None if colors is None else colors[near]
    if len(rect) < 100:
        raise TeeError(
            "pc_empty_facade",
            f"Only {len(rect)} points face this way.",
            fix="Check the azimuth; it is the direction the facade LOOKS, in degrees.",
        )

    u, z = rect[:, 0] - rect[:, 0].min(), rect[:, 1] - rect[:, 1].min()
    width = int(np.ceil(u.max() * px_per_m)) + 1
    height = int(np.ceil(z.max() * px_per_m)) + 1
    if width * height > MAX_PIXELS:
        raise TeeError(
            "pc_image_too_large",
            f"{width} x {height} px is {width * height / 1e6:.0f} MP.",
            fix=f"Lower px_per_m to about {px_per_m * (MAX_PIXELS / (width * height)) ** 0.5:.0f}.",
        )

    ix = np.clip((u * px_per_m).astype(int), 0, width - 1)
    iy = np.clip((height - 1 - z * px_per_m).astype(int), 0, height - 1)
    img = np.full((height, width, 3), 255, np.uint8)
    covered = np.zeros((height, width), bool)
    # nearest surface wins, so a facade is not shown through its own openings
    order = np.argsort(-rect[:, 2])
    if colors is not None and len(colors) == len(rect):
        paint = colors[order]
    else:
        shade = np.clip(255 - (rect[:, 2] - rect[:, 2].min()) * 255 / 2.0, 0, 255).astype(np.uint8)
        paint = np.repeat(shade[order, None], 3, axis=1)

    # Each point is a SAMPLE, not a pixel. Asked for 10 mm pixels on a cloud
    # sampled every 30 mm, one-pixel splats give a 64%-white stipple that
    # reads as a texture rather than a surface - the exact complaint the
    # depth rasters drew. So a point paints its own footprint: dot px wide,
    # derived from the measured spacing. Nothing is invented; the sample is
    # simply drawn at the size it actually represents.
    dot = 1 if spacing_m is None else int(np.clip(round(spacing_m * px_per_m), 1, 9))
    span = range(-(dot // 2), dot - dot // 2)
    for dy in span:
        for dx in span:
            yy = np.clip(iy[order] + dy, 0, height - 1)
            xx = np.clip(ix[order] + dx, 0, width - 1)
            img[yy, xx] = paint
            covered[yy, xx] = True

    _burn_scale(img, px_per_m)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(out)
    return {
        "path": str(out),
        "px_per_m": round(float(px_per_m), 2),
        "pixels": [width, height],
        "extent_m": [round(float(u.max()), 3), round(float(z.max()), 3)],
        "coverage": round(float(covered.mean()), 3),
        "points_drawn": len(rect),
        "mm_per_pixel": round(1000.0 / px_per_m, 2),
        "dot_px": dot,
    }


def _burn_scale(img: np.ndarray, px_per_m: float) -> None:
    """A 1 m checker bar and an origin cross, in the pixels themselves."""
    height, width = img.shape[:2]
    bar = int(BAR_METRES * px_per_m)
    thick = max(2, int(0.02 * px_per_m))
    x0, y0 = thick * 2, height - thick * 4
    if bar + x0 >= width or y0 <= 0:
        return
    for i in range(bar):
        shade = 0 if (i // max(1, bar // 10)) % 2 == 0 else 255
        img[y0 : y0 + thick, x0 + i] = shade
    img[y0 - thick : y0 + thick * 2, x0] = 0
    img[y0 - thick : y0 + thick * 2, x0 + bar] = 0
    # origin cross at the image's own (0, 0), which is bottom-left
    arm = int(0.10 * px_per_m)
    img[height - 1 - arm : height, 0:thick] = 0
    img[height - thick : height, 0:arm] = 0
