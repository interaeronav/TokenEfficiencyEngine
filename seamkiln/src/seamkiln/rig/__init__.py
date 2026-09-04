"""Rigs: a skinned character authored in code, and glTF read/write by hand.

WHY this package exists. `avatar.custom_avatar` loads a studio body with
`trimesh.load(path, force="mesh")`, which flattens a scene to ONE mesh and
throws the skeleton away, so `session` falls back to a rigid body and `walk`
moves the finest rigged character in the world as a statue. Everything the
gait work bought - a pelvis rising ~50 mm in a walk and ~140 mm in a run,
counter-phase arm swing, trunk lean - is lost on any body a studio brings.

Closing that needs three things, one per module:

* `character` - a rigged humanoid AUTHORED HERE, because a fixture must be
  deterministic, licence-clean and runnable in CI. The owner's asset folder
  holds only CLO `.avt` containers with obfuscated payloads, and SMPL /
  SMPL-X / STAR are non-commercial (research doc 67 §2) and cannot ship.
  Anny (Apache-2.0, CC0 assets) remains the route to a production body; this
  is the fixture that proves the pipeline, not a face.
* `gltf_write` - `.glb` written by hand from json + struct + numpy. NO new
  dependency: `pygltflib` is not installed and must not be added, and trimesh
  5.1.0 ignores glTF skins entirely, so it cannot do this either way.
* `gltf_read`, `naming` - the other half: reading a studio's rigged file, and
  mapping its joint names onto seamkiln's. The character deliberately uses
  the glTF/Mixamo names (`Hips`, `LeftUpLeg`, ...) and never seamkiln's own,
  so the mapping layer is exercised rather than satisfied by accident.

`import seamkiln.rig` pulls in the character and the writer only; the reader
and the name map are imported from their modules by anything that needs them.
"""

from __future__ import annotations

from .character import JOINT_NAMES, JOINT_PARENTS, MAX_INFLUENCES, Character, build_character
from .gltf_write import (
    Skeleton,
    SkinnedPrimitive,
    accessor_array,
    column_major,
    read_glb,
    write_glb,
)

__all__ = [
    "JOINT_NAMES",
    "JOINT_PARENTS",
    "MAX_INFLUENCES",
    "Character",
    "Skeleton",
    "SkinnedPrimitive",
    "accessor_array",
    "build_character",
    "column_major",
    "read_glb",
    "write_glb",
]
