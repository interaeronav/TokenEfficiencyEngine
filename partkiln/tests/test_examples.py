"""The three example pipelines, run in `--probe` mode, in this process.

An example that does not run is documentation, not an example, so CI runs
all three end to end on every push. Probe mode is what makes that affordable
(under a second each on the A66 machine) - and the thing this file asserts
hardest is that a probe SAYS it is a probe, in words, in the manifest it
writes. A coarse run that reads like a delivered one is the failure this
whole convention exists to prevent.

In process, not by subprocess: `main(argv)` is the same entry point
`python -m examples.<name>` reaches, it costs no interpreter start-up, and a
traceback from inside the kernel arrives intact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytest.importorskip("OCP", reason="partkiln[brep] not installed")

# `examples/` sits beside `src/` and `tests/`, and only `src` is on the path
# (pyproject's `pythonpath`), so put the package root there for this file.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from examples.bracket.__main__ import main as bracket_main  # noqa: E402
from examples.shaft_housing.__main__ import main as shaft_main  # noqa: E402
from examples.sheet_bracket.__main__ import main as sheet_main  # noqa: E402

pytestmark = pytest.mark.brep

EXAMPLES = {
    "bracket": bracket_main,
    "shaft_housing": shaft_main,
    "sheet_bracket": sheet_main,
}


def _run(name: str, out: Path) -> dict[str, Any]:
    assert EXAMPLES[name](["all", "--out", str(out), "--probe"]) == 0
    return json.loads((out / "manifest.json").read_text())


@pytest.fixture(scope="module")
def manifests(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, Any]]:
    """Every example, once, in probe mode. Module-scoped: three runs, not nine."""
    root = tmp_path_factory.mktemp("examples")
    return {name: _run(name, root / name) for name in EXAMPLES}


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_a_probe_run_says_it_is_a_probe(name: str, manifests: dict[str, Any]) -> None:
    """The words are the assertion: a probe manifest disclaims its own numbers."""
    manifest = manifests[name]
    assert manifest["example"] == name
    assert manifest["probe"] is True
    note = manifest["note"]
    assert note.startswith("PROBE RUN:")
    assert "proves only that the pipeline runs" in note
    assert "no number in this manifest is evidence of the part" in note
    assert "Never rely on a coarse preview." in note


@pytest.mark.parametrize("name", sorted(EXAMPLES))
def test_a_full_run_carries_no_probe_note(name: str, tmp_path: Path) -> None:
    """The inverse, on the cheapest stage: only a probe is stamped as one."""
    assert EXAMPLES[name](["model", "--out", str(tmp_path)]) == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["probe"] is False
    assert "note" not in manifest


def test_the_bracket_reports_its_features_and_its_mass(manifests: dict[str, Any]) -> None:
    """W1's numbers, as this kernel actually builds it (chamfer before slot)."""
    manifest = manifests["bracket"]
    assert manifest["volume_mm3"] == pytest.approx(91159.605, abs=5e-4)
    assert manifest["mass_g"] == pytest.approx(715.603, abs=5e-4)
    assert manifest["bbox_mm"] == [120.0, 80.0, 10.0]
    deltas = {row["id"]: row["delta_mm3"] for row in manifest["features"]}
    assert deltas["feat:plate"] == pytest.approx(96000.0, abs=5e-4)
    assert deltas["feat:h"] == pytest.approx(-1368.478, abs=5e-4)
    # Law 13: the selectors say how many sub-shapes they caught.
    caught = {row["id"]: row["resolved"] for row in manifest["features"]}
    assert caught["feat:f1"]["plate:edges(dir=Z)"] == 4
    assert caught["feat:c1"]["plate:edges(of=end, loop=outer)"] == 8
    assert manifest["check"]["verdict"] == "pass"
    # Law 15: every dimension is read back from the model and agrees.
    assert all(dim["agree"] for dim in manifest["drawing"]["dimensions"])
    assert [dim["value_mm"] for dim in manifest["drawing"]["dimensions"]] == [
        120.0,
        80.0,
        6.6,
        100.0,
        50.0,
        10.0,
    ]
    # A probe skips the PDF and the STEP round trip; it must not pretend it did them.
    assert sorted(row["format"] for row in manifest["drawing"]["files"]) == ["dxf", "svg"]
    assert manifest["export"]["step_roundtrip"] is None
    assert manifest["export"]["deflection_mm"] == 0.5


def test_the_assembly_reports_dof_clearance_and_a_bom(manifests: dict[str, Any]) -> None:
    manifest = manifests["shaft_housing"]
    assert manifest["parts"]["housing"]["volume_mm3"] == pytest.approx(98385.784, abs=5e-4)
    assert manifest["parts"]["shaft"]["volume_mm3"] == pytest.approx(32986.723, abs=5e-4)
    # Six degrees of freedom, then two, then one: the constraints land in order.
    assert [step["dof"] for step in manifest["assemble"]["steps"]] == [0, 6, 2, 1]
    check = manifest["check"]
    assert check["dof"] == 1 and check["dof_by_component"] == {"shaft": 1}
    assert check["interference"] == []
    assert check["clearance_mm"] == pytest.approx(0.1, abs=1e-6)
    assert check["bom"]["total_g"] == pytest.approx(1031.274, abs=5e-4)
    assert manifest["export"]["step"]["products"] == 2
    assert manifest["export"]["poses_written"] is False


def test_the_sheet_bracket_reports_its_bend_table_and_layers(manifests: dict[str, Any]) -> None:
    """W3's pinned arithmetic: BA 4.524, BD 3.476, flat 96.524 at K 0.44."""
    manifest = manifests["sheet_bracket"]
    sheet = manifest["sheet"]
    assert sheet["ba_total_mm"] == 4.524 and sheet["bd_total_mm"] == 3.476
    assert sheet["flat_mm"] == [96.524, 50.0]
    assert sheet["folded_bbox_mm"] == [60.0, 50.0, 40.0]
    assert sheet["volume_delta_mm3"] == pytest.approx(18.85, abs=5e-4)
    (bend,) = manifest["bend_table"]
    assert (bend["ba_mm"], bend["ossb_mm"], bend["bd_mm"]) == (4.524, 4.0, 3.476)
    assert bend["zone_mm3"] == pytest.approx(471.239, abs=5e-4)
    assert manifest["flat_length_mm"] == 96.524
    assert manifest["flat"]["layers"] == ["OUTLINE", "BEND_UP", "BEND_DOWN", "HOLES"]
    assert manifest["flat"]["insunits"] == 4  # DXF says millimetres, out loud
    # The B-rep is the check on the arithmetic; they must agree exactly here.
    fold = manifest["fold"]
    assert fold["volume_brep_mm3"] == fold["volume_arithmetic_mm3"] == 9576.206


def test_a_later_stage_refuses_without_the_script_and_names_the_fix(tmp_path: Path) -> None:
    """Law 16 made runnable: the hand-off between stages IS the script."""
    with pytest.raises(SystemExit) as caught:
        bracket_main(["export", "--out", str(tmp_path)])
    assert "run `model` first" in str(caught.value)
