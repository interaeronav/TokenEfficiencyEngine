"""P3 acceptance through the DOCUMENT verbs: components, mates, joints on F6.

The library numbers were pinned in `test_assembly_solver.py` and
`test_assembly_checks.py`; this file pins the wire above them - that a mate
addresses geometry by NAME (`block.bore.1.wall`, Law 13), that every verb
answers with ONE `details.asm` on the `regen` channel (D7), that an
over-constrained assembly is REPORTED and only a frame-kind mismatch
refuses, and that the poses join the fingerprint so a replay reproduces them
(D3).

F6, built here through the verbs rather than `brep.fixtures`: block 40x40x20
with a d10 through hole (30 429.204 mm3), pin d10 x 40 (3 141.593), the d11
variant that interferes by 329.867 mm3 at (20, 20, 10), and steel at
7850 kg/m3 - 238.869 g and 24.662 g.
"""

from __future__ import annotations

import json
import time
from typing import Any

import pytest

from partkiln.document import CommandError, Document

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

pytestmark = pytest.mark.brep

BLOCK_MM3 = 30429.204
PIN_MM3 = 3141.593


def F6(pin_dia: float = 10.0) -> list[dict[str, Any]]:
    """Block with a d10 bore, and a pin of `pin_dia` - both as command scripts."""
    return [
        {"op": "create", "kind": "part", "name": "block", "props": {"material": "steel_s275"}},
        {
            "op": "create",
            "kind": "sketch",
            "name": "bsk",
            "props": {"plane": "XY", "profile": [{"rect": [40, 40], "tag": "r"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "body",
            "props": {"sketch": "bsk", "distance": 20},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "bore",
            "props": {"on": "body.end", "at": [[20, 20]], "dia": 10},
        },
        {"op": "create", "kind": "part", "name": "pin", "props": {"material": "steel_s275"}},
        {
            "op": "create",
            "kind": "sketch",
            "name": "psk",
            "props": {"plane": "XY", "profile": [{"circle": pin_dia, "tag": "c"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "shaft",
            "props": {"sketch": "psk", "distance": 40, "part": "pin"},
        },
    ]


def build(commands: list[dict[str, Any]], name: str = "f6") -> Document:
    doc = Document(name=name)
    for command in commands:
        doc.apply(command)
    return doc


def placed(pin_at: tuple[float, float, float] = (3.0, -4.0, 7.0), dia: float = 10.0) -> Document:
    doc = build(F6(dia))
    doc.apply({"op": "create", "kind": "component", "props": {"part": "block"}})
    doc.apply({"op": "create", "kind": "component", "props": {"part": "pin", "at": list(pin_at)}})
    return doc


# --------------------------------------------------------------------------- components


def test_the_first_component_is_grounded_and_says_so() -> None:
    doc = build(F6())
    first = doc.apply({"op": "create", "kind": "component", "props": {"part": "block"}})
    assert first["id"] == "cmp:block" and first["grounded"] is True
    assert first["assumed"]["grounded"] == "the first component is grounded"
    assert first["regen"]["asm"]["components"] == 1
    second = doc.apply(
        {"op": "create", "kind": "component", "props": {"part": "pin", "at": [3, -4, 7]}}
    )
    assert second["id"] == "cmp:pin" and second["grounded"] is False
    assert second["pose"]["translation"] == [3.0, -4.0, 7.0]
    assert second["regen"]["asm"]["dof"] == 6  # the pin is free, the block is not
    assert doc.assemblies["main"].asm.grounded == ["block"]


def test_a_component_needs_a_part_that_exists() -> None:
    doc = build(F6())
    with pytest.raises(CommandError) as caught:
        doc.apply({"op": "create", "kind": "component", "props": {"part": "widget"}})
    assert caught.value.code == "pk_ref_unknown"
    assert "part:block" in str(caught.value) and "part:pin" in str(caught.value)
    with pytest.raises(CommandError) as caught:
        doc.apply({"op": "create", "kind": "component", "props": {}})
    assert caught.value.code == "pk_needs"


def test_a_virtual_object_is_a_component_with_no_geometry() -> None:
    doc = placed()
    out = doc.apply({"op": "create", "kind": "object", "name": "brg", "props": {"part": "brg6204"}})
    assert out["virtual"] is True and out["id"] == "cmp:brg"
    assert out["regen"]["asm"]["components"] == 3
    with pytest.raises(CommandError) as caught:
        doc.apply(
            {
                "op": "create",
                "kind": "mate",
                "props": {"type": "insert", "a": "brg.face", "b": "pin.shaft.side.c"},
            }
        )
    assert caught.value.code == "pk_ref_empty"


# --------------------------------------------------------------------------- joints and mates


def test_a_cylindrical_joint_leaves_two_degrees_of_freedom() -> None:
    doc = placed()
    started = time.perf_counter()
    out = doc.apply(
        {
            "op": "create",
            "kind": "joint",
            "name": "j1",
            "props": {"type": "cylindrical", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    ms = (time.perf_counter() - started) * 1000
    assert out["id"] == "jt:j1" and out["type"] == "cylindrical"
    assert out["dof_removed"] == 4 and out["dof"] == 2
    assert out["status"] == "under" and out["residual"] == 0.0
    asm = out["regen"]["asm"]
    assert asm["dof"] == 2 and asm["dof_by_component"] == {"pin": 2}
    assert asm["joint_values"]["j1"]["angle_deg"] == 0.0
    assert ms < 500, f"one joint took {ms:.0f} ms"


@pytest.mark.parametrize(
    ("kind", "dof"),
    [("rigid", 0), ("revolute", 1), ("slider", 1), ("cylindrical", 2), ("planar", 3), ("ball", 3)],
)
def test_every_joint_kind_removes_what_it_claims(kind: str, dof: int) -> None:
    doc = placed()
    out = doc.apply(
        {
            "op": "create",
            "kind": kind,  # the D5 spelling: the kind IS the joint kind on the wire
            "name": "j",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    assert out["kind"] == "joint" and out["type"] == kind
    assert out["dof"] == dof and out["dof_removed"] == 6 - dof


def test_insert_and_mate_seat_the_pin_at_20_20_20() -> None:
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "mate",
            "name": "ins",
            "props": {"kind": "insert", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    out = doc.apply(
        {
            "op": "create",
            "kind": "mate",
            "name": "seat",
            "props": {"type": "mate", "a": "block.body.end", "b": "pin.shaft.start"},
        }
    )
    assert out["pose"]["component"] == "pin"
    assert out["pose"]["translation"] == pytest.approx([20.0, 20.0, 20.0], abs=1e-6)
    assert out["dof"] == 1 and out["residual"] == pytest.approx(0.0, abs=1e-9)
    assert out["regen"]["asm"]["contacts"] == [["block", "pin"]]
    assert out["regen"]["asm"]["interference"] == []


def test_only_a_frame_kind_mismatch_refuses() -> None:
    doc = placed()
    with pytest.raises(CommandError) as caught:
        doc.apply(
            {
                "op": "create",
                "kind": "mate",
                "name": "bad",
                "props": {"type": "insert", "a": "block.body.end", "b": "pin.shaft.start"},
            }
        )
    assert caught.value.code == "pk_spec_conflict"
    assert "axis frame" in str(caught.value) and "use mate for plane-plane" in str(caught.value)
    # and the refusal left nothing behind (Law 16)
    assert doc.assemblies["main"].asm.constraint_names() == []


def test_an_over_constrained_assembly_is_reported_not_refused() -> None:
    """The model can only fix what it can see: the LATER constraint is named
    with its own residual, and the poses satisfy the consistent subset."""
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "joint",
            "name": "rg",
            "props": {"type": "rigid", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    out = doc.apply(
        {
            "op": "create",
            "kind": "mate",
            "name": "m5",
            "props": {"type": "mate", "a": "block.body.end", "b": "pin.shaft.start", "offset": 5},
        }
    )
    assert out["status"] == "conflict" and out["over_constrained"] == ["m5"]
    asm = out["regen"]["asm"]
    assert asm["conflicts"] == [{"constraint": "m5", "residual_mm": 4.0}]
    assert asm["residual"] == pytest.approx(4.0, abs=1e-6)
    # the rigid joint still holds the pin where it put it
    assert doc.assemblies["main"].asm.component("pin").pose.translation == pytest.approx(
        (20.0, 20.0, 21.0), abs=1e-6
    )


def test_an_unspelled_mate_is_the_plane_mate_and_says_what_axes_need() -> None:
    """`create mate` with no `type` is the `mate` kind (planes coincident), so
    two cylinders refuse by naming the constraint that does take them."""
    doc = placed()
    with pytest.raises(CommandError) as caught:
        doc.apply(
            {
                "op": "create",
                "kind": "mate",
                "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
            }
        )
    assert caught.value.code == "pk_spec_conflict"
    assert "use insert for axis-axis" in str(caught.value)


def test_a_joint_needs_a_kind_and_the_refusal_lists_them() -> None:
    doc = placed()
    for props in (
        {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        {"type": "welded", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
    ):
        with pytest.raises(CommandError) as caught:
            doc.apply({"op": "create", "kind": "joint", "props": props})
        assert caught.value.code == "pk_bad_op"
        assert "revolute" in str(caught.value) and "type" in str(caught.value)


# --------------------------------------------------------------------------- edits


def test_set_on_a_mate_re_solves_and_reports_the_new_state() -> None:
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "insert",
            "name": "ins",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "mate",
            "name": "seat",
            "props": {"type": "mate", "a": "block.body.end", "b": "pin.shaft.start"},
        }
    )
    out = doc.apply({"op": "set", "id": "mate:seat", "props": {"offset": "5mm"}})
    assert out["props"] == [{"key": "offset_mm", "old": None, "new": 5.0}]
    assert out["pose"]["translation"] == pytest.approx([20.0, 20.0, 25.0], abs=1e-6)
    assert out["regen"]["asm"]["dof"] == 1
    # suppressing it gives the freedom back and says which is off
    off = doc.apply({"op": "set", "id": "mate:seat", "props": {"suppressed": True}})
    assert off["regen"]["asm"]["dof"] == 2
    assert off["regen"]["asm"]["suppressed"] == ["seat"]


def test_set_on_a_component_moves_it_and_grounds_it() -> None:
    doc = placed()
    out = doc.apply({"op": "set", "id": "cmp:pin", "props": {"at": [10, 10, 30], "grounded": True}})
    assert out["pose"]["translation"] == [10.0, 10.0, 30.0]
    assert {c["key"] for c in out["props"]} == {"pose", "grounded"}
    assert out["regen"]["asm"]["dof"] == 0
    assert out["regen"]["asm"]["grounded"] == ["block", "pin"]


def test_delete_refuses_while_a_mate_holds_the_component() -> None:
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "insert",
            "name": "ins",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    with pytest.raises(CommandError) as caught:
        doc.apply({"op": "delete", "id": "cmp:pin"})
    assert caught.value.code == "pk_delete_blocked" and "mate:ins" in str(caught.value)
    out = doc.apply({"op": "delete", "id": "cmp:pin", "cascade": True})
    assert out["deleted"] == ["cmp:pin", "mate:ins"] and out["components"] == 1
    assert doc.assemblies["main"].asm.constraint_names() == []


def test_a_part_that_a_component_instances_is_a_dependent() -> None:
    doc = placed()
    assert doc.dependents_of("part:pin") == ["cmp:pin"]


# --------------------------------------------------------------------------- numbers


def test_the_d11_pin_interferes_by_329_867_through_the_verbs() -> None:
    doc = build(F6())
    doc.apply({"op": "create", "kind": "component", "props": {"part": "block"}})
    doc.apply({"op": "create", "kind": "part", "name": "pin11"})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "p11",
            "props": {"plane": "XY", "profile": [{"circle": 11, "tag": "c"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "extrude",
            "name": "s11",
            "props": {"sketch": "p11", "distance": 40, "part": "pin11"},
        }
    )
    out = doc.apply(
        {
            "op": "create",
            "kind": "component",
            "name": "fat",
            "props": {"part": "pin11", "at": [20, 20, -10], "grounded": True},
        }
    )
    asm = out["regen"]["asm"]
    assert asm["interference"] == [
        {"a": "block", "b": "fat", "mm3": 329.867, "centroid": [20.0, 20.0, 10.0]}
    ]
    assert asm["contacts"] == []


def test_the_exact_fit_reads_zero_interference_with_contact() -> None:
    doc = placed(pin_at=(20.0, 20.0, -10.0))
    out = doc.apply({"op": "set", "id": "cmp:pin", "props": {"grounded": True}})
    asm = out["regen"]["asm"]
    assert asm["interference"] == [] and asm["contacts"] == [["block", "pin"]]


def test_a_clearance_pin_reports_the_gap() -> None:
    doc = placed(pin_at=(20.0, 20.0, -10.0), dia=9.9)
    out = doc.apply({"op": "set", "id": "cmp:pin", "props": {"grounded": True}})
    asm = out["regen"]["asm"]
    assert asm["interference"] == [] and asm["contacts"] == []
    assert asm["clearance_mm"] == {"block-pin": 0.05}


def test_the_part_volumes_are_the_pinned_f6_numbers() -> None:
    doc = build(F6())
    assert doc.parts["block"].volume() == pytest.approx(BLOCK_MM3, abs=5e-4)
    assert doc.parts["pin"].volume() == pytest.approx(PIN_MM3, abs=5e-4)


# --------------------------------------------------------------------------- rows and replay


def test_the_assembly_is_rows_the_way_everything_else_is() -> None:
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "insert",
            "name": "ins",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    rows = {row["id"]: row for row in doc.entities()}
    assert {"asm", "cmp:block", "cmp:pin", "mate:ins"} <= set(rows)
    assert rows["asm"]["kind"] == "assembly" and rows["asm"]["components"] == 2
    assert rows["asm"]["dof"] == 2 and rows["asm"]["status"] == "under"
    assert rows["cmp:pin"]["parent"] == "asm" and rows["cmp:pin"]["part"] == "part:pin"
    assert rows["mate:ins"]["type"] == "insert" and rows["mate:ins"]["suppressed"] is False
    assert rows["mate:ins"]["a"] == "block.bore.1.wall"
    assert rows["doc"]["components"] == 2 and rows["doc"]["assemblies"] == 1
    detail = doc.detail("mate:ins")
    assert detail["a_frame"]["kind"] == "axis" and detail["a_frame"]["radius_mm"] == 5.0
    assert doc.detail("cmp:pin")["used_by"] == ["mate:ins"]
    assert doc.detail("asm")["dof"] == 2


def test_the_poses_join_the_fingerprint_and_a_replay_reproduces_them() -> None:
    doc = placed()
    before = doc.fingerprint()
    doc.apply(
        {
            "op": "create",
            "kind": "insert",
            "name": "ins",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "mate",
            "name": "seat",
            "props": {"type": "mate", "a": "block.body.end", "b": "pin.shaft.start"},
        }
    )
    assert doc.fingerprint() != before  # the pin moved, and the fingerprint knows
    twin = Document.replay(json.loads(json.dumps(doc.script())))
    assert twin.fingerprint() == doc.fingerprint()
    assert twin.assemblies["main"].asm.component("pin").pose.translation == pytest.approx(
        (20.0, 20.0, 20.0), abs=1e-6
    )


def test_a_document_with_no_assembly_hashes_as_it_always_did() -> None:
    """The assemblies key appears only when there is one, so P3 did not move
    the fingerprint of every part-only document ever checkpointed."""
    from test_document_parts import F1
    from test_document_parts import build as build_parts

    plain = build_parts(F1())
    twin = Document.replay(plain.script())
    assert twin.fingerprint() == plain.fingerprint()
    assert "assemblies" not in json.dumps(plain.script())


def test_a_failed_assembly_command_leaves_the_fingerprint_alone() -> None:
    doc = placed()
    before = doc.fingerprint()
    with pytest.raises(CommandError):
        doc.apply(
            {
                "op": "create",
                "kind": "mate",
                "name": "bad",
                "props": {"type": "insert", "a": "block.body.end", "b": "pin.shaft.start"},
            }
        )
    assert doc.fingerprint() == before


def test_a_component_that_is_moved_where_its_mates_forbid_reports_where_it_landed() -> None:
    """`set cmp: at=` asks; the solve answers, and the answer is what the row
    and the result carry - a pose sent but not reached would be a lie."""
    doc = placed()
    doc.apply(
        {
            "op": "create",
            "kind": "insert",
            "name": "ins",
            "props": {"a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
        }
    )
    out = doc.apply({"op": "set", "id": "cmp:pin", "props": {"at": [0, 0, 5]}})
    # the insert holds x and y on the bore axis; only z was free to take
    assert out["pose"]["translation"] == pytest.approx([20.0, 20.0, 5.0], abs=1e-6)
    rows = {row["id"]: row for row in doc.entities()}
    assert rows["cmp:pin"]["pose"]["translation"] == out["pose"]["translation"]
