"""Local-LLM client contract (A34 M1): the local_vlm sibling, offline.

Unit tests fake urllib (the vision-lane idiom); the last tests run the
real client against the threaded fake endpoint so URL handling, headers,
and framing are proven end to end with no model anywhere.
"""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest
from fixtures_llm import fake_llm_server

from tee.kernel import local_llm
from tee.kernel.errors import TeeError


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _reply(text: str) -> _FakeResponse:
    return _FakeResponse(
        json.dumps({"choices": [{"message": {"role": "assistant", "content": text}}]}).encode()
    )


def test_complete_builds_thinking_off_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data)
        return _reply("\n\nOne-line diagnosis.")

    monkeypatch.setattr(local_llm.urllib.request, "urlopen", fake_urlopen)
    answer = local_llm.complete("triage this", system="You are the traceback chore.")

    assert answer == "One-line diagnosis."
    assert seen["url"].endswith("/chat/completions")
    body = seen["body"]
    assert body["model"] == local_llm.DEFAULT_MODEL
    assert body["temperature"] == 0.0
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert [m["role"] for m in body["messages"]] == ["system", "user"]


def test_leaked_think_block_is_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        local_llm.urllib.request,
        "urlopen",
        lambda request, timeout=0: _reply("<think>secret musing</think>\nThe fix is X."),
    )
    assert local_llm.complete("q") == "The fix is X."


def test_unreachable_is_one_cheap_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(local_llm.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(TeeError) as excinfo:
        local_llm.complete("anything")
    assert excinfo.value.code == "llm_unreachable"
    assert "TEE_LOCAL_LLM_URL" in (excinfo.value.fix or "")
    assert "deterministic" in (excinfo.value.fix or "")


def test_empty_content_is_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        local_llm.urllib.request,
        "urlopen",
        lambda request, timeout=0: _FakeResponse(b'{"choices": []}'),
    )
    with pytest.raises(TeeError) as excinfo:
        local_llm.complete("q")
    assert excinfo.value.code == "llm_bad_response"


def test_complete_json_parses_fenced_and_requests_json_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        seen["body"] = json.loads(request.data)
        return _reply('Here you go:\n```json\n{"diagnosis": "x", "fix": "y"}\n```')

    monkeypatch.setattr(local_llm.urllib.request, "urlopen", fake_urlopen)
    assert local_llm.complete_json("q") == {"diagnosis": "x", "fix": "y"}
    assert seen["body"]["response_format"] == {"type": "json_object"}


def test_complete_json_retries_once_then_fails_loud(monkeypatch: pytest.MonkeyPatch) -> None:
    replies = iter(["not json at all", "still prose"])
    calls: list[str] = []

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        body = json.loads(request.data)
        calls.append(body["messages"][-1]["content"])
        return _reply(next(replies))

    monkeypatch.setattr(local_llm.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(TeeError) as excinfo:
        local_llm.complete_json("q")
    assert excinfo.value.code == "llm_bad_json"
    assert len(calls) == 2
    assert "ONLY the JSON" in calls[1]


# --- end to end against the threaded fake endpoint --------------------------


def test_round_trip_against_fake_endpoint() -> None:
    with fake_llm_server(['{"ok": true}']) as (url, calls):
        assert local_llm.available(url=url) is True
        answer = local_llm.complete_json("structure this", url=url, model="fake")
        assert answer == {"ok": True}
        assert calls[0]["model"] == "fake"


def test_available_false_when_nothing_listens() -> None:
    assert local_llm.available(url="http://127.0.0.1:9/v1", timeout=0.3) is False


def test_a_probe_asks_about_the_model_not_just_the_port():
    """An endpoint that answers while serving OTHER models is not this
    chore's engine. Found for real: a proxy fronting different model
    groups replied to /models happily and then 400'd every chore, which
    read as a broken suite rather than 'no local model here'."""
    from fixtures_llm import fake_llm_server

    from tee.kernel import local_llm

    with fake_llm_server([""], models=("some-other-model",)) as (url, _):
        assert local_llm.available(url=url, model="tee-coder") is False
        assert local_llm.available(url=url, model="some-other-model") is True
        # an endpoint that will not enumerate keeps the benefit of the doubt
        assert local_llm.available(url=url, model=None) is True


def test_a_chore_degrades_when_the_endpoint_serves_a_different_model():
    """The consequence: the deterministic path, not a 400 mid-chore."""
    import pytest
    from fixtures_llm import fake_llm_server

    from tee.kernel.errors import TeeError
    from tee.llm import chores

    with fake_llm_server([""], models=("some-other-model",)) as (url, calls):
        cfg = {"url": url, "model": "tee-coder"}
        assert chores.triage("boom", "ctx", refine="auto", cfg=cfg) is None
        with pytest.raises(TeeError) as excinfo:
            chores.triage("boom", "ctx", refine="local", cfg=cfg)
    assert excinfo.value.code == "llm_unreachable"
    assert calls == []  # never sent - refused at the probe, not at the wire
