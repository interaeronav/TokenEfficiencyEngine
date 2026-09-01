"""Avatars: a body that can be POSED, a body you bring yourself, and gait.

The blend-shape lane in `animation.py` changes a body's SHAPE. This changes
its POSE, which is a different problem and the one a garment cares about most:
a t-shirt over a walk cycle is thrown up and down by the pelvis and dragged
across the shoulders by the arm swing, and none of that happens when only the
phenotype sliders move.

Three things live here.

`posed_mannequin` builds the stand-in body from JOINT ANGLES, out of the same
capsules `mannequin` always used. It is NOT the same body: a jointed leg is
two capsules with a knee between them where the A-pose mannequin's is one, and
the extra hemisphere at the joint makes the jointed body 1.811 m tall against
1.792 m. `mannequin()` is left exactly as it was rather than delegating here,
because every measured number in this project's tests belongs to the body that
produced it, and quietly swapping the body under them would invalidate the lot
while every test still passed.

`gait` writes a walk or a run as a pose track. The angles are the standard
clinical gait-analysis ranges, and they are labelled as such: textbook
kinematics for level walking and running, not something measured here. What
they buy is that the body moves the way a body moves - the pelvis RISES AND
FALLS (about 50 mm peak-to-peak in a walk, about 140 mm in a run), the arms
swing counter-phase to the legs, and the trunk leans further forward the
faster you go. A gait that forgets the vertical displacement produces a
garment that never gets thrown, which looks like a stiff fabric and is not.

`custom_avatar` takes a body the studio already has - any mesh trimesh can
read - and checks it before letting it into the solver, because the failure
mode for a wrongly-scaled avatar is a garment that appears to fit a doll.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np

# Sagittal-plane joints, degrees. Positive is FLEXION (the limb swings
# forward), which is the clinical sign convention and the opposite of what
# looks natural in a 3D package - worth saying once here rather than being
# wrong about it in four places.
JOINTS = (
    "hip_l",
    "hip_r",
    "knee_l",
    "knee_r",
    "shoulder_l",
    "shoulder_r",
    "elbow_l",
    "elbow_r",
    "trunk_lean",
)


@dataclass(slots=True)
class Pose:
    """One instant of a body. Angles in degrees, rise in metres."""

    hip_l: float = 0.0
    hip_r: float = 0.0
    knee_l: float = 0.0
    knee_r: float = 0.0
    shoulder_l: float = 0.0
    shoulder_r: float = 0.0
    elbow_l: float = 0.0
    elbow_r: float = 0.0
    trunk_lean: float = 0.0
    rise_m: float = 0.0  # pelvis height above its standing position

    @classmethod
    def a_pose(cls) -> Pose:
        """Arms down and out at 35 degrees - what a garment is draped over.

        Abduction, not flexion, so it is not in `JOINTS`: the A-pose's arms go
        out to the SIDE, and `posed_mannequin` applies that separately.
        """
        return cls()

    @classmethod
    def from_values(cls, values: dict[str, float]) -> Pose:
        unknown = set(values) - set(JOINTS) - {"rise_m"}
        if unknown:
            raise ValueError(
                f"unknown joint(s) {sorted(unknown)}; joints: {', '.join(JOINTS)} (plus rise_m)."
            )
        return cls(**{k: float(v) for k, v in values.items()})

    def as_values(self) -> dict[str, float]:
        return {name: float(getattr(self, name)) for name in (*JOINTS, "rise_m")}


def _v(*xyz: float) -> np.ndarray:
    """An explicit vector. `array + [a, b, c]` is vector addition here, not
    list concatenation, and spelling it out stops both a reader and a linter
    reading it the other way."""
    return np.asarray(xyz, dtype=np.float64)


def _swing(origin: np.ndarray, length: float, degrees: float, abduct: float = 0.0) -> np.ndarray:
    """Where a limb segment ends, hanging DOWN from `origin` then rotated.

    Sagittal rotation is about X, in seamkiln's Y-up world with +Z forward.
    `abduct` swings it out sideways as well, which is what an A-pose is.
    """
    a, b = math.radians(degrees), math.radians(abduct)
    direction = np.asarray(
        [math.sin(b), -math.cos(a) * math.cos(b), math.sin(a) * math.cos(b)], dtype=np.float64
    )
    return origin + direction * length


def posed_mannequin(
    pose: Pose | None = None,
    *,
    height: float = 1.75,
    chest: float = 1.00,
    arm_abduction: float = 35.0,
) -> Any:
    """The stand-in body, at a pose. Metres, Y up, +Z forward.

    Same capsules and the same proportions the A-pose mannequin always had -
    including the two that were learned the hard way and are commented where
    they are built: the shoulder ledge a t-shirt hangs off, and hips wider
    than the chest for it to catch on.
    """
    import trimesh

    from seamkiln.drape.body import _capsule_between

    pose = pose or Pose.a_pose()
    torso_r = chest / (2 * np.pi)
    rise = pose.rise_m
    shoulder_y = height * 0.82 + rise
    hip_y = height * 0.53 + rise
    pelvis_y = height * 0.48 + rise
    shoulder_half = max(torso_r * 1.28, height * 0.112)

    # The trunk leans forward about the hips, so the shoulders travel with it.
    lean = math.radians(pose.trunk_lean)
    spine = shoulder_y - hip_y
    shoulder_z = math.sin(lean) * spine
    shoulder_y = hip_y + math.cos(lean) * spine
    top = np.asarray([0.0, shoulder_y, shoulder_z])

    parts = [
        # the shoulder LEDGE - a plain capsule torso is a smooth dome with
        # nothing to catch on, and the drape slid off it onto the floor
        _capsule_between(
            top + _v(-shoulder_half, 0.0, 0.0), top + _v(shoulder_half, 0.0, 0.0), torso_r * 0.62
        ),
        _capsule_between([0, hip_y, 0], top, torso_r),  # torso
        # hips WIDER than the chest, which is what the garment catches on
        _capsule_between([0, pelvis_y, 0], [0, hip_y, 0], torso_r * 1.06),
        _capsule_between(top, top + _v(0.0, height * 0.05, 0.0), torso_r * 0.34),  # neck
        trimesh.creation.icosphere(subdivisions=2, radius=height * 0.066).apply_translation(
            top + _v(0.0, height * 0.11, 0.0)
        ),
    ]

    upper_arm, forearm = height * 0.19, height * 0.23
    thigh, shank = height * 0.245, height * 0.245
    for side, tag in ((-1.0, "l"), (1.0, "r")):
        shoulder = top + np.asarray([side * shoulder_half, -height * 0.015, 0.0])
        elbow = _swing(
            shoulder, upper_arm, getattr(pose, f"shoulder_{tag}"), abduct=side * arm_abduction
        )
        # The elbow only ever bends one way, and it bends BACKWARD relative to
        # the upper arm's direction - which is why its angle is subtracted
        # from the shoulder's rather than added to it.
        hand = _swing(
            elbow,
            forearm,
            getattr(pose, f"shoulder_{tag}") - getattr(pose, f"elbow_{tag}"),
            abduct=side * arm_abduction * 0.4,
        )
        parts.append(_capsule_between(shoulder, elbow, torso_r * 0.30))
        parts.append(_capsule_between(elbow, hand, torso_r * 0.26))

        hip = np.asarray([side * torso_r * 0.45, pelvis_y, 0.0])
        knee = _swing(hip, thigh, getattr(pose, f"hip_{tag}"))
        foot = _swing(knee, shank, getattr(pose, f"hip_{tag}") - getattr(pose, f"knee_{tag}"))
        parts.append(_capsule_between(hip, knee, torso_r * 0.42))
        parts.append(_capsule_between(knee, foot, torso_r * 0.32))

    body = trimesh.util.concatenate(parts)
    body.merge_vertices()
    return body


# -- gait ----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Gait:
    """One locomotion pattern, as the ranges a gait lab would quote.

    Every number is textbook clinical kinematics for level ground - the peaks
    of the standard hip, knee and shoulder curves - NOT something measured by
    this project, and `tier` says so the way a fabric card does.
    """

    name: str
    cycle_s: float  # one full stride, both feet
    speed_ms: float
    hip_flex: float  # peak forward swing, degrees
    hip_ext: float  # peak backward, degrees (negative flexion)
    knee_swing: float  # peak knee bend in swing, degrees
    knee_stance: float  # the small stance-phase bend
    shoulder_swing: float  # arm swing amplitude, degrees
    elbow_hold: float  # how bent the elbow is held
    trunk_lean: float
    rise_mm: float  # pelvis vertical travel, peak to peak
    source: str = "standard clinical gait-analysis ranges for level locomotion"


GAITS: dict[str, Gait] = {
    "walk": Gait(
        name="walk",
        cycle_s=1.05,
        speed_ms=1.35,
        hip_flex=30.0,
        hip_ext=-10.0,
        knee_swing=60.0,
        knee_stance=18.0,
        shoulder_swing=20.0,
        elbow_hold=20.0,
        trunk_lean=2.0,
        rise_mm=50.0,
    ),
    "run": Gait(
        name="run",
        cycle_s=0.70,
        speed_ms=3.50,
        hip_flex=45.0,
        hip_ext=-20.0,
        knee_swing=125.0,
        knee_stance=35.0,
        shoulder_swing=45.0,
        elbow_hold=85.0,
        trunk_lean=8.0,
        rise_mm=140.0,
    ),
    "stand": Gait(
        name="stand",
        cycle_s=1.0,
        speed_ms=0.0,
        hip_flex=0.0,
        hip_ext=0.0,
        knee_swing=0.0,
        knee_stance=0.0,
        shoulder_swing=0.0,
        elbow_hold=0.0,
        trunk_lean=0.0,
        rise_mm=0.0,
    ),
}


@dataclass(slots=True)
class PoseTrack:
    """A pose per instant. The same shape as a BlendTrack, different channels.

    Kept separate rather than folded into BlendTrack because BlendTrack
    validates its channels against the phenotype list, and that validation is
    there to catch typos - loosening it to admit joint names would cost more
    than the duplication saves.
    """

    times: list[float] = field(default_factory=list)
    poses: list[Pose] = field(default_factory=list)
    gait: str = "stand"
    meta: dict[str, Any] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.poses)

    @property
    def duration(self) -> float:
        return (self.times[-1] - self.times[0]) if self.times else 0.0

    def sample(self, fps: float = 12.0) -> list[tuple[float, dict[str, float]]]:
        if not self.poses:
            return []
        count = max(round(self.duration * fps) + 1, 1)
        want = np.linspace(self.times[0], self.times[-1], count)
        have = np.asarray(self.times)
        out: list[tuple[float, dict[str, float]]] = []
        for t in want:
            values = {
                channel: float(np.interp(t, have, [getattr(p, channel) for p in self.poses]))
                for channel in (*JOINTS, "rise_m")
            }
            out.append((float(t), values))
        return out

    def as_dict(self) -> dict[str, Any]:
        return {
            "gait": self.gait,
            "duration_s": round(self.duration, 3),
            "poses": len(self.poses),
            "channels": [*JOINTS, "rise_m"],
            **self.meta,
        }


def gait(kind: str = "walk", *, cycles: float = 1.0, samples_per_cycle: int = 16) -> PoseTrack:
    """A walk or a run, as a pose track.

    The left and right sides are half a cycle out of phase and the arms are
    counter-phase to the legs on the same side - which is the thing everyone
    animating a walk by hand gets wrong first, and the thing a garment
    notices, because counter-rotation is what twists a shirt across the back.
    """
    if kind not in GAITS:
        raise ValueError(f"unknown gait {kind!r}. Known: {', '.join(sorted(GAITS))}")
    spec = GAITS[kind]
    count = max(round(samples_per_cycle * cycles), 2)
    times, poses = [], []
    for i in range(count + 1):
        phase = (i / samples_per_cycle) % 1.0
        times.append(spec.cycle_s * i / samples_per_cycle)
        poses.append(_pose_at(spec, phase))
    return PoseTrack(
        times=times,
        poses=poses,
        gait=kind,
        meta={
            "speed_ms": spec.speed_ms,
            "cycle_s": spec.cycle_s,
            "distance_m": round(spec.speed_ms * spec.cycle_s * cycles, 3),
            "rise_mm": spec.rise_mm,
            "source": spec.source,
        },
    )


def _pose_at(spec: Gait, phase: float) -> Pose:
    def hip(p: float) -> float:
        mid = 0.5 * (spec.hip_flex + spec.hip_ext)
        amp = 0.5 * (spec.hip_flex - spec.hip_ext)
        return mid + amp * math.cos(2 * math.pi * p)

    def knee(p: float) -> float:
        # Two humps per stride, and they are not the same size: a small one in
        # loading response and the big one in swing. One sine would give a
        # symmetric bend, which is a gait nobody has.
        swing = spec.knee_swing * max(math.sin(2 * math.pi * (p - 0.45)), 0.0) ** 1.5
        stance = spec.knee_stance * max(math.sin(2 * math.pi * (p + 0.1)), 0.0) ** 2
        return swing + stance

    # The pelvis rises TWICE per stride - once over each stance leg - which is
    # why this is 4*pi and not 2*pi, and why a walk bounces at double the
    # stride frequency.
    rise = 0.5 * (spec.rise_mm / 1000.0) * math.cos(4 * math.pi * phase)
    other = (phase + 0.5) % 1.0
    return Pose(
        hip_r=hip(phase),
        hip_l=hip(other),
        knee_r=knee(phase),
        knee_l=knee(other),
        # arms counter-phase to the leg on the SAME side
        shoulder_r=-spec.shoulder_swing * math.cos(2 * math.pi * phase),
        shoulder_l=-spec.shoulder_swing * math.cos(2 * math.pi * other),
        elbow_r=spec.elbow_hold,
        elbow_l=spec.elbow_hold,
        trunk_lean=spec.trunk_lean,
        rise_m=rise,
    )


def walk(
    garment,
    track: PoseTrack,
    *,
    fabric: str = "cotton_jersey",
    fps: float = 8.0,
    frames_per_step: int | None = None,
    voxel_mm: float = 12.0,
    height: float = 1.75,
    chest: float = 1.00,
    body_factory=None,
    settings=None,
) -> list[Any]:
    """Drape along a pose track, carrying the cloth forward frame to frame.

    Reuses the blend-shape animator, because "solve, carry the points forward,
    solve again" is the same job whether the body changed shape or moved. The
    only difference is which body_factory is handed in.
    """
    from seamkiln.animation import (
        AnimationFrame,  # noqa: F401  (documents the return type)
        animate,
    )

    if body_factory is None:

        def body_factory(values: dict[str, float]):
            return posed_mannequin(Pose.from_values(values), height=height, chest=chest)

    return animate(
        garment,
        _as_blend_track(track),
        fabric=fabric,
        fps=fps,
        frames_per_step=frames_per_step,
        voxel_mm=voxel_mm,
        body_factory=body_factory,
        settings=settings,
    )


class _PoseAsTrack:
    """Adapter: makes a PoseTrack quack like a BlendTrack for `animate`."""

    def __init__(self, track: PoseTrack):
        self._track = track
        self.keys = track.poses  # animate() only checks this for emptiness

    def sample(self, fps: float = 12.0):
        return self._track.sample(fps)


def _as_blend_track(track: PoseTrack) -> Any:
    return _PoseAsTrack(track)


# -- bring your own body -------------------------------------------------------

# What a human body is, in metres. Outside these, something is wrong with the
# file rather than with the person - the shortest and tallest adults ever
# recorded are 0.55 m and 2.72 m, so this is generous on purpose.
PLAUSIBLE_HEIGHT_M = (0.5, 2.8)


def custom_avatar(
    path: str | Path,
    *,
    units: str = "auto",
    up: str = "auto",
    forward_z: bool = True,
) -> Any:
    """Load a studio's own avatar, and CHECK it before the solver sees it.

    The failure mode this is built against is silent: an avatar exported in
    centimetres arrives 100x too big, the garment is a postage stamp on it,
    every seam closes perfectly, and the fit report is full of confident
    numbers about a garment that would fit a doll. So the units are inferred
    from the mesh's own height and the inference is REPORTED, never assumed.
    """
    import trimesh

    mesh = trimesh.load(str(path), force="mesh")
    if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
        raise ValueError(f"{path} does not contain a mesh")
    mesh = mesh.copy()

    notes: list[str] = []
    if up == "auto":
        extents = np.asarray(mesh.extents, dtype=np.float64)
        axis = int(np.argmax(extents))
        # A body is clearly taller than it is wide. Something with no
        # meaningfully longest axis - a sphere, a cube - is not lying down, it
        # is just not a body, and the height check below is the honest place
        # to say so. Guessing "lying down" here sent that refusal to the wrong
        # reason entirely.
        if extents[axis] < 1.2 * float(np.median(extents)):
            up = "Y"
            notes.append(
                f"no clearly longest axis in {np.round(extents, 3).tolist()}; assuming Y-up"
            )
        else:
            up = "XYZ"[axis]
            notes.append(
                f"up axis inferred as {up} (the tallest of {np.round(extents, 3).tolist()})"
            )
    if up == "Z":
        mesh.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 2, [1.0, 0.0, 0.0]))
        notes.append("rotated Z-up to seamkiln's Y-up")
    elif up == "X":
        raise ValueError(
            "this mesh is widest along X, so it is probably lying down rather than "
            "X-up. Rotate it upright before importing, or pass up='Y'/'Z' explicitly."
        )

    span = float(mesh.extents[1])
    if units == "auto":
        scale, units = _infer_units(span)
        if scale != 1.0:
            notes.append(f"scaled by {scale:g}: {span:.3g} reads as {units}, not metres")
    else:
        scale = {"m": 1.0, "cm": 0.01, "mm": 0.001, "in": 0.0254}.get(units, 0.0)
        if scale == 0.0:
            raise ValueError(f"unknown units {units!r}. Known: m, cm, mm, in, auto.")
    if scale != 1.0:
        mesh.apply_scale(scale)

    height = float(mesh.extents[1])
    low, high = PLAUSIBLE_HEIGHT_M
    if not low <= height <= high:
        raise ValueError(
            f"this avatar is {height:.3g} m tall, which is not a body. Either the "
            f"units are wrong (pass units='cm'/'mm') or the file is not an avatar. "
            f"Refusing rather than draping a garment onto it, because a wrongly "
            f"scaled avatar produces a perfect-looking fit report about nothing."
        )
    # stand it on the floor at the origin, which is where every body here is
    mesh.apply_translation([-mesh.centroid[0], -mesh.bounds[0][1], -mesh.centroid[2]])
    if not forward_z:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [0.0, 1.0, 0.0]))
        notes.append("turned 180 degrees so +Z is forward")

    mesh.metadata["seamkiln_avatar"] = {
        "path": str(path),
        "height_m": round(height, 4),
        "units_in": units,
        "notes": notes,
    }
    return mesh


def _infer_units(span_m: float) -> tuple[float, str]:
    """A body is about 1.7 of something. Which something is a size question."""
    for scale, name in ((1.0, "m"), (0.01, "cm"), (0.001, "mm"), (0.0254, "in")):
        if PLAUSIBLE_HEIGHT_M[0] <= span_m * scale <= PLAUSIBLE_HEIGHT_M[1]:
            return scale, name
    return 1.0, "m"


def describe(mesh: Any) -> dict[str, Any]:
    """What an imported avatar is, measured - not what the file claimed."""
    from seamkiln.drape.garment import body_landmarks

    info = dict(mesh.metadata.get("seamkiln_avatar") or {})
    try:
        marks = body_landmarks(mesh)
    except (ValueError, IndexError) as exc:  # a mesh that is not body-shaped
        return {**info, "measured": None, "why": str(exc)}
    return {
        **info,
        "height_mm": round(float(mesh.extents[1]) * 1000.0, 1),
        "watertight": bool(mesh.is_watertight),
        "triangles": len(mesh.faces),
        "landmarks": marks.get("landmarks", {}),
    }


def adjust(mesh: Any, *, height_m: float | None = None, girth_scale: float = 1.0) -> Any:
    """Adjust an imported avatar's anatomy: stature and girth, separately.

    Separately, because they are separate on a body. Scaling a whole avatar to
    change its height also changes every circumference, which turns a taller
    person into a bigger one - and the garment that then fits is not the
    garment that fits the taller person.
    """
    out = mesh.copy()
    if height_m is not None:
        current = float(out.extents[1])
        if current <= 0.0:
            raise ValueError("this mesh has no height to adjust")
        out.apply_transform(np.diag([1.0, height_m / current, 1.0, 1.0]))
    if girth_scale != 1.0:
        out.apply_transform(np.diag([girth_scale, 1.0, girth_scale, 1.0]))
    out.apply_translation([-out.centroid[0], -out.bounds[0][1], -out.centroid[2]])
    out.metadata["seamkiln_avatar"] = {
        **(mesh.metadata.get("seamkiln_avatar") or {}),
        "adjusted": {"height_m": height_m, "girth_scale": girth_scale},
    }
    return out


__all__ = [
    "GAITS",
    "JOINTS",
    "Gait",
    "Pose",
    "PoseTrack",
    "adjust",
    "custom_avatar",
    "describe",
    "gait",
    "posed_mannequin",
    "replace",
    "walk",
]
