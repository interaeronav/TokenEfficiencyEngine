"""Hosted generation drivers (A14): Tripo and Meshy behind the ONE
GenerationLane adapter. Thin HTTP shells - API shapes per each vendor's
public docs (2026-08); exercised live only on keyed machines (the lane
contract itself is tested with the fake driver).

Costs are upfront tables, not billed-after surprises: ~$0.30/textured gen
(Tripo), ~$0.60 (Meshy) - surfaced in estimate() and gated by
confirm_cost at the lane level.
"""

from __future__ import annotations

import json
import urllib.request
from typing import Any

from tee.assets.http import USER_AGENT
from tee.kernel.errors import TeeError


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        raise TeeError(
            "generator_http_error", f"{url.split('/')[2]}: {exc.__class__.__name__}: {exc}"
        ) from exc


def _get_json(url: str, headers: dict) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **headers})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        raise TeeError(
            "generator_http_error", f"{url.split('/')[2]}: {exc.__class__.__name__}: {exc}"
        ) from exc


class TripoDriver:
    id = "tripo"
    paid = True
    _API = "https://api.tripo3d.ai/v2/openapi"

    def __init__(self, api_key: str):
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def estimate(self, kind: str, options: dict[str, Any]) -> dict[str, Any]:
        return {"cost_usd": 0.30, "note": "text->textured model, standard tier"}

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str:
        payload: dict[str, Any] = {"type": "text_to_model", "prompt": prompt}
        payload.update(options)
        out = _post_json(f"{self._API}/task", payload, self._headers)
        task_id = (out.get("data") or {}).get("task_id")
        if not task_id:
            raise TeeError("generation_failed", f"tripo: no task id in {str(out)[:120]}")
        return str(task_id)

    def poll(self, task_id: str) -> dict[str, Any]:
        out = _get_json(f"{self._API}/task/{task_id}", self._headers)
        data = out.get("data") or {}
        status = str(data.get("status", "unknown"))
        state = {
            "queued": "queued",
            "running": "running",
            "success": "done",
            "failed": "failed",
            "cancelled": "failed",
        }.get(status, "running")
        result = None
        if state == "done":
            output = data.get("output") or {}
            result = {"model_url": output.get("pbr_model") or output.get("model")}
        return {"state": state, "result": result, "error": data.get("error")}


class MeshyDriver:
    id = "meshy"
    paid = True
    _API = "https://api.meshy.ai/openapi/v2"

    def __init__(self, api_key: str):
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def estimate(self, kind: str, options: dict[str, Any]) -> dict[str, Any]:
        return {"cost_usd": 0.60, "note": "text->textured model incl. remesh"}

    def submit(self, kind: str, prompt: str, options: dict[str, Any]) -> str:
        payload: dict[str, Any] = {"mode": "preview", "prompt": prompt}
        payload.update(options)
        out = _post_json(f"{self._API}/text-to-3d", payload, self._headers)
        task_id = out.get("result")
        if not task_id:
            raise TeeError("generation_failed", f"meshy: no task id in {str(out)[:120]}")
        return str(task_id)

    def poll(self, task_id: str) -> dict[str, Any]:
        out = _get_json(f"{self._API}/text-to-3d/{task_id}", self._headers)
        status = str(out.get("status", "unknown"))
        state = {
            "PENDING": "queued",
            "IN_PROGRESS": "running",
            "SUCCEEDED": "done",
            "FAILED": "failed",
            "CANCELED": "failed",
        }.get(status, "running")
        result = None
        if state == "done":
            urls = out.get("model_urls") or {}
            result = {"model_url": urls.get("glb") or urls.get("fbx")}
        return {"state": state, "result": result, "error": out.get("task_error")}
