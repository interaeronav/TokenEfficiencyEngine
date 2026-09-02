"""`python -m examples.fur_walk {sim|render|sound|encode|all} --out DIR [--probe]`"""

from __future__ import annotations

import sys
from pathlib import Path

from examples import _common
from examples.fur_walk import sim, sound

HERE = Path(__file__).resolve().parent
DOC = "A fur jacket on a figure walking toward the camera."


def stage_sim(args) -> int:
    paths = _common.layout(args.out)
    sim.simulate(paths["sim"], fps=args.fps, seconds=args.seconds, probe=args.probe)
    return 0


def stage_render(args) -> int:
    paths = _common.layout(args.out)
    manifest = _common.read_manifest(paths["sim"])
    args.probe = args.probe or bool(manifest.get("probe"))
    res, samples = _common.render_settings(args, res=(1920, 1080), samples=48)
    code = _common.run_blender(
        HERE / "render_blender.py",
        [paths["sim"], paths["frames"], args.first, args.last, *res, samples],
        blender=args.blender,
        log=paths["log"],
    )
    print(f"render: exit {code}; frames in {paths['frames']} (log: {paths['log']})")
    return code


def stage_sound(args) -> int:
    paths = _common.layout(args.out)
    sound.soundtrack(paths["sim"], paths["wav"])
    return 0


def stage_encode(args) -> int:
    paths = _common.layout(args.out)
    manifest = _common.read_manifest(paths["sim"])
    probe = args.probe or bool(manifest.get("probe"))
    if not sorted(paths["frames"].glob("*.png")):
        print(f"encode: no frames in {paths['frames']} - run `render` first")
        return 2
    res = (640, 360) if probe else (1920, 1080)
    to = Path(args.to) if args.to else paths["root"] / "fur-jacket-walk.mp4"
    code = _common.encode(
        paths["frames"],
        to,
        fps=int(manifest["fps"]),
        audio=paths["wav"],
        res=res,
        blender=args.blender,
        log=paths["log"],
    )
    print(f"encode: exit {code}; {to}")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = _common.parser(
        "examples.fur_walk", DOC, seconds=sim.DURATION, fps=24, out="fur_walk_out"
    )
    args = parser.parse_args(argv)
    if args.stage == "all":
        for stage in (stage_sim, stage_sound, stage_render, stage_encode):
            code = stage(args)
            if code:
                return code
        return 0
    return {"sim": stage_sim, "render": stage_render, "sound": stage_sound, "encode": stage_encode}[
        args.stage
    ](args)


if __name__ == "__main__":
    sys.exit(main())
