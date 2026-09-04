"""P2c acceptance for naming.py: the NameTable (no OCP), the selector grammar, and
resolution on F1 (names, history, fingerprint, the refusals with candidates)."""

from __future__ import annotations

import pytest

from partkiln.document import CommandError, Document
from partkiln.naming import (
    NameEntry,
    NameTable,
    Selector,
    is_selector,
    keys_match,
    materialise,
    survivor_selector,
)

# -- pure Python ----------------------------------------------------------------------------


def test_name_table_round_trips_scalars() -> None:
    table = NameTable()
    table.add(
        NameEntry(
            "plate.end",
            "face",
            "plate",
            "end",
            0,
            ("plane", 6000.0, (50.0, 30.0, 10.0), (0.0, 0.0, 1.0), None),
        )
    )
    table.add(
        NameEntry(
            "h.1.wall",
            "face",
            "h",
            "1.wall",
            1,
            ("cylinder", 314.159, (50.0, 30.0, 5.0), None, 5.0),
        )
    )
    raw = table.as_dict()
    assert raw["plate.end"] == {
        "kind": "face",
        "feature": "plate",
        "role": "end",
        "index": 0,
        "key": ["plane", 6000.0, (50.0, 30.0, 10.0), (0.0, 0.0, 1.0), None],
    }
    twin = NameTable.from_dict(raw)
    assert twin.names() == ["h.1.wall", "plate.end"]
    assert twin.get("h.1.wall").key == ("cylinder", 314.159, (50.0, 30.0, 5.0), None, 5.0)
    assert [e.name for e in twin.of_feature("h")] == ["h.1.wall"]
    dropped = twin.drop_feature("h")
    assert [e.name for e in dropped] == ["h.1.wall"] and "h.1.wall" not in twin
    assert [e.name for e in twin.drop_from(0)] == ["plate.end"] and len(twin) == 0


def test_keys_match_within_1e_3_and_not_across_types() -> None:
    a = ("plane", 6000.0, (50.0, 30.0, 10.0), (0.0, 0.0, 1.0), None)
    assert keys_match(a, ("plane", 6000.0005, (50.0, 30.0, 10.0009), (0.0, 0.0, 1.0), None))
    assert not keys_match(a, ("plane", 6000.0, (50.0, 30.0, 10.002), (0.0, 0.0, 1.0), None))
    assert not keys_match(a, ("cylinder", 6000.0, (50.0, 30.0, 10.0), (0.0, 0.0, 1.0), None))
    assert not keys_match(a, ("plane", 6000.0, (50.0, 30.0, 10.0), (0.0, 0.0, -1.0), None))


def test_selector_grammar_parses_and_refuses() -> None:
    sel = Selector("plate:edges(dir=Z, not(len>50), nearest=[1,2,3], seams)")
    assert sel.scope == "plate" and sel.kind == "edge"
    assert sel.filters == ["dir=Z", "not(len>50)", "nearest=[1,2,3]", "seams"]
    assert is_selector("bracket:faces(normal=+Z)") and not is_selector("plate.end")
    with pytest.raises(CommandError, match="Form:") as excinfo:
        Selector("plate.end")
    assert excinfo.value.code == "pk_ref_unknown"


def test_survivor_selector_and_materialise() -> None:
    entry = NameEntry(
        "h.1.wall",
        "face",
        "h",
        "1.wall",
        1,
        ("cylinder", 314.159, (50.0, 30.0, 5.0), (-1.0, 0.0, 0.0), 5.0),
    )
    assert (
        survivor_selector("plate", entry)
        == "plate:faces(type=cylinder, normal=-X, r=5, nearest=[50,30,5])"
    )
    edge = NameEntry(
        "x", "edge", "plate", "", 0, ("line", 10.0, (0.0, 0.0, 5.0), (0.0, 0.0, 1.0), None)
    )
    assert survivor_selector("plate", edge) == "plate:edges(type=line, dir=Z, nearest=[0,0,5])"
    assert materialise(["a", "b"]) == ["a", "b"]
    assert materialise([f"n{i}" for i in range(12)]) == {
        "count": 12,
        "first": [f"n{i}" for i in range(8)],
    }


# -- on F1 ------------------------------------------------------------------------------------


pytest.importorskip("OCP", reason="partkiln[brep] not installed")

from test_document_parts import F1, F2, build  # noqa: E402

from partkiln.naming import resolve  # noqa: E402


@pytest.fixture(scope="module")
def f1_part():
    doc = build(F1())
    return doc.parts["plate"]


@pytest.mark.brep
def test_inventory_names_every_face_and_edge(f1_part) -> None:
    inv = f1_part.inventory()
    assert sorted(inv.face_names) == sorted(
        [
            "plate.start",
            "plate.end",
            "plate.side.r.0",
            "plate.side.r.1",
            "plate.side.r.2",
            "plate.side.r.3",
            "hole1.1.wall",
        ]
    )
    assert len(inv.edge_names) == 15 and len(set(inv.edge_names)) == 15
    assert "hole1.1.wall~seam" in inv.edge_names
    assert inv.stale == {}
    assert not any(n.startswith("plate.face[") for n in inv.face_names)  # nothing left unnamed


@pytest.mark.brep
@pytest.mark.parametrize(
    "selector,kind,count,names",
    [
        ("plate:edges(dir=Z)", "edge", 4, None),
        ("plate:faces(normal=+Z)", "face", 1, ["plate.end"]),
        ("plate:faces(normal=-Z)", "face", 1, ["plate.start"]),
        ("plate:faces(type=cylinder)", "face", 1, ["hole1.1.wall"]),
        ("plate:faces(type=cyl, r=5)", "face", 1, ["hole1.1.wall"]),
        (
            "plate:edges(type=circle, r=5)",
            "edge",
            2,
            ["hole1.1.wall|plate.start", "hole1.1.wall|plate.end"],
        ),
        ("plate:edges(of=plate.end, loop=outer)", "edge", 4, None),
        ("plate:edges(of=plate.end, loop=inner)", "edge", 1, ["hole1.1.wall|plate.end"]),
        ("plate:edges(dir=X, len>50)", "edge", 4, None),
        ("plate:edges(dir=Y, len<70)", "edge", 4, None),
        ("plate:edges(not(dir=Z), not(type=circle))", "edge", 8, None),
        ("plate:edges(convex, dir=Z)", "edge", 4, None),
        ("plate:faces(area>6000)", "face", 0, None),
        ("plate:faces(nearest=[50,30,10])", "face", 1, ["plate.end"]),
        ("plate:edges(dir=X, nearest=[50,0,10])", "edge", 1, ["plate.end|plate.side.r.0"]),
        ("hole1:faces()", "face", 1, ["hole1.1.wall"]),
        ("hole1:edges()", "edge", 2, None),
        ("plate:faces(created_by=hole1)", "face", 1, ["hole1.1.wall"]),
        ("plate:edges(created_by=hole1, seams)", "edge", 3, None),
    ],
)
def test_selectors_on_f1(f1_part, selector, kind, count, names) -> None:
    if count == 0:
        with pytest.raises(CommandError) as excinfo:
            resolve(f1_part, selector, kind)
        assert excinfo.value.code == "pk_ref_empty"
        assert "area>6000" in str(excinfo.value) and "Face areas in scope" in str(excinfo.value)
        return
    res = resolve(f1_part, selector, kind)
    assert res.count == count, res.names
    if names is not None:
        assert sorted(res.names) == sorted(names)
    assert res.echo() == {selector: count}


@pytest.mark.brep
def test_seams_are_excluded_by_default_and_counted(f1_part) -> None:
    res = resolve(f1_part, "plate:edges(dir=Z)", "edge")
    assert res.seam_excluded == 1 and res.count == 4
    kept = resolve(f1_part, "plate:edges(dir=Z, seams)", "edge")
    assert kept.seam_excluded == 0 and kept.count == 5
    assert "hole1.1.wall~seam" in kept.names


@pytest.mark.brep
def test_cardinality_and_empty_refusals_name_the_reason(f1_part) -> None:
    with pytest.raises(CommandError) as excinfo:
        resolve(f1_part, "plate:faces(type=plane)", "face", "one")
    assert excinfo.value.code == "pk_ref_ambiguous"
    assert "matched 6" in str(excinfo.value) and "plate.end at (50.000, 30.000, 10.000)" in str(
        excinfo.value
    )
    with pytest.raises(CommandError) as excinfo:
        resolve(f1_part, "plate:edges(dir=Z, len>500)", "edge")
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_ref_empty"
    assert "5 candidate(s) after dir=Z, none after len>500" in message
    assert "run 10.000-100.000 mm" in message
    with pytest.raises(CommandError, match="Known: plate, hole1, plate") as excinfo:
        resolve(f1_part, "ghost:faces()", "face")
    assert excinfo.value.code == "pk_ref_unknown"
    with pytest.raises(CommandError, match=r"loop=outer\|inner needs of=") as excinfo:
        resolve(f1_part, "plate:edges(loop=outer)", "edge")
    with pytest.raises(CommandError, match="selects faces but this field takes edges"):
        resolve(f1_part, "plate:faces(normal=+Z)", "edge")
    with pytest.raises(CommandError, match="Face names:") as excinfo:
        resolve(f1_part, "plate.top", "face")
    assert excinfo.value.code == "pk_ref_unknown"


@pytest.mark.brep
def test_names_follow_history_across_later_features() -> None:
    doc = build(F2())
    part = doc.parts["bracket"]
    inv = part.inventory()
    # the base's end face was cut by the upright and drilled four times; still one face, still named
    assert inv.face_index("base.end") is not None
    assert inv.face_index("upright.end") is not None
    assert inv.face_index("fillet1.face[0]") is not None
    # a unified face carries both its makers' names (coplanar side faces merged by UnifySameDomain)
    merged = {
        n
        for n in inv.aliases
        if inv.aliases[n] == inv.aliases[inv.face_names[inv.aliases["base.side.r.0"]]]
    }
    assert len(merged) >= 1
    assert resolve(part, "base.end", "face", "one").how == "name"
    rim = resolve(part, "base.end|h.1.wall", "edge", "one")
    assert rim.count == 1 and rim.infos[0].curve_type == "circle"


@pytest.mark.brep
def test_fan_out_is_named_with_an_index_and_ambiguous_for_on() -> None:
    doc = build(F1())
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "slot_sk",
            "props": {
                "plane": "on:plate.end",
                "profile": [{"rect": [4, 100], "at": [48, -20], "tag": "s"}],
            },
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "slot",
            "props": {"sketch": "slot_sk", "distance": "through", "mode": "cut"},
        }
    )
    part = doc.parts["plate"]
    inv = part.inventory()
    assert inv.face_index("plate.end[0]") is not None and inv.face_index("plate.end[1]") is not None
    both = resolve(part, "plate.end", "face")
    assert both.count == 2 and both.names == ["plate.end[0]", "plate.end[1]"]
    with pytest.raises(CommandError) as excinfo:
        resolve(part, "plate.end", "face", "one")
    assert excinfo.value.code == "pk_ref_ambiguous" and "plate.end[1]" in str(excinfo.value)
    one = resolve(part, "plate.end[1]", "face", "one")
    assert one.count == 1


# -- units in a selector's numeric filters (A66 defect audit) ----------------------------------


def _inch_plate(name: str = "imperial"):
    """A 4 x 2 x 0.4 INCH plate: 101.6 x 50.8 x 10.16 mm, so a bare `len>5`
    reads 127 mm in this document and 5 mm in a millimetre one."""
    doc = Document(name=name)
    doc.apply({"op": "set", "id": "doc", "props": {"units": "in"}})
    doc.apply({"op": "create", "kind": "part", "name": "plate"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": [4, 2], "tag": "r"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": 0.4},
        }
    )
    return doc


@pytest.mark.brep
def test_numeric_filters_accept_a_unit_suffix(f1_part) -> None:
    """F1's bore is r 5 mm = 0.19685 in and its long edges are 100 mm = 3.937 in.

    Law 12 at the selector boundary: `r=0.19685in` must find the bore that
    `r=0.19685` (mm) misses, and `len>4in` must find nothing where `len>4`
    (mm) finds four. A suffix used to reach a bare `float()` and crash with
    pk_op_failed 'report this'.
    """
    assert resolve(f1_part, "plate:faces(type=cyl, r=5mm)", "face").count == 1
    assert resolve(f1_part, "plate:faces(type=cyl, r=0.19685in)", "face").names == ["hole1.1.wall"]
    assert resolve(f1_part, "plate:edges(dir=X, len>3in)", "edge").count == 4
    with pytest.raises(CommandError) as excinfo:
        resolve(f1_part, "plate:edges(dir=X, len>4in)", "edge")
    assert excinfo.value.code == "pk_ref_empty"
    # area is the unit SQUARED: 9 in2 = 5806.4 mm2 keeps only the two 5921.46 mm2 faces
    assert resolve(f1_part, "plate:faces(area>9in2)", "face").count == 2
    assert resolve(f1_part, "plate:faces(area>9in)", "face").count == 2
    # nearest is a point in the document's unit too
    assert resolve(f1_part, "plate:edges(dir=X, nearest=[1.9685in,0,0.3937in])", "edge").names == [
        "plate.end|plate.side.r.0"
    ]
    with pytest.raises(CommandError) as excinfo:
        resolve(f1_part, "plate:faces(r=0.25in)", "face")
    assert excinfo.value.code == "pk_ref_empty"
    assert "Radii in scope: 5" in str(excinfo.value)


@pytest.mark.brep
def test_an_unknown_unit_in_a_filter_refuses_with_the_accepted_ones(f1_part) -> None:
    for selector, kind in (
        ("plate:faces(r=6qq)", "face"),
        ("plate:edges(len>6qq)", "edge"),
        ("plate:faces(area>6qq)", "face"),
        ("plate:edges(nearest=[6qq,0,0])", "edge"),
    ):
        with pytest.raises(CommandError) as excinfo:
            resolve(f1_part, selector, kind)
        assert excinfo.value.code == "pk_unit_unknown", selector
        assert "mm, cm, m, in, ft, mil" in str(excinfo.value), selector


@pytest.mark.brep
def test_a_bare_number_in_a_filter_is_the_document_unit() -> None:
    """The inch plate's long edges are 4 in: `len>3` keeps them, `len>5` keeps none.

    Read as millimetres (the old hard-wiring) `len>5` would keep all four.
    """
    doc = _inch_plate()
    kept = doc.apply(
        {
            "op": "create",
            "kind": "fillet",
            "name": "f1",
            "props": {"edges": "plate:edges(dir=X, len>3)", "r": 0.05},
        }
    )
    assert kept["resolved"] == {"plate:edges(dir=X, len>3)": 4}
    with pytest.raises(CommandError) as excinfo:
        _inch_plate("imperial2").apply(
            {
                "op": "create",
                "kind": "fillet",
                "name": "f2",
                "props": {"edges": "plate:edges(dir=X, len>5)", "r": 0.05},
            }
        )
    assert excinfo.value.code == "pk_ref_empty"
    assert "len>5" in str(excinfo.value)


@pytest.mark.brep
def test_a_one_reference_that_matches_nothing_refuses_pk_ref_empty() -> None:
    """`pk_ref_ambiguous` said "it matched 0 ... name one of them" - of nothing.

    D8: a refusal names the fix. Nothing matched, so the fix is what emptied
    the scope plus the names that DO exist.
    """
    doc = build(F1())
    doc.apply({"op": "set", "id": "feat:hole1", "props": {"suppressed": True}})
    part = doc.parts["plate"]
    with pytest.raises(CommandError) as excinfo:
        resolve(part, "hole1:faces()", "face", "one")
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_ref_empty"
    assert "hole1" in message and "no faces" in message
    assert "plate.end" in message  # the names that do exist
    assert "plate:faces(" in message  # a selector that would match
    with pytest.raises(CommandError) as excinfo:
        resolve(part, [], "face", "one")
    assert excinfo.value.code == "pk_ref_empty"
