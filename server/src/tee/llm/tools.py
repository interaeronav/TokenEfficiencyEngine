"""Virtual tools over the chore layer (A34 M2): llm_explain.

Long-tail by design - the chores add zero always-loaded surface. Tools
degrade to a structured start-the-stack refusal when no endpoint
answers; with the default 'auto' they answer honestly that the chore is
unavailable and the evidence stands.

llm_triage is deliberately NOT registered: the M2 trap suite blocked the
traceback-triage chore at rung 0 (kwarg-drift traps answered with
intent-destroying fixes labeled grounded, across three models -
PROGRESS 2026-08-28). The chore function and its trap suite stay in the
tree as the rung-1 training target; registration returns only when the
full trap suite passes.
"""

from __future__ import annotations

from pathlib import Path

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.llm import chores


def register_llm_tools(app, project_root: Path | str) -> None:
    cfg = dict(getattr(app.config, "llm", {}) or {})

    def llm_explain(args):
        result = chores.explain_lint(
            str(args.get("finding", "")),
            refine=str(args.get("refine", "auto")),
            cfg=cfg,
        )
        if result is None:
            raise TeeError(
                "llm_unavailable",
                "No local model is running; the finding stands as-is.",
                fix="Start the local stack (see [llm] in .tee/config.toml); "
                "the checker's finding is already actionable.",
            )
        return result

    for tool in [
        VirtualTool(
            "llm_explain",
            "The shortest actionable phrasing of a deterministic checker "
            "finding (lint, plaus_check, validators). The checker stays the "
            "judge - this never overrules, only translates.",
            {
                "type": "object",
                "properties": {
                    "finding": {"type": "string"},
                    "refine": {"type": "string"},
                },
                "required": ["finding"],
            },
            llm_explain,
            tags=["llm", "lint", "explain", "finding", "checker"],
        ),
    ]:
        app.registry.register(tool)
