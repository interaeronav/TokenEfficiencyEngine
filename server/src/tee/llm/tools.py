"""Virtual tools over the chore layer (A34 M2): llm_triage, llm_explain.

Long-tail by design - the chores add zero always-loaded surface. Both
tools degrade to a structured start-the-stack refusal when no endpoint
answers and refine='local' is asked for; with the default 'auto' they
answer honestly that the chore is unavailable and the evidence stands.
"""

from __future__ import annotations

from pathlib import Path

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.llm import chores


def register_llm_tools(app, project_root: Path | str) -> None:
    cfg = dict(getattr(app.config, "llm", {}) or {})

    def llm_triage(args):
        result = chores.triage(
            str(args.get("failure", "")),
            str(args.get("context", "")),
            refine=str(args.get("refine", "auto")),
            cfg=cfg,
        )
        if result is None:
            raise TeeError(
                "llm_unavailable",
                "No local model is running; the failure text stands as-is.",
                fix="Start the local stack (see [llm] in .tee/config.toml) or "
                "reason from the traceback directly.",
            )
        return result

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
            "llm_triage",
            "One-line diagnosis + exact fix for a failure/traceback, from the "
            "local code model at zero client reasoning cost. Evidence-only: "
            "answers confidence='needs_verification' when the fix depends on "
            "an API fact not in the evidence (the A30 boundary). Server-side, "
            "provenance-stamped.",
            {
                "type": "object",
                "properties": {
                    "failure": {"type": "string"},
                    "context": {"type": "string"},
                    "refine": {"type": "string"},
                },
                "required": ["failure"],
            },
            llm_triage,
            tags=["llm", "triage", "traceback", "debug", "diagnose", "error", "fix"],
            examples=[{"failure": "Traceback ... AttributeError: 'NoneType' ..."}],
        ),
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
