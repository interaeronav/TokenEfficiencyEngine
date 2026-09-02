"""P2b acceptance for GLB: metres AND Y-up by instruction, both negatives kept visible."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from partkiln._errors import KernelError

pytestmark = pytest.mark.brep


@pytest.fixture(scope="module")
def ocp() -> Any:
    return pytest.importorskip("OCP", reason="partkiln[brep] not installed")


def _f1() -> Any:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

    box = BRepPrimAPI_MakeBox(100.0, 60.0, 10.0).Shape()
    axis = gp_Ax2(gp_Pnt(50.0, 30.0, -1.0), gp_Dir(0.0, 0.0, 1.0))
    cyl = BRepPrimAPI_MakeCylinder(axis, 5.0, 12.0).Shape()
    return BRepAlgoAPI_Cut(box, cyl).Shape()


def _probe(path: str) -> dict[str, Any] | None:
    """TEE's own reader when it is importable (tests only; src never imports tee)."""
    try:
        from tee.assets.gltf import probe
    except ImportError:
        return None
    return probe(Path(path))


def test_glb_is_metres_and_y_up(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.gltf import read_back, write_glb

    out = write_glb([("plate", _f1())], tmp_path / "f1.glb")
    assert out["units"] == "m" and out["up"] == "Y" and out["merged"] is True
    assert out["meshes"] == 1
    assert out["extents"] == pytest.approx([0.1, 0.01, 0.06], abs=1e-6)
    back = read_back(out["path"])
    assert back["names"] == ["plate"]
    assert back["triangles"] > 100
    probed = _probe(out["path"])
    if probed is not None:
        assert probed["extents_m"] == pytest.approx([0.1, 0.01, 0.06], abs=1e-6)
        assert probed["dims_zup_m"] == pytest.approx([0.1, 0.06, 0.01], abs=1e-6)
        assert probed["meshes"] == 1
        assert probed["units"] == "m"


def test_glb_without_length_unit_is_a_thousand_times_too_big(ocp: Any, tmp_path: Path) -> None:
    """The first trap: no `SetLengthUnit_s(doc, 0.001)` and 10 mm becomes 10 m."""
    from partkiln.exchange.gltf import write_glb

    out = write_glb([("plate", _f1())], tmp_path / "no_unit.glb", metres=False)
    assert out["units"] == "mm"
    assert out["extents"] == pytest.approx([100.0, 10.0, 60.0], abs=1e-6)


def test_glb_without_zup_input_lies_on_its_side(ocp: Any, tmp_path: Path) -> None:
    """The second trap: no Z-up input coordinate system and the writer rotates nothing."""
    from partkiln.exchange.gltf import write_glb

    out = write_glb([("plate", _f1())], tmp_path / "no_rot.glb", y_up=False)
    assert out["up"] == "Z"
    assert out["extents"] == pytest.approx([0.1, 0.06, 0.01], abs=1e-6)


def test_glb_merge_faces_gives_one_mesh(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.gltf import write_glb

    merged = write_glb([("plate", _f1())], tmp_path / "merged.glb")
    split = write_glb([("plate", _f1())], tmp_path / "split.glb", merge_faces=False)
    assert merged["meshes"] == 1
    assert split["meshes"] == 7  # one per face of F1
    assert split["extents"] == pytest.approx(merged["extents"], abs=1e-6)


def test_glb_bytes_identical_on_repeat_and_names_carry(ocp: Any, tmp_path: Path) -> None:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf, gp_Vec

    from partkiln.exchange.gltf import read_back, write_glb

    shape = _f1()
    a = write_glb([("plate", shape)], tmp_path / "a.glb")
    b = write_glb([("plate", _f1())], tmp_path / "b.glb")
    assert Path(a["path"]).read_bytes() == Path(b["path"]).read_bytes()

    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(150.0, 0.0, 0.0))
    moved = BRepBuilderAPI_Transform(shape, trsf, True).Shape()
    two = write_glb([("left", shape), ("right", moved)], tmp_path / "two.glb")
    assert two["meshes"] == 2
    assert read_back(two["path"])["names"] == ["left", "right"]
    assert two["extents"] == pytest.approx([0.25, 0.01, 0.06], abs=1e-6)

    with pytest.raises(KernelError, match="at least one"):
        write_glb([], tmp_path / "none.glb")
