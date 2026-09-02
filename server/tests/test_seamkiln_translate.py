"""The seamkiln adapter's OWN logic, tested with no seamkiln installed.

A53 P4 asked for "a fake-adapter test suite so CI needs no solver" and got
`importorskip("seamkiln")` instead - a CI box without the kernel skipped
fifteen tests rather than running any. This is the part of that debt that can
be paid honestly: everything the adapter does BEFORE the kernel (translating
wire ops into commands, naming entities, refusing unknown ops) is pure and is
tested here without it. The kernel-backed tests still need the kernel, and
say so.
"""

from __future__ import annotations

import pytest

from tee.adapters.seamkiln.adapter import _PASSTHROUGH, _WIRE_OPS, _panel_id, _translate
from tee.kernel.errors import TeeError


def test_create_block_panel_and_seam_become_commands() -> None:
    assert _translate({"op": "create", "kind": "block", "props": {"block": "tee"}}, 0) == [
        {"op": "block", "args": {"block": "tee"}}
    ]
    [panel] = _translate(
        {"op": "create", "kind": "panel", "name": "SQ", "props": {"outline": []}}, 0
    )
    assert panel == {"op": "panel", "args": {"outline": [], "id": "SQ"}}
    [seam] = _translate({"op": "create", "kind": "seam", "name": "s", "props": {"a": 1}}, 0)
    assert seam["op"] == "seam" and seam["args"]["id"] == "s"


def test_set_only_knows_seam_allowance_and_strips_the_entity_prefix() -> None:
    [cmd] = _translate({"op": "set", "id": "panel:FRONT", "props": {"seam_allowance_mm": 10}}, 3)
    assert cmd == {"op": "allowance", "args": {"mm": 10, "panels": ["FRONT"]}}
    with pytest.raises(TeeError, match="nothing settable"):
        _translate({"op": "set", "id": "panel:FRONT", "props": {"colour": "red"}}, 3)
    assert _panel_id("panel:BACK") == "BACK" and _panel_id("BACK") == "BACK"


def test_arrange_splits_into_a_body_and_an_arrangement() -> None:
    body, arrange = _translate(
        {"op": "arrange", "props": {"body": "anny", "stature_m": 1.7, "particle_distance_mm": 12}},
        1,
    )
    assert body == {"op": "body", "args": {"kind": "anny", "stature_m": 1.7}}
    assert arrange["op"] == "arrange" and arrange["args"]["particle_distance_mm"] == 12


def test_every_session_verb_added_since_a53_passes_straight_through() -> None:
    """A verb added to the Session reaches TEE by being named once. These are
    the ones the follow-up campaigns added; a missing name here is a feature
    the model cannot reach."""
    for verb in (
        "zip",
        "unzip",
        "button",
        "unfasten",
        "handoff",
        "walk",
        "pull",
        "fold",
        "ease",
        "lock",
        "unlock",
        "rip",
        "pinch",
        "lace",
        "finish",
        "animate",
    ):
        assert verb in _PASSTHROUGH, verb
        assert _translate({"op": verb, "props": {"x": 1}}, 0) == [{"op": verb, "args": {"x": 1}}]


def test_an_unknown_op_names_every_op_that_exists() -> None:
    with pytest.raises(TeeError) as caught:
        _translate({"op": "teleport"}, 7)
    assert "batch[7]" in caught.value.message
    for op in _WIRE_OPS:
        assert op in caught.value.fix
