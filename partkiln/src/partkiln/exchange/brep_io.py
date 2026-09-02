"""OCCT's own `.brep` format: the checkpoint cache (D3) and the fastest round trip there is.

`BRepTools.Write_s(shape, path, withTriangles, withNormals, version)` at
`TopTools_FormatVersion_VERSION_3` with NO triangulation is the measured
checkpoint: F5 (106 faces) 81 KB, 1.4-3 ms write, 1 ms read, volume bit-
identical (P0a). Triangles are opt-in because they triple the file for
nothing a replay needs — the script is the state, the B-rep is a cache.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import file_result


def write_brep(shape: Any, path: str | Path, with_triangles: bool = False) -> dict[str, Any]:
    """Write one shape as VERSION_3 `.brep`; {path, bytes, with_triangles}."""
    require_ocp()
    from OCP.BRepTools import BRepTools
    from OCP.TopTools import TopTools_FormatVersion

    if shape is None or shape.IsNull():
        raise KernelError("write_brep: the shape is null.", fix="build the part first")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = BRepTools.Write_s(
        shape,
        str(out),
        bool(with_triangles),
        False,
        TopTools_FormatVersion.TopTools_FormatVersion_VERSION_3,
    )
    if not ok:
        raise KernelError(f"BREP write to {out} failed.", fix="is the directory writable?")
    return file_result(out, with_triangles=bool(with_triangles), declares_units=False)


def read_brep(path: str | Path) -> Any:
    """Read a `.brep` file back into a `TopoDS_Shape`; refuses on a missing or unreadable file."""
    require_ocp()
    from OCP.BRep import BRep_Builder
    from OCP.BRepTools import BRepTools
    from OCP.TopoDS import TopoDS_Shape

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no BREP file at {src}.", fix="snapshot first, or replay the script")
    shape = TopoDS_Shape()
    if not BRepTools.Read_s(shape, str(src), BRep_Builder()) or shape.IsNull():
        raise KernelError(f"{src.name} is not a readable .brep file.", fix="replay the script")
    return shape


__all__ = ["read_brep", "write_brep"]
