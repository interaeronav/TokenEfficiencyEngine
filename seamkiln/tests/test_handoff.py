"""Handing a garment to the next application, in ITS coordinates.

The claims here about Blender were CHECKED in a real Blender 5.2, headless -
see `test_a_glb_lands_upright_in_a_real_blender`, which is marked `dcc` and
skips on a machine without one. The rest are hermetic and hold everywhere.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from seamkiln.handoff import SOURCE, TARGETS, transform_for
from seamkiln.session import Command, CommandError, Session

BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"


@pytest.fixture(scope="module")
def zipped(tmp_path_factory):
    session = Session()
    for command in (
        Command("block", {"block": "jacket-zip"}),
        Command("body", {"kind": "mannequin"}),
        Command("arrange", {"particle_distance_mm": 12.0}),
        Command("zip", {"opening": "centre-front", "material": "metal", "frames": 120}),
    ):
        session.apply(command)
    return session, tmp_path_factory.mktemp("handoff")


def test_a_self_describing_format_is_left_alone() -> None:
    """The trap. glTF states +Y up in metres and conforming importers convert;
    a second rotation from us would double-convert. Measured in Blender 5.2:
    with no transform the jacket stands at z 0.830..1.574 m, tallest axis Z.
    With our rotation baked in as well it lies on its face at z -0.189..0.175."""
    for name in TARGETS:
        assert np.allclose(transform_for(TARGETS[name], "glb"), np.eye(4)), name
        assert np.allclose(transform_for(TARGETS[name], "usdc"), np.eye(4)), name


def test_obj_carries_the_transform_because_obj_defines_nothing() -> None:
    """OBJ has no units, no axis and no handedness, so every application
    guesses - which is exactly why the transform is baked into the vertices
    rather than written down as advice in a README nobody reads."""
    up = np.asarray([0.0, 1.0, 0.0, 1.0])  # a metre straight up, in seamkiln

    blender = transform_for(TARGETS["blender"], "obj") @ up
    assert blender[:3] == pytest.approx([0.0, 0.0, 1.0]), "Blender is Z-up, metres"

    maya = transform_for(TARGETS["maya"], "obj") @ up
    assert maya[:3] == pytest.approx([0.0, 100.0, 0.0]), "Maya is Y-up, centimetres"

    marvelous = transform_for(TARGETS["marvelous"], "obj") @ up
    assert marvelous[:3] == pytest.approx([0.0, 1000.0, 0.0]), "Marvelous works in mm"

    unreal = transform_for(TARGETS["unreal"], "obj") @ up
    assert unreal[:3] == pytest.approx([0.0, 0.0, 100.0]), "Unreal is Z-up, cm, left-handed"
    # left-handedness is a REFLECTION, so it flips the determinant's sign
    assert np.linalg.det(transform_for(TARGETS["unreal"], "obj")[:3, :3]) < 0.0
    assert np.linalg.det(transform_for(TARGETS["maya"], "obj")[:3, :3]) > 0.0


def test_seamkiln_states_its_own_convention() -> None:
    """Half of every pipeline argument is one side not saying what it means."""
    assert (SOURCE.up, SOURCE.handed, SOURCE.unit_m) == ("Y", "right", 1.0)


def test_a_bundle_carries_the_mesh_the_uvs_and_the_hardware(zipped) -> None:
    session, root = zipped
    out = session.apply(Command("handoff", {"out": str(root / "blender"), "target": "blender"}))
    assert out["target"] == "blender"
    assert out["transform"] == [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    assert Path(out["files"]["garment"]).exists()
    assert Path(out["files"]["hardware"]).exists(), "the zipper did not come with it"
    manifest = json.loads(Path(out["files"]["manifest"]).read_text())
    assert manifest["uv"].startswith("from the flat pattern")
    assert manifest["transform_applied"] is False
    assert "double-convert" in manifest["why_no_transform"]
    assert manifest["panels"].keys() == session.garment.panel_slices.keys()
    zips = [h for h in manifest["hardware"] if h["kind"] == "zipper"]
    assert len(zips) == 1 and zips[0]["material"] == "metal"
    # a downstream artist swaps in their own slider, so the size has to be there
    assert zips[0]["slider_mm"] == [20.0, 12.0]


def test_a_target_tee_can_drive_gets_ops_and_one_it_cannot_gets_a_reason(zipped) -> None:
    """Refusing beats guessing. Godot's bridge can only instantiate an allowed
    CLASS - it has no file-import op at all - so emitting one would fail inside
    Godot instead of here, which is the expensive place to find out."""
    session, root = zipped
    blender = session.apply(Command("handoff", {"out": str(root / "b2"), "target": "blender"}))
    assert blender["ops"][0]["kind"] == "import_file"
    assert blender["ops"][0]["props"]["path"] == blender["files"]["garment"]
    assert len(blender["ops"]) == 2, "the hardware needs importing too"

    godot = session.apply(Command("handoff", {"out": str(root / "g"), "target": "godot"}))
    assert godot["ops"] is None
    assert "no file-import op" in godot["why_no_ops"]
    assert Path(godot["files"]["garment"]).exists(), "the files are still written"


def test_an_unknown_target_names_the_known_ones(zipped) -> None:
    session, root = zipped
    with pytest.raises(CommandError, match="maya"):
        session.apply(Command("handoff", {"out": str(root / "x"), "target": "cinema4d"}))


def test_a_handoff_needs_a_garment() -> None:
    session = Session()
    session.apply(Command("block", {"block": "jacket-zip"}))
    with pytest.raises(CommandError, match="Run 'arrange' first"):
        session.apply(Command("handoff", {"out": "/tmp/nope"}))


@pytest.mark.dcc
@pytest.mark.skipif(not Path(BLENDER).exists(), reason="needs Blender on this machine")
def test_a_glb_lands_upright_in_a_real_blender(zipped, tmp_path) -> None:
    """The claim, checked rather than asserted. Runs in a factory-startup
    headless Blender - it never touches whatever the owner has open."""
    session, root = zipped
    out = session.apply(Command("handoff", {"out": str(root / "live"), "target": "blender"}))
    script = tmp_path / "measure.py"
    script.write_text(
        "import json, sys, bpy, mathutils\n"
        "bpy.ops.wm.read_factory_settings(use_empty=True)\n"
        "bpy.ops.import_scene.gltf(filepath=sys.argv[-1])\n"
        "objs=[o for o in bpy.data.objects if o.type=='MESH']\n"
        "lo=[1e9]*3; hi=[-1e9]*3\n"
        "for o in objs:\n"
        "    for v in o.bound_box:\n"
        "        w=o.matrix_world @ mathutils.Vector(v)\n"
        "        for k in range(3):\n"
        "            lo[k]=min(lo[k],w[k]); hi[k]=max(hi[k],w[k])\n"
        "size=[hi[k]-lo[k] for k in range(3)]\n"
        "print('TEE_RESULT '+json.dumps({'size':size,'min_z':lo[2],'max_z':hi[2],"
        "'uv':sorted({l.name for o in objs for l in o.data.uv_layers}),"
        "'unit':bpy.context.scene.unit_settings.length_unit}))\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            BLENDER,
            "--background",
            "--factory-startup",
            "--python",
            str(script),
            "--",
            out["files"]["garment"],
        ],
        capture_output=True,
        text=True,
        timeout=300,
    )
    line = next(x for x in proc.stdout.splitlines() if x.startswith("TEE_RESULT"))
    got = json.loads(line[len("TEE_RESULT ") :])
    assert got["unit"] == "METERS"
    assert got["uv"] == ["UVMap"], "the flat-pattern UVs did not survive the trip"
    # upright: the tallest axis is Z, not Y
    assert got["size"].index(max(got["size"])) == 2, f"it is lying down: {got['size']}"
    # and standing ON the mannequin, not sunk through the floor at the origin
    assert got["min_z"] > 0.5 and got["max_z"] < 1.8, got
