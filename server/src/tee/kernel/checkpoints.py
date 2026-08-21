"""Checkpoint / rollback manager (principle P6).

Every mutation batch gets an automatic checkpoint before it runs; the model
can also create labelled checkpoints and roll back by id or label. Payloads
are opaque adapter snapshots (real adapters keep them small or spill to disk;
the manager only bounds how many are retained).
"""

from __future__ import annotations

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
    def __init__(self, keep: int = _KEEP):
        self._keep = keep
        self._by_adapter: dict[str, list[Checkpoint]] = {}
        self._counter = 0

    def create(self, adapter: Adapter, label: str, revision: int) -> Checkpoint:
        info = adapter.info()
        self._counter += 1
        cp = Checkpoint(
            id=f"cp{self._counter}",
            label=label,
            adapter_id=info.id,
            revision=revision,
            created_at=time.time(),
            payload=adapter.snapshot(label),
        )
        stack = self._by_adapter.setdefault(info.id, [])
        stack.append(cp)
        if len(stack) > self._keep:
            del stack[: len(stack) - self._keep]
        return cp

    def rollback(self, adapter: Adapter, ref: str) -> Checkpoint:
        """Restore the checkpoint matching `ref` (id, or newest with that
        label) and drop every checkpoint taken after it."""
        info = adapter.info()
        stack = self._by_adapter.get(info.id, [])
        index = None
        for i in range(len(stack) - 1, -1, -1):
            if stack[i].id == ref or stack[i].label == ref:
                index = i
                break
        if index is None:
            known = ", ".join(f"{c.id}:{c.label}" for c in stack[-5:]) or "(none)"
            raise TeeError(
                "unknown_checkpoint",
                f"No checkpoint '{ref}' for adapter '{info.id}'.",
                fix=f"Recent checkpoints: {known}.",
            )
        cp = stack[index]
        adapter.restore(cp.payload)
        del stack[index + 1 :]
        return cp

    def list(self, adapter_id: str | None = None) -> list[dict[str, Any]]:
        if adapter_id is not None:
            stacks = [self._by_adapter.get(adapter_id, [])]
        else:
            stacks = list(self._by_adapter.values())
        out: list[dict[str, Any]] = []
        for stack in stacks:
            out.extend(cp.to_payload() for cp in stack)
        return out
