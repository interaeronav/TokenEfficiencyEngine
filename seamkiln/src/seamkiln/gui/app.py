"""The seamkiln shell: a window that writes the same script a caller would.

**The architecture is the feature.** Every control here builds a
`seamkiln.session.Command` and hands it to `Session.apply`. The window keeps
no garment state of its own - it re-reads the session after each command - so
there is no path through this interface that a script cannot take, and "save
script" is not an export feature, it is just handing over the history that
was being kept anyway.

The 3D view is a RENDERED IMAGE, refreshed after each drape, not an
interactive viewport. That was a decision, not an omission: seamkiln already
has a Blender preview lane that produces a properly lit, correctly shaded
garment, and a second renderer inside Qt would be a worse picture and a whole
new surface to maintain. The cost is honest - you cannot orbit it - and an
interactive QOpenGLWidget viewport is the obvious next step for someone who
needs to.

Qt is an EXTRA. `import seamkiln` must work with no Qt installed, and a test
asserts it.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

from seamkiln.session import Command, CommandError, Session

WINDOW_TITLE = "seamkiln"


def _require_qt():
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "the seamkiln shell needs PySide6 (LGPLv3). "
            "Install it with: uv pip install 'seamkiln[gui]'"
        ) from exc


class SeamkilnWindow:
    """A thin shell over a Session. Deliberately not a QMainWindow subclass -
    composition keeps the Qt objects at arm's length and the logic testable."""

    def __init__(self, session: Session | None = None, *, workdir: str | Path | None = None):
        _require_qt()
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import (
            QGraphicsScene,
            QGraphicsView,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QPlainTextEdit,
            QPushButton,
            QSplitter,
            QVBoxLayout,
            QWidget,
        )

        self.session = session or Session()
        self.workdir = Path(workdir or tempfile.mkdtemp(prefix="seamkiln-gui-"))
        self.window = QMainWindow()
        self.window.setWindowTitle(WINDOW_TITLE)
        self.window.resize(1280, 860)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.render_label = QLabel("no drape yet")
        self.render_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.render_label.setMinimumWidth(320)
        self.render_label.setStyleSheet("background:#2b2b2b;color:#bbb;")

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(190)

        buttons = QWidget()
        row = QHBoxLayout(buttons)
        row.setContentsMargins(0, 0, 0, 0)
        self._actions = [
            ("Tee block", lambda: Command("block", {"block": "tee"})),
            ("Seam allowance 10mm", lambda: Command("allowance", {"mm": 10.0})),
            ("Body", lambda: Command("body", {"kind": "mannequin"})),
            ("Arrange", lambda: Command("arrange", {"particle_distance_mm": 20.0})),
            ("Drape", lambda: Command("drape", {"fabric": "cotton_jersey", "frames": 200})),
            ("Fit report", lambda: Command("fit", {})),
        ]
        for label, factory in self._actions:
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, f=factory: self.run(f()))
            row.addWidget(button)
        save = QPushButton("Save script")
        save.clicked.connect(self.save_script)
        row.addWidget(save)

        left = QWidget()
        column = QVBoxLayout(left)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(buttons)
        column.addWidget(self.view, stretch=1)
        column.addWidget(self.log)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(self.render_label)
        splitter.setSizes([900, 380])
        self.window.setCentralWidget(splitter)
        self.refresh()

    # -- the only way anything changes ------------------------------------

    def run(self, command: Command) -> dict[str, Any]:
        """Apply a command through the session, then re-read it. No shortcuts."""
        try:
            result = self.session.apply(command)
        except CommandError as exc:
            self._say(f"! {command.op}: {exc}")
            return {"error": str(exc)}
        self._say(f"> {command.op} {json.dumps(command.args)}")
        self._say(f"  {json.dumps(result)[:400]}")
        self.refresh()
        if command.op == "drape":
            self.refresh_render()
        return result

    def refresh(self) -> dict[str, int]:
        from seamkiln.gui.scene import build_scene

        counts = build_scene(self.session, self.scene)
        if counts["panels"]:
            self.view.fitInView(self.scene.itemsBoundingRect(), _keep_aspect())
        summary = self.session.summary()
        self.window.setWindowTitle(
            f"{WINDOW_TITLE} - {summary.get('name', 'untitled')} "
            f"({summary.get('commands', 0)} commands)"
        )
        return counts

    def refresh_render(self) -> str | None:
        """Ask the preview lane for a picture. Absent Blender, say so in words."""
        from seamkiln.drape import preview

        if self.session.garment is None:
            return None
        ok, why = preview.available()
        if not ok:
            self.render_label.setText(f"no render:\n{why}")
            return None
        points = self.session.drape.points if self.session.drape else self.session.garment.points
        preview.render(
            self.workdir / "view",
            garment=preview.garment_mesh(points, self.session.garment.triangles),
            body=self.session.body,
            views={"front": (0.0, 5.0)},
            width=380,
            height=520,
        )
        image = self.workdir / "view_front.png"
        from PySide6.QtGui import QPixmap

        self.render_label.setPixmap(QPixmap(str(image)))
        return str(image)

    def save_script(self, path: str | Path | None = None) -> Path:
        destination = Path(path or (self.workdir / "session.json"))
        self.session.save_script(destination)
        self._say(f"= script saved: {destination} ({len(self.session.history)} commands)")
        return destination

    def _say(self, line: str) -> None:
        self.log.appendPlainText(line)

    def grab(self, path: str | Path) -> Path:
        """Save a picture of the window itself - how this GUI is tested."""
        destination = Path(path)
        self.window.grab().save(str(destination))
        return destination


def _keep_aspect():
    from PySide6.QtCore import Qt

    return Qt.AspectRatioMode.KeepAspectRatio


def main(argv: list[str] | None = None) -> int:
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication(argv or sys.argv)
    shell = SeamkilnWindow()
    shell.window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
