"""The handoff: what each file says about itself, and who can load it.

The trap this module exists for, in one line: glTF DEFINES +Y up in metres
and partkiln's own writer already converts (XCAF LengthUnit 0.001 m plus the
Z-up input coordinate system), so a .glb needs the IDENTITY transform - and
applying one anyway lands the part on its face. Everything else is the
opposite problem: STL and OBJ declare NOTHING, so the conversion has to be
baked into the vertices and written down in the manifest.

The bundles that touch OCCT carry `@pytest.mark.brep`; the table, the
matrices, the manifest hook and the refusals are pure arithmetic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from partkiln import handoff
from partkiln.document import CommandError


@pytest.fixture(scope="module")
def ocp() -> Any:
    return pytest.importorskip("OCP", reason="partkiln[brep] not installed")


@pytest.fixture
def f1(ocp: Any) -> Any:
    """F1: the 100 x 60 x 10 plate with a d10 hole; 59 214.602 mm3."""
    from partkiln.brep.fixtures import build_F1

    return build_F1()


# --------------------------------------------------------------------------- the table


def test_the_source_is_partkilns_own_convention() -> None:
    assert handoff.SOURCE.name == "partkiln"
    assert (handoff.SOURCE.up, handoff.SOURCE.handed, handoff.SOURCE.unit_m) == (
        "Z",
        "right",
        0.001,
    )


@pytest.mark.parametrize("name", ["blender", "unreal", "godot", "maya", "zbrush", "houdini"])
def test_every_target_states_all_six_facts(name: str) -> None:
    spec = handoff.target(name)
    assert spec.up in ("Y", "Z")
    assert spec.handed in ("left", "right")
    assert spec.unit_m > 0
    assert spec.prefers in handoff.WRITERS
    assert isinstance(spec.driven_by_tee, bool)
    assert spec.driven_by_tee is (name in ("blender", "unreal"))
    assert spec.note or name == "houdini"


def test_an_unknown_target_refuses_naming_the_ones_there_are() -> None:
    with pytest.raises(CommandError) as excinfo:
        handoff.target("substance")
    assert excinfo.value.code == "pk_ref_unknown"
    assert "blender" in str(excinfo.value) and "godot" in str(excinfo.value)


# --------------------------------------------------------------------------- the matrices


@pytest.mark.parametrize("name", sorted(handoff.TARGETS))
@pytest.mark.parametrize("fmt", ["glb", "gltf", "step", "iges", "3mf"])
def test_a_self_describing_format_gets_the_identity(name: str, fmt: str) -> None:
    """A second conversion on top of one the file already states is the
    double-convert bug, for every target - including the Y-up ones."""
    assert np.allclose(handoff.transform_for(handoff.target(name), fmt), np.eye(4))


def test_a_mesh_for_a_y_up_centimetre_target_carries_the_whole_conversion() -> None:
    matrix = handoff.transform_for(handoff.target("maya"), "obj")
    assert not np.allclose(matrix, np.eye(4))
    assert handoff.scale_of(matrix) == pytest.approx(0.1)  # mm -> cm
    # +Z up becomes +Y up, and 100 mm becomes 10 cm.
    assert (matrix[:3, :3] @ np.array([0.0, 0.0, 100.0])) == pytest.approx([0.0, 10.0, 0.0])
    assert (matrix[:3, :3] @ np.array([100.0, 0.0, 0.0])) == pytest.approx([10.0, 0.0, 0.0])


def test_a_mesh_for_a_left_handed_target_flips_and_scales_only() -> None:
    matrix = handoff.transform_for(handoff.target("unreal"), "stl")
    assert np.linalg.det(matrix[:3, :3]) < 0  # left-handed: a reflection, not a rotation
    assert handoff.scale_of(matrix) == pytest.approx(0.1)  # mm -> cm
    assert (matrix[:3, :3] @ np.array([0.0, 0.0, 100.0])) == pytest.approx([0.0, 0.0, 10.0])
    assert (matrix[:3, :3] @ np.array([0.0, 100.0, 0.0])) == pytest.approx([0.0, -10.0, 0.0])


def test_a_mesh_for_a_z_up_metre_target_is_scale_only() -> None:
    matrix = handoff.transform_for(handoff.target("blender"), "stl")
    assert handoff.scale_of(matrix) == pytest.approx(0.001)
    assert np.allclose(matrix[:3, :3] / 0.001, np.eye(3))


# --------------------------------------------------------------------------- the manifest hook


def test_the_manifest_hook_answers_per_format_and_target() -> None:
    """`partkiln.methods` reaches for `handoff.manifest` by name so an export
    decorates itself from ONE table."""
    glb = handoff.manifest("glb", "blender")
    assert (glb["units"], glb["up"], glb["declares_units"]) == ("m", "Y", True)
    assert glb["transform_needed"] is False
    assert "double-convert" in glb["why_no_transform"]
    assert glb["target_up"] == "Z" and glb["scale_from_mm"] == pytest.approx(0.001)

    stl = handoff.manifest("stl", "unreal")
    assert (stl["units"], stl["up"], stl["handed"]) == ("cm", "Z", "left")
    assert stl["declares_units"] is False and stl["transform_needed"] is True
    assert "declares nothing" in stl["why_transform"]

    step = handoff.manifest("step")
    assert (step["units"], step["up"], step["declares_units"]) == ("mm", "Z", True)
    assert step["transform_needed"] is False

    assert handoff.manifest("dxf") == {}  # a drawing format is not this module's to answer


# --------------------------------------------------------------------------- bundles


@pytest.mark.brep
def test_f1_to_blender_as_glb_is_metres_y_up_and_untransformed(f1: Any, tmp_path: Path) -> None:
    bundle = handoff.bundle({"plate": f1}, tmp_path, target="blender", fmt="glb", name="F1")
    manifest = json.loads(Path(bundle.files["manifest"]).read_text(encoding="utf-8"))
    assert manifest["partkiln_handoff"] == 1 and manifest["name"] == "F1"
    assert manifest["format"] == "glb"
    assert (manifest["units"], manifest["up"], manifest["handed"]) == ("m", "Y", "right")
    assert manifest["declares_units"] is True
    assert manifest["transform_applied"] is False
    assert manifest["transform"] == np.eye(4).tolist()
    assert "double-convert" in manifest["why_no_transform"]
    assert manifest["why_transform"] is None
    assert manifest["source"] == {
        "kernel": "partkiln",
        "up": "Z",
        "handed": "right",
        "units": "mm",
    }
    assert manifest["target"] == {
        "name": "blender",
        "up": "Z",
        "handed": "right",
        "unit_m": 1.0,
        "prefers": "glb",
    }
    assert manifest["files"]["plate"]["units"] == "m"
    # The measured read-back of F1 through the writer: 100 x 10 x 60 mm in metres.
    assert manifest["files"]["plate"]["extents"] == pytest.approx([0.1, 0.01, 0.06], abs=1e-6)
    assert manifest["driven_by_tee"] is True
    assert Path(bundle.files["plate"]).suffix == ".glb"


@pytest.mark.brep
def test_f1_to_godot_writes_the_files_and_says_to_drop_them_in(f1: Any, tmp_path: Path) -> None:
    bundle = handoff.bundle({"plate": f1}, tmp_path, target="godot")
    assert bundle.fmt == "glb"  # godot's own preference
    assert bundle.manifest["transform_applied"] is False
    assert "res://" in bundle.manifest["note"]
    assert bundle.manifest["driven_by_tee"] is False
    assert Path(bundle.files["plate"]).is_file()
    with pytest.raises(CommandError) as excinfo:
        handoff.ops_for(bundle)
    assert excinfo.value.code == "pk_not_served"
    assert "res://" in str(excinfo.value) and "manifest.json" in str(excinfo.value)


@pytest.mark.brep
def test_an_stl_declares_nothing_and_so_carries_its_conversion(f1: Any, tmp_path: Path) -> None:
    bundle = handoff.bundle({"plate": f1}, tmp_path, target="blender", fmt="stl")
    manifest = bundle.manifest
    assert manifest["declares_units"] is False
    assert manifest["transform_applied"] is True
    assert manifest["scale"] == pytest.approx(0.001)
    assert manifest["units"] == "m"  # the vertices ARE metres; the file does not say so
    assert "declares nothing" in manifest["why_transform"]
    assert bundle.summary()["declares_units"] is False


@pytest.mark.brep
def test_the_deflection_is_scaled_with_the_transform(f1: Any, tmp_path: Path) -> None:
    """`tessellate` takes an ABSOLUTE deflection, in the units of the shape it
    is handed. Measured: scaling F1 to metres and meshing at the unscaled
    0.1 gave 18 triangles, not watertight, with the hole gone - the deflection
    was the size of the part. Scaled, the same part meshes identically at any
    target scale."""
    from partkiln.exchange.stl import mesh_stats

    counts = {}
    for target in ("blender", "unreal", "maya"):
        bundle = handoff.bundle({"plate": f1}, tmp_path / target, target=target, fmt="stl")
        stats = mesh_stats(bundle.files["plate"])
        assert stats["watertight"], target
        counts[target] = stats["triangles"]
        scale = bundle.manifest["scale"]
        # Sorted: maya is Y-up, so its extents come back in a different order.
        assert sorted(stats["extents"]) == pytest.approx(
            sorted(v * scale for v in (100.0, 60.0, 10.0)), rel=1e-6
        )
    assert len(set(counts.values())) == 1, counts


@pytest.mark.brep
@pytest.mark.parametrize("fmt", ["step", "3mf", "obj", "brep", "iges"])
def test_every_writer_lands_a_file_and_a_manifest(f1: Any, tmp_path: Path, fmt: str) -> None:
    bundle = handoff.bundle({"plate": f1}, tmp_path / fmt, target="blender", fmt=fmt)
    assert Path(bundle.files["plate"]).stat().st_size > 0
    assert bundle.manifest["declares_units"] is (fmt in handoff.DECLARES_UNITS)
    assert bundle.manifest["files"]["plate"]["units"] == bundle.manifest["units"]
    assert bundle.manifest["tol_mm"] == handoff.DEFAULT_TOL_MM


@pytest.mark.brep
def test_a_bundle_of_two_parts_names_both(f1: Any, tmp_path: Path) -> None:
    from partkiln.brep import shapes

    pin = shapes.cylinder(5.0, 40.0)
    bundle = handoff.bundle({"plate": f1, "pin": pin}, tmp_path, target="blender")
    assert sorted(bundle.files) == ["manifest", "pin", "plate"]
    assert sorted(bundle.manifest["files"]) == ["pin", "plate"]
    ops = handoff.ops_for(bundle)
    assert sorted(op["name"] for op in ops) == ["pin", "plate"]


# --------------------------------------------------------------------------- ops_for


@pytest.mark.brep
def test_ops_for_blender_is_the_tee_import_file_op(f1: Any, tmp_path: Path) -> None:
    """The Blender codegen dispatches on `op` (not `kind`) and reads `path`
    off the op itself - the shape TEE's own asset importer emits."""
    bundle = handoff.bundle({"plate": f1}, tmp_path, target="blender")
    (op,) = handoff.ops_for(bundle)
    assert op["op"] == "import_file"
    assert op["name"] == "plate"
    assert op["path"] == bundle.files["plate"]
    assert op["props"] == {}
    assert handoff.ops_for(bundle, name="bracket")[0]["name"] == "bracket"


@pytest.mark.brep
def test_ops_for_unreal_is_the_adapter_method_not_a_batch_op(f1: Any, tmp_path: Path) -> None:
    """Epic's AssetTools cannot import, so TEE's asset lane calls the adapter
    method directly; emitting a batch op here would fail inside the editor."""
    bundle = handoff.bundle({"plate": f1}, tmp_path, target="unreal")
    (call,) = handoff.ops_for(bundle)
    assert "op" not in call
    assert call["adapter"] == "unreal" and call["method"] == "import_asset_file"
    assert set(call["params"]) == {"path", "destination", "label", "location", "scale"}
    assert call["params"]["destination"] == "/Game/TeeAssets"
    assert call["params"]["path"] == bundle.files["plate"]
    assert "content plugin" in call["note"]


@pytest.mark.parametrize("name", ["godot", "maya", "zbrush", "houdini"])
def test_ops_for_refuses_for_every_target_tee_cannot_drive(name: str) -> None:
    spec = handoff.target(name)
    bundle = handoff.Bundle(target=spec, directory=Path("/tmp/x"), fmt=spec.prefers)
    with pytest.raises(CommandError) as excinfo:
        handoff.ops_for(bundle)
    assert excinfo.value.code == "pk_not_served"
    assert name in str(excinfo.value)


# --------------------------------------------------------------------------- refusals


def test_bundle_refuses_an_empty_set_and_a_format_it_cannot_write(tmp_path: Path) -> None:
    with pytest.raises(CommandError) as excinfo:
        handoff.bundle({}, tmp_path)
    assert excinfo.value.code == "pk_needs"
    with pytest.raises(CommandError) as excinfo:
        handoff.bundle({"plate": object()}, tmp_path, target="blender", fmt="dwg")
    assert excinfo.value.code == "pk_bad_op"
    assert "blender prefers glb" in str(excinfo.value)


def test_handoff_reaches_ocp_only_from_inside_a_function() -> None:
    """`import partkiln.handoff` must cost no B-rep kernel (Law 17): every OCP
    import here is indented inside the function that needs it."""
    source = Path(handoff.__file__).read_text(encoding="utf-8")
    top_level = [
        line
        for line in source.splitlines()
        if line.startswith(("import ", "from ")) and not line.startswith((" ", "\t"))
    ]
    assert top_level, "the scan found no imports at all - it is not looking at the module"
    for line in top_level:
        assert "OCP" not in line and " tee" not in line, line
    assert any("OCP" in line for line in source.splitlines() if line.startswith("    ")), (
        "the OCP imports should be inside functions, not absent"
    )
