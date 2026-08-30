"""Response budgeter (principles P1/P7).

Every read tool's payload passes through `enforce_budget` before leaving the
server. Token counts are estimated conservatively (~1 token per 3.5 chars of
compact JSON - matching the wire format, which is also compact JSON); when a
payload exceeds its budget the budgeter trims its largest collection fields
(lists AND dicts) and attaches one truncation notice naming everything that
was dropped plus the narrowing parameter, so the model learns to ask smaller
questions instead of retrying blind. The result is always parseable JSON that
keeps the payload's scalar fields (ok, checkpoint ids, scene stamps).
"""

from __future__ import annotations

import json
import time
from typing import Any

DEFAULT_MAX_TOKENS = 20_000
CHARS_PER_TOKEN = 3.5
_SCALAR_STR_LIMIT = 300
COLUMNAR_MIN_ROWS = 20
COLUMNAR_MIN_SHARED = 0.6


def estimate_tokens(obj: Any) -> int:
    text = (
        obj
        if isinstance(obj, str)
        else json.dumps(obj, separators=(",", ":"), default=str, ensure_ascii=False)
    )
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def columnarize(
    payload: dict[str, Any],
    *,
    min_rows: int = COLUMNAR_MIN_ROWS,
    min_shared: float = COLUMNAR_MIN_SHARED,
) -> dict[str, Any]:
    """Adaptive columnar encoding (Phase 8, A12): rewrite any top-level
    list-of-dicts field with >= min_rows rows sharing >= min_shared of their
    keys from repeated-key objects to {"cols": [...], "rows": [[...], ...]}
    (missing keys become null). Rewritten field names are listed in a
    top-level "columnar" marker so the model can decode. Small or
    heterogeneous lists pass through untouched - measured 42% smaller at
    100 homogeneous rows, ~nothing below the threshold."""
    rewritten: list[str] = []
    out = payload
    for key, value in payload.items():
        if (
            not isinstance(value, list)
            or len(value) < min_rows
            or not all(isinstance(row, dict) for row in value)
        ):
            continue
        key_counts: dict[str, int] = {}
        for row in value:
            for k in row:
                key_counts[k] = key_counts.get(k, 0) + 1
        if not key_counts:
            continue
        cols = sorted(k for k, n in key_counts.items() if n / len(value) >= min_shared)
        if not cols or len(set().union(*value)) > 2 * len(cols):
            continue  # too heterogeneous to pay off
        extras = sorted(set(key_counts) - set(cols))
        rows = []
        for row in value:
            encoded = [row.get(c) for c in cols]
            rest = {k: row[k] for k in extras if k in row}
            if rest:
                encoded.append(rest)
            rows.append(encoded)
        if out is payload:
            out = dict(payload)
        out[key] = {"cols": cols, "rows": rows}
        rewritten.append(key)
    if rewritten:
        out["columnar"] = rewritten
    return out


def enforce_budget(
    payload: dict[str, Any],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    narrow_hint: str = "use limit=/offset= or a filter to narrow the query",
) -> dict[str, Any]:
    """Return `payload` unchanged if within budget; otherwise trim collection
    fields until it fits, with one accurate cumulative truncation notice."""
    if estimate_tokens(payload) <= max_tokens:
        return payload

    trimmed = dict(payload)
    dropped: dict[str, int] = {}

    def notice() -> str:
        parts = ", ".join(f"{count} from '{key}'" for key, count in dropped.items())
        return f"response exceeded {max_tokens} tokens; dropped {parts} - {narrow_hint}"

    for _ in range(64):
        key, size = _largest_collection(trimmed)
        if key is None or size <= 1:
            break
        value = trimmed[key]
        keep = max(1, size // 2)
        if isinstance(value, list):
            trimmed[key] = value[:keep]
        else:  # dict
            kept_keys = list(value)[:keep]
            trimmed[key] = {k: value[k] for k in kept_keys}
        dropped[key] = dropped.get(key, 0) + (size - keep)
        trimmed["truncated"] = notice()
        if estimate_tokens(trimmed) <= max_tokens:
            return trimmed

    # Still over budget: fall back to the scalar skeleton (never unparseable
    # previews - checkpoint ids and scene stamps must survive).
    skeleton: dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            skeleton[key] = (
                value if len(value) <= _SCALAR_STR_LIMIT else value[:_SCALAR_STR_LIMIT] + "…"
            )
        elif isinstance(value, (int, float, bool)) or value is None:
            skeleton[key] = value
        else:
            dropped[key] = dropped.get(key, 0) + _collection_size(value)
    skeleton["truncated"] = notice()
    return skeleton


def _largest_collection(payload: dict[str, Any]) -> tuple[str | None, int]:
    best_key, best_cost = None, 0
    for key, value in payload.items():
        if key == "truncated" or not isinstance(value, (list, dict)):
            continue
        cost = len(json.dumps(value, separators=(",", ":"), default=str, ensure_ascii=False))
        if cost > best_cost and _collection_size(value) > 1:
            best_key, best_cost = key, cost
    if best_key is None:
        return None, 0
    return best_key, _collection_size(payload[best_key])


def _collection_size(value: Any) -> int:
    try:
        return len(value)
    except TypeError:
        return 1


_READ_ONLY_AUDIT_SKIP = frozenset(
    {
        "read-scene",
        "read-state",
        "read-session",
        "read-kb",
        "read-extract",
        "read-assets",
        "read-design",
        "read-uefn",
    }
)


class ResponseLog:
    """Per-tool response-size log (standing rule: measure before optimizing).

    Keeps a bounded in-memory record; `report()` flags any tool whose median
    response exceeds the alert threshold (default 2K tokens).
    """

    def __init__(self, alert_tokens: int = 2_000, keep: int = 500):
        self._alert = alert_tokens
        self._keep = keep
        self._sizes: dict[str, list[int]] = {}
        # the session ledger (A37 P6): request/response token sums per tool
        self._calls: dict[str, int] = {}
        self._tokens_in: dict[str, int] = {}
        self._tokens_out: dict[str, int] = {}
        # A43 L5: the audit trail. This record already fired on every call at
        # the MCP seam, so auditing is one struct widened rather than a new
        # call site - and the trail covers side effects only, because logging
        # every read would bury the entries that matter.
        self.audit: list[dict[str, Any]] = []
        self._audit_keep = 200

    def record(
        self,
        tool: str,
        payload: Any,
        request: Any = None,
        *,
        capability: str | None = None,
        caller: str | None = None,
        taint: tuple[str, ...] = (),
        decision: str = "allowed",
    ) -> int:
        tokens = estimate_tokens(payload)
        if capability is not None and capability not in _READ_ONLY_AUDIT_SKIP:
            entry: dict[str, Any] = {
                "at": time.strftime("%H:%M:%S"),
                "tool": tool,
                "capability": capability,
                "caller": caller or "content-derived",
                "decision": decision,
            }
            if taint:
                entry["taint"] = list(taint)[:3]
            self.audit.append(entry)
            if len(self.audit) > self._audit_keep:
                del self.audit[: len(self.audit) - self._audit_keep]
        sizes = self._sizes.setdefault(tool, [])
        sizes.append(tokens)
        if len(sizes) > self._keep:
            del sizes[: len(sizes) - self._keep]
        self._calls[tool] = self._calls.get(tool, 0) + 1
        self._tokens_out[tool] = self._tokens_out.get(tool, 0) + tokens
        if request is not None:
            self._tokens_in[tool] = self._tokens_in.get(tool, 0) + estimate_tokens(request)
        return tokens

    def ledger(self) -> dict[str, Any]:
        """The session ledger. `virtual:<name>` rows break tee_call traffic
        down per virtual tool; their tokens are ALREADY inside tee_call's
        own row, so totals count only wire-level rows (no double count)."""
        tools: dict[str, dict[str, int]] = {}
        totals = {"calls": 0, "tokens_in": 0, "tokens_out": 0}
        for tool in sorted(self._calls):
            row = {
                "calls": self._calls[tool],
                "tokens_in": self._tokens_in.get(tool, 0),
                "tokens_out": self._tokens_out.get(tool, 0),
            }
            tools[tool] = row
            if not tool.startswith("virtual:"):
                totals["calls"] += row["calls"]
                totals["tokens_in"] += row["tokens_in"]
                totals["tokens_out"] += row["tokens_out"]
        return {"tools": tools, "totals": totals}

    def report(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for tool, sizes in sorted(self._sizes.items()):
            ordered = sorted(sizes)
            median = ordered[len(ordered) // 2]
            entry: dict[str, Any] = {
                "calls": len(sizes),
                "median_tokens": median,
                "max_tokens": ordered[-1],
            }
            if median > self._alert:
                entry["alert"] = f"median exceeds {self._alert} tokens - shrink this response"
            out[tool] = entry
        return out
