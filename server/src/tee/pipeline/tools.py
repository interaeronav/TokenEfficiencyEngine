"""Pipeline virtual tools (A43 P0): `pipeline_list` only, deliberately.

P0 ships the schema, the validator and the hostile fixtures with NO
runner in existence - the acceptance is that the declaration surface is
provably safe before anything can execute.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from tee.kernel import trustctx
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.pipeline import graph, report, runner, schema


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

    def pipeline_init(args: dict[str, Any]) -> dict[str, Any]:
        """Draft a candidate file from the project's own scripts."""
        _guard_live_turn("pipeline_init")
        from tee.pipeline import init as init_mod

        proposed = root / ".tee" / "pipeline.proposed.toml"
        if proposed.exists() and not args.get("replace"):
            raise TeeError(
                "pipeline_draft_exists",
                f"{proposed} already exists and may hold proposals you have not read.",
                fix="Review and clear it, or call again with replace = true.",
            )
        candidates = init_mod.scan(root)
        text = init_mod.draft(root, candidates)
        proposed.parent.mkdir(parents=True, exist_ok=True)
        proposed.write_text(text, encoding="utf-8")
        return {
            "drafted": str(proposed),
            "candidates": [
                {"name": c.name, "path": c.path, "kind_guess": c.kind_guess} for c in candidates
            ],
            "runnable": False,
            "next": "Every block is commented out. Uncomment what you want, "
            "replace each <FILL>, state inputs/outputs, then approve the "
            f"file as {root / '.tee' / 'pipeline.toml'}.",
        }

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
            "pipeline_init",
            "Draft a candidate .tee/pipeline.toml by scanning this project's "
            "own scripts for entry points, their docstrings and the flags "
            "they require. Every drafted step is written COMMENTED OUT - the "
            "draft copied verbatim declares zero steps - because a scan is a "
            "guess about intent, not permission to run anything.",
            {"type": "object", "properties": {"replace": {"type": "boolean"}}},
            pipeline_init,
            tags=["pipeline", "init", "draft", "scan", "declare", "propose"],
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


def register_run_tools(app, project_root: Path | str) -> None:
    """`pipeline_run` (A43 P1): execute a DECLARED step as a job.

    Everything narrow about the lane converges here: the step must be
    declared, the declaration must be approved on this machine, the
    params must satisfy their declared constraints, and the capability
    must be granted. What comes back is an ANSWER - an artifact diff for
    a produce step, the step's own budgeted output for a query - never a
    log dump.
    """
    root = Path(project_root)

    def pipeline_run(args: dict[str, Any]) -> dict[str, Any]:
        pipeline = schema.load(root)
        if not pipeline.approved:
            raise TeeError(
                "pipeline_unapproved",
                f"{pipeline.path.name} is not approved on this machine ({pipeline.change}).",
                fix=f"Read it, then write its digest {pipeline.digest} to "
                f"{schema.pin_path(root)}. A declaration TEE has not been shown "
                "is attacker-authored by definition - a cloned repo ships one too.",
            )
        target = pipeline.require(str(args.get("step") or ""))
        values = dict(args.get("params") or {})
        force = bool(args.get("force"))
        # The target's params are validated BEFORE anything else looks at
        # them - including before freshness. A bad value must be refused on
        # its own terms; letting a fresh step swallow it would answer
        # "nothing to do" to a request that was never valid, which is a
        # success-shaped reply to a rejected question.
        schema.substitute(target, values)
        # P2: the target resolves through the DECLARED graph, and only stale
        # steps run. Every step's params are validated before anything
        # executes - a bad value must not surface halfway through a build.
        to_run, skipped = graph.plan(root, pipeline, target.name, values, force=force)
        plans = [(step, schema.substitute(step, values)) for step in to_run]
        if not plans:
            app.machine.record_pipeline(skipped=len(skipped))
            done: dict[str, Any] = {
                "target": target.name,
                "ran": [],
                "skipped": skipped,
                "answer": "all fresh - nothing to do",
            }
            # A question asked again gets its ANSWER, not a status line. The
            # inputs are unchanged, so the recorded answer is still the true
            # one - served for nothing instead of re-derived. It answers in
            # the SAME compact shape as a fresh run: a cached answer that
            # costs more than the answer would have is not a saving (P6
            # measured the fat envelope at 81 tokens against 59 fresh).
            if target.kind == "query":
                cached = graph.cached_answer(root, target)
                if cached is not None:
                    compact = {"step": target.name, "answer": cached.get("answer")}
                    if cached.get("format") not in (None, "text"):
                        compact["format"] = cached["format"]
                    compact["cached"] = cached.get("answered_at")
                    return compact
            return done

        timeout_s = float(
            args.get("timeout_s")
            or max((_declared_timeout(step) for step in to_run), default=runner.DEFAULT_TIMEOUT_S)
        )
        footprint = max(
            (float(step.cost.get("footprint_gb") or 2.0) for step in to_run), default=2.0
        )
        ledger_key = f"pipeline:{target.name}"
        app.machine.register_job(ledger_key, "pipeline-step", footprint_gb=footprint)
        started_at = time.strftime("%Y-%m-%d %H:%M:%S")

        def run_one(step: schema.Step, argv: list[str]) -> dict[str, Any]:
            before = report.snapshot_outputs(root, step, values) if step.kind == "produce" else {}
            inputs_digest = report.digest_inputs(root, step, values)
            result = runner.run(
                argv,
                cwd=root,
                timeout_s=timeout_s,
                env=schema.substitute_env(step, values),
            )
            payload: dict[str, Any] = {
                "step": step.name,
                "provenance": report.provenance(
                    step, argv, inputs_digest, started_at, result.wall_s
                ),
            }
            if not result.ok:
                # An exit code is worth its tokens only when it is not zero.
                payload["exit"] = result.exit_code
            if not result.ok:
                # Rule 6: one honest line naming the step, plus enough tail
                # to place it. 1200 characters WAS the stack-trace novel the
                # rule forbids - and it also made the lane cost more than
                # pasting the traceback, which is the whole thing it is
                # supposed to beat (P6 measured +23%).
                payload["error"] = result.failure_line(step.name)
                payload["tail"] = (result.stderr_tail or result.stdout_tail)[-600:]
                return payload
            if step.kind == "produce":
                payload["artifacts"] = report.artifact_diff(root, step, values, before)
            else:
                payload.update(report.query_answer(step, result.stdout_tail))
            # Only a SUCCESSFUL run is recorded, so a failure stays stale and
            # a retry actually retries. A query's answer is stored with it.
            graph.record_run(
                root,
                step,
                inputs_digest,
                payload["provenance"]["argv_hash"],
                answer=None
                if step.kind == "produce"
                else report.query_answer(step, result.stdout_tail),
            )
            return payload

        def worker() -> dict[str, Any]:
            ran: list[dict[str, Any]] = []
            try:
                for step, argv in plans:
                    outcome = run_one(step, argv)
                    ran.append(outcome)
                    if outcome.get("error"):
                        break  # never build on a broken dependency
            finally:
                app.machine.release_job(ledger_key)
            app.machine.record_pipeline(
                ran=len(ran),
                skipped=len(skipped),
                wall_s=sum(r["provenance"]["wall_s"] for r in ran),
            )
            if len(ran) == 1 and not skipped and ran[0]["step"] == target.name:
                return ran[0]  # the common case stays compact
            payload: dict[str, Any] = {"target": target.name, "ran": ran}
            if skipped:
                payload["skipped"] = skipped
            if force:
                payload["forced"] = "ran regardless of freshness (force = true)"
            return payload

        try:
            job_id = app.jobs.submit(
                f"pipeline {target.name}", worker, qos="batch", engine="pipeline-step"
            )
        except TeeError:
            app.machine.release_job(ledger_key)
            raise
        answer: dict[str, Any] = {
            "job": job_id,
            "target": target.name,
            "kind": target.kind,
            "will_run": [step.name for step in to_run],
            "note": "poll tee_job; produce steps answer with an artifact diff, "
            "query steps with their own budgeted output",
        }
        if skipped:
            answer["skipped"] = skipped
        return answer

    app.registry.register(
        VirtualTool(
            "pipeline_run",
            "Run one DECLARED step from this project's .tee/pipeline.toml as a "
            "job. Produce steps answer with an artifact diff (which declared "
            "outputs were created/changed/unchanged, sizes, hashes); query "
            "steps answer with their own output in the declared format, "
            "budgeted and provenance-stamped. Refuses an unapproved "
            "declaration, an undeclared step, or a param that breaks its "
            "declared constraint.",
            {
                "type": "object",
                "properties": {
                    "step": {"type": "string"},
                    "params": {"type": "object"},
                    "timeout_s": {"type": "number"},
                    "force": {"type": "boolean"},
                },
                "required": ["step"],
            },
            pipeline_run,
            tags=["pipeline", "run", "step", "build", "query", "declared", "job"],
        )
    )


def _declared_timeout(step: schema.Step) -> float:
    """A step's own cost hint is the timeout it asked for - generously
    doubled, because a hint is not a promise."""
    wall = step.cost.get("wall_s")
    if isinstance(wall, list) and wall:
        return max(60.0, float(wall[-1]) * 2)
    return runner.DEFAULT_TIMEOUT_S
