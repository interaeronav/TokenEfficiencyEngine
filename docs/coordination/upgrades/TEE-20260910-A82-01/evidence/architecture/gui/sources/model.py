"""Validated architectural state shared by headless, GUI and exchange clients.

Millimetres throughout. Commands replace state only after validation of the whole
batch; undo restores geometry/project facts while revision numbers stay monotonic.
"""

from __future__ import annotations

import copy
import json
import math
import re
import uuid
from collections import Counter
from typing import Any

SCHEMA = "tee-architecture/1"
MAX_ENTITIES = 512
MAX_HISTORY = 20
MAX_BYTES = 8_000_000
_ID = re.compile(r"[A-Za-z0-9_-]{1,80}\Z")
_COMMON = {"id", "kind", "name", "properties", "provenance"}
_FIELDS = {
    "storey": {"elevation", "height"},
    "wall": {"storey", "start", "end", "thickness", "height"},
    "opening": {"wall", "offset", "width", "height", "sill", "fill"},
    "space": {"storey", "polygon", "height"},
    "slab": {"storey", "polygon", "thickness"},
    "roof": {"storey", "polygon", "thickness", "base_height", "form"},
    "cabinet": {
        "storey",
        "origin",
        "width",
        "depth",
        "height",
        "panel_thickness",
        "back_thickness",
        "shelves",
        "doors",
        "plinth_height",
        "grain",
        "edge_band_mm",
        "material",
    },
}


class ArchitectureError(ValueError):
    """A bounded, actionable refusal; the TEE boundary maps this to TeeError."""

    def __init__(
        self, code: str, message: str | None = None, fix: str = "Correct the named field."
    ) -> None:
        if message is None:
            message, code = code, "ak_invalid"
        super().__init__(message)
        self.code = code
        self.fix = fix


def number(value: Any, field: str, *, minimum: float | None = None) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or abs(value) > 1e9
        or not math.isfinite(value)
        or (minimum is not None and value < minimum)
    ):
        raise ArchitectureError(f"{field} needs a finite number within ±1e9 mm.")
    return float(value)


def positive(value: Any, field: str) -> float:
    result = number(value, field, minimum=0)
    if result <= 0:
        raise ArchitectureError(f"{field} must be positive.")
    return result


def _text(value: Any, field: str, limit: int = 256) -> None:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ArchitectureError(f"{field} needs nonempty text of at most {limit} characters.")


def _json(value: Any, *, limit: int = MAX_BYTES) -> None:
    def visit(item: Any, depth: int) -> None:
        if depth > 12:
            raise ArchitectureError("JSON nesting exceeds 12 levels.")
        if item is None or isinstance(item, (str, bool)):
            return
        if isinstance(item, (float, int)):
            if (isinstance(item, float) and not math.isfinite(item)) or (
                isinstance(item, int) and item.bit_length() > 4096
            ):
                raise ArchitectureError("JSON numbers must be finite.")
        elif isinstance(item, list):
            for child in item:
                visit(child, depth + 1)
        elif isinstance(item, dict) and all(isinstance(k, str) for k in item):
            for child in item.values():
                visit(child, depth + 1)
        else:
            raise ArchitectureError("Use JSON objects, arrays and scalar values only.")

    visit(value, 0)
    if len(json.dumps(value, allow_nan=False).encode()) > limit:
        raise ArchitectureError("ak_limit", f"JSON exceeds the {limit}-byte limit.")


def _point(value: Any, field: str, dimensions: int = 2) -> None:
    if not isinstance(value, list) or len(value) != dimensions:
        raise ArchitectureError(f"{field} needs {dimensions} coordinates in mm.")
    for coordinate in value:
        number(coordinate, field)


def polygon_area(polygon: list[list[float]]) -> float:
    """Translation-stable signed area; positive is counterclockwise."""
    x, y = polygon[0]
    return (
        sum(
            (a[0] - x) * (b[1] - y) - (b[0] - x) * (a[1] - y)
            for a, b in zip(polygon, polygon[1:] + polygon[:1], strict=True)
        )
        / 2
    )


def _polygon(value: Any, field: str) -> None:
    if not isinstance(value, list) or not 3 <= len(value) <= 256:
        raise ArchitectureError(f"{field} needs 3-256 polygon vertices.")
    for point in value:
        _point(point, field)
    if len({tuple(p) for p in value}) != len(value):
        raise ArchitectureError(f"{field} repeats a vertex; omit the closing duplicate.")
    if abs(polygon_area(value)) <= 1e-6:
        raise ArchitectureError(f"{field} has zero area.")

    def cross(a: list, b: list, c: list) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on(a: list, b: list, p: list) -> bool:
        return min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(
            a[1], b[1]
        )

    segments = list(zip(value, value[1:] + value[:1], strict=True))
    for i, (a, b) in enumerate(segments):
        # Adjacent collinear reversals overlap even though endpoints are shared.
        c = value[(i + 2) % len(value)]
        if cross(a, b, c) == 0 and (
            (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) < 0
        ):
            raise ArchitectureError(f"{field} has overlapping edges.")
        for j, (c, d) in enumerate(segments):
            if j <= i + 1 or (i == 0 and j == len(segments) - 1):
                continue
            ab_c, ab_d, cd_a, cd_b = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
            if (
                (ab_c * ab_d < 0 and cd_a * cd_b < 0)
                or (ab_c == 0 and on(a, b, c))
                or (ab_d == 0 and on(a, b, d))
                or (cd_a == 0 and on(c, d, a))
                or (cd_b == 0 and on(c, d, b))
            ):
                raise ArchitectureError(f"{field} has intersecting edges.")


def _validate_state(data: dict[str, Any]) -> None:
    if isinstance(data, dict) and "document_id" not in data:
        raise ArchitectureError(
            "ak_identity",
            "Saved document lacks its persistent document_id.",
            "Recreate fixtures with Document.create; do not derive identity from a name.",
        )
    if not isinstance(data, dict) or set(data) != {
        "schema",
        "document_id",
        "units",
        "revision",
        "project",
        "entities",
    }:
        raise ArchitectureError("Document fields do not match tee-architecture/1.")
    if data["schema"] != SCHEMA or data["units"] != "mm":
        raise ArchitectureError("Document must declare tee-architecture/1 and mm units.")
    identity = data["document_id"]
    try:
        valid_identity = isinstance(identity, str) and str(uuid.UUID(identity)) == identity
    except (ValueError, AttributeError):
        valid_identity = False
    if not valid_identity:
        raise ArchitectureError(
            "ak_identity",
            "document_id must be a persistent canonical UUID.",
            "Create a document through Document.create; preserve its identity when saving.",
        )
    if type(data["revision"]) is not int or data["revision"] < 0:
        raise ArchitectureError("revision must be a nonnegative integer.")
    project = data["project"]
    if not isinstance(project, dict) or set(project) != {"name", "jurisdiction", "facts"}:
        raise ArchitectureError("project needs name, jurisdiction and facts.")
    _text(project["name"], "project.name")
    jurisdiction = project["jurisdiction"]
    if not isinstance(jurisdiction, dict) or set(jurisdiction) != {
        "country",
        "region",
        "municipality",
    }:
        raise ArchitectureError("jurisdiction needs country, region and municipality.")
    if any(
        v is not None and (not isinstance(v, str) or len(v) > 256) for v in jurisdiction.values()
    ):
        raise ArchitectureError("Jurisdiction values must be text or null (unknown).")
    if not isinstance(project["facts"], dict):
        raise ArchitectureError("project.facts must be an object.")
    _json(project, limit=32_000)
    entities = data["entities"]
    if (
        not isinstance(entities, dict)
        or len(entities) > MAX_ENTITIES
        or any(not isinstance(e, dict) for e in entities.values())
    ):
        raise ArchitectureError(f"A document supports at most {MAX_ENTITIES} entities.")
    for eid, entity in entities.items():
        if not isinstance(eid, str) or not _ID.fullmatch(eid):
            raise ArchitectureError("Entity IDs use 1-80 letters, digits, underscore or hyphen.")
        if not isinstance(entity, dict) or entity.get("id") != eid:
            raise ArchitectureError(f"Entity {eid} must carry its matching id.")
        kind = entity.get("kind")
        if not isinstance(kind, str) or kind not in _FIELDS:
            raise ArchitectureError(f"Entity {eid} has an unknown kind.")
        required = _FIELDS[kind] - {"form"}
        if not required <= entity.keys() or set(entity) - (_COMMON | _FIELDS[kind]):
            raise ArchitectureError(f"Entity {eid} fields do not match kind {kind}.")
        _text(entity.get("name"), f"{eid}.name")
        for field in ("properties", "provenance"):
            if field in entity:
                if not isinstance(entity[field], dict):
                    raise ArchitectureError(f"{eid}.{field} must be an object.")
                _json(entity[field], limit=16_000)
        if "storey" in entity:
            ref = entity["storey"]
            if not isinstance(ref, str) or entities.get(ref, {}).get("kind") != "storey":
                raise ArchitectureError(
                    "ak_reference", f"{eid}.storey does not reference a storey."
                )
        for field in ("height", "thickness"):
            if field in entity:
                positive(entity[field], f"{eid}.{field}")
        if kind == "storey":
            number(entity["elevation"], f"{eid}.elevation")
        elif kind == "wall":
            _point(entity["start"], f"{eid}.start")
            _point(entity["end"], f"{eid}.end")
            if math.dist(entity["start"], entity["end"]) <= 1e-6:
                raise ArchitectureError(f"{eid} wall has zero length.")
        elif kind in {"space", "slab", "roof"}:
            _polygon(entity["polygon"], f"{eid}.polygon")
            if kind == "roof":
                number(entity["base_height"], f"{eid}.base_height", minimum=0)
                if entity.get("form") != "flat":
                    raise ArchitectureError(f"{eid} roof must explicitly declare form='flat'.")
        elif kind == "opening":
            wall = entities.get(entity["wall"]) if isinstance(entity["wall"], str) else None
            if not isinstance(wall, dict) or wall.get("kind") != "wall":
                raise ArchitectureError("ak_reference", f"{eid}.wall does not reference a wall.")
            for field in ("offset", "sill"):
                number(entity[field], f"{eid}.{field}", minimum=0)
            positive(entity["width"], f"{eid}.width")
            if not isinstance(entity["fill"], str) or entity["fill"] not in {
                "door",
                "window",
                "void",
            }:
                raise ArchitectureError(f"{eid}.fill must be door, window or void.")
            # Validate the host before measuring even if a malformed host occurs later in map order.
            _point(wall.get("start"), f"{wall.get('id')}.start")
            _point(wall.get("end"), f"{wall.get('id')}.end")
            positive(wall.get("height"), f"{wall.get('id')}.height")
            if (
                entity["offset"] + entity["width"] > math.dist(wall["start"], wall["end"])
                or entity["sill"] + entity["height"] > wall["height"]
            ):
                raise ArchitectureError("ak_host_bounds", f"{eid} opening exceeds its host wall.")
        elif kind == "cabinet":
            _point(entity["origin"], f"{eid}.origin", 3)
            from tee.architecture.cabinets import panels

            panels(entity)
    openings = [e for e in entities.values() if e["kind"] == "opening"]
    for i, a in enumerate(openings):
        for b in openings[i + 1 :]:
            if a["wall"] == b["wall"] and (
                min(a["offset"] + a["width"], b["offset"] + b["width"])
                > max(a["offset"], b["offset"])
                and min(a["sill"] + a["height"], b["sill"] + b["height"])
                > max(a["sill"], b["sill"])
            ):
                raise ArchitectureError("ak_overlap", f"Openings {a['id']} and {b['id']} overlap.")

    if project["facts"].get("wall_join_policy") is not None:
        from .exchange import validate_geometry_policy

        validate_geometry_policy(data)


class Document:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = copy.deepcopy(data)
        self._data.setdefault("history", [])
        self.validate()

    @classmethod
    def create(cls, name: str) -> Document:
        return cls(
            {
                "schema": SCHEMA,
                "document_id": str(uuid.uuid4()),
                "units": "mm",
                "revision": 0,
                "project": {
                    "name": name,
                    "jurisdiction": {
                        "country": None,
                        "region": None,
                        "municipality": None,
                    },
                    "facts": {},
                },
                "entities": {},
            }
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        if not isinstance(data, dict):
            raise ArchitectureError("Document must be an object.")
        return cls(data)

    @property
    def data(self) -> dict[str, Any]:
        return self.to_dict()

    @property
    def entities(self) -> dict[str, Any]:
        return copy.deepcopy(self._data["entities"])

    @property
    def revision(self) -> int:
        return self._data["revision"]

    def to_dict(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

    def validate(self) -> dict[str, Any]:
        _json(self._data)
        current = {k: v for k, v in self._data.items() if k != "history"}
        _validate_state(current)
        history = self._data.get("history", [])
        if not isinstance(history, list) or len(history) > MAX_HISTORY:
            raise ArchitectureError(f"history supports at most {MAX_HISTORY} states.")
        previous = -1
        for state in history:
            _validate_state(state)
            if state["document_id"] != self._data["document_id"]:
                raise ArchitectureError("ak_identity", "Undo history belongs to another document.")
            if not previous < state["revision"] < self.revision:
                raise ArchitectureError("History revisions must increase below current revision.")
            previous = state["revision"]
        return {"ok": True, "revision": self.revision, "entities": len(self._data["entities"])}

    def _revision_check(self, expected: int | None) -> None:
        if expected is not None and (type(expected) is not int or expected != self.revision):
            raise ArchitectureError(
                "ak_conflict", "Document revision changed.", "Reload and retry."
            )

    def apply(
        self, operations: list[dict[str, Any]], expected_revision: int | None = None
    ) -> dict[str, Any]:
        self._revision_check(expected_revision)
        if not isinstance(operations, list) or not 1 <= len(operations) <= 256:
            raise ArchitectureError("ak_limit", "apply needs 1-256 operations.")
        _json(operations, limit=1_000_000)
        candidate = self.to_dict()
        entities = candidate["entities"]
        for operation in operations:
            if not isinstance(operation, dict):
                raise ArchitectureError("Each operation must be an object.")
            op = operation.get("op")
            fields = {
                "create": {"op", "entity"},
                "update": {"op", "id", "changes"},
                "delete": {"op", "id"},
                "project": {"op", "changes"},
            }
            if not isinstance(op, str) or op not in fields or set(operation) != fields[op]:
                raise ArchitectureError("Use create, update, delete or project with their fields.")
            if op == "create":
                entity = copy.deepcopy(operation["entity"])
                if not isinstance(entity, dict):
                    raise ArchitectureError("create.entity must be an object.")
                eid = entity.setdefault("id", "ak_" + uuid.uuid4().hex[:20])
                if not isinstance(eid, str) or not _ID.fullmatch(eid):
                    raise ArchitectureError(
                        "Entity id must use safe letters/digits/underscore/hyphen."
                    )
                if eid in entities:
                    raise ArchitectureError("ak_duplicate", f"Entity {eid} already exists.")
                if entity.get("kind") == "roof":
                    entity.setdefault("form", "flat")
                entities[eid] = entity
            elif op in {"update", "delete"}:
                eid = operation["id"]
                if not isinstance(eid, str) or eid not in entities:
                    raise ArchitectureError("ak_reference", "Entity id does not exist.")
                if op == "delete":
                    del entities[eid]
                else:
                    changes = operation["changes"]
                    if not isinstance(changes, dict) or {"id", "kind"} & changes.keys():
                        raise ArchitectureError("update.changes must preserve entity id and kind.")
                    entities[eid].update(copy.deepcopy(changes))
            else:
                changes = operation["changes"]
                if not isinstance(changes, dict) or set(changes) - {
                    "name",
                    "jurisdiction",
                    "facts",
                }:
                    raise ArchitectureError("project changes may set name, jurisdiction or facts.")
                for key, value in changes.items():
                    if key == "jurisdiction" and isinstance(value, dict):
                        candidate["project"][key].update(copy.deepcopy(value))
                    else:
                        candidate["project"][key] = copy.deepcopy(value)
        prior = {k: copy.deepcopy(v) for k, v in self._data.items() if k != "history"}
        candidate["revision"] += 1
        candidate["history"] = (candidate["history"] + [prior])[-MAX_HISTORY:]
        validated = Document.from_dict(candidate)
        before = self._data["entities"]
        result = {
            "ok": True,
            "revision": validated.revision,
            "created": sorted(entities.keys() - before.keys()),
            "updated": sorted(
                k for k in entities.keys() & before.keys() if entities[k] != before[k]
            ),
            "deleted": sorted(before.keys() - entities.keys()),
        }
        self._data = validated._data
        return result

    def undo(self, expected_revision: int | None = None) -> dict[str, Any]:
        self._revision_check(expected_revision)
        if not self._data["history"]:
            raise ArchitectureError("ak_no_undo", "No retained command to undo.")
        candidate = copy.deepcopy(self._data["history"][-1])
        candidate["revision"] = self.revision + 1
        candidate["history"] = copy.deepcopy(self._data["history"][:-1])
        self._data = Document.from_dict(candidate)._data
        return {"ok": True, "revision": self.revision, "undone": True}

    def summary(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "document_id": self._data["document_id"],
            "units": "mm",
            "revision": self.revision,
            "project": {
                k: copy.deepcopy(v) for k, v in self._data["project"].items() if k != "facts"
            },
            "fact_count": len(self._data["project"]["facts"]),
            "entities": len(self._data["entities"]),
            "counts": dict(
                sorted(Counter(e["kind"] for e in self._data["entities"].values()).items())
            ),
            "undo_available": len(self._data["history"]),
        }
