"""SI-B21 — one door for opening image files, so HEIC works everywhere.

TEE opened images with a bare `PIL.Image.open` in seven places across five
modules. Pillow ships no HEIF plugin, so every one of them raised
`UnidentifiedImageError` on a `.heic` file — the native format of the
owner's capture device, and a format `docs/okongo-capture-protocol.md`
explicitly says photos arrive in ("HEIC/DNG/JPG as shot"). The extract lane
was rejecting the camera it was built for.

`pillow-heif` registers a real Pillow plugin, so once it is registered the
existing `Image.open` / `img.save` calls read and write HEIC unchanged.
The registration has to happen before the first open, which is why this
module exists rather than a line in each call site: one place to get right,
and one place to look when it is wrong.

**Licence, recorded rather than discovered later.** pillow-heif's source is
BSD-3-Clause, but its own bundled manifest says: "License for 'pillow-heif'
binary wheels: GPLv2, due to base library licenses" (libheif LGPLv3 plus
GPLv2 codecs). TEE is private and not distributed, and this is an OPTIONAL
extra the owner installs themselves rather than anything shipped inside the
.mcpb — so no copyleft obligation is triggered. If TEE is ever distributed,
this is the dependency to look at first.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError

# Formats Pillow cannot open until the HEIF plugin is registered.
HEIF_SUFFIXES = frozenset({".heic", ".heif", ".hif", ".heics", ".avif"})

_lock = threading.Lock()
_state: dict[str, Any] = {"registered": None}  # None = not yet tried


def heif_available() -> bool:
    """True when HEIC can actually be read, having tried to register."""
    return _register() is True


def _register() -> bool:
    """Idempotent, thread-safe, and cheap after the first call. Returns
    False rather than raising: a caller opening a JPEG must not be broken
    by the absence of an optional HEIC plugin."""
    if _state["registered"] is not None:
        return bool(_state["registered"])
    with _lock:
        if _state["registered"] is not None:
            return bool(_state["registered"])
        try:
            import pillow_heif

            pillow_heif.register_heif_opener()
            _state["registered"] = True
        except Exception:
            # ImportError, or a wheel whose native lib will not load.
            _state["registered"] = False
    return bool(_state["registered"])


def _heif_refusal(path: Path) -> TeeError:
    return TeeError(
        "image_heif_unsupported",
        f"{path.name} is a HEIF/HEIC image and the HEIF plugin is not installed.",
        fix="uv pip install 'tee-engine[extract]'  (brings pillow-heif). "
        "Or convert first:  sips -s format jpeg in.heic --out out.jpg",
    )


def open_image(path: str | Path):
    """`PIL.Image.open` with HEIF registered first.

    Returns the Pillow image, so every existing use — context manager,
    `ImageOps.exif_transpose`, `getexif()` — keeps working unchanged.
    """
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:  # Pillow itself absent, not just the plugin
        raise TeeError(
            "image_pillow_missing",
            "Reading images needs Pillow, which is not installed.",
            fix="uv pip install 'tee-engine[extract]'",
        ) from exc

    p = Path(path)
    is_heif = p.suffix.lower() in HEIF_SUFFIXES
    if is_heif and not _register():
        raise _heif_refusal(p)
    _register()  # cheap after the first call; also covers a mislabelled suffix
    try:
        return Image.open(p)
    except UnidentifiedImageError as exc:
        if is_heif:
            raise _heif_refusal(p) from exc
        raise TeeError(
            "image_unreadable",
            f"{p.name} is not an image Pillow can read.",
            fix="Check the file is not truncated, and that its extension matches its contents.",
        ) from exc


def save_image(img, path: str | Path, **kwargs: Any) -> Path:
    """`img.save` with HEIF registered first, so writing .heic works.

    Pillow picks the writer from the suffix; registering the plugin is what
    makes `.heic` a suffix it knows.
    """
    p = Path(path)
    if p.suffix.lower() in HEIF_SUFFIXES and not _register():
        raise _heif_refusal(p)
    _register()
    img.save(p, **kwargs)
    return p
