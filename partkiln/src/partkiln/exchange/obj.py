"""Wavefront OBJ through trimesh from OCCT's tessellation.

`OCP.RWObj` is NOT bound in cadquery-ocp 7.9.3 (P0a), so the triangles are
lifted off the B-rep (`partkiln.exchange.triangles`) and trimesh writes the
text. OBJ has no unit field at all — the result says `declares_units: False`
so a consumer that assumes metres is warned once rather than surprised by a
part a thousand times too big.

`volume_mm3` is reported ONLY when the tessellation is watertight. trimesh's
volume is the divergence theorem over the triangles, which answers a
confident number for a mesh with a hole in it (measured 2026-09-04: the
100x60x10 box shell with one face removed reads 60000.0 mm3, the CLOSED
box's volume) — a number next to `watertight: False` is worse than no
number, so an open mesh gets None and a `volume_note` naming the reason.
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
    watertight = bool(mesh.is_watertight)
    note = (
        None
        if watertight
        else (
            f"volume omitted: the mesh at deflection {deflection_mm} mm is not watertight, "
            "so it encloses no volume. Fix: export a closed solid (sew the shell), or "
            "re-tessellate finer."
        )
    )
    return file_result(
        out,
        triangles=len(mesh.faces),
        watertight=watertight,
        volume_mm3=float(mesh.volume) if watertight else None,
        volume_note=note,
        declares_units=False,
    )


def read_obj(path: str | Path) -> dict[str, Any]:
    """Load an OBJ with trimesh: {triangles, watertight, volume, extents}; volume in FILE units.

    `volume` is None for an open mesh, for the reason in the module
    docstring: an unclosed surface has no enclosed volume, and trimesh
    prints one anyway.
    """
    import trimesh

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no OBJ file at {src}.", fix="check the path")
    mesh = trimesh.load(str(src), force="mesh")
    watertight = bool(mesh.is_watertight)
    return {
        "path": str(src),
        "triangles": len(mesh.faces),
        "watertight": watertight,
        "volume": float(mesh.volume) if watertight else None,
        "extents": [float(x) for x in mesh.extents],
        "declares_units": False,
    }


__all__ = ["read_obj", "write_obj"]
