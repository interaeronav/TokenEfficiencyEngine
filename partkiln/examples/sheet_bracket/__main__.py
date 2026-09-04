"""`python -m examples.sheet_bracket {model|table|flat|fold|all} --out DIR [--probe]`"""

from __future__ import annotations

import argparse
from typing import Any

from examples import _common
from examples.sheet_bracket import model

DOC = (
    "W3, the flat-first sheet-metal L: t 2, width 50, flanges 60 and 40 at 90 deg "
    "r 2, two M5 clearance holes - the bend table, the flat pattern DXF with its "
    "four layers, and the folded solid."
)
STAGES = ("model", "table", "flat", "fold")


def _sheet(kernel: Any) -> Any:
    return kernel.document.sheets["brk"]


def stage_model(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    _common.banner("model", probe=args.probe)
    kernel, row = model.build()
    print(
        f"  sheet:{row['id'].split(':')[1]}  t {row['t']} mm  k {row['k']}  bends {row['bends']}  "
        f"flanges {row['flanges']}  holes {row['holes']}"
    )
    print(f"  flat blank      {row['flat_mm'][0]:,.3f} x {row['flat_mm'][1]:,.3f} mm")
    print(f"  folded bbox     {row['folded_bbox_mm']}")
    print(f"  BA total {row['ba_total_mm']:,.3f} mm   BD total {row['bd_total_mm']:,.3f} mm")
    print(
        f"  volume: flat {row['flat_volume_mm3']:,.3f} mm3  folded {row['folded_volume_mm3']:,.3f} "
        f"mm3  delta {row['volume_delta_mm3']:+,.3f} mm3"
    )
    print(f"  mass (folded)   {row['mass_g']:,.3f} g of {row['material']}")
    for note in row["notes"]:
        print(f"  note: {note}")
    _common.save(kernel, paths)
    _common.write_manifest(
        paths, {"example": "sheet_bracket", "params": model.PARAMS, "sheet": row}, probe=args.probe
    )
    return 0


def stage_table(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("table", probe=probe)
    kernel = _common.load(paths, "table")
    sheet = _sheet(kernel)
    rows = model.bend_table(sheet)
    print("  bend   angle    r     K      dir     len      BA      OSSB     BD     zone mm3")
    for r in rows:
        print(
            f"  {r['bend']:<6} {r['angle_deg']:>5.1f}  {r['r_inner_mm']:>4.1f}  {r['k']:>5.2f}  "
            f"{r['dir']:<6} {r['length_mm']:>6.1f}  {r['ba_mm']:>6.3f}  {r['ossb_mm']:>6.3f}  "
            f"{r['bd_mm']:>6.3f}  {r['zone_mm3']:>9.3f}"
        )
    length, width = sheet.flat.extents()
    # Flat length = sum of the outside legs - BD per bend. Printed as the
    # arithmetic, so the table can be checked without trusting the kernel.
    legs = sum(f.length for f in sheet.flat.flanges)
    bd_total = sum(r["bd_mm"] for r in rows)
    print(
        f"  flat length {length:,.3f} mm = legs {legs:,.3f} - BD {bd_total:,.3f}   "
        f"width {width:,.3f} mm"
    )
    _common.write_manifest(
        paths,
        {"bend_table": rows, "flat_length_mm": round(length, 3), "flat_width_mm": round(width, 3)},
        probe=probe,
    )
    return 0


def stage_flat(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("flat", probe=probe)
    kernel = _common.load(paths, "flat")
    paths["export"].mkdir(parents=True, exist_ok=True)
    out = kernel.call(
        "flat", {"name": "brk", "out": str(paths["export"] / "brk"), "formats": ["dxf", "svg"]}
    )
    dxf = out["files"]["dxf"]
    print(f"  layers {', '.join(out['layers'])}  entities {dxf['entities']}")
    print(
        f"  dxf declares its unit: $INSUNITS {dxf['insunits']} ({dxf['units']}) - "
        f"the one drawing format that does"
    )
    files = _common.files({fmt: row for fmt, row in out["files"].items()})
    _common.write_manifest(
        paths,
        {
            "flat": {
                "layers": out["layers"],
                "entities": dxf["entities"],
                "insunits": dxf["insunits"],
                "files": files,
            }
        },
        probe=probe,
    )
    return 0


def stage_fold(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("fold", probe=probe)
    kernel = _common.load(paths, "fold")
    paths["export"].mkdir(parents=True, exist_ok=True)
    sheet = _sheet(kernel)
    from partkiln.brep import shapes
    from partkiln.exchange.step import write_step
    from partkiln.exchange.stl import write_stl

    watch = _common.Stopwatch()
    solid = sheet.solid("folded")
    built_ms = watch.s * 1000
    measured = shapes.volume(solid)
    arithmetic = sheet.flat.folded_volume()
    counted = shapes.counts(solid)
    # The B-rep is the check on the arithmetic, not the source of it: if these
    # two disagree by more than rounding, the fold is wrong, not the formula.
    print(
        f"  folded solid   {counted['faces']} faces, {counted['edges']} edges, "
        f"valid {shapes.is_valid(solid)}   built in {built_ms:.0f} ms"
    )
    print(
        f"  volume: B-rep {measured:,.3f} mm3  vs arithmetic {arithmetic:,.3f} mm3  "
        f"(diff {measured - arithmetic:+.6f})"
    )
    step = write_step([("brk", solid)], paths["export"] / "brk.step", schema="AP242")
    stl = write_stl(solid, paths["export"] / "brk.stl", deflection_mm=_common.tol_mm(probe))
    print(f"  step  schema {step['schema']}  products {step['products']}  unit {step['unit']}")
    print(
        f"  stl   {stl['triangles']:,} triangles at deflection {stl['deflection_mm']} mm  "
        f"watertight {stl['watertight']}"
    )
    files = _common.files({"step": step, "stl": stl})
    _common.write_manifest(
        paths,
        {
            "fold": {
                "faces": counted["faces"],
                "edges": counted["edges"],
                "volume_brep_mm3": round(measured, 3),
                "volume_arithmetic_mm3": round(arithmetic, 3),
                "build_ms": round(built_ms, 1),
                "files": files,
            }
        },
        probe=probe,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    top = _common.parser("examples.sheet_bracket", DOC, STAGES, out="sheet_bracket_out")
    args = top.parse_args(argv)
    table = {
        "model": stage_model,
        "table": stage_table,
        "flat": stage_flat,
        "fold": stage_fold,
    }
    if args.stage == "all":
        return _common.run_all(args, tuple(table[name] for name in STAGES))
    return table[args.stage](args)


if __name__ == "__main__":
    raise SystemExit(main())
