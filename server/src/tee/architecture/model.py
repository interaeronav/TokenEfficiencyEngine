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
    "wall": {"storey", "start", "end", "thickness", "height", "base_offset"},
    "virtual_boundary": {"storey", "start", "end", "height", "base_offset", "space_ids"},
    "opening": {"wall", "offset", "width", "height", "sill", "fill"},
    "space": {
        "storey",
        "polygon",
        "height",
        "additional_polygons",
        "base_offset",
        "environment",
        "conditioned",
    },
    "slab": {"storey", "polygon", "thickness", "base_offset"},
    "slab_opening": {"slab", "polygon"},
    "roof": {"storey", "polygon", "thickness", "base_height", "form", "pitch_deg", "planes"},
    "stair": {
        "storey",
        "top_storey",
        "start",
        "direction_deg",
        "width",
        "riser_count",
        "going",
        "waist_thickness",
        "landing_depth",
        "headroom_target_mm",
    },
    "furnishing": {"storey", "origin", "size", "category"},
    "member": {"storey", "origin", "profile", "holes", "axis", "x_direction", "length", "role"},
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
        required = _FIELDS[kind] - {
            "form",
            "pitch_deg",
            "headroom_target_mm",
            "base_offset",
            "additional_polygons",
            "space_ids",
            "planes",
            "environment",
            "conditioned",
            "holes",
        }
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
        if "rotation_deg" in entity.get("properties", {}):
            if kind not in {"furnishing", "cabinet"}:
                raise ArchitectureError("rotation_deg is supported for furnishings and cabinets.")
            number(entity["properties"]["rotation_deg"], f"{eid}.rotation_deg")
        for field in ("height", "thickness"):
            if field in entity:
                positive(entity[field], f"{eid}.{field}")
        if "base_offset" in entity:
            number(entity["base_offset"], f"{eid}.base_offset")
        if kind == "storey":
            number(entity["elevation"], f"{eid}.elevation")
        elif kind in {"wall", "virtual_boundary"}:
            _point(entity["start"], f"{eid}.start")
            _point(entity["end"], f"{eid}.end")
            if math.dist(entity["start"], entity["end"]) <= 1e-6:
                raise ArchitectureError(f"{eid} {kind} has zero length.")
            if kind == "virtual_boundary":
                refs = entity.get("space_ids", [])
                if (
                    not isinstance(refs, list)
                    or len(refs) > 2
                    or any(not isinstance(ref, str) for ref in refs)
                    or len(set(refs)) != len(refs)
                    or any(entities.get(ref, {}).get("kind") != "space" for ref in refs)
                    or any(entities[ref]["storey"] != entity["storey"] for ref in refs)
                ):
                    raise ArchitectureError(
                        "ak_reference",
                        f"{eid}.space_ids needs up to two distinct spaces on its storey.",
                    )
                binding = entity.get("properties", {}).get("bim", {})
                if binding.get("material_id") or binding.get("type_id"):
                    raise ArchitectureError(
                        "ak_boundary_semantics",
                        f"{eid} is nonphysical and cannot carry a material or physical type.",
                    )
        elif kind in {"space", "slab", "roof"}:
            _polygon(entity["polygon"], f"{eid}.polygon")
            if kind == "space":
                from .spatial import space_environment

                environment = space_environment(entity)
                if not isinstance(environment, str) or environment not in {
                    "interior",
                    "exterior",
                    "unclassified",
                }:
                    raise ArchitectureError(
                        f"{eid}.environment must be interior, exterior or unclassified."
                    )
                if (
                    entity.get("conditioned") is not None
                    and type(entity["conditioned"]) is not bool
                ):
                    raise ArchitectureError(f"{eid}.conditioned must be true, false or null.")
                if environment == "exterior" and entity.get("conditioned") is True:
                    raise ArchitectureError(
                        f"{eid} exterior space cannot be an enclosed conditioned zone."
                    )
                legacy = entity.get("properties", {}).get("outdoor")
                if legacy is not None and (
                    type(legacy) is not bool
                    or (
                        "environment" in entity
                        and environment != ("exterior" if legacy else "interior")
                    )
                ):
                    raise ArchitectureError(
                        f"{eid} environment conflicts with legacy properties.outdoor."
                    )
                extra = entity.get("additional_polygons", [])
                if not isinstance(extra, list) or len(extra) > 31:
                    raise ArchitectureError(
                        f"{eid}.additional_polygons supports up to 31 exterior rings."
                    )
                for index, ring in enumerate(extra):
                    _polygon(ring, f"{eid}.additional_polygons[{index}]")
                if extra:
                    from .spatial import space_geometry

                    shape = space_geometry(entity)
                    if not shape.is_valid:
                        raise ArchitectureError(
                            "ak_space_parts",
                            f"{eid} space parts overlap or share an edge; union them first.",
                        )
            if kind == "roof":
                number(entity["base_height"], f"{eid}.base_height", minimum=0)
                from .systems import validate_roof

                validate_roof(entity)
        elif kind == "member":
            from .members import validate_member

            validate_member(entity)
        elif kind == "stair":
            from .systems import stair_dimensions

            _point(entity["start"], f"{eid}.start")
            stair_dimensions(entity, entities)
            if entity.get("headroom_target_mm") is not None:
                positive(entity["headroom_target_mm"], f"{eid}.headroom_target_mm")
        elif kind == "slab_opening":
            _polygon(entity["polygon"], f"{eid}.polygon")
            ref = entity["slab"]
            if not isinstance(ref, str) or entities.get(ref, {}).get("kind") != "slab":
                raise ArchitectureError("ak_reference", f"{eid}.slab does not reference a slab.")
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
        elif kind == "furnishing":
            _point(entity["origin"], f"{eid}.origin", 3)
            _point(entity["size"], f"{eid}.size", 3)
            for value in entity["size"]:
                positive(value, f"{eid}.size")
            if not isinstance(entity["category"], str) or entity["category"] not in {
                "bed",
                "sofa",
                "table",
                "chair",
                "basin",
                "wc",
                "shower",
                "appliance",
                "storage",
            }:
                raise ArchitectureError(f"{eid}.category is not a supported furnishing category.")
        elif kind == "cabinet":
            _point(entity["origin"], f"{eid}.origin", 3)
            from tee.architecture.cabinets import panels

            panels(entity)
    from .penetrations import validate_openings

    validate_openings(entities)
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

    for eid, wall in entities.items():
        if wall["kind"] != "wall":
            continue
        gross = math.dist(wall["start"], wall["end"]) * wall["height"]
        removed = sum(o["width"] * o["height"] for o in openings if o["wall"] == eid)
        if gross - removed <= 1e-6:
            raise ArchitectureError(
                "ak_empty_wall",
                f"{eid} has no physical wall material after its openings.",
                (
                    "Use a virtual_boundary for an unbuilt/reference plane, "
                    "or author the actual framing; do not invent wall material."
                ),
            )

    if project["facts"].get("wall_join_policy") is not None:
        from .exchange import validate_geometry_policy

        validate_geometry_policy(data)

    from .bim import validate_bim

    validate_bim(data)
    from .distribution import validate_distribution

    validate_distribution(data)
    from .thermal import validate_thermal

    validate_thermal(data)


def _resolve_available_types(state: dict[str, Any], explicit_updates: dict[str, set[str]]) -> None:
    """Propagate available bindings in command order, without partial validation.

    A later edit must see effective values and overrides from earlier commands.
    Resolving only at batch end also loses values when a type parameter is removed
    and turns earlier untyped edits into overrides of newly introduced parameters.
    Unknown forward references and malformed temporary states are left for the
    final resolver/validator; no candidate is published before that succeeds.
    """
    from .bim import PARAMETERS

    facts = state["project"].get("facts", {})
    library = facts.get("bim", {}) if isinstance(facts, dict) else {}
    types = library.get("types", {}) if isinstance(library, dict) else {}
    for eid in list(explicit_updates):
        if eid not in state["entities"]:
            explicit_updates.pop(eid)
    for eid, entity in state["entities"].items():
        props = entity.get("properties", {})
        binding = props.get("bim", {}) if isinstance(props, dict) else None
        if isinstance(binding, dict) and not binding.get("type_id"):
            explicit_updates.pop(eid, None)
            continue
        if not isinstance(binding, dict) or not isinstance(binding.get("type_id"), str):
            continue
        definition = types.get(binding["type_id"]) if isinstance(types, dict) else None
        if not isinstance(definition, dict) or definition.get("kind") != entity.get("kind"):
            continue
        kind = definition.get("kind")
        if not isinstance(kind, str) or kind not in PARAMETERS:
            continue
        parameters = definition.get("parameters", {})
        overrides = binding.get("overrides", [])
        if (
            not isinstance(parameters, dict)
            or set(parameters) - PARAMETERS[kind]
            or not isinstance(overrides, list)
            or any(not isinstance(field, str) for field in overrides)
        ):
            continue
        selected = set(overrides) | (explicit_updates.pop(eid, set()) & parameters.keys())
        binding["overrides"] = sorted(selected)
        for key, value in parameters.items():
            target = props if key == "assembly" else entity
            if key not in selected and target.get(key) != value:
                target[key] = copy.deepcopy(value)


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
        explicit_updates: dict[str, set[str]] = {}
        for operation in operations:
            if not isinstance(operation, dict):
                raise ArchitectureError("Each operation must be an object.")
            op = operation.get("op")
            fields = {
                "create": {"op", "entity"},
                "update": {"op", "id", "changes"},
                "delete": {"op", "id"},
                "project": {"op", "changes"},
                "bim_material": {"op", "id", "definition"},
                "bim_type": {"op", "id", "definition"},
                "bim_assign": {"op", "id", "type_id"},
                "bim_override": {"op", "id", "values"},
            }
            if not isinstance(op, str) or op not in fields or set(operation) != fields[op]:
                raise ArchitectureError(
                    "Use create/update/delete/project or bim_material/bim_type/"
                    "bim_assign/bim_override with their declared fields."
                )
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
                    previous = entities[eid]
                    changed = explicit_updates.setdefault(eid, set())
                    changed.update(
                        key for key, value in changes.items() if previous.get(key) != value
                    )
                    props = changes.get("properties")
                    previous_props = previous.get("properties", {})
                    previous_assembly = (
                        previous_props.get("assembly") if isinstance(previous_props, dict) else None
                    )
                    if (
                        isinstance(props, dict)
                        and "assembly" in props
                        and props["assembly"] != previous_assembly
                    ):
                        changed.add("assembly")
                    entities[eid].update(copy.deepcopy(changes))
            elif op in {"bim_material", "bim_type"}:
                key, definition = operation["id"], operation["definition"]
                if not isinstance(key, str) or not _ID.fullmatch(key):
                    raise ArchitectureError("BIM library IDs need safe letters/digits/_/-.")
                if not isinstance(definition, dict):
                    raise ArchitectureError("BIM definition must be an object.")
                library = candidate["project"]["facts"].setdefault(
                    "bim", {"schema": "tee-bim/1", "materials": {}, "types": {}}
                )
                if not isinstance(library, dict):
                    raise ArchitectureError("project.facts.bim must be an object.")
                table = library.setdefault("materials" if op == "bim_material" else "types", {})
                if not isinstance(table, dict):
                    raise ArchitectureError("BIM library tables must be objects keyed by ID.")
                table[key] = copy.deepcopy(definition)
            elif op in {"bim_assign", "bim_override"}:
                eid = operation["id"]
                if not isinstance(eid, str) or eid not in entities:
                    raise ArchitectureError("ak_reference", "BIM instance id does not exist.")
                entity = entities[eid]
                props = entity.setdefault("properties", {})
                if not isinstance(props, dict):
                    raise ArchitectureError("Instance properties must be an object.")
                binding = props.setdefault("bim", {})
                if not isinstance(binding, dict):
                    raise ArchitectureError("Instance properties.bim must be an object.")
                if op == "bim_assign":
                    type_id = operation["type_id"]
                    if not isinstance(type_id, str) or not _ID.fullmatch(type_id):
                        raise ArchitectureError("Use a valid BIM type ID.")
                    binding.update({"type_id": type_id, "overrides": []})
                    explicit_updates.pop(eid, None)
                else:
                    values = operation["values"]
                    if not isinstance(values, dict) or not values:
                        raise ArchitectureError("bim_override.values needs named parameters.")
                    type_id = binding.get("type_id")
                    library = candidate["project"]["facts"].get("bim", {})
                    if not isinstance(library, dict):
                        raise ArchitectureError("project.facts.bim must be an object.")
                    types = library.get("types", {})
                    if not isinstance(types, dict):
                        raise ArchitectureError("BIM types must be an object keyed by ID.")
                    definition = types.get(type_id) if isinstance(type_id, str) else None
                    if not isinstance(definition, dict):
                        raise ArchitectureError("Assign an existing BIM type before overriding it.")
                    parameters = definition.get("parameters", {})
                    if not isinstance(parameters, dict) or set(values) - parameters.keys():
                        raise ArchitectureError(
                            "Override only parameters supplied by this BIM type."
                        )
                    overrides = binding.get("overrides", [])
                    if not isinstance(overrides, list) or any(
                        not isinstance(v, str) for v in overrides
                    ):
                        raise ArchitectureError("BIM overrides must list parameter names.")
                    selected = set(overrides)
                    for field, value in values.items():
                        if value is None:
                            selected.discard(field)
                            explicit_updates.get(eid, set()).discard(field)
                        else:
                            selected.add(field)
                            target = props if field == "assembly" else entity
                            target[field] = copy.deepcopy(value)
                    binding["overrides"] = sorted(selected)
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
            _resolve_available_types(candidate, explicit_updates)
        from .bim import resolve_types

        resolve_types(candidate, explicit_updates)
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
        changed_levels = {
            key
            for key in entities.keys() & before.keys()
            if entities[key]["kind"] == "storey"
            and entities[key]["elevation"] != before[key]["elevation"]
        }
        changed_slabs = {
            e["slab"]
            for source in (before, entities)
            for key, e in source.items()
            if e["kind"] == "slab_opening" and before.get(key) != entities.get(key)
        }
        dependents = sorted(
            key
            for key, entity in entities.items()
            if (
                (
                    entity["kind"] in {"roof", "stair", "slab", "wall", "space", "virtual_boundary"}
                    and {entity["storey"], entity.get("top_storey")} & changed_levels
                )
                or key in changed_slabs
                or (
                    entity["kind"] == "opening"
                    and (
                        entities[entity["wall"]] != before.get(entity["wall"])
                        or entities[entity["wall"]]["storey"] in changed_levels
                    )
                )
                or (
                    entity["kind"] == "slab_opening"
                    and (
                        entities[entity["slab"]] != before.get(entity["slab"])
                        or entities[entity["slab"]]["storey"] in changed_levels
                    )
                )
            )
            and key not in result["created"]
            and key not in result["updated"]
        )
        if dependents:
            result["dependent_geometry"] = dependents
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
