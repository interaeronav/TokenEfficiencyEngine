"""STL through OCCT's own mesher and `StlAPI_Writer`.

Deflection is ABSOLUTE millimetres (D4; build123d's `tolerance` is relative —
the trap this signature avoids) and `angular` is OCCT's own argument, radians.
The shape is re-tessellated from clean every call so the bytes depend only on
(shape, deflection, angular): measured identical on repeat and on a freshly
rebuilt F1 (`tests/test_exchange_mesh_formats.py`). STL carries no unit, so the
result says `declares_units: False`; watertightness and the triangle count are
read back through trimesh, not assumed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import file_result, quiet_ocp_messenger, tessellate


def write_stl(
    shape: Any,
    path: str | Path,
    deflection_mm: float = 0.1,
    angular: float = 0.5,
    binary: bool = True,
) -> dict[str, Any]:
    """Tessellate and write STL; {path, bytes, triangles, watertight, binary, declares_units}."""
    require_ocp()
    quiet_ocp_messenger()
    from OCP.StlAPI import StlAPI_Writer

    if shape is None or shape.IsNull():
        raise KernelError("write_stl: the shape is null.", fix="build the part first")
    tessellate(shape, deflection_mm, angular)
    writer = StlAPI_Writer()
    writer.ASCIIMode = not binary
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not writer.Write(shape, str(out)):
        raise KernelError(f"STL write to {out} failed.", fix="is the directory writable?")
    stats = mesh_stats(out)
    return file_result(
        out,
        triangles=stats["triangles"],
        watertight=stats["watertight"],
        binary=bool(binary),
        deflection_mm=float(deflection_mm),
        declares_units=False,
    )


def mesh_stats(path: str | Path) -> dict[str, Any]:
    """Read a mesh back with trimesh: {triangles, vertices, watertight, volume_mm3, extents}."""
    import trimesh

    mesh = trimesh.load(str(path), force="mesh")
    return {
        "triangles": len(mesh.faces),
        "vertices": len(mesh.vertices),
        "watertight": bool(mesh.is_watertight),
        "volume_mm3": float(mesh.volume) if mesh.is_watertight else None,
        "extents": [float(x) for x in mesh.extents],
    }


__all__ = ["mesh_stats", "write_stl"]
