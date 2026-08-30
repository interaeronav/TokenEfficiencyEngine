"""Savings meter + handoff pack (A37 P6 = A36 G3/G4, research 51 F2/F3).

The meter turns the session ledger (ResponseLog counts every request and
response) into the product's core claim, live: measured tokens vs a
naive-pattern estimate derived from the MEASURED benchmark scenario
ratios. The estimate is labelled as an estimate everywhere it appears -
baseline honesty is the acceptance, not a nicety.

The handoff pack is one <=500-token plain-text brief - project memory,
scene stamps, checkpoints, open jobs - designed to be pasted into ANY
AI, MCP-connected or not.

Both ship as virtual tools plus a compact `savings` block in the recap:
zero always-loaded growth.
"""

from __future__ import annotations

import time
from typing import Any

from tee.kernel import spend
from tee.kernel.budget import estimate_tokens
from tee.kernel.registry import VirtualTool

# Measured scenario ratios (fraction saved), each cited to its dated
# RESULTS.md row. These price the naive-pattern estimate; tools outside
# every lane are counted in the measured totals but never estimated.
MEASURED_RATIOS: dict[str, tuple[float, str]] = {
    "scenes": (0.903, "scenes total, live battery 2026-08-29"),
    "web": (0.953, "web lookup x4, live battery 2026-08-29"),
    "kb": (0.967, "kb paving lookup, live battery 2026-08-29"),
    "extract": (0.931, "extraction ingest-once, live battery 2026-08-29"),
    "assets": (0.940, "asset find-select-place, live battery 2026-08-29"),
    "gateway": (0.954, "gateway filesystem task, 2026-08-29"),
}

_SCENE_TOOLS = {
    "tee_batch",
    "tee_scene_summary",
    "tee_entity_detail",
    "tee_diff",
    "tee_script",
    "tee_checkpoint",
    "tee_rollback",
    "tee_capture",
}

ESTIMATE_NOTE = (
    "naive_estimate is an ESTIMATE: measured tokens scaled by the dated "
    "benchmark scenario ratios in benchmarks/RESULTS.md; tools outside "
    "every measured lane are counted but not estimated"
)


def lane_for(tool: str) -> str | None:
    """Map a ledger row to the measured scenario that prices its naive
    baseline; None = no honest baseline exists for this tool."""
    if tool in _SCENE_TOOLS:
        return "scenes"
    if tool == "tee_web_lookup":
        return "web"
    if tool.startswith("virtual:"):
        name = tool[len("virtual:") :]
        if name.startswith("kb_"):
            return "kb"
        if name.startswith("ex_"):
            return "extract"
        if name.startswith(("as_", "vox_")):
            return "assets"
        if "." in name:  # gateway-prefixed backend tools (fs.read_text_file)
            return "gateway"
    return None


def savings(ledger: dict[str, Any]) -> dict[str, Any]:
    """The meter: measured session totals + the labelled naive estimate.

    Lane tokens come from `virtual:` rows too (they detail tee_call
    traffic) - but the measured totals stay wire-level, so the block
    reads: 'this session really cost X; the naive pattern for the work
    that has a measured ratio would have cost ~Y'."""
    lanes: dict[str, dict[str, Any]] = {}
    for tool, row in ledger["tools"].items():
        lane = lane_for(tool)
        if lane is None:
            continue
        entry = lanes.setdefault(lane, {"tokens": 0, "calls": 0})
        entry["tokens"] += row["tokens_in"] + row["tokens_out"]
        entry["calls"] += row["calls"]
    naive_total = 0
    for lane, entry in lanes.items():
        ratio, source = MEASURED_RATIOS[lane]
        entry["naive_estimate"] = round(entry["tokens"] / (1.0 - ratio))
        entry["ratio_source"] = source
        naive_total += entry["naive_estimate"]
    totals = ledger["totals"]
    measured = totals["tokens_in"] + totals["tokens_out"]
    out: dict[str, Any] = {
        "measured": {"tokens": measured, "calls": totals["calls"]},
        "note": ESTIMATE_NOTE,
    }
    if lanes:
        out["lanes"] = lanes
        out["naive_estimate"] = naive_total
        estimated_tokens = sum(e["tokens"] for e in lanes.values())
        if naive_total > 0:
            out["saved_pct_on_estimated_lanes"] = round(
                100.0 * (1 - estimated_tokens / naive_total), 1
            )
    return out


def savings_block(ledger: dict[str, Any]) -> dict[str, Any] | None:
    """The compact recap form: one line of numbers plus the label."""
    full = savings(ledger)
    if not ledger["totals"]["calls"]:
        return None
    block = {"tokens": full["measured"]["tokens"], "calls": full["measured"]["calls"]}
    if "naive_estimate" in full:
        block["naive_estimate"] = full["naive_estimate"]
        block["saved_pct"] = full.get("saved_pct_on_estimated_lanes")
    block["note"] = "estimate per measured RESULTS.md ratios; report_savings has the table"
    money = spend.block()
    if money is not None:
        block["spend"] = money
    return block


# -- handoff ----------------------------------------------------------------

HANDOFF_BUDGET = 500


def handoff_brief(app) -> dict[str, Any]:
    """One portable plain-text brief; trimmed to the budget from the
    least load-bearing end (notes first, then facts)."""
    from tee import __version__

    stamps = []
    for name, cache in app.caches.items():
        stamp = cache.stamp()
        counts: dict[str, int] = {}
        for entity in cache.entities.values():
            counts[entity.kind] = counts.get(entity.kind, 0) + 1
        kinds = ", ".join(f"{k} x{v}" for k, v in sorted(counts.items())[:6])
        stamps.append(
            f"{name}: epoch {stamp.get('epoch')} rev {stamp.get('revision')}"
            + (f" ({kinds})" if kinds else "")
        )
    memory = app.memory.preamble() if hasattr(app, "memory") else {}
    facts = memory.get("facts") or {}
    notes = memory.get("notes") or []
    checkpoints = app.checkpoints.list()[-3:]
    jobs = [j for j in app.jobs.list() if j["state"] in ("queued", "running")]

    def compose(fact_items: list[tuple[str, str]], note_items: list[str]) -> str:
        lines = [
            "TEE HANDOFF - portable project brief (plain text, paste into any AI)",
            f"generated {time.strftime('%Y-%m-%d %H:%M')} | tee {__version__} | "
            f"project {app.project_root.name}",
            "scene state: " + ("; ".join(stamps) if stamps else "no adapters"),
        ]
        if fact_items:
            lines.append("memory: " + "; ".join(f"{k}={v}" for k, v in fact_items))
        if note_items:
            lines.append("notes: " + " | ".join(note_items))
        if checkpoints:
            lines.append(
                "checkpoints: "
                + ", ".join(f"{c.get('id')} ({c.get('label')})" for c in checkpoints)
            )
        lines.append(
            "open jobs: "
            + (", ".join(f"{j['job']} {j['label']}" for j in jobs) if jobs else "none")
        )
        lines.append(
            "to continue with TEE: connect the MCP server, call tee_recall then "
            "tee_status(recap=true). Without TEE: the facts above ARE the state."
        )
        return "\n".join(lines)

    fact_items = [(k, str(v)[:160]) for k, v in list(facts.items())]
    note_items = [str(n.get("text") if isinstance(n, dict) else n)[:160] for n in notes[-3:]]
    text = compose(fact_items, note_items)
    while estimate_tokens(text) > HANDOFF_BUDGET and (note_items or fact_items):
        if note_items:
            note_items.pop()  # notes go first, facts are more load-bearing
        else:
            fact_items.pop()
        text = compose(fact_items, note_items)
    return {"brief": text, "tokens": estimate_tokens(text), "budget": HANDOFF_BUDGET}


def register_session_tools(app) -> None:
    """report_savings + handoff: kernel-level, adapter-agnostic, virtual."""

    def report_savings(args):
        result = savings(app.response_log.ledger())
        machine = getattr(app, "machine", None)
        if machine is not None:
            # the merged meter (A42 R2): escalation, swap and job-class
            # columns together; scheduler columns reserved in-schema (seam 2)
            result["routing"] = machine.meter_block()
        # A45 P1: what the engines cost and what left the machine. Only
        # present once an engine has actually been called.
        money = spend.block()
        if money is not None:
            result["spend"] = money
        return result

    def report_spend(args):
        return spend.summary()

    def handoff(args):
        return handoff_brief(app)

    for tool in [
        VirtualTool(
            "report_savings",
            "The session token ledger: measured tokens/calls per tool plus a "
            "LABELLED naive-pattern estimate priced by the measured benchmark "
            "scenario ratios (RESULTS.md) - the live form of TEE's "
            "tokens-per-task claim. The recap carries the one-line version.",
            {"type": "object", "properties": {}},
            report_savings,
            tags=["session", "savings", "meter", "tokens", "ledger", "report"],
        ),
        VirtualTool(
            "report_spend",
            "What the engines cost and what LEFT this machine: per engine "
            "calls, tokens sent/returned, reasoning tokens the provider "
            "billed but never showed, bytes on the wire and the endpoint "
            "host - plus a cost ESTIMATE when a rate is declared beside the "
            "profile. A local-only session reads a clean zero.",
            {"type": "object", "properties": {}},
            report_spend,
            tags=["spend", "cost", "money", "egress", "sent", "paid", "billing", "meter"],
        ),
        VirtualTool(
            "handoff",
            "One <=500-token portable project brief - memory, scene stamps, "
            "checkpoints, open jobs - as plain text with a one-line preamble, "
            "designed to be pasted into ANY AI (MCP-connected or not) to "
            "continue this project.",
            {"type": "object", "properties": {}},
            handoff,
            tags=["session", "handoff", "brief", "resume", "portable", "continue"],
        ),
    ]:
        app.registry.register(tool)
