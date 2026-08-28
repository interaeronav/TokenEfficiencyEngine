"""W4 media arms: captions and transcripts with structured degrades, the
cost-confirm size gate, and the anti-goals (streaming refused pre-fetch,
paywalls answered as errors). All hermetic - VLM and whisper are faked at
their module seams; NOTHING running is the default these tests prove.
"""

from __future__ import annotations

import sys
from typing import Any

import pytest
from fixtures_web import HOSTILE_ALT

from tee.kernel import local_vlm
from tee.kernel.errors import TeeError
from tee.web import media as web_media
from tee.web.fetch import WebFetcher
from tee.web.tools import WebLookupService

PAGE_WITH_IMAGES = """<!doctype html>
<html><head><title>Roofing guide</title></head><body>
<p>Corrugated iron weathers to a dull grey over a decade.</p>
<img src="/img/roof-closeup.jpg" alt="weathered corrugated iron roof closeup">
<img src="https://cdn.example/roof-far.png" alt="roof from the street">
<img src="data:image/gif;base64,R0lGOD">
<img src="/img/roof-closeup.jpg" alt="duplicate">
</body></html>"""


def service(tmp_path, routes: dict[str, Any], **kwargs) -> WebLookupService:
    def transport(target, headers, timeout):
        entry = routes[target.url]
        if isinstance(entry, list):
            return entry.pop(0) if len(entry) > 1 else entry[0]
        return entry

    fetcher = WebFetcher(
        tmp_path,
        transport=transport,
        resolve=lambda host, port: ["93.184.216.34"],
        min_interval_s=0.0,
        sleep=lambda s: None,
    )
    return WebLookupService(tmp_path, fetcher=fetcher, **kwargs)


ROBOTS = {"http://site.example/robots.txt": (404, {}, b"")}


# --- anti-goals -------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=abc",
        "https://youtu.be/abc",
        "https://open.spotify.com/track/x",
    ],
)
def test_streaming_hosts_refused_before_any_fetch(tmp_path, url) -> None:
    calls: list[str] = []

    def transport(target, headers, timeout):
        calls.append(target.url)
        raise AssertionError("must not fetch")

    fetcher = WebFetcher(tmp_path, transport=transport, resolve=lambda h, p: ["93.184.216.34"])
    svc = WebLookupService(tmp_path, fetcher=fetcher)
    with pytest.raises(TeeError) as excinfo:
        svc.lookup(url, "what is said in this video?")
    assert excinfo.value.code == "web_streaming_blocked"
    assert calls == []


def test_paywall_is_an_error_not_a_bypass(tmp_path) -> None:
    svc = service(tmp_path, {**ROBOTS, "http://site.example/paid": (402, {}, b"")})
    with pytest.raises(TeeError) as excinfo:
        svc.lookup("http://site.example/paid", "what does it say?")
    assert excinfo.value.code == "web_http_error"


# --- image arm --------------------------------------------------------------


def test_question_wants_image_heuristic() -> None:
    assert web_media.question_wants_image("what does the roof look like?")
    assert web_media.question_wants_image("describe the diagram")
    assert not web_media.question_wants_image("when must free() be called?")


def test_collect_images_resolves_dedupes_and_skips_data_uris() -> None:
    images = web_media.collect_images(PAGE_WITH_IMAGES, "http://site.example/guide")
    assert [i["url"] for i in images] == [
        "http://site.example/img/roof-closeup.jpg",
        "https://cdn.example/roof-far.png",
    ]
    assert images[0]["alt"] == "weathered corrugated iron roof closeup"


def test_image_question_without_vlm_gets_structured_note(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(local_vlm, "available", lambda *a, **k: False)
    svc = service(
        tmp_path, {**ROBOTS, "http://site.example/guide": (200, {}, PAGE_WITH_IMAGES.encode())}
    )
    answer = svc.lookup("http://site.example/guide", "what does the roof look like?")
    assert answer["media"]["images_on_page"] == 2
    assert "no local VLM" in answer["media"]["unavailable"]
    assert "Corrugated iron weathers" in answer["quote"]  # text path untouched


def test_image_question_with_vlm_captions_top_images(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(local_vlm, "available", lambda *a, **k: True)
    seen: list[tuple[bytes, str]] = []

    def fake_describe(data, question, **kwargs):
        seen.append((data, question))
        return "A weathered corrugated roof."

    monkeypatch.setattr(local_vlm, "describe", fake_describe)
    routes = {
        **ROBOTS,
        "http://site.example/guide": (200, {}, PAGE_WITH_IMAGES.encode()),
        "http://site.example/img/roof-closeup.jpg": (200, {}, b"\xff\xd8jpg"),
        "https://cdn.example/robots.txt": (404, {}, b""),
        "https://cdn.example/roof-far.png": (200, {}, b"\x89PNGpng"),
    }
    svc = service(tmp_path, routes)
    answer = svc.lookup("http://site.example/guide", "what does the roof look like?")
    captions = answer["media"]["captions"]
    assert len(captions) == 2
    assert all(c["caption"] == "A weathered corrugated roof." for c in captions)
    assert len(seen) == 2


def test_text_question_never_touches_images(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        local_vlm, "available", lambda *a, **k: pytest.fail("must not probe the VLM")
    )
    svc = service(
        tmp_path, {**ROBOTS, "http://site.example/guide": (200, {}, PAGE_WITH_IMAGES.encode())}
    )
    answer = svc.lookup("http://site.example/guide", "how long until the iron weathers?")
    assert "media" not in answer


def test_media_off_disables_both_arms(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        local_vlm, "available", lambda *a, **k: pytest.fail("must not probe the VLM")
    )
    svc = service(
        tmp_path, {**ROBOTS, "http://site.example/guide": (200, {}, HOSTILE_ALT.encode())}
    )
    answer = svc.lookup("http://site.example/guide", "what does the picture show?", media="off")
    assert "media" not in answer


# --- audio/video arm --------------------------------------------------------

FAKE_FACTS = [
    {"kind": "transcript", "language": "en", "language_probability": 0.99, "segments": 2,
     "model": "large-v3"},
    {"kind": "transcript_segment", "start_s": 0.0, "end_s": 4.2,
     "text": "Bedding sand goes down first."},
    {"kind": "transcript_segment", "start_s": 4.2, "end_s": 9.0,
     "text": "Then the blocks are laid from the edge restraint."},
]  # fmt: skip


def test_av_url_transcribed_and_budget_cut(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("tee.extract.audio.extract_audio", lambda path, derived: FAKE_FACTS)
    svc = service(tmp_path, {**ROBOTS, "http://site.example/clip.mp3": (200, {}, b"ID3fake")})
    answer = svc.lookup("http://site.example/clip.mp3", "what goes down first?")
    assert "Bedding sand goes down first." in answer["quote"]
    assert answer["media"]["kind"] == "transcript"
    assert answer["media"]["language"] == "en"
    assert answer["media"]["model"] == "faster-whisper-large-v3"


def test_big_av_needs_cost_confirmation(tmp_path) -> None:
    big = {"Content-Length": str(web_media.AV_FREE_BYTES + 1)}
    svc = service(tmp_path, {**ROBOTS, "http://site.example/talk.mp3": (200, big, b"")})
    with pytest.raises(TeeError) as excinfo:
        svc.lookup("http://site.example/talk.mp3", "what is discussed?")
    assert excinfo.value.code == "cost_confirmation_required"
    assert "media='confirm'" in (excinfo.value.fix or "")


def test_confirmed_big_av_proceeds(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("tee.extract.audio.extract_audio", lambda path, derived: FAKE_FACTS)
    big = {"Content-Length": str(web_media.AV_FREE_BYTES + 1)}
    svc = service(tmp_path, {**ROBOTS, "http://site.example/talk.mp3": (200, big, b"ID3fake")})
    answer = svc.lookup("http://site.example/talk.mp3", "what goes first?", media="confirm")
    assert answer["media"]["kind"] == "transcript"


def test_av_without_whisper_names_the_extra(tmp_path, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "tee.extract.audio", None)
    svc = service(tmp_path, {**ROBOTS, "http://site.example/clip.mp3": (200, {}, b"ID3fake")})
    with pytest.raises(TeeError) as excinfo:
        svc.lookup("http://site.example/clip.mp3", "what is said?")
    assert excinfo.value.code == "web_media_unavailable"
    assert "[extract]" in (excinfo.value.fix or "")


def test_transcript_with_no_speech_is_loud(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "tee.extract.audio.extract_audio",
        lambda path, derived: [{"kind": "note", "note": "transcription unavailable (broken)"}],
    )
    svc = service(tmp_path, {**ROBOTS, "http://site.example/clip.mp3": (200, {}, b"ID3fake")})
    with pytest.raises(TeeError) as excinfo:
        svc.lookup("http://site.example/clip.mp3", "what is said?")
    assert excinfo.value.code == "web_media_unavailable"


def test_size_hints_demote_chrome_and_promote_content() -> None:
    page = """<body>
    <img src="/spacer.gif" width="16" height="16" alt="">
    <img src="/tagline.png" width="120" height="14" alt="the free encyclopedia tagline">
    <img src="/roof-photo.jpg" width="640" height="480" alt="roof">
    </body>"""
    images = web_media.collect_images(page, "http://site.example/x")
    ranked = web_media.rank_images(images, "what does the roof look like?")
    assert ranked[0]["url"].endswith("/roof-photo.jpg")
    assert ranked[-1]["url"].endswith(("/spacer.gif", "/tagline.png"))


def test_unsized_images_keep_alt_relevance_ranking() -> None:
    images = web_media.collect_images(PAGE_WITH_IMAGES, "http://site.example/guide")
    ranked = web_media.rank_images(images, "weathered corrugated roof?")
    assert ranked[0]["alt"].startswith("weathered corrugated")
