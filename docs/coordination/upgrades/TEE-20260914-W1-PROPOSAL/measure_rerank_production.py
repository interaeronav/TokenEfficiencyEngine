"""W1 revision 2: the five rerank fixtures through the REAL public chore.

Explicit source and output arguments - revision 1's reproduction command had an
undefined INSTALLED_SRC and wrote into an ephemeral scratch directory.

  python measure_rerank_production.py <installed_src> <out_dir> [caps...]

Instruments by WRAPPING local_llm.complete_json, so production prompts, the
effective budget _run computes, the request mode wire_thinking derives, and the
chore's own validator are all the real ones. One record per attempt; usage is
aggregated across attempts rather than overwritten.
"""
import hashlib, json, sys, time
from pathlib import Path

SRC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
CAPS = [int(x) for x in sys.argv[3:]] or [None]        # None = production literal
sys.path.insert(0, str(SRC))

from tee.kernel import local_llm
from tee.llm import chores, profiles
from tee.kernel import machine
import tomllib

# --- assert we imported the tree we were told to, not the editable install ---
for mod in (local_llm, chores, profiles):
    assert Path(mod.__file__).resolve().is_relative_to(SRC), (
        f"{mod.__name__} came from {mod.__file__}, not {SRC}")

CFG = tomllib.load(open("/Users/john/TokenEfficiencyEngine/.tee/config.toml", "rb"))["llm"]

QUERIES = ["watertight wall with openings", "drape a garment on a body",
           "level a point cloud to the floor plane", "extrude a sketch to a solid",
           "run a wind tunnel sweep and read the polar"]
# rerank's contract is [{id, title}] and its validator demands a permutation
# of exactly the ids shown - revision 1's {name, summary} never reached the
# model at all (KeyError 'id', zero attempts).
CANDIDATES = [
    {"id": "wall_with_openings", "title": "one watertight mesh with door/window openings"},
    {"id": "bl_create", "title": "add a primitive to the Blender scene"},
    {"id": "sk_drape", "title": "drape a sewn garment on a body"},
    {"id": "pc_level", "title": "level a point cloud to its dominant horizontal plane"},
    {"id": "pk_extrude", "title": "extrude a partkiln sketch into a solid"},
    {"id": "wt_sweep", "title": "run a wind-tunnel alpha sweep and return the polar"},
]
EXPECT = ["wall_with_openings", "sk_drape", "pc_level", "pk_extrude", "wt_sweep"]

records = []
_real = local_llm.complete_json

def wrapped(prompt, **kw):
    """Observe the REAL request; append one record per HTTP attempt."""
    attempts = []
    def meter(payload, nbytes, secs, _a=attempts):
        ch = (payload.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        u = payload.get("usage") or {}
        _a.append({
            "finish_reason": ch.get("finish_reason", "unknown"),
            "content_present": bool((msg.get("content") or "").strip()),
            "reasoning_chars": len(msg.get("reasoning_content") or msg.get("reasoning") or ""),
            "prompt_tokens": u.get("prompt_tokens", "unknown"),
            "completion_tokens": u.get("completion_tokens", "unknown"),
            "seconds": round(secs, 2),
        })
    inner = kw.pop("on_usage", None)
    def both(payload, nbytes, secs):
        meter(payload, nbytes, secs)
        if inner: inner(payload, nbytes, secs)
    wrapped.seen = {"requested_max_tokens": kw.get("max_tokens"),
                    "thinking_on_wire": kw.get("thinking"),
                    "json_mode": kw.get("json_mode"),
                    "model": kw.get("model"), "url": kw.get("url"),
                    "adapters": kw.get("adapters")}
    try:
        out = _real(prompt, on_usage=both, **kw)
        wrapped.seen["attempts"] = attempts
        return out
    except Exception:
        wrapped.seen["attempts"] = attempts
        raise

local_llm.complete_json = wrapped

def run(profile, cap, mode):
    cfg = {**CFG, "_profile": profile,
           "_state_dir": "/Users/john/TokenEfficiencyEngine/.tee"}
    resolved = profiles.resolve(cfg)
    floor = machine.min_chore_tokens(resolved.get("profile"))
    for i, q in enumerate(QUERIES):
        wrapped.seen = {}
        t0 = time.monotonic()
        err = None
        try:
            r = chores.rerank(q, CANDIDATES, refine=mode, cfg=cfg)
        except Exception as e:
            r, err = None, f"{type(e).__name__}:{getattr(e,'code','')}:{str(e)[:120]}"
        seen = dict(wrapped.seen)
        att = seen.pop("attempts", [])
        top = ""
        if isinstance(r, dict):
            order = r.get("order") or []
            top = str(order[0]) if order else ""
        records.append({
            "fixture": f"rerank_{i}", "query": q, "expect_top": EXPECT[i],
            "profile": profile, "route_model": resolved.get("model"),
            "route_url": resolved.get("url"), "profile_declares_thinking":
                bool(resolved.get("thinking")),
            "literal_cap": 200 if cap is None else cap,
            "engine_floor": floor,
            "effective_cap_expected": max(200 if cap is None else cap, floor),
            "refine_mode": mode, "path": "public_chore" if cap is None else "run_seam",
            "observed_request": seen,
            "attempts": att,
            "attempt_count": len(att),
            "tokens_generated_total": sum(a["completion_tokens"] for a in att
                                          if isinstance(a["completion_tokens"], int)),
            "validator_result": "accepted" if r is not None else "rejected_or_error",
            "task_top_choice": top[:60],
            "task_correct": (top == EXPECT[i]) if top else False,
            "error": err,
            "elapsed_s": round(time.monotonic() - t0, 2),
        })
        print(f"  {profile:<8} {mode:<6} cap={records[-1]['literal_cap']:<5} "
              f"{records[-1]['fixture']:<10} valid={r is not None} "
              f"att={len(att)} tok={records[-1]['tokens_generated_total']} "
              f"finish={[a['finish_reason'] for a in att]} err={err}", flush=True)

for prof in ("27b", "27b4bit"):
    for mode in ("auto", "local"):
        for cap in CAPS:
            run(prof, cap, mode)

fp = hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "rerank-production.json").write_text(json.dumps(
    {"source": str(SRC), "records": records, "records_sha256": fp}, indent=1))
print("saved", OUT / "rerank-production.json", fp[:16])
