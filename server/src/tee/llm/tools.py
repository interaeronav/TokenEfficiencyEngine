"""Virtual tools over the chore layer (A34 M2): llm_triage, llm_explain.

Long-tail by design - the chores add zero always-loaded surface. Tools
degrade to a structured start-the-stack refusal when no endpoint
answers; with the default 'auto' they answer honestly that the chore is
unavailable and the evidence stands.

llm_triage was blocked at rung 0 (kwarg-drift traps answered with
intent-destroying fixes across three bare models) and returned at rung
1: the tee-triage-a2 adapter passes the FULL trap suite plus the
latency, quality, and held-out gates (PROGRESS 2026-08-28). Serving
with the adapter: docs/setup-local-llm.md (TEE_LOCAL_LLM_ADAPTERS /
[llm] adapters).
"""

from __future__ import annotations

from pathlib import Path

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.llm import chores


def register_llm_tools(app, project_root: Path | str) -> None:
    cfg = getattr(app, "llm_cfg", None) or dict(getattr(app.config, "llm", {}) or {})

    def llm_switch(args):
        from tee.llm import profiles

        profile = str(args.get("profile", "")).strip().lower()
        if profile in ("auto", "roam"):
            # The owner lifts the pin: the R1 router may roam the ladder.
            state = profiles.load_state(cfg)
            state.pop("pinned", None)
            profiles.save_state(cfg, state)
            return {"ok": True, "report": "pin cleared - the router may roam the ladder"}
        target = profiles.profiles(cfg).get(profile) or {}
        if target.get("paid"):
            from tee.kernel import trust, trustctx

            decision = trust.check(
                "call-paid-engine",
                caller=trustctx.caller(),
                grants=app.registry.grants,
                taint=trustctx.taint(),
                consent=True,  # an explicit TEE/Q switch IS the owner asking
            )
            decision.raise_if_denied(f"llm_switch to '{profile}'")
        result = profiles.switch(cfg, profile, jobs=app.jobs)
        if target.get("paid") and result.get("ok"):
            result["egress"] = (
                "PAID, off-machine: chore inputs sent while this profile is "
                "active leave this machine and bill per token"
            )
        if result.get("ok"):
            # An explicit TEE/Q choice is owner intent: roaming suspends
            # until TEE/AUTO (the A39 owner-ceiling law).
            state = profiles.load_state(cfg)
            state["pinned"] = True
            profiles.save_state(cfg, state)
            from tee.kernel import machine, shadow

            engine = next(
                (n for n, s in machine.ENGINES.items() if s.get("profile") == profile), None
            )
            shadow.record(
                shadow.TaskDescriptor(
                    id=f"swap:{profile}", kind="swap", qos="maintenance", engine=engine
                ),
                {"outcome": "switched", "pinned": True},
            )
            machine_ledger = getattr(app, "machine", None)
            if machine_ledger is not None:
                machine_ledger.record_swap()  # explicit owner swap, the meter's column
        return result

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
            "llm_switch",
            "Switch the chore engine between local-model profiles. THE CHAT "
            "PHRASE: the user typing TEE/Q14B or TEE/Q27B is a switch "
            "request - call this with profile='q14b'/'q27b'. q14b (14B + "
            "tee-triage-a2) is the default; q27b passes the traps bare at "
            "~4-6x chore latency (3.11-10.12 s measured). The choice "
            "persists across restarts; with [llm] managed = true TEE also "
            "stops/starts the servers each profile owns (single occupancy, "
            "verified; a cold load returns a tee_job token and chores "
            "answer their deterministic paths meanwhile). An explicit "
            "choice PINS the engine (router roaming suspends); "
            "profile='auto' (TEE/AUTO) lifts the pin.",
            {
                "type": "object",
                "properties": {"profile": {"type": "string"}},
                "required": ["profile"],
            },
            llm_switch,
            tags=["llm", "switch", "profile", "model", "chore", "engine", "q14b", "q27b"],
            examples=[{"profile": "q27b"}],
        ),
        VirtualTool(
            "llm_triage",
            "One-line diagnosis + exact fix for a failure/traceback, from the "
            "local code model at zero client reasoning cost. Evidence-only: "
            "answers confidence='needs_verification' when the fix depends on "
            "an API fact not in the evidence (the A30 boundary, adapter-"
            "enforced). Server-side, provenance-stamped.",
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
            tags=["llm", "debug", "traceback", "triage", "error", "fix"],
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
