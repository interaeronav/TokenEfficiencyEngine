"""A fur jacket, on a body that walks toward camera.

Three things are asked of the stack at once, and each is solved by the part
of it that should solve it:

  the WALK    is a pose track from standard clinical gait kinematics; the
              lowest foot is put on the ground every frame and the pelvis
              rises because the stance leg straightens.
  the JACKET  is a real sewn pattern (two fronts, a back, two sleeves, a
              zipped centre front), wrap-arranged from the figure's own
              frame and DRESSED by the kernel, then draped on the moving
              body carrying its velocity frame to frame.
  the FUR     is grown on the DRAPED cloth, scattered by triangle area, and
              regrown each frame from the same seed - which roots every
              strand at the same barycentric point on the same triangle.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from examples._common import Stopwatch
from seamkiln import finishing, materials
from seamkiln.avatar import GAITS, Pose, gait
from seamkiln.drape.body import sdf_from_mesh
from seamkiln.drape.dressing import dress, frame_from_figure, shoulder_anchors, wrap_arrangement
from seamkiln.drape.environment import Environment
from seamkiln.drape.garment import build_garment
from seamkiln.drape.solve import DrapeSettings, drape, prepare
from seamkiln.figure import figure, standing_offset
from seamkiln.hardware import zipper as Z
from seamkiln.pattern.fixtures import jacket_block

HEIGHT = 1.80
DURATION = 4.5  # at 1.35 m/s this covers 6.1 m and ends 1.5 m short of the camera
# The figure is built facing +Z and walks +Z: the front of the garment and
# the front of the body are the same direction without a rotation to get wrong.
WALK_START_Z = -7.6
FUR_PER_CM2 = 6.0

# 11 mm: the jacket CONVERGES there (worst seam 36.5 mm); 14 mm does not.
FULL = {
    "fps": 24,
    "particle_mm": 11.0,
    "voxel_mm": 14.0,
    "substeps": 22,
    "hold": 180,
    "settle": 220,
}
PROBE = {"fps": 6, "particle_mm": 20.0, "voxel_mm": 24.0, "substeps": 8, "hold": 30, "settle": 30}


def fur_shell() -> str:
    """The jacket's shell: heavy, stiff, high-friction. A fur coat holds a bell
    shape instead of following the body, and that shape is most of what makes
    it read as fur before a single strand is drawn."""
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    base = fabric_by_name("wool_suiting")
    return materials.add(
        materials.derive(
            "wool_suiting",
            "fur_shell",
            gsm=base.gsm * 1.85,
            thickness_mm=5.0,
            bend_warp=base.bend_warp * 3.4,
            bend_weft=base.bend_weft * 3.2,
            friction=min(base.friction * 1.5, 0.95),
            notes="shearling shell: pelt plus backing, heavy and stiff in bending",
        ),
        category="fur",
        overwrite=True,
    ).name


def jacket_pattern():
    """half_chest 420 is +25 % ease over this figure's chest, which a bulky
    coat has; the sleeve WIDTH is set by the arm (`biceps=`) and the cap
    height solved to the armhole - the trade a drafter makes."""
    arm_mm = 2.0 * math.pi * HEIGHT * 0.034 * 1000.0
    return jacket_block(
        opening="zipper",
        length=700.0,
        half_chest=420.0,
        shoulder=250.0,
        sleeve_length=480.0,
        cuff=170.0,
        biceps=arm_mm * 1.25,
    )


def walk_pose(track, t: float, fps: int) -> Pose:
    """The gait at a moment, with the scripted rise taken OUT: the body is
    placed by its own feet, so keeping it would lift the figure twice."""
    cycle = track.duration
    values = dict(track.sample(fps * 4))
    keys = sorted(values)
    at = t % cycle
    lo = max([k for k in keys if k <= at], default=keys[0])
    return Pose.from_values({k: v for k, v in values[lo].items() if k != "rise_m"})


def simulate(
    out_dir: str | Path,
    *,
    fps: int | None = None,
    seconds: float = DURATION,
    probe: bool = False,
    log=print,
) -> dict[str, Any]:
    """Run the walk. Returns the manifest it wrote to `out_dir`."""
    opts = dict(PROBE if probe else FULL)
    if fps is not None:
        opts["fps"] = int(fps)
    fps = int(opts["fps"])
    out = Path(out_dir)
    for sub in ("cloth", "fur", "body"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    shell = fur_shell()
    track = gait("walk", cycles=1.0, samples_per_cycle=48)
    # The gait's OWN speed: moved slower or faster than its stride a body
    # slides every foot through its own stance.
    speed = GAITS["walk"].speed_ms
    pattern = jacket_pattern()
    rest_pose = walk_pose(track, 0.0, fps)
    frame = frame_from_figure(rest_pose, height=HEIGHT)
    garment = build_garment(
        pattern,
        wrap_arrangement(pattern, frame, height=HEIGHT),
        particle_distance=float(opts["particle_mm"]),
    )
    log(
        f"jacket: {garment.n_points} particles, {garment.triangles.shape[0]} triangles"
        + ("  [PROBE - not evidence]" if probe else "")
    )

    fitted = Z.install(
        garment,
        garment.points,
        seam_id="centre-front",
        spec=Z.ZipperSpec(material="metal", size=8.0),
    )
    Z.apply(garment, fitted)
    log(f"zip: {json.dumps(fitted.summary())}")

    room = Environment(
        name="still room", wind=(0.0, 0.0, -0.35), wind_gust=0.25, temperature_c=6.0, humidity=0.55
    )
    settings = DrapeSettings(
        frames=max(round((1.0 / fps) / (1.0 / 60.0)), 1),
        substeps=int(opts["substeps"]),
        environment=room,
    )
    prepared = prepare(garment, fabric=shell, settings=settings)

    frames = round(seconds * fps)
    manifest: dict[str, Any] = {
        "example": "fur_walk",
        "probe": bool(probe),
        "fps": fps,
        "frames": frames,
        "height_m": HEIGHT,
        "fabric": shell,
        "zip": fitted.summary(),
        "settings": opts,
        "shots": [],
    }
    if probe:
        manifest["note"] = (
            "a probe proves the pipeline runs; what it measures is not evidence "
            "- never rely on a coarse preview"
        )
    velocity = None
    clock = Stopwatch()
    fur_seconds = 0.0
    for i in range(frames):
        t = i / fps
        pose = walk_pose(track, t, fps)
        local = figure(pose, height=HEIGHT, facing_deg=0.0)
        lift = float(standing_offset(local)[1])  # the lowest foot ON the ground
        offset = np.array([0.0, lift, WALK_START_Z + speed * t])
        placed = local.copy()
        placed.apply_translation(offset)
        field = sdf_from_mesh(placed, voxel_mm=float(opts["voxel_mm"]))

        if i == 0:
            # dress the jacket onto the body before the walk starts, or the
            # first second of the shot is a coat falling into place
            garment.points = garment.points + offset
            settled = dress(
                garment,
                field,
                fabric=shell,
                anchors=shoulder_anchors(frame, offset),
                hold_frames=int(opts["hold"]),
                settle_frames=int(opts["settle"]),
                substeps=int(opts["substeps"]),
            )
            manifest["dressed"] = {
                "seam_max_mm": settled.seam_gaps["max_gap_mm"],
                "touching_fraction": settled.contact["touching_fraction"],
                "mean_distance_mm": settled.contact["mean_distance_mm"],
                "worn": bool(settled.contact.get("worn")),
            }
            log(
                f"  dressed: worst seam {settled.seam_gaps['max_gap_mm']:.1f} mm, "
                f"touching {settled.contact['touching_fraction']:.0%}, "
                f"mean gap {settled.contact['mean_distance_mm']:.0f} mm, "
                f"worn {settled.contact.get('worn')}"
            )
        else:
            garment.points = garment.points + np.array([0.0, 0.0, speed / fps])

        result = drape(
            garment, field, fabric=shell, settings=settings, prepared=prepared, velocity=velocity
        )
        velocity = result.velocity
        garment.points = result.points

        fur_clock = Stopwatch()
        pelt = finishing.fur(
            result.points,
            garment.triangles,
            density_per_cm2=FUR_PER_CM2,
            length_mm=26.0,
            curl=0.55,
            droop=0.62,
            clump=0.45,
            seed=4242,
        )
        fur_seconds += fur_clock.s

        np.save(out / "cloth" / f"{i:04d}.npy", result.points.astype(np.float32))
        np.save(
            out / "fur" / f"{i:04d}.npy",
            np.stack([pelt.starts, pelt.mids, pelt.ends], axis=1).astype(np.float32),
        )
        local.export(out / "body" / f"{i:04d}.ply")
        manifest["shots"].append(
            {
                "frame": i,
                "t": round(t, 3),
                "offset": [round(float(v), 4) for v in offset],
                "pelvis_y": round(float(lift), 4),
                "strands": int(pelt.starts.shape[0]),
                "seam_max_mm": result.seam_gaps["max_gap_mm"],
                "worn": bool(result.contact.get("worn")),
            }
        )
        if i % max(fps // 2, 1) == 0:
            log(
                f"  frame {i:3d}/{frames}  t={t:.2f}s  z={offset[2]:+.2f}  lift={lift:.3f}  "
                f"{pelt.starts.shape[0]} strands  {clock.s:5.1f}s"
            )

    np.save(out / "cloth_topology.npy", garment.triangles)
    np.save(out / "cloth_uv.npy", garment.rest_points_mm)
    manifest["fur_seconds"] = round(fur_seconds, 2)
    manifest["seconds"] = round(clock.s, 1)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log(f"done: {frames} frames in {clock.s:.1f}s ({fur_seconds:.1f}s growing fur) -> {out}")
    return manifest
