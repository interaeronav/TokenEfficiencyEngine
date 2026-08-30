"""Pipeline virtual tools (A43 P0): `pipeline_list` only, deliberately.

P0 ships the schema, the validator and the hostile fixtures with NO
runner in existence - the acceptance is that the declaration surface is
provably safe before anything can execute.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.registry import VirtualTool
from tee.pipeline import schema


def register_pipeline_tools(app, project_root: Path | str) -> None:
    root = Path(project_root)

    def pipeline_list(args: dict[str, Any]) -> dict[str, Any]:
        pipeline = schema.load(root)
        payload: dict[str, Any] = {
            "file": str(pipeline.path),
            "steps": [step.summary() for step in pipeline.steps.values()],
            "approved": pipeline.approved,
        }
        if not pipeline.approved:
            # Trust on first use: a declaration TEE has not been shown is
            # attacker-authored by default (a cloned repo ships one too).
            payload["blocked"] = pipeline.change
            payload["to_approve"] = (
                f"Read {pipeline.path}, then write its digest {pipeline.digest} "
                f"to {schema.pin_path(root)} - TEE never approves its own inputs."
            )
        return payload

    app.registry.register(
        VirtualTool(
            "pipeline_list",
            "The build/query steps this project declares in .tee/pipeline.toml: "
            "names, kinds (produce|query), argv and params. Says whether the "
            "declaration is approved for this machine, and how to approve it.",
            {"type": "object", "properties": {}},
            pipeline_list,
            tags=["pipeline", "steps", "build", "query", "declared", "project"],
        )
    )
