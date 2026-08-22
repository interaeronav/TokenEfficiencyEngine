"""Local library ingest (9.1.4): index the user's own asset folders.

glTF/GLB files are probed for tri counts and exact extents from the JSON
header (no DCC); loose texture sets are grouped into materials by the
map-suffix convention regex; thumbnails are phashed when Pillow is
available. Local assets carry license 'local' - they belong to the user,
so the SPDX gate does not apply, and they are marked as such in credits.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tee.assets import gltf

MODEL_SUFFIXES = {".gltf", ".glb"}
OTHER_MODEL_SUFFIXES = {".fbx", ".obj", ".stl", ".usd", ".usdc", ".usdz", ".blend"}
TEXTURE_SUFFIXES = {".png", ".jpg", ".jpeg", ".exr", ".tif", ".tiff", ".webp"}

# Map-role suffix convention: BrickWall_2k_diffuse.png / _nrm / _rough …
_MAP_RE = re.compile(
    r"(?P<stem>.+?)[_\-\. ]"
    r"(?P<role>albedo|basecolor|base_color|diff(?:use)?|col(?:or)?|"
    r"nor(?:mal)?(?:_?gl|_?dx)?|nrm|rough(?:ness)?|metal(?:lic|ness)?|"
    r"ao|ambientocclusion|occlusion|height|disp(?:lacement)?|bump|"
    r"spec(?:ular)?|arm|orm|emissive|emission|opacity|alpha)"
    r"(?:[_\-\. ].*)?$",
    re.IGNORECASE,
)

_ROLE_CANON = {
    "albedo": "base_color",
    "basecolor": "base_color",
    "base_color": "base_color",
    "diff": "base_color",
    "diffuse": "base_color",
    "col": "base_color",
    "color": "base_color",
    "nor": "normal",
    "normal": "normal",
    "nrm": "normal",
    "nor_gl": "normal",
    "normal_gl": "normal",
    "norgl": "normal",
    "nor_dx": "normal_dx",
    "normal_dx": "normal_dx",
    "nordx": "normal_dx",
    "rough": "roughness",
    "roughness": "roughness",
    "metal": "metallic",
    "metallic": "metallic",
    "metalness": "metallic",
    "ao": "ao",
    "ambientocclusion": "ao",
    "occlusion": "ao",
    "height": "height",
    "disp": "height",
    "displacement": "height",
    "bump": "height",
    "spec": "specular",
    "specular": "specular",
    "arm": "arm",
    "orm": "arm",
    "emissive": "emission",
    "emission": "emission",
    "opacity": "alpha",
    "alpha": "alpha",
}


def texture_sets(paths: list[Path]) -> dict[str, dict[str, str]]:
    """Group texture files into material sets by common stem: returns
    {set_name: {role: file path}}."""
    sets: dict[str, dict[str, str]] = {}
    for path in paths:
        if path.suffix.lower() not in TEXTURE_SUFFIXES:
            continue
        match = _MAP_RE.match(path.stem)
        if not match:
            continue
        stem = re.sub(r"[_\-\. ]+(\d+k|\d{3,4})$", "", match.group("stem"), flags=re.IGNORECASE)
        role = _ROLE_CANON.get(match.group("role").lower().replace(" ", ""))
        if role is None:
            continue
        sets.setdefault(stem, {})[role] = str(path)
    # a lone base_color is just an image, not a material set
    return {k: v for k, v in sets.items() if len(v) >= 2 or "normal" in v}


def _phash(path: Path) -> str | None:
    try:
        import imagehash
        from PIL import Image

        with Image.open(path) as img:
            return str(imagehash.phash(img))
    except Exception:
        return None


def ingest_directory(store, directory: Path) -> dict[str, Any]:
    """Index every model and texture set under `directory` into the asset
    store index (files stay in place - the user's library is not copied)."""
    directory = Path(directory)
    report: dict[str, Any] = {"models": 0, "material_sets": 0, "skipped": []}
    index = store.index()
    textures: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in MODEL_SUFFIXES:
            try:
                probed = gltf.probe(path)
            except Exception as exc:
                report["skipped"].append(f"{path.name}: {exc}")
                continue
            key = f"local:{path.stem}"
            index[key] = {
                "key": key,
                "name": path.stem,
                "source": "local",
                "license": "local",
                "path": str(path),
                "primary": path.name,
                "class": "model",
                "tris": probed.get("triangles"),
                "dims_m": probed.get("dims_zup_m"),
                "format": probed.get("format"),
            }
            report["models"] += 1
        elif suffix in OTHER_MODEL_SUFFIXES:
            key = f"local:{path.stem}"
            index[key] = {
                "key": key,
                "name": path.stem,
                "source": "local",
                "license": "local",
                "path": str(path),
                "primary": path.name,
                "class": "model",
                "format": suffix.lstrip("."),
                "note": "dims unknown (non-glTF); measured at import",
            }
            report["models"] += 1
        elif suffix in TEXTURE_SUFFIXES:
            textures.append(path)
    for set_name, maps in texture_sets(textures).items():
        key = f"local:{set_name}"
        entry: dict[str, Any] = {
            "key": key,
            "name": set_name,
            "source": "local",
            "license": "local",
            "class": "material",
            "maps": maps,
        }
        base = maps.get("base_color")
        if base:
            phash = _phash(Path(base))
            if phash:
                entry["phash"] = phash
        index[key] = entry
        report["material_sets"] += 1
    store._save_index(index)
    return report
