"""Translation with no kernel at all (A66 P4).

`_translate` is a pure function: one wire op in, the kernel commands that
carry it out. Testing it alone is how the vocabulary stays honest on a
machine with no OCCT, no sidecar and no partkiln - which is most machines,
including the Claude Desktop extension runtime this lane was designed
around. Nothing here constructs a kernel; the refusals are the point.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tee.adapters.partkiln import adapter as pk
from tee.adapters.partkiln.adapter import INSTALL_HINT, PartkilnAdapter
from tee.kernel.errors import TeeError

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "partkiln" / "src"


def test_create_carries_kind_name_and_props() -> None:
    commands = pk._translate(
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": "T"},
        },
        0,
    )
    assert commands == [
        {
            "op": "create",
            "kind": "extrude",
            "props": {"sketch": "base", "distance": "T"},
            "name": "plate",
        }
    ]


def test_translation_never_mutates_the_callers_op() -> None:
    """Checkpoint replay re-sends the same dicts; an adapter that edits its
    input corrupts the script it is about to replay."""
    op = {"op": "create", "kind": "hole", "name": "h", "props": {"at": [[0, 0]]}}
    keep = json.loads(json.dumps(op))
    pk._translate(op, 0)
    assert op == keep


def test_a_set_on_a_param_becomes_param_set() -> None:
    """One concept, one kernel command: `set param:T` and `param_set` are the
    same edit, so they must not take two code paths through regen."""
    assert pk._translate({"op": "set", "id": "param:T", "props": {"value": "12mm"}}, 0) == [
        {"op": "param_set", "params": {"T": "12mm"}}
    ]
    assert pk._translate({"op": "param_set", "props": {"W": 120, "H": "W/2"}}, 0) == [
        {"op": "param_set", "params": {"W": 120, "H": "W/2"}}
    ]
    assert pk._translate({"op": "param_set", "props": {"params": {"W": 120}}}, 0) == [
        {"op": "param_set", "params": {"W": 120}}
    ]


def test_set_and_delete_keep_the_entity_id() -> None:
    assert pk._translate({"op": "set", "id": "feat:h", "props": {"dia": "12mm"}}, 0) == [
        {"op": "set", "id": "feat:h", "props": {"dia": "12mm"}}
    ]
    assert pk._translate({"op": "delete", "id": "feat:h"}, 0) == [{"op": "delete", "id": "feat:h"}]
    assert pk._translate({"op": "delete", "id": "feat:h", "props": {"cascade": True}}, 0) == [
        {"op": "delete", "id": "feat:h", "cascade": True}
    ]
    # no id at all: `set` falls back to the document, which is where units,
    # standard and strict_units live
    assert pk._translate({"op": "set", "props": {"units": "mm"}}, 0) == [
        {"op": "set", "id": "doc", "props": {"units": "mm"}}
    ]


def test_export_and_check_pass_through_as_their_own_ops() -> None:
    assert pk._translate({"op": "export", "props": {"format": "step", "out": "a.step"}}, 0) == [
        {"op": "export", "props": {"format": "step", "out": "a.step"}}
    ]
    assert pk._translate({"op": "check", "props": {"spec": {"faces": 7}}}, 0) == [
        {"op": "check", "props": {"spec": {"faces": 7}}}
    ]


def test_deferred_ops_split_out_only_when_the_kernel_lacks_the_verb() -> None:
    """A kernel that registers `export` as a verb gets it inside the one
    `apply`; one that does not gets it as a method afterwards. Either way the
    caller wrote the same batch."""
    commands = [
        (0, {"op": "create", "kind": "part", "props": {}}),
        (1, {"op": "export", "props": {"format": "stl", "out": "a.stl"}}),
    ]
    applied, deferred = pk._split(commands, ("create", "set", "delete", "param_set"))
    assert [c["op"] for c in applied] == ["create"]
    assert deferred == [(1, "export", {"format": "stl", "out": "a.stl"})]

    applied, deferred = pk._split(commands, ("create", "export"))
    assert [c["op"] for c in applied] == ["create", "export"] and deferred == []


@pytest.mark.parametrize(
    ("op", "code", "needle"),
    [
        ({"op": "frobnicate"}, "pk_bad_op", "partkiln accepts"),
        ({"op": "create"}, "pk_needs", "pk_verbs"),
        ({"op": "create", "kind": "extrude", "props": [1, 2]}, "pk_bad_request", '"props"'),
        ({"op": "set", "id": "feat:h"}, "pk_needs", "suppressed"),
        ({"op": "set", "id": "param:T", "props": {}}, "pk_needs", "param_set"),
        ({"op": "delete"}, "pk_needs", "cascade"),
        ({"op": "param_set", "props": {}}, "pk_needs", "param_set"),
    ],
)
def test_every_refusal_carries_a_code_and_the_exact_fix(op, code, needle) -> None:
    with pytest.raises(TeeError) as excinfo:
        pk._translate(op, 3)
    assert excinfo.value.code == code
    assert "batch[3]" in excinfo.value.message
    assert needle in excinfo.value.fix


def test_id_prefixes_map_to_the_D7_entity_kinds() -> None:
    """The prefix IS the kind when a row carries none - so a mistyped prefix
    would silently invent an entity kind the scene cache then keys on."""
    cases = {
        "doc": "doc",
        "param:W": "param",
        "plane:XY": "datum",
        "sk:base": "sketch",
        "feat:plate": "feature",
        "part:bracket": "body",
        "cmp:pin1": "component",
        "mate:m1": "mate",
        "jt:j1": "joint",
        "dwg:sheet1": "drawing",
        "vw:front": "view",
        "dim:d1": "dimension",
        "sheet:brk": "sheet",
        "export:a.step": "export",
        "obj:kit_a": "object",
    }
    for eid, kind in cases.items():
        entity = pk._entity({"id": eid})
        assert entity.kind == kind, eid
        assert entity.name == (eid.partition(":")[2] or eid)


def test_an_entity_keeps_scalars_and_drops_bulk() -> None:
    entity = pk._entity(
        {
            "id": "part:bracket",
            "kind": "body",
            "volume_mm3": 91_158.6,
            "bbox_mm": [120, 80, 10],
            "tree": ["feat:plate", "feat:h"],
            "mesh": [[0, 0, 0]] * 500,
        }
    )
    assert entity.summary["volume_mm3"] == 91_158.6
    assert entity.summary["bbox_mm"] == [120, 80, 10]
    assert entity.summary["features"] == 2  # the tree becomes its length
    assert "mesh" not in entity.summary and "tree" not in entity.summary


def test_a_feature_row_parents_itself_to_its_body() -> None:
    entity = pk._entity({"id": "feat:h", "kind": "hole", "part": "part:bracket"})
    assert entity.parent == "part:bracket"
    assert entity.concise() == {
        "id": "feat:h",
        "name": "h",
        "kind": "hole",
        "parent": "part:bracket",
    }


def test_the_verb_answer_is_read_in_every_shape_a_kernel_might_send() -> None:
    assert pk._verb_names({"verbs": ["create", "set"]}) == ["create", "set"]
    assert pk._verb_names({"verbs": {"create": "...", "set": "..."}}) == ["create", "set"]
    assert pk._verb_names(["create", "set"]) == ["create", "set"]
    assert pk._verb_names(None) == []


def test_the_install_hint_names_both_routes_and_the_novtk_trap() -> None:
    """The two ways this kernel is reached fail differently, and the dev one
    has a trap: `cadquery-ocp-novtk` ships the same top-level OCP package and
    would clobber the wheel server/.venv already has (P0a row 3)."""
    assert "server/.venv/bin/python -e partkiln" in INSTALL_HINT
    assert "never add [brep]" in INSTALL_HINT
    assert "sidecars/partkiln" in INSTALL_HINT and "--python 3.11" in INSTALL_HINT


def test_with_neither_route_every_entry_point_refuses_with_that_hint(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pk, "_in_process_available", lambda: False)
    adapter = PartkilnAdapter(tmp_path, config={"python": str(tmp_path / "no-such-python")})
    assert adapter.mode == "absent"
    assert adapter.probe() is False
    assert adapter.list_entities() == []
    payload = adapter.info().to_payload()
    # `connected` is the ROUTE's answer; `version` is a fact about the
    # interpreter (this repo IS the checkout, so the package may well be
    # importable while no route to a kernel exists). Only the first is a
    # claim about whether anything can be driven.
    assert payload["connected"] is False
    assert payload["fix"] == INSTALL_HINT
    for call in (
        lambda: adapter.execute([{"op": "create", "kind": "part", "name": "x"}]),
        lambda: adapter.call("measure", {}),
        lambda: adapter.restore({"path": "x"}),
    ):
        with pytest.raises(TeeError) as excinfo:
            call()
        assert excinfo.value.code == "pk_kernel_absent"
        assert excinfo.value.fix == INSTALL_HINT
    # health() is the exception, deliberately: "absent" is an answer, and a
    # tool that refuses to say so is the one that wastes a round trip.
    health = adapter.health()
    assert health["mode"] == "absent" and health["fix"] == INSTALL_HINT


def test_the_server_never_imports_partkiln_or_ocp_to_offer_the_lane() -> None:
    """In a subprocess, because an earlier test in this session may already
    have imported the kernel - and the claim is about a fresh server."""
    probe = (
        "import sys, tee.app, tee.adapters.partkiln.tools, tee.adapters.partkiln.adapter;"
        "print(('partkiln' in sys.modules, 'OCP' in sys.modules))"
    )
    out = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, timeout=60, check=True
    )
    assert out.stdout.strip() == "(False, False)"


def test_the_wire_ops_are_exactly_the_kernels_verbs_plus_the_deferrables() -> None:
    """The vocabulary is closed on both sides, so it can drift. `VERBS` is
    read from a subprocess with PYTHONPATH, because partkiln is deliberately
    not installed in the server interpreter."""
    if not SRC.is_dir():
        pytest.skip("partkiln/src is not beside server/")
    out = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json, partkiln.document as d; print(json.dumps(list(d.VERBS)))",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    if out.returncode != 0:
        pytest.skip(f"partkiln is not importable: {out.stderr.strip()[:120]}")
    verbs = set(json.loads(out.stdout))
    assert verbs <= set(pk._WIRE_OPS), f"the kernel grew verbs the adapter cannot send: {verbs}"
    assert set(pk._BASE_VERBS) == verbs, "the adapter's fallback verb set drifted from the kernel"
    assert set(pk._DEFERRABLE) == set(pk._WIRE_OPS) - verbs
