"""P5b acceptance: flat-first sheet metal, its numbers, its files and its fold.

The pinned numbers are A66's fixture F7 (T 2, R 2, K 0.44, 90 deg, outside
legs 50 and 30, W 40) and worked example W3 (t 2, width 50, flanges 60 and
40 at 90 deg r 2, two M5 clearance holes):

    F7   BA 4.524 (4.398 at K 0.4, 4.712 at K 0.5), OSSB 4.000, BD 3.476,
         flat 76.524, bend zone 376.991 mm3 - K-independent
    W3   ba 4.524, bd 3.476, flat [96.524, 50], folded bbox [60, 50, 40],
         folded - flat = +18.850 mm3

The tests that need OCCT carry `@pytest.mark.brep` and `importorskip`; every
number above is arithmetic and is checked without it, because a flat pattern
is 2D and the shop can have it while the kernel is still warming (Law 17).
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

import partkiln.sheetmetal.verbs  # noqa: F401 - importing registers create sheet / flat
from partkiln.client import LocalKernel, known_methods
from partkiln.document import CommandError, Document
from partkiln.sheetmetal import flat as F
from partkiln.sheetmetal.fold import Sheet, chain, flat_solid, folded_extents, folded_solid

# F7, re-derived by hand in the A66 script's fixture table.
F7 = {"t": 2.0, "r": 2.0, "angle": 90.0, "width": 40.0, "legs": (50.0, 30.0)}
F7_BA = {0.4: 4.398, 0.44: 4.524, 0.5: 4.712}
F7_OSSB = 4.0
F7_BD = 3.476
F7_FLAT = 76.524
F7_ZONE = 376.991

# W3: the same bend on a 50 mm-wide chain of two flanges.
W3_FLANGES: list[dict[str, Any]] = [
    {"len": 60},
    {"len": 40, "angle": 90, "r": 2, "dir": "up"},
]
W3_FLAT_MM = [96.524, 50.0]
W3_FOLDED_BBOX_MM = [60.0, 50.0, 40.0]
W3_DELTA_MM3 = 18.85
W3_FOLDED_MM3 = 9671.239  # = 9200 + one 471.239 mm3 sector: K-free (see below)


@pytest.fixture
def w3() -> F.Flat:
    return F.Flat.from_flanges(2.0, 50.0, W3_FLANGES, F.DEFAULT_K)


def _sheet_op(**props: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"t": 2, "width": 50, "flanges": W3_FLANGES}
    base.update(props)
    return {"op": "create", "kind": "sheet", "name": "brk", "props": base}


# --------------------------------------------------------------------------- the formulas


def test_f7_bend_allowance_setback_and_deduction() -> None:
    ba = F.bend_allowance(F7["angle"], F7["r"], F7["t"], 0.44)
    assert round(ba, 3) == F7_BA[0.44]
    assert round(F.outside_setback(F7["angle"], F7["r"], F7["t"]), 3) == F7_OSSB
    assert round(F.bend_deduction(F7["angle"], F7["r"], F7["t"], 0.44), 3) == F7_BD
    # BD = 2*OSSB - BA is a definition, not a second measurement.
    assert F.bend_deduction(90, 2, 2, 0.44) == pytest.approx(2 * F7_OSSB - ba, abs=1e-12)


@pytest.mark.parametrize("k", [0.4, 0.44, 0.5])
def test_bend_allowance_is_parametrised_by_k(k: float) -> None:
    """K is the ONE modelling choice in the formula, so it is a parameter, and
    the default 0.44 has no more standing than 0.4 or 0.5 - it is just ours."""
    assert round(F.bend_allowance(90, 2, 2, k), 3) == F7_BA[k]
    assert F.bend_allowance(90, 2, 2, k) == pytest.approx(math.pi / 2 * (2 + k * 2), abs=1e-12)


def test_f7_flat_length_of_an_l_from_its_outside_legs() -> None:
    assert round(F.flat_length(F7["legs"], 90, 2, 2, 0.44), 3) == F7_FLAT
    assert round(F.flat_length(F7["legs"], 90, 2, 2, 0.4), 3) == 76.398
    assert round(F.flat_length(F7["legs"], 90, 2, 2, 0.5), 3) == 76.712


def test_bend_zone_volume_is_k_independent() -> None:
    """The folded bend zone is an annular sector: geometry, with no K in it.

    K says where the neutral fibre is, which is a statement about the FLAT.
    The equality below is exact, not approximate, because `bend_zone_volume`
    takes no k at all - and that is the point being pinned.
    """
    zone = F.bend_zone_volume(90, 2, 2, F7["width"])
    assert round(zone, 3) == F7_ZONE
    assert round(zone, 1) == 377.0
    low = F.Bend("b", ((0.0, 40.0), (0.0, 0.0)), 90, 2, 2, 0.4, "up")
    high = F.Bend("b", ((0.0, 40.0), (0.0, 0.0)), 90, 2, 2, 0.5, "up")
    assert low.zone_volume == high.zone_volume == zone
    # The flat strip it replaces is NOT K-independent - that is the difference.
    assert low.strip_volume != high.strip_volume
    assert round(high.strip_volume, 3) == round(zone, 3)  # K = 0.5 is the break-even


@pytest.mark.parametrize(
    ("kwargs", "wanted"),
    [
        ({"angle_deg": 0.0}, "not in (0, 180)"),
        ({"angle_deg": 180.0}, "hem"),
        ({"t": 0.0}, "must be > 0"),
        ({"r_inner": -1.0}, "must be >= 0"),
        ({"k": 1.5}, "DIN 6935"),
    ],
)
def test_check_bend_refuses_and_names_the_fix(kwargs: dict[str, Any], wanted: str) -> None:
    args = {"angle_deg": 90.0, "r_inner": 2.0, "t": 2.0, "k": 0.44}
    args.update(kwargs)
    with pytest.raises(CommandError) as excinfo:
        F.check_bend(**args)
    assert wanted in str(excinfo.value)
    assert excinfo.value.code == "pk_needs"


def test_the_k_default_is_declared_not_standard() -> None:
    assert F.DEFAULT_K == 0.44
    assert F.K_TYPICAL[0] < F.DEFAULT_K < F.K_TYPICAL[1]
    assert "no standard fixes K" in F.K_NOTE
    assert "CC BY-SA 4.0" in F.FORMULA_SOURCE and "Industrial Press 1994" in F.FORMULA_SOURCE


# --------------------------------------------------------------------------- the flat model


def test_w3_flat_extents_and_volumes(w3: F.Flat) -> None:
    summary = w3.summary()
    assert summary["flat_mm"] == W3_FLAT_MM
    assert summary["ba_total_mm"] == 4.524
    assert summary["bd_total_mm"] == 3.476
    assert summary["volume_delta_mm3"] == W3_DELTA_MM3
    assert summary["folded_volume_mm3"] == W3_FOLDED_MM3
    assert [f.name for f in w3.flanges] == ["f1", "f2"]
    assert (w3.flanges[0].flat_start, w3.flanges[0].flat_end) == (0.0, 56.0)


def test_a_flange_shorter_than_its_setbacks_refuses_by_name() -> None:
    with pytest.raises(CommandError) as excinfo:
        F.Flat.from_flanges(2.0, 50.0, [{"len": 60}, {"len": 3, "angle": 90, "r": 2}], 0.44)
    assert "flange f2" in str(excinfo.value) and "outside setbacks" in str(excinfo.value)


def test_the_folded_volume_of_a_chain_is_k_free_but_the_blank_is_not() -> None:
    """K moves the BLANK, not the part: the flat length changes with K, the
    folded part does not (its flanges are set by OSSB and its bend zone by
    geometry). W3: 9 671.239 mm3 at K 0.4 and at K 0.5 alike."""
    lengths, volumes = set(), set()
    for k in (0.4, 0.44, 0.5):
        sheet = F.Flat.from_flanges(2.0, 50.0, W3_FLANGES, k)
        lengths.add(round(sheet.extents()[0], 6))
        volumes.add(round(sheet.folded_volume(), 6))
    assert len(lengths) == 3
    assert volumes == {round(9200.0 + F.bend_zone_volume(90, 2, 2, 50.0), 6)}


def test_a_hole_in_a_bend_zone_refuses_naming_the_zone(w3: F.Flat) -> None:
    with pytest.raises(CommandError) as excinfo:
        w3.add_hole(5.5, (58.0, 25.0))
    assert "bend zone of b1" in str(excinfo.value) and "0..4.524" in str(excinfo.value)


def test_a_hole_off_its_flange_refuses_naming_the_bounds(w3: F.Flat) -> None:
    with pytest.raises(CommandError) as excinfo:
        w3.add_hole(5.5, (34.0, 25.0), "f2")
    assert "leaves flange f2" in str(excinfo.value)
    # f1 ends AT the bend line, so its far bound is the zone's: that message wins.
    with pytest.raises(CommandError) as excinfo:
        w3.add_hole(5.5, (55.0, 25.0), "f1")
    assert "bend zone of b1" in str(excinfo.value)
    with pytest.raises(CommandError) as excinfo:
        w3.add_hole(5.5, (5.0, 25.0), "f9")
    assert excinfo.value.code == "pk_ref_unknown"


def test_relief_notches_shorten_the_bend_and_the_outline(w3: F.Flat) -> None:
    relieved = F.Flat.from_flanges(2.0, 50.0, W3_FLANGES, 0.44, {"width": 3.0, "extra": 1.0})
    assert relieved.bends[0].length == 44.0  # 50 - 2 x 3
    assert len(relieved.outline) > len(w3.outline)
    assert relieved.area() < w3.area()
    with pytest.raises(CommandError) as excinfo:
        F.Flat.from_flanges(2.0, 50.0, W3_FLANGES, 0.44, {"width": 30.0})
    assert "half the sheet width" in str(excinfo.value)


# --------------------------------------------------------------------------- the files


def test_dxf_has_the_four_layers_and_says_millimetres(w3: F.Flat, tmp_path: Path) -> None:
    ezdxf = pytest.importorskip("ezdxf")
    w3.add_hole(5.5, (15.0, 25.0), "f1")
    out = w3.write_dxf(tmp_path / "brk.dxf")
    assert out["insunits"] == F.DXF_INSUNITS_MM == 4
    assert out["units"] == "mm" and out["declares_units"] is True
    assert out["layers"] == list(F.DXF_LAYERS) == ["OUTLINE", "BEND_UP", "BEND_DOWN", "HOLES"]
    assert out["entities"] == {"OUTLINE": 1, "BEND_UP": 1, "BEND_DOWN": 0, "HOLES": 1}
    doc = ezdxf.readfile(out["path"])
    assert doc.header["$INSUNITS"] == 4
    assert set(F.DXF_LAYERS) <= {layer.dxf.name for layer in doc.layers}
    msp = doc.modelspace()
    outline = msp.query("LWPOLYLINE")[0]
    assert outline.dxf.layer == "OUTLINE" and outline.closed
    (circle,) = msp.query("CIRCLE")
    assert circle.dxf.layer == "HOLES" and circle.dxf.radius == pytest.approx(2.75)
    (line,) = msp.query("LINE")
    # The bend line a brake operator marks is the middle of the zone, not its edge.
    assert line.dxf.layer == "BEND_UP"
    assert line.dxf.start.x == pytest.approx(56.0 + 4.5238934 / 2, abs=1e-6)


def test_a_down_bend_lands_on_the_bend_down_layer(tmp_path: Path) -> None:
    down = F.Flat.from_flanges(
        2.0, 50.0, [{"len": 60}, {"len": 40, "angle": 90, "r": 2, "dir": "down"}], 0.44
    )
    out = down.write_dxf(tmp_path / "down.dxf")
    assert out["entities"]["BEND_DOWN"] == 1 and out["entities"]["BEND_UP"] == 0


def test_dxf_and_svg_are_byte_identical_on_repeat(w3: F.Flat, tmp_path: Path) -> None:
    """Law 7. ezdxf stamps a fresh $VERSIONGUID and $TDUPDATE on every save
    unless its fixed-metadata option is set; write_dxf sets it and restores it."""
    for name, write in (("brk.dxf", w3.write_dxf), ("brk.svg", w3.write_svg)):
        first = Path(write(tmp_path / f"a-{name}")["path"]).read_bytes()
        second = Path(write(tmp_path / f"b-{name}")["path"]).read_bytes()
        assert first == second


def test_svg_is_one_user_unit_per_millimetre(w3: F.Flat, tmp_path: Path) -> None:
    from xml.etree import ElementTree

    out = w3.write_svg(tmp_path / "brk.svg")
    root = ElementTree.parse(out["path"]).getroot()
    assert root.get("width") == "96.524mm" and root.get("height") == "50.000mm"
    assert root.get("viewBox") == "0 0 96.524 50.000"
    groups = {g.get("id") for g in root.iter("{http://www.w3.org/2000/svg}g")}
    assert groups == set(F.DXF_LAYERS)


# --------------------------------------------------------------------------- the verb


def test_create_sheet_returns_the_d7_row_and_declares_its_defaults() -> None:
    doc = Document()
    out = doc.apply(_sheet_op(material="steel_s275"))
    assert out["id"] == "sheet:brk" and out["kind"] == "sheet"
    assert out["t"] == 2.0 and out["k"] == 0.44 and out["bends"] == 1
    assert out["flat_mm"] == W3_FLAT_MM
    assert out["folded_bbox_mm"] == W3_FOLDED_BBOX_MM
    assert out["ba_total_mm"] == 4.524 and out["bd_total_mm"] == 3.476
    assert out["volume_delta_mm3"] == W3_DELTA_MM3
    assert out["mass_g"] == pytest.approx(75.919, abs=5e-4)
    assert out["assumed"]["k"] == 0.44
    assert any("no standard fixes K" in note for note in out["notes"])
    assert any("annular sector" in note for note in out["notes"])
    assert doc.sheets["brk"].material == "steel_s275"


def test_create_sheet_defaults_r_to_t_and_the_angle_to_90() -> None:
    doc = Document()
    out = doc.apply(_sheet_op(flanges=[{"len": 60}, {"len": 40}]))
    assert out["assumed"]["bend_r"] == "r = t"
    assert out["assumed"]["bend_angle"] == "90deg"
    assert out["assumed"]["bend_dir"] == "up"
    assert doc.sheets["brk"].flat.bends[0].r_inner == 2.0


def test_create_sheet_takes_units_params_and_expressions() -> None:
    doc = Document()
    doc.apply({"op": "param_set", "props": {"T": "2mm", "L": "60mm"}})
    doc.apply(_sheet_op(t="T", width="5cm", flanges=[{"len": "L"}, {"len": "L - 20mm", "r": "T"}]))
    sheet = doc.sheets["brk"]
    assert sheet.flat.t == 2.0
    assert sheet.summary()["flat_mm"] == W3_FLAT_MM


def test_create_sheet_holes_from_a_standard_and_from_a_diameter() -> None:
    doc = Document()
    out = doc.apply(
        _sheet_op(
            holes=[
                {"flange": "f1", "at": [15, 25], "std": "M5 clearance normal"},
                {"flange": "f2", "at": [15, 25], "dia": "5.5mm"},
            ]
        )
    )
    assert out["holes"] == 2
    holes = doc.sheets["brk"].flat.holes
    assert [h.dia for h in holes] == [5.5, 5.5]
    assert holes[0].centre == (15.0, 25.0)  # f1's flat portion starts at x = 0
    assert holes[1].centre[0] == pytest.approx(60.5238934 + 15.0, abs=1e-6)
    assert any("ISO 273" in note for note in out["notes"])


@pytest.mark.parametrize(
    ("props", "code", "wanted"),
    [
        ({"t": None}, "pk_needs", "needs t"),
        ({"width": None}, "pk_needs", "needs width"),
        ({"flanges": []}, "pk_needs", "non-empty list"),
        ({"flanges": [{"len": 60, "angle": 90}]}, "pk_spec_conflict", "flange f1 is the base"),
        ({"flanges": [{"len": 60}, {"len": 40, "dir": "sideways"}]}, "pk_needs", "'up' or 'down'"),
        ({"flanges": [{"len": 60}, {"length": 40}]}, "pk_bad_op", "unknown field(s) length"),
        ({"k": 1.5}, "pk_needs", "DIN 6935"),
        ({"holes": [{"flange": "f1", "at": [15, 25]}]}, "pk_needs", "needs dia"),
        (
            {"holes": [{"flange": "f1", "at": [15, 25], "dia": 5, "std": "M5 clearance"}]},
            "pk_spec_conflict",
            "dia OR std",
        ),
        ({"holes": [{"flange": "f1", "at": 15, "dia": 5}]}, "pk_needs", "at is [x, y]"),
        ({"relief": {"wide": 3}}, "pk_bad_op", "unknown field(s) wide"),
    ],
)
def test_create_sheet_refusals_name_the_reason_and_the_fix(
    props: dict[str, Any], code: str, wanted: str
) -> None:
    doc = Document()
    op = _sheet_op(**props)
    for key, value in props.items():
        if value is None:
            op["props"].pop(key)
    with pytest.raises(CommandError) as excinfo:
        doc.apply(op)
    assert excinfo.value.code == code
    assert wanted in str(excinfo.value)
    assert doc.sheets == {}  # Law 16: a refused command leaves nothing behind


def test_an_unusual_k_is_noted_not_refused() -> None:
    """0 < k < 1 is arithmetically fine and a shop that measured 0.25 is right;
    only a k that is not a neutral-axis fraction at all is refused."""
    out = Document().apply(_sheet_op(k=0.25))
    assert out["k"] == 0.25
    assert any("outside the typical 0.3-0.5 range" in note for note in out["notes"])


def test_the_sheet_is_an_entity_row_and_a_detail() -> None:
    doc = Document()
    doc.apply(_sheet_op(material="steel_s275"))
    rows = {row["id"]: row for row in doc.entities()}
    assert "sheet:brk" in rows
    assert rows["sheet:brk"]["kind"] == "sheet"
    assert rows["doc"]["sheets"] == 1
    detail = doc.detail("sheet:brk")
    assert [b["name"] for b in detail["bend_rows"]] == ["b1"]
    assert detail["bend_rows"][0]["ba_mm"] == 4.524
    assert detail["bend_rows"][0]["zone_volume_mm3"] == 471.239
    assert any("annular sector" in note for note in detail["notes"])


def test_a_sheet_replays_to_the_same_numbers(tmp_path: Path) -> None:
    doc = Document()
    doc.apply(_sheet_op(material="steel_s275", holes=[{"flange": "f1", "at": [15, 25], "dia": 5}]))
    again = Document.replay(doc.script())
    assert again.sheets["brk"].fingerprint() == doc.sheets["brk"].fingerprint()
    assert again.sheets["brk"].summary() == doc.sheets["brk"].summary()
    thicker = Document.replay(doc.script(), overrides=None)
    assert thicker.fingerprint() == doc.fingerprint()


# --------------------------------------------------------------------------- the flat method


def test_the_flat_method_is_on_the_kernel_and_writes_both_files(tmp_path: Path) -> None:
    doc = Document()
    doc.apply(_sheet_op(holes=[{"flange": "f1", "at": [15, 25], "std": "M5 clearance normal"}]))
    kernel = LocalKernel(doc)
    assert "flat" in known_methods()
    out = kernel.call("flat", {"out": str(tmp_path / "brk")})
    assert out["id"] == "sheet:brk" and out["flat_mm"] == W3_FLAT_MM
    assert sorted(out["files"]) == ["dxf", "svg"]
    assert out["layers"] == list(F.DXF_LAYERS)
    assert out["files"]["dxf"]["insunits"] == 4
    assert Path(out["files"]["dxf"]["path"]).name == "brk.dxf"
    assert Path(out["files"]["svg"]["path"]).exists()
    only = kernel.call("flat", {"out": str(tmp_path / "one.dxf"), "formats": "dxf"})
    assert sorted(only["files"]) == ["dxf"]
    assert Path(only["files"]["dxf"]["path"]).name == "one.dxf"


def test_export_format_dxf_of_a_sheet_routes_here(tmp_path: Path) -> None:
    """`methods.m_export` sends `export format=dxf of=<sheet>` to this method
    with the SINGULAR `format`, so both lanes write one file from one path."""
    doc = Document()
    doc.apply(_sheet_op())
    out = LocalKernel(doc).call(
        "export", {"format": "dxf", "of": "sheet:brk", "out": str(tmp_path / "brk.dxf")}
    )
    assert out["format"] == "dxf" and out["id"] == "sheet:brk"
    assert Path(out["path"]).name == "brk.dxf" and out["bytes"] > 0
    assert sorted(out["files"]) == ["dxf"]
    assert out["layers"] == list(F.DXF_LAYERS)


@pytest.mark.parametrize(
    ("params", "code", "wanted"),
    [
        ({}, "pk_needs", "flat needs out"),
        ({"out": "x", "formats": ["pdf"]}, "pk_bad_op", "flat writes dxf and svg"),
        ({"out": "x", "sheet": "nope"}, "pk_ref_unknown", "no sheet"),
    ],
)
def test_the_flat_method_refuses_with_the_fix(
    params: dict[str, Any], code: str, wanted: str, tmp_path: Path
) -> None:
    doc = Document()
    doc.apply(_sheet_op())
    if "out" in params:
        params = {**params, "out": str(tmp_path / str(params["out"]))}
    with pytest.raises(CommandError) as excinfo:
        LocalKernel(doc).call("flat", params)
    assert excinfo.value.code == code and wanted in str(excinfo.value)


def test_the_flat_method_refuses_when_there_is_no_sheet() -> None:
    with pytest.raises(CommandError) as excinfo:
        LocalKernel(Document()).call("flat", {"out": "x"})
    assert excinfo.value.code == "pk_ref_empty"


# --------------------------------------------------------------------------- import hygiene


def test_create_sheet_resolves_through_the_documents_lazy_loader() -> None:
    """A cold process must reach `create sheet` with no import of its own:
    `document._VERB_MODULES` names `partkiln.sheetmetal.verbs` and imports it
    the first time a create names a kind the document does not know."""
    code = (
        "from partkiln.document import Document;"
        "d = Document();"
        "r = d.apply({'op': 'create', 'kind': 'sheet', 'name': 'brk', 'props':"
        " {'t': 2, 'width': 50, 'flanges': [{'len': 60}, {'len': 40}]}});"
        "print(r['flat_mm'], r['folded_bbox_mm'])"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(Path(__file__).resolve().parents[1]),
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
    )
    assert proc.stdout.strip() == "[96.524, 50.0] [60.0, 50.0, 40.0]"


def test_importing_sheet_metal_loads_no_ocp() -> None:
    """A flat pattern is 2D: the package that computes one must not drag in a
    26 s cold B-rep import (Law 17), and `create sheet` must work without it."""
    code = (
        "import sys, partkiln.sheetmetal, partkiln.sheetmetal.verbs, partkiln.handoff;"
        "loaded = sorted(m for m in ('OCP', 'cadquery', 'tee') if m in sys.modules);"
        "print(loaded)"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(Path(__file__).resolve().parents[1]),
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"},
    )
    assert proc.stdout.strip() == "[]"


# --------------------------------------------------------------------------- the fold (OCCT)


@pytest.fixture(scope="module")
def ocp() -> Any:
    return pytest.importorskip("OCP", reason="partkiln[brep] not installed")


@pytest.mark.brep
def test_w3_folds_to_the_arithmetic(ocp: Any, w3: F.Flat) -> None:
    """The exact B-rep volume of the folded body equals the arithmetic of
    flat.py, and its bounding box equals the analytic one - which is what
    makes `folded_bbox_mm` safe to report with no kernel present."""
    from partkiln.brep import shapes

    solid = folded_solid(w3)
    assert shapes.is_valid(solid)
    assert shapes.counts(solid) == {"solids": 1, "faces": 10, "edges": 24, "vertices": 16}
    assert shapes.volume(solid) == pytest.approx(w3.folded_volume(), rel=1e-12)
    assert round(shapes.volume(solid), 3) == W3_FOLDED_MM3
    lo = shapes.bbox(solid)
    measured = [lo[i + 3] - lo[i] for i in range(3)]
    assert measured == pytest.approx(W3_FOLDED_BBOX_MM, abs=1e-9)
    assert list(folded_extents(w3)) == pytest.approx(measured, abs=1e-9)


@pytest.mark.brep
def test_the_flat_body_is_the_blank_and_the_difference_is_the_k_factor(
    ocp: Any, w3: F.Flat
) -> None:
    from partkiln.brep import shapes

    blank = flat_solid(w3)
    assert shapes.volume(blank) == pytest.approx(w3.flat_volume(), rel=1e-12)
    assert round(shapes.volume(folded_solid(w3)) - shapes.volume(blank), 3) == W3_DELTA_MM3
    assert "annular sector" in w3.volume_note() and "0 at K = 0.5" in w3.volume_note()


@pytest.mark.brep
@pytest.mark.parametrize("k", [0.4, 0.5])
def test_the_folded_solid_is_k_independent(ocp: Any, k: float) -> None:
    """Measured on the solid, not only in the arithmetic: the bend zone is an
    annular sector, so the folded body has the same volume at K 0.4 and 0.5
    while the blank it is cut from does not."""
    from partkiln.brep import shapes

    sheet = F.Flat.from_flanges(2.0, 50.0, W3_FLANGES, k)
    assert shapes.volume(folded_solid(sheet)) == pytest.approx(W3_FOLDED_MM3, abs=1e-3)
    assert shapes.volume(flat_solid(sheet)) != pytest.approx(9652.389, abs=1e-3)


@pytest.mark.brep
@pytest.mark.parametrize(
    ("label", "flanges", "relief", "bbox"),
    [
        (
            "down",
            [{"len": 60}, {"len": 40, "angle": 90, "r": 2, "dir": "down"}],
            None,
            [60, 50, 40],
        ),
        (
            "u_channel",
            [
                {"len": 30},
                {"len": 80, "angle": 90, "r": 2, "dir": "up"},
                {"len": 30, "angle": 90, "r": 2, "dir": "up"},
            ],
            None,
            [30, 50, 80],
        ),
        (
            "z_channel",
            [
                {"len": 30},
                {"len": 80, "angle": 90, "r": 2, "dir": "up"},
                {"len": 30, "angle": 90, "r": 2, "dir": "down"},
            ],
            None,
            [58, 50, 80],
        ),
        ("obtuse", [{"len": 60}, {"len": 40, "angle": 120, "r": 2}], None, [57.0718, 50, 34.641]),
        (
            "relieved",
            W3_FLANGES,
            {"width": 3, "extra": 1},
            [60, 50, 40],
        ),
    ],
)
def test_every_chain_folds_to_its_own_arithmetic(
    ocp: Any,
    label: str,
    flanges: list[dict[str, Any]],
    relief: dict[str, Any] | None,
    bbox: list[float],
) -> None:
    """`dir` is read in each flange's own frame: up/up folds a U, up/down a Z."""
    from partkiln.brep import shapes

    sheet = F.Flat.from_flanges(2.0, 50.0, flanges, 0.44, relief)
    solid = folded_solid(sheet)
    assert shapes.is_valid(solid), label
    assert shapes.volume(solid) == pytest.approx(sheet.folded_volume(), rel=1e-9), label
    lo = shapes.bbox(solid)
    assert [lo[i + 3] - lo[i] for i in range(3)] == pytest.approx(bbox, abs=1e-4), label
    assert list(folded_extents(sheet)) == pytest.approx(bbox, abs=1e-4), label


@pytest.mark.brep
def test_holes_go_through_both_bodies_in_the_same_place(ocp: Any, w3: F.Flat) -> None:
    from partkiln.brep import shapes

    plain = shapes.volume(folded_solid(w3))
    w3.add_hole(5.5, (15.0, 25.0), "f1")
    w3.add_hole(5.5, (15.0, 25.0), "f2")
    drilled = folded_solid(w3)
    removed = 2 * math.pi * 2.75**2 * 2.0
    assert plain - shapes.volume(drilled) == pytest.approx(removed, rel=1e-6)
    assert shapes.volume(flat_solid(w3)) == pytest.approx(w3.flat_volume(), rel=1e-9)
    # The f2 hole came round the bend with its flange: it is a vertical wall now.
    lo = shapes.bbox(drilled)
    assert [lo[i + 3] - lo[i] for i in range(3)] == pytest.approx(W3_FOLDED_BBOX_MM, abs=1e-9)


@pytest.mark.brep
def test_a_sheet_with_no_bends_folds_to_its_own_blank(ocp: Any) -> None:
    from partkiln.brep import shapes

    plate = F.Flat.from_flanges(2.0, 50.0, [{"len": 60}], 0.44)
    assert plate.bends == []
    assert list(folded_extents(plate)) == pytest.approx([60.0, 50.0, 2.0], abs=1e-9)
    assert shapes.volume(folded_solid(plate)) == pytest.approx(shapes.volume(flat_solid(plate)))


@pytest.mark.brep
def test_the_sheet_entity_hands_back_both_bodies(ocp: Any, w3: F.Flat) -> None:
    from partkiln.brep import shapes

    sheet = Sheet("brk", w3, "steel_s275", 0.44)
    assert shapes.volume(sheet.solid("folded")) == pytest.approx(w3.folded_volume(), rel=1e-9)
    assert shapes.volume(sheet.solid()) == pytest.approx(w3.folded_volume(), rel=1e-9)
    assert shapes.volume(sheet.solid("flat")) == pytest.approx(w3.flat_volume(), rel=1e-9)
    with pytest.raises(CommandError) as excinfo:
        sheet.solid("exploded")
    assert excinfo.value.code == "pk_bad_op"
    assert sheet.summary()["mass_g"] == pytest.approx(75.919, abs=5e-4)


def test_a_slanted_bend_line_is_refused_not_guessed() -> None:
    """The fold folds the chain `create sheet` lays out; anything else refuses
    by name rather than producing something that is nearly right."""
    bend = F.Bend("b1", ((0.0, 0.0), (40.0, 40.0)), 90, 2, 2, 0.44, "up")
    hand_built = F.Flat(2.0, [(0.0, 0.0), (80.0, 0.0), (80.0, 40.0), (0.0, 40.0)], [bend])
    with pytest.raises(CommandError) as excinfo:
        chain(hand_built)
    assert "create sheet" in str(excinfo.value) and excinfo.value.code == "pk_needs"
