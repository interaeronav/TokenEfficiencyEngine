"""P2b acceptance for STEP: schema by request, names through XCAF, the ordering trap pinned.

Fixtures are built with raw OCP here (F1 = 100x60x10 minus a d10 at (50,30),
59 214.602 mm³; F5 = 220x220x12 with 100 d8 holes, 520 481.421 mm³) so this
file depends on nothing but OCP and `partkiln.exchange`.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from partkiln._errors import KernelError

SRC = Path(__file__).resolve().parents[1] / "src"

F1_VOLUME = 59214.602
F5_VOLUME = 520481.421
F8_VOLUME = 5204814.21


def test_exchange_imports_without_ocp() -> None:
    """`import partkiln.exchange.*` must never pull OCP (D1; OCP costs 26 s cold)."""
    code = (
        "import sys, partkiln.exchange, partkiln.exchange.step, partkiln.exchange.iges, "
        "partkiln.exchange.brep_io, partkiln.exchange.stl, partkiln.exchange.obj, "
        "partkiln.exchange.threemf, partkiln.exchange.gltf; "
        "assert 'OCP' not in sys.modules and 'trimesh' not in sys.modules, sorted(sys.modules)"
    )
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    subprocess.run([sys.executable, "-c", code], check=True, env=env)


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


def _translated(shape: Any, dx: float, dy: float) -> Any:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.gp import gp_Trsf, gp_Vec

    trsf = gp_Trsf()
    trsf.SetTranslation(gp_Vec(dx, dy, 0.0))
    return BRepBuilderAPI_Transform(shape, trsf, True).Shape()


def test_f1_ap242_roundtrip_with_name(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.step import SCHEMA_TOKENS, read_step, write_step

    shape = _f1()
    out = write_step([("plate", shape)], tmp_path / "f1.step")
    assert out["schema"] == "AP242"
    assert SCHEMA_TOKENS["AP242"] in out["file_schema"]
    assert out["products"] == 1
    assert out["bytes"] > 1000

    back = read_step(out["path"])
    assert SCHEMA_TOKENS["AP242"] in back["schema"]
    assert (back["unit"], back["unit_source"]) == ("MM", "header")
    assert len(back["products"]) == 1
    product = back["products"][0]
    assert product["name"] == "plate"
    assert product["volume_mm3"] == pytest.approx(F1_VOLUME, abs=1e-3)
    assert product["volume_mm3"] == pytest.approx(F1_VOLUME, rel=1e-8)
    assert product["faces"] == 7
    assert product["solids"] == 1


def test_roundtrip_helper_is_exact_to_1e9(ocp: Any) -> None:
    from partkiln.exchange.step import roundtrip

    result = roundtrip(_f1())
    assert result["volume_ok"] and result["faces_ok"]
    assert result["volume_rel"] <= 1e-9
    assert result["faces_in"] == result["faces_out"] == 7
    assert "AP242_MANAGED" in result["file_schema"]


@pytest.mark.parametrize("schema", ["AP214", "AP203"])
def test_other_schemas_declare_themselves(ocp: Any, tmp_path: Path, schema: str) -> None:
    from partkiln.exchange.step import SCHEMA_TOKENS, read_step, write_step

    out = write_step([("plate", _f1())], tmp_path / f"f1_{schema}.step", schema=schema)
    assert SCHEMA_TOKENS[schema] in out["file_schema"]
    back = read_step(out["path"])
    assert back["products"][0]["volume_mm3"] == pytest.approx(F1_VOLUME, rel=1e-8)


def test_schema_set_after_transfer_stays_ap214(ocp: Any, tmp_path: Path) -> None:
    """The ordering trap, pinned: the schema is captured at the FIRST Transfer."""
    from OCP.Interface import Interface_Static
    from OCP.STEPCAFControl import STEPCAFControl_Writer
    from OCP.STEPControl import STEPControl_AsIs, STEPControl_Controller

    from partkiln.exchange import add_named_shapes, new_xcaf_document, quiet_ocp_messenger
    from partkiln.exchange.step import SCHEMA_TOKENS, file_schema, write_step

    quiet_ocp_messenger()
    STEPControl_Controller.Init_s()
    assert Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    doc = new_xcaf_document()
    add_named_shapes(doc, [("plate", _f1())])
    writer = STEPCAFControl_Writer()
    writer.SetNameMode(True)
    assert writer.Transfer(doc, STEPControl_AsIs)
    assert Interface_Static.SetCVal_s("write.step.schema", "AP242DIS")  # too late
    path = tmp_path / "late.step"
    writer.Write(str(path))
    header = file_schema(path)
    assert SCHEMA_TOKENS["AP214"] in header
    assert SCHEMA_TOKENS["AP242"] not in header

    # and the module is immune: it sets the static before its own fresh writer's Transfer
    out = write_step([("plate", _f1())], tmp_path / "after.step")
    assert SCHEMA_TOKENS["AP242"] in out["file_schema"]


def test_ten_named_f5_plates_round_trip(ocp: Any, tmp_path: Path) -> None:
    """F8: 10 products, 1060 unique faces, volume sum 5 204 814.21, every name back."""
    from partkiln.exchange.step import read_step, write_step

    f5 = _f5()
    shapes = [(f"plate_{k}", _translated(f5, 250.0 * (k % 5), 250.0 * (k // 5))) for k in range(10)]
    t0 = time.perf_counter()
    out = write_step(shapes, tmp_path / "f8.step")
    t_write = time.perf_counter() - t0
    assert out["products"] == 10
    t0 = time.perf_counter()
    back = read_step(out["path"])
    t_read = time.perf_counter() - t0
    products = back["products"]
    assert len(products) == 10
    assert [p["name"] for p in products] == [f"plate_{k}" for k in range(10)]
    assert sum(p["faces"] for p in products) == 1060
    assert all(p["solids"] == 1 for p in products)
    assert round(sum(p["volume_mm3"] for p in products), 2) == F8_VOLUME
    assert products[3]["volume_mm3"] == pytest.approx(F5_VOLUME, abs=1e-3)
    # warm this Mac: 0.17 s / 0.39 s measured; generous ceilings against contention
    assert t_write < 5.0 and t_read < 10.0


def test_inch_file_declares_inch_and_reads_back_in_mm(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.step import declared_unit, read_step, write_step

    out = write_step([("plate", _f1())], tmp_path / "inch.step", unit="INCH")
    assert out["unit"] == "INCH"
    assert declared_unit(out["path"]) == ("INCH", "header")
    back = read_step(out["path"])
    assert back["unit"] == "INCH"
    assert back["products"][0]["volume_mm3"] == pytest.approx(F1_VOLUME, rel=1e-6)


def test_refusals_name_the_fix(ocp: Any, tmp_path: Path) -> None:
    from partkiln.exchange.step import read_step, write_step

    with pytest.raises(KernelError, match="AP203"):
        write_step([("plate", _f1())], tmp_path / "x.step", schema="AP999")
    with pytest.raises(KernelError, match="at least one"):
        write_step([], tmp_path / "x.step")
    with pytest.raises(KernelError, match="check the path"):
        read_step(tmp_path / "missing.step")
    (tmp_path / "junk.step").write_text("not a step file\n")
    with pytest.raises(KernelError, match="not a readable STEP"):
        read_step(tmp_path / "junk.step")


def test_transfer_chatter_stays_off_stdout(ocp: Any, tmp_path: Path, capfd: Any) -> None:
    """The NDJSON worker owns stdout: OCCT's transfer statistics must not print."""
    from partkiln.exchange.step import read_step, write_step

    out = write_step([("plate", _f1())], tmp_path / "quiet.step")
    read_step(out["path"])
    captured = capfd.readouterr()
    assert "Statistics on Transfer" not in captured.out
    assert "Statistics on Transfer" not in captured.err
