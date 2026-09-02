"""P2b acceptance for IGES, BREP, STL, OBJ and 3MF (F1/F5 built with raw OCP)."""

from __future__ import annotations

import time
import zipfile
from pathlib import Path
from typing import Any

import pytest

from partkiln._errors import KernelError

pytestmark = pytest.mark.brep

F1_VOLUME = 59214.602
F5_VOLUME = 520481.421


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


def _f5() -> Any:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt
    from OCP.TopTools import TopTools_ListOfShape

    args = TopTools_ListOfShape()
    args.Append(BRepPrimAPI_MakeBox(220.0, 220.0, 12.0).Shape())
    tools = TopTools_ListOfShape()
    for i in range(10):
        for j in range(10):
            axis = gp_Ax2(gp_Pnt(20.0 + 20 * i, 20.0 + 20 * j, -1.0), gp_Dir(0, 0, 1))
            tools.Append(BRepPrimAPI_MakeCylinder(axis, 4.0, 14.0).Shape())
    cut = BRepAlgoAPI_Cut()
    cut.SetArguments(args)
    cut.SetTools(tools)
    cut.SetRunParallel(True)
    cut.Build()
    return cut.Shape()


def test_counts_are_unique_not_explorer_visits(ocp: Any) -> None:
    """Law 20: F5 has 312 unique edges; the explorer visits 624."""
    from OCP.TopAbs import TopAbs_EDGE
    from OCP.TopExp import TopExp_Explorer

    from partkiln.exchange import count_unique, volume_mm3

    f5 = _f5()
    assert volume_mm3(f5) == pytest.approx(F5_VOLUME, abs=1e-3)
    assert count_unique(f5, "face") == 106
    assert count_unique(f5, "edge") == 312
    visits = 0
    explorer = TopExp_Explorer(f5, TopAbs_EDGE)
    while explorer.More():
        visits += 1
        explorer.Next()
    assert visits == 624
    with pytest.raises(KernelError, match="unknown sub-shape kind"):
        count_unique(f5, "blob")


def test_iges_round_trip(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.iges import read_iges, write_iges

    out = write_iges([("plate", _f1())], tmp_path / "f1.igs")
    assert out["shapes"] == 1 and out["unit"] == "MM" and out["names_written"] is False
    assert out["bytes"] > 1000

    raw = read_iges(out["path"], sew=False)
    assert raw["roots"] == 1
    assert raw["faces"] == 7
    assert raw["solids"] == 0  # IGES carries faces: no solid unless sewn
    assert raw["volume_mm3"] == pytest.approx(F1_VOLUME, rel=1e-6)

    sewn = read_iges(out["path"])
    assert sewn["sewn"] is True
    assert sewn["solids"] == 1
    assert sewn["faces"] == 7
    assert sewn["volume_mm3"] == pytest.approx(F1_VOLUME, rel=1e-6)
    assert sewn["volume_mm3"] > 0

    with pytest.raises(KernelError, match="check the path"):
        read_iges(tmp_path / "missing.igs")


def test_brep_checkpoint_is_small_fast_and_exact(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange import count_unique, volume_mm3
    from partkiln.exchange.brep_io import read_brep, write_brep

    f5 = _f5()
    t0 = time.perf_counter()
    out = write_brep(f5, tmp_path / "f5.brep")
    t_write = time.perf_counter() - t0
    assert out["bytes"] < 100_000, out["bytes"]  # measured 81 KB
    assert out["with_triangles"] is False and out["declares_units"] is False

    t0 = time.perf_counter()
    back = read_brep(out["path"])
    t_read = time.perf_counter() - t0
    # F1 comes back bit-identical; F5 differs by 2.2e-15 relative (one ulp of the 17-digit
    # text form of a cylinder parameter), so "identical" is asserted at 1e-12, not ==
    assert volume_mm3(back) == pytest.approx(volume_mm3(f5), rel=1e-12)
    assert count_unique(back, "face") == 106
    assert count_unique(back, "edge") == 312
    assert t_write < 1.0 and t_read < 1.0  # measured 2 ms / 1 ms

    with_tri = write_brep(f5, tmp_path / "f5_tri.brep", with_triangles=True)
    assert with_tri["bytes"] >= out["bytes"]

    with pytest.raises(KernelError, match="replay the script"):
        read_brep(tmp_path / "gone.brep")


def test_stl_bytes_identical_and_watertight(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.stl import write_stl

    shape = _f1()
    a = write_stl(shape, tmp_path / "a.stl")
    b = write_stl(shape, tmp_path / "b.stl")
    c = write_stl(_f1(), tmp_path / "c.stl")  # a freshly built F1, not the same object
    assert a["watertight"] is True
    assert a["triangles"] > 100
    assert a["declares_units"] is False and a["binary"] is True
    a_bytes = Path(a["path"]).read_bytes()
    assert a_bytes == Path(b["path"]).read_bytes()
    assert a_bytes == Path(c["path"]).read_bytes()
    assert a["bytes"] == 84 + 50 * a["triangles"]  # the binary STL layout

    # coarse first, then fine: the fine file must equal a fresh fine one (Clean_s before meshing)
    write_stl(shape, tmp_path / "coarse.stl", deflection_mm=0.5)
    fine = write_stl(shape, tmp_path / "fine.stl", deflection_mm=0.1)
    assert Path(fine["path"]).read_bytes() == a_bytes

    ascii_out = write_stl(shape, tmp_path / "ascii.stl", binary=False)
    assert ascii_out["watertight"] is True
    assert Path(ascii_out["path"]).read_bytes().startswith(b"solid")

    with pytest.raises(KernelError, match="deflection_mm"):
        write_stl(shape, tmp_path / "bad.stl", deflection_mm=0.0)


def test_obj_reloads_within_a_tenth_of_a_percent(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.obj import read_obj, write_obj

    shape = _f1()
    out = write_obj(shape, tmp_path / "f1.obj")
    assert out["declares_units"] is False
    assert out["watertight"] is True
    back = read_obj(out["path"])
    assert back["watertight"] is True
    assert back["volume"] == pytest.approx(F1_VOLUME, rel=1e-3)
    assert back["extents"] == pytest.approx([100.0, 60.0, 10.0], abs=1e-6)
    again = write_obj(shape, tmp_path / "f1b.obj")
    assert Path(out["path"]).read_bytes() == Path(again["path"]).read_bytes()


def test_3mf_declares_millimetres_and_reloads(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.threemf import read_3mf, write_3mf

    shape = _f1()
    out = write_3mf([("plate", shape)], tmp_path / "f1.3mf")
    assert out["unit"] == "millimeter" and out["declares_units"] is True
    assert out["objects"] == 1 and out["watertight"] is True
    with zipfile.ZipFile(out["path"]) as z:
        assert sorted(z.namelist()) == ["3D/3dmodel.model", "[Content_Types].xml", "_rels/.rels"]
        assert b'unit="millimeter"' in z.read("3D/3dmodel.model")
    back = read_3mf(out["path"])
    assert back["unit"] == "millimeter"
    assert [o["name"] for o in back["objects"]] == ["plate"]
    assert back["objects"][0]["watertight"] is True
    assert back["volume"] == pytest.approx(F1_VOLUME, rel=1e-3)

    again = write_3mf([("plate", shape)], tmp_path / "f1b.3mf")
    assert Path(out["path"]).read_bytes() == Path(again["path"]).read_bytes()

    two = write_3mf([("a", shape), ("b", _f5())], tmp_path / "two.3mf")
    assert two["objects"] == 2
    # 100 d8 holes meshed at 0.1 mm are 0.10 % heavier than the B-rep (chords sit inside
    # every circle), so the two-object file is checked against its own mesh volume at 6 dp
    assert read_3mf(two["path"])["volume"] == pytest.approx(two["volume_mm3"], rel=1e-6)
    assert two["volume_mm3"] == pytest.approx(F1_VOLUME + F5_VOLUME, rel=2e-3)
