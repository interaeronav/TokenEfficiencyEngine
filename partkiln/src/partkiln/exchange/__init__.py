"""Exchange: every file format partkiln writes or reads, one module each.

Wire and kernel are millimetres/degrees (D4); every writer here declares that
unit in the file whenever the format can carry one (STEP `write.step.unit=MM`,
IGES `"MM"`, 3MF `unit="millimeter"`, glTF metres via the XCAF LengthUnit) and
says `declares_units: False` when it cannot (OBJ, STL, BREP).

Layout (D1): `step.py` `iges.py` `brep_io.py` `stl.py` `obj.py` `threemf.py`
`gltf.py`. Each public function calls `partkiln.brep.require_ocp()` first, and
every OCP import lives inside a function, so `import partkiln.exchange` costs
nothing and succeeds with no OCP installed. The helpers below are shared by the
modules and are private to the package.

Measured (A66 P0a/P2b, 2026-09-02, OCP 7.9.3): STEP F5 write 13.5 ms / read
44 ms; F8 (10 named F5 copies, 4.1 MB) write 0.17 s / read 0.39 s; BREP F5
81 KB, 2 ms / 1 ms; GLB F1 1.5 ms; mesh F5 at 0.05 mm 42 ms. Three traps every
module pins with a test: the STEP schema must be set BEFORE the writer's first
`Transfer`; the glTF writer needs BOTH the 0.001 m LengthUnit and the Z-up
input coordinate system; sub-shape counts are `TopExp.MapShapes_s` (unique),
never explorer visits (the explorer double-counts shared edges: F5 624 vs 312).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError

_messenger_quiet = False


def quiet_ocp_messenger() -> None:
    """Raise the OCCT messenger's trace level so transfers stop printing to stdout.

    `STEPControl_Writer.Transfer` and the readers print colourised
    "Statistics on Transfer" blocks through `Message::DefaultMessenger()` at
    Info gravity. A headless kernel whose worker speaks NDJSON on stdout
    (D1 `worker.py`) cannot afford that, so the one default printer is set to
    report Fail and above only. Idempotent; called by every writer/reader.
    """
    global _messenger_quiet
    if _messenger_quiet:
        return
    from OCP.Message import Message, Message_Gravity

    printers = Message.DefaultMessenger_s().Printers()
    for i in range(1, printers.Length() + 1):
        printers.Value(i).SetTraceLevel(Message_Gravity.Message_Fail)
    _messenger_quiet = True


def volume_mm3(shape: Any) -> float:
    """Exact B-rep volume via `BRepGProp` (F1 = 59 214.602 mm³, the arithmetic)."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps

    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, props)
    return props.Mass()


def count_unique(shape: Any, kind: str) -> int:
    """Number of UNIQUE sub-shapes of `kind` ("face" | "edge" | "solid" | "vertex").

    Law 20: `TopExp.MapShapes_s`, never `TopExp_Explorer` visits — the explorer
    reaches every shared edge once per owning face (F5: 624 visits, 312 edges).
    """
    from OCP.TopAbs import TopAbs_EDGE, TopAbs_FACE, TopAbs_SOLID, TopAbs_VERTEX
    from OCP.TopExp import TopExp
    from OCP.TopTools import TopTools_IndexedMapOfShape

    kinds = {
        "face": TopAbs_FACE,
        "edge": TopAbs_EDGE,
        "solid": TopAbs_SOLID,
        "vertex": TopAbs_VERTEX,
    }
    if kind not in kinds:
        raise KernelError(f"unknown sub-shape kind {kind!r}.", fix=f"one of {sorted(kinds)}")
    found = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, kinds[kind], found)
    return found.Extent()


def new_xcaf_document() -> Any:
    """A fresh BinXCAF `TDocStd_Document` from the one XCAF application.

    The same construction serves the STEP writer/reader and the glTF writer;
    `XCAFApp_Application.GetApplication_s()` is a process singleton, so this
    is the cheap part of every exchange call.
    """
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDocStd import TDocStd_Document
    from OCP.XCAFApp import XCAFApp_Application

    fmt = TCollection_ExtendedString("BinXCAF")
    doc = TDocStd_Document(fmt)
    XCAFApp_Application.GetApplication_s().NewDocument(fmt, doc)
    return doc


def add_named_shapes(doc: Any, shapes: list[tuple[str, Any]]) -> int:
    """Add each (name, shape) to the document's ShapeTool as a free shape; returns the count.

    `AddShape(shape, False)` = no assembly decomposition, so one product per
    entry; the `TDataStd_Name` on the label is what `SetNameMode(True)` writers
    carry into the file (measured: F8 names round-trip through STEP).
    """
    from OCP.TCollection import TCollection_ExtendedString
    from OCP.TDataStd import TDataStd_Name
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    for name, shape in shapes:
        if shape is None or shape.IsNull():
            raise KernelError(f"shape {name!r} is null.", fix="build the part before exporting")
        label = tool.AddShape(shape, False)
        TDataStd_Name.Set_s(label, TCollection_ExtendedString(str(name)))
    return len(shapes)


def free_shapes(doc: Any) -> list[tuple[str, Any]]:
    """Every free shape in the document as (name, shape); unnamed labels get ""."""
    from OCP.TDataStd import TDataStd_Name
    from OCP.TDF import TDF_LabelSequence
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    labels = TDF_LabelSequence()
    tool.GetFreeShapes(labels)
    out: list[tuple[str, Any]] = []
    for i in range(1, labels.Length() + 1):
        label = labels.Value(i)
        attr = TDataStd_Name()
        found = label.FindAttribute(TDataStd_Name.GetID_s(), attr)
        name = attr.Get().ToExtString() if found else ""
        out.append((name, tool.GetShape_s(label)))
    return out


def tessellate(shape: Any, deflection_mm: float = 0.1, angular: float = 0.5) -> None:
    """Triangulate `shape` in place at an ABSOLUTE deflection (mm) and angular deflection (rad).

    build123d's `tolerance` is relative; ours is absolute (D4). The existing
    triangulation is cleaned first so the result depends only on (shape,
    deflection, angular) and never on an earlier, finer call — that is what
    makes STL/GLB bytes identical on repeat. `isInParallel=True` is safe: the
    serial and parallel meshes hash identically on this build (P0a, pinned).
    """
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.BRepTools import BRepTools

    if deflection_mm <= 0:
        raise KernelError(
            f"deflection_mm must be > 0 (got {deflection_mm}).", fix="typical 0.05-0.5 mm"
        )
    BRepTools.Clean_s(shape)
    BRepMesh_IncrementalMesh(shape, float(deflection_mm), False, float(angular), True)


def triangles(shape: Any) -> tuple[Any, Any]:
    """The current triangulation as (vertices[n,3] mm, faces[m,3] int) numpy arrays.

    Reversed faces are flipped so every triangle winds outward; vertices are
    NOT merged here (trimesh does that when it builds the mesh). Call
    `tessellate` first — a face with no triangulation is skipped.
    """
    import numpy as np
    from OCP.BRep import BRep_Tool
    from OCP.TopAbs import TopAbs_FACE, TopAbs_REVERSED
    from OCP.TopExp import TopExp
    from OCP.TopLoc import TopLoc_Location
    from OCP.TopoDS import TopoDS
    from OCP.TopTools import TopTools_IndexedMapOfShape

    verts: list[tuple[float, float, float]] = []
    tris: list[tuple[int, int, int]] = []
    offset = 0
    # Unique faces (Law 20): an explorer would emit a face shared by two
    # solids of a compound twice, and its triangles with it.
    found = TopTools_IndexedMapOfShape()
    TopExp.MapShapes_s(shape, TopAbs_FACE, found)
    for k in range(1, found.Extent() + 1):
        face = TopoDS.Face_s(found.FindKey(k))
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is None:
            continue
        trsf = loc.Transformation()
        n = tri.NbNodes()
        for i in range(1, n + 1):
            p = tri.Node(i).Transformed(trsf)
            verts.append((p.X(), p.Y(), p.Z()))
        reversed_face = face.Orientation() == TopAbs_REVERSED
        for i in range(1, tri.NbTriangles() + 1):
            a, b, c = tri.Triangle(i).Get()
            if reversed_face:
                tris.append((offset + a - 1, offset + c - 1, offset + b - 1))
            else:
                tris.append((offset + a - 1, offset + b - 1, offset + c - 1))
        offset += n
    return np.asarray(verts, dtype=np.float64).reshape(-1, 3), np.asarray(
        tris, dtype=np.int64
    ).reshape(-1, 3)


def to_trimesh(shape: Any, deflection_mm: float = 0.1, angular: float = 0.5) -> Any:
    """Tessellate and return a merged `trimesh.Trimesh` (mm), the base of OBJ/3MF/STL checks."""
    import trimesh

    tessellate(shape, deflection_mm, angular)
    verts, tris = triangles(shape)
    return trimesh.Trimesh(vertices=verts, faces=tris, process=True)


def file_result(path: str | Path, **extra: Any) -> dict[str, Any]:
    """The common tail of every writer's result: absolute path and byte size."""
    p = Path(path)
    return {"path": str(p), "bytes": p.stat().st_size, **extra}


__all__ = [
    "add_named_shapes",
    "count_unique",
    "file_result",
    "free_shapes",
    "new_xcaf_document",
    "quiet_ocp_messenger",
    "tessellate",
    "to_trimesh",
    "triangles",
    "volume_mm3",
]
