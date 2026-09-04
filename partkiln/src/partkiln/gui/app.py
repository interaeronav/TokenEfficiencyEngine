"""The window. Qt lives here and nowhere else.

Every string this window shows is produced by a tested, Qt-free function on
`PartkilnShell` - the feature tree, the parameter table, the diff, the SVG.
Qt only places them. That is deliberate: PySide6 is not installed on the
machine that wrote this package, so any logic that lived in a widget would
have shipped unexercised, and `tests/test_gui.py` drives the whole shell with
Qt absent instead.

PySide6 is an EXTRA (LGPL-3.0, dynamically linked, never vendored - the same
posture `partkiln/pyproject.toml` takes with fpdf2). `import partkiln` must
work with no Qt installed, and a test asserts it.

There is no 3D viewport, by decision: see `preview.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from partkiln.document import CommandError
from partkiln.gui.shell import PartkilnShell

WINDOW_TITLE = "partkiln"
BUTTONS_PER_ROW = 8


def _require_qt() -> None:
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "the partkiln shell needs PySide6 (LGPL-3.0). "
            "Install it with: uv pip install 'partkiln[gui]'"
        ) from exc


def _svg_pane() -> Any:
    """A QSvgWidget when the Qt build has one, else a label that says so.

    QtSvg is a separate module in some PySide6 packagings, and a missing
    optional module should cost the preview pane, not the whole window.
    """
    try:
        from PySide6.QtSvgWidgets import QSvgWidget
    except ImportError:
        from PySide6.QtWidgets import QLabel

        label = QLabel("no QtSvg in this PySide6 build; the SVG files are in the working directory")
        label.setWordWrap(True)
        return label
    return QSvgWidget()


class PartkilnWindow:
    """A thin shell over a `PartkilnShell`. Composition, not a QMainWindow
    subclass: the Qt objects stay at arm's length and the logic stays testable."""

    def __init__(self, shell: PartkilnShell | None = None, *, workdir: str | Path | None = None):
        _require_qt()
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QFont
        from PySide6.QtWidgets import (
            QGridLayout,
            QMainWindow,
            QPlainTextEdit,
            QPushButton,
            QSplitter,
            QTableWidget,
            QVBoxLayout,
            QWidget,
        )

        self.shell = shell or PartkilnShell(workdir=workdir)
        self.window = QMainWindow()
        self.window.setWindowTitle(WINDOW_TITLE)
        self.window.resize(1360, 900)
        mono = QFont("Menlo")
        mono.setStyleHint(QFont.StyleHint.Monospace)

        buttons = QWidget()
        grid = QGridLayout(buttons)
        grid.setContentsMargins(0, 0, 0, 0)
        for index, control in enumerate(self.shell.controls):
            button = QPushButton(control.label)
            button.clicked.connect(lambda _=False, c=control: self.press(c))
            grid.addWidget(button, index // BUTTONS_PER_ROW, index % BUTTONS_PER_ROW)
        save = QPushButton("Save script")
        save.clicked.connect(lambda _=False: self.shell.save_script())
        grid.addWidget(save, len(self.shell.controls) // BUTTONS_PER_ROW, BUTTONS_PER_ROW - 1)

        self.tree = QPlainTextEdit()
        self.tree.setReadOnly(True)
        self.tree.setFont(mono)

        self.params = QTableWidget(0, 5)
        self.params.setHorizontalHeaderLabels(["name", "value", "unit", "expression", "used by"])
        self.params.setMaximumHeight(220)

        self.diff = QPlainTextEdit()
        self.diff.setReadOnly(True)
        self.diff.setFont(mono)

        self.preview = _svg_pane()
        self.preview.setMinimumWidth(420)

        left = QWidget()
        column = QVBoxLayout(left)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(buttons)
        column.addWidget(self.tree, stretch=1)
        column.addWidget(self.params)

        right = QSplitter(Qt.Orientation.Vertical)
        right.addWidget(self.preview)
        right.addWidget(self.diff)
        right.setSizes([560, 300])

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([820, 520])
        self.window.setCentralWidget(splitter)
        self.refresh()

    # -- the only way anything changes ------------------------------------------

    def press(self, control: Any) -> dict[str, Any]:
        """One button, one command, one repaint. A refusal repaints the log and
        leaves the preview showing what is still true."""
        result = self.shell.press(control)
        self.refresh()
        if "error" not in result:
            self.refresh_preview()
            self.refresh()  # the preview's own refusal, if it had one, is a log line
        return result

    def refresh(self) -> None:
        from PySide6.QtWidgets import QTableWidgetItem

        self.tree.setPlainText("\n".join(self.shell.tree_lines()))
        self.diff.setPlainText("\n".join(self.shell.log[-200:]))
        self.diff.verticalScrollBar().setValue(self.diff.verticalScrollBar().maximum())
        rows = self.shell.param_rows()
        self.params.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, key in enumerate(("name", "value", "unit", "expr", "used_by")):
                self.params.setItem(r, c, QTableWidgetItem(str(row.get(key, ""))))
        doc = self.shell.doc_row()
        self.window.setWindowTitle(
            f"{WINDOW_TITLE} - {doc.get('name', 'untitled')} "
            f"({doc.get('script_commands', 0)} commands, {doc.get('fingerprint', '-')})"
        )

    def refresh_preview(self) -> str | None:
        """The sheet if there is one, else the active sketch, else nothing.

        Both are SVG the kernel wrote; a refusal becomes words in the log, the
        same as a refused command.
        """
        try:
            source = (
                self.shell.render_drawing().read_text(encoding="utf-8")
                if self.shell.drawing_names()
                else self.shell.sketch_svg()
            )
        except CommandError as exc:
            self.shell.log.append(f"! [{exc.code}] preview: {exc}")
            return None
        loader = getattr(self.preview, "load", None)
        if loader is None:  # the QtSvg-less fallback label
            return source
        loader(source.encode("utf-8"))
        return source

    def grab(self, path: str | Path) -> Path:
        """Save a picture of the window itself - how a Qt shell is tested at all."""
        destination = Path(path)
        self.window.grab().save(str(destination))
        return destination


def main(argv: list[str] | None = None) -> int:
    _require_qt()
    from PySide6.QtWidgets import QApplication

    app = QApplication(argv or sys.argv)
    window = PartkilnWindow()
    window.shell.warm()
    window.refresh()
    window.window.show()
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
