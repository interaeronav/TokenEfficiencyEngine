"""Creation lane 2 (A14): photo-derived PBR - the classical, always-available
path (rectify -> maps). Identity is correct (it IS the site's surface);
response is ESTIMATED and labeled so: normal from Sobel gradients,
roughness from local high-frequency energy, metallic clamped to 0 on
masonry/paint. The GPU refinements (Marigold delight/IID, Real-ESRGAN)
slot in on the physical machine behind the same function signature.

Facades of a specific building are NOT tiled - they are rectified and
UV-projected; tiling is for generic surfaces (research 24).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError


def _require_cv():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise TeeError(
            "extract_extra_missing",
            "Photo-derived PBR needs OpenCV + numpy (the [extract] extra).",
            fix="uv sync --extra extract",
        ) from exc
    return cv2, np


def rectify(
    photo: Path,
    corners: list[list[float]],
    out_path: Path,
    *,
    width_m: float,
    height_m: float,
    px_per_m: int = 512,
) -> dict[str, Any]:
    """Homography-rectify a quad (4 corners, clockwise from top-left, in
    source pixels) to a metric texture: px_per_m sets the output density."""
    cv2, np = _require_cv()
    if len(corners) != 4:
        raise TeeError(
            "bad_corners", "corners must be 4 [x, y] points, clockwise from top-left."
        )
    img = cv2.imread(str(photo))
    if img is None:
        raise TeeError("bad_image", f"Cannot read {photo}.")
    w_px, h_px = int(width_m * px_per_m), int(height_m * px_per_m)
    src = np.array(corners, dtype=np.float32)
    dst = np.array([[0, 0], [w_px, 0], [w_px, h_px], [0, h_px]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, matrix, (w_px, h_px))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), out)
    return {
        "path": str(out_path),
        "px": [w_px, h_px],
        "px_per_m": px_per_m,
        "honesty": "measured-identity",
    }


def derive_maps(
    base_color: Path,
    out_dir: Path,
    *,
    surface: str = "generic",
    normal_strength: float = 2.0,
) -> dict[str, Any]:
    """Estimated normal + roughness (+ metallic constant) from one photo.
    Classical: Sobel-gradient normals, roughness from inverted local
    high-frequency energy. Labeled 'estimated' - Marigold replaces these
    on GPU machines, same return shape."""
    cv2, np = _require_cv()
    img = cv2.imread(str(base_color), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise TeeError("bad_image", f"Cannot read {base_color}.")
    out_dir.mkdir(parents=True, exist_ok=True)
    gray = img.astype(np.float32) / 255.0

    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3) * normal_strength
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3) * normal_strength
    nz = np.ones_like(gray)
    length = np.sqrt(gx * gx + gy * gy + nz * nz)
    normal = np.stack(
        [(-gx / length + 1) / 2, (gy / length + 1) / 2, (nz / length + 1) / 2], axis=-1
    )
    normal_path = out_dir / (base_color.stem + "_normal_est.png")
    cv2.imwrite(str(normal_path), (normal[..., ::-1] * 255).astype(np.uint8))

    blur = cv2.GaussianBlur(gray, (0, 0), 4.0)
    high_freq = np.abs(gray - blur)
    energy = cv2.GaussianBlur(high_freq, (0, 0), 8.0)
    peak = float(energy.max()) or 1.0
    # busier micro-structure -> rougher; smooth areas floor at 0.35
    roughness = np.clip(0.35 + 0.6 * energy / peak, 0.0, 1.0)
    rough_path = out_dir / (base_color.stem + "_rough_est.png")
    cv2.imwrite(str(rough_path), (roughness * 255).astype(np.uint8))

    metallic = 0.0  # masonry/paint/wood: clamp (research 24)
    return {
        "base_color": str(base_color),
        "normal": str(normal_path),
        "roughness": str(rough_path),
        "metallic": metallic,
        "surface": surface,
        "honesty": "estimated (classical); GPU lane refines with Marigold-IID",
    }


def make_tileable(base_color: Path, out_path: Path, *, blend_frac: float = 0.12) -> dict[str, Any]:
    """Offset-half + linear seam blend: born-tileable for unstructured
    surfaces. Structured/facade textures should be UV-projected instead."""
    cv2, np = _require_cv()
    img = cv2.imread(str(base_color))
    if img is None:
        raise TeeError("bad_image", f"Cannot read {base_color}.")
    h, w = img.shape[:2]
    rolled = np.roll(np.roll(img, h // 2, axis=0), w // 2, axis=1).astype(np.float32)
    band_w = max(2, int(w * blend_frac))
    band_h = max(2, int(h * blend_frac))
    # blend the wrapped seams (now crossing the middle) with the original
    original = img.astype(np.float32)
    out = rolled.copy()
    for axis, band, size in ((1, band_w, w), (0, band_h, h)):
        center = size // 2
        for offset in range(-band, band):
            alpha = 0.5 * (1 - abs(offset) / band)
            index = center + offset
            if axis == 1:
                out[:, index] = (1 - alpha) * rolled[:, index] + alpha * original[:, index]
            else:
                out[index, :] = (1 - alpha) * rolled[index, :] + alpha * original[index, :]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), out.astype(np.uint8))
    return {"path": str(out_path), "note": "offset-half + seam blend (classical)"}
