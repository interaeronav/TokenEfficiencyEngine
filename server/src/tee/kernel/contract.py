"""The adapter contract as a runnable test suite (A37 P3, the adapter kit).

A third-party adapter proves itself against TEE's kernel expectations by
subclassing this in its own pytest file and overriding `make_adapter`:

    from tee.kernel.contract import AdapterContract

    class TestMyAdapter(AdapterContract):
        def make_adapter(self):
            return MyAdapter(connect_args...)

pytest collects the inherited test_* methods. TEE's own FakeAdapter and
the kit's toy adapter run this exact class in-tree
(tests/test_adapter_kit.py), so the packaged suite and the kernel's real
expectations cannot drift apart.

Every test states WHY the kernel needs the behavior - the contract is
token dogma made executable: diffs over dumps, stable ids, rule-6
failures, budgets respected.
"""

from __future__ import annotations

from typing import Any

import pytest

from tee.kernel.errors import TeeError

__all__ = ["AdapterContract"]


class AdapterContract:
    """Subclass with a `Test` prefix and override make_adapter()."""

    def make_adapter(self) -> Any:
        raise NotImplementedError("override make_adapter() to return a fresh adapter")

    # -- identity ----------------------------------------------------------

    def test_info_payload_shape(self) -> None:
        """tee_status forwards info().to_payload() verbatim: the four core
        keys must exist so every adapter reads the same way."""
        payload = self.make_adapter().info().to_payload()
        for key in ("id", "product", "version", "connected"):
            assert key in payload, f"info payload lacks '{key}'"
        assert isinstance(payload["id"], str) and payload["id"]

    def test_probe_answers_a_bool(self) -> None:
        """The kernel probes before warming caches; probe() must answer a
        plain bool and never hang (deadlines are the adapter's job)."""
        assert self.make_adapter().probe() in (True, False)

    # -- execute: diffs over dumps -----------------------------------------

    def test_create_set_delete_roundtrip(self) -> None:
        """The core loop: typed ops in, a diff out, the listing agrees.
        tee_batch forwards the diff to the model - it must name exactly
        what changed."""
        adapter = self.make_adapter()
        diff = adapter.execute([{"op": "create", "kind": "object", "name": "kit_a"}])
        assert len(diff.created) == 1 and not diff.modified and not diff.deleted
        eid = diff.created[0]
        assert eid in diff.details, "a created id must carry compact details"
        assert any(e.id == eid for e in adapter.list_entities())

        diff = adapter.execute([{"op": "set", "id": eid, "props": {"name": "kit_b"}}])
        assert diff.modified == [eid]
        listed = next(e for e in adapter.list_entities() if e.id == eid)
        assert listed.name == "kit_b"

        diff = adapter.execute([{"op": "delete", "id": eid}])
        assert diff.deleted == [eid]
        assert all(e.id != eid for e in adapter.list_entities())

    def test_diff_reports_changes_not_the_world(self) -> None:
        """Principle P1: after a mutation the model sees what changed,
        never the whole scene - the diff over a 1-op batch must not grow
        with unrelated entity count."""
        adapter = self.make_adapter()
        for i in range(3):
            adapter.execute([{"op": "create", "kind": "object", "name": f"bg_{i}"}])
        diff = adapter.execute([{"op": "create", "kind": "object", "name": "fg"}])
        payload = diff.to_payload()
        assert len(payload.get("created", [])) == 1
        assert len(payload.get("details", {})) == 1, "details must cover changed ids only"

    def test_unknown_op_fails_rule6(self) -> None:
        """Fail loud and cheap: a bad op answers one TeeError naming the
        problem and the fix - never a stack trace, never silence."""
        adapter = self.make_adapter()
        with pytest.raises(TeeError) as excinfo:
            adapter.execute([{"op": "frobnicate"}])
        assert excinfo.value.code
        assert excinfo.value.fix, "the error must name the exact fix"

    def test_unknown_entity_fails_rule6(self) -> None:
        adapter = self.make_adapter()
        with pytest.raises(TeeError) as excinfo:
            adapter.execute([{"op": "set", "id": "no-such-id", "props": {"x": 1}}])
        assert excinfo.value.code and excinfo.value.fix

    def test_execute_does_not_mutate_the_callers_batch(self) -> None:
        """Checkpoint replay and retries re-use op dicts; an adapter that
        edits its input corrupts them."""
        adapter = self.make_adapter()
        op = {"op": "create", "kind": "object", "name": "kit_c", "props": {"size": 2}}
        keep = {k: (dict(v) if isinstance(v, dict) else v) for k, v in op.items()}
        adapter.execute([op])
        assert op == keep

    # -- ids and listings --------------------------------------------------

    def test_entity_ids_are_stable_across_listings(self) -> None:
        """Diffs, checkpoints and the scene cache all key on entity id; an
        id that changes between listings breaks every downstream surface."""
        adapter = self.make_adapter()
        adapter.execute([{"op": "create", "kind": "object", "name": "kit_d"}])
        first = sorted(e.id for e in adapter.list_entities())
        second = sorted(e.id for e in adapter.list_entities())
        assert first == second

    def test_concise_rows_are_compact(self) -> None:
        """concise() feeds tee_scene_summary rows: identity only (id, name,
        kind, optional parent) - geometry and bulk stay behind
        tee_entity_detail."""
        adapter = self.make_adapter()
        adapter.execute([{"op": "create", "kind": "object", "name": "kit_e", "props": {"size": 1}}])
        row = adapter.list_entities()[0].concise()
        assert set(row) <= {"id", "name", "kind", "parent"}

    # -- checkpoints -------------------------------------------------------

    def test_snapshot_restore_roundtrip(self) -> None:
        """tee_checkpoint/tee_rollback are exactly snapshot()/restore();
        restore must return the world to the snapshot's state."""
        adapter = self.make_adapter()
        adapter.execute([{"op": "create", "kind": "object", "name": "kit_keep"}])
        payload = adapter.snapshot("contract")
        assert isinstance(payload, dict)
        adapter.execute([{"op": "create", "kind": "object", "name": "kit_drop"}])
        adapter.restore(payload)
        names = sorted(e.name for e in adapter.list_entities())
        assert "kit_keep" in names and "kit_drop" not in names

    # -- capture -----------------------------------------------------------

    def test_capture_respects_the_byte_budget_or_refuses_loud(self) -> None:
        """Principle P3: pixels are last-resort evidence and always
        budgeted. capture() answers JPEG bytes under max_bytes, or raises
        a structured TeeError where the view/DCC cannot."""
        adapter = self.make_adapter()
        try:
            data = adapter.capture("viewport", 65536)
        except TeeError as exc:
            assert exc.code and exc.fix
            return
        assert isinstance(data, bytes) and len(data) <= 65536
        assert data.startswith(b"\xff\xd8"), "capture answers JPEG bytes"
