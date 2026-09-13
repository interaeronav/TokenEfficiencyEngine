"""W0: the thinking engine's contracts, pinned.

Every assertion here cost a live measurement on 2026-09-13 and would
otherwise be invisible until a chore silently stopped working:

- the two local backends DISAGREE about `response_format` - the MLX server
  accepts it and ignores it, vLLM refuses it outright (HTTP 400, "requires
  the optional llguidance dependency") rather than return unconstrained
  output. TEE sent it unconditionally, so it could not reach vLLM at all.
- the reasoning field is named `reasoning` on one backend and
  `reasoning_content` on the other. Reading the wrong one reads as "this
  model cannot think" - it produced two false negatives in one session.
- a thinking model can spend its whole budget reasoning and answer nothing
  (26,608 chars, finish=length, zero content). That must fail loudly.
- reasoning must never reach the client, or a thinking engine stops being
  free in the metric TEE is judged by.
"""

from __future__ import annotations

import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tee.kernel import local_llm
from tee.kernel.errors import TeeError


@contextlib.contextmanager
def backend(handler):
    """A fake OpenAI endpoint. `handler(request) -> (status, message_dict)`."""
    calls: list[dict] = []

    class H(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = json.dumps({"data": [{"id": "fake"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(request)
            status, message = handler(request)
            body = (
                json.dumps({"error": {"message": message}})
                if status != 200
                else json.dumps({"choices": [{"message": message}]})
            ).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1", calls
    finally:
        server.shutdown()
        server.server_close()


def _vllm(request):
    """vLLM's real behaviour: refuse response_format rather than fake it."""
    if "response_format" in request:
        return 400, (
            "response_format type 'json_object' requires the optional llguidance "
            "dependency (pip install llguidance); refusing to silently return "
            "unconstrained output"
        )
    return 200, {"role": "assistant", "content": '{"ok": true}'}


@pytest.fixture(autouse=True)
def _forget_negotiation():
    local_llm._NO_JSON_MODE.clear()
    yield
    local_llm._NO_JSON_MODE.clear()


def test_response_format_is_negotiated_away_when_the_endpoint_refuses_it():
    with backend(_vllm) as (url, calls):
        out = local_llm.complete_json("hi", url=url, model="fake", adapters=None)
    assert out == {"ok": True}
    assert "response_format" in calls[0], "the first attempt should try the field"
    assert "response_format" not in calls[1], "the retry must drop it"
    assert local_llm.json_mode_unsupported(url, "fake"), "the refusal must be remembered"


def test_a_refusal_is_remembered_so_the_next_chore_pays_no_round_trip():
    with backend(_vllm) as (url, calls):
        local_llm.complete_json("one", url=url, model="fake", adapters=None)
        local_llm.complete_json("two", url=url, model="fake", adapters=None)
    assert len(calls) == 3, "2 for the first (400 + retry), 1 for the second"
    assert "response_format" not in calls[2]


def test_json_mode_off_never_sends_the_field_at_all():
    with backend(_vllm) as (url, calls):
        local_llm.complete_json("hi", url=url, model="fake", adapters=None, json_mode="off")
    assert len(calls) == 1 and "response_format" not in calls[0]


def test_json_mode_on_does_not_negotiate_and_the_refusal_surfaces():
    with backend(_vllm) as (url, _), pytest.raises(TeeError) as caught:
        local_llm.complete_json("hi", url=url, model="fake", adapters=None, json_mode="on")
    assert caught.value.code == "llm_failed"


@pytest.mark.parametrize("field", ["reasoning", "reasoning_content"])
def test_reasoning_is_read_from_either_backend_field_name(field):
    def h(_request):
        return 200, {"role": "assistant", "content": "answer", field: "because X"}

    seen: list[str] = []
    with backend(h) as (url, _):
        text = local_llm.complete(
            "hi", url=url, model="fake", adapters=None, on_reasoning=seen.append
        )
    assert text == "answer"
    assert seen == ["because X"], f"{field} must be recognised as reasoning"


def test_an_inline_think_block_is_captured_not_merely_stripped():
    def h(_request):
        return 200, {"role": "assistant", "content": "<think>weighing it</think>answer"}

    seen: list[str] = []
    with backend(h) as (url, _):
        text = local_llm.complete(
            "hi", url=url, model="fake", adapters=None, on_reasoning=seen.append
        )
    assert text == "answer"
    assert seen == ["weighing it"]


def test_thinking_rides_the_wire_and_defaults_off():
    def h(_request):
        return 200, {"role": "assistant", "content": "x"}

    with backend(h) as (url, calls):
        local_llm.complete("hi", url=url, model="fake", adapters=None)
        local_llm.complete("hi", url=url, model="fake", adapters=None, thinking=True)
    assert calls[0]["chat_template_kwargs"] == {"enable_thinking": False}
    assert calls[1]["chat_template_kwargs"] == {"enable_thinking": True}


def test_a_model_that_only_reasons_fails_loudly_instead_of_returning_empty():
    """The measured runaway: full budget spent reasoning, nothing said."""

    def h(_request):
        return 200, {"role": "assistant", "content": "", "reasoning": "x" * 500}

    with backend(h) as (url, _), pytest.raises(TeeError) as caught:
        local_llm.complete("hi", url=url, model="fake", adapters=None, thinking=True)
    assert caught.value.code == "llm_no_answer"
    assert "500" in caught.value.message


def test_chores_do_not_inherit_thinking_from_the_profile():
    """Opt-in, not inherit — the whole policy in one assertion.

    Measured 2026-09-13: thinking costs 2.8-4.0x, is indistinguishable on the
    three chores with genuine verifiers (8/8 either way) and is WORSE on the
    one calibration chore (traps 6/6 off vs 5/6 on). Zero chores are measured
    to benefit. So a profile that declares thinking must NOT switch it on for
    every chore that happens to run there; a chore opts in, with a number.
    """
    from tee.llm import chores, profiles

    def h(_request):
        return 200, {"role": "assistant", "content": '{"explanation": "ok"}'}

    with backend(h) as (url, calls):
        profiles.BUILTIN_PROFILES["_thinks"] = {
            "url": url,
            "model": "fake",
            "adapters": "",
            "thinking": True,
        }
        try:
            resolved = profiles.resolve({"_profile": "_thinks"})
            assert resolved["thinking"] is True, "the PROFILE still declares it"
            chores.explain_lint("a finding", refine="local", cfg={"_profile": "_thinks"})
        finally:
            profiles.BUILTIN_PROFILES.pop("_thinks", None)

    assert calls, "the chore reached the endpoint"
    assert calls[0]["chat_template_kwargs"] == {"enable_thinking": False}, (
        "a chore that never opted in must not think just because its engine can"
    )


def test_rerank_asks_for_a_permutation_of_what_it_actually_showed():
    """The listing and the demanded permutation must derive from one slice.

    Before 2026-09-13 `ids` came from ALL candidates while the prompt listed
    only the first 20, so 21+ candidates made the validator demand ids the
    model had never seen: a deterministic llm_bad_shape that two benchmark
    rungs (rerank L n=32, XL n=64) had been scoring as a capability limit.
    """
    from tee.llm import chores, profiles

    shown: list[str] = []

    def h(request):
        shown.append(request["messages"][-1]["content"])
        ids = [
            ln.split(":")[0].removeprefix("- ").strip()
            for ln in shown[-1].splitlines()
            if ln.startswith("- ")
        ]
        return 200, {"role": "assistant", "content": json.dumps({"order": list(reversed(ids))})}

    cands = [{"id": f"tool-{i}", "title": f"param {i}"} for i in range(64)]
    with backend(h) as (url, _):
        profiles.BUILTIN_PROFILES["_rr"] = {"url": url, "model": "fake", "adapters": ""}
        try:
            out = chores.rerank("q", cands, refine="local", cfg={"_profile": "_rr"})
        finally:
            profiles.BUILTIN_PROFILES.pop("_rr", None)

    assert out is not None, "64 candidates must not be an automatic verifier kill"
    assert len(out["order"]) == chores.RERANK_MAX
    listed = [ln for ln in shown[0].splitlines() if ln.startswith("- ")]
    assert len(listed) == chores.RERANK_MAX, "the model saw exactly what it must return"
