"""Local vision-model client: pixels in, a short text answer out (P3).

Talks OpenAI chat/completions to the machine's local model shim (LiteLLM on
127.0.0.1:4000 fronting a Qwen3-VL server). The shim lazy-starts the vision
server on the first image request, so the first call of a session can take a
minute; later calls are seconds. Stdlib-only on purpose - the core package
must not grow a dependency for one HTTP POST.

The token story: a viewport question answered here costs the host model only
the answer text (tens of tokens). The same question via a returned capture
costs the full budgeted image every time it is (re)read.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request

from tee.kernel.errors import TeeError

DEFAULT_URL = os.environ.get("TEE_LOCAL_VLM_URL", "http://127.0.0.1:4000/v1")
DEFAULT_MODEL = os.environ.get("TEE_LOCAL_VLM_MODEL", "claude-qwen-vl")

_UNREACHABLE_FIX = (
    "Start the local model stack (any claude-qwen session, or "
    "`litellm --config ~/.claude/qwen-local/litellm.yaml`), or set "
    "TEE_LOCAL_VLM_URL. Text-first tools (ue_scene_checks) need no VLM."
)


def available(url: str = DEFAULT_URL, timeout: float = 2.0) -> bool:
    """True when the shim answers; the vision server itself may still be
    cold (it lazy-starts on first use), which only costs latency."""
    try:
        urllib.request.urlopen(f"{url}/models", timeout=timeout)
        return True
    except (urllib.error.URLError, OSError, ValueError):
        return False


def describe(
    image_bytes: bytes,
    question: str,
    *,
    url: str = DEFAULT_URL,
    model: str = DEFAULT_MODEL,
    media_type: str = "image/jpeg",
    max_tokens: int = 500,
    timeout: float = 240.0,
) -> str:
    """Ask the local vision model one question about one image."""
    data_uri = f"data:{media_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    body = json.dumps(
        {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": question},
                    ],
                }
            ],
        }
    ).encode()
    request = urllib.request.Request(
        f"{url}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer local"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read()[:200].decode(errors="replace")
        raise TeeError(
            "vlm_failed",
            f"The local vision model rejected the request ({exc.code}): {detail}",
            fix="Check the shim log (~/.claude/qwen-local/litellm.log); "
            "ue_capture still returns the raw image if you need it.",
        ) from exc
    except (urllib.error.URLError, OSError) as exc:
        raise TeeError(
            "vlm_unreachable", f"No local vision model at {url} ({exc}).", fix=_UNREACHABLE_FIX
        ) from exc
    try:
        text = payload["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise TeeError(
            "vlm_bad_response",
            "The local vision model returned no text content.",
            fix="Check the vision server log (~/.claude/qwen-local/vlm-server.log).",
        ) from exc
    return text.strip()
