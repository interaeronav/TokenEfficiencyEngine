"""Chore-layer contract (A34 M2): every chore green on the fake endpoint,
schema gates fail closed, the refine idiom degrades exactly as specified,
and the extractive-by-verification guarantee kills invented sentences.
"""

from __future__ import annotations

import json

import pytest
from fixtures_llm import fake_llm_server
from fixtures_web import HOSTILE_BODY

from tee.kernel.errors import TeeError
from tee.llm import chores


@pytest.fixture(autouse=True)
def _fresh_probe_cache():
    chores._probe_cache.clear()
    yield
    chores._probe_cache.clear()


def cfg(url: str) -> dict:
    return {"url": url, "model": "fake"}


# --- the refine idiom -------------------------------------------------------


def test_refine_off_makes_no_request() -> None:
    with fake_llm_server(["never"]) as (url, calls):
        assert chores.triage("boom", refine="off", cfg=cfg(url)) is None
        assert calls == []


def test_refine_auto_degrades_to_none_when_nothing_runs() -> None:
    assert chores.triage("boom", refine="auto", cfg=cfg("http://127.0.0.1:9/v1")) is None


def test_refine_local_requires_the_endpoint() -> None:
    with pytest.raises(TeeError) as excinfo:
        chores.triage("boom", refine="local", cfg=cfg("http://127.0.0.1:9/v1"))
    assert excinfo.value.code == "llm_unreachable"


def test_bad_refine_mode_is_loud() -> None:
    with pytest.raises(TeeError) as excinfo:
        chores.triage("boom", refine="turbo")
    assert excinfo.value.code == "llm_bad_arg"


# --- chore 1: triage --------------------------------------------------------


def test_triage_happy_path_stamps_provenance() -> None:
    reply = json.dumps(
        {"diagnosis": "bm is None", "fix": "guard with if bm:", "confidence": "grounded"}
    )
    with fake_llm_server([reply]) as (url, _):
        result = chores.triage("Traceback ...", cfg=cfg(url))
    assert result == {
        "diagnosis": "bm is None",
        "fix": "guard with if bm:",
        "confidence": "grounded",
        "model": chores.STAMP,
    }


def test_triage_bad_confidence_fails_closed() -> None:
    reply = json.dumps({"diagnosis": "d", "fix": "f", "confidence": "certain"})
    with fake_llm_server([reply, reply]) as (url, _):
        assert chores.triage("boom", cfg=cfg(url)) is None


# --- chore 2: script repair -------------------------------------------------


def test_repair_script_shape() -> None:
    reply = json.dumps({"repaired_code": "x = 1", "note": "removed the import"})
    with fake_llm_server([reply]) as (url, _):
        result = chores.repair_script("import os\nx = 1", "import is not allowed", cfg=cfg(url))
    assert result["repaired_code"] == "x = 1"
    assert result["model"] == chores.STAMP


def test_repair_essay_rejected() -> None:
    reply = json.dumps({"repaired_code": "y" * 5000, "note": "n"})
    with fake_llm_server([reply, reply]) as (url, _):
        assert chores.repair_script("x = 1", "err", cfg=cfg(url)) is None


# --- chore 3: lint explanation ----------------------------------------------


def test_explain_lint_shape() -> None:
    reply = json.dumps({"explanation": "The wall overlaps the door; move it 0.2m east."})
    with fake_llm_server([reply]) as (url, _):
        result = chores.explain_lint("plaus_check: overlap wall/door", cfg=cfg(url))
    assert result["explanation"].startswith("The wall overlaps")


# --- chore 4: extract refinement, extractive by verification ----------------

PAGE_TEXT = (
    "Laying block paving\n"
    "Bedding sand should be 25 to 40 mm thick once compacted.\n"
    "Edge restraints go in before the blocks."
)


def test_refine_extract_verbatim_sentences_pass() -> None:
    reply = json.dumps({"sentences": ["Bedding sand should be 25 to 40 mm thick once compacted."]})
    with fake_llm_server([reply]) as (url, _):
        result = chores.refine_extract(PAGE_TEXT, "how thick?", 200, cfg=cfg(url))
    assert result["quote"] == "Bedding sand should be 25 to 40 mm thick once compacted."
    assert result["model"] == chores.STAMP


def test_refine_extract_invented_sentence_kills_the_lot() -> None:
    reply = json.dumps(
        {
            "sentences": [
                "Bedding sand should be 25 to 40 mm thick once compacted.",
                "Bedding sand must always be exactly 30 mm.",  # invented
            ]
        }
    )
    with fake_llm_server([reply, reply]) as (url, _):
        assert chores.refine_extract(PAGE_TEXT, "how thick?", 200, cfg=cfg(url)) is None


def test_refine_extract_empty_selection_is_abstention_even_under_local() -> None:
    reply = json.dumps({"sentences": []})
    with fake_llm_server([reply]) as (url, _):
        assert (
            chores.refine_extract(PAGE_TEXT, "unrelated?", 200, refine="local", cfg=cfg(url))
            is None
        )


def test_refine_extract_whitespace_normalized_still_verbatim() -> None:
    reply = json.dumps({"sentences": ["Edge restraints  go in\nbefore the blocks."]})
    with fake_llm_server([reply]) as (url, _):
        result = chores.refine_extract(PAGE_TEXT, "edge restraints?", 200, cfg=cfg(url))
    assert result["quote"] == "Edge restraints go in before the blocks."


# --- chores 5-7 -------------------------------------------------------------


def test_structure_facts_typed_and_gated() -> None:
    good = json.dumps({"facts": [{"kind": "dimension", "text": "wall height 2.4 m"}]})
    with fake_llm_server([good]) as (url, _):
        result = chores.structure_facts("the wall is 2.4 m high", cfg=cfg(url))
    assert result["facts"] == [{"kind": "dimension", "text": "wall height 2.4 m"}]
    bad = json.dumps({"facts": [{"kind": "vibe", "text": "nice"}]})
    with fake_llm_server([bad, bad]) as (url, _):
        assert chores.structure_facts("text", cfg=cfg(url)) is None


def test_compress_recap_one_line() -> None:
    reply = json.dumps({"summary": "3 meshes, cp2 latest, blender 5.2 connected."})
    with fake_llm_server([reply]) as (url, _):
        result = chores.compress_recap({"adapters": {"blender": {}}}, cfg=cfg(url))
    assert result["summary"].endswith("connected.")


def test_rerank_must_be_a_permutation() -> None:
    candidates = [{"id": "a", "title": "A"}, {"id": "b", "title": "B"}]
    good = json.dumps({"order": ["b", "a"]})
    with fake_llm_server([good]) as (url, _):
        assert chores.rerank("q", candidates, cfg=cfg(url))["order"] == ["b", "a"]
    lossy = json.dumps({"order": ["b"]})
    with fake_llm_server([lossy, lossy]) as (url, _):
        assert chores.rerank("q", candidates, cfg=cfg(url)) is None


# --- integration: the repair draft rides the tee_script refusal -------------


def test_script_refusal_carries_repair_draft(tmp_path) -> None:
    import anyio
    from mcp.client import Client

    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.server import build_server

    reply = json.dumps({"repaired_code": "result = 2", "note": "dropped the import"})
    with fake_llm_server([reply]) as (url, _):
        (tmp_path / ".tee").mkdir()
        (tmp_path / ".tee" / "config.toml").write_text(f'[llm]\nurl = "{url}"\nmodel = "fake"\n')
        app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
        try:
            server = build_server(app)

            async def scenario():
                async with Client(server) as client:
                    result = await client.call_tool("tee_script", {"code": "import os\nresult = 2"})
                    return json.loads(result.content[0].text)

            payload = anyio.run(scenario)
        finally:
            app.shutdown()
    assert payload["ok"] is False
    assert payload["error"]["code"].startswith("script_")
    assert payload["repair"]["repaired_code"] == "result = 2"
    assert payload["repair"]["model"] == chores.STAMP


# --- integration: web refinement under the verification guarantee -----------


def test_web_lookup_refined_quote_carries_stamp(tmp_path) -> None:
    from tee.web.fetch import WebFetcher
    from tee.web.tools import WebLookupService

    def reply(request: dict) -> str:
        if "extract-refinement" in request["messages"][0]["content"]:
            return json.dumps(
                {"sentences": ["Bedding sand should be 25 to 40 mm thick once compacted."]}
            )
        return json.dumps({})

    routes = {
        "http://site.example/robots.txt": (404, {}, b""),
        "http://site.example/p": (200, {}, HOSTILE_BODY.encode()),
    }
    with fake_llm_server(reply) as (url, _):
        fetcher = WebFetcher(
            tmp_path,
            transport=lambda target, headers, timeout: routes[target.url],
            resolve=lambda host, port: ["93.184.216.34"],
            min_interval_s=0.0,
        )
        service = WebLookupService(
            tmp_path, fetcher=fetcher, llm={"url": url, "model": "fake", "refine": "auto"}
        )
        answer = service.lookup("http://site.example/p", "how thick is bedding sand?")
    assert answer["quote"] == "Bedding sand should be 25 to 40 mm thick once compacted."
    assert answer["model"] == chores.STAMP


def test_web_lookup_refine_off_never_calls_the_model(tmp_path) -> None:
    from tee.web.fetch import WebFetcher
    from tee.web.tools import WebLookupService

    routes = {
        "http://site.example/robots.txt": (404, {}, b""),
        "http://site.example/p": (200, {}, HOSTILE_BODY.encode()),
    }
    with fake_llm_server(["never"]) as (url, calls):
        fetcher = WebFetcher(
            tmp_path,
            transport=lambda target, headers, timeout: routes[target.url],
            resolve=lambda host, port: ["93.184.216.34"],
            min_interval_s=0.0,
        )
        service = WebLookupService(
            tmp_path, fetcher=fetcher, llm={"url": url, "model": "fake", "refine": "off"}
        )
        answer = service.lookup("http://site.example/p", "how thick is bedding sand?")
    assert "model" not in answer
    assert calls == []
    assert "25 to 40 mm" in answer["quote"]  # the dumb path stands


def test_adapters_passthrough_reaches_the_request_body(monkeypatch) -> None:
    reply = json.dumps({"diagnosis": "d", "fix": "f", "confidence": "grounded"})
    with fake_llm_server([reply]) as (url, calls):
        result = chores.triage(
            "boom", cfg={"url": url, "model": "fake", "adapters": "/tmp/adapter-x"}
        )
    assert result is not None
    assert calls[0].get("adapters") == "/tmp/adapter-x"


def test_llm_triage_is_registered_again(tmp_path) -> None:
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.llm.tools import register_llm_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        register_llm_tools(app, tmp_path)
        description = app.registry.describe("llm_triage")["description"]
        assert "needs_verification" in description
    finally:
        app.shutdown()
