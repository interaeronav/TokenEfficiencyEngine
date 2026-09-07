"""Adapter contract between the kernel and a DCC (Blender / Unreal / fake).

Adapters translate typed batch operations into DCC calls and report results
as diffs (principle P1: diffs over dumps). Entity ids must be stable for the
life of a DCC session (Blender: session_uid; Unreal: object path).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from tee.kernel.errors import TeeError

# A batch is a list of typed operations:
#   {"op": "create", "kind": <str>, "name": <str>, "props": {...}}
#   {"op": "set", "id": <entity id>, "props": {...}}
#   {"op": "delete", "id": <entity id>}
# Adapters may accept additional adapter-specific ops; unknown ops raise.


@dataclass
class Entity:
    """Compact cached view of one DCC object. `summary` holds small scalar
    facts only (bounds, counts, kind-specific flags) - never geometry."""

    id: str
    name: str
    kind: str
    parent: str | None = None
    summary: dict[str, Any] = field(default_factory=dict)

    def concise(self) -> dict[str, Any]:
        d: dict[str, Any] = {"id": self.id, "name": self.name, "kind": self.kind}
        if self.parent:
            d["parent"] = self.parent
        return d

    def detailed(self) -> dict[str, Any]:
        d = self.concise()
        if self.summary:
            d.update(self.summary)
        return d


@dataclass
class Diff:
    """What one batch changed. `details` carries per-id compact change info
    (e.g. new transform) so the model never needs a follow-up read.
    `upserts` carries the created/modified entities for the scene cache; it
    is kernel-internal and never serialized to the model."""

    created: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    details: dict[str, dict[str, Any]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    upserts: list[Entity] = field(default_factory=list, repr=False)

    def is_empty(self) -> bool:
        return not (self.created or self.modified or self.deleted)

    def to_payload(self) -> dict[str, Any]:
        d: dict[str, Any] = {}
        if self.created:
            d["created"] = self.created
        if self.modified:
            d["modified"] = self.modified
        if self.deleted:
            d["deleted"] = self.deleted
        if self.details:
            d["details"] = self.details
        if self.notes:
            d["notes"] = self.notes
        return d


@dataclass(frozen=True)
class LaneVocab:
    """What one lane accepts, declared so the kernel can route WITHOUT asking.

    A68: an omitted adapter= resolves by what a batch contains - an entity id,
    a create kind, an op verb - against these declarations, and the reply
    says where the batch went. `ops`/`kinds` of None mean the lane claims
    every verb / every kind (the default for an adapter that declares
    nothing, which on a multi-lane server surfaces as an honest
    adapter_required until it does). `kind_optional`: a create with no kind
    is accepted (Blender makes a cube). `imports`: file suffixes an
    import_file op lands. `renders`: capture() can answer pixels at all.
    `purpose`: one line for tee_status and the instructions. Optional for
    third-party adapters: the eighth method of the kit, `vocab()`."""

    ops: tuple[str, ...] | None = None
    kinds: tuple[str, ...] | None = None
    kind_optional: bool = True
    imports: tuple[str, ...] = ()
    renders: bool = True
    purpose: str = ""

    def accepts_op(self, verb: Any) -> bool:
        return self.ops is None or verb in self.ops

    def accepts_kind(self, kind: Any) -> bool:
        if kind is None:
            return self.kind_optional
        return self.kinds is None or kind in self.kinds

    def accepts(self, op: dict[str, Any]) -> bool:
        """One op, as the router judges it: verb first, then the create kind."""
        verb = op.get("op")
        if not self.accepts_op(verb):
            return False
        return verb != "create" or self.accepts_kind(op.get("kind"))


@dataclass
class AdapterInfo:
    id: str
    product: str
    version: str
    connected: bool
    extra: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "product": self.product,
            "version": self.version,
            "connected": self.connected,
        }
        if self.extra:
            d.update(self.extra)
        return d


@runtime_checkable
class Adapter(Protocol):
    """Contract every DCC adapter implements. All methods are synchronous and
    must fail fast (raise TeeError) rather than block past a client timeout."""

    def info(self) -> AdapterInfo: ...

    def probe(self) -> bool:
        """Cheap liveness check; must never hang."""
        ...

    def list_entities(self) -> list[Entity]:
        """Full entity listing, used only for cache (re)sync - not exposed raw."""
        ...

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        """Apply typed operations atomically (best effort) and return the diff."""
        ...

    def snapshot(self, label: str) -> dict[str, Any]:
        """Opaque checkpoint payload (kept small or spilled to disk by the adapter)."""
        ...

    def restore(self, payload: dict[str, Any]) -> None: ...

    def capture(self, view: str, max_bytes: int) -> bytes:
        """JPEG bytes for the requested view, under max_bytes (principle P3)."""
        ...


class FakeAdapter:
    """In-memory adapter used by kernel tests and as the reference semantics
    for real adapters. Entity ids are `e1`, `e2`, ... in creation order."""

    def __init__(self) -> None:
        self._store: dict[str, Entity] = {}
        self._next_id = 1
        self._connected = True

    # -- Adapter protocol -------------------------------------------------

    def info(self) -> AdapterInfo:
        return AdapterInfo(
            id="fake",
            product="FakeDCC",
            version="0.0",
            connected=self._connected,
            extra={"entities": len(self._store)},
        )

    def probe(self) -> bool:
        return self._connected

    def vocab(self) -> LaneVocab:
        """The reference declaration: exactly the ops execute() dispatches,
        any create kind, a kind-less create accepted."""
        return LaneVocab(
            ops=("create", "set", "assign_material", "delete"),
            kinds=None,
            kind_optional=True,
            imports=(),
            renders=True,
            purpose="in-memory reference scene",
        )

    def list_entities(self) -> list[Entity]:
        return [copy.deepcopy(e) for e in self._store.values()]

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        diff = Diff()
        for i, op in enumerate(batch):
            kind = op.get("op")
            if kind == "create":
                eid = f"e{self._next_id}"
                self._next_id += 1
                ent = Entity(
                    id=eid,
                    name=op.get("name") or eid,
                    kind=op.get("kind", "object"),
                    parent=op.get("parent"),
                    summary=dict(op.get("props") or {}),
                )
                self._store[eid] = ent
                diff.created.append(eid)
                diff.details[eid] = ent.detailed()
                _upsert(diff, ent)
            elif kind == "set":
                ent = self._require(op, i)
                props = dict(op.get("props") or {})  # never mutate the caller's op
                if "name" in props:
                    ent.name = props.pop("name")
                ent.summary.update(props)
                if ent.id not in diff.created and ent.id not in diff.modified:
                    diff.modified.append(ent.id)
                diff.details[ent.id] = ent.detailed()
                _upsert(diff, ent)
            elif kind == "assign_material":
                ent = self._require(op, i)
                props = dict(op.get("props") or {})
                ent.summary["material"] = props.get("material") or f"{ent.name}_mat"
                for key in ("base_color", "metallic", "roughness"):
                    if key in props:
                        ent.summary[key] = props[key]
                if ent.id not in diff.created and ent.id not in diff.modified:
                    diff.modified.append(ent.id)
                diff.details[ent.id] = ent.detailed()
                _upsert(diff, ent)
            elif kind == "delete":
                ent = self._require(op, i)
                del self._store[ent.id]
                if ent.id in diff.created:
                    diff.created.remove(ent.id)  # created+deleted nets to nothing
                else:
                    diff.deleted.append(ent.id)
                if ent.id in diff.modified:
                    diff.modified.remove(ent.id)
                diff.details.pop(ent.id, None)
                diff.upserts = [u for u in diff.upserts if u.id != ent.id]
            else:
                raise TeeError(
                    "bad_op",
                    f"Unknown op '{kind}' at batch index {i}.",
                    fix="Use one of: create, set, assign_material, delete.",
                )
        return diff

    def _require(self, op: dict[str, Any], index: int) -> Entity:
        eid = op.get("id")
        ent = self._store.get(eid) if eid else None
        if ent is None:
            raise TeeError(
                "unknown_entity",
                f"No entity '{eid}' (batch index {index}).",
                fix="List current ids with tee_scene_summary.",
            )
        return ent

    def snapshot(self, label: str) -> dict[str, Any]:
        return {
            "label": label,
            "store": {k: copy.deepcopy(v) for k, v in self._store.items()},
            "next_id": self._next_id,
        }

    def restore(self, payload: dict[str, Any]) -> None:
        self._store = {k: copy.deepcopy(v) for k, v in payload["store"].items()}
        self._next_id = payload["next_id"]

    def capture(self, view: str, max_bytes: int) -> bytes:
        # Smallest valid JPEG header/footer; enough for transport tests.
        return b"\xff\xd8\xff\xe0" + b"\x00" * 16 + b"\xff\xd9"

    # -- test helpers -----------------------------------------------------

    def disconnect(self) -> None:
        self._connected = False


def _upsert(diff: Diff, ent: Entity) -> None:
    diff.upserts = [u for u in diff.upserts if u.id != ent.id]
    diff.upserts.append(copy.deepcopy(ent))
