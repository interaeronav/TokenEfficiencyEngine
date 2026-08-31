"""SI-B21 — HEIC reads and writes everywhere TEE opens an image.

Before this, `PIL.Image.open` was called bare in nine places and Pillow
ships no HEIF plugin, so every one raised `UnidentifiedImageError` on the
format the owner's iPhone actually shoots — while
`docs/okongo-capture-protocol.md` says photos arrive "HEIC/DNG/JPG as shot".
The extract lane rejected the camera it was built for.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

from tee.kernel import imaging
from tee.kernel.errors import TeeError

heif = pytest.mark.skipif(not imaging.heif_available(), reason="pillow-heif not installed")


def _heic(tmp_path):
    """A real HEIC, written by the same plugin under test. Round-tripping
    through the plugin is the point: it proves read and write agree."""
    from PIL import Image

    src = Image.new("RGB", (64, 48), (200, 90, 30))
    return imaging.save_image(src, tmp_path / "fixture.heic", quality=70)


@heif
def test_a_heic_round_trips(tmp_path):
    p = _heic(tmp_path)
    assert p.stat().st_size > 0
    with imaging.open_image(p) as img:
        assert img.size == (64, 48)
        assert img.format == "HEIF"


@heif
def test_ordinary_formats_are_untouched(tmp_path):
    """Registering a plugin must not disturb the paths that already worked."""
    from PIL import Image

    for suffix in (".jpg", ".png"):
        p = imaging.save_image(Image.new("RGB", (32, 16), (10, 20, 30)), tmp_path / f"x{suffix}")
        with imaging.open_image(p) as img:
            assert img.size == (32, 16)


@heif
def test_the_extract_lane_reads_a_heic_end_to_end(tmp_path):
    from tee.extract.images import extract_image

    facts = extract_image(_heic(tmp_path))
    photo = [f for f in facts if f["kind"] == "photo"]
    assert photo and photo[0]["width"] == 64 and photo[0]["height"] == 48


def test_a_missing_plugin_refuses_with_the_exact_fix(tmp_path, monkeypatch):
    """The refusal has to name the install line. A bare
    UnidentifiedImageError is the thing this module exists to stop."""
    monkeypatch.setitem(imaging._state, "registered", False)
    with pytest.raises(TeeError) as e:
        imaging.open_image(tmp_path / "nope.heic")
    assert e.value.code == "image_heif_unsupported"
    assert "tee-engine[extract]" in e.value.fix
    assert "sips" in e.value.fix  # the no-install escape hatch


def test_registration_is_idempotent_and_cached():
    imaging._state["registered"] = None
    first = imaging.heif_available()
    assert imaging._state["registered"] is first
    assert imaging.heif_available() is first


def test_no_module_opens_an_image_file_behind_this_helpers_back():
    """The guard that keeps the fix from decaying: a new bare
    `Image.open(<path>)` anywhere in the tree reintroduces the bug for that
    call site only, which is exactly how this got to nine places."""
    root = pathlib.Path(imaging.__file__).parent.parent
    offenders = []
    for py in root.rglob("*.py"):
        if py.name == "imaging.py":
            continue
        try:
            tree = ast.parse(py.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            if not (isinstance(f, ast.Attribute) and f.attr == "open"):
                continue
            if not (isinstance(f.value, ast.Name) and f.value.id == "Image"):
                continue
            # Image.open(BytesIO(...)) is in-memory bytes, not a file path
            arg = node.args[0] if node.args else None
            if isinstance(arg, ast.Call) and "BytesIO" in ast.dump(arg):
                continue
            offenders.append(f"{py.relative_to(root)}:{node.lineno}")
    assert offenders == [], (
        "bare Image.open on a path - use tee.kernel.imaging.open_image so "
        f"HEIC keeps working: {offenders}"
    )
