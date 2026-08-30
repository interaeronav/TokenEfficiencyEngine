"""tee_trust: the visibility surface for the trust kernel (A43 L1/L6/L7).

Research 61's rule: a capability model nobody can inspect is a capability
model nobody can grant, and an ungrantable model gets disabled the first
time it blocks real work. So: what may this project do, which file said
so, what was refused and why, what is carrying untrusted content, and -
for the enforcement flip - whether the evidence supports turning the
quality band on.

The flip itself is deliberately NOT a tool action. TEE never writes the
owner's policy: `tee_trust {action:"rollout"}` shows the evidence and the
exact line to add, and the owner writes it. A model cannot flip a
safety switch by calling a tool, which is the point.
"""

from __future__ import annotations

from typing import Any

from tee.kernel import trust, trustctx
from tee.kernel.registry import VirtualTool


def register_trust_tools(app) -> None:
    def tee_trust(args: dict[str, Any]) -> dict[str, Any]:
        grants = app.registry.grants
        action = str(args.get("action") or "status")
        tier = (
            "power"
            if grants.granted & trust.HIGH_RISK
            else "build"
            if "run-declared-step" in grants.granted
            else "read+baseline"
        )
        if action == "rollout":
            return _rollout(app, grants)
        payload: dict[str, Any] = {
            "project": str(app.project_root),
            "config": grants.source,
            "tier": tier,
            "granted": sorted(grants.granted) or ["(none beyond baseline)"],
            "baseline": sorted(trust.BASELINE - trust.READ_TIER),
            "high_risk_enforced_always": sorted(trust.HIGH_RISK),
            "quality_band": "enforcing" if grants.enforce_quality_band else "shadow (measuring)",
        }
        taint = trustctx.taint()
        if taint:
            payload["this_task_carries"] = list(taint)[:5]
        denials = app.registry.trust_denials[-5:]
        if denials:
            payload["recent_shadow_denials"] = denials
        audit = [e for e in app.response_log.audit[-5:]]
        if audit:
            payload["recent_side_effects"] = audit
        return payload

    def _rollout(app, grants) -> dict[str, Any]:
        """L7: the evidence for flipping the quality band on - never a single
        scalar a caller could steer (research 64 FP-4)."""
        denials = app.registry.trust_denials
        classes_seen = {e.get("capability") for e in app.response_log.audit}
        return {
            "flip": "[trust] enforce = true",
            "where": grants.source,
            "state": "enforcing" if grants.enforce_quality_band else "shadow (measuring)",
            "evidence": {
                "shadow_denials_recorded": len(denials),
                "capability_classes_exercised": sorted(c for c in classes_seen if c),
                "high_risk_already_enforced": sorted(trust.HIGH_RISK),
            },
            "note": "TEE does not write policy. Read the shadow denials above, "
            "then add the line yourself - a model cannot flip a safety switch "
            "by calling a tool.",
        }

    app.registry.register(
        VirtualTool(
            "tee_trust",
            "What this project may do and why: the capability tier, the active "
            "grants AND the config file that granted them, what was refused "
            "recently (with the reason), what untrusted content this task is "
            "carrying, and the side-effect audit tail. action='rollout' shows "
            "the evidence for enabling the quality-denial band.",
            {
                "type": "object",
                "properties": {"action": {"type": "string"}},
            },
            tee_trust,
            tags=["trust", "capability", "grants", "permission", "audit", "taint", "security"],
        )
    )
