"""STEP AP242 / AP214 / AP203 with product names, through XCAF.

The one trap, measured on OCP 7.9.3 (P0a) and pinned by
`tests/test_exchange_step.py`: `write.step.schema` is captured at the writer's
FIRST `Transfer`. Set it after and the file says `AUTOMOTIVE_DESIGN` (AP214)
no matter what was asked. `STEPCAFControl_Writer` has no `Model`; a reused
writer needs `ChangeWriter().Model(True)` — this module never reuses one, it
builds a fresh writer per call and sets the schema before it.

Names: each shape is a free shape on an XCAF label carrying `TDataStd_Name`;
`SetNameMode(True)` on both sides carries it (F8: 10 named plates round-trip).
Units: `write.step.unit=MM` always (D4); on read the file's declared unit is
scanned from its own `LENGTH_UNIT` entity because
`StepData_StepModel.LocalLengthUnit()` reports 1.0 for an inch file and for a
mm file alike (measured 2026-09-02). Determinism: the geometry is; the bytes
are not, because OCCT stamps `FILE_NAME` with the wall clock — hash the
read-back volume/faces, never the file.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.brep import require_ocp
from partkiln.exchange import (
    add_named_shapes,
    count_unique,
    file_result,
    free_shapes,
    new_xcaf_document,
    quiet_ocp_messenger,
    volume_mm3,
)

SCHEMAS: dict[str, str] = {"AP242": "AP242DIS", "AP214": "AP214IS", "AP203": "AP203"}
"""Requested schema -> the `write.step.schema` static OCCT accepts (only these five exist:
AP203 / AP214CD / AP214DIS / AP214IS / AP242DIS; the CD/DIS variants of 214 are not offered)."""

SCHEMA_TOKENS: dict[str, str] = {
    "AP242": "AP242_MANAGED_MODEL_BASED_3D_ENGINEERING",
    "AP214": "AUTOMOTIVE_DESIGN",
    "AP203": "CONFIG_CONTROL_DESIGN",
}
"""What the file's `FILE_SCHEMA` must contain for each request — asserted after every write."""

_FILE_SCHEMA = re.compile(rb"FILE_SCHEMA\s*\(\s*\((.*?)\)\s*\)", re.S)
_LENGTH_ENTITY = re.compile(rb"#\d+\s*=\s*\([^;]*?LENGTH_UNIT\(\)[^;]*?;", re.S)
_CONVERSION = re.compile(rb"CONVERSION_BASED_UNIT\(\s*'([A-Za-z_ ]+)'")
_SI = re.compile(rb"SI_UNIT\(\s*(\.[A-Z]+\.|\$)\s*,\s*\.METRE\.\s*\)")
_SI_PREFIX = {b"$": "M", b".MILLI.": "MM", b".CENTI.": "CM", b".MICRO.": "UM", b".KILO.": "KM"}


def _set_statics(schema: str, unit: str) -> None:
    from OCP.Interface import Interface_Static
    from OCP.STEPControl import STEPControl_Controller

    if schema not in SCHEMAS:
        raise KernelError(f"unknown STEP schema {schema!r}.", fix=f"one of {sorted(SCHEMAS)}")
    STEPControl_Controller.Init_s()
    if not Interface_Static.SetCVal_s("write.step.schema", SCHEMAS[schema]):
        raise KernelError(
            f"OCCT refused write.step.schema={SCHEMAS[schema]!r}.",
            fix="only AP203 / AP214CD / AP214DIS / AP214IS / AP242DIS exist on this build",
        )
    if not Interface_Static.SetCVal_s("write.step.unit", unit):
        raise KernelError(f"OCCT refused write.step.unit={unit!r}.", fix="MM (D4)")


def file_schema(path: str | Path) -> str:
    """The `FILE_SCHEMA` payload of a STEP file's header (first 64 KB), or "" if absent."""
    with Path(path).open("rb") as fh:
        head = fh.read(65536)
    found = _FILE_SCHEMA.search(head)
    return found.group(1).decode("ascii", "replace").strip() if found else ""


def declared_unit(path: str | Path) -> tuple[str, str]:
    """(unit, source): the file's own length unit from its `LENGTH_UNIT` entity.

    A `CONVERSION_BASED_UNIT('INCH', ...)` wins over the SI base it is defined
    on (an inch file carries both); an SI prefix maps through `_SI_PREFIX`.
    Source is "header" when found, else "assumed" with unit "MM" — the reader
    converts to mm either way (`xstep.cascade.unit` is MM), so this is a
    report, not a scale factor.
    """
    data = Path(path).read_bytes()
    conversions: list[str] = []
    si: list[str] = []
    for entity in _LENGTH_ENTITY.finditer(data):
        text = entity.group(0)
        conv = _CONVERSION.search(text)
        if conv:
            conversions.append(conv.group(1).decode("ascii", "replace").strip().upper())
            continue
        base = _SI.search(text)
        if base and base.group(1) in _SI_PREFIX:
            si.append(_SI_PREFIX[base.group(1)])
    if conversions:
        return conversions[0], "header"
    if si:
        return si[0], "header"
    return "MM", "assumed"


def write_step(
    shapes: list[tuple[str, Any]],
    path: str | Path,
    schema: str = "AP242",
    unit: str = "MM",
) -> dict[str, Any]:
    """Write named shapes as one STEP file; returns {path, bytes, schema, file_schema, products}.

    Order of operations is the whole point (see the module docstring): statics
    first, then a fresh `STEPCAFControl_Writer`, then `Transfer`, then `Write`,
    then the header is re-read and the schema token asserted so a silent
    fallback to AP214 can never leave this function.
    """
    require_ocp()
    quiet_ocp_messenger()
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Writer
    from OCP.STEPControl import STEPControl_AsIs

    if not shapes:
        raise KernelError(
            "write_step needs at least one (name, shape).", fix="pass [(name, shape), ...]"
        )
    _set_statics(schema, unit)
    doc = new_xcaf_document()
    products = add_named_shapes(doc, shapes)
    writer = STEPCAFControl_Writer()
    writer.SetNameMode(True)
    writer.SetColorMode(True)
    writer.SetLayerMode(True)
    if not writer.Transfer(doc, STEPControl_AsIs):
        raise KernelError("STEP transfer failed (no entity produced).", fix="check the shapes")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if writer.Write(str(out)) != IFSelect_RetDone:
        raise KernelError(f"STEP write to {out} failed.", fix="is the directory writable?")
    header = file_schema(out)
    if SCHEMA_TOKENS[schema] not in header:
        raise KernelError(
            f"STEP file says {header!r}, not {schema} — the schema was set after Transfer.",
            fix="set write.step.schema BEFORE the writer's first Transfer",
        )
    return file_result(out, schema=schema, file_schema=header, products=products, unit=unit)


def read_step(path: str | Path) -> dict[str, Any]:
    """Read a STEP file with names: {products: [{name, shape, volume_mm3, faces, solids}], ...}.

    Also reports `unit` / `unit_source` from the header scan and `schema`.
    Shapes come back in mm regardless of the file's unit (OCCT converts to
    `xstep.cascade.unit`); the volume is exact `BRepGProp`, counts are unique.
    """
    require_ocp()
    quiet_ocp_messenger()
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader
    from OCP.STEPControl import STEPControl_Controller

    src = Path(path)
    if not src.is_file():
        raise KernelError(f"no STEP file at {src}.", fix="check the path")
    STEPControl_Controller.Init_s()
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(True)
    reader.SetLayerMode(True)
    if reader.ReadFile(str(src)) != IFSelect_RetDone:
        raise KernelError(f"{src.name} is not a readable STEP file.", fix="check the header")
    doc = new_xcaf_document()
    if not reader.Transfer(doc):
        raise KernelError(
            f"STEP transfer of {src.name} produced no shape.",
            fix="the file has a header but no product geometry; check it in another reader",
        )
    products = [
        {
            "name": name,
            "shape": shape,
            "volume_mm3": volume_mm3(shape),
            "faces": count_unique(shape, "face"),
            "solids": count_unique(shape, "solid"),
        }
        for name, shape in free_shapes(doc)
    ]
    unit, source = declared_unit(src)
    return {
        "path": str(src),
        "products": products,
        "unit": unit,
        "unit_source": source,
        "schema": file_schema(src),
    }


def roundtrip(shape: Any, schema: str = "AP242", rel: float = 1e-9) -> dict[str, Any]:
    """Write `shape` to a temporary STEP and read it back; {volume_ok, faces_ok, ...} at `rel`.

    The export diff and the tests both use this: F1 comes back 59 214.602 to
    1e-9 relative with 7 faces (measured "volume identical").
    """
    require_ocp()
    v_in = volume_mm3(shape)
    f_in = count_unique(shape, "face")
    with tempfile.TemporaryDirectory() as tmp:
        written = write_step([("part", shape)], Path(tmp) / "roundtrip.step", schema=schema)
        back = read_step(written["path"])
    total = sum(p["volume_mm3"] for p in back["products"])
    faces = sum(p["faces"] for p in back["products"])
    delta = abs(total - v_in) / v_in if v_in else abs(total)
    return {
        "schema": schema,
        "file_schema": written["file_schema"],
        "volume_in": v_in,
        "volume_out": total,
        "volume_rel": delta,
        "volume_ok": delta <= rel,
        "faces_in": f_in,
        "faces_out": faces,
        "faces_ok": faces == f_in,
        "products": len(back["products"]),
    }


__all__ = [
    "SCHEMAS",
    "SCHEMA_TOKENS",
    "declared_unit",
    "file_schema",
    "read_step",
    "roundtrip",
    "write_step",
]
