"""A figure that can be dressed: heroic proportions, but human ones.

The capsule mannequin in `drape.body` is a COLLIDER - it exists so a garment
has something to land on, and it looks like what it is. This is a figure: a
silhouette with shoulders, a waist narrower than the ribcage, boots, gloves
and a cowl, built from truncated cones with a sphere at every joint so limbs
taper and joints stay round when they bend. Every dimension is a fraction of
stature, so the whole figure scales from one number.

Two things it learned the hard way, both worth keeping in view:

* **The SAME mesh is the collider and the render mesh.** A pretty version for
  the camera and a crude one for the solver is how a cape ends up passing
  through a chest the physics never knew about.
* **It has to be CLOTHABLE.** The first cut was heroic to the point of
  impossibility - an upper arm 194 mm across on a 1.8 m body, where a real
  one is about 100 - and no sleeve drafted to a matching armhole could ever
  have gone round it. The sleeves flapped beside bare arms, which looked like
  a cloth-solver failure and was an anatomy failure. An unclothable body reads
  as a broken solver.

The figure is built facing +Z, which is the plane its joints swing in and the
direction seamkiln's cylinder arrangement calls "front" (centre angle 0).
Turn it with `facing_deg` if a shot needs it to travel elsewhere - and turn
the cape clasps with it, which is what `clasp_points` does.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import trimesh

# Part tags, so a renderer can give each its own material without UVs on a
# body that has none. They travel in the RED channel of the vertex colours
# (byte = tag * 40 + 20) and alpha is left free for wetness, because Blender's
# PLY importer runs colour channels through sRGB->linear but leaves alpha
# exactly as written - checked, not assumed.
PARTS = ("suit", "skin", "boot", "glove", "belt", "emblem")
SUIT, SKIN, BOOT, GLOVE, BELT, EMBLEM = range(6)

JOINT_NAMES = (
    "pelvis",
    "waist",
    "chest",
    "neck",
    "head",
    "shoulder_l",
    "shoulder_r",
    "elbow_l",
    "elbow_r",
    "hand_l",
    "hand_r",
    "hip_l",
    "hip_r",
    "knee_l",
    "knee_r",
    "foot_l",
    "foot_r",
)


def _frustum(a, b, ra: float, rb: float, sections: int = 40) -> trimesh.Trimesh | None:
    """A truncated cone from `a` to `b`, capped so it stays watertight."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    axis = b - a
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return None
    theta = np.linspace(0.0, 2.0 * np.pi, sections, endpoint=False)
    ring = np.stack([np.cos(theta), np.sin(theta)], axis=1)
    bottom = np.hstack([ring * ra, np.zeros((sections, 1))])
    top = np.hstack([ring * rb, np.full((sections, 1), length)])
    verts = np.vstack([bottom, top, [[0.0, 0.0, 0.0], [0.0, 0.0, length]]])
    low, high = 2 * sections, 2 * sections + 1
    faces = []
    for i in range(sections):
        j = (i + 1) % sections
        faces.append([i, j, sections + j])
        faces.append([i, sections + j, sections + i])
        faces.append([low, j, i])
        faces.append([high, sections + i, sections + j])
    mesh = trimesh.Trimesh(vertices=verts, faces=np.asarray(faces), process=False)
    z = np.asarray([0.0, 0.0, 1.0])
    direction = axis / length
    if np.allclose(direction, -z):
        rotation = trimesh.transformations.rotation_matrix(np.pi, [1.0, 0.0, 0.0])
    else:
        rotation = trimesh.geometry.align_vectors(z, direction)
    mesh.apply_transform(rotation)
    mesh.apply_translation(a)
    return mesh


def _ball(centre, radius: float, squash=(1.0, 1.0, 1.0), subdivisions: int = 2):
    s = trimesh.creation.icosphere(subdivisions=subdivisions, radius=radius)
    s.apply_transform(np.diag([*squash, 1.0]))
    s.apply_translation(centre)
    return s


def _swing(origin, length: float, degrees: float, abduct: float = 0.0) -> np.ndarray:
    """Where a limb segment ends: hanging down, then rotated. Y up, +Z front.

    Positive is FLEXION - the limb swings forward - which is the clinical
    sign convention and the opposite of what looks natural in a 3D package.
    """
    a, b = math.radians(degrees), math.radians(abduct)
    d = np.asarray([math.sin(b), -math.cos(a) * math.cos(b), math.sin(a) * math.cos(b)])
    return np.asarray(origin, dtype=np.float64) + d * length


def _yaw(degrees: float) -> np.ndarray:
    a = math.radians(degrees)
    return np.asarray(
        [[math.cos(a), 0.0, math.sin(a)], [0.0, 1.0, 0.0], [-math.sin(a), 0.0, math.cos(a)]]
    )


def joints(pose: Any, *, height: float = 1.80, arm_abduction: float = 32.0) -> dict[str, Any]:
    """Every joint the figure hangs off, in metres. Y up, +Z forward, unturned.

    `pose` is a `seamkiln.avatar.Pose` (or anything with its attributes).
    """
    H = height
    rise = float(getattr(pose, "rise_m", 0.0))
    lean = math.radians(float(getattr(pose, "trunk_lean", 0.0)))

    pelvis = np.asarray([0.0, H * 0.480 + rise, 0.0])
    waist = pelvis + np.asarray([0.0, H * 0.115, 0.0])
    spine = H * 0.195
    # 0.68 of the way up, not 0.55: lower, the widest point of the torso sat
    # at the bottom of the ribcage and the chest read as a bowl.
    chest = waist + np.asarray([0.0, math.cos(lean) * spine * 0.68, math.sin(lean) * spine * 0.68])
    neck = waist + np.asarray([0.0, math.cos(lean) * spine, math.sin(lean) * spine])
    head = neck + np.asarray([0.0, math.cos(lean) * H * 0.085, math.sin(lean) * H * 0.085])

    half = H * 0.135
    out: dict[str, Any] = {
        "pelvis": pelvis,
        "waist": waist,
        "chest": chest,
        "neck": neck,
        "head": head,
        "shoulder_half": half,
        "height": H,
        "lean": lean,
    }
    upper, fore = H * 0.170, H * 0.155
    thigh, calf = H * 0.245, H * 0.230
    for side, tag in ((-1.0, "l"), (1.0, "r")):
        shoulder = neck + np.asarray([side * half, -H * 0.012, 0.0])
        swing = float(getattr(pose, f"shoulder_{tag}", 0.0))
        bend = float(getattr(pose, f"elbow_{tag}", 0.0))
        elbow = _swing(shoulder, upper, swing, abduct=side * arm_abduction)
        hand = _swing(elbow, fore, swing - bend, abduct=side * arm_abduction * 0.35)
        hip = pelvis + np.asarray([side * H * 0.055, 0.0, 0.0])
        flex = float(getattr(pose, f"hip_{tag}", 0.0))
        knee_bend = float(getattr(pose, f"knee_{tag}", 0.0))
        knee = _swing(hip, thigh, flex)
        foot = _swing(knee, calf, flex - knee_bend)
        out.update(
            {
                f"shoulder_{tag}": shoulder,
                f"elbow_{tag}": elbow,
                f"hand_{tag}": hand,
                f"hip_{tag}": hip,
                f"knee_{tag}": knee,
                f"foot_{tag}": foot,
            }
        )
    return out


def figure(
    pose: Any,
    *,
    height: float = 1.80,
    arm_abduction: float = 32.0,
    facing_deg: float = 0.0,
) -> trimesh.Trimesh:
    """The figure, as one watertight mesh with a per-face part tag.

    The proportions are a garment's numbers, not a comic's: a 0.034H upper arm
    is 122 mm across on a 1.8 m body, a 0.106H chest is a 1.2 m girth. The
    joints and part tags ride in `mesh.metadata`.
    """
    H = height
    j = joints(pose, height=H, arm_abduction=arm_abduction)
    parts: list[tuple[trimesh.Trimesh, int]] = []

    def add(mesh, tag):
        if mesh is not None and len(mesh.faces):
            parts.append((mesh, tag))

    chest_r, waist_r, pelvis_r = H * 0.106, H * 0.068, H * 0.086
    add(_frustum(j["waist"], j["chest"], waist_r, chest_r), SUIT)
    add(_frustum(j["chest"], j["neck"], chest_r, chest_r * 0.88), SUIT)
    add(_ball(j["chest"], chest_r, squash=(1.0, 0.42, 0.86)), SUIT)
    add(_frustum(j["pelvis"], j["waist"], pelvis_r, waist_r), SUIT)
    add(_ball(j["pelvis"], pelvis_r, squash=(1.0, 0.62, 0.80)), SUIT)
    for tag in ("l", "r"):
        add(_ball(j[f"shoulder_{tag}"], H * 0.040, squash=(1.24, 0.94, 1.0)), SUIT)

    belt = j["waist"] + np.asarray([0.0, -H * 0.014, 0.0])
    add(
        _frustum(belt, belt + np.asarray([0.0, H * 0.032, 0.0]), waist_r * 1.12, waist_r * 1.12),
        BELT,
    )

    up = j["neck"] - j["waist"]
    up = up / max(float(np.linalg.norm(up)), 1e-9)
    front = np.asarray([0.0, -up[2], up[1]])
    badge = j["waist"] + up * (H * 0.118) + front * chest_r
    add(_ball(badge, H * 0.031, squash=(1.20, 1.35, 0.22)), EMBLEM)

    head_r = H * 0.072
    add(_frustum(j["neck"], j["head"], H * 0.046, H * 0.044), SKIN)
    crown = j["head"] + up * (head_r * 0.72)
    add(_ball(crown, head_r, squash=(0.94, 1.10, 1.02), subdivisions=3), SKIN)
    add(
        _ball(
            crown + up * (head_r * 0.10) - front * (head_r * 0.16),
            head_r * 1.02,
            squash=(1.02, 1.06, 0.98),
            subdivisions=3,
        ),
        SUIT,
    )

    upper_r, fore_r = H * 0.034, H * 0.028
    thigh_r, calf_r = H * 0.056, H * 0.040
    for tag in ("l", "r"):
        s_, e, h = j[f"shoulder_{tag}"], j[f"elbow_{tag}"], j[f"hand_{tag}"]
        # radii MATCH at every shared joint, or the limb reads as stacked tins
        elbow_r = upper_r * 0.78
        add(_frustum(s_, e, upper_r, elbow_r), SUIT)
        add(_ball(e, elbow_r), SUIT)
        wrist = e + (h - e) * 0.74
        wrist_r = fore_r * 0.86
        add(_frustum(e, wrist, elbow_r, wrist_r), SUIT)
        add(_frustum(wrist, h, wrist_r * 1.16, wrist_r * 1.02), GLOVE)
        add(_ball(h, wrist_r * 1.08, squash=(1.0, 1.12, 0.88)), GLOVE)

        hip, knee, foot = j[f"hip_{tag}"], j[f"knee_{tag}"], j[f"foot_{tag}"]
        knee_r = thigh_r * 0.64
        add(_frustum(hip, knee, thigh_r, knee_r), SUIT)
        add(_ball(knee, knee_r), SUIT)
        ankle = knee + (foot - knee) * 0.70
        ankle_r = calf_r * 0.76
        add(_frustum(knee, ankle, knee_r, ankle_r), SUIT)
        add(_frustum(ankle, foot, ankle_r * 1.22, ankle_r * 1.14), BOOT)
        toe = foot + np.asarray([0.0, 0.0, H * 0.062])
        add(_ball(foot, ankle_r * 1.16, squash=(1.0, 0.78, 1.0)), BOOT)
        add(_frustum(foot, toe, ankle_r * 1.12, ankle_r * 0.68), BOOT)

    body = trimesh.util.concatenate([m for m, _ in parts])
    per_face = np.concatenate([np.full(len(m.faces), t, dtype=np.int32) for m, t in parts])
    per_vertex = np.zeros(len(body.vertices), dtype=np.int32)
    offset = 0
    for mesh, tag in parts:
        per_vertex[offset : offset + len(mesh.vertices)] = tag
        offset += len(mesh.vertices)
    colours = np.zeros((len(body.vertices), 4), dtype=np.uint8)
    colours[:, 0] = (per_vertex * 40 + 20).astype(np.uint8)
    colours[:, 3] = 255
    body.visual.vertex_colors = colours
    if facing_deg:
        turn = np.eye(4)
        turn[:3, :3] = _yaw(facing_deg)
        body.apply_transform(turn)
    body.metadata["part_per_face"] = per_face
    body.metadata["part_per_vertex"] = per_vertex
    body.metadata["joints"] = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in j.items()
    }
    body.metadata["facing_deg"] = float(facing_deg)
    body.metadata["seamkiln_figure"] = {"height_m": height, "parts": list(PARTS)}
    return body


def clasp_points(
    pose: Any, *, height: float = 1.80, count: int = 2, facing_deg: float = 0.0
) -> np.ndarray:
    """Where a cape is fastened: the tops of both shoulders, at the back.

    A cape hangs off the SHOULDERS. Hung from one point at the neck it is a
    towel someone draped on - it needs two anchors far enough apart to hold
    the top edge open.
    """
    j = joints(pose, height=height)
    back = np.asarray([0.0, 0.0, -height * 0.055])
    lift = np.asarray([0.0, height * 0.030, 0.0])
    left = j["shoulder_l"] + back + lift
    right = j["shoulder_r"] + back + lift
    points = np.stack([left + (right - left) * (k / max(count - 1, 1)) for k in range(count)])
    return points @ _yaw(facing_deg).T if facing_deg else points


def standing_offset(mesh: trimesh.Trimesh, ground_y: float = 0.0) -> np.ndarray:
    """The translation that puts the figure's LOWEST point on the ground.

    A posed figure moves its own feet relative to its origin, so on the ground
    the origin is solved for rather than dictated - which is also where the
    vertical bob of a walk comes from: the pelvis rises because the stance leg
    straightens, not because anyone scripted a rise.
    """
    return np.asarray([0.0, ground_y - float(mesh.bounds[0][1]), 0.0])


__all__ = [
    "BELT",
    "BOOT",
    "EMBLEM",
    "GLOVE",
    "JOINT_NAMES",
    "PARTS",
    "SKIN",
    "SUIT",
    "clasp_points",
    "figure",
    "joints",
    "standing_offset",
]
