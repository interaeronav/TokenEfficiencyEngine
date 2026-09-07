"""Checkpoint / rollback manager (principle P6).

Every mutation batch gets an automatic checkpoint before it runs; the model
can also create labelled checkpoints and roll back by id or label. Payloads
are opaque adapter snapshots (real adapters keep them small or spill to disk;
the manager only bounds how many are retained).
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass, field
from typing import Any

from tee.kernel.adapter import Adapter
from tee.kernel.errors import TeeError

_KEEP = 20  # most-recent checkpoints retained per adapter


@dataclass
class Checkpoint:
    id: str
    label: str
    adapter_id: str
    revision: int
    created_at: float
    payload: dict[str, Any] = field(repr=False, default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "adapter": self.adapter_id,
            "revision": self.revision,
        }


class CheckpointManager:
    """Stacks keyed by SERVED LANE NAME when the caller passes one (A68) -
    the app always does - else by the adapter's own id, as before. Ids are
    global (`cp{N}`), and every checkpoint records its lane, so a rollback
    can find its lane from the ref alone (`find`); two adapters that report
    the same id (two fakes) no longer share a stack."""

    def __init__(self, keep: int = _KEEP):
        self._keep = keep
        self._by_adapter: dict[str, list[Checkpoint]] = {}
        self._counter = 0

    @staticmethod
    def _key(adapter: Adapter, lane: str | None) -> str:
        return lane if lane is not None else adapter.info().id

    def create(
        self, adapter: Adapter, label: str, revision: int, *, lane: str | None = None
    ) -> Checkpoint:
        key = self._key(adapter, lane)
        self._counter += 1
        cp = Checkpoint(
            id=f"cp{self._counter}",
            label=label,
            adapter_id=key,
            revision=revision,
            created_at=time.time(),
            payload=adapter.snapshot(label),
        )
        stack = self._by_adapter.setdefault(key, [])
        stack.append(cp)
        if len(stack) > self._keep:
            evicted = stack[: len(stack) - self._keep]
            del stack[: len(stack) - self._keep]
            _discard(adapter, evicted)
        return cp

    def rollback(self, adapter: Adapter, ref: str, *, lane: str | None = None) -> Checkpoint:
        """Restore the checkpoint matching `ref` (id, or newest with that
        label) and drop every checkpoint taken after it."""
        key = self._key(adapter, lane)
        stack = self._by_adapter.get(key, [])
        index = None
        for i in range(len(stack) - 1, -1, -1):
            if stack[i].id == ref or stack[i].label == ref:
                index = i
                break
        if index is None:
            known = ", ".join(f"{c.id}:{c.label}" for c in stack[-5:]) or "(none)"
            raise TeeError(
                "unknown_checkpoint",
                f"No checkpoint '{ref}' for adapter '{key}'.",
                fix=f"Recent checkpoints: {known}.",
            )
        cp = stack[index]
        adapter.restore(cp.payload)
        dropped = stack[index + 1 :]
        del stack[index + 1 :]
        _discard(adapter, dropped)
        return cp

    def find(self, ref: str) -> tuple[str, Checkpoint]:
        """The lane that owns `ref`, and the checkpoint: by id (global, so
        unique), else the newest with that label - in ONE lane. A label that
        names checkpoints in several lanes is ambiguous and says so."""
        by_label: list[tuple[str, Checkpoint]] = []
        for key, stack in self._by_adapter.items():
            for cp in reversed(stack):
                if cp.id == ref:
                    return key, cp
            newest = next((cp for cp in reversed(stack) if cp.label == ref), None)
            if newest is not None:
                by_label.append((key, newest))
        if len(by_label) == 1:
            return by_label[0]
        if not by_label:
            recent = self.list()[-5:]
            known = ", ".join(f"{c['id']}:{c['label']} ({c['adapter']})" for c in recent)
            raise TeeError(
                "unknown_checkpoint",
                f"No checkpoint '{ref}' in any served lane.",
                fix=f"Recent checkpoints: {known or '(none)'}.",
            )
        where = ", ".join(f"{key} ({cp.id})" for key, cp in by_label)
        raise TeeError(
            "checkpoint_ambiguous",
            f"Label '{ref}' names checkpoints in {len(by_label)} lanes: {where}.",
            fix="Roll back by id, or pass adapter=<lane>.",
        )

    def discard_all(self, adapter: Adapter, *, lane: str | None = None) -> None:
        """Release every checkpoint for this adapter (server shutdown)."""
        stack = self._by_adapter.pop(self._key(adapter, lane), [])
        _discard(adapter, stack)

    def list(self, adapter_id: str | None = None) -> list[dict[str, Any]]:
        if adapter_id is not None:
            stacks = [self._by_adapter.get(adapter_id, [])]
        else:
            stacks = list(self._by_adapter.values())
        out: list[dict[str, Any]] = []
        for stack in stacks:
            out.extend(cp.to_payload() for cp in stack)
        return out


def _discard(adapter: Adapter, checkpoints: list[Checkpoint]) -> None:
    """Let the adapter release snapshot resources (e.g. temp .blend files)
    for checkpoints that can no longer be rolled back to."""
    hook = getattr(adapter, "discard_snapshot", None)
    if hook is None:
        return
    for cp in checkpoints:
        with contextlib.suppress(Exception):
            hook(cp.payload)
