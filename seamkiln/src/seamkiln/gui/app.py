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
from collections.abc import Callable
from pathlib import Path
from typing import Any

from seamkiln.session import Command, CommandError, Session

WINDOW_TITLE = "seamkiln"

ActionFactory = Callable[[Session], Command]


# -- the buttons ---------------------------------------------------------------
#
# Law 3 of the A53 script: a button BUILDS A COMMAND, it never touches the
# garment. Each factory reads the session as it stands and returns the
# Command the button means, so the click and the script line are the same
# thing. Kept at module level and Qt-free so the table can be tested with no
# Qt installed - the follow-up verbs were script- and TEE-only for eleven
# campaigns because nothing exercised the shell on a machine without it.


def _opening(session: Session):
    """The seam a jacket opens on: the one declared a zipper or a placket."""
    if session.pattern is None:
        raise ValueError("no pattern yet: start from a block")
    for seam in session.pattern.seams:
        if getattr(seam, "kind", "plain") in ("zipper", "placket"):
            return seam
    raise ValueError(
        "this pattern has no opening: a zipper or placket seam is needed "
        "(the jacket-zip and jacket-placket blocks ship with one)"
    )


def _edge_point(session: Session, ref, along: float, inset_mm: float):
    """A flat-pattern point a fraction along an edge, moved into the panel."""
    panel = session.pattern.panel(ref.panel)
    outline = list(panel.outline)
    a = outline[ref.edge % len(outline)]
    b = outline[(ref.edge + 1) % len(outline)]
    x = a.x + (b.x - a.x) * along
    y = a.y + (b.y - a.y) * along
    minx, miny, maxx, maxy = panel.bbox
    cx, cy = (minx + maxx) / 2.0, (miny + maxy) / 2.0
    dx, dy = cx - x, cy - y
    norm = max((dx * dx + dy * dy) ** 0.5, 1e-9)
    return x + dx / norm * inset_mm, y + dy / norm * inset_mm


def _zip(session: Session) -> Command:
    opening = _opening(session)
    return Command("zip", {"opening": opening.id, "material": "metal", "size": 8.0, "frames": 120})


def _button(session: Session) -> Command:
    """One button a third of the way down the opening, hole on the other side."""
    opening = _opening(session)
    x, y = _edge_point(session, opening.a, 0.35, 14.0)
    hx, hy = _edge_point(session, opening.b, 0.35, 14.0)
    return Command(
        "button",
        {
            "panel": opening.a.panel,
            "x": round(x, 2),
            "y": round(y, 2),
            "hole_panel": opening.b.panel,
            "hole_x": round(hx, 2),
            "hole_y": round(hy, 2),
            "frames": 120,
        },
    )


def _walk(session: Session) -> Command:
    return Command("walk", {"gait": "walk", "cycles": 0.5, "fps": 8, "travel": True})


def _pull(session: Session) -> Command:
    """Grab the hem where it hangs lowest and pull it 60 mm outward."""
    if session.garment is None:
        raise ValueError("nothing to pull yet: arrange the garment first")
    points = session.drape.points if session.drape else session.garment.points
    hem = points[int(points[:, 1].argmin())]
    centre = points.mean(axis=0)
    away = hem - centre
    away[1] = 0.0
    norm = max(float((away * away).sum() ** 0.5), 1e-9)
    to = hem + away / norm * 0.06
    return Command(
        "pull",
        {
            "x": round(float(hem[0]), 4),
            "y": round(float(hem[1]), 4),
            "z": round(float(hem[2]), 4),
            "to_x": round(float(to[0]), 4),
            "to_y": round(float(to[1]), 4),
            "to_z": round(float(to[2]), 4),
            "radius_mm": 40.0,
            "steps": 12,
            "settle": 40,
        },
    )


ACTIONS: tuple[tuple[str, ActionFactory], ...] = (
    ("Tee block", lambda s: Command("block", {"block": "tee"})),
    ("Jacket block", lambda s: Command("block", {"block": "jacket-zip"})),
    ("Seam allowance 10mm", lambda s: Command("allowance", {"mm": 10.0})),
    ("Body", lambda s: Command("body", {"kind": "mannequin"})),
    ("Figure", lambda s: Command("body", {"kind": "figure", "stature_m": 1.80})),
    ("Arrange", lambda s: Command("arrange", {"particle_distance_mm": 20.0})),
    ("Drape", lambda s: Command("drape", {"fabric": "cotton_jersey", "frames": 200})),
    ("Fit report", lambda s: Command("fit", {})),
    ("Zip", _zip),
    ("Button", _button),
    ("Walk", _walk),
    ("Pull hem", _pull),
)

# The verbs the shell still has NO button for. Script- and TEE-driven only;
# recorded here (and in docs/seamkiln-lane.md) rather than implied covered.
VERBS_WITHOUT_A_BUTTON = (
    "animate",
    "cut",
    "delete",
    "ease",
    "export",
    "finish",
    "fold",
    "grade",
    "handoff",
    "lace",
    "load",
    "lock",
    "panel",
    "pinch",
    "rip",
    "seam",
    "techpack",
    "unfasten",
    "unlock",
    "unzip",
)


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
        self._actions = list(ACTIONS)
        for label, factory in self._actions:
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, f=factory: self.press(f))
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

    def press(self, factory: ActionFactory) -> dict[str, Any]:
        """A button: build the Command from the session as it is, then run it.

        A factory that cannot build its Command (a button on a garment that
        has no opening yet) says so in the log and changes nothing - the same
        contract as a refused command.
        """
        try:
            command = factory(self.session)
        except (CommandError, KeyError, ValueError, AttributeError) as exc:
            self._say(f"! {exc}")
            return {"error": str(exc)}
        return self.run(command)

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
