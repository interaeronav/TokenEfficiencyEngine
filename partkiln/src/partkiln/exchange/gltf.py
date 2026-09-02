"""GLB through `RWGltf_CafWriter`: metres and Y-up, both by explicit instruction.

Two traps, both measured on OCP 7.9.3 (P0a) and both pinned by
`tests/test_exchange_gltf.py` through the keyword options that reproduce them:

* `metres=True` sets `XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)` — the
  value is the document's unit IN METRES, so 0.001 means "this document is in
  mm" and the writer scales to glTF's normative metre. Without it a 10 mm
  plate reads back as 10 m (F1 extents [100, 10, 60]).
* `y_up=True` sets `ChangeCoordinateSystemConverter().SetInputCoordinateSystem(
  RWMesh_CoordinateSystem_Zup)`. The writer applies NO rotation unless told
  the input is Z-up; without it the part lies on its side ([0.1, 0.06, 0.01]).

With both, F1 reads back extents [0.1, 0.01, 0.06] m and `dims_zup_m`
[0.1, 0.06, 0.01]. `SetMergeFaces(True)` gives one mesh per shape (F1: 1
instead of 7). This is why `handoff.py` can hand a GLB to seamkiln's Target
table with NO extra transform: the writer already rotated and scaled it.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import (
    add_named_shapes,
    file_result,
    new_xcaf_document,
    quiet_ocp_messenger,
    tessellate,
)


def write_glb(
    shapes: list[tuple[str, Any]],
    path: str | Path,
    deflection_mm: float = 0.1,
    angular: float = 0.5,
    y_up: bool = True,
    metres: bool = True,
    merge_faces: bool = True,
) -> dict[str, Any]:
    """Write named shapes as one binary glTF; {path, bytes, meshes, units, up, ...}.

    `y_up=False` / `metres=False` exist so the tests can reproduce the two
    measured wrong files; production callers leave the defaults alone. The
    result reports what the file actually is (`units: 'mm'`, `up: 'Z'`) when
    a negative option is used, never the intended value.
    """
    require_ocp()
    quiet_ocp_messenger()
    from OCP.Message import Message_ProgressRange
    from OCP.RWGltf import RWGltf_CafWriter
    from OCP.RWMesh import RWMesh_CoordinateSystem
    from OCP.TCollection import TCollection_AsciiString
    from OCP.TColStd import TColStd_IndexedDataMapOfStringString
    from OCP.XCAFDoc import XCAFDoc_DocumentTool

    if not shapes:
        raise KernelError(
            "write_glb needs at least one (name, shape).", fix="pass [(name, shape), ...]"
        )
    doc = new_xcaf_document()
    if metres:
        XCAFDoc_DocumentTool.SetLengthUnit_s(doc, 0.001)
    for _, shape in shapes:
        if shape is not None and not shape.IsNull():
            tessellate(shape, deflection_mm, angular)
    products = add_named_shapes(doc, shapes)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = RWGltf_CafWriter(TCollection_AsciiString(str(out)), True)
    writer.SetMergeFaces(bool(merge_faces))
    if y_up:
        writer.ChangeCoordinateSystemConverter().SetInputCoordinateSystem(
            RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup
        )
    ok = writer.Perform(doc, TColStd_IndexedDataMapOfStringString(), Message_ProgressRange())
    if not ok:
        raise KernelError(f"glTF write to {out} failed.", fix="is the directory writable?")
    back = read_back(out)
    return file_result(
        out,
        products=products,
        meshes=back["meshes"],
        units="m" if metres else "mm",
        up="Y" if y_up else "Z",
        merged=bool(merge_faces),
        extents=back["extents"],
        declares_units=True,
    )


def read_back(path: str | Path) -> dict[str, Any]:
    """Load a GLB with trimesh: {meshes, names, extents, triangles} in the file's own axes."""
    import trimesh

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no GLB file at {src}.", fix="check the path")
    scene = trimesh.load(str(src))
    if isinstance(scene, trimesh.Scene):
        geometries = dict(scene.geometry)
        extents = scene.extents
    else:
        geometries = {"mesh": scene}
        extents = scene.extents
    return {
        "path": str(src),
        "meshes": len(geometries),
        "names": sorted(geometries),
        "triangles": int(sum(len(g.faces) for g in geometries.values())),
        "extents": [round(float(x), 6) for x in extents],
    }


__all__ = ["read_back", "write_glb"]
