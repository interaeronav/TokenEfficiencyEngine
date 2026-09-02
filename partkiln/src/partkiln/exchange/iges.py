"""IGES 5.3 out and in, millimetres.

`IGESControl_Writer` and `IGESControl_Reader` share the process-wide
`IGESControl_Controller` and its statics and are NOT thread-safe; the caller
holds the one kernel lock (D2: one Protocol, one kernel per process) and this
module never spawns anything. Names do not survive IGES here (the plain writer
has no name mode), so the tuple form is accepted for symmetry with STEP but
only the shapes are written — the result says so (`names_written: False`).

Measured (F1, OCP 7.9.3): write 0.8 ms / 18 KB, read 1.6 ms, volume back to
1e-12 relative, 7 faces, ZERO solids — IGES carries faces, so `sew=True`
stitches the shell and makes a solid when the shell is closed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import count_unique, file_result, quiet_ocp_messenger, volume_mm3


def write_iges(shapes: list[tuple[str, Any]], path: str | Path) -> dict[str, Any]:
    """Write every shape into one IGES file in mm; {path, bytes, shapes, names_written: False}."""
    require_ocp()
    quiet_ocp_messenger()
    from OCP.IGESControl import IGESControl_Controller, IGESControl_Writer

    if not shapes:
        raise KernelError(
            "write_iges needs at least one (name, shape).", fix="pass [(name, shape), ...]"
        )
    IGESControl_Controller.Init_s()
    writer = IGESControl_Writer("MM", 0)  # 0 = faces (BRep) mode; 1 would emit trimmed surfaces
    added = 0
    for name, shape in shapes:
        if shape is None or shape.IsNull():
            raise KernelError(f"shape {name!r} is null.", fix="build the part before exporting")
        if not writer.AddShape(shape):
            raise KernelError(
                f"IGES could not translate shape {name!r}.",
                fix="run partkiln.brep.shapes.fix on it, or export STEP instead",
            )
        added += 1
    writer.ComputeModel()
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not writer.Write(str(out)):
        raise KernelError(f"IGES write to {out} failed.", fix="is the directory writable?")
    return file_result(out, shapes=added, unit="MM", names_written=False)


def read_iges(path: str | Path, sew: bool = True, tolerance_mm: float = 1e-3) -> dict[str, Any]:
    """Read an IGES file: {shape, roots, volume_mm3, faces, solids, sewn}.

    With `sew` the faces are stitched (`BRepBuilderAPI_Sewing`) and a closed
    shell becomes a solid so downstream booleans have something to cut; an
    open result is returned as-is with `solids: 0`, never faked.
    """
    require_ocp()
    quiet_ocp_messenger()
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.IGESControl import IGESControl_Controller, IGESControl_Reader

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no IGES file at {src}.", fix="check the path")
    IGESControl_Controller.Init_s()
    reader = IGESControl_Reader()
    if reader.ReadFile(str(src)) != IFSelect_RetDone:
        raise KernelError(f"{src.name} is not a readable IGES file.", fix="check the header")
    roots = reader.TransferRoots()
    if roots == 0:
        raise KernelError(
            f"IGES transfer of {src.name} produced no root shape.",
            fix="the file has no translatable entities; check it in another reader",
        )
    shape = reader.OneShape()
    sewn = False
    if sew:
        shape, sewn = _sew(shape, tolerance_mm)
    return {
        "path": str(src),
        "shape": shape,
        "roots": roots,
        "volume_mm3": volume_mm3(shape),
        "faces": count_unique(shape, "face"),
        "solids": count_unique(shape, "solid"),
        "sewn": sewn,
    }


def _sew(shape: Any, tolerance_mm: float) -> tuple[Any, bool]:
    """Stitch faces into shells; a closed shell becomes a solid. Returns (shape, changed)."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    from OCP.TopAbs import TopAbs_IN, TopAbs_SHELL
    from OCP.TopoDS import TopoDS

    sewing = BRepBuilderAPI_Sewing(tolerance_mm)
    sewing.Add(shape)
    sewing.Perform()
    sewn = sewing.SewedShape()
    if sewn.IsNull():
        return shape, False
    if sewn.ShapeType() == TopAbs_SHELL and sewn.Closed():
        solid = BRepBuilderAPI_MakeSolid(TopoDS.Shell_s(sewn)).Solid()
        # an inside-out shell classifies infinity as IN; flip it rather than ship a negative volume
        classifier = BRepClass3d_SolidClassifier(solid)
        classifier.PerformInfinitePoint(tolerance_mm)
        if classifier.State() == TopAbs_IN:
            solid = solid.Reversed()
        return solid, True
    return sewn, True


__all__ = ["read_iges", "write_iges"]
