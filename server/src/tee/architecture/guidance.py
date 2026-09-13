"""Executable, progressively disclosed CADAgent lessons on the headless BIM core.

Authoring cards never execute themselves. The client uses normal tee_call grants,
revision checks, jobs and learning observations; no separate agent backend runs.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from tee.kernel.errors import TeeError

TOPICS = {
    "cadagent_roof_stair.build": "Create typed pitched roof and stair study linked to levels.",
    "cadagent_roof_stair.revise": "Raise level; revise roof pitch and riser count atomically.",
    "cadagent_roof_stair.inspect": "Read quantities, issues, drawings and actual IFC geometry.",
    "cadagent_stair_clearance.block": "Add a floor to the initial study; measure its obstruction.",
    "cadagent_stair_clearance.open": "Cut a floor opening and measure headroom.",
    "cadagent_stair_clearance.inspect": "Read slab quantities, headroom witness and exports.",
    "cadagent_bim.build": "Create the typed compact dwelling, including kitchen cabinetry.",
    "cadagent_bim.inspect": "Inspect types, opening heights, cabinet schedules and design issues.",
    "cadagent_circulation.build": (
        "Create exterior circulation with a real profile column and design targets."
    ),
    "cadagent_circulation.inspect": (
        "Measure routes, read information gaps and inspect the shared GUI."
    ),
    "cadagent_services.build": "Create a rotated duct study with a deliberately broken connection.",
    "cadagent_services.inspect": "Measure interface gaps, section agreement and disconnected ends.",
    "cadagent_services.repair": "Repair the measured duct gap and export verified IFC4 port links.",
    "cadagent_thermal.inspect": (
        "Read sourced thermal inputs, selected heat flow and missing coverage."
    ),
}


def _call(tool_name: str, **args: Any) -> dict[str, Any]:
    return {"name": tool_name, "args": args}


def _roof_type(pitch: float) -> dict:
    return {
        "op": "bim_type",
        "id": "roof_type",
        "definition": {
            "name": "Pitched roof study",
            "kind": "roof",
            "parameters": {"form": "gable", "pitch_deg": pitch, "thickness": 200},
        },
    }


def _stair_type(count: int) -> dict:
    return {
        "op": "bim_type",
        "id": "stair_type",
        "definition": {
            "name": "Monolithic stair study",
            "kind": "stair",
            "parameters": {
                "width": 1000,
                "riser_count": count,
                "going": 260,
                "waist_thickness": 150,
                "landing_depth": 1000,
            },
        },
    }


def _build() -> list[dict]:
    entities = [
        {"id": "lower", "kind": "storey", "name": "Lower level", "elevation": 1200, "height": 3000},
        {"id": "upper", "kind": "storey", "name": "Upper level", "elevation": 4200, "height": 3000},
        {
            "id": "roof",
            "kind": "roof",
            "name": "Gable roof",
            "storey": "upper",
            "polygon": [[0, 0], [8000, 0], [8000, 6000], [0, 6000]],
            "base_height": 3000,
            "thickness": 200,
            "form": "gable",
            "pitch_deg": 30,
        },
        {
            "id": "stair",
            "kind": "stair",
            "name": "Straight stair",
            "storey": "lower",
            "top_storey": "upper",
            "start": [500, 500],
            "direction_deg": 0,
            "width": 1000,
            "riser_count": 16,
            "going": 260,
            "waist_thickness": 150,
            "landing_depth": 1000,
        },
    ]
    return [
        {
            "op": "project",
            "changes": {
                "facts": {
                    "drawing": {
                        "sections": [
                            {
                                "id": "STAIR",
                                "axis": "y",
                                "coordinate_mm": 1000,
                                "direction": "positive",
                            },
                            {
                                "id": "ROOF",
                                "axis": "x",
                                "coordinate_mm": 4000,
                                "direction": "positive",
                            },
                        ]
                    },
                    "specifications": {
                        "scope": (
                            "Isolated parametric roof/stair geometry study; "
                            "no building, structural, drainage or code approval."
                        )
                    },
                }
            },
        },
        _roof_type(30),
        _stair_type(16),
        *[{"op": "create", "entity": e} for e in entities],
        {"op": "bim_assign", "id": "roof", "type_id": "roof_type"},
        {"op": "bim_assign", "id": "stair", "type_id": "stair_type"},
    ]


def guide(topic: str | None = None) -> dict[str, Any]:
    common = {
        "lane": "architecture",
        "offline": True,
        "units": {"length": "mm", "angle": "deg"},
        "integration": (
            "TEE-authored CADAgent workflow; execute calls through tee_call. No model training "
            "or standalone agent execution is implied."
        ),
    }
    if topic is None:
        return {
            **common,
            "topics": dict(TOPICS),
            "next": _call("ak_guide", topic="cadagent_roof_stair.build"),
        }
    if not isinstance(topic, str) or topic not in TOPICS:
        raise TeeError(
            "guide_topic",
            "Unknown architectural CADAgent lesson.",
            fix="Call ak_guide without topic for the index.",
        )
    if topic == "cadagent_thermal.inspect":
        calls = [
            _call("ak_query", model_id="$model_id", detail="thermal", collection=c, limit=5)
            for c in ("assemblies", "surfaces", "zones", "spaces")
        ]
        acceptance = {
            "inputs": (
                "Read each source and missing field. Use explicit SI resistance/conductivity "
                "or a whole-product U-value. An insulation R-value alone is not a wall rating."
            ),
            "geometry": (
                "Wall area excludes apertures; window U applies to the full product. "
                "Roof area includes the authored eaves; no thermal boundary is inferred."
            ),
            "interpretation": (
                "Positive flow is outward; negative is heat gain. Zone values are selected "
                "surface subtotals. Exterior spaces cannot join conditioned thermal zones. "
                "No whole-building load, annual energy, HVAC sizing or code approval."
            ),
            "paging": "Use page.next_offset to inspect every requested row.",
            "gui": "ak_open edits the same explicit thermal facts and preserves revision checks.",
        }
    elif topic == "cadagent_services.build":
        from .service_lessons import build_operations

        calls = [
            _call("ak_create", name="CADAgent connected services study", preset="empty"),
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=build_operations(),
            ),
        ]
        acceptance = {
            "gap_mm": 25,
            "connection_status": "not_connected",
            "scope": "Isolated synthetic study, never an inferred Okongo service design.",
            "next": "cadagent_services.inspect",
        }
    elif topic == "cadagent_services.inspect":
        calls = [
            _call("ak_query", model_id="$model_id", detail="distribution", collection=c, limit=5)
            for c in ("connections", "ports", "systems")
        ]
        acceptance = {
            "checks": (
                "Read every connection check. A declared link is not measured connectivity; "
                "bad links remain editable but refuse IFC export."
            ),
            "axes": "Mating face normals oppose; IFC SOURCE/SINK flow axes align.",
            "coverage": (
                "Read connected_components, unconnected_ports and ends_without_ports. "
                "An accepted pair is not a complete or engineered network."
            ),
            "next": "cadagent_services.repair",
        }
    elif topic == "cadagent_services.repair":
        calls = [
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=[
                    {"op": "update", "id": "b", "changes": {"origin": [10600, 20800, 100]}}
                ],
            ),
            _call(
                "ak_query", model_id="$model_id", detail="distribution", collection="connections"
            ),
            _call("ak_export", model_id="$model_id", expected_revision="$revision", format="ifc"),
        ]
        acceptance = {
            "prerequisite": "The isolated cadagent_services.build study at its current revision.",
            "gap_mm": 0,
            "connection_status": "geometrically_connected",
            "ifc": (
                "Reopen IFC: two ducts, one system, four fixed nested ports and one connection. "
                "The mating ports are at world [10600,20800,1300] mm."
            ),
            "remaining": (
                "Two outer ends remain unconnected. Fittings, seals, supports, pressure/flow "
                "sizing and local compliance are unverified. Use ak_open for the shared editor."
            ),
        }
    elif topic == "cadagent_circulation.build":
        calls = [
            _call("ak_create", name="CADAgent exterior circulation study", preset="empty"),
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=[
                    {
                        "op": "create",
                        "entity": {
                            "id": "ground",
                            "kind": "storey",
                            "name": "Ground",
                            "elevation": 0,
                            "height": 3000,
                        },
                    },
                    {
                        "op": "create",
                        "entity": {
                            "id": "outside",
                            "kind": "space",
                            "name": "Exterior circulation",
                            "storey": "ground",
                            "environment": "exterior",
                            "conditioned": False,
                            "polygon": [[0, 0], [4000, 0], [4000, 3000], [0, 3000]],
                            "height": 3000,
                        },
                    },
                    {
                        "op": "create",
                        "entity": {
                            "id": "column",
                            "kind": "member",
                            "name": "Profile column",
                            "storey": "ground",
                            "origin": [1800, 1300, 0],
                            "profile": [[0, 0], [400, 0], [400, 400], [0, 400]],
                            "axis": [0, 0, 1],
                            "x_direction": [1, 0, 0],
                            "length": 3000,
                            "role": "column",
                        },
                    },
                    {
                        "op": "project",
                        "changes": {
                            "facts": {
                                "drawing": {"working_dimensions": True},
                                "performance": {
                                    "clearance_width_mm": 900,
                                    "clearance_height_mm": 2000,
                                    "basis": "explicit geometric study; not legal requirement",
                                    "routes": [
                                        {
                                            "id": "cross",
                                            "space_id": "outside",
                                            "start_mm": [800, 1500],
                                            "end_mm": [3200, 1500],
                                        }
                                    ],
                                },
                            }
                        },
                    },
                ],
            ),
        ]
        acceptance = {
            "geometry": "One exterior space and one column; path must avoid the real solid.",
            "approval": (
                "Targets are a design scenario, never a jurisdiction rule or structural approval."
            ),
        }
    elif topic == "cadagent_circulation.inspect":
        calls = [
            _call(
                "ak_query", model_id="$model_id", detail="performance", collection="routes", limit=5
            ),
            _call(
                "ak_query",
                model_id="$model_id",
                detail="bim",
                collection="information_gaps",
                limit=5,
            ),
            _call(
                "ak_query", model_id="$model_id", detail="schedules", collection="members", limit=5
            ),
        ]
        acceptance = {
            "route": (
                "Remeasure the complete path, not sampled grid points. Missing "
                "objects and operating envelopes remain outside coverage."
            ),
            "gui": (
                "The same document is editable through ak_open. Usable space / "
                "routes overlays the current page on the plan."
            ),
            "learning": (
                "Normal TEE tool outcomes enter the existing learning observer; no "
                "separate training daemon or granted approval is implied."
            ),
        }
    elif topic == "cadagent_roof_stair.build":
        calls = [
            _call("ak_create", name="CADAgent roof and stair study", preset="empty"),
            _call(
                "ak_edit", model_id="$model_id", expected_revision="$revision", operations=_build()
            ),
        ]
        acceptance = {
            "stair_rise_mm": 3000,
            "riser_height_mm": 187.5,
            "riser_count": 16,
            "flight_run_mm": 4160,
            "roof_plan_area_m2": 48,
            "roof_pitch_deg": 30,
        }
    elif topic == "cadagent_roof_stair.revise":
        calls = [
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=[
                    {"op": "update", "id": "upper", "changes": {"elevation": 4800}},
                    _roof_type(45),
                    _stair_type(20),
                ],
            )
        ]
        acceptance = {
            "stair_rise_mm": 3600,
            "riser_height_mm": 180,
            "riser_count": 20,
            "flight_run_mm": 5200,
            "roof_plan_area_m2": 48,
            "roof_pitch_deg": 45,
            "roof_eave_underside_world_mm": 7800,
        }
    elif topic == "cadagent_roof_stair.inspect":
        calls = [
            _call("ak_query", model_id="$model_id", detail="schedules", collection=c, limit=5)
            for c in ("roofs", "stairs")
        ]
        calls += [
            _call("ak_query", model_id="$model_id", detail="quality", collection="issues", limit=5),
            _call("ak_export", model_id="$model_id", expected_revision="$revision", format="all"),
        ]
        acceptance = {
            "ifc": (
                "Require IFC4 schema and measured geometry pass; compare volume/bounds to "
                "schedules and GLB, not merely declared dimensions."
            ),
            "stair": (
                "IfcStair aggregates IfcStairFlight and optional IfcSlab LANDING; verify "
                "riser/tread counts and both level references."
            ),
            "drawings": (
                "Inspect both floor plans and sections; stair top tread must meet destination "
                "level; roof ridge/eaves must match geometry."
            ),
            "issues": "stair_design_unverified and roof_details_unverified remain visible.",
        }
    elif topic == "cadagent_stair_clearance.block":
        calls = [
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=[
                    {
                        "op": "create",
                        "entity": {
                            "id": "upper_floor",
                            "kind": "slab",
                            "name": "Upper floor",
                            "storey": "upper",
                            "polygon": [[0, 0], [8000, 0], [8000, 6000], [0, 6000]],
                            "thickness": 200,
                        },
                    },
                    {"op": "update", "id": "stair", "changes": {"headroom_target_mm": 2100}},
                ],
            )
        ]
        acceptance = {
            "prerequisite": "Use cadagent_roof_stair.build in a fresh study, before revise.",
            "headroom_mm": 0,
            "status": "below_target",
            "issue": "stair_solid_intersection",
            "target_basis": "2100 mm is the study design target, not a jurisdictional rule.",
        }
    elif topic == "cadagent_stair_clearance.open":
        calls = [
            _call(
                "ak_edit",
                model_id="$model_id",
                expected_revision="$revision",
                operations=[
                    {
                        "op": "create",
                        "entity": {
                            "id": "stair_void",
                            "kind": "slab_opening",
                            "name": "Stair floor opening",
                            "slab": "upper_floor",
                            "polygon": [[1200, 450], [5660, 450], [5660, 1550], [1200, 1550]],
                        },
                    },
                ],
            )
        ]
        acceptance = {
            "prerequisite": "Run cadagent_stair_clearance.block on the initial 16-riser study.",
            "minimum_headroom_mm": 2107.6923076923076,
            "status": "meets_target_in_scope",
            "opening_area_m2": 4.906,
            "slab_net_volume_m3": 8.6188,
            "scope": "Authored slabs/roofs only; no railing, bearing or code approval.",
        }
    elif topic == "cadagent_stair_clearance.inspect":
        calls = [
            _call("ak_query", model_id="$model_id", detail="schedules", collection=c, limit=5)
            for c in ("stairs", "slabs", "slab_openings")
        ]
        calls += [
            _call("ak_query", model_id="$model_id", detail="quality", collection="issues", limit=5),
            _call("ak_export", model_id="$model_id", expected_revision="$revision", format="all"),
        ]
        acceptance = {
            "geometry": (
                "Compare reopened IFC/GLB net slab volume to schedules, and inspect "
                "opening edges in plan/section."
            ),
            "ifc": (
                "IfcOpeningElement must void the slab with IfcRelVoidsElement; retain "
                "host/opening GUIDs across edits."
            ),
            "headroom": (
                "Read the limiting obstacle and full-width analytic witness; an unset "
                "target or absent overhead is not a compliance pass."
            ),
        }
    elif topic == "cadagent_bim.build":
        calls = [_call("ak_create", name="CADAgent compact dwelling", preset="compact-dwelling")]
        acceptance = {
            "scope": (
                "Typed compact dwelling with authored kitchen construction; separate fixture "
                "from the roof/stair study."
            )
        }
    else:
        calls = [
            _call("ak_query", model_id="$model_id", detail="bim", collection="types", limit=5),
            _call(
                "ak_query", model_id="$model_id", detail="schedules", collection="openings", limit=5
            ),
            _call(
                "ak_query", model_id="$model_id", detail="schedules", collection="cabinets", limit=5
            ),
            _call("ak_query", model_id="$model_id", detail="quality", collection="issues", limit=5),
        ]
        acceptance = {
            "opening": (
                "Compare sill/head relative to storey and world Z with actual views and IFC; "
                "low glazing can be intentional."
            ),
            "cabinet": (
                "Use returned cabinet id with ak_query detail=cabinet for panels, machining "
                "provenance, costs and stock nesting. Missing prices, hardware and commissioned"
                " posts remain unknown."
            ),
            "paging": "Follow page.next_offset until every requested row has been inspected.",
        }
    return deepcopy(
        {
            **common,
            "topic": topic,
            "calls": calls,
            "acceptance": acceptance,
            "bindings": (
                "Execute in order. Replace $model_id and $revision with actual latest values "
                "from ak_create/ak_query/ak_edit for the chosen model. Never guess IDs or "
                "revisions. A rejected edit requires rereading state."
            ),
            "jobs": (
                "ak_export returns a job: poll tee_job with job_id set to its returned job "
                "value; inspect completed.result and output files. Queued or done alone is not "
                "acceptance."
            ),
            "undo": _call("ak_undo", model_id="$model_id", expected_revision="$revision"),
            "limits": (
                "Development authoring studies. Complete roof/stair systems, engineered "
                "connections, global code coverage and commissioned CNC remain unverified. Do "
                "not alter an existing DCC scene to run these lessons."
            ),
        }
    )
