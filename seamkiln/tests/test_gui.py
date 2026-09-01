"""The Qt shell (A53 P5). Skips cleanly when Qt is absent - and asserts that
the core does not need it, which is the law the extra exists to keep."""

from __future__ import annotations

import importlib.util
import os

import pytest

from seamkiln.session import Command, Session


def test_the_core_never_needs_qt() -> None:
    """`import seamkiln` must work with no Qt installed. The GUI is an extra;
    a core that quietly depends on it is a core nobody can run headless."""
    import seamkiln.drape.solve
    import seamkiln.pattern
    import seamkiln.session  # noqa: F401

    for module in ("seamkiln", "seamkiln.pattern", "seamkiln.session", "seamkiln.drape.solve"):
        assert importlib.util.find_spec(module) is not None


@pytest.fixture(scope="module")
def qt_app():
    pytest.importorskip("PySide6", reason="seamkiln[gui] not installed")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_the_window_draws_what_the_session_holds(qt_app, tmp_path) -> None:
    from seamkiln.gui.app import SeamkilnWindow

    shell = SeamkilnWindow(workdir=tmp_path)
    assert shell.refresh() == {"panels": 0, "marks": 0, "internals": 0}

    shell.run(Command("block", {"block": "tee"}))
    counts = shell.refresh()
    assert counts["panels"] == 4
    assert counts["marks"] == 9  # 3 front + 4 back + 1 per sleeve
    assert counts["internals"] == 5


def test_panels_are_laid_out_rather_than_stacked(qt_app, tmp_path) -> None:
    """Drafted about a shared origin, four pieces drawn raw sit on top of one
    another - which is what the first version of this window showed."""
    from seamkiln.gui.app import SeamkilnWindow

    shell = SeamkilnWindow(workdir=tmp_path)
    shell.run(Command("block", {"block": "tee"}))
    rect = shell.scene.itemsBoundingRect()
    widest = max(panel.bbox[2] - panel.bbox[0] for panel in shell.session.pattern.panels)
    assert rect.width() > widest * 1.5, "the panels are stacked on one another"


def test_a_gui_session_replays_headlessly(qt_app, tmp_path) -> None:
    """P5's acceptance, and the whole architectural claim: an afternoon of
    clicking exports as a script that reproduces the garment exactly."""
    from seamkiln.gui.app import SeamkilnWindow

    shell = SeamkilnWindow(workdir=tmp_path)
    for command in (
        Command("block", {"block": "tee"}),
        Command("allowance", {"mm": 10.0}),
        Command("body", {"kind": "mannequin"}),
        Command("arrange", {"particle_distance_mm": 25.0}),
        Command("drape", {"fabric": "cotton_poplin", "frames": 30}),
    ):
        shell.run(command)

    script = shell.save_script(tmp_path / "session.json")
    assert Session.replay(script).fingerprint() == shell.session.fingerprint()


def test_a_refused_command_shows_in_the_log_and_changes_nothing(qt_app, tmp_path) -> None:
    from seamkiln.gui.app import SeamkilnWindow

    shell = SeamkilnWindow(workdir=tmp_path)
    result = shell.run(Command("delete", {"id": "NOPE"}))
    assert "error" in result
    assert shell.session.history == []
    assert "!" in shell.log.toPlainText()


def test_the_window_can_photograph_itself(qt_app, tmp_path) -> None:
    """How this GUI is tested at all: offscreen Qt plus widget.grab()."""
    from seamkiln.gui.app import SeamkilnWindow

    shell = SeamkilnWindow(workdir=tmp_path)
    shell.run(Command("block", {"block": "tee"}))
    image = shell.grab(tmp_path / "window.png")
    assert image.is_file() and image.stat().st_size > 5000
