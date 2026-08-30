#!/usr/bin/env python3
"""A43 P6: tokens per completed build and per answered query, lane vs naive.

The naive baseline is what actually happens without the lane, measured
rather than guessed: the model pastes the command into the conversation,
the command runs, and its whole output comes back into context - because
nothing has decided in advance which part of it was the answer. For a
produce step the model then has to ask what changed on disk, so the
naive column includes an `ls -l` of the declared outputs.

Every number below is measured on THIS machine against the two real
projects (A43 P4/P5). No step is stubbed and no output is trimmed by
hand.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server" / "src"))

from tee.app import TeeApp  # noqa: E402
from tee.kernel import trustctx  # noqa: E402
from tee.kernel.adapter import FakeAdapter  # noqa: E402
from tee.kernel.budget import estimate_tokens  # noqa: E402
from tee.pipeline import schema  # noqa: E402
from tee.pipeline.tools import register_pipeline_tools, register_run_tools  # noqa: E402

CASES = [
    ("basemap", "~/DiversionPlanner-BaseMap", "plan", {"cell": "N51W001"}),
    ("basemap", "~/DiversionPlanner-BaseMap", "selftest", {}),
    ("okongosim", "~/OkongoSim", "dimensions_selftest", {}),
    ("okongosim", "~/OkongoSim", "validate_catalog", {}),
    # The expensive query: 130+ s of hashing for a four-line answer. This is
    # where a cached answer stops being a token argument and starts being a
    # wall-clock one.
    ("basemap", "~/DiversionPlanner-BaseMap", "verify", {}),
]


def naive_tokens(root: Path, step: schema.Step, values: dict) -> tuple[int, dict]:
    """What lands in context without the lane: the command, then whatever
    the command says, then a listing when artifacts are the point."""
    argv = schema.substitute(step, values)
    env = {**os.environ, **schema.substitute_env(step, values)}
    started = time.time()
    done = subprocess.run(argv, cwd=root, capture_output=True, text=True, env=env, check=False)
    wall = time.time() - started
    parts = {
        "the command, pasted": estimate_tokens(" ".join(argv)),
        "its stdout": estimate_tokens(done.stdout or ""),
        "its stderr": estimate_tokens(done.stderr or ""),
    }
    if step.kind == "produce":
        listing = subprocess.run(
            ["ls", "-l", *[p.split("/")[0] for p in schema.substitute(
                schema.Step(name=step.name, kind=step.kind, argv=step.outputs, params=step.params),
                values)][:1]],
            cwd=root, capture_output=True, text=True, check=False,
        )
        parts["ls -l of the outputs"] = estimate_tokens(listing.stdout or "")
    return sum(parts.values()), {"parts": parts, "wall_s": round(wall, 2)}


def lane_tokens(app, step_name: str, values: dict) -> tuple[int, dict]:
    started = app.registry.call("pipeline_run", {"step": step_name, "params": values,
                                                 "force": True})
    while "job" in started:
        status = app.jobs.status(started["job"])
        if status["state"] in ("done", "error"):
            started = status.get("result") or status
            break
        time.sleep(0.1)
    return estimate_tokens(started), started


def main() -> int:
    rows = []
    for project, path, step_name, values in CASES:
        root = Path(os.path.expanduser(path))
        app = TeeApp({"fake": FakeAdapter()}, project_root=root)
        register_pipeline_tools(app, root)
        register_run_tools(app, root)
        trustctx.CALLER.set("live-turn")
        pipeline = schema.load(root)
        step = pipeline.require(step_name)

        naive, naive_detail = naive_tokens(root, step, values)
        lane, lane_payload = lane_tokens(app, step_name, values)
        app.shutdown()

        rows.append({
            "project": project,
            "step": step_name,
            "kind": step.kind,
            "naive_tokens": naive,
            "lane_tokens": lane,
            "wall_s": naive_detail["wall_s"],
            "saved_pct": round(100 * (naive - lane) / naive, 1) if naive else 0.0,
            "naive_detail": naive_detail,
            "lane_ok": "error" not in lane_payload,
        })
        print(f"{project:11} {step_name:20} {step.kind:8} "
              f"naive {naive:6}  lane {lane:6}  saved {rows[-1]['saved_pct']:6.1f}%  "
              f"wall {naive_detail['wall_s']:7.2f}s")

    # The repeat case: the same question asked twice. The lane answers from
    # the record; the naive path re-runs and re-pastes, every time.
    root = Path(os.path.expanduser("~/DiversionPlanner-BaseMap"))
    app = TeeApp({"fake": FakeAdapter()}, project_root=root)
    register_pipeline_tools(app, root)
    register_run_tools(app, root)
    trustctx.CALLER.set("live-turn")
    for primed in ("selftest", "verify"):
        lane_tokens(app, primed, {})  # prime the record
        started = time.time()
        # Must WAIT: a step that is not served from the record comes back as
        # a job token, and timing the submit would report a 132 s check as
        # instant. A cached answer returns inline, which is the difference
        # the row is trying to show.
        repeat = app.registry.call("pipeline_run", {"step": primed})
        while "job" in repeat:
            status = app.jobs.status(repeat["job"])
            if status["state"] in ("done", "error"):
                repeat = status.get("result") or status
                break
            time.sleep(0.1)
        rows.append({
            "project": "basemap",
            "step": f"{primed} (asked again)",
            "kind": "query",
            "naive_tokens": next(r["naive_tokens"] for r in rows if r["step"] == primed),
            "lane_tokens": estimate_tokens(repeat),
            "wall_s": round(time.time() - started, 3),
            "naive_wall_s": next(r["wall_s"] for r in rows if r["step"] == primed),
            "served_from_record": "cached" in repeat,
            "lane_ok": True,
        })
        rows[-1]["saved_pct"] = round(
            100 * (rows[-1]["naive_tokens"] - rows[-1]["lane_tokens"]) / rows[-1]["naive_tokens"],
            1,
        )
        print(f"{'basemap':11} {primed + ' (again)':20} {'query':8} "
              f"naive {rows[-1]['naive_tokens']:6}  lane {rows[-1]['lane_tokens']:6}  "
              f"saved {rows[-1]['saved_pct']:6.1f}%  "
              f"wall {rows[-1]['wall_s']:7.2f}s vs {rows[-1]['naive_wall_s']:.2f}s  "
              f"{'cached' if rows[-1]['served_from_record'] else 'RE-RAN'}")
    app.shutdown()

    out = Path(__file__).parent / "p6_pipeline.json"
    out.write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
