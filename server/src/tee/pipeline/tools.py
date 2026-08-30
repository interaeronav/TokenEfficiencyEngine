"""Pipeline virtual tools (A43 P0): `pipeline_list` only, deliberately.

P0 ships the schema, the validator and the hostile fixtures with NO
runner in existence - the acceptance is that the declaration surface is
provably safe before anything can execute.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel import trustctx
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.pipeline import runner, schema


def register_pipeline_tools(app, project_root: Path | str) -> None:
    root = Path(project_root)

    def pipeline_list(args: dict[str, Any]) -> dict[str, Any]:
        pipeline = schema.load(root)
        payload: dict[str, Any] = {
            "file": str(pipeline.path),
            "steps": [step.summary() for step in pipeline.steps.values()],
            "approved": pipeline.approved,
        }
        if not pipeline.approved:
            # Trust on first use: a declaration TEE has not been shown is
            # attacker-authored by default (a cloned repo ships one too).
            payload["blocked"] = pipeline.change
            payload["to_approve"] = (
                f"Read {pipeline.path}, then write its digest {pipeline.digest} "
                f"to {schema.pin_path(root)} - TEE never approves its own inputs."
            )
        return payload

    app.registry.register(
        VirtualTool(
            "pipeline_list",
            "The build/query steps this project declares in .tee/pipeline.toml: "
            "names, kinds (produce|query), argv and params. Says whether the "
            "declaration is approved for this machine, and how to approve it.",
            {"type": "object", "properties": {}},
            pipeline_list,
            tags=["pipeline", "steps", "build", "query", "declared", "project"],
        )
    )


def register_adhoc_tools(app, project_root: Path | str) -> None:
    """The ad-hoc door (A43 P0b) and the adopt flow.

    Declared steps are the norm and the ONLY thing anything automatic may
    run. This door exists because discovery is real - the owner does not
    know the step until he has run the command once - but it opens for a
    LIVE HUMAN TURN only, and only when the project has opted in.
    Untrusted content can never cause execution; that invariant does not
    bend, so the caller class is checked here as well as in the kernel.
    """
    root = Path(project_root)

    def _guard_live_turn(what: str) -> None:
        caller = trustctx.caller()
        if caller != "live-turn":
            raise TeeError(
                "pipeline_not_a_live_turn",
                f"{what} is refused for a '{caller}' caller.",
                fix="Ad-hoc commands run only in a live human turn - never "
                "from a job, a schedule, a chore, a fronted backend, or any "
                "path carrying fetched content. Declare the step in "
                ".tee/pipeline.toml and run it with pipeline_run instead.",
            )
        if trustctx.taint():
            raise TeeError(
                "pipeline_tainted_turn",
                f"{what} is refused: this turn carries untrusted content "
                f"({', '.join(list(trustctx.taint())[:2])}).",
                fix="Untrusted content can never cause execution. Start a "
                "fresh turn and type the command yourself if you intend it.",
            )

    def _adhoc_enabled() -> None:
        pipeline_cfg = dict(getattr(app.config, "pipeline", {}) or {})
        if not pipeline_cfg.get("allow_adhoc", False):
            raise TeeError(
                "pipeline_adhoc_disabled",
                "Ad-hoc commands are not enabled for this project.",
                fix="Add [pipeline] allow_adhoc = true to .tee/config.toml "
                "(default false, the allow_code_exec precedent) AND grant "
                "'run-adhoc' in [trust] grants. Declared steps need neither.",
            )

    def pipeline_adhoc(args: dict[str, Any]) -> dict[str, Any]:
        _guard_live_turn("pipeline_adhoc")
        _adhoc_enabled()
        argv = args.get("argv")
        if not isinstance(argv, list):
            raise TeeError(
                "pipeline_bad_argv",
                "argv must be a list of arguments.",
                fix='argv = ["python", "builder/build.py", "--tile", "north"] '
                "- never a command string; TEE runs no shell.",
            )
        result = runner.run(
            [str(a) for a in argv],
            cwd=root,
            timeout_s=float(args.get("timeout_s") or runner.DEFAULT_TIMEOUT_S),
            observe=True,
        )
        _LAST_ADHOC[str(root)] = result
        payload: dict[str, Any] = {
            "ran": "ad-hoc, not declared",  # labelled in the report AND provenance
            "argv": result.argv,
            "exit": result.exit_code,
            "wall_s": result.wall_s,
            "cached": False,
            "scheduled": False,
        }
        if result.created or result.modified:
            payload["touched"] = {"created": result.created, "modified": result.modified}
        if not result.ok:
            payload["error"] = result.failure_line("ad-hoc")
            payload["tail"] = result.stderr_tail or result.stdout_tail
        elif result.stdout_tail:
            payload["output_tail"] = result.stdout_tail[-600:]
        payload["adopt"] = "pipeline_adopt {name: '<step name>'} turns this into a declaration"
        return payload

    def pipeline_adopt(args: dict[str, Any]) -> dict[str, Any]:
        """Offer the declaration TEE WOULD write - the owner moves it in."""
        _guard_live_turn("pipeline_adopt")
        last = _LAST_ADHOC.get(str(root))
        if last is None:
            raise TeeError(
                "pipeline_nothing_to_adopt",
                "No ad-hoc run in this session to adopt.",
                fix="Run pipeline_adhoc first; adoption describes what that run actually did.",
            )
        name = str(args.get("name") or "")
        if not schema._NAME.match(name):
            raise TeeError(
                "pipeline_bad_step",
                f"'{name}' is not a usable step name.",
                fix="Lower-case identifier, e.g. name = 'build_basemap'.",
            )
        kind = "produce" if (last.created or last.modified) else "query"
        outputs = sorted(set(last.created + last.modified))[:10]
        lines = [
            "# Proposed by TEE from an ad-hoc run - REVIEW BEFORE ADOPTING.",
            "# TEE does not write .tee/pipeline.toml; move this in yourself.",
            "[[step]]",
            f'name = "{name}"',
            f'kind = "{kind}"',
            "argv = [" + ", ".join(f'"{a}"' for a in last.argv) + "]",
        ]
        if kind == "produce" and outputs:
            lines.append("outputs = [" + ", ".join(f'"{o}"' for o in outputs) + "]")
        if kind == "query":
            lines.append('answer = { format = "text", max_tokens = 400 }')
        lines.append(
            f"cost = {{ wall_s = [{max(1, int(last.wall_s))}, {max(2, int(last.wall_s * 3))}] }}"
        )
        proposed = root / ".tee" / "pipeline.proposed.toml"
        proposed.parent.mkdir(parents=True, exist_ok=True)
        text = "\n".join(lines) + "\n"
        with proposed.open("a", encoding="utf-8") as handle:
            handle.write(("\n" if proposed.stat().st_size else "") + text)
        return {
            "proposed": str(proposed),
            "declaration": text,
            "next": f"Read it, then move the [[step]] block into "
            f"{root / '.tee' / 'pipeline.toml'} and approve the file. TEE "
            "never writes your declaration or approves its own inputs.",
            "inferred": {"kind": kind, "outputs": outputs},
        }

    app.registry.register(
        VirtualTool(
            "pipeline_adhoc",
            "Run ONE argv list in this project, live-turn only, when the "
            "project has opted in ([pipeline] allow_adhoc) and 'run-adhoc' is "
            "granted. Unscheduled, uncached and labelled 'ad-hoc, not "
            "declared'. This is the discovery door: run it once, then "
            "pipeline_adopt turns it into a declared step.",
            {
                "type": "object",
                "properties": {
                    "argv": {"type": "array", "items": {"type": "string"}},
                    "timeout_s": {"type": "number"},
                },
                "required": ["argv"],
            },
            pipeline_adhoc,
            tags=["pipeline", "adhoc", "run", "command", "discovery"],
        )
    )
    app.registry.register(
        VirtualTool(
            "pipeline_adopt",
            "Turn the last ad-hoc run into the declaration TEE would write - "
            "argv, kind and outputs inferred from what the run actually "
            "touched, plus a measured cost hint. Written to "
            ".tee/pipeline.proposed.toml for you to review and move; TEE never "
            "writes the real declaration.",
            {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
            pipeline_adopt,
            tags=["pipeline", "adopt", "declare", "propose", "step"],
        )
    )


_LAST_ADHOC: dict[str, runner.RunResult] = {}
