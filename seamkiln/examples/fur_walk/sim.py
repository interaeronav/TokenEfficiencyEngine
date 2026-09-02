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
from seamkiln.drape.body import BodyMotion, sdf_from_mesh
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
    """The jacket's shell: heavy and high-friction, stiffer than a suiting but
    not a board. The first cut was 3.4x a suiting's bending and 40 % ease, and
    it hung like a box - the pelt reads as fur through its strands, not
    through the shell refusing to bend."""
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    base = fabric_by_name("wool_suiting")
    return materials.add(
        materials.derive(
            "wool_suiting",
            "fur_shell",
            gsm=base.gsm * 1.6,
            thickness_mm=4.0,
            bend_warp=base.bend_warp * 2.2,
            bend_weft=base.bend_weft * 2.0,
            friction=min(base.friction * 1.5, 0.95),
            notes="shearling shell: pelt plus backing, heavy, firm in bending",
        ),
        category="fur",
        overwrite=True,
    ).name


# Two layers, as a pelt has: a dense short undercoat and sparse long guard
# hairs with pale tips. One uniform layer read as a bath mat.
UNDERCOAT = {
    "density_per_cm2": 9.0,
    "length_mm": 24.0,
    "curl": 0.5,
    "droop": 0.7,
    "clump": 0.5,
    "seed": 4242,
}
GUARD = {
    "density_per_cm2": 1.4,
    "length_mm": 46.0,
    "curl": 0.35,
    "droop": 0.85,
    "clump": 0.3,
    "seed": 4243,
}


def jacket_pattern():
    """A fitted jacket: +30 % ease over the figure's 1.2 m chest (half_chest
    390 on a 191 mm chest radius), shoulders a little past the figure's own
    (215 mm against a 197 mm neck-to-joint), and a sleeve 1.32 times the arm
    - wide enough to hook over the deltoid with margin, which a 1.18x sleeve
    slid off during the walk - with the cap height solved to the armhole.
    The block ties the armhole to the length and the chest, so this is the
    cut that takes that sleeve. The first cut had 40 % ease and 250 mm
    shoulders and hung like a tent."""
    arm_mm = 2.0 * math.pi * HEIGHT * 0.034 * 1000.0
    return jacket_block(
        opening="zipper",
        length=700.0,
        half_chest=390.0,
        shoulder=215.0,
        sleeve_length=470.0,
        # a half-width: 160 is a 320 mm cuff, which the figure's 295 mm hand
        # passes with room; 150 was 300 and tight on the elbow ball
        cuff=160.0,
        biceps=arm_mm * 1.32,
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


def arms_by_the_sides(track, fps: int) -> float:
    """The moment in the cycle when both arms hang straightest.

    A fitter dresses a figure with its arms at its sides, and so must this.
    The gait track begins mid-swing - one arm 20 degrees forward, the other
    20 back - and a jacket dressed in that pose had one sleeve hung on a
    forward-swung arm: measured, that sleeve slid 60 mm down the outside of
    the arm in the first second of the walk while the other never moved. The
    walk simply starts here instead; a gait has no first frame.
    """
    best, best_t = None, 0.0
    for k in range(int(fps * 4 * track.duration) + 1):
        t = k / (fps * 4)
        pose = walk_pose(track, t, fps)
        swing = abs(float(pose.shoulder_l)) + abs(float(pose.shoulder_r))
        if best is None or swing < best:
            best, best_t = swing, t
    return best_t


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
    for sub in ("cloth", "fur", "guard", "body"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    shell = fur_shell()
    track = gait("walk", cycles=1.0, samples_per_cycle=48)
    # The gait's OWN speed: moved slower or faster than its stride a body
    # slides every foot through its own stance.
    speed = GAITS["walk"].speed_ms
    pattern = jacket_pattern()
    phase = arms_by_the_sides(track, fps)
    rest_pose = walk_pose(track, phase, fps)
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
        "phase_offset_s": round(phase, 4),
        "shots": [],
    }
    if probe:
        manifest["note"] = (
            "a probe proves the pipeline runs; what it measures is not evidence "
            "- never rely on a coarse preview"
        )
    # The body moves CONTINUOUSLY through each frame. Every pose is built
    # body-local up front (milliseconds each) so its field can be baked on the
    # one lattice all the frames share; the walk's travel and the lift that
    # keeps the lowest foot on the ground are a rigid placement the solver
    # carries exactly, and the pose change between two frames is two fields
    # blended across the frame's substeps. The jacket is never teleported -
    # the contact carries it - and the cloth's velocity is carried from frame
    # to frame, seeded with the walk's speed so the shot has no first frame.
    voxel = float(opts["voxel_mm"])
    steps = settings.frames * settings.substeps
    poses = [walk_pose(track, i / fps + phase, fps) for i in range(frames)]
    locals_ = [figure(pose, height=HEIGHT, facing_deg=0.0) for pose in poses]
    bounds = (
        np.min([m.bounds[0] for m in locals_], axis=0),
        np.max([m.bounds[1] for m in locals_], axis=0),
    )
    velocity = None
    previous = None
    clock = Stopwatch()
    fur_seconds = 0.0
    field_seconds = 0.0
    for i in range(frames):
        t = i / fps
        local = locals_[i]
        lift = float(standing_offset(local)[1])  # the lowest foot ON the ground
        offset = np.array([0.0, lift, WALK_START_Z + speed * t])
        bake = Stopwatch()
        placed = sdf_from_mesh(local, voxel_mm=voxel, bounds=bounds).moved(offset)
        field_seconds += bake.s

        if i == 0:
            # dress the jacket onto the body before the walk starts, or the
            # first second of the shot is a coat falling into place
            garment.points = garment.points + offset
            settled = dress(
                garment,
                placed,
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
            result = drape(garment, placed, fabric=shell, settings=settings, prepared=prepared)
            velocity = result.velocity + np.array([0.0, 0.0, speed])[None, :]
        else:
            motion = BodyMotion.between(previous, placed, steps=steps)
            result = drape(
                garment,
                previous,
                fabric=shell,
                settings=settings,
                prepared=prepared,
                velocity=velocity,
                motion=motion,
            )
            velocity = result.velocity
        garment.points = result.points
        previous = placed

        fur_clock = Stopwatch()
        pelt = finishing.fur(result.points, garment.triangles, **UNDERCOAT)
        guard = finishing.fur(result.points, garment.triangles, **GUARD)
        fur_seconds += fur_clock.s

        np.save(out / "cloth" / f"{i:04d}.npy", result.points.astype(np.float32))
        np.save(
            out / "fur" / f"{i:04d}.npy",
            np.stack([pelt.starts, pelt.mids, pelt.ends], axis=1).astype(np.float32),
        )
        np.save(
            out / "guard" / f"{i:04d}.npy",
            np.stack([guard.starts, guard.mids, guard.ends], axis=1).astype(np.float32),
        )
        local.export(out / "body" / f"{i:04d}.ply")
        manifest["shots"].append(
            {
                "frame": i,
                "t": round(t, 3),
                "offset": [round(float(v), 4) for v in offset],
                "pelvis_y": round(float(lift), 4),
                "strands": int(pelt.starts.shape[0]),
                "guard_hairs": int(guard.starts.shape[0]),
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
    manifest["field_seconds"] = round(field_seconds, 2)
    manifest["body_motion"] = "continuous within each frame (BodyMotion.between)"
    manifest["seconds"] = round(clock.s, 1)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log(f"done: {frames} frames in {clock.s:.1f}s ({fur_seconds:.1f}s growing fur) -> {out}")
    return manifest
