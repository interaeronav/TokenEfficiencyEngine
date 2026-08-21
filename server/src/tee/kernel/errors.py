"""Structured, token-cheap errors.

Every user-visible failure is one short message naming the fix (principle P7).
Tool handlers raise TeeError; the server layer converts it to a compact
payload. Anything else escaping a handler is a bug and is reported as such,
truncated, never as a full traceback.
"""

from __future__ import annotations

from typing import Any


class TeeError(Exception):
    """A failure with a stable code, a one-line message, and an actionable fix."""

    def __init__(self, code: str, message: str, fix: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.fix = fix

    def to_payload(self) -> dict[str, Any]:
        err: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.fix:
            err["fix"] = self.fix
        return {"ok": False, "error": err}


class AdapterUnavailable(TeeError):
    """The requested DCC is not connected. Fails fast instead of hanging."""

    def __init__(self, adapter_id: str, hint: str | None = None):
        super().__init__(
            code="adapter_unavailable",
            message=f"DCC adapter '{adapter_id}' is not connected.",
            fix=hint or "Start the DCC and its bridge, then retry; check with tee_status.",
        )


def internal_error_payload(exc: Exception, limit: int = 300) -> dict[str, Any]:
    """Compact payload for unexpected exceptions (no tracebacks to the model)."""
    text = f"{type(exc).__name__}: {exc}"
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    return {"ok": False, "error": {"code": "internal", "message": text}}
