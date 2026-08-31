"""A45 P2 — the fleet's virtual tools.

Registered like every other long-tail capability: discovered through
`tee_search_tools`, invoked through `tee_call`. Zero always-loaded cost,
and nothing here imports a solver at registration time - the modules are
pulled in on first call, so an absent extra costs nothing but a clear
refusal.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.registry import VirtualTool

_SPEC_SCHEMA = {
    "type": "object",
    "properties": {
        "sense": {"type": "string"},
        "objective": {"type": "object"},
        "variables": {"type": "object"},
        "constraints": {"type": "array"},
        "backend": {"type": "string"},
        "time_limit": {"type": "number"},
        "show": {"type": "integer"},
    },
    "required": ["variables"],
}

_EXAMPLE = {
    "sense": "max",
    "objective": {"x": 3, "y": 4},
    "variables": {"x": {"lb": 0, "ub": 10}, "y": {"lb": 0, "ub": 10}},
    "constraints": [{"name": "cap", "lhs": {"x": 1, "y": 2}, "op": "<=", "rhs": 14}],
    "backend": "highs",
}


def register_fleet_tools(app) -> None:
    def solve_program(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import solve

        return solve.solve(dict(args or {}))

    def solve_cpsat(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import solve

        return solve.cpsat(dict(args or {}))

    def solve_detail(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import solve

        a = dict(args or {})
        return solve.detail(
            str(a.get("solution_id", "")),
            offset=int(a.get("offset") or 0),
            limit=int(a.get("limit") or 50),
            log=bool(a.get("log")),
        )

    def solve_backends(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import solve

        return solve.backends()

    def quant_optimize(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import quant

        return quant.optimize(dict(args or {}))

    def quant_detail(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import quant

        a = dict(args or {})
        return quant.detail(
            str(a.get("weights_id", "")),
            offset=int(a.get("offset") or 0),
            limit=int(a.get("limit") or 100),
        )

    def quant_backends(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import quant

        return quant.backends()

    def _med_cfg(args: dict[str, Any]) -> dict[str, Any]:
        """Merge [med] from the project config under the call's own args."""
        base = dict(getattr(app.config, "med", {}) or {})
        base.update(dict(args or {}))
        return base

    def med_archive(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.system(_med_cfg(args))

    def med_find_studies(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.find_studies(_med_cfg(args))

    def med_study_tree(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.study_tree(_med_cfg(args))

    def med_instance_tags(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.instance_tags(_med_cfg(args))

    def med_volume_stats(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.volume_stats(dict(args or {}))

    def med_backends(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import med

        return med.backends(_med_cfg(args))

    def cad_scad_build(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import cad

        return cad.scad_build(dict(args or {}))

    def cad_measure(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import cad

        return cad.measure(dict(args or {}))

    def cad_probe(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import cad

        return cad.probe()

    def trade_backtest(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import trade

        return trade.backtest(dict(args or {}))

    def trade_detail(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import trade

        a = dict(args or {})
        return trade.detail(str(a.get("run_id", "")), points=int(a.get("points") or 40))

    def trade_probe(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import trade

        return trade.probe()

    def _bi_cfg(args: dict[str, Any]) -> dict[str, Any]:
        base = dict(getattr(app.config, "bi", {}) or {})
        base.update(dict(args or {}))
        return base

    def bi_catalogue(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import bi

        return bi.catalogue(_bi_cfg(args))

    def bi_query(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import bi

        return bi.query(_bi_cfg(args))

    def bi_detail(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import bi

        a = dict(args or {})
        return bi.detail(
            str(a.get("result_id", "")),
            offset=int(a.get("offset") or 0),
            limit=int(a.get("limit") or 100),
        )

    def bi_probe(args: dict[str, Any]) -> dict[str, Any]:
        from tee.fleet import bi

        return bi.probe(_bi_cfg(args))

    for tool in [
        VirtualTool(
            "solve_program",
            "Solve a linear or mixed-integer program (LP / MILP) on HiGHS, "
            "SCIP or COIN-OR Cbc. Variable types decide LP vs MIP: "
            "cont|int|bin. Answers COMPACTLY - status, objective, binding "
            "constraints and the largest non-zero variables with a "
            "solution_id; the full vector is a solve_detail call, never the "
            "default. Optimisation, scheduling, blending, assignment, "
            "knapsack, resource allocation.",
            _SPEC_SCHEMA,
            solve_program,
            tags=[
                "solve",
                "solver",
                "optimize",
                "optimisation",
                "linear",
                "programming",
                "lp",
                "mip",
                "milp",
                "integer",
                "highs",
                "scip",
                "cbc",
                "constraint",
                "schedule",
                "allocation",
                "knapsack",
                "assignment",
                "blending",
                "minimise",
                "maximise",
            ],
            examples=[_EXAMPLE],
        ),
        VirtualTool(
            "solve_cpsat",
            "Solve an integer CONSTRAINT PROGRAM with Google OR-Tools "
            "CP-SAT - a different paradigm from LP: combinatorial "
            "feasibility and scheduling rather than a continuous "
            "relaxation. Same compact answer contract as solve_program.",
            _SPEC_SCHEMA,
            solve_cpsat,
            tags=[
                "cpsat",
                "cp-sat",
                "ortools",
                "constraint",
                "programming",
                "combinatorial",
                "feasibility",
                "scheduling",
                "rostering",
                "sat",
                "integer",
                "google",
            ],
            examples=[
                {
                    "sense": "max",
                    "objective": {"a": 5, "b": 3, "c": 4},
                    "variables": {
                        "a": {"lb": 0, "ub": 1},
                        "b": {"lb": 0, "ub": 1},
                        "c": {"lb": 0, "ub": 1},
                    },
                    "constraints": [
                        {"name": "weight", "lhs": {"a": 3, "b": 2, "c": 2}, "op": "<=", "rhs": 4}
                    ],
                }
            ],
        ),
        VirtualTool(
            "solve_detail",
            "Page the FULL solution vector of an earlier solve by "
            "solution_id, or fetch that engine's own log with log=true. The "
            "opt-in half of the compact-answer contract.",
            {
                "type": "object",
                "properties": {
                    "solution_id": {"type": "string"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "log": {"type": "boolean"},
                },
                "required": ["solution_id"],
            },
            solve_detail,
            tags=["solve", "detail", "solution", "vector", "page", "log", "solver"],
            examples=[{"solution_id": "sol_1", "limit": 50}],
        ),
        VirtualTool(
            "solve_backends",
            "Which solver engines are installed here (HiGHS, SCIP, Cbc, "
            "CP-SAT), their versions, and the install line when none are.",
            {"type": "object", "properties": {}},
            solve_backends,
            tags=["solve", "backends", "solver", "installed", "probe", "versions"],
        ),
        VirtualTool(
            "quant_optimize",
            "Portfolio optimisation over price or return series: max_sharpe, "
            "min_volatility, hierarchical risk parity (PyPortfolioOpt) or "
            "mean-risk (skfolio). Returns the holdings that matter plus "
            "return / volatility / Sharpe computed on ONE basis for every "
            "method so they are comparable - the libraries' own numbers are "
            "not. Arithmetic, explicitly not investment advice.",
            {
                "type": "object",
                "properties": {
                    "prices": {"type": "object"},
                    "returns": {"type": "object"},
                    "method": {"type": "string"},
                    "risk_free_rate": {"type": "number"},
                    "periods_per_year": {"type": "number"},
                    "min_weight": {"type": "number"},
                    "max_weight": {"type": "number"},
                    "risk_measure": {"type": "string"},
                    "show": {"type": "integer"},
                },
            },
            quant_optimize,
            tags=[
                "portfolio",
                "quant",
                "optimize",
                "weights",
                "allocation",
                "sharpe",
                "volatility",
                "risk",
                "efficient",
                "frontier",
                "markowitz",
                "hrp",
                "skfolio",
                "pyportfolioopt",
                "rebalance",
            ],
            examples=[
                {"returns": {"AAA": [0.01, -0.002], "BBB": [0.003, 0.004]}, "method": "max_sharpe"}
            ],
        ),
        VirtualTool(
            "quant_detail",
            "Page the FULL weight vector of an earlier quant_optimize by "
            "weights_id - the opt-in half of the compact answer.",
            {
                "type": "object",
                "properties": {
                    "weights_id": {"type": "string"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "required": ["weights_id"],
            },
            quant_detail,
            tags=["portfolio", "quant", "detail", "weights", "page"],
        ),
        VirtualTool(
            "quant_backends",
            "Which portfolio engines are installed (PyPortfolioOpt, "
            "skfolio), the methods available, and the install line.",
            {"type": "object", "properties": {}},
            quant_backends,
            tags=["portfolio", "quant", "backends", "installed", "probe"],
        ),
        VirtualTool(
            "med_archive",
            "Is a DICOM archive (Orthanc) reachable, and what does it hold: "
            "version, loaded plugins, and counts of patients / studies / "
            "series / instances. Orthanc is a server YOU run; TEE only "
            "speaks HTTP to it and never bundles or links it.",
            {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
            },
            med_archive,
            tags=["dicom", "medical", "orthanc", "pacs", "archive", "imaging", "radiology"],
        ),
        VirtualTool(
            "med_find_studies",
            "Search a DICOM archive for studies. Compact rows - date, "
            "description, modality, series count - with full Orthanc IDs "
            "you can pass on. PATIENT IDENTIFIERS ARE WITHHELD unless you "
            "pass phi=true.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "object"},
                    "limit": {"type": "integer"},
                    "phi": {"type": "boolean"},
                    "url": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
            },
            med_find_studies,
            tags=["dicom", "study", "search", "find", "orthanc", "medical", "modality", "pacs"],
            examples=[{"query": {"ModalitiesInStudy": "CT"}, "limit": 10}],
        ),
        VirtualTool(
            "med_study_tree",
            "One study's series: modality, description, body part and "
            "instance counts, with IDs. Never instance-level, never pixels.",
            {
                "type": "object",
                "properties": {
                    "study_id": {"type": "string"},
                    "phi": {"type": "boolean"},
                    "url": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["study_id"],
            },
            med_study_tree,
            tags=["dicom", "study", "series", "tree", "orthanc", "medical"],
        ),
        VirtualTool(
            "med_instance_tags",
            "The DICOM header of one instance. Pixel data is never "
            "returned; pass `tags` to select specific ones, phi=true to "
            "include identifiers.",
            {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string"},
                    "tags": {"type": "array"},
                    "phi": {"type": "boolean"},
                    "url": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
                "required": ["instance_id"],
            },
            med_instance_tags,
            tags=["dicom", "tags", "header", "metadata", "instance", "orthanc"],
        ),
        VirtualTool(
            "med_volume_stats",
            "Scalar statistics of a LOCAL image volume via MONAI - shape, "
            "intensity range, mean, spacing, non-zero fraction. Never the "
            "voxel array. Reads DICOM, NIfTI, PNG and more.",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            med_volume_stats,
            tags=["monai", "volume", "nifti", "dicom", "statistics", "imaging", "medical", "voxel"],
        ),
        VirtualTool(
            "med_backends",
            "Which imaging libraries are installed and whether a DICOM "
            "archive is reachable, with the exact fix for each.",
            {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "username": {"type": "string"},
                    "password": {"type": "string"},
                },
            },
            med_backends,
            tags=["medical", "imaging", "backends", "probe", "installed", "orthanc", "monai"],
        ),
        VirtualTool(
            "cad_scad_build",
            "Build a solid from OpenSCAD source and export it (STL, 3MF, "
            "SVG, DXF, OFF, AMF, CSG). Parameters go through OpenSCAD's "
            "customizer JSON and are type-checked; the -D flag is NOT "
            "exposed because it prepends arbitrary statements rather than "
            "setting a value. Answers with facets, size and the output "
            "path - never geometry.",
            {
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "path": {"type": "string"},
                    "params": {"type": "object"},
                    "format": {"type": "string"},
                    "out": {"type": "string"},
                },
            },
            cad_scad_build,
            tags=[
                "cad",
                "openscad",
                "scad",
                "solid",
                "model",
                "export",
                "stl",
                "3mf",
                "dxf",
                "svg",
                "parametric",
                "mesh",
                "3d",
                "print",
            ],
            examples=[
                {
                    "source": "difference(){cube([20,10,5],center=true);"
                    "cylinder(h=20,r=hole_r,center=true,$fn=64);}",
                    "params": {"hole_r": 4},
                    "format": "binstl",
                }
            ],
        ),
        VirtualTool(
            "cad_measure",
            "Scalar geometry of an existing model: volume, surface area, "
            "bounding box and validity. STEP via CadQuery; binary STL "
            "measured directly (signed-tetrahedron volume, exact for a "
            "closed mesh) with no dependency at all.",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            cad_measure,
            tags=["cad", "measure", "volume", "area", "bbox", "stl", "step", "geometry", "solid"],
        ),
        VirtualTool(
            "cad_probe",
            "Is OpenSCAD on PATH and is CadQuery installed - with versions, "
            "supported export formats and the exact install line for each.",
            {"type": "object", "properties": {}},
            cad_probe,
            tags=["cad", "probe", "openscad", "cadquery", "installed", "backends"],
        ),
        VirtualTool(
            "trade_backtest",
            "Backtest a DECLARATIVE rule (sma_cross, threshold, buy_hold) "
            "over a price series: total return, CAGR, max drawdown, Sharpe, "
            "trade count, win rate, exposure, and buy-and-hold for "
            "comparison. Signals act on the bar AFTER they form, so there "
            "is no look-ahead. RESEARCH ONLY - TEE places no orders and "
            "reads no broker account.",
            {
                "type": "object",
                "properties": {
                    "prices": {"type": "array"},
                    "rule": {"type": "object"},
                    "fee_bps": {"type": "number"},
                    "periods_per_year": {"type": "number"},
                    "risk_free_rate": {"type": "number"},
                },
                "required": ["prices"],
            },
            trade_backtest,
            tags=[
                "backtest",
                "trading",
                "strategy",
                "signal",
                "sma",
                "crossover",
                "momentum",
                "drawdown",
                "sharpe",
                "equity",
                "returns",
                "quant",
            ],
            examples=[
                {"prices": [100, 101, 99], "rule": {"kind": "sma_cross", "fast": 10, "slow": 40}}
            ],
        ),
        VirtualTool(
            "trade_detail",
            "The equity curve of an earlier backtest, RESAMPLED to a "
            "readable number of points rather than paged - the shape is the "
            "answer, not the rows.",
            {
                "type": "object",
                "properties": {
                    "run_id": {"type": "string"},
                    "points": {"type": "integer"},
                },
                "required": ["run_id"],
            },
            trade_detail,
            tags=["backtest", "equity", "curve", "detail", "trading"],
        ),
        VirtualTool(
            "trade_probe",
            "What trading research is available here, which engines run in "
            "their own interpreter and why, and - explicitly - what TEE "
            "never builds: order placement, fund movement, live strategy "
            "control, or reading a live broker account.",
            {"type": "object", "properties": {}},
            trade_probe,
            tags=[
                "trading",
                "probe",
                "backends",
                "jesse",
                "nautilus",
                "hummingbot",
                "openalgo",
                "safety",
            ],
        ),
        VirtualTool(
            "bi_catalogue",
            "What a Cube semantic layer can answer: cube names with their "
            "measures and dimensions. Names only - ask bi_query for numbers.",
            {
                "type": "object",
                "properties": {"url": {"type": "string"}, "token": {"type": "string"}},
            },
            bi_catalogue,
            tags=[
                "bi",
                "cube",
                "semantic",
                "catalogue",
                "measures",
                "dimensions",
                "analytics",
                "warehouse",
            ],
        ),
        VirtualTool(
            "bi_query",
            "Run a Cube query and get a COMPACT table: a cols header plus "
            "arrays-of-arrays, numbers coerced and rounded, with the row "
            "count and a result_id. Cube's own response is ~92% annotation; "
            "this returns the answer.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "object"},
                    "rows": {"type": "integer"},
                    "url": {"type": "string"},
                    "token": {"type": "string"},
                },
                "required": ["query"],
            },
            bi_query,
            tags=[
                "bi",
                "cube",
                "query",
                "analytics",
                "aggregate",
                "measure",
                "dimension",
                "sql",
                "warehouse",
                "report",
            ],
            examples=[{"query": {"measures": ["orders.count"], "dimensions": ["orders.status"]}}],
        ),
        VirtualTool(
            "bi_detail",
            "Page the full row set of an earlier bi_query by result_id. "
            "Prefer aggregating in the query itself - a paged dump is worse "
            "than the aggregate you actually wanted.",
            {
                "type": "object",
                "properties": {
                    "result_id": {"type": "string"},
                    "offset": {"type": "integer"},
                    "limit": {"type": "integer"},
                },
                "required": ["result_id"],
            },
            bi_detail,
            tags=["bi", "cube", "detail", "rows", "page"],
        ),
        VirtualTool(
            "bi_probe",
            "Is a Cube semantic layer reachable, and what does it expose - "
            "with the exact docker line when it is not.",
            {
                "type": "object",
                "properties": {"url": {"type": "string"}, "token": {"type": "string"}},
            },
            bi_probe,
            tags=["bi", "cube", "probe", "reachable", "installed"],
        ),
    ]:
        app.registry.register(tool)
