"""Response budgeter (principles P1/P7).

Every read tool's payload passes through `enforce_budget` before leaving the
server. Token counts are estimated conservatively (~1 token per 3.5 chars of
JSON); when a payload exceeds its budget the budgeter trims list fields and
attaches a truncation notice that names the narrowing parameter, so the model
learns to ask smaller questions instead of retrying blind.
"""

from __future__ import annotations

import json
from typing import Any

DEFAULT_MAX_TOKENS = 20_000
CHARS_PER_TOKEN = 3.5


def estimate_tokens(obj: Any) -> int:
    text = obj if isinstance(obj, str) else json.dumps(obj, separators=(",", ":"), default=str)
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def enforce_budget(
    payload: dict[str, Any],
    *,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    narrow_hint: str = "use limit=/offset= or a filter to narrow the query",
) -> dict[str, Any]:
    """Return `payload` unchanged if within budget; otherwise trim its largest
    list field until it fits and attach a `truncated` notice."""
    if estimate_tokens(payload) <= max_tokens:
        return payload
    trimmed = dict(payload)
    # Repeatedly halve the largest list field until within budget.
    for _ in range(32):
        largest_key = None
        largest_len = 1
        for key, value in trimmed.items():
            if isinstance(value, list) and len(value) > largest_len:
                largest_key, largest_len = key, len(value)
        if largest_key is None:
            break
        kept = trimmed[largest_key][: max(1, largest_len // 2)]
        dropped = largest_len - len(kept)
        trimmed[largest_key] = kept
        trimmed["truncated"] = (
            f"response exceeded {max_tokens} tokens; dropped {dropped} items "
            f"from '{largest_key}' - {narrow_hint}"
        )
        if estimate_tokens(trimmed) <= max_tokens:
            return trimmed
    # No list to trim (or still too large): hard-truncate the JSON text.
    text = json.dumps(payload, separators=(",", ":"), default=str)
    keep = int(max_tokens * CHARS_PER_TOKEN * 0.9)
    return {
        "truncated": (
            f"response exceeded {max_tokens} tokens and had no trimmable list; {narrow_hint}"
        ),
        "preview": text[:keep] + "…",
    }


class ResponseLog:
    """Per-tool response-size log (standing rule: measure before optimizing).

    Keeps a bounded in-memory record; `report()` flags any tool whose median
    response exceeds the alert threshold (default 2K tokens).
    """

    def __init__(self, alert_tokens: int = 2_000, keep: int = 500):
        self._alert = alert_tokens
        self._keep = keep
        self._sizes: dict[str, list[int]] = {}

    def record(self, tool: str, payload: Any) -> int:
        tokens = estimate_tokens(payload)
        sizes = self._sizes.setdefault(tool, [])
        sizes.append(tokens)
        if len(sizes) > self._keep:
            del sizes[: len(sizes) - self._keep]
        return tokens

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
