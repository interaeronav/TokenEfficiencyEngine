"""The shell (A66 gap 1), driven end to end with PySide6 ABSENT.

PySide6 is not installed on this machine and was not installed to write the
package, which is the point: the controls, the routing, the diff formatting and
the SVG preview are all Qt-free, so this file exercises the whole shell without
it. What Qt adds is placement, and `test_the_window_needs_the_extra` pins the
one thing that fails without it.

The other two laws asserted here: `import partkiln` still loads neither Qt nor
OCP, and the list of things the shell does NOT do is checked against the
kernel's own verb, kind and method tables, so it cannot silently rot.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from partkiln import document
from partkiln.client import LocalKernel, known_methods
from partkiln.gui import actions
from partkiln.gui.actions import (
    CONTROLS,
    KINDS_WITHOUT_A_CONTROL,
    METHODS_THE_SHELL_DRIVES,
    METHODS_WITHOUT_A_CONTROL,
    VERBS_WITHOUT_A_CONTROL,
)
from partkiln.gui.shell import PartkilnShell


def _control(label: str) -> Any:
    return next(c for c in CONTROLS if c.label == label)


# -- the laws the extra exists to keep -----------------------------------------


def test_importing_partkiln_loads_neither_qt_nor_ocp() -> None:
    """A fresh interpreter, because `sys.modules` in this one is already dirty
    from the rest of the suite. The kernel is headless first (owner decision 2)
    and the GUI is a client added later; if importing the core dragged in Qt,
    the headless lane would be paying for a window nobody opened."""
    code = (
        "import sys, partkiln, partkiln.document, partkiln.client;"
        "assert 'PySide6' not in sys.modules, 'the core imported Qt';"
        "assert 'OCP' not in sys.modules, 'the core imported OCP';"
        "import partkiln.gui.actions, partkiln.gui.shell, partkiln.gui.preview;"
        "assert 'PySide6' not in sys.modules, 'the Qt-free shell imported Qt';"
        "assert 'OCP' not in sys.modules, 'the Qt-free shell imported OCP';"
        "print('clean')"
    )
    root = str(Path(__file__).resolve().parents[1] / "src")
    done = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": root, "PATH": "/usr/bin:/bin"},
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert "clean" in done.stdout


def test_the_window_needs_the_extra() -> None:
    """PySide6 is absent here, so the window refuses with the install line -
    the only failure Qt's absence is allowed to cause."""
    from partkiln.gui import app

    if "PySide6" in sys.modules:  # pragma: no cover - a machine that has the extra
        pytest.skip("PySide6 is installed here; the refusal cannot be observed")
    with pytest.raises(RuntimeError, match=r"partkiln\[gui\]"):
        app._require_qt()
    with pytest.raises(RuntimeError, match="PySide6"):
        app.main([])


# -- the gap list, asserted against the kernel's own tables ---------------------


def test_every_verb_kind_and_method_is_either_covered_or_listed() -> None:
    """The A65 lesson: what is not written down is assumed covered. A kind
    added to the kernel and to neither list fails this test the same day."""
    document.load_verb_modules()
    verbs, kinds = set(document.VERBS), set(document.KINDS)
    covered_verbs = {c.op for c in CONTROLS} & verbs
    covered_kinds = set(actions.covered_kinds())

    assert covered_verbs | set(VERBS_WITHOUT_A_CONTROL) == verbs
    assert not covered_verbs & set(VERBS_WITHOUT_A_CONTROL), "a verb is listed as both"
    assert covered_kinds | set(KINDS_WITHOUT_A_CONTROL) == kinds
    assert not covered_kinds & set(KINDS_WITHOUT_A_CONTROL), "a kind is listed as both"

    methods = set(known_methods())
    covered_methods = set(actions.covered_methods())
    assert covered_methods | set(METHODS_WITHOUT_A_CONTROL) == methods
    assert not covered_methods & set(METHODS_WITHOUT_A_CONTROL), "a method is listed as both"
    assert set(METHODS_THE_SHELL_DRIVES) <= methods


def test_the_coverage_numbers_are_the_ones_the_guide_prints() -> None:
    """Measured 2026-09-04: 4 of 4 verbs, 10 of 35 create kinds, 12 of 25
    kernel methods. Pinned so a new kind moves the number, not the claim."""
    coverage = actions.coverage()
    assert coverage["verbs"] == (4, 4)
    assert coverage["kinds"] == (10, 37)
    assert coverage["methods"] == (12, 25)


# -- the controls, without Qt ---------------------------------------------------


def test_a_control_builds_the_same_dict_the_batch_vocabulary_accepts() -> None:
    """D5 in one assertion: what a button emits is what `tee_batch` takes."""
    shell = PartkilnShell(LocalKernel())
    command = _control("Parameters").build(shell.state, shell.workdir)
    assert command == {"op": "param_set", "props": dict(actions.PARAMS)}
    parsed = document.Command.from_dict(command)
    assert parsed.op == "param_set" and parsed.args["W"] == "120mm"


def test_a_control_that_cannot_build_says_which_button_comes_first() -> None:
    """A refusal names the exact fix (rule 6) and changes nothing."""
    shell = PartkilnShell(LocalKernel())
    out = shell.press(_control("Sketch"))
    assert out["code"] == "pk_needs" and "press Parameters first" in out["error"]
    assert shell.kernel.document.history == []

    shell.press(_control("Parameters"))
    out = shell.press(_control("Extrude"))
    assert "no part yet: press New part." in out["error"]

    shell.press(_control("New part"))
    out = shell.press(_control("Extrude"))
    assert "no sketch yet: press Sketch first." in out["error"]


def test_the_mirror_control_asks_for_its_datum_plane() -> None:
    shell = PartkilnShell(LocalKernel())
    shell.press(_control("Parameters"))
    out = shell.press(_control("Mirror"))
    assert "press Midplane first" in out["error"]


def test_names_are_counted_not_reused() -> None:
    """Two presses of one button must not redefine the first feature."""
    shell = PartkilnShell(LocalKernel())
    shell.press(_control("Parameters"))
    first = _control("Sketch").build(shell.state, shell.workdir)
    shell.run(first)
    second = _control("Sketch").build(shell.state, shell.workdir)
    assert first["name"] == "sk1" and second["name"] == "sk2"


def test_the_geometry_controls_refuse_once_when_the_kernel_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No OCP wheel: the command mirror still answers, geometry says so."""
    import partkiln.brep as brep

    monkeypatch.setattr(brep, "ocp_available", lambda: False)
    shell = PartkilnShell(LocalKernel())
    assert shell.brep_available() is False
    assert "error" not in shell.press(_control("Parameters"))
    assert "error" not in shell.press(_control("New part"))
    assert "error" not in shell.press(_control("Sketch"))
    out = shell.press(_control("Extrude"))
    assert out["code"] == "pk_kernel_absent"
    assert "partkiln[brep]" in out["error"]
    assert shell.doc_row()["features"] == 0


def test_an_unknown_op_is_refused_by_the_kernels_own_tables() -> None:
    shell = PartkilnShell(LocalKernel())
    out = shell.run({"op": "sculpt", "props": {}})
    assert out["code"] == "pk_bad_op"
    assert "param_set" in out["error"] and "export" in out["error"]


# -- the whole v1 loop, one press at a time ------------------------------------


@pytest.mark.brep
def test_every_control_drives_the_v1_loop_and_the_diffs_are_the_kernels(
    tmp_path: Path,
) -> None:
    """Press all sixteen in order, headlessly, and assert the numbers the
    kernel answered with - not a re-read of the model afterwards."""
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    shell = PartkilnShell(LocalKernel(), workdir=tmp_path)

    assert "error" not in shell.press(_control("Parameters"))
    assert shell.press(_control("New part"))["id"] == "part:part1"
    sketch = shell.press(_control("Sketch"))
    assert sketch["id"] == "sk:sk1" and sketch["assumed"]["at"] == {"outer": [0, 0]}

    extrude = shell.press(_control("Extrude"))
    assert extrude["id"] == "feat:ex1"
    assert extrude["volume_mm3"] == pytest.approx(96000.0, abs=5e-4)
    assert extrude["faces"] == 6 and extrude["assumed"]["mode"] == "new"

    fillet = shell.press(_control("Fillet"))
    assert fillet["delta_mm3"] == pytest.approx(-214.602, abs=5e-4)
    assert fillet["faces"] == 10 and fillet["resolved"] == {"ex1:edges(dir=Z)": 4}

    hole = shell.press(_control("Hole"))
    assert hole["delta_mm3"] == pytest.approx(-342.119, abs=5e-4)
    assert "ISO 273" in hole["assumed"]["dia"] and hole["assumed"]["depth"] == "through"

    chamfer = shell.press(_control("Chamfer"))
    assert chamfer["delta_mm3"] == pytest.approx(-194.661, abs=5e-4)
    assert chamfer["resolved"] == {"ex1:edges(of=end, loop=outer)": 8}

    pattern = shell.press(_control("Pattern"))
    assert pattern["instances"] == 2 and pattern["assumed"]["layout"] == "rect"
    assert pattern["delta_mm3"] == pytest.approx(-342.119, abs=5e-4)

    assert shell.press(_control("Midplane"))["id"] == "plane:mid1"
    mirror = shell.press(_control("Mirror"))
    assert mirror["delta_mm3"] == pytest.approx(-342.119, abs=5e-4)
    assert mirror["volume_mm3"] == pytest.approx(94564.379, abs=5e-4)

    # `set` on a feature: the edit regenerates what depends on it and reports
    # every downstream feature's own delta.
    edited = shell.press(_control("Edit fillet"))
    assert edited["props"] == [{"key": "r", "old": "R", "new": "R*1.6"}]
    assert [row["feature"] for row in edited["changed"]] == ["fl1", "ch1"]
    assert edited["failed"] == []

    # `param_set` on W: the part family in one press.
    widened = shell.press(_control("Set W"))
    assert widened["changed"] == [{"name": "W", "old": 120.0, "new": 140.0}]
    regen = widened["regen"]["part:part1"]
    assert regen["changed"][0]["feature"] == "ex1"
    assert regen["changed"][0]["delta_mm3"] == pytest.approx(16000.0, abs=5e-4)

    checked = shell.press(_control("Check spec"))
    assert checked["verdict"] == "pass", checked.get("violations")
    assert set(checked["checked"]) >= {"bbox", "valid"}

    drawing = shell.press(_control("Draw sheet"))
    assert drawing["id"] == "dwg:sheet1" and drawing["views"] == 2
    assert [d["agree"] for d in drawing["dimensions"]] == [True, True, True]
    assert drawing["dimensions"][0]["value_mm"] == pytest.approx(140.0, abs=5e-4)

    exported = shell.press(_control("Export STEP"))
    assert exported["schema"] == "AP242" and exported["bytes"] > 1000
    assert Path(exported["path"]).is_file()

    deleted = shell.press(_control("Delete last"))
    assert deleted["deleted"] == ["feat:mr1"]

    # Every press landed as one script line, and the script rebuilds the model.
    script = json.loads(shell.save_script().read_text(encoding="utf-8"))
    ops = [c["op"] for c in script["commands"]]
    assert ops.count("create") == 10 and ops.count("param_set") == 2
    assert "set" in ops and "delete" in ops
    assert "check" not in ops and "export" not in ops  # reads and artefacts, not model
    replayed = document.Document.replay(script)
    assert replayed.fingerprint() == shell.fingerprint()


@pytest.mark.brep
def test_the_panes_show_the_kernels_own_rows(tmp_path: Path) -> None:
    """Tree, parameters and diff: D7 rows and the last answer, never a re-read."""
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    shell = PartkilnShell(LocalKernel(), workdir=tmp_path)
    for label in ("Parameters", "New part", "Sketch", "Extrude", "Fillet"):
        shell.press(_control(label))

    tree = shell.tree_lines()
    assert any(line.startswith("part:part1") for line in tree)
    assert any("feat:ex1" in line and "extrude" in line for line in tree)
    assert any("sk:sk1" in line and "dof 0 ok" in line for line in tree)

    names = [row["name"] for row in shell.param_rows()]
    assert names == sorted(actions.PARAMS)
    assert next(r for r in shell.param_rows() if r["name"] == "R")["used_by"] == 1

    diff = "\n".join(shell.diff_lines())
    assert "feat:fl1  fillet" in diff
    assert "delta -214.602 mm3" in diff
    assert "resolved ex1:edges(dir=Z) -> 4" in diff
    assert "fingerprint" in diff


@pytest.mark.brep
def test_the_preview_is_partkilns_own_svg(tmp_path: Path) -> None:
    """No second renderer: the sketch goes through the drawing writer's own
    element emitters, and the sheet pane shows the file the kernel wrote."""
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    shell = PartkilnShell(LocalKernel(), workdir=tmp_path)
    for label in ("Parameters", "New part", "Sketch"):
        shell.press(_control(label))

    svg = shell.sketch_svg()
    assert svg.startswith("<?xml") and svg.rstrip().endswith("</svg>")
    # 120 x 80 rectangle plus an 8 mm margin on each side, in sheet millimetres.
    assert 'width="136mm" height="96mm"' in svg
    assert svg.count("<line") == 4 and '<g class="visible">' in svg

    for label in ("Extrude", "Draw sheet"):
        shell.press(_control(label))
    sheet = shell.render_drawing()
    assert sheet.is_file() and sheet.name == "sheet1.svg"
    text = sheet.read_text(encoding="utf-8")
    assert 'width="420mm"' in text and "HOLE TABLE" not in text  # no holes pressed here
    # Deterministic: the same document draws the same bytes (rule 7).
    assert shell.render_drawing().read_text(encoding="utf-8") == text


def test_the_sketch_preview_refuses_on_a_kernel_that_has_no_document() -> None:
    """Solved coordinates are not D7 rows and never will be (hard rule 1), so
    a remote kernel gets an honest refusal rather than a geometry channel."""

    class Remote:
        """The KernelClient surface the shell touches, minus `document`."""

        def __init__(self) -> None:
            self.inner = LocalKernel()

        def __getattr__(self, name: str) -> Any:
            if name == "document":
                raise AttributeError(name)
            return getattr(self.inner, name)

    shell = PartkilnShell(Remote())
    shell.press(_control("Parameters"))
    shell.press(_control("Sketch"))
    with pytest.raises(document.CommandError, match="in-process kernel") as excinfo:
        shell.sketch_svg()
    assert excinfo.value.code == "pk_not_served"


def test_an_empty_shell_previews_nothing_and_says_so() -> None:
    shell = PartkilnShell(LocalKernel())
    with pytest.raises(document.CommandError, match="press Sketch"):
        shell.sketch_svg()
    with pytest.raises(document.CommandError, match="press Draw sheet"):
        shell.render_drawing()
    assert shell.tree_lines() == ["empty document"]
    assert shell.diff_lines() == ["nothing applied yet"]
