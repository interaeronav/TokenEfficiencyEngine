"""Executable teaching cards stay discoverable, offline and safe to revise."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fixtures_fusion import FakeFusionWire

from tee.adapters.fusion import codegen, guidance
from tee.adapters.fusion.adapter import FusionAdapter
from tee.kernel.errors import TeeError

TOPICS = ("cadagent_enclosure", "cadagent_flange", "cadagent_joint")


class NoWire:
    """A guide or its preflight must not depend on an installed/running Fusion."""

    def __getattr__(self, name: str) -> Any:
        pytest.fail(f"offline teaching accessed Fusion wire: {name}")


def test_index_discloses_three_lessons_without_reading_or_returning_their_ops(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_read(*args: Any, **kwargs: Any) -> str:
        pytest.fail("default guide loaded a detailed recipe")

    monkeypatch.setattr(Path, "read_text", no_read)
    index = FusionAdapter(NoWire()).guide()
    assert set(TOPICS) <= index["topics"].keys()
    assert "ops" not in index
    assert len(json.dumps(index)) < 1200


@pytest.mark.parametrize("topic", TOPICS)
def test_complete_creation_card_loads_offline_and_preflights(topic: str) -> None:
    adapter = FusionAdapter(NoWire())
    card = adapter.guide(topic)
    assert card["topic"] == topic
    assert card["title"] and card["intent"]
    assert card["ops"] and card["revision"]["ops"]
    assert card.get("expected") or card.get("checks")
    exports = card["exports"]
    assert {call["args"]["format"] for call in exports} == {"step", "f3d"}
    assert all("of" not in call["args"] for call in exports)
    adapter.preflight(card["ops"])
    compile(codegen.compile_batch(card["ops"]), f"<{topic}>", "exec")


@pytest.mark.parametrize("topic", TOPICS)
def test_mutating_nested_recipe_data_does_not_change_the_next_call(topic: str) -> None:
    adapter = FusionAdapter(NoWire())
    original = adapter.guide(topic)
    changed = adapter.guide(topic)
    changed["ops"][0]["props"].clear()
    changed["revision"]["ops"].clear()
    changed["units"]["length"] = "in"
    assert adapter.guide(topic) == original


@pytest.mark.parametrize("topic", ["../cadagent_enclosure", "recipes/cadagent_joint", "unknown"])
def test_unlisted_topics_fail_before_any_recipe_file_read(
    topic: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_read(*args: Any, **kwargs: Any) -> str:
        pytest.fail("an unlisted topic reached the filesystem")

    monkeypatch.setattr(Path, "read_text", no_read)
    with pytest.raises(TeeError) as error:
        FusionAdapter(NoWire()).guide(topic)
    assert error.value.code == "guide_topic"


def test_packaged_recipe_paths_do_not_depend_on_working_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    expected = {topic: guidance.guide(topic) for topic in TOPICS}
    monkeypatch.chdir(tmp_path)
    for topic in TOPICS:
        assert guidance.guide(topic) == expected[topic]


@pytest.mark.parametrize("topic", ["cadagent_enclosure", "cadagent_flange"])
def test_separate_parameter_revision_names_existing_drivers_without_stale_aliases(
    topic: str,
) -> None:
    adapter = FusionAdapter(NoWire())
    card = adapter.guide(topic)
    parameters = {op["name"] for op in card["ops"] if op.get("kind") == "param"}
    drivers: set[str] = set()
    for op in card["ops"]:
        props = op.get("props", {})
        if "expression" in props:
            drivers.add(props["expression"])
        drivers.update(dimension["expression"] for dimension in props.get("dims", []))
    revision = card["revision"]["ops"]
    assert {op["name"] for op in revision} <= parameters & drivers
    assert "@" not in json.dumps(revision)
    adapter.preflight(revision)


def test_joint_revision_requires_binding_a_returned_id_before_preflight() -> None:
    adapter = FusionAdapter(NoWire())
    card = adapter.guide("cadagent_joint")
    assert card["bindings"]["joint_id"]["kind"] == "joint"
    for phase in ("revision", "motion_probe"):
        ops = card[phase]["ops"]
        with pytest.raises(TeeError):
            adapter.preflight(ops)
        # This is a synthetic returned id for validation, never a live id guess.
        bound = json.loads(json.dumps(ops).replace("{{joint_id}}", "j731"))
        adapter.preflight(bound)
        assert all(op["id"] == "j731" for op in bound)
        assert "@" not in json.dumps(bound)


def test_enclosure_footprint_is_constrained_and_parameter_revision_drives_geometry() -> None:
    """A parameter declaration alone and dimension-only rectangles both mislead."""
    card = guidance.guide("cadagent_enclosure")
    shell_index = next(i for i, op in enumerate(card["ops"]) if op.get("kind") == "shell")
    adapter = FusionAdapter(FakeFusionWire())
    adapter.execute(card["ops"][:shell_index])
    entities = adapter.list_entities()
    footprint = next(entity for entity in entities if entity.kind == "sketch")
    body = next(entity for entity in entities if entity.kind == "body")
    assert footprint.summary["constrained"] is True
    assert body.summary["bbox_mm"] == pytest.approx(card["expected"]["bbox_mm"])

    adapter.execute(card["revision"]["ops"])
    revised = next(entity for entity in adapter.list_entities() if entity.kind == "body")
    assert revised.summary["bbox_mm"] == pytest.approx(card["revision"]["expected"]["bbox_mm"])
    assert revised.summary["bbox_mm"] != body.summary["bbox_mm"]
    sketch = next(op for op in card["ops"] if op.get("kind") == "sketch")
    constraints = sketch["props"].get("constraints", [])
    assert {"type": "coincident", "of": ["r0.bl", "origin"]} in constraints


def test_open_enclosure_holes_start_on_the_stable_exterior_floor() -> None:
    """The +z face after shelling is the rim, not a face covering the cavity."""
    ops = guidance.guide("cadagent_enclosure")["ops"]
    shell = next(op for op in ops if op.get("kind") == "shell")
    hole = next(op for op in ops if op.get("kind") == "hole")
    assert shell["props"]["remove_faces"] == ["+z"]
    assert hole["props"]["face"] == "-z"
    assert hole["props"]["through"] is True
    assert ops.index(hole) > ops.index(shell)
