"""`python -m examples.shaft_housing {model|assemble|check|export|all} --out DIR [--probe]`"""

from __future__ import annotations

import argparse
from typing import Any

from examples import _common
from examples.shaft_housing import model

DOC = (
    "W2, the two-part assembly: a stepped shaft (journal d20 x 60, collar d30 x 20) "
    "in a 60 x 60 x 30 housing bored d20.2 - one insert mate, one revolute joint, "
    "then DOF, interference, clearance and the BOM."
)
STAGES = ("model", "assemble", "check", "export")


def stage_model(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    _common.banner("model", probe=args.probe)
    kernel, _results = model.build_parts()
    parts = {}
    for name in ("housing", "shaft"):
        mass = kernel.call("measure", {"of": name, "what": "mass"})
        parts[name] = {
            "volume_mm3": mass["volume_mm3"],
            "mass_g": mass["mass_g"],
            "bbox_mm": mass["bbox_mm"],
        }
        print(
            f"  part:{name:<8} volume {mass['volume_mm3']:>12,.3f} mm3  "
            f"mass {mass['mass_g']:>9,.3f} g  bbox {mass['bbox_mm']}"
        )
    # The mates address faces by name, so show how those names are found.
    found = kernel.call("query", {"of": "shaft", "sel": "body:faces(type=cylinder)"})
    for name, fact in zip(found["names"], found["facts"], strict=True):
        print(f"  shaft cylinder {name:<12} r {fact['radius_mm']:>6,.3f} mm  {fact['centroid_mm']}")
    _common.save(kernel, paths)
    _common.write_manifest(
        paths,
        {
            "example": "shaft_housing",
            "params": model.PARAMS,
            "parts": parts,
            "fingerprint": kernel.fingerprint(),
        },
        probe=args.probe,
    )
    return 0


def stage_assemble(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("assemble", probe=probe)
    kernel = _common.load(paths, "assemble")
    steps: list[dict[str, Any]] = []
    # One op at a time on purpose: the point of this stage is that the DOF
    # count falls as constraints land, and a single batch would show only
    # the last number.
    for op in model.ASM_OPS:
        row = kernel.apply([op])["results"][0]
        regen = row.get("regen", {}).get("asm", {})
        label = f"{op['kind']} {row.get('id', '')}"
        steps.append({"op": label, "dof": regen.get("dof"), "status": regen.get("status")})
        print(
            f"  {label:<24} components {regen.get('components')}  dof {regen.get('dof')}  "
            f"{regen.get('status', '')}"
        )
    asm = kernel.call("measure", {"what": "asm"})
    pose = asm["poses"]["shaft"] if "poses" in asm else None
    print(f"  solved: dof {asm['dof']}  residual {asm['residual']}  grounded {asm['grounded']}")
    if asm.get("redundant"):
        # Honest, not silent: the insert says the intent, the joint repeats it.
        print(
            f"  redundant: {', '.join(asm['redundant'])} - the revolute joint already says "
            "what the insert mate says; the solver reports it rather than dropping it"
        )
    _common.save(kernel, paths)
    _common.write_manifest(
        paths,
        {
            "assemble": {
                "steps": steps,
                "dof": asm["dof"],
                "residual": asm["residual"],
                "pose": pose,
            }
        },
        probe=probe,
    )
    return 0


def stage_check(args: argparse.Namespace) -> int:
    paths = _common.layout(args.out)
    probe = _common.probe_flag(args, paths)
    _common.banner("check", probe=probe)
    kernel = _common.load(paths, "check")
    asm = kernel.call("measure", {"what": "asm"})
    interference = kernel.call("measure", {"what": "interference"})
    clearance = kernel.call("measure", {"what": "clearance", "a": "shaft", "b": "housing"})
    bom = kernel.call("bom", {"view": "structured"})
    per_component, joints = asm["dof_by_component"], asm["joint_values"]
    print(f"  dof {asm['dof']}  per component {per_component}  joints {joints}")
    print(
        f"  interference {len(interference['interference'])}  contacts "
        f"{len(interference['contacts'])}  clearance {interference['clearance_mm']}"
    )
    print(
        f"  closest approach {clearance['mm']:.3f} mm between {clearance['points'][0]} and "
        f"{clearance['points'][1]}  (contact {clearance['contact']})"
    )
    for row in bom["rows"]:
        print(
            f"  bom {row['item']}  {row['part']:<8} qty {row['qty']}  {row['material']:<12} "
            f"{row['mass_g']:>9,.3f} g  total {row['total_g']:>9,.3f} g"
        )
    print(f"  bom total {bom['total_g']:,.3f} g over {bom['count']} rows")
    _common.write_manifest(
        paths,
        {
            "check": {
                "dof": asm["dof"],
                "dof_by_component": asm["dof_by_component"],
                "interference": interference["interference"],
                "clearance_mm": clearance["mm"],
                "bom": {"rows": bom["rows"], "total_g": bom["total_g"]},
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
    out = kernel.call(
        "export",
        {
            "format": "step",
            # The ASSEMBLY, not a list of parts: one product per component at
            # the pose the solve reached. A list of parts writes each body in
            # its OWN frame, which is a file that looks right and is wrong.
            "of": "asm",
            "out": str(paths["export"] / "shaft_housing.step"),
            "schema": "AP242",
            "roundtrip": not probe,
        },
    )
    print(f"  step  schema {out['schema']}  products {out['products']}  unit {out['unit']}")
    if "roundtrip" in out:
        trip = out["roundtrip"]
        print(
            f"        round trip: volume_ok {trip['volume_ok']}  faces_ok {trip['faces_ok']}  "
            f"rel {trip['volume_rel']:.2e}"
        )
    # Say whose coordinates the file is in, because a receiver cannot tell.
    # The manifest is the source of that sentence, never a literal typed here:
    # a print that disagrees with the file is worse than no print at all.
    place = out["manifest"].get("placement", {})
    print(
        f"        frame {out['manifest']['frame']}  poses_written "
        f"{out['manifest']['poses_written']}"
    )
    for row in place.get("components", []):
        xyz = ", ".join(f"{v:.3f}" for v in row["pose"]["translation"])
        print(f"        {row['name']:<10} placed_by {row['placed_by']:<8} at [{xyz}]")
    if "note" in place:
        print(f"        {place['note']}")
    files = _common.files({"step": out["path"]})
    _common.write_manifest(
        paths,
        {
            "export": {
                "step": {k: out[k] for k in ("schema", "products", "unit") if k in out},
                "step_roundtrip": out.get("roundtrip"),
                "manifest": out["manifest"],
                "poses_written": out["manifest"]["poses_written"],
                "files": files,
            }
        },
        probe=probe,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    top = _common.parser("examples.shaft_housing", DOC, STAGES, out="shaft_housing_out")
    args = top.parse_args(argv)
    table = {
        "model": stage_model,
        "assemble": stage_assemble,
        "check": stage_check,
        "export": stage_export,
    }
    if args.stage == "all":
        return _common.run_all(args, tuple(table[name] for name in STAGES))
    return table[args.stage](args)


if __name__ == "__main__":
    raise SystemExit(main())
