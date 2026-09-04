"""Foreign bone names, mapped onto seamkiln's nine joints - by table, never by guess.

`avatar.JOINTS` is a nine-name vocabulary (`hip_l` .. `trunk_lean`) that the
gait and pose code speaks. Every rig a studio brings speaks a different one:
Mixamo says `mixamorig:LeftUpLeg`, Unreal says `thigh_l`, Blender's Rigify
says `thigh.L`, Daz says `lThigh`. Something has to translate, and the way
that translation fails is the reason this module is a hand-written TABLE and
not a similarity match:

  * `LeftShoulder` in Mixamo, BVH and Unity is the CLAVICLE, not the joint
    that swings the arm - that is `LeftArm`. A fuzzy matcher scores
    "LeftShoulder" against "shoulder_l" at nearly 1.0 and pivots every
    sleeve from the collarbone.
  * `LeftLeg` in Mixamo is the SHIN. Match it to `hip_l` on the word "leg"
    and the knee bends where the hip should.

Both mistakes look exactly like a solver bug in the drape, three hours
downstream. So: an explicit alias table, priority-ordered inside each joint,
and a REFUSAL naming the joint, what the file actually carries and how to fix
it whenever a joint seamkiln needs is not there. Nothing is inferred from
position in the hierarchy or from string distance.

`KNOWN_OTHER` is the other half of a useful refusal - the bones we recognise
and deliberately do not map (clavicles, hands, feet, fingers, the pelvis root),
so the message can say "found LeftShoulder, which is the clavicle" instead of
"not found".
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from ..avatar import JOINTS


class RigNameError(ValueError):
    """A rig whose bones cannot be mapped onto seamkiln's joints."""


# Namespace junk that carries no meaning, longest first so "mixamorig:" is
# tried before "mixamorig".
_PREFIXES = (
    "mixamorig:",
    "mixamorig",
    "armature|",
    "armature:",
    "bip001",
    "bip01",
    "def-",
    "org-",
    "mch-",
    "root|",
)
_SEPARATORS = "_-.:| \t"


def normalise(name: str) -> str:
    """Fold a bone name to its comparison key: case, separators and namespaces gone.

    `mixamorig:LeftUpLeg`, `Left_Up_Leg` and `left up leg` are the same bone
    written by three exporters; `LeftShoulder` and `LeftArm` are not the same
    bone written two ways, and nothing here pretends otherwise.
    """
    key = name.strip().lower()
    changed = True
    while changed:
        changed = False
        for prefix in _PREFIXES:
            if key.startswith(prefix) and len(key) > len(prefix):
                key = key[len(prefix) :]
                changed = True
        key = key.lstrip(_SEPARATORS)
    return "".join(ch for ch in key if ch not in _SEPARATORS)


# seamkiln joint -> foreign names, MOST specific / most likely first. The
# first alias present in a file wins, so a Mixamo skeleton carrying Spine,
# Spine1 and Spine2 resolves `trunk_lean` to Spine deterministically rather
# than being called ambiguous.
ALIASES: dict[str, tuple[str, ...]] = {
    "hip_l": (
        "LeftUpLeg",
        "LeftThigh",
        "LeftUpperLeg",
        "thigh.L",
        "l_thigh",
        "lThigh",
        "upperleg.L",
        "LeftHip",
        "hip.L",
    ),
    "hip_r": (
        "RightUpLeg",
        "RightThigh",
        "RightUpperLeg",
        "thigh.R",
        "r_thigh",
        "rThigh",
        "upperleg.R",
        "RightHip",
        "hip.R",
    ),
    "knee_l": (
        "LeftLeg",
        "LeftShin",
        "LeftLowerLeg",
        "LeftCalf",
        "shin.L",
        "calf.L",
        "l_shin",
        "lShin",
        "lowerleg.L",
        "LeftKnee",
        "knee.L",
    ),
    "knee_r": (
        "RightLeg",
        "RightShin",
        "RightLowerLeg",
        "RightCalf",
        "shin.R",
        "calf.R",
        "r_shin",
        "rShin",
        "lowerleg.R",
        "RightKnee",
        "knee.R",
    ),
    # NOT LeftShoulder - see the module docstring and KNOWN_OTHER.
    "shoulder_l": (
        "LeftArm",
        "LeftUpperArm",
        "upper_arm.L",
        "upperarm.L",
        "l_upperarm",
        "lShldr",
        "LeftUpArm",
    ),
    "shoulder_r": (
        "RightArm",
        "RightUpperArm",
        "upper_arm.R",
        "upperarm.R",
        "r_upperarm",
        "rShldr",
        "RightUpArm",
    ),
    "elbow_l": (
        "LeftForeArm",
        "LeftLowerArm",
        "forearm.L",
        "lowerarm.L",
        "l_forearm",
        "lForeArm",
        "LeftElbow",
        "elbow.L",
    ),
    "elbow_r": (
        "RightForeArm",
        "RightLowerArm",
        "forearm.R",
        "lowerarm.R",
        "r_forearm",
        "rForeArm",
        "RightElbow",
        "elbow.R",
    ),
    # seamkiln's trunk_lean is a SAGITTAL lean applied at the base of the
    # trunk, so it maps to the first spine bone above the pelvis - not to the
    # chest, which leans a torso from halfway up.
    "trunk_lean": ("Spine", "spine_01", "Spine1", "spine.001", "abdomen", "torso", "chest"),
}

# Joints seamkiln owns that NO rig bone can supply. Empty today; the entry
# format is `joint -> why`, and `UNCOVERED` below is what a test watches.
UNMAPPABLE: dict[str, str] = {}

# Bones we recognise and deliberately do not map, so a refusal can say what
# it saw rather than shrugging.
KNOWN_OTHER: dict[str, str] = {
    "hips": "the pelvis root; seamkiln carries pelvis motion as Pose.rise_m, not a joint angle",
    "pelvis": "the pelvis root; seamkiln carries pelvis motion as Pose.rise_m",
    "root": "the transform root, not a body joint",
    "armature": "the armature object, not a body joint",
    "leftshoulder": "the CLAVICLE - seamkiln's shoulder_l is the upper-arm joint (LeftArm)",
    "rightshoulder": "the CLAVICLE - seamkiln's shoulder_r is the upper-arm joint (RightArm)",
    "clavicle.l": "the clavicle; seamkiln's shoulder_l is the upper-arm joint",
    "clavicle.r": "the clavicle; seamkiln's shoulder_r is the upper-arm joint",
    "lcollar": "the clavicle; seamkiln's shoulder_l is the upper-arm joint",
    "rcollar": "the clavicle; seamkiln's shoulder_r is the upper-arm joint",
    "neck": "above the joints seamkiln poses",
    "head": "above the joints seamkiln poses",
    "lefthand": "below the joints seamkiln poses",
    "righthand": "below the joints seamkiln poses",
    "leftfoot": "below the joints seamkiln poses",
    "rightfoot": "below the joints seamkiln poses",
    "lefttoebase": "below the joints seamkiln poses",
    "righttoebase": "below the joints seamkiln poses",
}

# Normalised alias -> seamkiln joint, built once. A duplicate here would be a
# bone claimed by two joints, which is a bug in the table above, not in a file.
_LOOKUP: dict[str, str] = {}
for _joint, _names in ALIASES.items():
    for _alias in _names:
        _key = normalise(_alias)
        if _LOOKUP.setdefault(_key, _joint) != _joint:
            raise RuntimeError(f"alias {_alias!r} is claimed by both {_LOOKUP[_key]} and {_joint}")

_KNOWN_OTHER_KEYS = {normalise(k): v for k, v in KNOWN_OTHER.items()}

# What a test asserts is empty: every seamkiln joint is either in the table or
# declared unmappable, so adding a tenth joint to `avatar.JOINTS` cannot land
# silently unmapped.
UNCOVERED: tuple[str, ...] = tuple(j for j in JOINTS if j not in ALIASES and j not in UNMAPPABLE)


@dataclass(frozen=True, slots=True)
class JointMap:
    """The translation, both ways, plus what was left over."""

    by_joint: dict[str, str]  # seamkiln joint -> the bone name in the file
    by_file: dict[str, str]  # bone name in the file -> seamkiln joint
    unused: tuple[str, ...]  # bones with no seamkiln role
    notes: tuple[str, ...] = ()

    def index_map(self, names: Sequence[str]) -> dict[str, int]:
        """seamkiln joint -> position in `names`, for indexing a rig's arrays."""
        order = {name: i for i, name in enumerate(names)}
        return {joint: order[bone] for joint, bone in self.by_joint.items()}


def _resolve(
    names: Sequence[str], required: Sequence[str], overrides: Mapping[str, str]
) -> tuple[dict[str, str], list[str], dict[str, list[str]]]:
    by_key: dict[str, list[str]] = {}
    for name in names:
        by_key.setdefault(normalise(name), []).append(name)
    found: dict[str, str] = {}
    missing: list[str] = []
    ambiguous: dict[str, list[str]] = {}
    for joint in required:
        if joint in overrides:
            continue
        for alias in ALIASES.get(joint, ()):
            hits = by_key.get(normalise(alias))
            if hits:
                if len(hits) > 1:
                    ambiguous[joint] = hits
                found[joint] = hits[0]
                break
        else:
            missing.append(joint)
    return found, missing, ambiguous


def map_joint_names(
    names: Iterable[str],
    *,
    overrides: Mapping[str, str] | None = None,
    required: Sequence[str] = JOINTS,
) -> JointMap:
    """Map a rig's bone names onto seamkiln's joints, or refuse by name.

    `overrides` is the escape hatch the refusal message points at: a
    `{seamkiln joint: bone name}` dict that wins over the table, for the rig
    whose convention nobody has met before. It is checked against the file's
    bones, so a typo refuses instead of silently leaving a joint unmapped.
    """
    names = list(names)
    overrides = dict(overrides or {})
    notes: list[str] = []

    unknown_joint = [j for j in overrides if j not in JOINTS]
    if unknown_joint:
        raise RigNameError(
            f"overrides name {', '.join(sorted(unknown_joint))}, which are not seamkiln "
            f"joints. Joints: {', '.join(JOINTS)}."
        )
    absent = [f"{j}={overrides[j]!r}" for j in overrides if overrides[j] not in names]
    if absent:
        raise RigNameError(
            f"overrides point at bones this rig does not have: {', '.join(sorted(absent))}. "
            f"Its {len(names)} bones are: {', '.join(names)}."
        )

    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise RigNameError(
            f"this rig has more than one bone called {', '.join(duplicates)}; a mapping by "
            "name cannot tell them apart. Fix: make the bone names unique on export, or "
            "pass overrides= after renaming."
        )

    found, missing, ambiguous = _resolve(names, required, overrides)
    if ambiguous:
        # MEASURED, 2026-09-04: a Blender export of a Rigify character carries
        # both the control bone `thigh.L` and the deform bone `DEF-thigh.L`
        # (the exporter's "deform bones only" switch is OFF by default), and
        # `normalise` strips DEF-/ORG-/MCH- so both fold to the same key. Taking
        # the first hit made the mapping depend on the order `skin.joints`
        # happened to list them: the same rig mapped hip_l to `thigh.L` one way
        # round and `DEF-thigh.L` the other. The control bone owns no vertices
        # in a baked export, so that leg then simply does not move - the exact
        # silent wrong mapping this module was written to make impossible.
        detail = "; ".join(f"{j}: {', '.join(hits)}" for j, hits in sorted(ambiguous.items()))
        first = sorted(ambiguous)[0]
        raise RigNameError(
            f"{len(ambiguous)} of seamkiln's joints match MORE THAN ONE bone in this rig "
            f"once namespaces and separators are folded away - {detail}. Choosing by the "
            "order the file lists them would be a guess, and the wrong choice is silent: a "
            "control bone owns no vertices, so the limb never moves. Fix: pass "
            f"overrides={{{first!r}: {ambiguous[first][0]!r}}} naming the DEFORM bone for "
            "each, or re-export with deform bones only."
        )
    found.update(overrides)
    if overrides:
        notes.append(
            f"{len(overrides)} joint(s) mapped by override: {', '.join(sorted(overrides))}"
        )

    if missing:
        wanted = "; ".join(
            f"{j}: any of {{{', '.join(ALIASES.get(j, ('- no aliases -',))[:4])}}}" for j in missing
        )
        recognised = [
            f"{n} ({_KNOWN_OTHER_KEYS[normalise(n)]})"
            for n in names
            if normalise(n) in _KNOWN_OTHER_KEYS
        ]
        seen = (
            f" Recognised but not a seamkiln joint: {'; '.join(recognised)}." if recognised else ""
        )
        raise RigNameError(
            f"this rig cannot drive {len(missing)} of seamkiln's {len(required)} joints: "
            f"{', '.join(missing)}. Its {len(names)} bones are: {', '.join(names)}.{seen} "
            f"Fix: rename the bone to one of the names seamkiln knows - {wanted} - or pass "
            f"overrides={{{missing[0]!r}: '<the bone that is that joint>'}}. Nothing is "
            "matched by position or by spelling distance, because a mis-mapped limb bends "
            "the wrong way and reads as a solver bug."
        )

    by_file = {bone: joint for joint, bone in found.items()}
    unused = tuple(n for n in names if n not in by_file)
    return JointMap(by_joint=found, by_file=by_file, unused=unused, notes=tuple(notes))
