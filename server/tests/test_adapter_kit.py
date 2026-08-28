"""The adapter kit's own acceptance (A37 P3).

1. FakeAdapter passes the PACKAGED contract suite - the shipped kit and
   the kernel's reference semantics cannot drift apart.
2. ToyAdapter: a minimal second implementation written by following
   docs/adapter-kit.md ONLY (the skeleton + the five rules - no peeking
   at FakeAdapter beyond what the doc itself shows). It has no extra
   ops and no viewport, proving the contract demands neither.
3. The suite actually catches a broken adapter (a mutator), so a green
   run means something.

The REAL rehearsal is P4: the FreeCAD fabrication toolset gets built
from the kit doc alone, and every stumble found there is a kit bug.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from tee.kernel.adapter import AdapterInfo, Diff, Entity, FakeAdapter
from tee.kernel.contract import AdapterContract
from tee.kernel.errors import TeeError


class ToyAdapter:
    """A note board: entities are sticky notes. Built from the kit doc."""

    def __init__(self) -> None:
        self._notes: dict[str, Entity] = {}
        self._serial = 0

    def info(self) -> AdapterInfo:
        return AdapterInfo(id="toy", product="NoteBoard", version="1.0", connected=True)

    def probe(self) -> bool:
        return True

    def list_entities(self) -> list[Entity]:
        return [copy.deepcopy(note) for note in self._notes.values()]

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        diff = Diff()
        for index, op in enumerate(batch):
            action = op.get("op")
            if action == "create":
                self._serial += 1
                note = Entity(
                    id=f"note{self._serial}",
                    name=str(op.get("name") or f"note{self._serial}"),
                    kind=str(op.get("kind") or "note"),
                    summary=dict(op.get("props") or {}),
                )
                self._notes[note.id] = note
                diff.created.append(note.id)
                diff.details[note.id] = note.detailed()
                diff.upserts.append(copy.deepcopy(note))
            elif action == "set":
                note = self._get(op, index)
                props = dict(op.get("props") or {})
                if "name" in props:
                    note.name = str(props.pop("name"))
                note.summary.update(props)
                diff.modified.append(note.id)
                diff.details[note.id] = note.detailed()
                diff.upserts.append(copy.deepcopy(note))
            elif action == "delete":
                note = self._get(op, index)
                del self._notes[note.id]
                diff.deleted.append(note.id)
            else:
                raise TeeError(
                    "bad_op",
                    f"Unknown op '{action}' at batch index {index}.",
                    fix="Use one of: create, set, delete.",
                )
        return diff

    def _get(self, op: dict[str, Any], index: int) -> Entity:
        note = self._notes.get(str(op.get("id")))
        if note is None:
            raise TeeError(
                "unknown_entity",
                f"No note '{op.get('id')}' (batch index {index}).",
                fix="List current ids with tee_scene_summary.",
            )
        return note

    def snapshot(self, label: str) -> dict[str, Any]:
        return {
            "label": label,
            "notes": {k: copy.deepcopy(v) for k, v in self._notes.items()},
            "serial": self._serial,
        }

    def restore(self, payload: dict[str, Any]) -> None:
        self._notes = {k: copy.deepcopy(v) for k, v in payload["notes"].items()}
        self._serial = payload["serial"]

    def capture(self, view: str, max_bytes: int) -> bytes:
        raise TeeError(
            "capture_unsupported",
            "NoteBoard has no viewport.",
            fix="Use entity summaries; there is nothing to render.",
        )


class TestFakeAdapterContract(AdapterContract):
    def make_adapter(self):
        return FakeAdapter()


class TestToyAdapterContract(AdapterContract):
    def make_adapter(self):
        return ToyAdapter()


def test_the_suite_catches_a_broken_adapter() -> None:
    """A green contract run must mean something: an adapter that edits
    the caller's batch fails the immutability test."""

    class Mutator(ToyAdapter):
        def execute(self, batch):
            for op in batch:
                op.setdefault("props", {})["sneaky"] = True
            return super().execute(batch)

    class Probe(AdapterContract):
        def make_adapter(self):
            return Mutator()

    with pytest.raises(AssertionError):
        Probe().test_execute_does_not_mutate_the_callers_batch()


def test_toy_adapter_gets_the_kernel_for_free(tmp_path) -> None:
    """The doc's wire-it-in claim: TeeApp over the toy adapter serves
    batch/checkpoint/rollback/diff with zero adapter-specific code."""
    from tee.app import TeeApp

    app = TeeApp({"toy": ToyAdapter()}, project_root=tmp_path)
    try:
        out = app.run_batch(
            "toy", [{"op": "create", "kind": "note", "name": "buy sandpaper"}], label="kit"
        )
        assert out["ok"] is True and len(out["created"]) == 1
        created = out["created"][0]
        second = app.run_batch("toy", [{"op": "set", "id": created, "props": {"done": True}}])
        assert second["modified"] == [created]
        # each batch auto-checkpoints BEFORE applying; rolling back to the
        # second batch's checkpoint undoes only the set
        app.rollback("toy", second["checkpoint"])
        note = next(e for e in app.adapter("toy").list_entities() if e.id == created)
        assert "done" not in note.summary  # rolled back through the kernel
    finally:
        app.shutdown()
