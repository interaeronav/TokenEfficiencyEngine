"""W1 baseline: record what a runtime does, then compare another against it.

  record  <src> <out.json> [--thinking on|off|unset]
  compare <src> <baseline.json> <out.json> [--thinking on|off|unset]

Same fixtures, same task checks, both sides. The fixture set is VERSIONED: a
comparison across different FIXTURES_VERSION values is refused rather than
silently reported, because that is the way a before/after row quietly stops
being one.

Task grading is independent of the chore validators where a fixture admits an
objective check, and marked shape_only where it does not. A shape pass is not
a task pass and the two are never summed.
"""
import argparse, hashlib, json, sys, time
from pathlib import Path

FIXTURES_VERSION = "w1-fixtures-1"

# ---------------------------------------------------------------- fixtures
CODE = ('rows = tee_call("bl_scene_summary", {"kind": "mesh"})\n'
        'total = 0\n'
        'for r in rows["items"]:\n'
        '    total = total + r["verts"]\n')
SLAB = ("The slab is 150 mm thick, C25/30, on 250 mm compacted G5 fill. Cover to "
        "reinforcement is 40 mm bottom, 25 mm top. Span 4.2 m one-way.")
CANDS = [{"id": "wall_with_openings", "title": "one watertight mesh with door/window openings"},
         {"id": "bl_create", "title": "add a primitive to the scene"},
         {"id": "sk_drape", "title": "drape a sewn garment on a body"},
         {"id": "pc_level", "title": "level a point cloud to the floor plane"},
         {"id": "pk_extrude", "title": "extrude a sketch into a solid"}]

# TRAPS must defer, CONTROLS must be grounded - the A34 calibration contract.
TRIAGE_CASES = [
    ("trap_kwarg", "TypeError: primitive_cube_add() got an unexpected keyword "
     "argument 'rotation'", "", "needs_verification"),
    ("trap_attr", "AttributeError: module 'unreal' has no attribute "
     "'EditorLevelLibrary'", "", "needs_verification"),
    ("ctrl_none", "AttributeError: 'NoneType' object has no attribute 'free'",
     "line 2: bm = existing.get(name)  # returns None when absent", "grounded"),
    ("ctrl_enum", "TypeError: enum \"FILL\" not found in "
     "('NOTHING', 'NGON', 'TRIFAN')", "", "grounded"),
]
RERANK_CASES = [
    ("wall", "watertight wall with openings", "wall_with_openings"),
    ("drape", "drape a garment on a body", "sk_drape"),
    ("level", "level a point cloud to the floor plane", "pc_level"),
    ("extrude", "extrude a sketch to a solid", "pk_extrude"),
]


def fixtures(chores, cfg, thinking, accepts_thinking):
    """(fixture_id, chore, callable, grader, graded?) - graded=False is shape only.

    W0's public chores have NO `thinking` parameter, so the kwarg is only sent
    to a runtime that accepts it. Passing it regardless turned every baseline
    fixture into a TypeError - a harness failure that would have been recorded
    as a runtime one.
    """
    TK = {"thinking": thinking} if accepts_thinking else {}
    F = []
    for fid, failure, ctx, want in TRIAGE_CASES:
        F.append((f"triage/{fid}", "triage",
                  lambda f=failure, c=ctx: chores.triage(f, c, cfg=cfg, **TK),
                  lambda r, w=want: (r or {}).get("confidence") == w, True))
    for fid, q, top in RERANK_CASES:
        F.append((f"rerank/{fid}", "rerank",
                  lambda q=q: chores.rerank(q, CANDS, cfg=cfg, **TK),
                  lambda r, t=top: bool(r) and r.get("order", [""])[0] == t, True))
    F.append(("repair_script/wrong_key", "repair_script",
              lambda: chores.repair_script(CODE,
                  "KeyError: 'verts'. Rows carry 'vertex_count'.", cfg=cfg, **TK),
              lambda r: bool(r) and "vertex_count" in r.get("repaired_code", ""), True))
    F.append(("refine_extract/cover", "refine_extract",
              lambda: chores.refine_extract(SLAB, "What is the cover to reinforcement?",
                  120, cfg=cfg, **TK),
              lambda r: bool(r) and "40 mm" in r.get("quote", ""), True))
    F.append(("structure_facts/slab", "structure_facts",
              lambda: chores.structure_facts(SLAB, cfg=cfg, **TK),
              lambda r: bool(r) and "150" in json.dumps(r), True))
    F.append(("phrase_deviation/numbers", "phrase_deviation",
              lambda: chores.phrase_deviation(
                  ["slab thickness 150 mm not 170 mm", "cover 40 mm bottom"],
                  cfg=cfg, **TK),
              lambda r: bool(r) and "150" in json.dumps(r) and "40" in json.dumps(r), True))
    F.append(("compress_recap/scene", "compress_recap",
              lambda: chores.compress_recap({"objects": 160, "ops": ["wall x62"]},
                  cfg=cfg, **TK),
              lambda r: r is not None, False))
    F.append(("explain_lint/e501", "explain_lint",
              lambda: chores.explain_lint("E501 line too long (118 > 100)",
                  cfg=cfg, **TK),
              lambda r: r is not None, False))
    return F


# ---------------------------------------------------------------- runner
def payload_fingerprint(src: Path) -> str:
    root = src / "tee"
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.is_symlink() or "__pycache__" in p.parts:
            continue
        if p.suffix in (".pyc", ".pyo") or p.name == ".DS_Store":
            continue
        b = p.read_bytes()
        files.append({"path": "tee/" + p.relative_to(root).as_posix(),
                      "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    blob = json.dumps({"algorithm": "tee-payload-v1", "files": files},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


def measure(src: Path, thinking_setting: str, model: str = "claude-qwen-27b"):
    sys.path.insert(0, str(src))
    from tee.kernel import local_llm
    from tee.llm import chores, profiles
    for m in (local_llm, chores, profiles):
        assert Path(m.__file__).resolve().is_relative_to(src), m.__file__

    state = Path(__file__).parent / "state"
    state.mkdir(parents=True, exist_ok=True)
    cfg = {"_state_dir": str(state), "_profile": "w1",
           "profiles": {"w1": {"url": "http://127.0.0.1:4000/v1",
                               "model": model, "adapters": "",
                               "thinking": True, "json_mode": "auto"}}}
    if thinking_setting != "unset":
        cfg["chore_thinking"] = thinking_setting

    # W0 has no owner setting; a per-call flag is the only way to ask it for ON.
    import inspect
    supports_owner_setting = hasattr(chores, "thinking_unavailable")
    accepts_thinking = "thinking" in inspect.signature(chores.triage).parameters
    per_call = None
    if not supports_owner_setting and thinking_setting == "on":
        per_call = True

    seen = {}
    real = local_llm.complete_json

    def wrapped(prompt, **kw):
        att = []

        def meter(payload, nbytes, secs):
            ch = (payload.get("choices") or [{}])[0]
            msg = ch.get("message") or {}
            u = payload.get("usage") or {}
            att.append({"finish_reason": ch.get("finish_reason", "unknown"),
                        "content_present": bool((msg.get("content") or "").strip()),
                        "reasoning_chars": len(msg.get("reasoning_content")
                                               or msg.get("reasoning") or ""),
                        "completion_tokens": u.get("completion_tokens", "unknown"),
                        "prompt_tokens": u.get("prompt_tokens", "unknown")})
        inner = kw.pop("on_usage", None)

        def both(p, n, s):
            meter(p, n, s)
            if inner:
                inner(p, n, s)
        seen.clear()
        seen.update(wire_thinking=kw.get("thinking"), cap=kw.get("max_tokens"),
                    model=kw.get("model"), url=kw.get("url"))
        try:
            return real(prompt, on_usage=both, **kw)
        finally:
            seen["attempts"] = att
    local_llm.complete_json = wrapped

    rows = []
    for fid, chore, call, grade, graded in fixtures(chores, cfg, per_call, accepts_thinking):
        chores._probe_cache.clear()
        t0 = time.monotonic()
        err = None
        try:
            r = call()
        except Exception as e:
            r, err = None, f"{type(e).__name__}:{getattr(e, 'code', '')}"
        obs = dict(seen)
        att = obs.pop("attempts", [])
        toks = sum(a["completion_tokens"] for a in att
                   if isinstance(a["completion_tokens"], int))
        rows.append({
            "fixture": fid, "chore": chore,
            "shape_ok": r is not None,
            "task_graded": graded,
            "task_ok": bool(grade(r)) if graded else None,
            "wire_thinking": obs.get("wire_thinking"),
            "effective_cap": obs.get("cap"),
            "attempts": len(att),
            "retries": max(0, len(att) - 1),
            "tokens_total": toks,
            "reasoning_chars": [a["reasoning_chars"] for a in att],
            "finish": [a["finish_reason"] for a in att],
            "degraded": getattr(chores, "LAST_DEGRADE", {}).get(chore),
            "error": err,
            "elapsed_s": round(time.monotonic() - t0, 2),
        })
        print(f"  {fid:<28} wire={obs.get('wire_thinking')} cap={obs.get('cap')} "
              f"shape={r is not None} task={rows[-1]['task_ok']} "
              f"tok={toks} err={err}", flush=True)

    return {
        "fixtures_version": FIXTURES_VERSION,
        "source": str(src),
        "payload_fingerprint": payload_fingerprint(src),
        "owner_setting_supported": supports_owner_setting,
        "public_chores_accept_thinking": accepts_thinking,
        "requested_setting": thinking_setting,
        "per_call_thinking": per_call,
        "route": {"model": cfg["profiles"]["w1"]["model"],
                  "url": cfg["profiles"]["w1"]["url"]},
        "records": rows,
    }


def totals(b):
    g = [r for r in b["records"] if r["task_graded"]]
    return {
        "task_correct": f"{sum(bool(r['task_ok']) for r in g)}/{len(g)}",
        "shape_ok": f"{sum(r['shape_ok'] for r in b['records'])}/{len(b['records'])}",
        "tokens_total": sum(r["tokens_total"] for r in b["records"]),
        "retries": sum(r["retries"] for r in b["records"]),
        "elapsed_s": round(sum(r["elapsed_s"] for r in b["records"]), 1),
        "thinking_on_wire": sum(bool(r["wire_thinking"]) for r in b["records"]),
        "degraded": sum(bool(r["degraded"]) for r in b["records"]),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["record", "compare"])
    ap.add_argument("src")
    ap.add_argument("rest", nargs="+")
    ap.add_argument("--thinking", default="unset", choices=["on", "off", "unset"])
    ap.add_argument("--model", default="claude-qwen-27b")
    a = ap.parse_args()
    src = Path(a.src).resolve()

    if a.action == "record":
        out = Path(a.rest[0])
        b = measure(src, a.thinking, a.model)
        b["totals"] = totals(b)
        out.write_text(json.dumps(b, indent=1))
        print("\n  BASELINE", out)
        print("  ", json.dumps(b["totals"]))
    else:
        base = json.loads(Path(a.rest[0]).read_text())
        out = Path(a.rest[1])
        cur = measure(src, a.thinking, a.model)
        cur["totals"] = totals(cur)
        if base["fixtures_version"] != cur["fixtures_version"]:
            raise SystemExit(f"REFUSED: fixture sets differ "
                             f"({base['fixtures_version']} vs {cur['fixtures_version']}); "
                             f"a comparison across fixture versions is not a before/after row")
        bi = {r["fixture"]: r for r in base["records"]}
        deltas = []
        for r in cur["records"]:
            o = bi.get(r["fixture"])
            if not o:
                deltas.append({"fixture": r["fixture"], "note": "new fixture"}); continue
            # A SHAPE regression counts. The first version of this check read
            # task_ok only, so a shape-graded fixture that stopped answering
            # at all was reported as "regressions: none" - the instrument
            # hiding the exact failure it was built to surface.
            task_lost = bool(o["task_ok"]) and not bool(r["task_ok"])
            shape_lost = bool(o["shape_ok"]) and not bool(r["shape_ok"])
            deltas.append({"fixture": r["fixture"],
                           "task": f"{o['task_ok']} -> {r['task_ok']}",
                           "shape": f"{o['shape_ok']} -> {r['shape_ok']}",
                           "finish": r["finish"],
                           "regressed": task_lost or shape_lost,
                           "regression_kind": ("task" if task_lost else
                                               "shape" if shape_lost else None),
                           "tokens": r["tokens_total"] - o["tokens_total"],
                           "elapsed_s": round(r["elapsed_s"] - o["elapsed_s"], 2),
                           "wire": f"{o['wire_thinking']} -> {r['wire_thinking']}"})
        report = {"baseline": {k: base[k] for k in
                               ("source", "payload_fingerprint", "requested_setting", "totals")},
                  "current": {k: cur[k] for k in
                              ("source", "payload_fingerprint", "requested_setting", "totals")},
                  "regressions": [d for d in deltas if d.get("regressed")],
                  "deltas": deltas, "current_records": cur["records"]}
        out.write_text(json.dumps(report, indent=1))
        print("\n  baseline", base["totals"])
        print("  current ", cur["totals"])
        print("  regressions:", [d["fixture"] for d in report["regressions"]] or "none")
        print("  ", out)
