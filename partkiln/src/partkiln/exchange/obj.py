"""Wavefront OBJ through trimesh from OCCT's tessellation.

`OCP.RWObj` is NOT bound in cadquery-ocp 7.9.3 (P0a), so the triangles are
lifted off the B-rep (`partkiln.exchange.triangles`) and trimesh writes the
text. OBJ has no unit field at all — the result says `declares_units: False`
so a consumer that assumes metres is warned once rather than surprised by a
part a thousand times too big.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import file_result, to_trimesh


def write_obj(
    shape: Any,
    path: str | Path,
    deflection_mm: float = 0.1,
    angular: float = 0.5,
) -> dict[str, Any]:
    """Tessellate and write OBJ; {path, bytes, triangles, watertight, declares_units: False}."""
    require_ocp()
    if shape is None or shape.IsNull():
        raise KernelError("write_obj: the shape is null.", fix="build the part first")
    mesh = to_trimesh(shape, deflection_mm, angular)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = mesh.export(file_type="obj", include_normals=False, include_texture=False)
    out.write_text(text if isinstance(text, str) else text.decode("utf-8"), encoding="utf-8")
    return file_result(
        out,
        triangles=len(mesh.faces),
        watertight=bool(mesh.is_watertight),
        volume_mm3=float(mesh.volume),
        declares_units=False,
    )


def read_obj(path: str | Path) -> dict[str, Any]:
    """Load an OBJ with trimesh: {triangles, watertight, volume, extents}; volume in FILE units."""
    import trimesh

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no OBJ file at {src}.", fix="check the path")
    mesh = trimesh.load(str(src), force="mesh")
    return {
        "path": str(src),
        "triangles": len(mesh.faces),
        "watertight": bool(mesh.is_watertight),
        "volume": float(mesh.volume),
        "extents": [float(x) for x in mesh.extents],
        "declares_units": False,
    }


__all__ = ["read_obj", "write_obj"]
