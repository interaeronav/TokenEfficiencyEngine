"""3MF (core spec 1.x) in millimetres, written with the standard library.

Why not `trimesh.exchange.threemf.export_3MF`: it is a soft dependency on
lxml, and lxml is absent from `server/.venv` (measured 2026-09-02:
`export_3MF` and `load_3MF` both die with `NameError: etree`); it also stamps
zip entries with the wall clock, which breaks "same input, same bytes". The
core spec is three XML parts in a zip, so this module writes them itself with
`xml.etree`, fixed zip timestamps and `unit="millimeter"`, and reads its own
output (and any core-spec file) back the same way. lib3mf stays the optional
`[threemf]` extra for materials/beam lattices, never a requirement.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import file_result, to_trimesh

_NS_CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
_NS_RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
_NS_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
_REL_MODEL = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
"""Fixed entry timestamp: zip's epoch, so the bytes never depend on the clock."""

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<Types xmlns="{_NS_TYPES}">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" '
    'ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    f'<Relationships xmlns="{_NS_RELS}">'
    f'<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="{_REL_MODEL}"/>'
    "</Relationships>"
)


def _model_xml(meshes: list[tuple[str, Any]]) -> bytes:
    """The 3D/3dmodel.model part: one <object> per mesh, all built, coordinates to 6 dp."""
    root = ET.Element("model", {"unit": "millimeter", "xml:lang": "en-US", "xmlns": _NS_CORE})
    resources = ET.SubElement(root, "resources")
    build = ET.SubElement(root, "build")
    for k, (name, mesh) in enumerate(meshes, start=1):
        obj = ET.SubElement(resources, "object", {"id": str(k), "name": name, "type": "model"})
        m = ET.SubElement(obj, "mesh")
        vs = ET.SubElement(m, "vertices")
        for x, y, z in mesh.vertices:
            ET.SubElement(vs, "vertex", {"x": f"{x:.6f}", "y": f"{y:.6f}", "z": f"{z:.6f}"})
        ts = ET.SubElement(m, "triangles")
        for a, b, c in mesh.faces:
            ET.SubElement(ts, "triangle", {"v1": str(a), "v2": str(b), "v3": str(c)})
        ET.SubElement(build, "item", {"objectid": str(k)})
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


def _entry(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=_ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def write_3mf(
    shapes: list[tuple[str, Any]],
    path: str | Path,
    deflection_mm: float = 0.1,
    angular: float = 0.5,
) -> dict[str, Any]:
    """Tessellate every (name, shape) into one 3MF in mm; {path, bytes, objects, triangles}."""
    require_ocp()
    if not shapes:
        raise KernelError(
            "write_3mf needs at least one (name, shape).", fix="pass [(name, shape), ...]"
        )
    meshes: list[tuple[str, Any]] = []
    for name, shape in shapes:
        if shape is None or shape.IsNull():
            raise KernelError(f"shape {name!r} is null.", fix="build the part before exporting")
        meshes.append((str(name), to_trimesh(shape, deflection_mm, angular)))
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr(_entry("[Content_Types].xml"), _CONTENT_TYPES)
        z.writestr(_entry("_rels/.rels"), _RELS)
        z.writestr(_entry("3D/3dmodel.model"), _model_xml(meshes))
    out.write_bytes(buffer.getvalue())
    # Volume only when EVERY object is closed. trimesh answers the divergence
    # theorem over the triangles whether or not the mesh has a hole in it
    # (measured 2026-09-04: an open 100x60x10 box shell reads 60000.0 mm3, the
    # CLOSED box's volume), so a total next to `watertight: False` would be a
    # confident number for a shell that encloses nothing — and one open object
    # poisons the sum, so no partial total is offered either.
    open_objects = [name for name, m in meshes if not m.is_watertight]
    watertight = not open_objects
    return file_result(
        out,
        objects=len(meshes),
        triangles=int(sum(len(m.faces) for _, m in meshes)),
        watertight=watertight,
        volume_mm3=float(sum(m.volume for _, m in meshes)) if watertight else None,
        volume_note=(
            None
            if watertight
            else (
                f"volume omitted: {', '.join(open_objects)} "
                f"{'is' if len(open_objects) == 1 else 'are'} not watertight at deflection "
                f"{deflection_mm} mm, so the total would count a shell that encloses nothing. "
                "Fix: export closed solids (sew the shells), or re-tessellate finer."
            )
        ),
        unit="millimeter",
        declares_units=True,
    )


def read_3mf(path: str | Path) -> dict[str, Any]:
    """Parse a core-spec 3MF: {unit, objects: [{name, triangles, watertight, volume}], volume}.

    Volume is in the file's declared unit (3MF defaults to millimeter when
    the attribute is absent, per the spec); only `<mesh>` objects count. An
    object whose triangles do not close gets `volume: None`, and one such
    object makes the file total None (see `write_3mf`): a number from an
    open mesh is a wrong number, not a rough one.
    """
    import numpy as np
    import trimesh

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no 3MF file at {src}.", fix="check the path")
    with zipfile.ZipFile(src) as z:
        models = [n for n in z.namelist() if n.lower().endswith(".model")]
        if not models:
            raise KernelError(f"{src.name} has no .model part.", fix="is it a 3MF?")
        root = ET.fromstring(z.read(models[0]))
    unit = root.attrib.get("unit", "millimeter")
    ns = {"c": root.tag[1:].split("}")[0]} if root.tag.startswith("{") else {}
    prefix = "c:" if ns else ""
    objects: list[dict[str, Any]] = []
    for obj in root.iterfind(f"{prefix}resources/{prefix}object", ns):
        mesh_el = obj.find(f"{prefix}mesh", ns)
        if mesh_el is None:
            continue
        verts = np.array(
            [
                [float(v.attrib["x"]), float(v.attrib["y"]), float(v.attrib["z"])]
                for v in mesh_el.iterfind(f"{prefix}vertices/{prefix}vertex", ns)
            ],
            dtype=np.float64,
        ).reshape(-1, 3)
        faces = np.array(
            [
                [int(t.attrib["v1"]), int(t.attrib["v2"]), int(t.attrib["v3"])]
                for t in mesh_el.iterfind(f"{prefix}triangles/{prefix}triangle", ns)
            ],
            dtype=np.int64,
        ).reshape(-1, 3)
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        watertight = bool(mesh.is_watertight)
        objects.append(
            {
                "name": obj.attrib.get("name", ""),
                "triangles": len(mesh.faces),
                "watertight": watertight,
                "volume": float(mesh.volume) if watertight else None,
            }
        )
    closed = all(o["volume"] is not None for o in objects)
    return {
        "path": str(src),
        "unit": unit,
        "objects": objects,
        "volume": float(sum(o["volume"] for o in objects)) if closed else None,
    }


__all__ = ["read_3mf", "write_3mf"]
