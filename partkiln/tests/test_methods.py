"""The kernel methods behind the fourteen `pk_*` tools (D9), through `call()`.

One door, fourteen backends: `probe verbs lint query measure check standards
materials bom export import script drawing flat`. What this file pins is the
contract the adapter's tools are thin wrappers over - the numbers (F1
59 214.602 mm3, M6 clearance 6.6 mm, the F6 BOM at 337.517 g), the shapes of
the answers (scalars, never geometry), the refusals (a D8 code with the fix),
and the one law that makes `lint` worth calling: it answers WITHOUT the
kernel, proved here by running it in a process where importing OCP raises.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from partkiln import document
from partkiln.client import LocalKernel, known_methods
from partkiln.document import CommandError, Document

SRC = Path(__file__).resolve().parents[1] / "src"

PARAMS = {"op": "param_set", "props": {"W": "100mm", "H": "60mm"}}
SKETCH = {
    "op": "create",
    "kind": "sketch",
    "name": "base",
    "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "r"}]},
}


def kernel_with(commands: list[dict[str, Any]]) -> LocalKernel:
    kernel = LocalKernel(Document(name="methods"))
    if commands:
        kernel.apply(commands)
    return kernel


def f1_kernel() -> LocalKernel:
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_document_parts import F1

    return kernel_with(F1())


def f6_kernel(pins: int = 4) -> LocalKernel:
    pytest.importorskip("OCP", reason="partkiln[brep] not installed")
    from test_assembly_verbs import F6

    kernel = kernel_with(F6())
    kernel.apply([{"op": "create", "kind": "component", "props": {"part": "block"}}])
    for i in range(pins):
        kernel.apply(
            [
                {
                    "op": "create",
                    "kind": "component",
                    "name": f"pin{i + 1}",
                    "props": {"part": "pin", "at": [10 * i, 0, 40], "grounded": True},
                }
            ]
        )
    return kernel


# --------------------------------------------------------------------------- probe / verbs


def test_probe_names_the_kernel_the_formats_and_the_licences() -> None:
    out = kernel_with([PARAMS]).call("probe", {})
    assert out["alive"] is True and out["mode"] == "local"
    assert out["partkiln"] and out["python"].startswith("3.1")
    assert isinstance(out["ocp"], bool)
    assert "step" in out["formats"]["export"] and "glb" in out["formats"]["export"]
    assert set(out["formats"]["import"]) >= {"step", "brep", "iges"}
    assert set(out["formats"]["targets"]) == {"blender", "unreal", "godot"}
    assert out["document"]["commands"] == 1
    assert any("LGPL" in line and "OCCT" in line for line in out["licence"])
    assert out["phases"]["parts"] is True
    assert "lint" in out["methods"] and "export" in out["methods"]


def test_every_registered_kind_has_an_example_in_verbs() -> None:
    out = kernel_with([]).call("verbs", {})
    assert set(out["kinds"]) == set(document.KINDS)
    assert set(out["verbs"]) >= set(document.VERBS) | {"export", "check"}
    for kind, row in out["kinds"].items():
        example = row["example"]
        assert example["op"] == "create" and example["kind"] == kind
        assert isinstance(example.get("props"), dict)
    # the ones the model reaches for first are documented, not generated
    for kind in ("extrude", "hole", "fillet", "component", "mate", "joint", "drawing"):
        assert out["kinds"][kind].get("documented") is not False
    assert out["kinds"]["fillet"]["required"] == ["edges"]
    assert out["units"]["length"] == "mm"
    assert set(out["methods"]) == set(known_methods())


# --------------------------------------------------------------------------- lint


BAD_BATCH: list[dict[str, Any]] = [
    {"op": "create", "kind": "part", "name": "bracket"},
    {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "base", "distance": "10 smoots"},
    },
    {"op": "create", "kind": "fillet", "name": "f1", "props": {"r": "2mm"}},
    {
        "op": "create",
        "kind": "hole",
        "name": "h",
        "props": {"on": "gone.end", "at": [[1, 1]], "dia": 6},
    },
    {"op": "export", "props": {"format": "dwg", "out": "x.dwg"}},
]


def test_lint_catches_a_bad_unit_a_missing_prop_and_a_stale_ref() -> None:
    kernel = kernel_with([PARAMS, SKETCH])
    out = kernel.call("lint", {"commands": BAD_BATCH})
    assert out["ok"] is False and out["kernel_called"] is False
    codes = {(issue["index"], issue["code"]) for issue in out["issues"]}
    assert (1, "pk_unit_unknown") in codes  # "10 smoots" is not a length
    assert (2, "pk_needs") in codes  # a fillet without edges (design intent)
    assert (3, "pk_ref_unknown") in codes or (3, "pk_ref_stale") in codes
    assert (4, "pk_bad_op") in codes  # partkiln does not write DWG
    for issue in out["issues"]:
        assert issue["fix"], f"{issue['code']} came without a fix"
    assert out["needs"] and len(out["needs"]) <= 3
    assert kernel.document.history and len(kernel.document.history) == 2  # nothing applied


def test_lint_predicts_the_sketch_dof_before_the_batch_runs() -> None:
    kernel = kernel_with([PARAMS])
    out = kernel.call(
        "lint",
        {
            "commands": [
                {
                    "op": "create",
                    "kind": "sketch",
                    "name": "s",
                    "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "r"}]},
                }
            ]
        },
    )
    assert out["ok"] is True
    assert out["sketches"] == [
        {"index": 0, "name": "s", "dof": 0, "status": "ok", "closed": True, "entities": 8}
    ]


def test_lint_refuses_a_batch_that_is_not_a_list() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([]).call("lint", {})
    assert caught.value.code == "pk_needs" and "commands" in str(caught.value)


def test_lint_never_touches_the_kernel(monkeypatch: pytest.MonkeyPatch) -> None:
    """In-process spy: any route into the B-rep layer goes through
    `partkiln.brep.require_ocp`, and here it explodes."""
    import partkiln.brep as brep

    def boom() -> None:
        raise AssertionError("lint reached the kernel")

    monkeypatch.setattr(brep, "require_ocp", boom)
    monkeypatch.setattr(brep, "ocp_available", boom)
    out = kernel_with([PARAMS, SKETCH]).call("lint", {"commands": BAD_BATCH})
    assert out["kernel_called"] is False and out["issues"]


def test_lint_answers_in_a_process_where_importing_ocp_raises() -> None:
    """The honest spy: no OCP at all. `lint` is the pre-flight, so it has to
    answer on the interpreter that has not paid the 26 s import (Law 17)."""
    code = """
import json, sys
class _NoOCP:
    def find_spec(self, name, path=None, target=None):
        if name == "OCP" or name.startswith("OCP."):
            raise ImportError("OCP is blocked for this test")
        return None
sys.meta_path.insert(0, _NoOCP())
from partkiln.client import LocalKernel
from partkiln.document import Document
kernel = LocalKernel(Document())
kernel.apply(json.loads(sys.argv[1]))
out = kernel.call("lint", {"commands": json.loads(sys.argv[2])})
print(json.dumps({"issues": len(out["issues"]), "ok": out["ok"], "ocp": "OCP" in sys.modules}))
"""
    proc = subprocess.run(
        [sys.executable, "-c", code, json.dumps([PARAMS, SKETCH]), json.dumps(BAD_BATCH)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        check=True,
    )
    answer = json.loads(proc.stdout.strip().splitlines()[-1])
    assert answer == {"issues": 4, "ok": False, "ocp": False}


# --------------------------------------------------------------------------- query


@pytest.mark.brep
def test_query_resolves_a_selector_with_sub_shape_facts() -> None:
    kernel = f1_kernel()
    out = kernel.call("query", {"sel": "plate:edges(dir=Z)"})
    assert out["count"] == 4 and out["seam_excluded"] == 1
    assert out["kind"] == "edge" and out["part"] == "part:plate"
    assert all(fact["type"] == "line" and fact["length_mm"] == 10.0 for fact in out["facts"])
    face = kernel.call("query", {"sel": "plate.end"})
    assert face["count"] == 1 and face["facts"][0]["type"] == "plane"
    assert face["facts"][0]["area_mm2"] == pytest.approx(5921.460, abs=5e-4)


@pytest.mark.brep
def test_query_prints_the_tree_as_text() -> None:
    lines = f1_kernel().call("query", {"what": "tree"})["lines"]
    assert any(line.startswith("doc ") for line in lines)
    assert any("part:plate" in line and "59214.602" in line for line in lines)
    assert any("feat:hole1 hole ok" in line for line in lines)


@pytest.mark.brep
def test_query_changes_names_the_part_that_moved() -> None:
    kernel = f1_kernel()
    before = kernel.call("query", {"what": "changes"})
    assert before["parts"]["plate"] and before["commands"] == 4
    kernel.apply([{"op": "set", "id": "feat:hole1", "props": {"dia": 12}}])
    after = kernel.call("query", {"what": "changes", "since": before})
    assert after["equal"] is False and after["changed"] == ["part:plate"]
    same = kernel.call("query", {"what": "changes", "since": after})
    assert same["equal"] is True and same["changed"] == []


def test_query_needs_something_to_resolve() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([PARAMS]).call("query", {"what": "names"})
    assert caught.value.code == "pk_needs"


# --------------------------------------------------------------------------- measure


@pytest.mark.brep
def test_measure_mass_is_the_f1_arithmetic() -> None:
    out = f1_kernel().call("measure", {"what": "mass", "material": "steel_s275"})
    assert out["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert out["area_mm2"] == pytest.approx(15357.080, abs=5e-4)
    assert out["com_mm"] == [50.0, 30.0, 5.0]
    assert out["bbox_mm"] == [100.0, 60.0, 10.0]
    assert out["mass_g"] == pytest.approx(464.835, abs=5e-3)
    assert out["density_kg_m3"] == 7850.0 and out["honesty"] == "standard_value"
    assert "inertia_mm5" in out and out["source"] == "document"


@pytest.mark.brep
def test_measure_faces_counts_unique_sub_shapes_and_the_cylinders() -> None:
    out = f1_kernel().call("measure", {"what": "faces"})
    body = out["bodies"][0]
    assert body["faces"] == 7 and body["edges"] == 15 and body["solids"] == 1
    assert body["by_type"] == {"plane": 6, "cylinder": 1}
    assert body["cylinders"] == [{"dia_mm": 10.0, "faces": 1}]
    assert body["valid"] is True


@pytest.mark.brep
def test_measure_section_wall_and_bbox() -> None:
    kernel = f1_kernel()
    section = kernel.call("measure", {"what": "section", "at": "x=50"})
    assert section["area_mm2"] == pytest.approx(500.0, abs=1e-3)
    wall = kernel.call("measure", {"what": "wall", "limit_mm": 2})
    assert wall["ok"] is True and wall["min_mm"] >= 2.0
    box = kernel.call("measure", {"what": "bbox"})
    assert box["bbox_mm"] == [100.0, 60.0, 10.0]


@pytest.mark.brep
def test_measure_asm_interference_and_clearance_on_f6() -> None:
    kernel = f6_kernel(pins=1)
    asm = kernel.call("measure", {"what": "asm"})
    assert asm["components"] == 2 and asm["dof"] == 0
    rows = kernel.call("measure", {"what": "interference"})
    assert rows["interference"] == [] and rows["components"] == 2
    gap = kernel.call("measure", {"what": "clearance", "a": "cmp:block", "b": "cmp:pin1"})
    assert gap["mm"] == 20.0 and gap["contact"] is False


def test_measure_refuses_an_unknown_what_by_listing_them() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([PARAMS]).call("measure", {"what": "stress"})
    assert caught.value.code == "pk_bad_op" and "interference" in str(caught.value)


# --------------------------------------------------------------------------- check


@pytest.mark.brep
def test_check_passes_and_fails_a_spec_with_the_fix() -> None:
    kernel = f1_kernel()
    good = kernel.call(
        "check",
        {"spec": {"bbox": [100, 60, 10], "holes": [{"dia": 10, "count": 1}], "faces": 7}},
    )
    assert good["verdict"] == "pass" and good["violations"] == []
    assert good["checked"] == ["bbox", "holes", "faces"] and good["of"] == "part:plate"
    bad = kernel.call("check", {"spec": {"volume_mm3": [0, 100], "min_wall_mm": 20}})
    assert bad["verdict"] == "fail" and len(bad["violations"]) == 2
    for violation in bad["violations"]:
        assert {"rule", "got", "limit", "fix"} <= set(violation)
    with pytest.raises(CommandError) as caught:
        kernel.call("check", {"spec": {"volume_mm3": [0, 100]}, "strict": True})
    assert caught.value.code == "pk_spec_conflict" and "volume_mm3" in str(caught.value)


def test_check_needs_a_spec() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([PARAMS]).call("check", {})
    assert caught.value.code == "pk_needs" and "min_wall_mm" in str(caught.value)


# --------------------------------------------------------------------------- standards / materials


def test_standards_answers_m6_with_its_source_and_licence() -> None:
    kernel = kernel_with([])
    clearance = kernel.call("standards", {"what": "clearance", "size": "M6"})
    assert clearance["dia_mm"] == 6.6 and clearance["series"] == "normal"
    assert clearance["close_mm"] == 6.4 and clearance["loose_mm"] == 7.0
    assert "ISO 273" in clearance["authority"] and clearance["licence"]
    assert kernel.call("standards", {"what": "tap", "size": "M6"})["drill_mm"] == 5.0
    assert kernel.call("standards", {"what": "pitch", "size": "M6"})["pitch_mm"] == 1.0
    bolt = kernel.call("standards", {"what": "fastener", "standard": "ISO 4762", "size": "M6"})
    assert bolt["standard"] == "ISO 4762" and bolt["size"] == "M6"
    assert "ISO 4762" in kernel.call("standards", {"what": "list"})["standards"]


def test_standards_refuses_an_untabled_size_by_naming_the_nearest() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([]).call("standards", {"what": "clearance", "size": "M6.5"})
    assert "M6" in str(caught.value)


def test_materials_is_a_pure_lookup_with_an_honesty_tier() -> None:
    kernel = kernel_with([])
    listing = kernel.call("materials", {})
    assert listing["count"] >= 3
    assert any(row["name"] == "steel_s275" for row in listing["materials"])
    card = kernel.call("materials", {"name": "steel_s275"})
    assert card["values"]["density"] == 7850.0
    assert card["honesty"]["density"] == "standard_value"
    assert "EN 1993-1-1" in card["sources"]["E"]
    assert kernel.document.history == []  # a lookup mutates nothing


# --------------------------------------------------------------------------- bom


@pytest.mark.brep
def test_bom_of_the_block_and_four_pins_totals_337_517_g() -> None:
    out = f6_kernel(pins=4).call("bom", {})
    assert out["view"] == "parts" and out["count"] == 5
    rows = {row["part"]: row for row in out["rows"]}
    assert rows["block"]["qty"] == 1 and rows["block"]["mass_g"] == 238.869
    assert rows["pin"]["qty"] == 4 and rows["pin"]["mass_g"] == 24.662
    assert rows["pin"]["total_g"] == 98.648
    assert out["total_g"] == 337.517
    assert rows["block"]["material"] == "steel_s275"
    structured = f6_kernel(pins=4).call("bom", {"view": "structured"})
    assert len(structured["rows"]) == 5 and structured["total_g"] == 337.517


# --------------------------------------------------------------------------- export / import


@pytest.mark.brep
def test_export_step_round_trips_and_carries_a_manifest(tmp_path: Path) -> None:
    kernel = f1_kernel()
    out = kernel.call("export", {"format": "step", "out": str(tmp_path / "f1.step")})
    assert out["id"] == "export:f1.step" and out["bytes"] > 0
    assert out["file_schema"].count("AP242") == 1
    assert out["roundtrip"]["volume_ok"] is True and out["roundtrip"]["faces_ok"] is True
    manifest = out["manifest"]
    assert {
        "format": "step",
        "source_units": "mm",
        "source_up": "Z",
        "units": "mm",
        "declares_units": True,
        "up": "Z",
    }.items() <= manifest.items()


@pytest.mark.brep
def test_export_glb_is_metres_y_up_and_needs_no_transform_for_blender(tmp_path: Path) -> None:
    out = f1_kernel().call(
        "export", {"format": "glb", "out": str(tmp_path / "f1.glb"), "target": "blender"}
    )
    assert out["units"] == "m" and out["up"] == "Y"
    assert out["extents"] == pytest.approx([0.1, 0.01, 0.06], abs=1e-6)
    assert out["manifest"]["transform_needed"] is False
    assert out["manifest"]["units"] == "m" and out["manifest"]["target_units"] == "m"
    assert out["manifest"]["scale_from_mm"] == 0.001


@pytest.mark.brep
def test_export_refuses_a_format_it_does_not_write(tmp_path: Path) -> None:
    kernel = f1_kernel()
    with pytest.raises(CommandError) as caught:
        kernel.call("export", {"format": "dwg", "out": str(tmp_path / "x.dwg")})
    assert caught.value.code == "pk_bad_op" and "step" in str(caught.value)
    with pytest.raises(CommandError) as caught:
        kernel.call("export", {"format": "step"})
    assert caught.value.code == "pk_needs" and "out" in str(caught.value)


@pytest.mark.brep
def test_import_reads_that_step_back_as_a_part_in_the_script(tmp_path: Path) -> None:
    source = f1_kernel()
    written = source.call("export", {"format": "step", "out": str(tmp_path / "f1.step")})
    kernel = kernel_with([])
    out = kernel.call("import", {"path": written["path"], "part": "back"})
    assert out["part"] == "part:back" and out["feature"] == "feat:import"
    assert out["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert out["faces"] == 7 and out["solids"] == 1 and out["valid"] is True
    assert out["units"] == "MM"
    assert out["names"] == 7  # every face named by fingerprint
    names = set(kernel.document.parts["back"].inventory().face_names)
    assert "import.face[0]" in names
    # the import is a COMMAND, so the script replays it (Law 16)
    twin = Document.replay(json.loads(json.dumps(kernel.script())))
    assert twin.fingerprint() == kernel.fingerprint()


def test_import_refuses_a_format_it_cannot_read(tmp_path: Path) -> None:
    mesh = tmp_path / "part.stl"
    mesh.write_text("solid x\nendsolid x\n", encoding="utf-8")
    with pytest.raises(CommandError) as caught:
        kernel_with([]).call("import", {"path": str(mesh)})
    assert caught.value.code == "pk_bad_op" and "STEP" in str(caught.value)
    with pytest.raises(CommandError) as caught:
        kernel_with([]).call("import", {"path": str(tmp_path / "nope.step")})
    assert caught.value.code == "pk_needs"


# --------------------------------------------------------------------------- script


@pytest.mark.brep
def test_script_dumps_replays_and_compares() -> None:
    kernel = f1_kernel()
    dump = kernel.call("script", {})
    assert dump["partkiln_script"] == 1 and dump["count"] == 4
    assert [c["op"] for c in dump["commands"]] == ["create"] * 4
    compared = kernel.call("script", {"what": "compare"})
    assert compared["equal"] is True and compared["changed"] == []
    assert compared["parts"]["plate"]["volume_mm3"] == pytest.approx(59214.602, abs=5e-4)
    assert kernel.call("script", {"what": "replay"})["committed"] is False


@pytest.mark.brep
def test_script_replays_a_family_with_overrides_without_touching_the_document() -> None:
    from test_document_parts import F2

    kernel = kernel_with(F2())
    before = kernel.fingerprint()
    out = kernel.call("script", {"what": "replay", "overrides": {"t": "8mm"}})
    assert out["equal"] is False
    assert out["parts"]["bracket"]["volume_mm3"] == pytest.approx(58403.27, abs=5e-3)
    assert kernel.fingerprint() == before and out["committed"] is False
    committed = kernel.call("script", {"what": "replay", "overrides": {"t": "8mm"}, "commit": True})
    assert committed["committed"] is True
    assert kernel.fingerprint() == committed["fingerprint"] != before
    assert kernel.document.parts["bracket"].volume() == pytest.approx(58403.27, abs=5e-3)


def test_script_refuses_an_override_no_param_set_sets() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([PARAMS]).call("script", {"what": "replay", "overrides": {"nope": 1}})
    assert caught.value.code == "pk_ref_unknown"


# --------------------------------------------------------------------------- the phase door


def test_an_unshipped_phase_refuses_by_naming_it() -> None:
    from partkiln.methods import _phase_method

    handler = _phase_method("flat", "partkiln.nosuchphase", "P5b (sheet metal)")
    with pytest.raises(CommandError) as caught:
        handler(kernel_with([]), {})
    assert caught.value.code == "pk_not_served"
    assert "P5b" in str(caught.value) and "partkiln.nosuchphase" in str(caught.value)


def test_an_unknown_method_lists_the_ones_that_answer() -> None:
    with pytest.raises(CommandError) as caught:
        kernel_with([]).call("stress", {})
    assert caught.value.code == "pk_bad_op"
    assert "measure" in str(caught.value) and "verbs" in str(caught.value)


@pytest.mark.brep
def test_an_imported_part_replays_in_a_fresh_process(tmp_path: Path) -> None:
    """A checkpoint is the script, and a script may be replayed anywhere - so
    `create import` has to be registered by the same lazy load every other
    kind is, not only by the door that served `pk_import`."""
    written = f1_kernel().call("export", {"format": "step", "out": str(tmp_path / "f1.step")})
    kernel = kernel_with([])
    kernel.call("import", {"path": written["path"], "part": "back"})
    script = tmp_path / "script.json"
    script.write_text(json.dumps(kernel.script()), encoding="utf-8")
    code = (
        "import sys\n"
        "from partkiln.document import Document\n"
        "doc = Document.replay(sys.argv[1])\n"
        "print(doc.fingerprint())\n"
        "print(round(doc.parts['back'].volume(), 3))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code, str(script)],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        check=True,
    )
    fingerprint, volume = proc.stdout.split()
    assert fingerprint == kernel.fingerprint()
    assert float(volume) == pytest.approx(59214.602, abs=5e-4)


@pytest.mark.brep
def test_check_over_the_assembly_reports_its_dof_and_interference() -> None:
    kernel = f6_kernel(pins=1)
    kernel.apply([{"op": "create", "kind": "object", "name": "brg", "props": {"part": "brg6204"}}])
    out = kernel.call("check", {"of": "asm", "spec": {"valid": True}, "no_interference": True})
    assert out["verdict"] == "pass" and out["of"] == "asm"
    assert out["asm"]["interference"] == 0 and out["asm"]["status"] in ("ok", "under")


@pytest.mark.brep
def test_a_virtual_component_is_counted_in_the_bom_without_a_mass() -> None:
    kernel = f6_kernel(pins=1)
    kernel.apply([{"op": "create", "kind": "object", "name": "brg", "props": {"part": "brg6204"}}])
    rows = {row["part"]: row for row in kernel.call("bom", {"view": "structured"})["rows"]}
    assert rows["brg6204"]["kind"] == "virtual" and rows["brg6204"]["mass_g"] == 0.0
    assert rows["block"]["mass_g"] == 238.869


def test_lint_walks_a_self_contained_batch_in_order() -> None:
    """The common case is a batch that defines everything it uses: the
    parameters in command 0, the sketch in 2, the face `plate.end` that
    command 3 will materialise. Calling that broken would make lint useless."""
    batch = [
        {"op": "param_set", "props": {"W": "120mm", "H": "80mm", "T": "10mm"}},
        {"op": "create", "kind": "part", "name": "bracket", "props": {"material": "steel_s275"}},
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
        },
        {
            "op": "create",
            "kind": "extrude",
            "name": "plate",
            "props": {"sketch": "base", "distance": "T"},
        },
        {
            "op": "create",
            "kind": "fillet",
            "name": "f1",
            "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
        },
        {
            "op": "create",
            "kind": "hole",
            "name": "h",
            "props": {"on": "plate.end", "at": [[20, 30]], "std": "M6 clearance normal"},
        },
        {"op": "export", "props": {"format": "step", "out": "out/bracket.step"}},
    ]
    out = kernel_with([]).call("lint", {"commands": batch})
    assert out["issues"] == [] and out["ok"] is True
    assert out["sketches"][0]["dof"] == 0
    # ...and a parameter the batch never defines is still caught
    broken = [
        {
            "op": "create",
            "kind": "extrude",
            "name": "p",
            "props": {"sketch": "s", "distance": "NOPE"},
        }
    ]
    codes = {i["code"] for i in kernel_with([]).call("lint", {"commands": broken})["issues"]}
    assert "pk_bad_expr" in codes
