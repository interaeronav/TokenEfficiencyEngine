"""What is actually answering, and which server software it is.

Never generates. `GET /v1/models` and a fingerprint from the response shape and
headers - that is all, because the digest that consumes this must never probe.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

TIMEOUT_S = 3.0


#: Server software, from what the response looks like. A fingerprint is a
#: guess with its evidence attached, never a claim of fact.
def fingerprint(headers: dict[str, str], payload: dict[str, Any]) -> dict[str, str]:
    server = (headers.get("server") or "").lower()
    rows = payload.get("data") or []
    owners = {str(r.get("owned_by", "")).lower() for r in rows if isinstance(r, dict)}
    ids = [str(r.get("id", "")) for r in rows if isinstance(r, dict)]
    litellm_like = "openai" in owners and any(i.startswith("claude-") for i in ids)
    if "litellm" in server or litellm_like:
        return {"software": "litellm", "why": "server header or claude-* route names"}
    if any(i.startswith("mlx-community/") for i in ids):
        return {"software": "mlx", "why": "mlx-community/* model ids"}
    if "uvicorn" in server:
        return {"software": "uvicorn-hosted", "why": "server: uvicorn"}
    if "ollama" in server or any(":" in i and "/" not in i for i in ids):
        return {"software": "ollama?", "why": "tag-shaped ids or server header"}
    return {"software": "unknown", "why": f"server={server or 'absent'}, {len(ids)} ids"}


def probe_endpoint(url: str, timeout: float = TIMEOUT_S) -> dict[str, Any]:
    """One endpoint: does it answer, what does it list, how fast, what is it."""
    base = url.rstrip("/")
    out: dict[str, Any] = {"url": base}
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(f"{base}/models", timeout=timeout) as r:
            body = r.read().decode("utf-8")
            headers = {k.lower(): v for k, v in dict(r.headers).items()}
            code = r.status
    except urllib.error.HTTPError as exc:
        out |= {"answers": False, "http": exc.code, "reason": "refused the listing"}
        out["round_trip_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return out
    except Exception as exc:
        out |= {"answers": False, "http": None, "reason": f"{type(exc).__name__}"}
        out["round_trip_ms"] = round((time.perf_counter() - t0) * 1000, 1)
        return out
    out["round_trip_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError:
        out |= {"answers": True, "http": code, "reason": "not JSON", "models": []}
        return out
    rows = payload.get("data") if isinstance(payload, dict) else None
    ids = [str(r.get("id")) for r in rows or [] if isinstance(r, dict) and r.get("id")]
    out |= {
        "answers": True,
        "http": code,
        "models": sorted(ids)[:64],
        "model_count": len(ids),
        **fingerprint(headers, payload if isinstance(payload, dict) else {}),
    }
    return out


def endpoints(
    cfg: dict[str, Any], llm_cfg: dict[str, Any], senses_cfg: dict[str, Any]
) -> list[str]:
    """Every endpoint TEE knows about, de-duplicated, in a stable order."""
    seen: list[str] = []

    def add(u: Any) -> None:
        if not u:
            return
        s = str(u).rstrip("/")
        if s not in seen:
            seen.append(s)

    add(llm_cfg.get("url"))
    for spec in (llm_cfg.get("profiles") or {}).values():
        if isinstance(spec, dict):
            add(spec.get("url"))
    add(senses_cfg.get("vision_url"))
    for u in cfg.get("endpoints") or []:
        add(u)
    # ALWAYS, not only as a fallback: the vision driver's default is where the
    # VLM actually lives on this machine, and [senses] vision_url is unset -
    # so a scan that only read the config missed :8081 entirely and then
    # reported the vision engine as unserved.
    from tee.kernel import local_llm, local_vlm

    add(local_llm.DEFAULT_URL)
    add(getattr(local_vlm, "DEFAULT_URL", None))
    return seen


def scan(
    cfg: dict[str, Any], llm_cfg: dict[str, Any], senses_cfg: dict[str, Any]
) -> dict[str, Any]:
    """Every known endpoint, probed once. The lane's only network read."""
    urls = endpoints(cfg, llm_cfg, senses_cfg)
    rows = [probe_endpoint(u, float(cfg.get("timeout_s", TIMEOUT_S))) for u in urls]
    answering = [r for r in rows if r.get("answers")]
    served: dict[str, list[str]] = {}
    for r in answering:
        for m in r.get("models", []):
            served.setdefault(m, []).append(r["url"])
    return {
        "scanned": len(rows),
        "answering": len(answering),
        "endpoints": rows,
        "served_models": served,
        "scanned_at": time.time(),
    }
