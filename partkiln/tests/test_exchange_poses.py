"""A66 gap 9: an exported assembly is where the SOLVE put it, not at the origin.

`pk_export` used to walk `_bodies`, which answers `(part.name, part.shape)` -
every part in its OWN frame - and `of` did not even accept an assembly. The
shaft_housing example therefore wrote a STEP with two products stacked at the
origin: a file that opens without an error, looks like a shaft and a housing,
and has the shaft driven through the housing's corner. Measured on the old
code, the two bodies at part coordinates share **2 356.194 mm3** of solid;
at the solved poses they share **0** with a 0.100 mm clearance. That is the
whole defect - a silently wrong file - and every test here is a number that
separates the two.

What each acceptance letter is asserted by, so a future reader does not have
to hunt (the letters are the gap's own):

* (a) `test_the_assembly_step_is_written_at_the_solved_poses` - 2 products
  named for the COMPONENTS, the shaft's read-back box starting at x = -29
  where the insert mate put it, and the union of the two boxes equal to
  `pk_measure(what=bbox, of=asm)` to the millimetre.
* (b) `test_the_glb_extents_are_the_placed_union` and
  `test_the_stl_is_one_mesh_of_two_placed_shells` - the GLB read back through
  TEE's own `probe`, and the STL's watertight answer given honestly for a
  multi-body compound (see that test's docstring for what the word means
  there).
* (c) `test_the_step_volume_is_the_sum_of_the_component_volumes` - a rigid
  pose moves no material, so the round trip is the sum to 1e-9 relative.
* (d) `test_an_unconstrained_component_still_exports_and_is_named_as_authored`
  - it exports, and the manifest says which components the solve placed and
  which sit where the model authored them.
* (e) `test_a_bare_part_is_still_written_in_its_own_frame` - the shipped path,
  unchanged: a part instanced at a non-identity pose still exports at the
  origin. (The byte-identity half of (e) is a two-tree measurement, not a
  test: the bracket's STEP is 88 585 B with the same sha256 before and after,
  and its STL is byte-identical.)

Every test needs OCCT: a pose is applied with `BRepBuilderAPI_Transform`, and
there is nothing to assert without a body to move.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

from partkiln._errors import KernelError
from partkiln.client import LocalKernel

pytestmark = pytest.mark.brep

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # `examples/` sits beside `src/`; only `src` is on the path
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="module")
def ocp() -> Any:
    return pytest.importorskip("OCP", reason="partkiln[brep] not installed")


@pytest.fixture
def shaft_housing(ocp: Any) -> LocalKernel:
    """The W2 example itself: a shaft inserted into a housing bore, solved.

    The example is the fixture on purpose - it is the file the gap was found
    in, and a fresh hand-typed twin could differ from it without anyone
    noticing.
    """
    from examples.shaft_housing import model

    kernel, _ = model.build_parts()
    kernel.apply(model.ASM_OPS)
    return kernel


def _read(path: Path) -> dict[str, Any]:
    from partkiln.exchange.step import read_step

    return read_step(path)


def _boxes(path: Path) -> dict[str, list[float]]:
    """{product name: [xmin, ymin, zmin, xmax, ymax, zmax]} read back off disk."""
    from partkiln.brep import shapes

    return {
        p["name"]: [round(c, 3) for c in shapes.bbox(p["shape"])] for p in _read(path)["products"]
    }


def _probe(path: Path) -> dict[str, Any] | None:
    """TEE's own glTF reader when it is importable (tests only; src never imports tee)."""
    try:
        from tee.assets.gltf import probe
    except ImportError:
        return None
    return probe(path)


# --------------------------------------------------------------------------- (a)


def test_the_assembly_step_is_written_at_the_solved_poses(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """`of: asm` writes each COMPONENT where the solve put it.

    The old code answered these same two products with both boxes starting at
    x = 0 (`shaft` [0, -15, -15, 80, 15, 15]) because it exported the part
    shapes; the insert mate's answer, -29 mm along the bore axis, was thrown
    away. The union box is the second half of the assertion: it has to agree
    with what the document itself says the assembly measures.
    """
    out = tmp_path / "asm.step"
    result = shaft_housing.call("export", {"format": "step", "of": "asm", "out": str(out)})

    assert result["products"] == 2
    assert result["of"] == ["housing", "shaft"]
    boxes = _boxes(out)
    assert sorted(boxes) == ["housing", "shaft"]
    # The solved pose, to the millimetre: translation (-29, 30, 30) on a
    # d20 journal / d30 collar shaft that is 80 long.
    assert boxes["housing"] == [0.0, 0.0, 0.0, 30.0, 60.0, 60.0]
    assert boxes["shaft"] == [-29.0, 15.0, 15.0, 51.0, 45.0, 45.0]

    union_min = [min(b[i] for b in boxes.values()) for i in range(3)]
    union_max = [max(b[i + 3] for b in boxes.values()) for i in range(3)]
    measured = shaft_housing.call("measure", {"what": "bbox", "of": "asm"})
    assert measured["bbox_min"] == union_min == [-29.0, 0.0, 0.0]
    assert measured["bbox_max"] == union_max == [51.0, 60.0, 60.0]
    assert measured["bbox_mm"] == [80.0, 60.0, 60.0]


def test_the_written_bodies_clear_each_other_and_the_part_frames_do_not(
    shaft_housing: LocalKernel,
) -> None:
    """The number that says the old file was WRONG, not merely differently placed.

    An insert mate is a fit: at the solved poses the shaft and the housing
    share no solid at all and stand 0.100 mm apart. In part coordinates the
    same two bodies share 2 356.194 mm3 - the journal ploughed through the
    housing's corner. A receiver cannot tell the two files apart by looking.
    """
    from partkiln.assembly.interference import report as contact_report

    doc = shaft_housing.document
    at_part_frames = contact_report(
        [("housing", doc.parts["housing"].shape), ("shaft", doc.parts["shaft"].shape)]
    )
    assert [row["mm3"] for row in at_part_frames["interference"]] == [2356.194]

    solved = shaft_housing.call("measure", {"what": "interference"})
    assert solved["interference"] == []
    assert shaft_housing.call("measure", {"what": "clearance", "a": "shaft", "b": "housing"})[
        "mm"
    ] == pytest.approx(0.1, abs=1e-9)


# --------------------------------------------------------------------------- (b)


def test_the_glb_extents_are_the_placed_union(shaft_housing: LocalKernel, tmp_path: Path) -> None:
    """Read back through `tee.assets.gltf.probe`: metres, Y-up, placed.

    [0.08, 0.06, 0.06] m is the assembly's own 80 x 60 x 60 mm box. Exporting
    the two PARTS instead gives [0.08, 0.074976, 0.074994] - the shaft's
    d30 collar hanging below the housing at the origin, and a mesh-resolution
    number rather than a design one, which is how a wrong GLB announces
    itself if you are looking.
    """
    placed = tmp_path / "asm.glb"
    parts = tmp_path / "parts.glb"
    shaft_housing.call("export", {"format": "glb", "of": "asm", "out": str(placed)})
    shaft_housing.call("export", {"format": "glb", "of": ["housing", "shaft"], "out": str(parts)})

    seen = _probe(placed)
    if seen is None:
        pytest.skip("tee is not importable here; the GLB was still written")
    assert seen["meshes"] == 2
    assert seen["units"] == "m"
    assert seen["extents_m"] == pytest.approx([0.08, 0.06, 0.06], abs=1e-6)
    part_frames = _probe(parts)
    assert part_frames is not None
    assert part_frames["extents_m"] == pytest.approx([0.08, 0.074976, 0.074994], abs=1e-6)


def test_the_stl_is_one_mesh_of_two_placed_shells(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """One watertight answer for a two-body compound, and what it means.

    trimesh loads the file with `force="mesh"`, so the two shells arrive as
    ONE mesh with two connected components; `is_watertight` asks whether
    every edge has two faces, which two separate closed shells satisfy. So
    True here means "each body is closed", NOT "the assembly is one solid" -
    and it is reported as the writer measured it rather than suppressed.
    """
    out = tmp_path / "asm.stl"
    result = shaft_housing.call("export", {"format": "stl", "of": "asm", "out": str(out)})
    assert result["triangles"] == 592
    assert result["watertight"] is True

    from partkiln.exchange.stl import mesh_stats

    stats = mesh_stats(out)
    assert stats["extents"] == pytest.approx([80.0, 60.0, 60.0], abs=0.11)  # deflection 0.05


# --------------------------------------------------------------------------- (c)


def test_the_step_volume_is_the_sum_of_the_component_volumes(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """A rigid pose moves no material: round trip == the sum, to 1e-9 relative."""
    out = tmp_path / "asm.step"
    result = shaft_housing.call("export", {"format": "step", "of": "asm", "out": str(out)})
    assert result["roundtrip"]["volume_ok"] is True

    # The EXACT `BRepGProp` volumes, not `measure mass`'s 3-dp report: rounding
    # the components to a thousandth of a mm3 is itself 1.03e-9 relative on
    # this pair, which would swamp the number under test.
    from partkiln.exchange import volume_mm3

    doc = shaft_housing.document
    components = sum(volume_mm3(doc.parts[name].shape) for name in ("housing", "shaft"))
    written = sum(product["volume_mm3"] for product in _read(out)["products"])
    assert components == pytest.approx(131372.507, abs=5e-4)
    assert abs(written - components) / components < 1e-9


# --------------------------------------------------------------------------- (d)


def _pin_kernel(instances: int) -> LocalKernel:
    """One d10 x 40 pin part, `instances` components 25 mm apart along x.

    The 4-pin pattern of gap 9: ONE part, four places, four products. No mate
    - the poses are authored, which is also what makes this the fixture for
    the under-constrained half of the acceptance.
    """
    kernel = LocalKernel()
    ops: list[dict[str, Any]] = [
        {"op": "create", "kind": "part", "name": "pin", "props": {"material": "steel_s275"}},
        {
            "op": "create",
            "kind": "sketch",
            "name": "psk",
            "props": {"plane": "XY", "profile": [{"circle": 10, "at": [0, 0], "tag": "c"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "psk", "distance": 40},
        },
    ]
    for i in range(instances):
        ops.append(
            {"op": "create", "kind": "component", "props": {"part": "pin", "at": [25 * i, 0, 0]}}
        )
    kernel.apply(ops)
    return kernel


def test_one_part_instanced_four_times_is_four_products(ocp: Any, tmp_path: Path) -> None:
    """Named for the COMPONENT, not the part - four products, four places.

    Naming the products for the part would write `pin` four times and leave a
    reader with no way to tell the instances apart; the auto-names the
    document already gives components (`pin, pin2, pin3, pin4`) are the names
    that go in the file.
    """
    kernel = _pin_kernel(4)
    out = tmp_path / "pins.step"
    result = kernel.call("export", {"format": "step", "of": "asm", "out": str(out)})
    assert result["products"] == 4
    assert result["of"] == ["pin", "pin2", "pin3", "pin4"]

    boxes = _boxes(out)
    assert [boxes[name][0] for name in ("pin", "pin2", "pin3", "pin4")] == [-5.0, 20.0, 45.0, 70.0]


def test_an_unconstrained_component_still_exports_and_is_named_as_authored(
    ocp: Any, tmp_path: Path
) -> None:
    """(d) An assembly the solver cannot pin down exports anyway, and says so.

    Only the first component is grounded, so the other three are free with no
    mate to move them: 18 degrees of freedom, `under`, and every one of them
    written where the model authored it. The manifest names both groups, so a
    reader is never left guessing which poses a solve is responsible for.
    """
    kernel = _pin_kernel(4)
    out = tmp_path / "loose.step"
    result = kernel.call("export", {"format": "step", "of": "asm", "out": str(out)})
    place = result["manifest"]["placement"]

    assert result["manifest"]["frame"] == "assembly:main"
    assert result["manifest"]["poses_written"] is True
    assert (place["dof"], place["status"]) == (18, "under")
    assert place["grounded"] == ["pin"]
    assert place["solved"] == []
    assert place["authored"] == ["pin2", "pin3", "pin4"]
    note = place["note_authored"]
    assert "pin2, pin3, pin4 is free and no live mate or joint touches it" in note
    assert "exactly where the model authored it" in note
    rows = {row["name"]: row for row in place["components"]}
    assert rows["pin"]["placed_by"] == "ground"
    assert rows["pin4"]["placed_by"] == "authored"
    assert rows["pin4"]["pose"]["translation"] == [75.0, 0.0, 0.0]
    assert rows["pin4"]["dof"] == 6
    # And the file agrees with the manifest, which is the point of the block.
    assert _boxes(out)["pin4"][0] == 70.0


def test_the_manifest_says_which_component_the_solve_moved(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """The solved case: the housing is grounded, the shaft is the solve's answer."""
    result = shaft_housing.call(
        "export",
        {"format": "step", "of": "asm", "out": str(tmp_path / "a.step"), "roundtrip": False},
    )
    place = result["manifest"]["placement"]
    assert place["assembly"] == "main"
    assert (place["grounded"], place["solved"], place["authored"]) == (["housing"], ["shaft"], [])
    assert (place["dof"], place["status"]) == (1, "over")
    assert "ONE solution" in place["note"]  # a revolute leaves the shaft free to spin
    rows = {row["name"]: row for row in place["components"]}
    assert rows["shaft"]["pose"]["translation"] == [-29.0, 30.0, 30.0]
    assert rows["shaft"]["part"] == "shaft"


# --------------------------------------------------------------------------- (e)


def test_a_bare_part_is_still_written_in_its_own_frame(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """The shipped path is untouched: `of: <part>` means the part's own frame.

    The shaft is instanced at (-29, 30, 30), and exporting `part:shaft` still
    writes it at the origin. This is the invariant that keeps every pinned
    number in the suite and the three examples true, so it is asserted rather
    than assumed.
    """
    out = tmp_path / "shaft.step"
    result = shaft_housing.call(
        "export", {"format": "step", "of": "shaft", "out": str(out), "roundtrip": False}
    )
    assert result["of"] == ["shaft"]
    assert result["manifest"]["frame"] == "part"
    assert result["manifest"]["poses_written"] is False
    assert "placement" not in result["manifest"]
    assert _boxes(out)["shaft"] == [0.0, -15.0, -15.0, 80.0, 15.0, 15.0]


def test_exporting_an_assembly_does_not_move_the_document(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """A document is not changed by exporting it: the pose goes on a COPY.

    `BRepBuilderAPI_Transform(copy=True)` is the reason - bake the pose into
    the part's own shape and the next feature, the next drawing and the next
    fingerprint all inherit a translation nobody asked for.
    """
    from partkiln.brep import shapes

    doc = shaft_housing.document
    before = shapes.bbox(doc.parts["shaft"].shape)
    fingerprint = shaft_housing.fingerprint()
    shaft_housing.call(
        "export",
        {"format": "step", "of": "asm", "out": str(tmp_path / "a.step"), "roundtrip": False},
    )
    assert shapes.bbox(doc.parts["shaft"].shape) == before
    assert shaft_housing.fingerprint() == fingerprint


# --------------------------------------------------------------------------- refusals


def test_a_list_of_of_is_a_list_of_parts_and_says_so(
    shaft_housing: LocalKernel, tmp_path: Path
) -> None:
    """`of: [asm]` refuses with the exact edit, rather than hunting for a part."""
    with pytest.raises(KernelError) as caught:
        shaft_housing.call(
            "export", {"format": "step", "of": ["asm"], "out": str(tmp_path / "x.step")}
        )
    assert caught.value.code == "pk_bad_request"
    assert "on its own" in caught.value.fix


def test_an_assembly_whose_part_has_no_body_refuses(ocp: Any, tmp_path: Path) -> None:
    """A component of an empty part names itself; it does not export a hole in the file."""
    kernel = _pin_kernel(1)
    kernel.apply(
        [
            {"op": "create", "kind": "part", "name": "boss"},
            {"op": "create", "kind": "component", "props": {"part": "boss"}},
        ]
    )
    with pytest.raises(KernelError) as caught:
        kernel.call("export", {"format": "step", "of": "asm", "out": str(tmp_path / "x.step")})
    assert caught.value.code == "pk_ref_empty"
    assert "boss" in str(caught.value)
