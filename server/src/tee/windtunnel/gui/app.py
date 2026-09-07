"""The only module here that touches Qt, and it does so inside its functions.

`import tee.windtunnel.gui.app` must work with PySide6 absent - a test asserts
it - so every Qt import sits below a `_require_qt()` gate. The window holds a
`QMainWindow` rather than subclassing one, which keeps the Qt objects at arm's
length and the logic in `shell.py`, where it is tested.

Launch:

    uv pip install --python server/.venv/bin/python 'tee-engine[gui]'
    server/.venv/bin/python -m tee.windtunnel.gui.app --project ~/TEE

Nothing is registered as a console script and no tool is added: the always-
loaded surface is still 17. partkiln's law - a kernel that installs a window
on the PATH is not headless-first - holds for a lane too.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from tee.windtunnel.gui.actions import CONTROLS
from tee.windtunnel.gui.shell import WindTunnelShell

POLL_MS = 2000


def _require_qt() -> None:
    try:
        import PySide6  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "the wind-tunnel panel needs PySide6 (LGPL-3.0). Install it with: "
            "uv pip install 'tee-engine[gui]'"
        ) from exc


def build_app(project: Path, adapter: str = "fake") -> Any:
    """The same server a model drives, built headless for the window.

    The panel is a client of the registry, not a second implementation, so it
    goes through `cli` exactly as `tee serve` does - trust kernel, job manager
    and all.
    """
    from tee import cli
    from tee.kernel.adapter import FakeAdapter

    app = cli.build_app([cli.Lane(adapter, FakeAdapter())], str(project), allow_code_exec=False)
    cli._attach_windtunnel(app, str(project))
    return app


class WindTunnelWindow:
    """Composition, not inheritance: `self.window` is the QMainWindow."""

    def __init__(self, shell: WindTunnelShell) -> None:
        _require_qt()
        from PySide6.QtWidgets import (
            QHBoxLayout,
            QLabel,
            QListWidget,
            QMainWindow,
            QPlainTextEdit,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )

        self.shell = shell
        self.window = QMainWindow()
        self.window.setWindowTitle("TEE - wind tunnel")
        central = QWidget()
        outer = QHBoxLayout(central)

        self.cases = QListWidget()
        self.cases.currentTextChanged.connect(self._selected)
        outer.addWidget(self.cases, 1)

        right = QVBoxLayout()
        self.status = QLabel("no case selected")
        self.result = QLabel("")
        right.addWidget(self.status)
        right.addWidget(self.result)

        self.buttons: dict[str, QPushButton] = {}
        for control in CONTROLS:
            if control.key in ("refresh", "show", "status", "result"):
                continue
            b = QPushButton(control.label)
            b.setToolTip(control.hint)
            b.clicked.connect(lambda _=False, k=control.key: self._press(k))
            right.addWidget(b)
            self.buttons[control.key] = b

        self.out = QPlainTextEdit()
        self.out.setReadOnly(True)
        right.addWidget(self.out, 1)
        outer.addLayout(right, 2)
        self.window.setCentralWidget(central)
        self._refresh()
        self._start_clock()

    # -- the window's own plumbing, each line delegating to the shell --------

    def _refresh(self) -> None:
        self.cases.clear()
        for row in self.shell.cases():
            self.cases.addItem(row["case_id"])

    def _selected(self, case_id: str) -> None:
        if case_id:
            self._show(self.shell.select(case_id))

    def _press(self, key: str) -> None:
        if key == "cancel":
            self._show(self.shell.cancel())
        elif key.startswith("open_"):
            self._show(self.shell.hand_off("openvsp" if key.endswith("openvsp") else "paraview"))
        elif key == "run":
            self._show(self.shell.start_run())
        elif key == "mesh":
            self._show(self.shell.build_mesh())
        else:
            self._show(self.shell.call(key, case_id=self.shell.case_id))

    def _show(self, out: dict[str, Any]) -> None:
        if out.get("state") or out.get("target"):
            self.out.appendPlainText(self.shell.handoff_line(out))
        elif out.get("error"):
            self.out.appendPlainText(
                f"{out['error']}: {out.get('message', '')}\n{out.get('fix', '')}"
            )
        else:
            self.out.appendPlainText(str(out)[:2000])

    def _start_clock(self) -> None:
        from PySide6.QtCore import QTimer

        self.timer = QTimer(self.window)
        self.timer.timeout.connect(self._tick)
        self.timer.start(POLL_MS)

    def _tick(self) -> None:
        out = self.shell.poll()
        if out.get("status"):
            self.status.setText(self.shell.status_line(out["status"]))

    def show(self) -> None:
        self.window.show()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tee.windtunnel.gui.app", description=__doc__)
    parser.add_argument("--project", default=str(Path.home() / "TEE"), help="project folder")
    args = parser.parse_args(argv)
    _require_qt()
    from PySide6.QtWidgets import QApplication

    qt = QApplication(sys.argv[:1])
    window = WindTunnelWindow(WindTunnelShell(build_app(Path(args.project))))
    window.show()
    return int(qt.exec())


if __name__ == "__main__":  # pragma: no cover - the entry point itself
    raise SystemExit(main())
