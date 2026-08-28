"""Local code-model client: a chore prompt in, a short answer out (A34 M1).

The sibling of `local_vlm.py`, same contract: stdlib-only OpenAI
chat/completions against any local endpoint (`TEE_LOCAL_LLM_URL`, default
the machine's LiteLLM shim; `TEE_LOCAL_LLM_MODEL` names the served model -
the reference setup is Qwen2.5-Coder-14B-Instruct-4bit per research 50
§M0). Thinking is disabled for chores (latency; the request says so and
any leaked <think> block is stripped defensively), temperature 0, and
`complete_json` guarantees parsed JSON or one loud error.

The token story: chores run server-side at zero client cost; the client
only ever sees the chore's budgeted, provenance-stamped result. The A30
boundary rides above this seam: chore prompts must confine the model to
evidence in-context - API facts from weights stay banned.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

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

_THINK_BLOCK = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def available(url: str = DEFAULT_URL, timeout: float = 2.0) -> bool:
    """True when the endpoint answers; the model itself may still be cold
    (lazy-start costs only latency, the local_vlm precedent)."""
    try:
        urllib.request.urlopen(f"{url}/models", timeout=timeout)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


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
) -> str:
    """One chore completion: deterministic, thinking-off, budgeted."""
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        # Chores never think out loud: honored by servers that know the
        # flag, enforced by the strip below for ones that don't.
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if response_format:
        body["response_format"] = response_format
    if adapters:
        body["adapters"] = adapters
    request = urllib.request.Request(
        f"{url}/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
    )
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
    try:
        text = payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise TeeError(
            "llm_bad_response",
            "The local model returned no text content.",
            fix="Check the endpoint log (a wrong --model name answers empty on some servers).",
        ) from exc
    return _THINK_BLOCK.sub("", text).strip()


def complete_json(
    prompt: str,
    *,
    system: str | None = None,
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    timeout: float = 120.0,
    adapters: str | None = DEFAULT_ADAPTERS,
) -> dict:
    """A completion that must parse as a JSON object - retried once with a
    corrective nudge, then failed loud. Schema validation stays with the
    caller (each chore owns its shape)."""
    kwargs = dict(
        system=system,
        url=url,
        model=model,
        max_tokens=max_tokens,
        timeout=timeout,
        response_format={"type": "json_object"},
        adapters=adapters,
    )
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
