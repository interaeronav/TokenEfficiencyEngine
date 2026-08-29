"""board_compose (A37 P7): styled SVG boards from live artifacts -
image/table/lines panels, refusal shapes, compact pointer response."""

from __future__ import annotations

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError

TINY_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c6300010000050001"
) + bytes.fromhex("0d0a2db40000000049454e44ae426082")


def app_fixture(tmp_path) -> TeeApp:
    return TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)


def test_board_composes_all_panel_kinds(tmp_path) -> None:
    app = app_fixture(tmp_path)
    try:
        image = tmp_path / "render.png"
        image.write_bytes(TINY_PNG)
        out = app.registry.call(
            "board_compose",
            {
                "title": "Fixture board",
                "subtitle": "three panel kinds",
                "style": "dark",
                "panels": [
                    {"image": str(image), "caption": "render"},
                    {
                        "table": {"cols": ["part", "qty"], "rows": [["Side", 2]]},
                        "caption": "cut list",
                    },
                    {"lines": ["fact one", "fact two"], "caption": "facts"},
                ],
                "out": str(tmp_path / "board.svg"),
            },
        )
        assert out["ok"] is True and out["panels"] == 3
        text = (tmp_path / "board.svg").read_text()
        assert text.startswith("<svg") and text.endswith("</svg>")
        assert "Fixture board" in text
        assert "data:image/png;base64," in text  # the render embedded
        assert "Side" in text and "fact two" in text
        assert "host-side by design" in text  # the scope statement ships on the page
    finally:
        app.shutdown()


def test_board_refusals_are_rule6(tmp_path) -> None:
    app = app_fixture(tmp_path)
    try:
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("board_compose", {"title": "x", "panels": []})
        assert excinfo.value.code == "board_bad_args"
        with pytest.raises(TeeError) as excinfo:
            app.registry.call(
                "board_compose",
                {"title": "x", "panels": [{"caption": "empty"}], "out": str(tmp_path / "b.svg")},
            )
        assert excinfo.value.code == "board_bad_panel"
        with pytest.raises(TeeError) as excinfo:
            app.registry.call(
                "board_compose",
                {
                    "title": "x",
                    "panels": [{"image": str(tmp_path / "missing.png")}],
                    "out": str(tmp_path / "b.svg"),
                },
            )
        assert "Render/export it first" in excinfo.value.fix
    finally:
        app.shutdown()


def test_board_escapes_hostile_text(tmp_path) -> None:
    app = app_fixture(tmp_path)
    try:
        out = app.registry.call(
            "board_compose",
            {
                "title": '<script>alert("x")</script>',
                "panels": [{"lines": ["</svg><evil>"], "caption": "inj"}],
                "out": str(tmp_path / "board.svg"),
            },
        )
        text = (tmp_path / "board.svg").read_text()
        assert "<script>" not in text and "<evil>" not in text
        assert out["ok"] is True
    finally:
        app.shutdown()
