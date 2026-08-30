"""A45 P1 — the money meter: what a paid engine cost, and what left the machine.

Closes the two halves the backlog had open:

  SI-B16  `paid = true` was declarative; the meter had no spend column, so
          off-machine cost was invisible next to the free local rows.
  SI-B18  the meter accounted for TOKENS but said nothing about EGRESS -
          nothing told the owner how much content went off-machine, to
          which endpoint, on whose behalf.

Two kinds of number live here and they are never blended:

* **Measured** — calls, tokens sent, tokens returned, reasoning tokens the
  provider billed but never showed the caller, bytes on the wire, endpoint
  host, wall time. These are read off the provider's own `usage` block and
  the request we actually serialised. They are exact.
* **Estimated** — money. TEE ships **no price table**. A rate that is
  wrong is worse than a rate that is absent, and published prices move and
  differ by region and contract. The owner declares the rate next to the
  profile; until then the meter reports tokens honestly and says, in the
  payload, which line would turn on the cost column.

The motivating measurement, from this machine: a four-word prompt to the
hosted engine billed 101 tokens - 68 of prompt overhead the shim wrapped
around it and 29 reasoning tokens the caller never sees. Roughly 14x its
visible content, and until now invisible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


@dataclass
class PaidCall:
    """One call to an engine, recorded whether or not it was billed."""

    profile: str
    endpoint: str  # host[:port] only - never the path, never a key
    model: str
    paid: bool
    tokens_in: int = 0
    tokens_out: int = 0
    reasoning_tokens: int = 0  # billed, never shown to the caller
    cached_tokens: int = 0
    bytes_sent: int = 0
    seconds: float = 0.0
    # rate declared by the owner beside the profile; None = no cost column
    price_in_per_mtok: float | None = None
    price_out_per_mtok: float | None = None
    currency: str | None = None
    price_source: str | None = None

    @property
    def cost(self) -> float | None:
        if self.price_in_per_mtok is None or self.price_out_per_mtok is None:
            return None
        return (
            self.tokens_in / 1_000_000.0 * self.price_in_per_mtok
            + self.tokens_out / 1_000_000.0 * self.price_out_per_mtok
        )


LEDGER: list[PaidCall] = []
_CAP = 2000  # bounded like every other ledger here


def endpoint_of(url: str) -> str:
    """Host and port only. A URL can carry a key in its query string and a
    ledger is a thing people paste into chats."""
    try:
        p = urlparse(url)
        return p.netloc or (p.path.split("/")[0] if p.path else "?")
    except Exception:
        return "?"


def record(call: PaidCall) -> None:
    LEDGER.append(call)
    if len(LEDGER) > _CAP:
        del LEDGER[: len(LEDGER) - _CAP]


def reset() -> None:
    LEDGER.clear()


def _blank() -> dict[str, Any]:
    return {
        "calls": 0,
        "tokens_sent": 0,
        "tokens_returned": 0,
        "reasoning_tokens": 0,
        "cached_tokens": 0,
        "bytes_sent": 0,
        "seconds": 0.0,
    }


def summary() -> dict[str, Any]:
    """The full table: per engine, plus the egress line and the cost column
    when - and only when - the owner has declared a rate."""
    paid = [c for c in LEDGER if c.paid]
    engines: dict[str, dict[str, Any]] = {}
    for c in LEDGER:
        row = engines.setdefault(
            c.profile,
            {**_blank(), "paid": c.paid, "endpoint": c.endpoint, "model": c.model},
        )
        row["calls"] += 1
        row["tokens_sent"] += c.tokens_in
        row["tokens_returned"] += c.tokens_out
        row["reasoning_tokens"] += c.reasoning_tokens
        row["cached_tokens"] += c.cached_tokens
        row["bytes_sent"] += c.bytes_sent
        row["seconds"] = round(row["seconds"] + c.seconds, 2)

    priced: dict[str, dict[str, Any]] = {}
    unpriced: list[str] = []
    for c in paid:
        cost = c.cost
        if cost is None:
            if c.profile not in unpriced:
                unpriced.append(c.profile)
            continue
        cur = c.currency or "?"
        slot = priced.setdefault(cur, {"estimated_cost": 0.0, "profiles": {}, "sources": []})
        slot["estimated_cost"] = round(slot["estimated_cost"] + cost, 6)
        slot["profiles"][c.profile] = round(slot["profiles"].get(c.profile, 0.0) + cost, 6)
        if c.price_source and c.price_source not in slot["sources"]:
            slot["sources"].append(c.price_source)

    out: dict[str, Any] = {
        "engines": engines,
        # SI-B18: the reassurance a local-only session deserves is a zero it
        # can see, not the absence of a column.
        "sent": {
            "off_machine_calls": len(paid),
            "tokens": sum(c.tokens_in for c in paid),
            "bytes": sum(c.bytes_sent for c in paid),
            "endpoints": sorted({c.endpoint for c in paid}),
        },
    }
    if priced:
        out["estimated_cost"] = priced
        out["cost_note"] = (
            "ESTIMATE from the rate declared beside the profile in .tee/config.toml, "
            "applied to the provider's own reported usage. Not a bill."
        )
    if unpriced:
        out["cost_unavailable_for"] = unpriced
        out["cost_fix"] = (
            "TEE ships no price table on purpose - a stale rate is worse than none. "
            "Add price_in_per_mtok / price_out_per_mtok / currency (and optionally "
            "price_source) under [llm.profiles.<name>] to turn the cost column on."
        )
    hidden = sum(c.reasoning_tokens for c in paid)
    if hidden:
        out["billed_but_unseen_tokens"] = hidden
        out["billed_but_unseen_note"] = (
            "reasoning tokens the provider billed and the caller never saw"
        )
    return out


def block() -> dict[str, Any] | None:
    """The compact recap form. None when nothing has left the machine AND
    no engine was called - silence beats a row of zeros in a recap."""
    if not LEDGER:
        return None
    paid = [c for c in LEDGER if c.paid]
    b: dict[str, Any] = {
        "engine_calls": len(LEDGER),
        "off_machine_calls": len(paid),
        "tokens_sent": sum(c.tokens_in for c in paid),
    }
    if paid:
        b["endpoints"] = sorted({c.endpoint for c in paid})
    costs = [c.cost for c in paid if c.cost is not None]
    if costs:
        cur = next((c.currency for c in paid if c.cost is not None), "?")
        b["estimated_cost"] = f"{round(sum(costs), 4)} {cur} (estimate)"
    elif paid:
        b["estimated_cost"] = "no rate declared - see report_spend"
    return b


def usage_from_payload(payload: dict[str, Any]) -> dict[str, int]:
    """Read an OpenAI-shaped `usage` block, tolerating the nested detail
    dicts providers add (reasoning_tokens, cached_tokens)."""
    u = dict((payload or {}).get("usage") or {})
    out = {
        "tokens_in": int(u.get("prompt_tokens") or 0),
        "tokens_out": int(u.get("completion_tokens") or 0),
        "reasoning_tokens": 0,
        "cached_tokens": 0,
    }
    detail = dict(u.get("completion_tokens_details") or {})
    out["reasoning_tokens"] = int(detail.get("reasoning_tokens") or 0)
    pdetail = dict(u.get("prompt_tokens_details") or {})
    out["cached_tokens"] = int(pdetail.get("cached_tokens") or 0)
    return out
