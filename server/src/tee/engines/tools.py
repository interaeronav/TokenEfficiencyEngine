"""The eng_* virtual tools (A76).

Zero added to the always-loaded surface. The digest never probes; probing is a
tool the caller chooses. Nothing here starts, stops, configures or serves.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tee.engines import discover, table, weights
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.llm import profiles as prof

SCAN_CACHE = "engine-scan.json"
CHECK_TOKENS = 8


class _Lane:
    def __init__(self, app, project_root: Path, cfg: dict[str, Any]) -> None:
        self.app = app
        self.root = Path(project_root)
        self.cfg = cfg

    # -- config seams ------------------------------------------------------
    def _llm_cfg(self) -> dict[str, Any]:
        cfg = dict(getattr(getattr(self.app, "config", None), "llm", {}) or {})
        cfg["_state_dir"] = str(self.root / ".tee")
        return cfg

    def _senses_cfg(self) -> dict[str, Any]:
        return dict(getattr(getattr(self.app, "config", None), "senses", {}) or {})

    def _state_dir(self) -> Path:
        return self.root / ".tee"

    def _cached_scan(self) -> dict[str, Any]:
        p = self._state_dir() / SCAN_CACHE
        if not p.is_file():
            return {"scanned": 0, "answering": 0, "endpoints": [], "served_models": {}}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"scanned": 0, "answering": 0, "endpoints": [], "served_models": {}}

    # -- tools -------------------------------------------------------------
    def scan(self, args: dict[str, Any]) -> dict[str, Any]:
        out = discover.scan(self.cfg, self._llm_cfg(), self._senses_cfg())
        d = self._state_dir()
        d.mkdir(parents=True, exist_ok=True)
        (d / SCAN_CACHE).write_text(json.dumps(out, indent=2, sort_keys=True))
        # the digest of the digest: endpoints and counts, never every id
        return {
            "scanned": out["scanned"],
            "answering": out["answering"],
            "endpoints": [
                {k: v for k, v in r.items() if k != "models"} | {"models": len(r.get("models", []))}
                for r in out["endpoints"]
            ],
            "served_model_count": len(out["served_models"]),
            "next": "eng_reconcile",
        }

    def senses(self, args: dict[str, Any]) -> dict[str, Any]:
        model = str(args.get("model") or "").strip()
        if not model:
            raise TeeError(
                "eng_needs_model",
                "eng_senses needs a model id.",
                fix="Give model='org/name' as the weights are named on disk.",
            )
        return weights.describe(model)

    def check(self, args: dict[str, Any]) -> dict[str, Any]:
        """One tiny completion, and READ WHAT COMES BACK.

        The lane exists because four of eight advertised routes on the owner's
        machine answer HTTP 200 with empty content. A check that reads the
        status code is not a check.
        """
        url = str(args.get("url") or self._llm_cfg().get("url") or "").rstrip("/")
        model = str(args.get("model") or "")
        if not url or not model:
            raise TeeError(
                "eng_needs_endpoint",
                "eng_ask needs url and model.",
                fix="eng_scan lists what answers and what each endpoint serves.",
            )
        if self._is_paid(model):
            raise TeeError(
                "eng_paid_refused",
                f"{model!r} resolves to a profile marked paid = true.",
                fix="The lane never measures a paid engine; it would bill you to "
                "learn a number the router is forbidden to use.",
            )
        body = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": "say OK"}],
                "max_tokens": CHECK_TOKENS,
            }
        ).encode()
        req = urllib.request.Request(
            f"{url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        t0 = time.perf_counter()
        try:
            timeout = float(self.cfg.get("check_timeout_s", 120))
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = json.loads(r.read().decode("utf-8"))
            http = r.status if hasattr(r, "status") else 200
        except urllib.error.HTTPError as exc:
            return {
                "url": url,
                "model": model,
                "http": exc.code,
                "produced": False,
                "wall_s": round(time.perf_counter() - t0, 3),
                "verdict": "errored",
                "detail": exc.read().decode()[:200],
            }
        except Exception as exc:
            return {
                "url": url,
                "model": model,
                "http": None,
                "produced": False,
                "wall_s": round(time.perf_counter() - t0, 3),
                "verdict": "unreachable",
                "detail": f"{type(exc).__name__}: {exc}"[:200],
            }
        wall = round(time.perf_counter() - t0, 3)
        choice = (payload.get("choices") or [{}])[0]
        content = (choice.get("message") or {}).get("content")
        usage = payload.get("usage") or {}
        produced = bool(content and str(content).strip())
        out = {
            "url": url,
            "model": model,
            "http": http,
            "wall_s": wall,
            "produced": produced,
            "verdict": "answers" if produced else "empty-200",
            "finish_reason": choice.get("finish_reason"),
            "completion_tokens": usage.get("completion_tokens"),
            "conformance": {
                "think_leaked": "<think>" in str(content or ""),
                "usage_present": bool(usage),
                "usage_claims_tokens_but_produced_nothing": bool(
                    not produced and usage.get("completion_tokens")
                ),
            },
        }
        if not produced:
            out["note"] = (
                "listed, HTTP 200, usage billed, nothing produced - a liveness "
                "check that reads /v1/models or the status code calls this healthy"
            )
        return out

    def _is_paid(self, model: str) -> bool:
        for spec in (self._llm_cfg().get("profiles") or {}).values():
            if isinstance(spec, dict) and spec.get("paid") and spec.get("model") == model:
                return True
        return False

    def audition(self, args: dict[str, Any]) -> dict[str, Any]:
        """Measure an engine by making it do TEE's own work. A job, because a
        sweep is minutes and a tool call never waits on one."""
        from tee.engines import audition as aud

        url = str(args.get("url") or self._llm_cfg().get("url") or "").rstrip("/")
        model = str(args.get("model") or "")
        engine = str(args.get("engine") or model or "unnamed")
        if not url or not model:
            raise TeeError(
                "eng_needs_endpoint",
                "eng_audition needs url and model.",
                fix="eng_scan lists what answers and what each endpoint serves.",
            )
        if self._is_paid(model):
            raise TeeError(
                "eng_paid_refused",
                f"{model!r} resolves to a profile marked paid = true.",
                fix="Measuring a hosted model bills you to learn a number the "
                "router is forbidden to use. Audition local engines only.",
            )
        cfg = self._llm_cfg()
        samples = int(args.get("samples", aud.WARM_SAMPLES))

        def work() -> dict[str, Any]:
            return aud.audition(cfg, engine=engine, url=url, model=model, samples=samples)

        jobs = getattr(self.app, "jobs", None)
        if jobs is None:  # a test app without a job kernel measures inline
            return {"row": work(), "note": "measured inline; no job kernel here"}
        job_id = jobs.submit(f"eng_audition {engine}", work, qos="batch", engine="engine-audition")
        return {
            "job": job_id,
            "engine": engine,
            "next": "tee_job to collect, then eng_adopt to make it authoritative",
        }

    def reconcile(self, args: dict[str, Any]) -> dict[str, Any]:
        llm_cfg = self._llm_cfg()
        out = table.reconcile(
            declared_profiles=prof.profiles(llm_cfg),
            scan=self._cached_scan(),
            measured=table.load_measured(self._state_dir()),
            resolved=prof.resolve(llm_cfg),
            stale_days=float(self.cfg.get("stale_days", table.STALE_DAYS)),
        )
        if not out["endpoints"]["scanned"]:
            out["note"] = "no scan cached: run eng_scan first (this tool never probes)"
        return out

    def adopt(self, args: dict[str, Any]) -> dict[str, Any]:
        engine = str(args.get("engine") or "")
        row = args.get("row")
        if not engine or not isinstance(row, dict):
            raise TeeError(
                "eng_needs_row",
                "eng_adopt needs engine and a measured row.",
                fix="Take the row from eng_audition; the lane does not invent one.",
            )
        if row.get("paid"):
            raise TeeError(
                "eng_paid_refused",
                f"{engine!r} is a paid engine; it is never a router target.",
                fix="Measure and adopt only local engines.",
            )
        rows = table.load_measured(self._state_dir())
        rows[engine] = {**row, "measured_at": row.get("measured_at") or time.time()}
        path = table.save_measured(self._state_dir(), rows)
        return {
            "adopted": engine,
            "path": str(path) if path else None,
            "measured_rows": len(rows),
            "note": "the ladder orders on this file; .tee/config.toml is untouched",
        }


_URL = {"type": "string", "description": "Endpoint base, e.g. http://127.0.0.1:4000/v1"}


def register_engine_tools(app, project_root: Path | str) -> None:
    root = Path(project_root)
    cfg = dict(getattr(getattr(app, "config", None), "engines", {}) or {})
    lane = _Lane(app, root, cfg)
    reg = app.registry

    specs: list[tuple[str, str, dict, Any, list[str], list[dict]]] = [
        (
            "eng_scan",
            "Which local model endpoints actually answer, what each serves, how fast, and "
            "which server software it looks like. Lists only; never generates.",
            {"type": "object", "properties": {}},
            lane.scan,
            ["engine", "local", "model", "endpoint", "discover", "serving"],
            [{"summary": "what is running", "arguments": {}}],
        ),
        (
            "eng_senses",
            "What a model's own weights say about it: vision or audio from its config.json, "
            "architectures, and a measured footprint. Never infers a sense from behaviour.",
            {"type": "object", "properties": {"model": {"type": "string"}}, "required": ["model"]},
            lane.senses,
            ["engine", "senses", "vision", "weights", "footprint", "config"],
            [
                {
                    "summary": "can this model see",
                    "arguments": {"model": "mlx-community/Qwen3-VL-30B-A3B-Instruct-4bit"},
                }
            ],
        ),
        (
            "eng_ask",
            "Ask one endpoint for eight tokens and read what comes back. A route can answer "
            "HTTP 200 with empty content and a billed usage block; only the content tells "
            "the truth. Refuses a paid engine by name.",
            {
                "type": "object",
                "properties": {"url": _URL, "model": {"type": "string"}},
                "required": ["model"],
            },
            lane.check,
            ["engine", "endpoint", "liveness", "completion", "produces", "empty"],
            [
                {
                    "summary": "does this route actually produce text",
                    "arguments": {"model": "claude-qwen-vl"},
                }
            ],
        ),
        (
            "eng_audition",
            "Measure an engine by making it do TEE's own chore, graded by that chore's own "
            "validator: warm and cold latency, the token floor found by a descending sweep, "
            "and whether it passes at all. A job. Refuses a paid engine.",
            {
                "type": "object",
                "properties": {
                    "url": _URL,
                    "model": {"type": "string"},
                    "engine": {"type": "string"},
                    "samples": {"type": "integer"},
                },
                "required": ["model"],
            },
            lane.audition,
            ["engine", "audition", "measure", "latency", "floor", "benchmark"],
            [
                {
                    "summary": "measure this engine for real",
                    "arguments": {"model": "mlx-community/Qwen3.8-27B-bf16", "engine": "q27b-bare"},
                }
            ],
        ),
        (
            "eng_reconcile",
            "The registry against reality: one verdict per engine and the one line that fixes "
            "it. Reads the cached scan and says how old it is; never probes.",
            {"type": "object", "properties": {}},
            lane.reconcile,
            ["engine", "reconcile", "drift", "registry", "stale", "declared"],
            [{"summary": "are the router's numbers still true", "arguments": {}}],
        ),
        (
            "eng_adopt",
            "Write a measured engine row where the router's ladder reads it. Refuses a paid "
            "engine. Never writes the owner's config - it prints the line to paste.",
            {
                "type": "object",
                "properties": {"engine": {"type": "string"}, "row": {"type": "object"}},
                "required": ["engine", "row"],
            },
            lane.adopt,
            ["engine", "adopt", "measured", "ladder", "persist"],
            [
                {
                    "summary": "make a measured row authoritative",
                    "arguments": {"engine": "q27b-bare", "row": {"footprint_gb": 50.956}},
                }
            ],
        ),
    ]
    for name, description, schema, handler, tags, examples in specs:
        reg.register(
            VirtualTool(
                name=name,
                description=description,
                schema=schema,
                handler=handler,
                tags=tags,
                examples=examples,
            )
        )
