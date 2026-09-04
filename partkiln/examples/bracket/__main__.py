"""`python -m examples.bracket {model|check|drawing|export|all} --out DIR [--probe]`"""

from __future__ import annotations

import argparse
from typing import Any

from examples import _common
from examples.bracket import model

DOC = (
    "W1, the mounting bracket: a 120 x 80 x 10 plate, corners filleted, four M6 "
    "clearance holes to ISO 273, a chamfered top loop and a through slot - then a "
    "spec check, a dimensioned A3 sheet, and STEP/GLB/STL out."
)
STAGES = ("model", "check", "drawing", "export")

# The spec the part has to satisfy. Every rule is a number the model must
# answer with, not a number typed into a drawing.
SPEC: dict[str, Any] = {
    "bbox": [120, 80, 10],
    "holes": [{"dia": 6.6, "count": 4}],
    "mass_g": [700, 730],
    "valid": True,
    "watertight": True,
}


def stage_model(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    _common.banner("model", probe=args.probe)
    watch = _common.Stopwatch()
    kernel, results = model.build()
    rows = model.feature_rows(results)
    for row in rows:
        caught = ", ".join(f"{sel} -> {n}" for sel, n in row["resolved"].items())
        print(
            f"  {row['id']:<12} {row['kind']:<8} delta {row['delta_mm3']:>12,.3f} mm3  "
            f"faces {row['faces']:>3}  {caught}".rstrip()
        )
    mass = kernel.call("measure", {"of": "bracket", "what": "mass"})
    print(
        f"  part:bracket volume {mass['volume_mm3']:,.3f} mm3  mass {mass['mass_g']:,.3f} g  "
        f"bbox {mass['bbox_mm']}  material {mass['material']} ({mass['honesty']})"
    )
    print(f"  fingerprint {kernel.fingerprint()}   {watch.s * 1000:.0f} ms")
    _common.save(kernel, paths)
    _common.write_manifest(
        paths,
        {
            "example": "bracket",
            "params": model.PARAMS,
            "features": rows,
            "volume_mm3": mass["volume_mm3"],
            "mass_g": mass["mass_g"],
            "bbox_mm": mass["bbox_mm"],
            "fingerprint": kernel.fingerprint(),
        },
        probe=args.probe,
    )
    return 0


def stage_check(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("check", probe=probe)
    kernel = _common.load(paths, "check")
    out = kernel.call("check", {"of": "bracket", "spec": SPEC})
    print(f"  verdict {out['verdict']}  checked {', '.join(out['checked'])}")
    for row in out.get("violations", []):
        print(f"  ! {row['rule']}: got {row.get('got')} vs {row.get('limit')} - {row.get('fix')}")
    for row in out.get("unproven", []):
        print(f"  ? {row['rule']}: {row.get('note', 'not disproven, which is not proven')}")
    _common.write_manifest(paths, {"check": out}, probe=probe)
    return 0 if out["verdict"] != "fail" else 1


def stage_drawing(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("drawing", probe=probe)
    kernel = _common.load(paths, "drawing")
    paths["drawing"].mkdir(parents=True, exist_ok=True)
    # A probe skips the PDF: fpdf2 lives in the optional [pdf] extra, and a
    # probe's job is to prove the pipeline runs, not to prove an extra is in.
    formats = ["svg", "dxf"] if probe else ["svg", "dxf", "pdf"]
    out = kernel.call(
        "drawing",
        {
            "name": "sheet1",
            "of": "bracket",
            "sheet": "A3L",
            "views": [{"name": "front", "dir": "front"}, {"name": "top", "dir": "top"}],
            "dims": [
                {"name": "d1", "view": "top", "kind": "extent", "axis": "X"},
                {"name": "d2", "view": "top", "kind": "extent", "axis": "Y"},
                {"name": "d3", "view": "top", "kind": "dia", "of": "h.1"},
                {"name": "d4", "view": "top", "kind": "dist", "a": "h.1", "b": "h.2", "axis": "X"},
                {"name": "d5", "view": "top", "kind": "dist", "a": "h.1", "b": "h.3", "axis": "Y"},
                {"name": "d6", "view": "front", "kind": "extent", "axis": "Y"},
            ],
            "hole_table": True,
            "title": {"part": "BRACKET-001", "rev": "A", "material": "S275", "scale": "1:1"},
            "formats": formats,
            "out_dir": str(paths["drawing"]),
        },
    )
    for view in out["views"]:
        print(
            f"  view {view['name']:<6} {view['dir']:<6} scale {view['scale']}  "
            f"visible {view['visible_edges']:>3}  hidden {view['hidden_edges']:>3}"
        )
    for dim in out["dimensions"]:
        # Law 15: the value is READ BACK from the model; `agree` says the
        # projected 2D length agrees with the 3D one.
        print(f"  dim {dim['name']}  {dim['value_mm']:>9,.3f} mm  agree {dim['agree']}")
    print(f"  hole table {len(out['hole_table'])} rows")
    written = _common.files(out["files"])
    _common.write_manifest(
        paths,
        {
            "drawing": {
                "views": out["views"],
                "dimensions": out["dimensions"],
                "hole_table_rows": len(out["hole_table"]),
                "files": written,
            }
        },
        probe=probe,
    )
    return 0


def stage_export(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("export", probe=probe)
    kernel = _common.load(paths, "export")
    paths["export"].mkdir(parents=True, exist_ok=True)
    tol = _common.tol_mm(probe)
    rows: dict[str, Any] = {}
    written: dict[str, str] = {}
    for fmt, extra in (
        # A probe skips the STEP round-trip: re-reading the file back through
        # OCCT is the slow half of the export and proves nothing about whether
        # the pipeline runs.
        ("step", {"schema": "AP242", "roundtrip": not probe}),
        ("glb", {"target": "blender"}),
        ("stl", {"tol": tol}),
    ):
        out = kernel.call(
            "export",
            {
                "format": fmt,
                "of": "bracket",
                "out": str(paths["export"] / f"bracket.{fmt}"),
                **extra,
            },
        )
        rows[fmt] = out
        written[fmt] = out["path"]
    step, glb, stl = rows["step"], rows["glb"], rows["stl"]
    print(f"  step  schema {step['schema']}  products {step['products']}  unit {step['unit']}")
    if "roundtrip" in step:
        trip = step["roundtrip"]
        print(
            f"        round trip: volume_ok {trip['volume_ok']}  faces_ok {trip['faces_ok']}  "
            f"rel {trip['volume_rel']:.2e}"
        )
    print(
        f"  glb   {glb['units']} {glb['up']}-up  extents {glb['extents']}  "
        f"meshes {glb['meshes']}  (declares its unit: {glb['declares_units']})"
    )
    print(
        f"  stl   {stl['triangles']:,} triangles at deflection {stl['deflection_mm']} mm  "
        f"watertight {stl['watertight']}  (declares nothing - the manifest carries the unit)"
    )
    files = _common.files(written)
    _common.write_manifest(
        paths,
        {
            "export": {
                "deflection_mm": tol,
                "step": {k: step[k] for k in ("schema", "products", "unit") if k in step},
                "step_roundtrip": step.get("roundtrip"),
                "glb": {k: glb[k] for k in ("units", "up", "extents", "meshes")},
                "stl": {k: stl[k] for k in ("triangles", "watertight", "deflection_mm")},
                "manifests": {fmt: rows[fmt]["manifest"] for fmt in rows},
                "files": files,
            }
        },
        probe=probe,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _common.parser("examples.bracket", DOC, STAGES, out="bracket_out").parse_args(argv)
    table = {
        "model": stage_model,
        "check": stage_check,
        "drawing": stage_drawing,
        "export": stage_export,
    }
    if args.stage == "all":
        return _common.run_all(args, tuple(table[name] for name in STAGES))
    return table[args.stage](args)


if __name__ == "__main__":
    raise SystemExit(main())
