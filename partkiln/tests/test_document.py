"""P1 acceptance for the document: commands, replay, fingerprints, the unit boundary."""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

import pytest

import partkiln.document as document_module
from partkiln.document import Command, CommandError, Document, register_verb

P1_VERBS = ("create", "delete", "param_set", "set")


def bracket() -> Document:
    doc = Document(name="bracket")
    doc.apply({"op": "param_set", "props": {"W": "120mm", "H": "80mm", "t": "6mm"}})
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "r"}]},
        }
    )
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "rib",
            "props": {"plane": "XZ", "profile": {"rect": ["W/2 - 5mm", "t"], "at": [0, "t"]}},
        }
    )
    return doc


# -- commands --------------------------------------------------------------------


def test_from_dict_tolerates_the_tee_wire_shape() -> None:
    cmd = Command.from_dict(
        {
            "op": "create",
            "kind": "sketch",
            "name": "base",
            "id": "sk:base",
            "props": {"plane": "XY"},
        }
    )
    assert cmd.op == "create"
    assert cmd.args == {"kind": "sketch", "name": "base", "id": "sk:base", "plane": "XY"}
    assert Command.from_dict(cmd.as_dict()) == cmd
    with pytest.raises(CommandError, match="no 'op'"):
        Command.from_dict({"kind": "sketch"})


def test_unknown_verb_lists_every_verb() -> None:
    doc = Document()
    with pytest.raises(CommandError) as excinfo:
        doc.apply({"op": "explode"})
    message = str(excinfo.value)
    for verb in P1_VERBS:
        assert verb in message
    assert excinfo.value.code == "pk_bad_op"
    assert set(P1_VERBS) <= set(document_module.VERBS)
    with pytest.raises(CommandError, match=r"creates: .*sketch"):
        doc.apply({"op": "create", "kind": "spaceship"})


def test_register_verb_extends_the_registry() -> None:
    @register_verb("_probe_test_verb")
    def _probe(doc, args, assumed):
        return {"ok": True}

    try:
        assert Document().apply({"op": "_probe_test_verb"}) == {"ok": True}
        assert "_probe_test_verb" in document_module.VERBS
    finally:
        del document_module._VERBS["_probe_test_verb"]


# -- sketches through the document ------------------------------------------------


def test_create_sketch_reports_and_never_returns_coordinates() -> None:
    doc = bracket()
    result = doc.apply(
        {"op": "create", "kind": "sketch", "props": {"plane": "XY", "profile": {"circle": 20}}}
    )
    assert result["id"] == "sk:sketch3"
    assert result["status"] == "ok"
    assert result["dof"] == 0
    assert result["closed"] is True
    assert result["area_mm2"] == pytest.approx(314.159, abs=1e-3)
    assert result["assumed"]["at"] == {"circle": [0, 0]}
    assert "solved" not in result
    summary = doc.summary()
    assert json.dumps(summary)  # serialisable
    assert summary["sketches"][0] == {
        "id": "sk:base",
        "plane": "XY",
        "dof": 0,
        "status": "ok",
        "closed": True,
    }
    assert "coords" not in json.dumps(summary)


def test_bare_numbers_echo_units_once() -> None:
    doc = Document()
    first = doc.apply(
        {"op": "create", "kind": "sketch", "props": {"plane": "XY", "profile": {"rect": [12, 8]}}}
    )
    assert first["assumed"]["units"] == "mm"
    second = doc.apply(
        {"op": "create", "kind": "sketch", "props": {"plane": "XY", "profile": {"rect": [12, 8]}}}
    )
    assert "units" not in second.get("assumed", {})
    assert doc.sketches["sketch1"].point("rect.p1").x == 12.0


def test_document_units_apply_to_bare_numbers() -> None:
    doc = Document()
    result = doc.apply({"op": "set", "id": "doc", "props": {"units": "in"}})
    assert result["assumed"]["doc_defaults"]["units"] == "mm"
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {"plane": "XY", "profile": {"rect": [1, 2]}},
        }
    )
    assert doc.sketches["s"].point("rect.p2").y == pytest.approx(50.8)
    again = doc.apply({"op": "set", "id": "doc", "props": {"standard": "ANSI"}})
    assert "assumed" not in again
    assert doc.drawing_angle == "third"


def test_strict_units_refuses_bare_numbers() -> None:
    doc = Document()
    doc.apply({"op": "set", "id": "doc", "props": {"strict_units": True}})
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "props": {"plane": "XY", "profile": {"rect": [12, 8]}},
            }
        )
    assert excinfo.value.code == "pk_unitless"
    assert "12mm" in str(excinfo.value)
    assert doc.sketches == {}  # nothing landed


def test_unit_refusals_through_the_document() -> None:
    doc = Document()
    with pytest.raises(CommandError, match="Accepted length units"):
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "props": {"plane": "XY", "profile": {"rect": ["12 furlongs", 8]}},
            }
        )
    with pytest.raises(CommandError, match="angle, not a length"):
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "props": {"plane": "XY", "profile": {"rect": ["90deg", 8]}},
            }
        )
    with pytest.raises(CommandError, match="plane"):
        doc.apply({"op": "create", "kind": "sketch", "props": {"profile": {"rect": [1, 1]}}})
    with pytest.raises(CommandError, match=r"__import__|not allowed"):
        doc.apply({"op": "param_set", "props": {"W": "__import__('os')"}})


def test_set_on_a_sketch_dimension_resolves_and_reports_change() -> None:
    doc = bracket()
    result = doc.apply({"op": "set", "id": "sk:base", "props": {"r.w": "150mm"}})
    assert result["changed"] == [{"tag": "r.w", "old": 120.0, "new": 150.0}]
    assert result["status"] == "ok"
    assert doc.sketches["base"].point("r.p1").x == pytest.approx(150.0)
    assert doc.history[-1].op == "set"
    with pytest.raises(CommandError, match="Dimensions:"):
        doc.apply({"op": "set", "id": "sk:base", "props": {"nope": 1}})


def test_conflict_refuses_naming_both_dims_and_leaves_state_intact() -> None:
    doc = bracket()
    before = doc.fingerprint()
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "name": "bad",
                "props": {
                    "plane": "XY",
                    "profile": {"rect": [100, 60], "tag": "r"},
                    "dims": [{"d": "len", "on": "r.3", "value": 61, "tag": "d61"}],
                },
            }
        )
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_sketch_overconstrained"
    assert "r.h " in message and "d61 " in message
    assert "bad" not in doc.sketches
    assert doc.fingerprint() == before
    assert len(doc.history) == 3


def test_param_set_regenerates_dependent_sketches() -> None:
    doc = bracket()
    result = doc.apply({"op": "param_set", "props": {"W": "200mm"}})
    assert [c["name"] for c in result["changed"]] == ["W"]
    assert result["unchanged"] == 2
    assert [s["id"] for s in result["sketches"]] == ["sk:base", "sk:rib"]
    assert doc.sketches["base"].point("r.p1").x == pytest.approx(200.0)
    assert doc.sketches["rib"].point("rect.p1").x == pytest.approx(95.0)
    assert doc.params.used_by("W") == ["sk:base", "sk:rib"]
    assert doc.params.used_by("H") == ["sk:base"]


def test_delete_a_sketch_and_the_dependents_hook() -> None:
    doc = bracket()
    assert doc.dependents_of("sk:base") == []
    doc.dependency_sources.append(lambda d, i: ["feat:plate"] if i == "sk:base" else [])
    with pytest.raises(CommandError, match="feat:plate"):
        doc.apply({"op": "delete", "id": "sk:base"})
    assert doc.apply({"op": "delete", "id": "sk:rib"}) == {"deleted": "sk:rib", "sketches": 1}
    assert doc.params.used_by("t") == []
    with pytest.raises(CommandError, match="Sketches:"):
        doc.apply({"op": "delete", "id": "sk:rib"})


def test_explicit_entities_constraints_and_dims() -> None:
    doc = Document()
    result = doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "tri",
            "props": {
                "plane": "YZ",
                "entities": [
                    {"point": "a", "at": [0, 0], "fixed": True},
                    {"point": "b", "at": [30, 0]},
                    {"point": "c", "at": [0, 40]},
                    {"line": "ab", "a": "a", "b": "b"},
                    {"line": "bc", "a": "b", "b": "c"},
                    {"line": "ca", "a": "c", "b": "a"},
                ],
                "constraints": [{"c": "horizontal", "on": "ab"}, {"c": "vertical", "on": "ca"}],
                "dims": [
                    {"d": "len", "on": "ab", "value": "3cm"},
                    {"d": "len", "on": "ca", "value": 40},
                    {"d": "len", "on": "bc", "value": 1, "driven": True, "tag": "hyp"},
                ],
            },
        }
    )
    assert result["status"] == "ok" and result["dof"] == 0
    assert result["frame"] == "YZ"
    assert result["area_mm2"] == pytest.approx(600.0)
    assert result["driven"]["hyp"] == pytest.approx(50.0)


# -- script, replay, fingerprint ------------------------------------------------


def test_script_round_trip_and_save(tmp_path: Path) -> None:
    doc = bracket()
    script = doc.script()
    assert script["partkiln_script"] == 1
    assert len(script["commands"]) == 3
    path = doc.save_script(tmp_path / "bracket.json")
    twin = Document.replay(path)
    assert twin.fingerprint() == doc.fingerprint()
    assert twin.summary() == doc.summary()
    with pytest.raises(CommandError, match="script version"):
        Document.replay({"partkiln_script": 99})


def _random_script(seed: int) -> Document:
    rng = random.Random(seed)
    doc = Document(name=f"seed{seed}")
    doc.apply(
        {
            "op": "param_set",
            "props": {"t": f"{rng.randint(2, 12)}mm", "W": f"{rng.randint(50, 200)}mm"},
        }
    )
    for step in range(rng.randint(3, 8)):
        roll = rng.random()
        if roll < 0.3:
            doc.apply({"op": "param_set", "props": {"W": f"{rng.randint(50, 200)}mm"}})
        elif roll < 0.8 or not doc.sketches:
            kind = rng.choice(("rect", "circle", "slot", "polygon"))
            spec: dict = {"tag": f"x{step}", "at": [rng.randint(-50, 50), rng.randint(-50, 50)]}
            if kind == "rect":
                spec["rect"] = [rng.choice(["W", "t*4", rng.randint(10, 90)]), rng.randint(10, 90)]
            elif kind == "circle":
                spec["circle"] = rng.choice(["t*2", rng.randint(5, 40)])
            elif kind == "slot":
                spec["slot"] = [rng.randint(30, 80), rng.randint(5, 20)]
                spec["angle"] = rng.choice([0, 90, 30])
            else:
                spec["polygon"] = rng.randint(3, 8)
                spec["d"] = rng.randint(10, 60)
            doc.apply(
                {
                    "op": "create",
                    "kind": "sketch",
                    "props": {"plane": rng.choice(("XY", "XZ")), "profile": spec},
                }
            )
        else:
            name = rng.choice(sorted(doc.sketches))
            sketch = doc.sketches[name]
            dim = rng.choice(sketch.dims)
            doc.apply(
                {
                    "op": "set",
                    "id": f"sk:{name}",
                    "props": {dim.tag: dim.value * rng.choice([1.1, 1.5, 0.9])},
                }
            )
    return doc


@pytest.mark.parametrize("seed", range(20))
def test_replay_reproduces_the_fingerprint(seed: int) -> None:
    doc = _random_script(seed)
    twin = Document.replay(json.loads(json.dumps(doc.script())))
    assert twin.fingerprint() == doc.fingerprint()
    assert twin.summary() == doc.summary()


def test_replay_with_overrides_is_a_different_family_member() -> None:
    doc = bracket()
    family = Document.replay(doc.script(), overrides={"t": "8mm"})
    assert family.fingerprint() != doc.fingerprint()
    assert family.params.value("t") == 8.0
    assert family.sketches["rib"].point("rect.p2").y == pytest.approx(16.0)
    with pytest.raises(CommandError, match="no param_set in the script sets"):
        Document.replay(doc.script(), overrides={"zz": "1mm"})


def test_regen_rebuilds_to_the_same_fingerprint() -> None:
    doc = bracket()
    before = doc.fingerprint()
    result = doc.regen(from_index=1)
    assert result == {"reapplied": 2, "commands": 3, "fingerprint": before}
    assert len(doc.history) == 3


def test_fingerprint_sources_join_the_hash() -> None:
    doc = bracket()
    before = doc.fingerprint()
    doc.fingerprint_sources.append(lambda d: b"part:bracket")
    assert doc.fingerprint() != before
    assert len(doc.fingerprint()) == 16


def test_import_hygiene_with_ocp_absent() -> None:
    """`import partkiln` and every P1 module load with no OCP, tee, cadquery or Qt."""
    code = (
        "import sys\n"
        "import partkiln, partkiln.units, partkiln.params, partkiln.document\n"
        "import partkiln.sketch, partkiln.sketch.model, partkiln.sketch.solver\n"
        "import partkiln.sketch.presets, partkiln.data, partkiln.standards\n"
        "import partkiln.materials, partkiln.brep, partkiln._licences, partkiln._errors\n"
        "from partkiln.document import Document\n"
        "Document().apply({'op': 'create', 'kind': 'sketch', "
        "'props': {'plane': 'XY', 'profile': {'rect': [1, 1]}}})\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in "
        "('OCP', 'tee', 'cadquery', 'casadi', 'py_slvs', 'fpdf', 'vtkmodules', 'PySide6')]\n"
        "print(sorted(bad))\n"
    )
    root = Path(__file__).resolve().parents[1] / "src"
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"},
        check=True,
    )
    assert out.stdout.strip() == "[]", out.stdout
