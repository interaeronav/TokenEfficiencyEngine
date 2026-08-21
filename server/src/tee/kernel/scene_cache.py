"""Differential scene cache (principle P1).

Holds the server-side view of one DCC scene: entities keyed by stable id, a
monotonic `revision` bumped per applied change-set, and an `epoch` bumped
whenever diff continuity breaks (rollback, file reload, forced resync). The
model tracks (epoch, revision); `diff_since` either returns the delta or says
"resync required" - it never silently returns a wrong delta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tee.kernel.adapter import Adapter, Diff, Entity

_LOG_LIMIT = 200  # bounded history of applied diffs


@dataclass
class _LogEntry:
    revision: int
    diff: Diff
    source: str  # "agent" | "user" | "resync"


@dataclass
class SceneCache:
    entities: dict[str, Entity] = field(default_factory=dict)
    revision: int = 0
    epoch: int = 0
    _log: list[_LogEntry] = field(default_factory=list)

    # -- state transitions -------------------------------------------------

    def resync(self, adapter: Adapter) -> dict[str, Any]:
        """Full rebuild from the adapter. Breaks diff continuity (new epoch)."""
        self.entities = {e.id: e for e in adapter.list_entities()}
        self.epoch += 1
        self.revision += 1
        self._log.clear()
        return self.stamp()

    def apply_diff(self, diff: Diff, upserts: list[Entity], source: str = "agent") -> int:
        """Fold one change-set into the cache; returns the new revision."""
        for ent in upserts:
            self.entities[ent.id] = ent
        for eid in diff.deleted:
            self.entities.pop(eid, None)
        self.revision += 1
        self._log.append(_LogEntry(self.revision, diff, source))
        if len(self._log) > _LOG_LIMIT:
            del self._log[: len(self._log) - _LOG_LIMIT]
        return self.revision

    def invalidate(self) -> None:
        """Continuity break without a rebuild (e.g. after rollback); the next
        diff_since from an older stamp will demand resync."""
        self.epoch += 1
        self._log.clear()

    # -- queries -----------------------------------------------------------

    def stamp(self) -> dict[str, int]:
        return {"epoch": self.epoch, "revision": self.revision}

    def diff_since(self, epoch: int, revision: int) -> dict[str, Any]:
        if epoch != self.epoch:
            return {
                "resync_required": True,
                "reason": "scene history was rewritten (rollback/reload)",
                **self.stamp(),
            }
        if revision > self.revision:
            return {
                "resync_required": True,
                "reason": f"revision {revision} is ahead of the scene ({self.revision})",
                **self.stamp(),
            }
        missing = [e for e in self._log if e.revision > revision]
        oldest_replayable = self._log[0].revision - 1 if self._log else self.revision
        covered = revision >= oldest_replayable
        if not covered:
            return {
                "resync_required": True,
                "reason": "diff history pruned; too far behind",
                **self.stamp(),
            }
        merged = _merge_log([e.diff for e in missing])
        user_edits = any(e.source == "user" for e in missing)
        payload = merged.to_payload()
        payload.update(self.stamp())
        if user_edits:
            payload["user_edits"] = True
        return payload

    def summary(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        kind: str | None = None,
        name_contains: str | None = None,
        detailed: bool = False,
    ) -> dict[str, Any]:
        items = list(self.entities.values())
        if kind:
            items = [e for e in items if e.kind == kind]
        if name_contains:
            needle = name_contains.lower()
            items = [e for e in items if needle in e.name.lower()]
        total = len(items)
        page = items[offset : offset + limit]
        kinds: dict[str, int] = {}
        for e in self.entities.values():
            kinds[e.kind] = kinds.get(e.kind, 0) + 1
        payload: dict[str, Any] = {
            **self.stamp(),
            "total": total,
            "kinds": kinds,
            "entities": [e.detailed() if detailed else e.concise() for e in page],
        }
        shown = len(page)
        if offset + shown < total:
            payload["truncated"] = (
                f"{total - offset - shown} more; narrow with kind=/name_contains= "
                f"or page with offset={offset + shown}"
            )
        return payload

    def get(self, entity_id: str) -> Entity | None:
        return self.entities.get(entity_id)


def _merge_log(diffs: list[Diff]) -> Diff:
    """Fold sequential diffs into one net diff.

    Net semantics over the window: created-then-deleted cancels out;
    deleted-then-recreated collapses to modified; details keep the latest
    value for ids that still exist at the end.
    """
    created: dict[str, None] = {}  # insertion-ordered sets
    modified: dict[str, None] = {}
    deleted: dict[str, None] = {}
    details: dict[str, dict[str, Any]] = {}
    notes: list[str] = []
    for d in diffs:
        for eid in d.created:
            if eid in deleted:
                del deleted[eid]
                modified[eid] = None
            else:
                created[eid] = None
        for eid in d.modified:
            if eid not in created:
                modified[eid] = None
        for eid in d.deleted:
            if eid in created:
                del created[eid]
            else:
                deleted[eid] = None
            modified.pop(eid, None)
            details.pop(eid, None)
        details.update(d.details)
        notes.extend(n for n in d.notes if n not in notes)
    for eid in deleted:
        details.pop(eid, None)
    return Diff(
        created=list(created),
        modified=list(modified),
        deleted=list(deleted),
        details=details,
        notes=notes,
    )
