"""A45 P2d — headless BI (Cube), compactly.

Cube Core is Apache-2.0 AND MIT, and TEE reaches it over plain HTTP with
**zero new dependencies** (stdlib `urllib`). It is a service the owner
runs; TEE neither bundles nor imports it.

**Why this module is not a passthrough.** Measured against a live Cube
1.7.30 on this machine, a three-row aggregate came back as **2,541 bytes**
of JSON - the rows themselves are perhaps 120 bytes and the rest is
annotation blocks, the echoed query, slow-query flags and per-member
metadata. Handing that to a model is the exact failure this project
exists to prevent.

So a result is returned as a `cols` header plus arrays-of-arrays, rounded,
with the row count and a `result_id`. That shape was measured at ~38%
cheaper than an array of objects even before the annotation is dropped.

A BI answer is quoted data from a database the model did not read, so
`read-bi` is a TAINT SOURCE: it is open by default (it changes nothing)
but its output can never go on to cause a side effect.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from tee.kernel.errors import TeeError

DEFAULT_URL = "http://127.0.0.1:4000"
API_PATH = "/cubejs-api/v1"
TIMEOUT = 60.0
DEFAULT_ROWS = 25
ROW_CAP = 500
_STORE: dict[str, dict[str, Any]] = {}
_STORE_CAP = 12
_SEQ = [0]


def _base(spec: dict[str, Any]) -> str:
    return str(spec.get("url") or DEFAULT_URL).rstrip("/")


def _get(spec: dict[str, Any], path: str, params: dict[str, str] | None = None) -> Any:
    url = f"{_base(spec)}{API_PATH}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET")
    token = spec.get("token") or spec.get("api_secret")
    if token:
        req.add_header("Authorization", str(token))
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:300].decode(errors="replace")
        if exc.code in (401, 403):
            raise TeeError(
                "bi_unauthorized",
                f"Cube refused the request ({exc.code}).",
                fix="Pass `token` (a Cube JWT). In dev mode Cube accepts none; "
                "in production it requires one signed with CUBEJS_API_SECRET.",
            ) from exc
        raise TeeError(
            "bi_http_error", f"Cube returned {exc.code}: {detail}", fix="Check the query shape."
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise TeeError(
            "bi_unreachable",
            f"No Cube at {_base(spec)} ({exc}).",
            fix="Start one: docker run -d -p 4100:4000 -v <conf>:/cube/conf "
            "cubejs/cube:latest, then pass url='http://127.0.0.1:4100'. "
            "NOTE Docker Desktop does not share /private/tmp - keep the config "
            "under your home directory.",
        ) from exc


def catalogue(spec: dict[str, Any]) -> dict[str, Any]:
    """What can be asked: cube names with their measures and dimensions."""
    started = time.monotonic()
    meta = _get(spec, "/meta")
    cubes = []
    for c in meta.get("cubes") or []:
        cubes.append(
            {
                "cube": c.get("name"),
                "measures": [m["name"] for m in c.get("measures") or []],
                "dimensions": [d["name"] for d in c.get("dimensions") or []],
            }
        )
    return {
        "ok": True,
        "url": _base(spec),
        "n_cubes": len(cubes),
        "cubes": cubes,
        "wall_s": round(time.monotonic() - started, 3),
        "note": "names only - ask bi_query for numbers",
    }


def _remember(payload: dict[str, Any]) -> str:
    _SEQ[0] += 1
    rid = f"bi_{_SEQ[0]}"
    _STORE[rid] = payload
    while len(_STORE) > _STORE_CAP:
        _STORE.pop(next(iter(_STORE)))
    return rid


def _round(v: Any) -> Any:
    """Cube returns numbers as STRINGS. Coerce, and round to the digits a
    decision needs rather than serialising whatever came back."""
    if isinstance(v, str):
        try:
            f = float(v)
        except ValueError:
            return v
        return int(f) if f.is_integer() else round(f, 4)
    if isinstance(v, float):
        return int(v) if float(v).is_integer() else round(v, 4)
    return v


def query(spec: dict[str, Any]) -> dict[str, Any]:
    q = spec.get("query")
    if not isinstance(q, dict) or not (q.get("measures") or q.get("dimensions")):
        raise TeeError(
            "bi_bad_query",
            "query needs at least one measure or dimension.",
            fix='query: {"measures": ["orders.count"], "dimensions": ["orders.status"]} '
            "- see bi_catalogue for the names.",
        )
    rows_wanted = max(1, min(int(spec.get("rows") or DEFAULT_ROWS), ROW_CAP))
    started = time.monotonic()
    payload = _get(spec, "/load", {"query": json.dumps(q)})
    if "error" in payload:
        raise TeeError(
            "bi_query_failed",
            str(payload["error"])[:300],
            fix="Check member names against bi_catalogue.",
        )
    data = payload.get("data") or []
    cols = list(data[0].keys()) if data else []
    table = [[_round(r.get(c)) for c in cols] for r in data]
    rid = _remember({"cols": cols, "rows": table, "query": q})
    out: dict[str, Any] = {
        "ok": True,
        "cols": cols,
        "rows": table[:rows_wanted],
        "n_rows": len(table),
        "result_id": rid,
        "wall_s": round(time.monotonic() - started, 3),
    }
    if len(table) > rows_wanted:
        out["more"] = (
            f"{len(table) - rows_wanted} more rows - bi_detail "
            f"{{result_id: '{rid}'}}, or aggregate in the query instead"
        )
    return out


def detail(result_id: str, offset: int = 0, limit: int = 100) -> dict[str, Any]:
    payload = _STORE.get(str(result_id))
    if payload is None:
        raise TeeError(
            "bi_unknown_result",
            f"No result '{result_id}' in this session.",
            fix=f"Known: {', '.join(_STORE) or '(none yet)'}. Re-run bi_query.",
        )
    rows = payload["rows"]
    offset = max(0, int(offset))
    limit = max(1, min(int(limit), ROW_CAP))
    return {
        "result_id": result_id,
        "cols": payload["cols"],
        "offset": offset,
        "returned": len(rows[offset : offset + limit]),
        "total": len(rows),
        "rows": rows[offset : offset + limit],
    }


def probe(spec: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = dict(spec or {})
    out: dict[str, Any] = {"url": _base(spec)}
    try:
        cat = catalogue(spec)
        out.update(
            {
                "reachable": True,
                "n_cubes": cat["n_cubes"],
                "cubes": [c["cube"] for c in cat["cubes"]],
            }
        )
    except TeeError as exc:
        out.update({"reachable": False, "why": exc.message, "fix": exc.fix})
    out["dependencies"] = "none - stdlib urllib only; Cube is a service you run"
    return out
