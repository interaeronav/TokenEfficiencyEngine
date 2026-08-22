"""TEE Design virtual tools (gd_*)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.design import checks, tables
from tee.design.spec import SpecStore, render_beat_chart, render_one_pager, validate
from tee.kernel.registry import VirtualTool


def register_design_tools(app, project_root: Path | str) -> SpecStore:
    store = SpecStore(project_root)
    reg = app.registry

    def _spec_from(args: dict[str, Any]) -> dict[str, Any]:
        if args.get("spec"):
            return args["spec"]
        return store.load(str(args.get("name", "")))

    def gd_validate(args):
        return validate(args["spec"])

    def gd_store(args):
        return store.save(args["spec"])

    def gd_load(args):
        return store.load(str(args["name"]))

    def gd_render(args):
        spec = _spec_from(args)
        view = str(args.get("view", "one_pager"))
        if view == "beat_chart":
            return {"view": view, "markdown": render_beat_chart(spec)}
        return {"view": "one_pager", "markdown": render_one_pager(spec)}

    def gd_check(args):
        return checks.run_battery(_spec_from(args), days=int(args.get("days", 90)))

    def gd_economy_sim(args):
        return checks.economy_sim(_spec_from(args), days=int(args.get("days", 90)))

    def gd_ethics(args):
        return checks.ethics_check(_spec_from(args))

    def gd_scope(args):
        return checks.scope_estimate(
            _spec_from(args),
            team_size=args.get("team_size"),
            weeks=args.get("weeks"),
        )

    def gd_benchmark(args):
        return tables.benchmark(
            str(args["metric"]),
            platform=str(args.get("platform", "mobile")),
            genre=args.get("genre"),
        )

    def gd_genre(args):
        if args.get("genre"):
            return tables.genre_conventions(str(args["genre"]))
        return {"opportunity_map": tables.opportunity_map()}

    def gd_selfplay(args):
        spec = _spec_from(args)
        if args.get("transcript") is not None:
            return checks.selfplay_score(spec, args["transcript"])
        return checks.selfplay_prepare(spec, turns=int(args.get("turns", 8)))

    spec_arg = {"spec": {"type": "object"}, "name": {"type": "string"}}
    tools = [
        VirtualTool(
            "gd_validate",
            "Structurally validate a tee-design/1 spec; errors name the "
            "exact fix. Quality problems are gd_check's job.",
            {"type": "object", "properties": {"spec": {"type": "object"}},
             "required": ["spec"]},
            gd_validate,
            tags=["design", "spec", "validate"],
        ),
        VirtualTool(
            "gd_store",
            "Validate and store a design spec (content-addressed revisions; "
            "a design change is a diff, not a new document).",
            {"type": "object", "properties": {"spec": {"type": "object"}},
             "required": ["spec"]},
            gd_store,
            tags=["design", "spec", "store", "save"],
        ),
        VirtualTool(
            "gd_load",
            "Load a stored design spec by name.",
            {"type": "object", "properties": {"name": {"type": "string"}},
             "required": ["name"]},
            gd_load,
            tags=["design", "spec", "load"],
        ),
        VirtualTool(
            "gd_render",
            "Render prose FROM the spec (never the reverse): view='one_pager' "
            "(Librande) or 'beat_chart' (Cerny macro).",
            {"type": "object", "properties": {**spec_arg, "view": {"type": "string"}}},
            gd_render,
            tags=["design", "render", "gdd", "one-pager"],
        ),
        VirtualTool(
            "gd_check",
            "The full verification battery, cost-ordered in ONE call: design "
            "lint, scope estimate, economy simulation per persona, "
            "progression validation, ethics/dark-pattern check (code rows "
            "hard-fail). Returns every finding with its one-line fix.",
            {"type": "object", "properties": {**spec_arg, "days": {"type": "integer"}}},
            gd_check,
            tags=["design", "check", "verify", "battery", "lint"],
        ),
        VirtualTool(
            "gd_economy_sim",
            "Discrete-time faucet/sink/converter simulation per player "
            "persona; flags inflation and archetype-band violations.",
            {"type": "object", "properties": {**spec_arg, "days": {"type": "integer"}}},
            gd_economy_sim,
            tags=["design", "economy", "simulation", "balance"],
        ),
        VirtualTool(
            "gd_ethics",
            "Dark-pattern rulebook check: code-severity rows (live "
            "enforcement: FTC, EU CPC, Belgium, Brazil, Australia) are hard "
            "failures the model cannot relax.",
            {"type": "object", "properties": spec_arg},
            gd_ethics,
            tags=["design", "ethics", "dark-pattern", "monetization", "compliance"],
        ),
        VirtualTool(
            "gd_scope",
            "Content-list scope estimate in person-day bands; flags "
            "scope/capacity mismatches given team_size and weeks.",
            {"type": "object", "properties": {**spec_arg,
             "team_size": {"type": "integer"}, "weeks": {"type": "integer"}}},
            gd_scope,
            tags=["design", "scope", "estimate", "content"],
        ),
        VirtualTool(
            "gd_benchmark",
            "Percentile benchmarks with source+year, never folk targets: "
            "metric in (d1, d7, d30, session, funnel, ftue, liveops), "
            "platform mobile|pc, optional genre.",
            {"type": "object", "properties": {
                "metric": {"type": "string"},
                "platform": {"type": "string"},
                "genre": {"type": "string"},
            }, "required": ["metric"]},
            gd_benchmark,
            tags=["design", "benchmark", "retention", "kpi"],
        ),
        VirtualTool(
            "gd_genre",
            "Genre convention template (session shape, price band, hit rate, "
            "evidence) or, with no genre, the evidence-backed opportunity map.",
            {"type": "object", "properties": {"genre": {"type": "string"}}},
            gd_genre,
            tags=["design", "genre", "market", "conventions", "opportunity"],
        ),
        VirtualTool(
            "gd_selfplay",
            "Bounded self-play: without transcript, returns the play "
            "instructions derived from the spec (the host model plays); with "
            "transcript, scores it deterministically (decision loop present?).",
            {"type": "object", "properties": {**spec_arg,
             "turns": {"type": "integer"}, "transcript": {"type": "array"}}},
            gd_selfplay,
            tags=["design", "selfplay", "playtest", "verify"],
        ),
    ]
    for tool in tools:
        reg.register(tool)
    return store
