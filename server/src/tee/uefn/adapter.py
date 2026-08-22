"""UEFN adapter (12.3, A22/A23): a capability-probed thin proxy of
Epic's UEFN MCP toolsets - NEVER a from-scratch bridge (the community
bridge graveyard is documented; Epic's own surface at
127.0.0.1:8000/mcp is the only one that survives the road to UE6).

Cloud shape: the typed interface + the Fake implementation carry the
contract (Scene-Graph-first entity/component ops, devices as the
parallel eventually-legacy family, Verse compile lane, sessions). The
live proxy lands on the physical Windows machine behind the same
interface, keyed by (editor version, toolset catalog hash, per-toolset
schema hash).

LUF <-> XYZ: the UEFN MCP has a documented coordinate translation bug
class. TEE normalizes at the boundary: everything TEE-side is UE XYZ
(X forward, Y right, Z up, cm); Scene Graph LUF (Left-Up-Forward) is
converted exactly once, here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tee.kernel.errors import TeeError

# -- coordinate normalization ----------------------------------------------


def luf_to_xyz(luf: list[float]) -> list[float]:
    """Scene Graph LUF (Left, Up, Forward) -> UE XYZ (Forward, Right, Up).
    right = -left; the mapping is its own documented contract and the
    round-trip is property-tested."""
    left, up, forward = (float(v) for v in luf[:3])
    return [forward, -left, up]


def xyz_to_luf(xyz: list[float]) -> list[float]:
    x, y, z = (float(v) for v in xyz[:3])
    return [-y, z, x]


# -- capability probe -------------------------------------------------------

TOOLSETS = ("registry", "verse", "scene_graph", "devices", "sessions")


@dataclass
class UefnCapabilities:
    editor_present: bool
    beta_access: bool = False
    toolsets: dict[str, str] = field(default_factory=dict)  # name -> schema hash
    engine_version: str | None = None

    def to_payload(self) -> dict[str, Any]:
        if not self.editor_present:
            return {
                "editor": False,
                "mode": "offline",
                "available_offline": [
                    "digest facts + lint", "digest diff", "verse templates",
                    "export_for_uefn preflight", "device catalog (cached index)",
                ],
                "fix": "live lanes need UEFN on Windows with 'Python Editor "
                "Scripting' + 'UEFN MCP Toolsets' enabled under Beta Access "
                "(Project Settings), MCP at 127.0.0.1:8000/mcp",
            }
        if not self.beta_access:
            return {
                "editor": True,
                "mode": "gated",
                "fix": "enable BOTH 'Python Editor Scripting' and 'UEFN MCP "
                "Toolsets' under Beta Access in Project Settings, then "
                "restart the editor (accounts may need the beta allow-list)",
            }
        return {
            "editor": True,
            "mode": "live",
            "engine": self.engine_version,
            "toolsets": self.toolsets,
        }


class UefnAdapter:
    """The contract. Stable ids abstract over Actor refPath (UE5) vs
    Scene Graph entity (UEFN/UE6) - one id string, prefix-tagged."""

    def probe(self) -> UefnCapabilities:
        raise NotImplementedError

    # Scene-Graph-first vocabulary (the UE6 object model)
    def entities(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def entity_batch(self, ops: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError

    # devices: parallel, eventually-legacy family
    def device_catalog(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError

    def place_device(self, device: str, xyz: list[float]) -> dict[str, Any]:
        raise NotImplementedError

    # Verse lane
    def verse_files(self) -> list[str]:
        raise NotImplementedError

    def verse_compile(self) -> dict[str, Any]:
        raise NotImplementedError


class FakeUefn(UefnAdapter):
    """Reference semantics for tests and the cloud container. Entities
    live in LUF internally (as the real Scene Graph toolset reports) so
    the normalization boundary is exercised for real."""

    def __init__(self, *, editor_present: bool = True, beta_access: bool = True):
        self._editor = editor_present
        self._beta = beta_access
        self._entities: dict[str, dict[str, Any]] = {}
        self._next = 1
        self._verse: dict[str, str] = {}
        self.catalog = [
            {"device": "button_device", "tags": ["interact", "trigger"]},
            {"device": "trigger_device", "tags": ["volume", "trigger"]},
            {"device": "item_granter_device", "tags": ["items", "grant"]},
            {"device": "player_spawner_device", "tags": ["spawn", "player"]},
            {"device": "timer_device", "tags": ["time", "countdown"]},
        ]

    def probe(self) -> UefnCapabilities:
        if not self._editor:
            return UefnCapabilities(editor_present=False)
        if not self._beta:
            return UefnCapabilities(editor_present=True, beta_access=False)
        return UefnCapabilities(
            editor_present=True,
            beta_access=True,
            engine_version="42.00-fake",
            toolsets={name: f"hash-{name}" for name in TOOLSETS},
        )

    def _require_live(self) -> None:
        payload = self.probe().to_payload()
        if payload["mode"] != "live":
            raise TeeError(
                "uefn_unavailable",
                f"UEFN is {payload['mode']}.",
                fix=payload.get("fix", "connect a live editor"),
            )

    def entities(self) -> list[dict[str, Any]]:
        self._require_live()
        return [
            {"id": eid, "name": e["name"], "components": sorted(e["components"]),
             "position_xyz": luf_to_xyz(e["position_luf"])}
            for eid, e in self._entities.items()
        ]

    def entity_batch(self, ops: list[dict[str, Any]]) -> dict[str, Any]:
        self._require_live()
        created, modified, deleted = [], [], []
        for i, op in enumerate(ops):
            kind = op.get("op")
            if kind == "create_entity":
                eid = f"sg:{self._next}"
                self._next += 1
                self._entities[eid] = {
                    "name": op.get("name") or eid,
                    "components": set(op.get("components") or ["Transform"]),
                    "position_luf": xyz_to_luf(op.get("position_xyz") or [0, 0, 0]),
                }
                created.append(eid)
            elif kind == "set_transform":
                entity = self._require(op, i)
                entity["position_luf"] = xyz_to_luf(op.get("position_xyz") or [0, 0, 0])
                modified.append(op["id"])
            elif kind == "add_component":
                entity = self._require(op, i)
                entity["components"].add(str(op.get("component")))
                modified.append(op["id"])
            elif kind == "delete_entity":
                self._require(op, i)
                del self._entities[op["id"]]
                deleted.append(op["id"])
            else:
                raise TeeError(
                    "bad_op",
                    f"Unknown Scene Graph op '{kind}' at index {i}.",
                    fix="Ops: create_entity, set_transform, add_component, "
                    "delete_entity.",
                )
        return {"created": created, "modified": modified, "deleted": deleted}

    def _require(self, op: dict[str, Any], index: int) -> dict[str, Any]:
        entity = self._entities.get(op.get("id"))
        if entity is None:
            raise TeeError(
                "unknown_entity",
                f"No Scene Graph entity '{op.get('id')}' (op {index}).",
                fix="List with uefn_entities.",
            )
        return entity

    def device_catalog(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        # answered from the LOCAL index - never a forwarded 4,698-row dump
        words = query.lower().split()
        hits = [
            d for d in self.catalog
            if any(w in d["device"] or w in " ".join(d["tags"]) for w in words)
        ]
        return hits[:limit]

    def place_device(self, device: str, xyz: list[float]) -> dict[str, Any]:
        self._require_live()
        known = {d["device"] for d in self.catalog}
        if device not in known:
            raise TeeError(
                "unknown_device",
                f"'{device}' is not in the device catalog.",
                fix="Search with uefn_devices first.",
            )
        eid = f"dev:{self._next}"
        self._next += 1
        self._entities[eid] = {
            "name": device,
            "components": {"Device"},
            "position_luf": xyz_to_luf(xyz),
        }
        return {"id": eid, "device": device, "position_xyz": [float(v) for v in xyz]}

    def verse_files(self) -> list[str]:
        self._require_live()
        return sorted(self._verse)

    def verse_write(self, path: str, code: str) -> None:
        self._verse[path] = code

    def verse_compile(self) -> dict[str, Any]:
        self._require_live()
        diagnostics = []
        for path, code in self._verse.items():
            if "vErr" in code:  # test hook: seeded failures
                diagnostics.append({
                    "severity": "error", "file": path, "line": 1,
                    "message": "seeded failure",
                })
        return {"ok": not diagnostics, "diagnostics": diagnostics}
