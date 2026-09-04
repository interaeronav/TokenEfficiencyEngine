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
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
import trimesh

# Part tags, so a renderer can give each its own material without UVs on a
# body that has none. They travel in the RED channel of the vertex colours
# (byte = tag * 40 + 20) and alpha is left free for wetness, because Blender's
# PLY importer runs colour channels through sRGB->linear but leaves alpha
# exactly as written - checked, not assumed.
PARTS = ("suit", "skin", "boot", "glove", "belt", "emblem")
# The torso's section: wider than deep, as a ribcage is (depth about 0.7 of
# width on a person). Built round, every part of the trunk was a body of
# revolution and NOTHING on the figure resisted a garment turning about it:
# measured on the walk, a zipped jacket yawed 15-20 degrees with every stride
# from the sleeves swinging on the arms, drifted 32 mm to one side in two
# seconds, and carried one shoulder over the crest of the deltoid. An
# elliptical trunk is what locks a jacket's yaw, on a person and here.
TORSO_SQUASH = (1.10, 0.78)  # x (width), z (depth) scale of the trunk parts
SUIT, SKIN, BOOT, GLOVE, BELT, EMBLEM = range(6)


@dataclass(frozen=True, slots=True)
class Build:
    """Every proportion of the figure as a fraction of stature (H).

    `MALE` is the figure as it has always been - its numbers are the ones
    every A65 measurement was made on and they stay bit-identical.
    `FEMALE` is derived from measured sex differences, dimension by
    dimension: the female/male ratio of the mean-relative-to-stature from
    ANSUR II (2012, US Army, 1,986 women and 4,082 men; public domain) is
    applied to the male figure's own value, so the stylisation stays and
    only what differs between the sexes moves. The source rows are quoted
    in `FEMALE`'s definition; anything not covered by a measured ratio is
    left at the male value and says so.
    """

    name: str
    # joints (fractions of H)
    pelvis_y: float = 0.480
    waist_rise: float = 0.115
    spine: float = 0.195
    head_rise: float = 0.085
    shoulder_half: float = 0.135
    shoulder_drop: float = 0.012
    hip_half: float = 0.055
    upper_arm: float = 0.170
    forearm: float = 0.155
    thigh: float = 0.245
    calf: float = 0.230
    # trunk radii and squash
    chest_r: float = 0.106
    waist_r: float = 0.068
    pelvis_r: float = 0.086
    torso_squash: tuple[float, float] = (1.10, 0.78)
    bust: float = 0.0  # a bust's forward relief as a fraction of chest_r; 0 = none
    # shoulders, neck, head
    deltoid_r: float = 0.040
    neck_r_top: float = 0.046
    neck_r_bottom: float = 0.044
    head_r: float = 0.072
    # limbs
    upper_arm_r: float = 0.034
    forearm_r: float = 0.028
    thigh_r: float = 0.056
    calf_r: float = 0.040
    # the arm's resting abduction, degrees
    arm_abduction: float = 32.0
    # the trapezius: how far the neck's base rises above the shoulder line,
    # as a fraction of H, with a slope from there down to each deltoid's
    # top. 0 is the flat trunk top the figure always had (its deltoids
    # stand 40 mm proud of it as bumps a sleeve cap has to climb); the
    # survey's cervicale minus acromial height, 0.0375 H on women, is the
    # drop a real shoulder line makes from the neck to the acromion.
    trapezius: float = 0.0
    # how each proportion scales with a change of chest girth at fixed
    # stature: log-log slopes on chest circumference, stature held, from
    # the survey (see ALLOMETRY). Missing fields scale with exponent 0.
    allometry: dict[str, float] = field(default_factory=dict)


# Log-log slopes of each dimension on chest circumference with stature held
# constant, fitted 2026-09-04 on the survey's women and men. A chest fitted
# 15 % smaller moves the shoulder joints 1.4 % in (women) but thins the
# upper arm 13 % and the waist 16 %: the figure's shoulder girdle is mostly
# bone and barely follows the chest, the arm is mostly muscle and does.
ALLOMETRY: dict[str, dict[str, float]] = {
    "female": {
        "shoulder_half": 0.090,
        "deltoid_r": 0.842,
        "upper_arm_r": 0.842,
        "forearm_r": 0.489,
        "neck_r_top": 0.463,
        "neck_r_bottom": 0.463,
        "waist_r": 1.116,
        "pelvis_r": 0.595,
        "hip_half": 0.542,
        "thigh_r": 0.689,
        "calf_r": 0.444,
    },
    "male": {
        "shoulder_half": 0.229,
        "deltoid_r": 0.932,
        "upper_arm_r": 0.932,
        "forearm_r": 0.618,
        "neck_r_top": 0.618,
        "neck_r_bottom": 0.618,
        "waist_r": 1.278,
        "pelvis_r": 0.732,
        "hip_half": 0.593,
        "thigh_r": 0.902,
        "calf_r": 0.647,
    },
}

MALE = Build(name="male", allometry=ALLOMETRY["male"])

# ANSUR II means, millimetres, from the 2012 survey's public data files
# (OpenLab, Penn State: 1,986 women, 4,082 men). Each female value of the
# figure is the male figure's fraction times the survey's female/male ratio
# of (mean / stature). Filled in by `_female_build()` below so the numbers
# and their arithmetic are visible in one place.
ANSUR_II: dict[str, tuple[float, float]] = {
    # dimension: (women, men) - means over 1,986 women and 4,082 men, mm,
    # computed 2026-09-04 from the public data files
    "stature": (1628.5, 1756.2),
    "chestcircumference": (946.9, 1058.7),
    "waistcircumference": (860.9, 940.6),
    "buttockcircumference": (1021.2, 1019.5),
    "hipbreadth": (353.8, 345.7),
    "biacromialbreadth": (365.3, 415.7),
    "bideltoidbreadth": (450.3, 510.4),
    "bicepscircumferenceflexed": (305.6, 358.1),
    "forearmcircumferenceflexed": (264.1, 310.1),
    "neckcircumference": (329.8, 397.6),
    "neckcircumferencebase": (371.2, 434.6),
    "thighcircumference": (616.1, 625.1),
    "calfcircumference": (373.3, 392.3),
    "headcircumference": (561.1, 574.4),
    "chestdepth": (247.4, 253.8),
    "shoulderelbowlength": (334.3, 363.7),
    "radialestylionlength": (241.3, 267.9),
    "trochanterionheight": (845.4, 900.9),
    "waistheightomphalion": (980.1, 1056.5),
    "cervicaleheight": (1395.7, 1517.3),
    "acromialheight": (1335.1, 1440.7),
    "kneeheightmidpatella": (449.0, 488.4),
}


def shape_ratio(dimension: str) -> float:
    """women's mean / stature over men's mean / stature - what differs
    between the sexes once size is taken out."""
    f, m = ANSUR_II[dimension]
    fs, ms = ANSUR_II["stature"]
    return (f / fs) / (m / ms)


def _female_build() -> Build:
    r = shape_ratio
    # the deltoid's overhang beyond the acromion, per side, relative to stature
    f_over = (ANSUR_II["bideltoidbreadth"][0] - ANSUR_II["biacromialbreadth"][0]) / 2
    m_over = (ANSUR_II["bideltoidbreadth"][1] - ANSUR_II["biacromialbreadth"][1]) / 2
    deltoid = (f_over / ANSUR_II["stature"][0]) / (m_over / ANSUR_II["stature"][1])
    # joint heights: pelvis from the trochanter, waist from the omphalion,
    # the shoulder line from the cervicale - each as the male fraction
    # times the survey's ratio, then the rises as their differences
    pelvis_y = MALE.pelvis_y * r("trochanterionheight")
    waist_y = (MALE.pelvis_y + MALE.waist_rise) * r("waistheightomphalion")
    neck_y = (MALE.pelvis_y + MALE.waist_rise + MALE.spine) * r("cervicaleheight")
    thigh = MALE.thigh * (
        (
            (ANSUR_II["trochanterionheight"][0] - ANSUR_II["kneeheightmidpatella"][0])
            / ANSUR_II["stature"][0]
        )
        / (
            (ANSUR_II["trochanterionheight"][1] - ANSUR_II["kneeheightmidpatella"][1])
            / ANSUR_II["stature"][1]
        )
    )
    # the shoulder line's drop from the neck base to the acromion, and the
    # deltoid's top above the joint, so the neck base sits that much above
    # the shoulder joint and the slope ends on the deltoid
    deltoid_r = MALE.deltoid_r * deltoid
    shoulder_line_drop = (
        ANSUR_II["cervicaleheight"][0] - ANSUR_II["acromialheight"][0]
    ) / ANSUR_II["stature"][0]
    return replace(
        MALE,
        name="female",
        allometry=ALLOMETRY["female"],
        trapezius=shoulder_line_drop + deltoid_r * 0.94 - MALE.shoulder_drop,
        pelvis_y=pelvis_y,
        waist_rise=waist_y - pelvis_y,
        spine=neck_y - waist_y,
        shoulder_half=MALE.shoulder_half * r("biacromialbreadth"),
        hip_half=MALE.hip_half * r("hipbreadth"),
        upper_arm=MALE.upper_arm * r("shoulderelbowlength"),
        forearm=MALE.forearm * r("radialestylionlength"),
        thigh=thigh,
        calf=MALE.calf * r("kneeheightmidpatella"),
        # the ribcage takes the chest-girth ratio; the bust is relief on top
        # of it, sized so the measured girth over the bust lands on the
        # ratio (see the test): 0.30 of the chest radius, measured
        chest_r=MALE.chest_r * r("chestcircumference"),
        waist_r=MALE.waist_r * r("waistcircumference"),
        pelvis_r=MALE.pelvis_r * r("buttockcircumference"),
        bust=0.30,
        deltoid_r=deltoid_r,
        neck_r_top=MALE.neck_r_top * r("neckcircumference"),
        neck_r_bottom=MALE.neck_r_bottom * r("neckcircumferencebase"),
        head_r=MALE.head_r * r("headcircumference"),
        upper_arm_r=MALE.upper_arm_r * r("bicepscircumferenceflexed"),
        forearm_r=MALE.forearm_r * r("forearmcircumferenceflexed"),
        thigh_r=MALE.thigh_r * r("thighcircumference"),
        calf_r=MALE.calf_r * r("calfcircumference"),
    )


FEMALE = _female_build()
BUILDS: dict[str, Build] = {"male": MALE, "female": FEMALE}


def build(name: str | Build) -> Build:
    if isinstance(name, Build):
        return name
    key = str(name or "male").strip().lower()
    if key not in BUILDS:
        raise ValueError(f"no build {name!r}; the figure has: {', '.join(sorted(BUILDS))}")
    return BUILDS[key]


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


def joints(
    pose: Any,
    *,
    height: float = 1.80,
    arm_abduction: float | None = None,
    build: str | Build = MALE,
) -> dict[str, Any]:
    """Every joint the figure hangs off, in metres. Y up, +Z forward, unturned.

    `pose` is a `seamkiln.avatar.Pose` (or anything with its attributes).
    """
    b = globals()["build"](build)
    if arm_abduction is None:
        arm_abduction = b.arm_abduction
    H = height
    rise = float(getattr(pose, "rise_m", 0.0))
    lean = math.radians(float(getattr(pose, "trunk_lean", 0.0)))

    pelvis = np.asarray([0.0, H * b.pelvis_y + rise, 0.0])
    waist = pelvis + np.asarray([0.0, H * b.waist_rise, 0.0])
    spine = H * b.spine
    # 0.68 of the way up, not 0.55: lower, the widest point of the torso sat
    # at the bottom of the ribcage and the chest read as a bowl.
    chest = waist + np.asarray([0.0, math.cos(lean) * spine * 0.68, math.sin(lean) * spine * 0.68])
    neck = waist + np.asarray([0.0, math.cos(lean) * spine, math.sin(lean) * spine])
    head = neck + np.asarray(
        [0.0, math.cos(lean) * H * b.head_rise, math.sin(lean) * H * b.head_rise]
    )

    half = H * b.shoulder_half
    out: dict[str, Any] = {
        "pelvis": pelvis,
        "waist": waist,
        "chest": chest,
        "neck": neck,
        "head": head,
        "shoulder_half": half,
        "height": H,
        "lean": lean,
        "build": b.name,
    }
    upper, fore = H * b.upper_arm, H * b.forearm
    thigh, calf = H * b.thigh, H * b.calf
    for side, tag in ((-1.0, "l"), (1.0, "r")):
        shoulder = neck + np.asarray([side * half, -H * b.shoulder_drop, 0.0])
        swing = float(getattr(pose, f"shoulder_{tag}", 0.0))
        bend = float(getattr(pose, f"elbow_{tag}", 0.0))
        elbow = _swing(shoulder, upper, swing, abduct=side * arm_abduction)
        hand = _swing(elbow, fore, swing - bend, abduct=side * arm_abduction * 0.35)
        hip = pelvis + np.asarray([side * H * b.hip_half, 0.0, 0.0])
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
    arm_abduction: float | None = None,
    facing_deg: float = 0.0,
    build: str | Build = MALE,
    chest_m: float | None = None,
) -> trimesh.Trimesh:
    """The figure, as one watertight mesh with a per-face part tag.

    The proportions are a garment's numbers, not a comic's: a 0.034H upper arm
    is 122 mm across on a 1.8 m body, a 0.106H chest is a 1.2 m girth. The
    joints and part tags ride in `mesh.metadata`. `build` picks the
    proportion set (`male`, the default and unchanged; `female`); `chest_m`
    is a chest girth in metres, the number a pattern maker has, and scales
    the trunk to it while the limbs, shoulders and lengths keep the build.
    """
    b = globals()["build"](build)
    if chest_m is not None:
        b = fitted_to_chest(b, height, chest_m, pose=pose)
    H = height
    j = joints(pose, height=H, arm_abduction=arm_abduction, build=b)
    parts: list[tuple[trimesh.Trimesh, int]] = []

    def add(mesh, tag):
        if mesh is not None and len(mesh.faces):
            parts.append((mesh, tag))

    chest_r, waist_r, pelvis_r = H * b.chest_r, H * b.waist_r, H * b.pelvis_r
    trunk = np.diag([b.torso_squash[0], 1.0, b.torso_squash[1], 1.0])

    def trunk_part(mesh):
        # the trunk parts sit on the body's axis, so scaling about the origin
        # widens and flattens them in place
        if mesh is not None:
            mesh.apply_transform(trunk)
        return mesh

    add(trunk_part(_frustum(j["waist"], j["chest"], waist_r, chest_r)), SUIT)
    add(trunk_part(_frustum(j["chest"], j["neck"], chest_r, chest_r * 0.88)), SUIT)
    add(trunk_part(_ball(j["chest"], chest_r, squash=(1.0, 0.42, 0.86))), SUIT)
    add(trunk_part(_frustum(j["pelvis"], j["waist"], pelvis_r, waist_r)), SUIT)
    add(trunk_part(_ball(j["pelvis"], pelvis_r, squash=(1.0, 0.62, 0.80))), SUIT)
    # The deltoid: a ball 1.06 wide across the shoulder, not 1.24. At 1.24 it
    # was 178 mm across on a 122 mm upper arm - 1.46 times the arm, where a
    # real shoulder is about 1.25 - and no sleeve a block will draft could
    # pass over it: a 1.18x sleeve slid off it in a walk, and the armhole
    # refused anything wider. At 1.06 it is 153 mm, and a 1.3x sleeve hooks
    # with margin to spare through a walk.
    for tag in ("l", "r"):
        add(_ball(j[f"shoulder_{tag}"], H * b.deltoid_r, squash=(1.06, 0.94, 1.0)), SUIT)
    if b.trapezius > 0.0:
        # the shoulder line: from the neck's base down to the top of each
        # deltoid, so a garment's shoulder seam rests on a slope that ends
        # on the deltoid instead of a flat top with the deltoid proud of it
        neck_base = j["neck"] + np.asarray([0.0, H * b.trapezius, 0.0])
        for tag in ("l", "r"):
            deltoid_top = j[f"shoulder_{tag}"] + np.asarray([0.0, H * b.deltoid_r * 0.94, 0.0])
            add(
                _frustum(
                    neck_base, deltoid_top, H * b.neck_r_bottom * 0.95, H * b.deltoid_r * 0.60
                ),
                SUIT,
            )

    belt = j["waist"] + np.asarray([0.0, -H * 0.014, 0.0])
    add(
        trunk_part(
            _frustum(belt, belt + np.asarray([0.0, H * 0.032, 0.0]), waist_r * 1.12, waist_r * 1.12)
        ),
        BELT,
    )

    up = j["neck"] - j["waist"]
    up = up / max(float(np.linalg.norm(up)), 1e-9)
    front = np.asarray([0.0, -up[2], up[1]])
    badge = j["waist"] + up * (H * 0.118) + front * (chest_r * b.torso_squash[1])
    add(_ball(badge, H * 0.031, squash=(1.20, 1.35, 0.22)), EMBLEM)
    if b.bust > 0.0:
        # the bust: two shallow balls on the chest's front, their relief a
        # fraction of the chest radius, so the garment's front hangs from
        # them the way a woman's tee does rather than from a flat ribcage
        for side in (-1.0, 1.0):
            centre = (
                j["chest"]
                + np.asarray([side * chest_r * b.torso_squash[0] * 0.42, -chest_r * 0.10, 0.0])
                + front * (chest_r * b.torso_squash[1] * 0.62)
            )
            add(_ball(centre, chest_r * b.bust, squash=(1.0, 0.92, 0.80)), SUIT)

    head_r = H * b.head_r
    add(_frustum(j["neck"], j["head"], H * b.neck_r_top, H * b.neck_r_bottom), SKIN)
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

    upper_r, fore_r = H * b.upper_arm_r, H * b.forearm_r
    thigh_r, calf_r = H * b.thigh_r, H * b.calf_r
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
        # the joints turn with the mesh they describe: left unturned, a
        # figure facing +x reported its shoulders at +-x while its arms
        # hung at +-z, and a check that trusted them read a sleeve on the
        # arm as 34 cm off it
        yaw = _yaw(facing_deg)
        j = {k: (yaw @ v if isinstance(v, np.ndarray) else v) for k, v in j.items()}
    body.metadata["part_per_face"] = per_face
    body.metadata["part_per_vertex"] = per_vertex
    body.metadata["joints"] = {
        k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in j.items()
    }
    body.metadata["facing_deg"] = float(facing_deg)
    body.metadata["seamkiln_figure"] = {
        "height_m": height,
        "parts": list(PARTS),
        "build": b.name,
    }
    return body


def trunk_girth_m(mesh: trimesh.Trimesh, y: float, *, band: float = 0.006) -> float:
    """The girth of the trunk alone at height `y`: the convex hull of the
    slice, with the arms cut away at the shoulder joints' x."""
    from shapely.geometry import MultiPoint

    j = mesh.metadata["joints"]
    # the trunk ends and the hanging upper arm begins between 0.85 and
    # 1.0 of the shoulder joint's x on both builds; the deltoid balls sit
    # above the chest joint, which is where the scan stops. A plane
    # section, not a vertex band: the frusta are two rings with nothing
    # between them, so a band between the rings finds no vertex at all.
    half = abs(float(j["shoulder_l"][0])) * 0.95
    _ = band
    section = mesh.section(plane_origin=[0.0, y, 0.0], plane_normal=[0.0, 1.0, 0.0])
    if section is None:
        return 0.0
    v = np.asarray(section.vertices)
    pts = v[np.abs(v[:, 0]) < half][:, [0, 2]]
    if len(pts) < 4:
        return 0.0
    return float(MultiPoint(pts).convex_hull.length)


def chest_girth_m(mesh: trimesh.Trimesh) -> float:
    """The figure's chest girth: the WIDEST trunk slice between the waist
    and the shoulders, which is where a garment's chest meets the body.

    Not the landmark scan's "chest": that scan reads the girth jump below
    the ribcage (912 mm on the male figure at 1.65 m, against 1,043 mm at
    the chest joint) and a body "matched" to a pattern by it was 8 % too
    big where the cloth actually touched.
    """
    j = mesh.metadata["joints"]
    # up to the chest joint and no higher: the deltoid balls' lowest point
    # is 6 mm above it on the male build, and a scan that reached them read
    # the shoulders (1,081 mm) for the chest and could not be fitted
    lo, hi = float(j["waist"][1]), float(j["chest"][1])
    return max(trunk_girth_m(mesh, y) for y in np.linspace(lo, hi, 24))


def fitted_to_chest(b: Build, height: float, chest_m: float, *, pose: Any = None) -> Build:
    """The build with its trunk scaled so the measured chest girth is `chest_m`.

    Measured, not assumed: the girth is read off the built mesh as the
    widest trunk slice, the chest radius is scaled by the ratio, and the
    read is repeated until it lands (three passes, within 5 mm on both
    builds - see the test). Everything else follows the chest by the
    survey's allometry (`Build.allometry`, log-log slopes at fixed
    stature): a chest fitted 15 % smaller on the female build moves the
    shoulder joints 1.4 % in, thins the upper arm and the deltoid 13 %,
    the waist 16 %, the hips 9 %. The first version scaled the trunk alone
    and left the shoulder girdle where it was: fitted to 860 mm the
    deltoids hung in free air outside the ribcage and both sleeve caps
    folded under them (facing -0.93 on the cap band).
    """
    if chest_m <= 0.3 or chest_m > 2.0:
        raise ValueError(f"chest_m is a girth in metres; {chest_m!r} is not a chest")
    if pose is None:
        from seamkiln.avatar import Pose

        pose = Pose()

    def scaled(k: float) -> Build:
        moved = {name: getattr(b, name) * k**e for name, e in b.allometry.items()}
        return replace(b, chest_r=b.chest_r * k, **moved)

    k = 1.0
    for _ in range(3):
        measured = chest_girth_m(figure(pose, height=height, build=scaled(k)))
        k *= chest_m / measured
    return scaled(k)


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
