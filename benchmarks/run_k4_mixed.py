"""A42 K4: the mixed-load benchmark — the scheduler wins here or reverts.

Two arms over an IDENTICAL live mixed workload, the machine quiet:

  static     [scheduler] qos/dispatch off - plain FIFO, today's behavior
  scheduled  qos law + reservation + greedy dispatch

Workload per arm (real lane work, no synthetic sleeps): 2 batch
reconstruction jobs (the 36-view preview through the real helper,
~16 s each) + 8 interactive-class jobs (real hillshade products via
qgis_process on the site DSM) submitted while the batches run + 6
routed live chores (triage on the mlx endpoint) interleaved. Metrics:
makespan, interactive job queue-wait p95 (the head-of-line number the
scheduler exists to kill), verified chores, client tokens, and the
meter block. Honesty: a scheduler adds nothing under a single task -
this row is the ONLY place it may claim a win (research 58).

Usage:
  uv run --project ../server python run_k4_mixed.py --url URL --orbit DIR --dsm FILE
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "server" / "src"))
sys.path.insert(0, str(REPO / "server" / "tests"))

from fixtures_llm import CONTROLS, TRAPS  # noqa: E402

from tee.app import TeeApp  # noqa: E402
from tee.capture.tools import register_capture_tools  # noqa: E402
from tee.extract.tools import register_extract_tools  # noqa: E402
from tee.kernel.adapter import FakeAdapter  # noqa: E402
from tee.llm import chores, router  # noqa: E402

Q14B = "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit"
A2 = str(REPO / "benchmarks" / "rung1" / "adapters" / "tee-triage-a2")


def run_arm(name: str, scheduled: bool, args) -> dict:
    project = Path.home() / ".cache" / f"tee-k4-{name}"
    project.mkdir(parents=True, exist_ok=True)
    config = project / ".tee" / "config.toml"
    config.parent.mkdir(exist_ok=True)
    config.write_text(
        "[scheduler]\nqos = {q}\ndispatch = {q}\n".format(q="true" if scheduled else "false")
    )
    app = TeeApp({"fake": FakeAdapter()}, project_root=project)
    store, _ = register_extract_tools(app, project)
    app.config.capture = {
        "helper": str(REPO / "helpers" / "photogrammetry" / "tee-photogrammetry"),
    }
    register_capture_tools(app, project, extract_store=store)

    orbit = sorted(Path(args.orbit).glob("*.jpg"))
    ingest = app.registry.call("capture_ingest", {"paths": [str(p) for p in orbit]})

    llm_cfg = {
        "url": args.url,
        "_state_dir": str(project / ".tee"),
        "profiles": {"q14b": {"model": Q14B, "adapters": A2}},
    }
    policy = "greedy" if scheduled else "static"
    started = time.time()

    # 2 batch reconstructions (real helper work)
    batch_jobs = []
    for detail in ("preview", "reduced"):
        job = app.registry.call(
            "capture_reconstruct",
            {"set": ingest["set"], "engine": "photogrammetry", "detail": detail},
        )
        batch_jobs.append(job["job"])

    # 6 routed live chores on a worker thread (interactive path, off-queue)
    chore_stats = {"verified": 0, "client_tokens": 0}

    def chore_stream():
        cases = [(t, "needs_verification") for t in TRAPS] + [
            (c, "grounded") for c in CONTROLS
        ]
        for fixture, expect in cases:
            routed = router.route(
                "triage",
                lambda cfg, f=fixture: chores.triage(
                    f["failure"], f["context"], refine="local", cfg=cfg
                ),
                cfg=llm_cfg,
                ledger=app.machine,
                input_pointer=f"k4:{fixture['name']}",
                policy=policy,
            )
            if routed["ok"] and routed["result"].get("confidence") == expect:
                chore_stats["verified"] += 1
            if not routed["ok"]:
                chore_stats["client_tokens"] += 300

    chore_thread = threading.Thread(target=chore_stream)
    chore_thread.start()

    # 8 interactive jobs (real hillshade) submitted while batches run
    time.sleep(0.5)
    interactive_jobs = []
    submit_times = {}
    for i in range(8):
        job_id = app.jobs.submit(
            f"hillshade-{i}",
            lambda i=i: app.registry.call(
                "capture_terrain", {"op": "hillshade", "dem": args.dsm}
            ),
            qos="interactive",
        )
        submit_times[job_id] = time.time()
        interactive_jobs.append(job_id)
        time.sleep(0.3)

    waits = []
    deadline = time.time() + 600
    pending = set(interactive_jobs + batch_jobs)
    finished_at = {}
    while pending and time.time() < deadline:
        for job_id in list(pending):
            status = app.jobs.status(job_id)
            if status["state"] in ("done", "error"):
                pending.discard(job_id)
                finished_at[job_id] = time.time()
        time.sleep(0.1)
    chore_thread.join(timeout=120)
    makespan = max(finished_at.values(), default=time.time()) - started

    for job_id in interactive_jobs:
        # queue wait approximated by completion minus submit minus own work;
        # hillshade work is ~constant, so completion latency IS the signal
        waits.append(finished_at.get(job_id, time.time()) - submit_times[job_id])
    waits.sort()
    p95 = waits[int(0.95 * (len(waits) - 1))] if waits else None
    block = app.machine.meter_block()
    app.shutdown()
    return {
        "arm": name,
        "makespan_s": round(makespan, 1),
        "interactive_latency_p95_s": round(p95, 2) if p95 is not None else None,
        "interactive_latencies_s": [round(w, 2) for w in waits],
        "chores_verified": f"{chore_stats['verified']}/6",
        "client_tokens": chore_stats["client_tokens"],
        "queue_column": block["scheduler"]["queue_age_s"],
        "dispatch": block["scheduler"]["dispatch_reason"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--orbit", required=True)
    parser.add_argument("--dsm", required=True)
    args = parser.parse_args()
    results = [run_arm("static", False, args), run_arm("scheduled", True, args)]
    print(json.dumps({"arms": results}, indent=1))
    static_arm, sched = results
    verdict = {
        "interactive_p95_improved": (
            sched["interactive_latency_p95_s"] < static_arm["interactive_latency_p95_s"]
            if None not in (sched["interactive_latency_p95_s"],
                            static_arm["interactive_latency_p95_s"])
            else None
        ),
        "makespan_delta_s": round(sched["makespan_s"] - static_arm["makespan_s"], 1),
    }
    print(json.dumps({"verdict": verdict}, indent=1))


if __name__ == "__main__":
    main()
