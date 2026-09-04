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


# -- A66 defect fixes: regen, fingerprint, checkpoints, units -------------------


def test_regen_rebuilds_under_the_units_the_script_was_recorded_in() -> None:
    """DEFECT 1: a regen after `set doc units=in` rebuilt a DIFFERENT model.

    Law 16 - the checkpoint is the script - only holds if replaying the script
    replays its settings too. The commands were recorded in mm; a regen that
    reads today's document unit turns 100 into 100 in and still claims the
    fingerprint is a fingerprint.
    """
    doc = bracket()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "bare",
            "props": {"plane": "XY", "profile": {"rect": [100, 60]}},
        }
    )
    before = doc.fingerprint()
    coords = json.dumps(doc.sketches["bare"].coordinates(), sort_keys=True)
    doc.apply({"op": "set", "id": "doc", "props": {"units": "in"}})
    doc.regen()
    assert doc.units == "in"  # the recorded `set doc` still lands, last
    assert json.dumps(doc.sketches["bare"].coordinates(), sort_keys=True) == coords
    assert doc.fingerprint() == doc.regen()["fingerprint"]
    # and the same script replays to the same geometry in a fresh document
    twin = Document.replay(json.loads(json.dumps(doc.script())))
    assert json.dumps(twin.sketches["bare"].coordinates(), sort_keys=True) == coords
    # the pre-`set doc` fingerprint differs only by the recorded unit setting
    assert before != doc.fingerprint()
    doc.history.pop()  # drop the `set doc units=in`
    doc.regen()
    assert doc.units == "mm" and doc.fingerprint() == before


def test_regen_replays_a_document_built_in_inches_as_inches() -> None:
    """A document constructed in inches records its settings in the script, so
    neither `regen()` nor `replay()` silently re-reads it as millimetres."""
    doc = Document(name="imperial", units="in")
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "plate",
            "props": {"plane": "XY", "profile": {"rect": [4, 2]}},
        }
    )
    assert doc.sketches["plate"].coordinates()["rect.p2"] == [101.6, 50.8]
    before = doc.fingerprint()
    doc.regen()
    assert doc.sketches["plate"].coordinates()["rect.p2"] == [101.6, 50.8]
    twin = Document.replay(json.loads(json.dumps(doc.script())))
    assert twin.units == "in" and twin.fingerprint() == before


def test_a_failed_regen_leaves_the_document_whole(monkeypatch: pytest.MonkeyPatch) -> None:
    """DEFECT 2 (Law 16): a regen that fails mid-script used to truncate the
    history and lose the sketches - one bad edit lost the model."""
    doc = bracket()
    before = doc.fingerprint()
    calls = {"n": 0}
    real = document_module._VERBS["create"]

    def flaky(d, args, assumed):  # type: ignore[no-untyped-def]
        calls["n"] += 1
        if calls["n"] == 2:
            raise CommandError("the kernel says no", code="pk_op_failed")
        return real(d, args, assumed)

    monkeypatch.setitem(document_module._VERBS, "create", flaky)
    with pytest.raises(CommandError) as excinfo:
        doc.regen()
    assert sorted(doc.sketches) == ["base", "rib"]
    assert len(doc.history) == 3
    assert doc.params.names() == ["H", "W", "t"]
    assert doc.fingerprint() == before
    assert "create" in str(excinfo.value) and "rib" in str(excinfo.value)
    assert "Nothing was rebuilt" in str(excinfo.value)
    assert excinfo.value.code == "pk_op_failed"


def test_fingerprint_separates_sketches_that_solve_to_the_same_points() -> None:
    """DEFECT 3: the fingerprint hashed only the SOLVED coordinates, so a
    different entity kind, a different constraint or a different dimension
    that lands on the same points hashed identically - and the replay law's
    oracle claimed more than it checked."""

    def build(
        line: dict[str, object] | None = None,
        constraints: list[dict[str, object]] | None = None,
        dims: list[dict[str, object]] | None = None,
    ) -> Document:
        doc = Document(name="d")
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "name": "s",
                "props": {
                    "plane": "XY",
                    "entities": [
                        {"point": "p1", "at": [0, 0], "fixed": True},
                        {"point": "p2", "at": [10, 0]},
                        {"point": "p3", "at": [10, 5]},
                        line or {"line": "l1", "a": "p1", "b": "p2"},
                    ],
                    "constraints": constraints or [],
                    "dims": dims or [],
                },
            }
        )
        return doc

    plain = build()
    coords = plain.sketches["s"].coordinates()

    # (a) the same points, a different entity: construction, then a different span
    for other in (
        build({"line": "l1", "a": "p1", "b": "p2", "construction": True}),
        build({"line": "l1", "a": "p1", "b": "p3"}),
    ):
        assert other.sketches["s"].coordinates() == coords
        assert other.fingerprint() != plain.fingerprint()

    # (b) a constraint that is already satisfied moves nothing and is still a
    #     different model - drop it and the sketch is free to move.
    constrained = build(constraints=[{"c": "horizontal", "on": "l1"}])
    assert constrained.sketches["s"].coordinates() == coords
    assert constrained.fingerprint() != plain.fingerprint()

    # (c) a dimension at the value the geometry already has, and the same
    #     dimension made driven (a reference, not a driver).
    driving = build(dims=[{"d": "len", "on": "l1", "value": 10}])
    driven = build(dims=[{"d": "len", "on": "l1", "value": 10, "driven": True}])
    assert driving.sketches["s"].coordinates() == coords
    assert driven.sketches["s"].coordinates() == coords
    assert len({plain.fingerprint(), driving.fingerprint(), driven.fingerprint()}) == 3


def test_the_richer_fingerprint_still_matches_across_processes() -> None:
    """Rule 7: round before hashing, so a second interpreter agrees exactly."""
    doc = bracket()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "hole",
            "props": {"plane": "XZ", "profile": {"circle": "t*2", "at": [10, 10]}},
        }
    )
    code = (
        "import json, sys\n"
        "from partkiln.document import Document\n"
        "print(Document.replay(json.loads(sys.stdin.read())).fingerprint())\n"
    )
    root = Path(__file__).resolve().parents[1] / "src"
    out = subprocess.run(
        [sys.executable, "-c", code],
        input=json.dumps(doc.script()),
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin"},
        check=True,
    )
    assert out.stdout.strip() == doc.fingerprint(), out.stderr


def test_a_broken_checkpoint_file_refuses_with_a_code(tmp_path: Path) -> None:
    """DEFECT 4: a truncated, empty or foreign checkpoint raised
    JSONDecodeError/KeyError out of restore() - rule 6 says one short message
    with the fix, and D8 says it carries a code."""
    cases = {
        "empty.json": "",
        "half.json": '{"partkiln_snapshot": 1, "script": {"partkiln_scr',
        "nokey.json": '{"partkiln_snapshot": 1, "fingerprint": "0000000000000000"}',
        "foreign.json": "not json at all",
        "list.json": "[1, 2, 3]",
    }
    for name, text in cases.items():
        path = tmp_path / name
        path.write_text(text, encoding="utf-8")
        with pytest.raises(CommandError) as excinfo:
            Document.restore(path)
        assert excinfo.value.code == "pk_checkpoint_missing", name
        assert "tee_purge" in str(excinfo.value) or "new checkpoint" in str(excinfo.value), name
        assert name in str(excinfo.value), name

    # a file that DOES carry a script is restorable however odd its cache
    # section is: the script is the checkpoint, the B-rep is only a cache (D3).
    for junk in ('"parts": 7', '"parts": {"a": 7}'):
        path = tmp_path / "junk.json"
        path.write_text('{"script": {"partkiln_script": 1, "commands": []}, ' + junk + "}")
        assert Document.restore(path).restored_via == "replay"


def test_strict_units_refuses_a_bare_angle_in_degrees() -> None:
    """DEFECT 5: the refusal told the model to write millimetres for an ANGLE.

    Law 12 says a bare number is mm OR deg by kind; a fix that names the wrong
    kind costs a round trip and teaches the wrong lesson.
    """
    doc = Document()
    doc.apply({"op": "set", "id": "doc", "props": {"strict_units": True}})
    with pytest.raises(CommandError) as excinfo:
        doc.angle(90, {})
    message = str(excinfo.value)
    assert excinfo.value.code == "pk_unitless"
    assert "90deg" in message and "mm" not in message
    with pytest.raises(CommandError) as excinfo:
        doc.length(12, {})
    assert "12mm" in str(excinfo.value)


def test_sketch_origin_accepts_unit_strings() -> None:
    """DEFECT 6: origin: ['10mm', '20mm', 0] crashed with a raw ValueError.

    Every other length on the wire goes through the document's parser; this
    one did not, so a unit literal - the very thing Law 12 encourages - was a
    kernel error instead of a coordinate.
    """
    doc = Document()
    doc.apply(
        {
            "op": "create",
            "kind": "sketch",
            "name": "s",
            "props": {
                "plane": "on:plate.end",
                "origin": ["10mm", "2cm", 0],
                "profile": {"rect": [10, 10]},
            },
        }
    )
    assert doc.sketches["s"].plane == "on:plate.end@10,20,0"
    with pytest.raises(CommandError) as excinfo:
        doc.apply(
            {
                "op": "create",
                "kind": "sketch",
                "name": "bad",
                "props": {
                    "plane": "on:plate.end",
                    "origin": ["10 furlongs", 0, 0],
                    "profile": {"rect": [10, 10]},
                },
            }
        )
    assert excinfo.value.code == "pk_unit_unknown"
