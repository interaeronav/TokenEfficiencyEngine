"""Small progressive structural interface; no always-loaded schemas."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

from . import environment, runner
from .examples import cantilever
from .service import StructuralService


def register_structural_tools(app: Any, project: Path) -> None:
    service = StructuralService(project, getattr(app.config, "structural", {}))
    app.structural = service

    def wrap(fn: Callable[[dict], dict]) -> Callable[[dict], dict]:
        def call(a: dict) -> dict:
            try:
                return fn(a)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                raise TeeError(
                    "structural_invalid",
                    str(exc),
                    fix=(
                        "Review explicit model inputs, current revision and retained solver "
                        "evidence; st_status detail=example shows the input contract."
                    ),
                ) from exc

        return call

    def solve(a: dict) -> dict:
        stop = threading.Event()
        # Snapshot scalars, preventing a caller from mutating a queued task.
        ident, rev, case, engine = a["model_id"], a["expected_revision"], a["case"], a["engine"]

        def run() -> dict:
            app.registry.require("call-engine", name="st_solve")
            return wrap(lambda _: service.solve(ident, rev, case, engine, stop))({})

        return {
            "job": app.jobs.submit("st_solve", run, on_cancel=stop.set),
            "state": "queued",
            "model_id": ident,
        }

    def status(a: dict) -> dict:
        if a.get("detail", "engines") == "example":
            return {
                "model": cantilever(),
                "next": (
                    "st_model model=<model>; then st_solve with returned model_id/revision "
                    "and explicit engine/case."
                ),
            }
        return runner.scan(service.config)

    def schema(props: dict, required: tuple | list = ()) -> dict:
        return {
            "type": "object",
            "properties": props,
            "required": list(required),
            "additionalProperties": False,
        }

    ident = {"type": "string", "pattern": "^structure_[a-f0-9]{16}$"}
    rev = {"type": "integer", "minimum": 1}
    paging = {
        "offset": {"type": "integer", "minimum": 0},
        "limit": {"type": "integer", "minimum": 1, "maximum": 50},
    }
    specs = [
        (
            "st_status",
            (
                "Find structural solvers without launching them; detail=example "
                "provides an explicit synthetic model."
            ),
            schema({"detail": {"type": "string", "enum": ["engines", "example"]}}),
            status,
        ),
        (
            "st_model",
            (
                "Create or replace a structural study: sourced planar Timoshenko frame "
                "in N-mm-MPa-rad. Existing model requires expected_revision. st_status "
                "detail=example shows all fields."
            ),
            schema(
                {"model": {"type": "object"}, "model_id": ident, "expected_revision": rev},
                ["model"],
            ),
            lambda a: service.save(a["model"], a.get("model_id"), a.get("expected_revision")),
        ),
        (
            "st_query",
            "Compact structural model summary or paginated explicit input rows.",
            schema(
                {
                    "model_id": ident,
                    "collection": {
                        "type": "string",
                        "enum": [
                            "summary",
                            "nodes",
                            "elements",
                            "materials",
                            "sections",
                            "supports",
                            "cases",
                            "combinations",
                        ],
                    },
                    **paging,
                },
                ["model_id"],
            ),
            lambda a: service.query(
                a["model_id"],
                a.get("collection", "summary"),
                a.get("offset", 0),
                a.get("limit", 20),
            ),
        ),
        (
            "st_solve",
            (
                "Run a named case/combination through a separate engine; tee_job "
                "reports completion/cancellation. Includes stability, equilibrium and "
                "native force checks. No code-compliance/capacity certification."
            ),
            schema(
                {
                    "model_id": ident,
                    "expected_revision": rev,
                    "case": {"type": "string"},
                    "engine": {"type": "string", "enum": list(runner.ENGINES)},
                },
                ["model_id", "expected_revision", "case", "engine"],
            ),
            solve,
        ),
        (
            "st_result",
            (
                "Verified structural result with stale-input flag; paginate "
                "displacements, reactions or local member end forces."
            ),
            schema(
                {
                    "model_id": ident,
                    "run_id": {"type": "string", "pattern": "^run_[a-f0-9]{16}$"},
                    "collection": {
                        "type": "string",
                        "enum": ["summary", "displacements", "reactions", "element_forces"],
                    },
                    **paging,
                },
                ["model_id", "run_id"],
            ),
            lambda a: service.result(
                a["model_id"],
                a["run_id"],
                a.get("collection", "summary"),
                a.get("offset", 0),
                a.get("limit", 20),
            ),
        ),
        (
            "st_from_bim",
            (
                "Read selected architectural beams/columns/braces/frames into a "
                "paginated centroid-axis geometry candidate with document revision. "
                "Connectivity, analysis plane and engineering properties remain "
                "explicit."
            ),
            schema(
                {
                    "model_id": {"type": "string"},
                    "entity_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "maxItems": 50,
                    },
                    **paging,
                },
                ["model_id", "entity_ids"],
            ),
            lambda a: service.from_bim(
                a["model_id"], a["entity_ids"], a.get("offset", 0), a.get("limit", 10)
            ),
        ),
        (
            "st_environment",
            (
                "Sourced desert and harsh-environment research: concrete/cement "
                "degradation, chloride/sulfate/carbonation, heat, abrasion and soil "
                "investigation; compare open-source software. No invented lifespan."
            ),
            schema(
                {
                    "collection": {"type": "string", "enum": ["mechanisms", "software"]},
                    "exposures": {
                        "type": "array",
                        "items": schema(
                            {
                                "mechanism": {"type": "string"},
                                "status": {
                                    "type": "string",
                                    "enum": ["present", "absent", "unknown"],
                                },
                                "source": {"type": "string"},
                            },
                            ["mechanism", "status", "source"],
                        ),
                    },
                    **paging,
                }
            ),
            lambda a: environment.assess(
                a.get("collection", "mechanisms"),
                a.get("exposures"),
                a.get("offset", 0),
                a.get("limit", 5),
            ),
        ),
    ]
    for name, description, spec, handler in specs:
        app.registry.register(
            VirtualTool(
                name=name,
                description=description,
                schema=spec,
                handler=wrap(handler),
                tags=[
                    "structural",
                    "architecture",
                    "engineering",
                    "desert",
                    "durability",
                    "cadagent",
                ],
            )
        )
