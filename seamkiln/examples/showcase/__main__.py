"""`python -m examples.showcase {stills|cards|montage|all} --cape DIR --fur DIR --to FILE`"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from examples import _common

HERE = Path(__file__).resolve().parent


def stage_stills(args) -> int:
    """The flat pattern and the arranged (undressed) jacket, as data for Blender."""
    from examples.fur_walk import sim as fur
    from seamkiln.drape.dressing import frame_from_figure, wrap_arrangement
    from seamkiln.drape.garment import build_garment
    from seamkiln.figure import figure, standing_offset
    from seamkiln.hardware import zipper as Z

    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    pattern = fur.jacket_pattern()
    pose = fur.walk_pose(fur.gait("walk", cycles=1.0, samples_per_cycle=48), 0.0, 24)
    frame = frame_from_figure(pose, height=fur.HEIGHT)
    garment = build_garment(
        pattern,
        wrap_arrangement(pattern, frame, height=fur.HEIGHT),
        particle_distance=fur.FULL["particle_mm"],
    )
    fitted = Z.install(
        garment,
        garment.points,
        seam_id="centre-front",
        spec=Z.ZipperSpec(material="metal", size=8.0),
    )
    body = figure(pose, height=fur.HEIGHT)
    lift = standing_offset(body)
    body.apply_translation(lift)
    body.export(work / "body.ply")
    np.save(work / "arranged.npy", (garment.points + lift).astype(np.float32))
    np.save(work / "arranged_tri.npy", garment.triangles)
    (work / "pattern.json").write_text(
        json.dumps(
            {
                "name": pattern.name,
                "panels": [
                    {"id": q.id, "outline": [[v.x, v.y] for v in q.outline]} for q in pattern.panels
                ],
                "seams": [{"id": s.id, "kind": getattr(s, "kind", "plain")} for s in pattern.seams],
                "zip": fitted.summary(),
            },
            indent=1,
        )
    )
    res = (640, 360) if args.probe else (1920, 1080)
    code = _common.run_blender(
        HERE / "stills_blender.py",
        [work, *res, 8 if args.probe else 48],
        blender=args.blender,
        log=work / "blender.log",
    )
    print(f"stills: exit {code} -> {work}")
    return code


def cards_spec(args) -> list[dict]:
    """What the cards say. Numbers here are the ones the campaign measured."""
    return [
        {
            "name": "title",
            "seconds": 3.0,
            "title": "seamkiln",
            "lines": [
                "the garment lane of the Token Efficiency Engine",
                "2D patterns · sewing · hardware · drape · fit · handoff",
                "headless first; the GUI and the AI drive the same session",
            ],
        },
        {
            "name": "draft",
            "seconds": 3.0,
            "title": "draft, arrange, dress",
            "lines": [
                "a sewn jacket block with a zipped centre front",
                "wrap-arranged from the figure's own frame, then dressed:",
                "shoulders pinned, seams basted, settled, released",
            ],
            "still": "pattern.png",
        },
        {
            "name": "arranged",
            "seconds": 3.0,
            "title": "on the body before the solver",
            "lines": [
                "panels wrap the cylinder the pattern dictates",
                "sleeves hang down the arm axes; the collar clears the deltoid",
                "hardware is trim: a #8 brass zipper with its own weight",
            ],
            "still": "arranged.png",
        },
        {"name": "fur", "seconds": 0.0, "title": "walk", "lines": [], "clip": "fur"},
        {"name": "cape", "seconds": 0.0, "title": "cape", "lines": [], "clip": "cape"},
        {
            "name": "end",
            "seconds": 4.0,
            "title": "measured, not asserted",
            "lines": [
                "29 session verbs, replayed to one fingerprint",
                "17 always-loaded tools, 2,033 tokens - unchanged since before A53",
                "14 sk_* virtual tools behind progressive disclosure",
                "both shots re-run from the repo: python -m examples.cape_shot all",
            ],
        },
    ]


def stage_cards(args) -> int:
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    spec = [c for c in cards_spec(args) if not c.get("clip")]
    (work / "cards.json").write_text(json.dumps(spec, indent=1))
    res = (640, 360) if args.probe else (1920, 1080)
    code = _common.run_blender(
        HERE / "cards_blender.py",
        [work, *res, 8 if args.probe else 32],
        blender=args.blender,
        log=work / "blender.log",
    )
    print(f"cards: exit {code} -> {work}")
    return code


def stage_montage(args) -> int:
    work = Path(args.work)
    cape, fur = _common.layout(args.cape), _common.layout(args.fur)
    fps = int(_common.read_manifest(fur["sim"])["fps"])
    if fps != int(_common.read_manifest(cape["sim"])["fps"]):
        print("montage: the two shots were simulated at different frame rates")
        return 2
    plan = []
    for card in cards_spec(args):
        if card.get("clip") == "fur":
            plan.append({"kind": "clip", "frames": str(fur["frames"]), "audio": str(fur["wav"])})
        elif card.get("clip") == "cape":
            plan.append({"kind": "clip", "frames": str(cape["frames"]), "audio": str(cape["wav"])})
        else:
            plan.append(
                {
                    "kind": "card",
                    "image": str(work / f"card_{card['name']}.png"),
                    "frames": round(card["seconds"] * fps),
                }
            )
    (work / "montage.json").write_text(json.dumps({"fps": fps, "plan": plan}, indent=1))
    res = (640, 360) if args.probe else (1920, 1080)
    to = Path(args.to).expanduser()
    code = _common.run_blender(
        HERE / "montage_blender.py",
        [work / "montage.json", to, *res],
        blender=args.blender,
        log=work / "blender.log",
    )
    _common.settle_output(to)
    print(f"montage: exit {code} -> {to}")
    return code


def main(argv: list[str] | None = None) -> int:
    top = argparse.ArgumentParser(prog="examples.showcase", description=__doc__)
    sub = top.add_subparsers(dest="stage", required=True)
    for stage in ("stills", "cards", "montage", "all"):
        p = sub.add_parser(stage)
        p.add_argument("--cape", default="cape_shot_out", help="the cape_shot --out directory")
        p.add_argument("--fur", default="fur_walk_out", help="the fur_walk --out directory")
        p.add_argument("--work", default="showcase_out")
        p.add_argument("--to", default="seamkiln-showcase.mp4")
        p.add_argument("--probe", action="store_true")
        p.add_argument("--blender", default=None)
    args = top.parse_args(argv)
    stages = {"stills": stage_stills, "cards": stage_cards, "montage": stage_montage}
    if args.stage == "all":
        for stage in (stage_stills, stage_cards, stage_montage):
            code = stage(args)
            if code:
                return code
        return 0
    return stages[args.stage](args)


if __name__ == "__main__":
    sys.exit(main())
