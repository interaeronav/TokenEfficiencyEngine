"""Local-VLM lane (3.7): the kernel client, the ue_look composition, and the
extraction driver - all offline, the HTTP layer faked at urllib."""

from __future__ import annotations

import io
import json
import urllib.error
from typing import Any

import pytest

from tee.adapters.unreal import vision
from tee.extract import vlm
from tee.kernel import local_vlm
from tee.kernel.errors import TeeError


class _FakeResponse(io.BytesIO):
    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _openai_reply(text: str) -> _FakeResponse:
    return _FakeResponse(
        json.dumps({"choices": [{"message": {"role": "assistant", "content": text}}]}).encode()
    )


def test_describe_builds_openai_payload_and_returns_text(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {}

    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data)
        return _openai_reply("\n\nThe door is blue.")

    monkeypatch.setattr(local_vlm.urllib.request, "urlopen", fake_urlopen)
    answer = local_vlm.describe(b"\xff\xd8jpegbytes", "What color is the door?")

    assert answer == "The door is blue."
    assert seen["url"].endswith("/chat/completions")
    assert seen["body"]["model"] == local_vlm.DEFAULT_MODEL
    image, text = seen["body"]["messages"][0]["content"]
    assert image["type"] == "image_url"
    assert image["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert text["text"] == "What color is the door?"


def test_describe_unreachable_is_one_cheap_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: Any, timeout: float = 0) -> _FakeResponse:
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(local_vlm.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(TeeError) as excinfo:
        local_vlm.describe(b"x", "anything")
    assert excinfo.value.code == "vlm_unreachable"
    assert "TEE_LOCAL_VLM_URL" in (excinfo.value.fix or "")


class _FakeCaptures:
    def capture_with_metadata(
        self, max_bytes: int, *, show_ui: bool = False
    ) -> tuple[bytes, dict[str, Any]]:
        assert not show_ui
        return b"jpeg", {
            "cameraLocation": [1, 2, 3],
            "labeled_actor_count": 7,
            "bytes": max_bytes,  # encode stat - must NOT leak into the answer
        }


def test_look_returns_answer_plus_free_metadata_only() -> None:
    result = vision.look(
        _FakeCaptures(), "Is it night?", describe=lambda data, question: "Yes, night."
    )
    assert result == {
        "answer": "Yes, night.",
        "cameraLocation": [1, 2, 3],
        "labeled_actor_count": 7,
    }


def test_local_driver_parses_schema_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
    sheet = tmp_path / "sheet01.jpg"
    sheet.write_bytes(b"\xff\xd8fake")
    monkeypatch.setattr(
        local_vlm,
        "describe",
        lambda data, question, **kw: 'Here you go:\n{"walls": [], "units": "m"}\nDone.',
    )
    driver = vlm.LocalVlmDriver()
    assert driver.extract_document_page(sheet, {"units": "m"}) == {"walls": [], "units": "m"}
