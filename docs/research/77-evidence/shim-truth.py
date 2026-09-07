"""77-evidence: what the shim advertises, against what it actually produces.

The lane's thesis in one measurement. `local_llm.available()` asks
`GET /v1/models` and calls a listed id available. This asks every advertised
route for six tokens and looks at what comes back.

    python3 shim-truth.py [base_url]
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:4000/v1"
TIMEOUT_S = 120.0


def _get(path: str):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def ask(model: str) -> dict:
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "say OK"}],
        "max_tokens": 6,
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/chat/completions", data=body,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as r:
            d = json.loads(r.read().decode())
        dt = time.perf_counter() - t0
        c = d["choices"][0]["message"].get("content")
        u = d.get("usage") or {}
        return {
            "http": 200, "wall_s": round(dt, 2),
            "content": c, "produced": bool(c and c.strip()),
            "completion_tokens": u.get("completion_tokens"),
            "finish": d["choices"][0].get("finish_reason"),
        }
    except urllib.error.HTTPError as e:
        return {"http": e.code, "wall_s": round(time.perf_counter() - t0, 2),
                "produced": False, "detail": e.read().decode()[:120]}
    except Exception as e:
        return {"http": None, "wall_s": round(time.perf_counter() - t0, 2),
                "produced": False, "detail": f"{type(e).__name__}: {e}"[:120]}


def main() -> None:
    listed = [m["id"] for m in _get("/models")["data"]]
    print(f"{BASE} advertises {len(listed)} routes\n")
    print(f"  {'route':22} {'/models':>8} {'asked':>7} {'produced':>9} {'tok':>4}  note")
    rows = {}
    for m in listed:
        if m.endswith("*"):
            print(f"  {m:22} {'listed':>8} {'-':>7} {'-':>9} {'-':>4}  wildcard, not a route")
            continue
        r = ask(m)
        rows[m] = r
        note = ""
        if r["http"] == 200 and not r["produced"]:
            note = "EMPTY 200 -- listed, usage billed, nothing produced"
        elif r["http"] == 200:
            note = repr(r.get("content", ""))[:28]
        else:
            note = f"{r.get('detail','')[:52]}"
        print(f"  {m:22} {'listed':>8} {str(r['http']):>7} "
              f"{str(r['produced']):>9} {str(r.get('completion_tokens') or '-'):>4}  {note}")

    answered = [m for m, r in rows.items() if r["produced"]]
    lying = [m for m, r in rows.items() if r["http"] == 200 and not r["produced"]]
    print(f"\n  advertised {len(listed)} | produce text {len(answered)} | "
          f"200-but-empty {len(lying)} | errored {len(rows) - len(answered) - len(lying)}")
    print("\n  A liveness check that reads /v1/models sees every one of these as healthy.")
    print("  A check that reads only the HTTP code still sees the empty ones as healthy.")
    print("  Only a check that reads the CONTENT is telling the truth.")
    json.dump({"base": BASE, "listed": listed, "rows": rows},
              open("shim-truth.json", "w"), indent=2, sort_keys=True)


main()
