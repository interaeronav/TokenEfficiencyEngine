"""The recorded acceptance session, executed as a test (A66 P6, A65 Law 19).

`partkiln/examples/acceptance/run_tee.py` is a SESSION, not a test: it drives
the whole lane through TEE's public surface in the order a model would work,
and prints every number it measured. This file runs that session and pins the
numbers, so the example cannot rot into a script that merely exits 0.

The split is deliberate. Everything that does not need a DCC runs in the
default suite from ONE `--probe` session (about 3 s), and the Blender handoff
runs under `-m dcc` as a second, complete session driven through the example's
own command line - which is also the only test of `--json`.

A number here that disagrees with `CLAUDE_A66_SCRIPT.md` is the measurement,
not a widened tolerance: the plan predicted the bracket at 91 158.6 mm3 from
hand arithmetic and the kernel measures 91 159.605 (the chamfer), and the
model is 12 mm thick from step 4 on because step 2 edits `T` and step 3 rolls
back to that edit rather than behind it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "partkiln" / "src"
EXAMPLE = REPO / "partkiln" / "examples" / "acceptance" / "run_tee.py"

# partkiln is deliberately NOT pip-installed into server/.venv (the dev route
# is `uv pip install -e partkiln`, and this repo IS that checkout), so its src
# goes on the path exactly as the editable install would put it there.
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

pytest.importorskip("partkiln", reason="partkiln/src is not beside server/")
if importlib.util.find_spec("OCP") is None:  # no import: the skip must beat the wheel
    pytest.skip("the OCP wheel is not in this interpreter", allow_module_level=True)
if not EXAMPLE.is_file():
    pytest.skip(f"{EXAMPLE} has not been written yet", allow_module_level=True)


def _example() -> Any:
    """Load the example by path - it is a script, not an installed module."""
    spec = importlib.util.spec_from_file_location("pk_acceptance_run_tee", EXAMPLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_tee = _example()


@pytest.fixture(scope="module")
def report(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    """One kernel-only session for the whole module: nine steps, ~3 s."""
    return run_tee.run(tmp_path_factory.mktemp("pk-acceptance"), probe=True)


def facts(report: dict[str, Any], step: int) -> dict[str, Any]:
    row = next(r for r in report["steps"] if r["step"] == step)
    assert not row.get("skipped"), f"step {step} was skipped: {row['skipped']}"
    return row["facts"]


# --------------------------------------------------------------------------- the session


def test_the_session_runs_every_step_but_the_dcc_handoff(report) -> None:
    assert [row["step"] for row in report["steps"]] == list(range(1, 11))
    skipped = [row["step"] for row in report["steps"] if row.get("skipped")]
    assert skipped == [7], skipped  # only the Blender step, and only under --probe
    total = report["totals"]
    assert total["steps_run"] == 9 and total["tokens"] > 0
    # The whole session is a handful of round trips, not a scene dump per step:
    # a ceiling nobody measures is one the next feature spends (hard rule 1).
    assert total["tokens"] < 12_000, total


def test_step_1_is_one_batch_and_one_diff_that_names_everything(report) -> None:
    got = facts(report, 1)
    assert got["created"] == [
        "part:bracket",
        "sk:base",
        "feat:plate",
        "feat:f1",
        "feat:h",
        "sk:slot_sk",
        "feat:slot",
        "feat:c1",
    ]
    assert got["features"] == {
        "feat:plate": [96_000.0, 6],
        "feat:f1": [-214.602, 10],
        "feat:h": [-1368.478, 14],
        "feat:slot": [-3062.655, 18],
        "feat:c1": [-194.661, 26],
    }
    assert got["part volume_mm3"] == pytest.approx(91_159.605, abs=1e-3)
    assert got["part mass_g"] == pytest.approx(715.603, abs=1e-3)
    assert got["part bbox_mm"] == [120.0, 80.0, 10.0]
    assert got["part faces/edges"] == [26, 64]
    # Law 19: the defaults are declared once, where they were taken.
    assert "feat:h" in got["assumed on"]
    # Law 13: a selector says what it resolved to, so nobody has to guess.
    assert got["resolved"]["feat:f1"] == {"plate:edges(dir=Z)": 4}
    assert got["resolved"]["feat:c1"] == {"plate:edges(of=plate.end, loop=outer)": 8}
    assert got["kernel OCCT"] == "7.9.3"
    # The 9-op batch and its whole answer, as a model would pay for them.
    assert got["batch tokens"] == pytest.approx(264, abs=40)
    assert got["diff tokens"] == pytest.approx(1106, abs=150)


def test_step_2_reports_the_blast_radius_and_not_the_new_world(report) -> None:
    got = facts(report, 2)
    assert [row.split()[0] for row in got["changed"]] == ["plate", "f1", "h", "slot"]
    assert got["unchanged"] == ["c1"] and got["failed"] == []
    assert got["volume_mm3"] == pytest.approx(109_430.458, abs=1e-3)
    assert got["param T"] == {"old": 10.0, "new": 12.0}
    assert "part:bracket" in got["diff_since modified"]
    assert "feat:c1" not in got["diff_since modified"]
    # Law 14 is also an economy: the edit costs ~11 tokens and the answer ~150.
    assert got["edit tokens"] < 30 and got["answer tokens"] < 400


def test_step_3_rolls_back_and_replays_in_a_real_subprocess(report) -> None:
    got = facts(report, 3)
    before, after = got["volume before/after rollback"]
    assert before == after == pytest.approx(109_430.458, abs=1e-3)
    assert got["fingerprint moved on edit"] is True
    assert got["fingerprint restored"] is True
    # The proof: the JSON alone, in an empty directory, in another process.
    assert got["replay fingerprint matches"] is True
    assert got["subprocess pid"] and got["subprocess spawn_s"] < 5.0
    assert got["subprocess replay_s"] < 30.0


def test_step_4_reads_its_dimensions_back_out_of_the_files(report) -> None:
    got = facts(report, 4)
    assert set(got["files"]) == {"svg", "dxf", "pdf"}
    assert got["sheet dims agree"] is True
    assert got["model bbox_mm"] == [120.0, 80.0, 12.0]
    # ezdxf, which never saw the model, measures the model's own numbers.
    assert got["DXF DIMENSION measurements"] == [12.0, 80.0, 120.0]
    assert got["DXF $INSUNITS"] == 4  # millimetres
    assert got["PDF mediabox_pt"] == [1190.55, 841.89]  # A3 landscape
    assert got["PDF pages"] == 1
    assert got["PDF text has 6.6"] and got["PDF text has ISO 273"]
    # The four M6 clearance holes are in the table with their standard note.
    assert [row[1] for row in got["hole table M6 rows"]] == [6.6, 6.6, 6.6, 6.6]
    assert all(row[2] == "THRU" for row in got["hole table M6 rows"])


def test_step_4_no_fillet_reaches_the_hole_table(report) -> None:
    """Using it found something testing it did not (A65 Law 19), and it is fixed.

    `hole_table` took every cylindrical face whose axis faced the view, with no
    concavity test, so the bracket's four convex r5 corner fillets printed as
    `4x d10` holes beside its four real M6 holes - ten rows for six features,
    and a note telling a shop to drill four holes that do not exist. The
    drawing now applies the same concavity test `checks/spec.py` uses.

    Five rows is the honest count: four M6 holes plus the slot, tabled as one
    slot. The slot's two end cylinders were two rows until they were paired
    (they ARE genuine concave cuts, so the old count was never a wrong number -
    just not how drafting practice dimensions a slot).
    """
    got = facts(report, 4)
    assert got["hole table rows"] == 5
    assert len(got["hole table M6 rows"]) == 4
    assert all(row[1] != 10.0 for row in got["hole table rows detail"]), got


def test_step_5_exports_declare_what_they_are(report) -> None:
    got = facts(report, 5)
    assert got["STEP schema"] == "AP242"
    assert got["STEP roundtrip"]["volume_ok"] is True
    assert got["STEP volume read back"] == pytest.approx(109_430.458, abs=1e-3)
    assert got["STEP vs kernel (rel)"] == 0.0
    assert got["GLB units/up"] == ["m", "Y"]  # glTF is Y-up and metres by spec
    # ... and the Z-up correction puts the 12 mm thickness back on Z.
    assert got["GLB probe dims_zup_m"] == [0.12, 0.08, 0.012]
    assert got["STL watertight/triangles"][0] is True
    assert got["STL declares units"] is False  # an STL declares nothing, and says so


def test_step_6_a_second_reader_agrees_with_the_kernel(report) -> None:
    got = facts(report, 6)
    assert got["relative difference"] < 1e-6
    assert got["cad_measure bbox"] == [120.0, 80.0, 12.0]
    assert got["cad_measure valid"] is True
    # Honest about what this is: one OCCT build, two readers. The genuinely
    # different kernel is FreeCAD's OCCT 7.8.1, and the session says whether
    # its bridge was up - it never starts one (the A37 bridge is GUI-bound).
    assert got["kernel OCCT"] == "7.9.3"
    assert isinstance(got["freecad"], str | dict)


def test_step_8_the_assembly_answers_dof_interference_and_a_bom(report) -> None:
    got = facts(report, 8)
    assert got["components"] == 2
    assert got["dof"] == 1  # insert + revolute on one axis pair
    assert got["status"] == "over" and got["redundant"] == ["ins"]
    assert got["residual"] == 0.0 and got["grounded"] == ["block"]
    assert got["interference (clean fit)"] == []
    # the deliberate overlap: a d11 pin in a d10 bore
    assert got["interference block/fat mm3"] == 329.867
    overlap = next(
        row for row in got["interference (d11 pin)"] if {row["a"], row["b"]} == {"block", "fat"}
    )
    assert overlap["centroid"] == [20.0, 20.0, 10.0]
    assert got["BOM total_g"] == pytest.approx(293.371, abs=1e-3)
    assert got["BOM partial"] is False
    assert len(got["BOM rows"]) == 3


def test_step_9_the_failing_spec_names_got_limit_and_fix(report) -> None:
    got = facts(report, 9)
    assert got["pass verdict"] == "pass"
    # an upper bound is not a proof, and the passing verdict says so
    assert any("upper bound" in note for note in got["pass unproven"])
    assert got["fail verdict"] == "fail"
    rules = {v["rule"]: v for v in got["fail violations"]}
    assert set(rules) == {"bbox", "mass_g"}
    assert rules["bbox"]["got"] == 12.0 and rules["bbox"]["limit"] == 10.0
    assert "change the Z extent" in rules["bbox"]["fix"]
    assert rules["mass_g"]["got"] == pytest.approx(859.029, abs=1e-3)
    assert "remove" in rules["mass_g"]["fix"]
    assert got["strict refusal"]["code"] == "pk_spec_conflict"
    assert got["strict refusal"]["fix"]


def test_step_10_sums_the_session(report) -> None:
    got = facts(report, 10)
    total = report["totals"]
    assert got["tokens total"] == total["tokens"] == total["tokens_in"] + total["tokens_out"]
    assert got["steps run"] == 9 and got["steps skipped"] == 1
    assert 0 < got["wall_s"] < 120  # the kernel-only session takes ~3 s here


# --------------------------------------------------------------------------- the DCC arm


@pytest.mark.dcc
@pytest.mark.timeout(300)
def test_the_full_session_hands_the_part_to_headless_blender(tmp_path) -> None:
    """The complete session through the example's own CLI, Blender included.

    Driven by `main()` so this also covers `--json`: the report a benchmark
    row is built from must be the same one the session printed.
    """
    if run_tee._find_blender() is None:
        pytest.skip("no Blender binary (set TEE_BLENDER)")
    out = tmp_path / "session"
    written = tmp_path / "report.json"
    assert run_tee.main(["--out", str(out), "--json", str(written)]) == 0
    report = json.loads(written.read_text(encoding="utf-8"))

    assert [row["step"] for row in report["steps"]] == list(range(1, 11))
    assert not [row for row in report["steps"] if row.get("skipped")]
    got = facts(report, 7)
    assert got["verify.ok"] is True
    assert got["scale band"] == "accept"
    assert got["read back dims_m"] == got["expected dims_m"] == [0.12, 0.08, 0.012]
    # Upright: the 12 mm thickness lands on Z. A glTF handed over without the
    # Z-up correction arrives lying on its side, and this is what catches it.
    assert got["entity dimensions_m"] == [0.12, 0.08, 0.012]
    assert got["entity summary"]["polys"] == 776
    assert got["bridge boot_s"] < 90.0
    assert report["totals"]["steps_run"] == 10
