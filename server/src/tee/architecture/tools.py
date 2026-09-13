"""Progressive TEE interface to the headless architectural document service."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tee.kernel import trust, trustctx
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

from .guidance import guide
from .model import ArchitectureError
from .service import ArchitectureService


def register_architecture_tools(app: Any, project_root: Path | str) -> None:
    service = ArchitectureService(project_root)
    app.architecture = service
    model = {"type": "string", "pattern": "^building_[a-f0-9]{16}$"}
    identifier = {"type": "string", "minLength": 1, "maxLength": 100}
    revision = {"type": "integer", "minimum": 0}

    def wrap(
        fn: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> Callable[[dict[str, Any]], dict[str, Any]]:
        def call(args: dict[str, Any]) -> dict[str, Any]:
            try:
                return fn(args)
            except ArchitectureError as exc:
                raise TeeError(
                    getattr(exc, "code", "architecture_invalid"),
                    str(exc),
                    fix=getattr(exc, "fix", None),
                ) from exc
            except (ImportError, OSError, ValueError) as exc:
                raise TeeError(
                    "architecture_operation",
                    f"Architectural operation failed: {exc}",
                    fix=(
                        "Check the selected file, explicit dimensions and optional library"
                        " availability."
                    ),
                ) from exc

        return call

    def job(
        label: str,
        fn: Callable[[dict[str, Any], Callable[[], bool]], dict[str, Any]],
        args: dict[str, Any],
    ) -> dict[str, Any]:
        cancelled = threading.Event()

        def execute() -> dict[str, Any]:
            app.registry.require(trust.capability_for(label), name=label)
            return wrap(lambda a: fn(a, cancelled.is_set))(args)

        job_id = app.jobs.submit(label, execute, on_cancel=cancelled.set)
        return {"job": job_id, "state": "queued", "model_id": args["model_id"]}

    def open_gui(args: dict[str, Any]) -> dict[str, Any]:
        if not args.get("launch", False):
            return {
                "ok": True,
                "product": "archkiln",
                "prepared": True,
                "launched": False,
                "next": (
                    "ak_open launch=true starts its local optional GUI; headless tools need no GUI."
                ),
            }
        app.registry.require("call-engine", name="ak_open launch")
        from .gui import ArchitectureGui

        gui = getattr(app, "architecture_gui", None)
        if gui is None:
            inherited_taint = trustctx.taint()

            def authorize(mutation: bool) -> None:
                decision = trust.check(
                    "write-artifacts" if mutation else "read-state",
                    caller="gateway-fronted",
                    grants=app.registry.grants,
                    taint=inherited_taint,
                )
                if not decision.allowed:
                    raise TeeError("architecture_gui_denied", decision.reason)

            gui = ArchitectureGui(service, authorize=authorize)
            gui.start()
            app.architecture_gui = gui
        return {
            "ok": True,
            "launched": True,
            "url": gui.url,
            "note": (
                "Local authenticated GUI; the same model operations and current pr"
                "oject grants apply."
            ),
        }

    rows = [
        (
            "ak_guide",
            (
                "CADAgent headless architecture/BIM lessons: build, revise and inspect pitched "
                "roofs, stairs, typed houses and cabinets. Omit topic for the compact index; "
                "returned calls do not execute themselves."
            ),
            {"topic": {"type": "string", "minLength": 1, "maxLength": 100}},
            [],
            lambda a: guide(a.get("topic")),
        ),
        (
            "ak_status",
            "archkiln model index, explicit units and optional architectural GUI readiness.",
            {},
            [],
            lambda a: service.status(),
        ),
        (
            "ak_create",
            (
                "Create a headless model. compact-dwelling includes two bedrooms, bathroom, "
                "living/kitchen, typed wall/opening assemblies and four cabinets; "
                "compact-house retains the legacy fixture. Examples need project review."
            ),
            {
                "name": {"type": "string", "minLength": 1, "maxLength": 200},
                "preset": {
                    "type": "string",
                    "enum": ["empty", "compact-house", "compact-dwelling"],
                },
            },
            ["name"],
            lambda a: service.create(a["name"], a.get("preset", "empty")),
        ),
        (
            "ak_edit",
            (
                "Atomic create/update/delete/project or bim_material/bim_type/bim_assign/"
                "bim_override operations in mm. Type propagation, instance overrides, "
                "host validation and undo; expected_revision rejects stale edits."
            ),
            {
                "model_id": model,
                "operations": {
                    "type": "array",
                    "items": {"type": "object"},
                    "minItems": 1,
                    "maxItems": 200,
                },
                "expected_revision": revision,
            },
            ["model_id", "operations"],
            lambda a: service.edit(a["model_id"], a["operations"], a.get("expected_revision")),
        ),
        (
            "ak_query",
            (
                "Paginated entity index or explicit entity detail. Model detail=bim, quality "
                "schedules, performance, distribution or thermal returns one collection "
                "and page metadata; report defaults are 5 rows. "
                "Use collection/offset/limit to retrieve subsequent rows. Cabinet detail "
                "adds BOM, hardware, costs and optional stock nesting in mm."
            ),
            {
                "model_id": model,
                "entity_id": identifier,
                "detail": {
                    "type": "string",
                    "enum": [
                        "entity",
                        "cabinet",
                        "bim",
                        "quality",
                        "schedules",
                        "performance",
                        "distribution",
                        "thermal",
                    ],
                },
                "offset": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "collection": {
                    "type": "string",
                    "enum": [
                        "openings",
                        "rooms",
                        "walls",
                        "cabinets",
                        "roofs",
                        "stairs",
                        "slabs",
                        "slab_openings",
                        "virtual_boundaries",
                        "members",
                        "spaces",
                        "routes",
                        "types",
                        "materials",
                        "instances",
                        "unconstructed_fillings",
                        "information_gaps",
                        "systems",
                        "ports",
                        "connections",
                        "surfaces",
                        "assemblies",
                        "zones",
                        "issues",
                        "portals",
                        "room_access",
                    ],
                    "description": (
                        "Model report collection; counts names the collections for each detail."
                    ),
                },
                "kind": {"type": "string", "minLength": 1},
                "stock": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["sheet_width", "sheet_height", "kerf"],
                    "properties": {
                        "sheet_width": {"type": "number", "exclusiveMinimum": 0},
                        "sheet_height": {"type": "number", "exclusiveMinimum": 0},
                        "kerf": {"type": "number", "minimum": 0},
                        "allow_rotate": {"type": "boolean"},
                        "algorithm": {"type": "string", "enum": ["best_fit", "rows"]},
                        "trim_mm": {"type": "number", "minimum": 0},
                    },
                },
            },
            ["model_id"],
            lambda a: service.query(
                a["model_id"],
                a.get("entity_id"),
                a.get("detail", "entity"),
                a.get("stock"),
                a.get("offset", 0),
                a.get("limit"),
                a.get("kind"),
                a.get("collection"),
            ),
        ),
        (
            "ak_undo",
            (
                "Undo the latest architectural transaction while advancing its rev"
                "ision and preserving stable IDs."
            ),
            {"model_id": model, "expected_revision": revision},
            ["model_id"],
            lambda a: service.undo(a["model_id"], a.get("expected_revision")),
        ),
        (
            "ak_import",
            (
                "Inspect a project-relative mesh, LiDAR or Unreal geometry manifes"
                "t and propose measured candidates as a job. Explicit source units"
                " and tolerance; no automatic authoring or concealed-property gues"
                "ses."
            ),
            {
                "model_id": model,
                "path": {"type": "string", "maxLength": 1024},
                "units": {"type": "string", "enum": ["mm", "cm", "m", "in", "ft"]},
                "tolerance_mm": {"type": "number", "exclusiveMinimum": 0},
                "transform": {
                    "type": "array",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "number"},
                    },
                },
            },
            ["model_id", "path", "units", "tolerance_mm"],
            lambda a: job(
                "ak_import",
                lambda x, cancelled: service.import_source(
                    x["model_id"],
                    x["path"],
                    x["units"],
                    x["tolerance_mm"],
                    x.get("transform"),
                    cancelled=cancelled,
                ),
                a,
            ),
        ),
        (
            "ak_candidates",
            (
                "Review retained source identity, measured fit and uncertain archi"
                "tectural candidates before promotion."
            ),
            {"model_id": model, "import_id": identifier},
            ["model_id", "import_id"],
            lambda a: service.candidates(a["model_id"], a["import_id"]),
        ),
        (
            "ak_promote",
            (
                "Promote one reviewed measured candidate using explicit constructi"
                "on height, thickness and centreline_offset_mm; no wall centreline"
                " is inferred from a visible face."
            ),
            {
                "model_id": model,
                "import_id": identifier,
                "candidate_id": identifier,
                "storey": identifier,
                "overrides": {"type": "object"},
                "expected_revision": revision,
            },
            ["model_id", "import_id", "candidate_id", "storey", "overrides"],
            lambda a: service.promote(
                a["model_id"],
                a["import_id"],
                a["candidate_id"],
                a["storey"],
                a["overrides"],
                a.get("expected_revision"),
            ),
        ),
        (
            "ak_export",
            (
                "Generate revision-bound IFC, architectural/shop drawings and sche"
                "dules as a job. Geometry/schema evidence is separate from legal c"
                "ompliance and fabrication approval. cabinet_cnc requires cabinet_id and "
                "a fully explicit virtual-router setup; it does not execute or commission "
                "a machine."
            ),
            {
                "model_id": model,
                "format": {
                    "type": "string",
                    "enum": ["all", "ifc", "drawings", "glb", "json", "cabinet_cnc"],
                },
                "expected_revision": revision,
                "cabinet_id": identifier,
                "cnc_setup": {"type": "object"},
            },
            ["model_id"],
            lambda a: job(
                "ak_export",
                lambda x, cancelled: service.export(
                    x["model_id"],
                    x.get("format", "all"),
                    cancelled=cancelled,
                    cabinet_id=x.get("cabinet_id"),
                    cnc_setup=x.get("cnc_setup"),
                    expected_revision=x.get("expected_revision"),
                ),
                a,
            ),
        ),
        (
            "ak_check",
            (
                "Check model validity and explicit worldwide jurisdiction rule pac"
                "ks. Missing sources, facts or coverage remain not_verified; this "
                "does not certify a building."
            ),
            {
                "model_id": model,
                "pack_paths": {"type": "array", "items": {"type": "string"}, "maxItems": 32},
                "assessment_date": {"type": "string", "maxLength": 10},
            },
            ["model_id"],
            lambda a: service.check(a["model_id"], a.get("pack_paths"), a.get("assessment_date")),
        ),
        (
            "ak_ifc_reference",
            "Retain an exact IFC reference in this model as a job. Preserves unsupported "
            "objects/relationships and source identity; creates no native approximation.",
            {
                "model_id": model,
                "path": {"type": "string", "maxLength": 1024},
                "expected_revision": revision,
                "expected_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            },
            ["model_id", "path"],
            lambda a: job(
                "ak_ifc_reference",
                lambda x, cancelled: service.ifc_reference(
                    x["model_id"],
                    x["path"],
                    x.get("expected_revision"),
                    x.get("expected_sha256"),
                    cancelled,
                ),
                a,
            ),
        ),
        (
            "ak_ifc_query",
            "Inspect a retained IFC with paged GUID/type/units/georeference information. "
            "full adds semantic detail; native returns only measured supported wall "
            "candidates requiring explicit storey/semantic mapping before authoring.",
            {
                "model_id": model,
                "reference_id": identifier,
                "detail": {"type": "string", "enum": ["index", "full", "native"]},
                "offset": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                "guids": {"type": "array", "items": {"type": "string"}, "maxItems": 16},
            },
            ["model_id", "reference_id"],
            lambda a: service.ifc_query(
                a["model_id"],
                a["reference_id"],
                a.get("detail", "index"),
                a.get("offset", 0),
                a.get("limit", 50),
                a.get("guids"),
            ),
        ),
        (
            "ak_ids",
            "Assess a retained IFC against an explicit project IDS file as a job. "
            "Validates IDS XML and all applicable entities including cardinality; "
            "information conformance remains separate from geometry and legal approval.",
            {
                "model_id": model,
                "reference_id": identifier,
                "ids_path": {"type": "string", "maxLength": 1024},
            },
            ["model_id", "reference_id", "ids_path"],
            lambda a: job(
                "ak_ids",
                lambda x, cancelled: service.ifc_ids(
                    x["model_id"], x["reference_id"], x["ids_path"], cancelled
                ),
                a,
            ),
        ),
        (
            "ak_federate",
            "Write a federation manifest of exact IFC references with explicit "
            "world-mm-to-authoring-mm transforms. Uses full source inventories, "
            "namespaces GUIDs and verifies hashes; expected_revision rejects stale writes.",
            {
                "model_id": model,
                "reference_ids": {
                    "type": "array",
                    "items": identifier,
                    "minItems": 1,
                    "maxItems": 16,
                    "uniqueItems": True,
                },
                "transforms_mm": {"type": "object"},
                "expected_revision": revision,
            },
            ["model_id", "reference_ids", "transforms_mm"],
            lambda a: job(
                "ak_federate",
                lambda x, cancelled: service.ifc_federate(
                    x["model_id"],
                    x["reference_ids"],
                    x["transforms_mm"],
                    cancelled,
                    x.get("expected_revision"),
                ),
                a,
            ),
        ),
        (
            "ak_open",
            (
                "Prepare the optional archkiln GUI; launch=true starts an authenti"
                "cated local interface using the same headless core. No browser wi"
                "ndow opens automatically."
            ),
            {"launch": {"type": "boolean"}},
            [],
            open_gui,
        ),
    ]
    for name, description, properties, required, handler in rows:
        app.registry.register(
            VirtualTool(
                name,
                description,
                {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                wrap(handler),
                tags=["architecture", "bim", "ifc", "building", "cabinet", "archkiln"]
                + (["cadagent", "guide", "lesson", "roof", "stair"] if name == "ak_guide" else []),
            )
        )
