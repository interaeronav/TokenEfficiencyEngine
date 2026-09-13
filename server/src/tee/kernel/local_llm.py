"""Local code-model client: a chore prompt in, a short answer out (A34 M1).

The sibling of `local_vlm.py`, same contract: stdlib-only OpenAI
chat/completions against any local endpoint (`TEE_LOCAL_LLM_URL`, default
the machine's LiteLLM shim; `TEE_LOCAL_LLM_MODEL` names the served model -
the reference setup is Qwen2.5-Coder-14B-Instruct-4bit per research 50
§M0). Thinking is PER-PROFILE (W0): chores default off for latency, the
27B agent profile turns it on, and reasoning is captured out of whichever
field the backend uses rather than discarded. temperature 0, and
`complete_json` guarantees parsed JSON or one loud error.

Backends disagree about `response_format` and the disagreement is not
cosmetic: the MLX server accepts `json_object` and silently ignores it,
while vLLM refuses it outright (HTTP 400, "requires the optional
llguidance dependency") rather than return unconstrained output. So the
field is negotiated per endpoint, not sent unconditionally - measured
2026-09-13 on :8082 and :8087.

The token story: chores run server-side at zero client cost; the client
only ever sees the chore's budgeted, provenance-stamped result. The A30
boundary rides above this seam: chore prompts must confine the model to
evidence in-context - API facts from weights stay banned.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from tee.kernel.errors import TeeError

DEFAULT_URL = os.environ.get("TEE_LOCAL_LLM_URL", "http://127.0.0.1:4000/v1")
DEFAULT_MODEL = os.environ.get("TEE_LOCAL_LLM_MODEL", "tee-coder")
# Optional LoRA adapter dir, passed per-request ("adapters" field). Needed
# because mlx_lm.server resolves its --adapter-path map against the
# already-resolved model path (server.py ~line 389, read 2026-08-28), so
# the startup flag alone never applies; other servers ignore the field.
DEFAULT_ADAPTERS = os.environ.get("TEE_LOCAL_LLM_ADAPTERS") or None

_UNREACHABLE_FIX = (
    "Start the local model stack (`mlx_lm.server --model "
    "mlx-community/Qwen2.5-Coder-14B-Instruct-4bit --port 8080` or any "
    "OpenAI-compatible endpoint) and/or set TEE_LOCAL_LLM_URL / "
    "TEE_LOCAL_LLM_MODEL. Every chore degrades to its deterministic "
    "path meanwhile."
)

_THINK_BLOCK = re.compile(r"<think>(.*?)</think>\s*", re.DOTALL)
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)

# Backends name the same thing differently: mlx_lm.server returns
# "reasoning", vLLM returns "reasoning_content". Read either; a name is
# not a capability (two probes read as false negatives on this alone).
_REASONING_FIELDS = ("reasoning", "reasoning_content")

# (url, model) pairs measured to REFUSE response_format. Populated by the
# 400 handler in complete_json so the cost is paid once per process, not
# per chore. A declaration in config still wins - this is the fallback for
# an endpoint nobody declared.
_NO_JSON_MODE: set[tuple[str, str]] = set()
_JSON_MODE_REFUSAL = "response_format"


def json_mode_unsupported(url: str, model: str) -> bool:
    """True when this endpoint has been measured to refuse response_format."""
    return (url, model) in _NO_JSON_MODE


def _reasoning_of(message: dict) -> str:
    for field in _REASONING_FIELDS:
        value = message.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def available(
    url: str = DEFAULT_URL, timeout: float = 2.0, model: str | None = DEFAULT_MODEL
) -> bool:
    """True when the endpoint answers AND serves the model we would call.

    An endpoint answering is not the same fact as a model being served: a
    proxy fronting other model groups replies to /models happily and then
    400s the chore. Asking about the model turns a confusing runtime error
    into the honest 'no local model' path. The model may still be COLD -
    listed but not loaded - which costs only latency (the local_vlm
    precedent), so a listing is enough.
    """
    try:
        with urllib.request.urlopen(f"{url}/models", timeout=timeout) as response:
            if not model:
                return True
            listed = json.loads(response.read().decode("utf-8") or "{}")
    except (urllib.error.URLError, OSError, ValueError):
        return False
    rows = listed.get("data")
    if not isinstance(rows, list) or not rows:
        return True  # an endpoint that will not enumerate gets the benefit
    return any(isinstance(row, dict) and row.get("id") == model for row in rows)


def complete(
    prompt: str,
    *,
    system: str | None = None,
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    temperature: float = 0.0,
    timeout: float = 120.0,
    response_format: dict | None = None,
    adapters: str | None = DEFAULT_ADAPTERS,
    thinking: bool = False,
    on_usage: Callable[[dict, int, float], None] | None = None,
    on_reasoning: Callable[[str], None] | None = None,
) -> str:
    """One chore completion: deterministic, budgeted, thinking per-profile.

    `on_usage(payload, bytes_sent, seconds)` is called after a successful
    reply so the caller can meter it (A45 P1). The client stays ignorant of
    money: it reports what the provider said and what went on the wire.

    `on_reasoning(text)` receives the model's deliberation when the backend
    returns any. It is deliberately a side channel: reasoning is recorded
    for audit and training, and NEVER returned to the client - that is what
    makes thinking free in the metric TEE is judged by."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        # Per-profile (W0). Servers that don't know the flag are covered
        # by the inline-<think> capture below.
        "chat_template_kwargs": {"enable_thinking": bool(thinking)},
    }
    if response_format:
        body["response_format"] = response_format
    if adapters:
        body["adapters"] = adapters
    encoded = json.dumps(body).encode()
    request = urllib.request.Request(
        f"{url}/chat/completions",
        data=encoded,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:200].decode(errors="replace")
        raise TeeError(
            "llm_failed",
            f"The local model rejected the request ({exc.code}): {detail}",
            fix="Check the endpoint log; chores fall back to their deterministic paths.",
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise TeeError(
            "llm_unreachable", f"No local model at {url} ({exc}).", fix=_UNREACHABLE_FIX
        ) from exc
    if on_usage is not None:
        # metering must never break the chore it is measuring
        with contextlib.suppress(Exception):
            on_usage(payload, len(encoded), time.monotonic() - started)
    try:
        message = payload["choices"][0]["message"]
        text = message.get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise TeeError(
            "llm_bad_response",
            "The local model returned no text content.",
            fix="Check the endpoint log (a wrong --model name answers empty on some servers).",
        ) from exc
    reasoning = _reasoning_of(message)
    inline = _THINK_BLOCK.search(text)
    if inline:  # a backend that leaves the block in content, not a field
        reasoning = reasoning or inline.group(1).strip()
        text = _THINK_BLOCK.sub("", text)
    text = text.strip()
    if reasoning and on_reasoning is not None:
        with contextlib.suppress(Exception):
            on_reasoning(reasoning)
    if not text and reasoning:
        # Measured 2026-09-13: a thinking model can spend its entire budget
        # reasoning and answer nothing (25k chars, finish=length, twice).
        # Empty-content-with-usage is the A76 trap; name it instead of
        # returning "" and letting a validator call it a bad shape.
        raise TeeError(
            "llm_no_answer",
            f"The model reasoned for {len(reasoning)} characters and produced no answer.",
            fix="Raise max_tokens for this chore, or turn thinking off for this profile.",
        )
    return text


def complete_json(
    prompt: str,
    *,
    system: str | None = None,
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    timeout: float = 120.0,
    adapters: str | None = DEFAULT_ADAPTERS,
    json_mode: str = "auto",
    thinking: bool = False,
    on_usage: Callable[[dict, int, float], None] | None = None,
    on_reasoning: Callable[[str], None] | None = None,
) -> dict:
    """A completion that must parse as a JSON object - retried once with a
    corrective nudge, then failed loud. Schema validation stays with the
    caller (each chore owns its shape).

    `json_mode` is 'on' (always send response_format), 'off' (never), or
    'auto' (send until this endpoint is measured to refuse it). Auto exists
    because the two local backends disagree and neither is wrong: MLX
    accepts the field and ignores it, vLLM refuses rather than pretend. A
    declared profile setting outranks discovery."""
    if json_mode not in ("auto", "on", "off"):
        raise TeeError(
            "llm_bad_arg",
            f"json_mode={json_mode!r} is not a mode.",
            fix="Use auto, on, or off.",
        )
    send_json = json_mode == "on" or (
        json_mode == "auto" and not json_mode_unsupported(url, model)
    )

    def _kwargs(response_format: dict | None) -> dict:
        return dict(
            system=system,
            url=url,
            model=model,
            max_tokens=max_tokens,
            timeout=timeout,
            response_format=response_format,
            adapters=adapters,
            thinking=thinking,
            on_usage=on_usage,
            on_reasoning=on_reasoning,
        )

    kwargs = _kwargs({"type": "json_object"} if send_json else None)
    try:
        text = complete(prompt, **kwargs)
    except TeeError as exc:
        refused = (
            send_json
            and json_mode == "auto"
            and exc.code == "llm_failed"
            and _JSON_MODE_REFUSAL in exc.message
        )
        if not refused:
            raise
        # Measured, not assumed: this endpoint answered 400 naming the
        # field. Remember it so the next chore pays no round trip.
        _NO_JSON_MODE.add((url, model))
        kwargs = _kwargs(None)
        text = complete(prompt, **kwargs)
    parsed = _parse_json_object(text)
    if parsed is None:
        text = complete(
            f"{prompt}\n\nYour previous reply was not a JSON object. "
            "Reply with ONLY the JSON object.",
            **kwargs,
        )
        parsed = _parse_json_object(text)
    if parsed is None:
        raise TeeError(
            "llm_bad_json",
            "The local model answered twice without a parseable JSON object.",
            fix="The deterministic path still works; consider a stronger "
            "TEE_LOCAL_LLM_MODEL for JSON chores.",
        )
    return parsed


def _parse_json_object(text: str) -> dict | None:
    candidates = [text]
    fence = _JSON_FENCE.search(text)
    if fence:
        candidates.insert(0, fence.group(1))
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None
