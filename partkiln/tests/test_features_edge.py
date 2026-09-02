"""P2c acceptance for fillet and chamfer through the verbs: the measured F1 numbers,
seam exclusion, the design-intent refusals and the per-edge `failed` report."""

from __future__ import annotations

import pytest

from partkiln.document import CommandError

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from test_document_parts import F1, build

pytestmark = pytest.mark.brep

TOP_FRONT = "plate:edges(dir=X, nearest=[50,0,10])"


def test_fillet_r2_on_the_four_verticals_excludes_the_seam() -> None:
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "f1",
            "props": {"edges": "plate:edges(dir=Z)", "r": 2},
        }
    )
    assert r["resolved"] == {"plate:edges(dir=Z)": 4}
    assert r["seam_excluded"] == 1
    assert sorted(r["selected"]["plate:edges(dir=Z)"]) == [
        "plate.side.r.0|plate.side.r.1",
        "plate.side.r.0|plate.side.r.3",
        "plate.side.r.1|plate.side.r.2",
        "plate.side.r.2|plate.side.r.3",
    ]
    assert r["delta_mm3"] == pytest.approx(-34.336, abs=5e-4)
    assert r["faces"] == 11 and r["names"] == [f"f1.face[{k}]" for k in range(4)]
    assert "failed" not in r
    assert doc.parts["plate"].summary()["volume_mm3"] == pytest.approx(59180.266, abs=5e-4)


def test_chamfer_d2_on_the_top_front_edge_is_minus_200() -> None:
    doc = build(F1())
    r = doc.apply(
        {"op": "create", "kind": "chamfer", "name": "c1", "props": {"edges": TOP_FRONT, "d": 2}}
    )
    assert r["selected"] == {TOP_FRONT: ["plate.end|plate.side.r.0"]}
    assert r["delta_mm3"] == pytest.approx(-200.000, abs=5e-4)
    assert r["faces"] == 8 and r["names"] == ["c1.face[0]"]
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "chamfer",
            "name": "c4",
            "props": {"edges": "plate:edges(of=plate.end, loop=outer)", "d": 2},
        }
    )
    # all four top edges: the fixture gives -629.333 / 11 faces (the corners
    # overlap), pinned as measured
    assert r["resolved"] == {"plate:edges(of=plate.end, loop=outer)": 4}
    assert r["delta_mm3"] == pytest.approx(-629.333, abs=5e-3) and r["faces"] == 11
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "chamfer",
            "name": "ca",
            "props": {"edges": TOP_FRONT, "d": [2, 4]},
        }
    )
    assert r["delta_mm3"] == pytest.approx(-400.0, abs=5e-4)
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "chamfer",
            "name": "cg",
            "props": {"edges": TOP_FRONT, "d": {"d": 2, "angle": 45}},
        }
    )
    assert r["delta_mm3"] == pytest.approx(-200.0, abs=5e-4) and r["d_mm"] == [2.0, 2.0]


def test_fillet_r12_on_the_top_front_edge_refuses_naming_edge_and_contours() -> None:
    doc = build(F1())
    before = doc.fingerprint()
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "fillet",
                "name": "big",
                "props": {"edges": TOP_FRONT, "r": 12},
            }
        )
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_op_failed"
    assert "plate.end|plate.side.r.0" in message and "NbFaultyContours=1" in message
    assert "reduce it" in message
    assert doc.fingerprint() == before and len(doc.parts["plate"].features) == 2


def test_fillet_and_chamfer_refuse_without_a_size() -> None:
    doc = build(F1())
    with pytest.raises(CommandError, match="design intent") as excinfo:
        doc.apply({"op": "create", "kind": "fillet", "props": {"edges": "plate:edges(dir=Z)"}})
    assert excinfo.value.code == "pk_needs"
    with pytest.raises(CommandError, match="design intent") as excinfo:
        doc.apply({"op": "create", "kind": "chamfer", "props": {"edges": "plate:edges(dir=Z)"}})
    assert excinfo.value.code == "pk_needs"
    with pytest.raises(CommandError, match="edges") as excinfo:
        doc.apply({"op": "create", "kind": "fillet", "props": {"r": 1}})
    assert excinfo.value.code == "pk_needs"


def test_an_edge_occt_generates_nothing_for_is_reported_failed() -> None:
    """Keeping the seam with `seams` hands OCCT the five raw dir=Z edges; it
    silently generates nothing for the seam (measured), and the diff says so."""
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "f",
            "props": {"edges": "plate:edges(dir=Z, seams)", "r": 2},
        }
    )
    assert r["resolved"] == {"plate:edges(dir=Z, seams)": 5}
    assert "seam_excluded" not in r
    assert r["failed"] == ["hole1.1.wall~seam"]
    assert r["delta_mm3"] == pytest.approx(-34.336, abs=5e-4) and r["faces"] == 11
    assert len(r["names"]) == 4
    with pytest.raises(CommandError, match="only seam edges") as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "fillet",
                "name": "s",
                "props": {"edges": "plate:edges(type=line, of=hole1.1.wall)", "r": 1},
            }
        )
    assert excinfo.value.code == "pk_ref_empty"


def test_variable_fillet_and_edge_names_survive_a_regen() -> None:
    doc = build(F1())
    r = doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "v",
            "props": {"edges": "plate.end|plate.side.r.0", "r": [1, 3]},
        }
    )
    assert r["names"] == ["v.face[0]"] and r["r_mm"] == [1.0, 3.0]
    edit = doc.apply({"op": "set", "id": "feat:plate", "props": {"distance": 12}})
    assert edit["failed"] == []
    assert [c["feature"] for c in edit["changed"]] == ["plate", "hole1"]
    assert edit["unchanged_features"] == ["v"]  # same edge, same rolled volume
    assert doc.parts["plate"].feature("v").selected == {
        "plate.end|plate.side.r.0": ["plate.end|plate.side.r.0"]
    }


def test_stale_edge_after_suppression_refuses_with_candidates_and_a_selector() -> None:
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "chamfer",
            "name": "rim",
            "props": {"edges": "plate.end|hole1.1.wall", "d": 1},
        }
    )
    r = doc.apply({"op": "set", "id": "feat:hole1", "props": {"suppressed": True}})
    assert [f["feature"] for f in r["failed"]] == ["rim"]
    error = r["failed"][0]["error"]
    assert "removed by hole hole1 being suppressed" in error
    assert error.count(" mm away") == 3
    assert "plate:faces(type=cylinder" in error and "nearest=[50,30,5]" in error
    rim = doc.parts["plate"].feature("rim")
    assert rim.status == "failed" and rim.details()["status"] == "failed"
    back = doc.apply({"op": "set", "id": "feat:hole1", "props": {"suppressed": False}})
    assert back["failed"] == [] and doc.parts["plate"].feature("rim").status == "ok"
