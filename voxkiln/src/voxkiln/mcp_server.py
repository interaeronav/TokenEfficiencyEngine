"""The MCP surface: exactly 4 tools (decision A28). Everything else -
weight management, format conversion, sampler exotica - lives in the
params dict, the CLI, or the Python API, never as tool schemas."""

from __future__ import annotations

import json
from typing import Any

from voxkiln.jobs import JobStore

_DESC = {
    "gen3d_generate": (
        "Generate a 3D asset (GLB with PBR textures) from one image. Blocks "
        "server-side until done or timeout_s, then returns the compact "
        "report: mesh stats, repair log, budget verdict with exact fixes, "
        "provenance. Identical requests hit the cache instead of the GPU. "
        "params: pipeline_type (512|1024|1024_cascade|1536_cascade), "
        "texture_size, target_faces, repair_level (fast|manifold|rebuild). "
        "budget: max_tris, require_watertight, target_size_m, max_texture. "
        "On timeout the answer carries the job_id - resume with gen3d_wait."
    ),
    "gen3d_wait": "Resume waiting on a job started by gen3d_generate that timed out.",
    "gen3d_query": "Look up a job or asset by id: state, report, provenance. No waiting.",
    "gen3d_status": (
        "Engine health: backend (mps/cuda/none + fix), weights cache, "
        "dependency probe, queue depth. Call this first on a new machine."
    ),
}


def build_server(store: JobStore | None = None):
    from mcp.server.mcpserver import MCPServer

    store = store or JobStore()
    mcp = MCPServer(
        name="voxkiln",
        instructions=(
            "Voxkiln: local image-to-3D generation for AI agents, built on "
            "TRELLIS.2. One gen3d_generate call returns the finished asset "
            "report - never poll in a loop. Reports are compact machine "
            "summaries (stats + repairs + verdict + provenance), not renders."
        ),
    )

    def _dump(payload: dict[str, Any]) -> str:
        return json.dumps(payload, separators=(",", ":"), default=str)

    @mcp.tool(structured_output=False, description=_DESC["gen3d_generate"])
    def gen3d_generate(
        image_path: str,
        params: dict | None = None,
        budget: dict | None = None,
        seed: int = 0,
        timeout_s: float = 900.0,
    ):
        from voxkiln.engine import EngineUnavailable

        try:
            return _dump(
                store.generate(
                    image_path, params=params, budget=budget, seed=seed, timeout_s=timeout_s
                )
            )
        except EngineUnavailable as exc:
            return _dump(exc.payload)
        except (FileNotFoundError, KeyError, ValueError) as exc:
            return _dump({"error": "bad_request", "message": str(exc)})

    @mcp.tool(structured_output=False, description=_DESC["gen3d_wait"])
    def gen3d_wait(job_id: str, timeout_s: float = 900.0):
        try:
            return _dump(store.wait(job_id, timeout_s=timeout_s))
        except KeyError as exc:
            return _dump({"error": "unknown_job", "message": str(exc)})

    @mcp.tool(structured_output=False, description=_DESC["gen3d_query"])
    def gen3d_query(job_id: str):
        try:
            return _dump(store.query(job_id))
        except KeyError as exc:
            return _dump({"error": "unknown_job", "message": str(exc)})

    @mcp.tool(structured_output=False, description=_DESC["gen3d_status"])
    def gen3d_status():
        from voxkiln.engine import doctor

        payload = doctor()
        payload["jobs"] = {jid: j.state for jid, j in store.jobs.items()}
        return _dump(payload)

    return mcp


def main() -> None:  # pragma: no cover - stdio entry
    build_server().run()
