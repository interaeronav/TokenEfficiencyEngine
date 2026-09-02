"""The shot, simulated: a cape of the Namibian flag on a leaping hero.

Everything the camera will see that MOVES is solved here rather than posed
by hand - the cape is cloth, the wind is a drag force per triangle, and
getting wet is a heavier fabric card, not a darker texture.

The beats, and what each one is physically:

    0.0 - 0.9   crouched on the first box; the cape hangs, the wind lifts it
    0.9 - 2.0   the leap: a parabola, so the body is in free fall and the
                cape is dragged by the air it is moving through
    2.0 - 2.7   landing on the second box, the cape catching up and folding
    2.7 - 3.75  the second leap, onto the bouncy mat
    3.75 - 4.03 the bounce: 0.28 s of contact, built from the velocities
    4.03 - 6.0  one ballistic arc into the water
    6.0 - 8.0   in the pool: the suit and the cape are WET. The fabric card
                is swapped for one carrying its own water, and wetness is
                tracked PER VERTEX, because a cape enters a pool hem-first.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from examples._common import Stopwatch
from seamkiln import materials
from seamkiln.avatar import Pose
from seamkiln.drape.body import sdf_from_mesh
from seamkiln.drape.environment import Environment
from seamkiln.drape.garment import GarmentMesh, Placement, build_garment
from seamkiln.drape.solve import DrapeSettings, drape, prepare
from seamkiln.figure import clasp_points, figure
from seamkiln.pattern.geometry import Vertex
from seamkiln.pattern.model import Panel, Pattern

HEIGHT = 1.80
# The figure is built facing +Z; this shot travels along +X, so it is turned.
FACING_DEG = 90.0
DRY = "silk_habotai"

# -- the set --------------------------------------------------------------------
BOX_A = {"centre": (0.0, 0.0, 0.0), "size": (1.1, 0.95, 1.1)}
BOX_B = {"centre": (2.6, 0.0, 0.0), "size": (1.1, 1.35, 1.1)}
MAT = {"centre": (5.2, 0.0, 0.0), "size": (2.0, 0.42, 2.0)}
# The pool is a HOLE: size[1] is a depth and the water sits just below ground
# level. As a solid block with water on top, the hero landed ON it like a
# plinth - you cannot get wet standing on a swimming pool.
POOL = {"centre": (8.6, 0.0, 0.0), "size": (4.2, 3.10, 2.9)}
WATER_Y = -0.06

# The bounce, in seconds: a trampoline contact is about a quarter of a second.
LAND, BOTTOM, LAUNCH = 3.75, 3.88, 4.03
# How far the mat gives. It MUST be less than the mat is thick: a 0.30 m mat
# compressed by 0.34 m put the hero's feet under the ground at the bottom of
# every bounce, and the bounce looked like nothing was happening.
MAT_DEPTH = 0.26
DURATION = 8.0

FULL = {"fps": 24, "particle_mm": 17.0, "voxel_mm": 16.0, "substeps": 22, "settle": 180}
PROBE = {"fps": 6, "particle_mm": 26.0, "voxel_mm": 26.0, "substeps": 8, "settle": 30}


def cape_pattern(*, width_mm: float = 620.0, length_mm: float = 1080.0) -> Pattern:
    """One panel: a cape is a flag with a neck edge.

    A trapezoid - narrow at the shoulders, wide at the hem - because that is
    what makes a cape billow rather than hang like a towel. The flat pattern
    IS the UV map, so the flag lands on it undistorted.
    """
    half_top, half_hem = width_mm * 0.42, width_mm * 0.95
    outline = [
        Vertex(-half_top, length_mm),
        Vertex(half_top, length_mm),
        Vertex(half_hem, 0.0),
        Vertex(-half_hem, 0.0),
        Vertex(-half_top, length_mm),
    ]
    return Pattern(
        name="namibia-cape", panels=[Panel(id="CAPE", name="Cape", outline=outline)], units="mm"
    )


def wet(base: str) -> str:
    """The same cloth, carrying water: +55 % mass, -35 % bending rigidity.

    `derive` makes the card and `add` puts it in the library, two steps on
    purpose; `derive` drops the tier to `plausible`, which is right - a
    measured cloth's test report does not describe one somebody dunked.
    """
    from seamkiln.pattern.fabric import fabric as fabric_by_name

    dry = fabric_by_name(base)
    return materials.add(
        materials.derive(
            base,
            f"{base}_wet",
            gsm=dry.gsm * 1.55,
            bend_warp=dry.bend_warp * 0.65,
            bend_weft=dry.bend_weft * 0.65,
            friction=min(dry.friction * 1.4, 0.95),
            notes="soaked: +55% mass from water pickup, -35% bending rigidity",
        ),
        category="wet",
        overwrite=True,
    ).name


def support(t: float, squash: float) -> float | None:
    """The surface underfoot, or None in the air.

    The trajectory places the body's ORIGIN and a body that folds moves its
    own feet relative to it; knowing where the ground is lets the feet be put
    ON it instead of near it.
    """
    if t < 0.9:
        return BOX_A["size"][1]
    if 2.0 <= t < 2.7:
        return BOX_B["size"][1]
    if LAND <= t < LAUNCH:
        return MAT["size"][1] - MAT_DEPTH * squash
    return None


def trajectory(t: float) -> tuple[np.ndarray, Pose, bool, float]:
    """Where the hero is, how they are folded, whether they are wet, and how
    hard the mat is being squashed underneath them."""

    def arc(t0, t1, x0, x1, y0, y1, peak):
        u = min(max((t - t0) / (t1 - t0), 0.0), 1.0)
        return x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + peak * 4.0 * u * (1.0 - u), u

    top_a, top_b, mat_top = BOX_A["size"][1], BOX_B["size"][1], MAT["size"][1]

    if t < 0.9:  # crouched, gathering
        u = t / 0.9
        crouch = 34.0 * math.sin(math.pi * u) ** 2
        return (
            np.array([0.0, top_a, 0.0]),
            Pose(
                hip_l=crouch,
                hip_r=crouch,
                knee_l=crouch * 1.9,
                knee_r=crouch * 1.9,
                shoulder_l=-18.0 * u,
                shoulder_r=-18.0 * u,
                elbow_l=30,
                elbow_r=30,
                trunk_lean=10.0 * u,
            ),
            False,
            0.0,
        )
    if t < 2.0:  # leap one
        x, y, u = arc(0.9, 2.0, 0.0, BOX_B["centre"][0], top_a, top_b, 1.05)
        tuck = 60.0 * math.sin(math.pi * u)
        return (
            np.array([x, y, 0.0]),
            Pose(
                hip_l=tuck,
                hip_r=tuck * 0.6,
                knee_l=tuck * 1.6,
                knee_r=tuck * 0.8,
                shoulder_l=-95.0 * math.sin(math.pi * u) - 10,
                shoulder_r=-70.0 * u - 10,
                elbow_l=15,
                elbow_r=25,
                trunk_lean=16.0,
            ),
            False,
            0.0,
        )
    if t < 2.7:  # land and re-gather
        u = (t - 2.0) / 0.7
        crouch = 44.0 * math.sin(math.pi * u) ** 2
        return (
            np.array([BOX_B["centre"][0], top_b, 0.0]),
            Pose(
                hip_l=crouch,
                hip_r=crouch,
                knee_l=crouch * 1.9,
                knee_r=crouch * 1.9,
                shoulder_l=-25.0,
                shoulder_r=-25.0,
                elbow_l=40,
                elbow_r=40,
                trunk_lean=8.0 + 8.0 * u,
            ),
            False,
            0.0,
        )
    if t < LAND:  # leap two, onto the mat
        x, y, u = arc(2.7, LAND, BOX_B["centre"][0], MAT["centre"][0], top_b, mat_top, 0.85)
        tuck = 55.0 * math.sin(math.pi * u)
        return (
            np.array([x, y, 0.0]),
            Pose(
                hip_l=tuck,
                hip_r=tuck * 0.7,
                knee_l=tuck * 1.7,
                knee_r=tuck,
                shoulder_l=-100.0 * math.sin(math.pi * u),
                shoulder_r=-85.0 * math.sin(math.pi * u),
                elbow_l=12,
                elbow_r=18,
                trunk_lean=14.0,
            ),
            False,
            0.0,
        )
    if t < LAUNCH:
        # THE BOUNCE, built from the velocities: the hero arrives at 4.2 m/s,
        # the mat brings that to rest in 0.13 s and returns it as 4.8 m/s
        # upward over 0.15 s. The first version ran the contact over 0.8 s,
        # topped out falling, and the next phase started 0.44 m higher - a
        # jump cut, not a bounce.
        if t < BOTTOM:
            u = (t - LAND) / (BOTTOM - LAND)
            y = mat_top - MAT_DEPTH * math.sin(u * math.pi / 2.0)
            squash = math.sin(u * math.pi / 2.0)
            fold = 20.0 + 55.0 * squash
        else:
            u = (t - BOTTOM) / (LAUNCH - BOTTOM)
            y = mat_top - MAT_DEPTH * (1.0 - u**2.1)
            squash = 1.0 - u**2.1
            fold = 75.0 * (1.0 - u) - 12.0 * u
        # A SQUAT: the knee folds about twice as far as the hip so the pelvis
        # comes down to the feet. Past 90 degrees of hip flexion the thigh
        # swings above horizontal and lifts the feet off the mat - 62 cm of
        # daylight under a hero who was supposed to be compressing it.
        return (
            np.array([MAT["centre"][0] + 0.30 * squash, y, 0.0]),
            Pose(
                hip_l=fold,
                hip_r=fold * 0.94,
                knee_l=fold * 1.9,
                knee_r=fold * 1.8,
                shoulder_l=-30.0 - 70.0 * (1.0 - squash),
                shoulder_r=-26.0 - 62.0 * (1.0 - squash),
                elbow_l=45.0 * squash + 8,
                elbow_r=42.0 * squash + 10,
                trunk_lean=18.0 * squash + 4.0,
            ),
            False,
            squash,
        )
    if t < 6.0:
        # ONE ballistic arc straight off the mat, beginning at exactly the
        # height and speed the rebound ended at - which removes the teleport.
        x, y, u = arc(
            LAUNCH,
            6.0,
            MAT["centre"][0] + 0.30,
            POOL["centre"][0] - 0.5,
            mat_top,
            WATER_Y + 0.10,
            2.40,
        )
        return (
            np.array([x, y, 0.0]),
            Pose(
                hip_l=-8 + 46 * u,
                hip_r=-6 + 40 * u,
                knee_l=10 + 55 * u,
                knee_r=8 + 48 * u,
                shoulder_l=-135 + 55 * u,
                shoulder_r=-125 + 48 * u,
                elbow_l=8 + 32 * u,
                elbow_r=12 + 32 * u,
                trunk_lean=-6.0 + 26 * u,
            ),
            u > 0.90,
            0.0,
        )
    # in the water: PLUNGE, then float back up. Getting the cape wet needs
    # the cape under, which needs the shoulders under, which needs a pool
    # deep enough to take a person head-first; and enough buoyancy to bring
    # them back out, because the point of the ending is seeing what got wet.
    u = (t - 6.0) / (DURATION - 6.0)
    plunge = 2.90 * (1.0 - math.exp(-u * 6.2))
    rise = 2.154 * max(0.0, (u - 0.34) / 0.66) ** 0.8
    bob = 0.05 * math.sin(u * math.pi * 3.2) * max(0.0, u - 0.5)
    return (
        np.array([POOL["centre"][0] - 0.5 + 0.7 * u, WATER_Y + 0.10 - plunge + rise + bob, 0.0]),
        Pose(
            hip_l=20 + 30 * u + 8 * math.sin(u * 7),
            hip_r=16 + 28 * u + 8 * math.cos(u * 7),
            knee_l=30 + 30 * u,
            knee_r=26 + 26 * u,
            shoulder_l=-100 + 55 * u + 18 * math.sin(u * 6),
            shoulder_r=-92 + 50 * u + 18 * math.cos(u * 6),
            elbow_l=25 + 34 * u,
            elbow_r=28 + 30 * u,
            trunk_lean=14.0 - 12.0 * u,
        ),
        True,
        0.0,
    )


def wind_at(t: float) -> Environment:
    """A windy day, and a gust that peaks over the jumps.

    4 m/s gusting to 6 - a stiff breeze. At 7.5-10 the drag swamped the
    cloth's own weight and the cape streamed rigid like a paper plane.
    Mostly a HEADWIND: a cross component near half the total blew the cape
    out past the shoulder and read as a flag on a pole.
    """
    gust = 1.0 + 0.42 * math.sin(t * 1.9) + 0.22 * math.sin(t * 4.7)
    speed = 4.0 * max(gust, 0.45)
    return Environment(
        name="windy day",
        wind=(-speed * 0.93, 0.22 * speed, -0.19 * speed),
        wind_gust=0.45,
        temperature_c=24.0,
        humidity=0.45,
    )


def top_edge(garment: GarmentMesh) -> np.ndarray:
    """The cape's neck edge - the particles the clasp holds."""
    flat = garment.rest_points_mm
    return np.nonzero(flat[:, 1] >= flat[:, 1].max() - 26.0)[0]


def clasp_targets(
    garment: GarmentMesh, clasp: np.ndarray, pose: Pose, offset: np.ndarray
) -> np.ndarray:
    """Where every clasp particle should be this frame: the top edge mapped
    along the line between the two shoulder anchors by its position in the
    FLAT pattern. Hung from one point at the neck a cape is a towel."""
    left, right = clasp_points(pose, height=HEIGHT, count=2, facing_deg=FACING_DEG)
    span = garment.rest_points_mm[clasp][:, 0]
    lo, hi = float(span.min()), float(span.max())
    u = (span - lo) / max(hi - lo, 1e-9)
    return left[None, :] + (right - left)[None, :] * u[:, None] + offset[None, :]


def hero(pose: Pose):
    return figure(pose, height=HEIGHT, facing_deg=FACING_DEG)


def simulate(
    out_dir: str | Path,
    *,
    fps: int | None = None,
    seconds: float = DURATION,
    probe: bool = False,
    log=print,
) -> dict[str, Any]:
    """Run the shot. Returns the manifest it wrote to `out_dir`."""
    opts = dict(PROBE if probe else FULL)
    if fps is not None:
        opts["fps"] = int(fps)
    fps = int(opts["fps"])
    out = Path(out_dir)
    (out / "cape").mkdir(parents=True, exist_ok=True)
    (out / "body").mkdir(parents=True, exist_ok=True)

    pattern = cape_pattern()
    shoulder_y = float(clasp_points(Pose.a_pose(), height=HEIGHT, facing_deg=FACING_DEG)[0][1])
    # Hung FLAT behind the shoulders rather than wrapped: a cape encircles
    # nothing, and wrapping it put the hem round the front where the wind
    # then pinned it. Rotated so it hangs behind the +X-facing figure.
    garment = build_garment(
        pattern,
        {
            "CAPE": Placement(
                flat=True,
                top_y_m=shoulder_y,
                rotation=np.asarray([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]),
                origin_m=np.array([-0.14, 0.0, 0.0]),
            )
        },
        particle_distance=float(opts["particle_mm"]),
    )
    clasp = top_edge(garment)
    log(
        f"cape: {garment.n_points} particles, {garment.triangles.shape[0]} triangles, "
        f"{len(clasp)} at the clasp" + ("  [PROBE - not evidence]" if probe else "")
    )

    frames = round(seconds * fps)
    manifest: dict[str, Any] = {
        "example": "cape_shot",
        "probe": bool(probe),
        "fps": fps,
        "frames": frames,
        "height_m": HEIGHT,
        "facing_deg": FACING_DEG,
        "settings": opts,
        "set": {"box_a": BOX_A, "box_b": BOX_B, "mat": MAT, "pool": POOL, "water_y": WATER_Y},
        "shots": [],
    }
    if probe:
        manifest["note"] = (
            "a probe proves the pipeline runs; what it measures is not evidence "
            "- never rely on a coarse preview"
        )

    cloth_frames = max(round((1.0 / fps) / (1.0 / 60.0)), 1)
    prepared, current_fabric, velocity, soaked = None, DRY, None, None
    cape_wet = np.zeros(garment.n_points)
    body_wet_prev = None
    clock = Stopwatch()
    for i in range(frames):
        t = i / fps
        offset, pose, is_wet, squash = trajectory(t)
        room = wind_at(t)

        # Two copies on purpose: the SOLVER needs the body where it is, and
        # the FILE is written body-local so the renderer can paint the boots
        # from object-space height.
        local = hero(pose)
        ground = support(t, squash)
        if ground is not None:
            offset = offset.copy()
            offset[1] = ground - float(local.bounds[0][1])
        placed = local.copy()
        placed.apply_translation(offset)
        field = sdf_from_mesh(placed, voxel_mm=float(opts["voxel_mm"]))

        if is_wet and soaked is None:
            soaked = wet(DRY)
            log(f"  [{t:.2f}s] entered the water: fabric -> {soaked}")
        fabric = soaked if (is_wet and soaked) else DRY

        settings = DrapeSettings(
            frames=cloth_frames, substeps=int(opts["substeps"]), environment=room
        )
        if prepared is None or fabric != current_fabric:
            prepared = prepare(garment, fabric=fabric, settings=settings)
            current_fabric, velocity = fabric, None

        pins = np.zeros(garment.n_points)
        pins[clasp] = 1.0
        target = garment.points.copy()
        target[clasp] = clasp_targets(garment, clasp, pose, offset)
        if i == 0:
            # Start the cape AT the clasp and let it settle before the shot
            # starts, or the first second is cloth that has not finished
            # being cloth yet.
            garment.points = (
                garment.points - garment.points[clasp].mean(axis=0) + target[clasp].mean(axis=0)
            )
            calm = Environment(name="settle")
            warm = DrapeSettings(
                frames=int(opts["settle"]), substeps=int(opts["substeps"]), environment=calm
            )
            settle = drape(
                garment,
                field,
                fabric=fabric,
                settings=warm,
                pins=pins,
                pin_target=target,
                prepared=prepare(garment, fabric=fabric, settings=warm),
            )
            garment.points = settle.points
            drop = float(settle.points[:, 1].max() - settle.points[:, 1].min())
            log(
                f"  cape settled: {drop * 1000:.0f} mm of drop "
                f"(the pattern is {pattern.panel('CAPE').bbox[3]:.0f} mm long)"
            )

        result = drape(
            garment,
            field,
            fabric=fabric,
            settings=settings,
            pins=pins,
            pin_target=target,
            prepared=prepared,
            velocity=velocity,
        )
        velocity = result.velocity
        garment.points = result.points

        # under the surface -> soaked; above it -> drying slowly
        under = result.points[:, 1] < WATER_Y
        cape_wet = np.maximum(cape_wet * 0.994, under.astype(np.float64))
        np.save(out / "cape" / f"{i:04d}.npy", result.points.astype(np.float32))
        np.save(out / "cape" / f"wet_{i:04d}.npy", cape_wet.astype(np.float32))

        # the hero's wetness rides in the vertex colour ALPHA, on top of the
        # figure's part tag in red
        colours = np.asarray(local.visual.vertex_colors).copy()
        world_y = local.vertices[:, 1] + offset[1]
        soak = np.clip((WATER_Y + 0.09 - world_y) / 0.18, 0.0, 1.0)
        body_wet = np.maximum(body_wet_prev, soak) if body_wet_prev is not None else soak
        colours[:, 3] = (body_wet * 255).astype(np.uint8)
        local.visual.vertex_colors = colours
        local.export(out / "body" / f"{i:04d}.ply")
        manifest["shots"].append(
            {
                "frame": i,
                "t": round(t, 3),
                "offset": [round(float(v), 4) for v in offset],
                "wet": bool(is_wet),
                "fabric": fabric,
                "mat_squash": round(float(squash), 4),
                "grounded": ground is not None,
                "cape_wet": round(float(cape_wet.mean()), 4),
                "body_wet": round(float(body_wet.mean()), 4),
                "wind_ms": round(float(np.linalg.norm(room.wind)), 2),
            }
        )
        body_wet_prev = body_wet
        if i % max(fps, 1) == 0:
            log(
                f"  frame {i:3d}/{frames}  t={t:.2f}s  {fabric:18s} "
                f"wind {np.linalg.norm(room.wind):4.1f} m/s  {clock.s:5.1f}s"
            )

    np.save(out / "cape_topology.npy", garment.triangles)
    np.save(out / "cape_uv.npy", garment.rest_points_mm)
    manifest["seconds"] = round(clock.s, 1)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    log(f"done: {frames} frames in {clock.s:.1f}s -> {out}")
    return manifest
