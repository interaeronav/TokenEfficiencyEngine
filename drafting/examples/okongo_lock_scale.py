"""Lock the Okongo scan's scale to tape readings, then report the correction.

    server/.venv/bin/python drafting/examples/okongo_lock_scale.py \
        --b1 3952 --b2 2874

Every argument is a TAPE reading in millimetres. Nothing here estimates one:
if you do not pass a baseline it is not used, and if you pass none the script
refuses. A drawing that says its scale is verified when nobody measured
anything is worse than one that admits it is not.

Two baselines minimum, on different axes, and prefer the LONG ones: a 5 mm
reading error over 3.9 m is 1,266 ppm, the same error over 1.5 m is 3,331.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, "/Users/john/TokenEfficiencyEngine/server/src")

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.pointcloud.tools import register_pointcloud_tools

WORK = Path(
    "/private/tmp/claude-501/-Users-john-TokenEfficiencyEngine/"
    "1d43fd51-eeff-4925-b1bd-bb2fba2d38c1/scratchpad/okongo-work"
)

# Where each baseline runs, in the levelled frame, from the P02 fit. The picks
# are approximate on purpose - pc_control_add snaps each one to its local wall.
BASELINES = {
    "b1": ("ROOM 01 north-south", [0.10, -2.30, 1.20], [0.10, 1.57, 1.20]),
    "b2": ("ROOM 01 east-west", [-1.27, -0.40, 1.20], [1.52, -0.40, 1.20]),
    "b3": ("ROOM 02 east-west", [-3.12, -0.90, 1.20], [-1.70, -0.90, 1.20]),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for key, (label, _, _) in BASELINES.items():
        parser.add_argument(f"--{key}", type=float, help=f"{label}, mm")
    parser.add_argument("--tol", type=float, default=8.0, help="tape tolerance, mm")
    args = parser.parse_args()

    given = {k: getattr(args, k) for k in BASELINES if getattr(args, k)}
    if len(given) < 2:
        parser.error(
            "give at least two baselines on different axes - one cannot "
            "distinguish a scale error from a single bad reading"
        )

    outputs = json.loads((WORK / "outputs.json").read_text())
    app = TeeApp({"fake": FakeAdapter()}, project_root=WORK)
    register_pointcloud_tools(app, WORK)
    call = lambda tool, **a: app.registry.call(tool, a)
    try:
        cloud = outputs["lid"]
        for key, reading in given.items():
            label, p1, p2 = BASELINES[key]
            out = call(
                "pc_control_add",
                cloud_id=cloud,
                name=label,
                p1=p1,
                p2=p2,
                true_mm=reading,
                tol_mm=args.tol,
            )
            print(
                f"  {label:24s} scan {out['measured_mm']:8.1f}  tape {reading:8.1f}"
                f"  delta {out['delta_mm']:+7.1f} mm"
            )

        check = call("pc_control_verify", cloud_id=cloud)
        print(f"\n  suggested scale   {check['suggested_scale']:.6f}")
        print(f"  residual          {check['scale_residual_ppm']:.0f} ppm")
        print(f"  worst offender    {check['worst_offender']} ({check['worst_delta_mm']:+.1f} mm)")
        for key in ("drift", "units_conflict", "fix"):
            if check.get(key):
                print(f"  {key.upper()}: {check[key]}")
        if check.get("drift"):
            print("\n  NOT applying a scale: drift means no single factor is right.")
            return 1

        scaled = call("pc_scale_apply", cloud_id=cloud)
        report = call("pc_report", cloud_id=scaled["cloud_id"])
        print(f"\n  scaled cloud      {scaled['cloud_id']}  (factor {scaled['factor']})")
        print(f"  verdict           {report['verdict']} - {report['advice']}")
        print(f"  worst control     {report.get('worst_control_mm', '-')} mm")
        outputs["lid"] = scaled["cloud_id"]
        outputs["scale_factor"] = scaled["factor"]
        (WORK / "outputs.json").write_text(json.dumps(outputs, default=str))
        print("\n  outputs.json updated - re-run okongo_reissue.py to issue P03.")
    finally:
        app.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
