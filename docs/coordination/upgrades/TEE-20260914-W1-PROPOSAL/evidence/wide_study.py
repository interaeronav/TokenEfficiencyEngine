"""Wider-scale study: 140 held-out triage records, both models, production effort.

Design notes, because the sample size is the point:

  FIXTURES   benchmarks/rung1/data/valid.jsonl - TEE's own held-out triage
             corpus, 140 records, 81 grounded / 59 needs_verification. The
             corpus system prompt is r2 and production is r4, but the diff is
             WORDING ONLY: every decision rule survives clause for clause,
             including the worked example. So the labels are valid ground
             truth and the PRODUCTION prompt is what gets sent.

  SPLIT      deterministic even/odd. Odd indices tune, even indices score.
             A corrector fitted and scored on the same records proves nothing.

  ARMS       both engines at the production effort. High effort was measured
             worse and is the slowest arm; spending the budget on 140 records
             at one setting buys more than 6 records at three.

  ANSWERS    every raw answer is stored, so any number of DETERMINISTIC
             correctors can be evaluated offline without another model call.
             That is the whole reason a syndrome is cheap: it is a function of
             (evidence, answer), so the model runs once.
"""
import json, sys, time
from pathlib import Path
SRC = Path("/Users/john/tee-w1-candidate/server/src")
sys.path.insert(0, str(SRC))
from tee.kernel import local_llm
from tee.llm.chores import _TRIAGE_SYSTEM

CORPUS = Path("/Users/john/TokenEfficiencyEngine/benchmarks/rung1/data/valid.jsonl")
OUT = Path("/Users/john/tee-w1-candidate/w1-lab/wide-study-raw.json")
ROUTES = {"8-bit": "claude-qwen-27b", "4-bit": "claude-qwen-27b-4bit"}

records = []
for i, line in enumerate(CORPUS.read_text().splitlines()):
    m = json.loads(line)["messages"]
    try:
        label = json.loads(m[2]["content"])
    except Exception:
        continue
    if label.get("confidence") not in ("grounded", "needs_verification"):
        continue
    records.append({"i": i, "user": m[1]["content"], "want": label["confidence"],
                    "split": "tune" if i % 2 else "score"})
print(f"  {len(records)} usable records "
      f"({sum(r['split']=='score' for r in records)} scoring)", flush=True)

out = {"prompt_revision": "r4 production", "records": len(records), "arms": {}}
for label, model in ROUTES.items():
    rows, t0 = [], time.monotonic()
    for n, rec in enumerate(records):
        try:
            ans = local_llm.complete_json(
                rec["user"], system=_TRIAGE_SYSTEM,
                url="http://127.0.0.1:4000/v1", model=model,
                max_tokens=1024, adapters=None, thinking=True, json_mode="auto")
            err = None
        except Exception as e:
            ans, err = None, f"{type(e).__name__}:{getattr(e,'code','')}"
        rows.append({**rec, "answer": ans, "error": err})
        if n % 20 == 19:
            done = sum(1 for x in rows if x["answer"])
            hit = sum(1 for x in rows if (x["answer"] or {}).get("confidence") == x["want"])
            print(f"    {label} {n+1}/{len(records)}  answered {done}  correct {hit}  "
                  f"{round(time.monotonic()-t0)}s", flush=True)
    out["arms"][label] = {"model": model, "wall_s": round(time.monotonic()-t0, 1), "rows": rows}
    hit = sum(1 for x in rows if (x["answer"] or {}).get("confidence") == x["want"])
    print(f"  {label}: {hit}/{len(rows)} correct, {out['arms'][label]['wall_s']}s", flush=True)

OUT.write_text(json.dumps(out, indent=1))
print("saved", OUT)
