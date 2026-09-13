"""F1-inspired lessons remain offline, executable and honest about their geometry."""

from __future__ import annotations

import importlib.util
import json
import math
import re
from pathlib import Path
from typing import Any

import pytest

from tee.adapters.fusion import codegen, guidance
from tee.adapters.fusion.adapter import FusionAdapter
from tee.kernel.errors import TeeError

TOPICS = ("cadagent_f1_wing", "cadagent_f1_brake", "cadagent_f1_wishbone")
PLACEHOLDER = re.compile(r"\{\{([a-z_]+)\}\}")


class NoWire:
    """Loading and validating a lesson never launches or contacts Fusion."""

    def __getattr__(self, name: str) -> Any:
        pytest.fail(f"offline F1 teaching accessed Fusion wire: {name}")


def test_index_discloses_f1_lessons_without_loading_their_geometry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_read(*args: Any, **kwargs: Any) -> str:
        pytest.fail("default guide loaded an F1 recipe")

    monkeypatch.setattr(Path, "read_text", no_read)
    card = FusionAdapter(NoWire()).guide()
    assert set(TOPICS) <= card["topics"].keys()
    assert "ops" not in card
    assert len(json.dumps(card)) < 1200


@pytest.mark.parametrize("topic", TOPICS)
def test_creation_cards_preflight_and_compile_without_fusion(topic: str) -> None:
    adapter = FusionAdapter(NoWire())
    card = adapter.guide(topic)
    assert card["topic"] == topic
    assert card["title"] and card["intent"]
    assert card["ops"] and card["revision"]["ops"]
    assert not PLACEHOLDER.search(json.dumps(card["ops"]))
    adapter.preflight(card["ops"])
    compile(codegen.compile_batch(card["ops"]), f"<{topic}>", "exec")
    assert {call["args"]["format"] for call in card["exports"]} == {"step", "f3d"}
    assert all("of" not in call["args"] for call in card["exports"])


@pytest.mark.parametrize("topic", TOPICS)
def test_cards_are_detached_and_do_not_depend_on_working_directory(
    topic: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = FusionAdapter(NoWire())
    original = adapter.guide(topic)
    changed = adapter.guide(topic)
    changed["ops"][0]["props"].clear()
    changed["revision"]["ops"].clear()
    monkeypatch.chdir(tmp_path)
    assert adapter.guide(topic) == original


@pytest.mark.parametrize("topic", TOPICS)
def test_parameter_revisions_reach_a_feature_or_sketch_driver(topic: str) -> None:
    card = guidance.guide(topic)
    declarations = {op["name"] for op in card["ops"] if op.get("kind") == "param"}
    drivers: set[str] = set()
    for op in card["ops"]:
        props = op.get("props", {})
        if op.get("op") == "set" and "expression" in props:
            drivers.update(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", props["expression"]))
        for dimension in props.get("dims", []):
            drivers.update(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", dimension["expression"]))
    revised = {op["name"] for op in card["revision"]["ops"] if op.get("op") == "param_set"}
    assert revised, "a useful revision changes a real driver, not only a label"
    assert revised <= declarations & drivers
    assert "@" not in json.dumps(card["revision"]["ops"])


@pytest.mark.parametrize("topic", ["cadagent_f1_brake", "cadagent_f1_wishbone"])
def test_separate_revisions_preflight_without_creation_batch_aliases(topic: str) -> None:
    card = guidance.guide(topic)
    ops = card["revision"]["ops"]
    assert not PLACEHOLDER.search(json.dumps(ops))
    FusionAdapter(NoWire()).preflight(ops)


def test_wing_stages_require_actual_occurrence_and_joint_bindings() -> None:
    adapter = FusionAdapter(NoWire())
    card = adapter.guide("cadagent_f1_wing")
    bindings = {"main_component": "c731", "flap_component": "c732", "wing_joint": "j733"}
    assert {name: row["kind"] for name, row in card["bindings"].items()} == {
        "main_component": "component",
        "flap_component": "component",
        "wing_joint": "joint",
    }
    for phase in ("assembly", "revision"):
        ops = card[phase]["ops"]
        serialized = json.dumps(ops)
        placeholders = set(PLACEHOLDER.findall(serialized))
        assert placeholders
        assert placeholders <= bindings.keys()
        with pytest.raises(TeeError):
            adapter.preflight(ops)
        # Synthetic returned IDs exercise the contract; no live ID is guessed.
        bound = json.loads(PLACEHOLDER.sub(lambda match: bindings[match.group(1)], serialized))
        adapter.preflight(bound)
        compile(codegen.compile_batch(bound), f"<wing-{phase}>", "exec")
        assert "@" not in json.dumps(bound)


def polygon_area(points: list[list[float]]) -> float:
    return (
        abs(
            math.fsum(
                a[0] * b[1] - b[0] * a[1]
                for a, b in zip(points, points[1:] + points[:1], strict=True)
            )
        )
        / 2
    )


@pytest.mark.parametrize("topic", ["cadagent_f1_wing", "cadagent_f1_wishbone"])
def test_authored_polylines_close_without_zero_edges_and_have_positive_area(topic: str) -> None:
    sketches = [
        op
        for op in guidance.guide(topic)["ops"]
        if op.get("kind") == "sketch" and op["props"].get("lines")
    ]
    assert len(sketches) >= 2
    for sketch in sketches:
        lines = sketch["props"]["lines"]
        points = [line[:2] for line in lines]
        for line, following in zip(lines, lines[1:] + lines[:1], strict=True):
            assert line[2:] == following[:2], f"{sketch['name']} has an open wire"
            assert line[:2] != line[2:], f"{sketch['name']} has a collapsed edge"
        assert len({tuple(point) for point in points}) == len(points)
        assert polygon_area(points) > 0


def test_wing_finite_trailing_edges_and_volumes_match_the_emitted_polygons() -> None:
    card = guidance.guide("cadagent_f1_wing")
    geometry = card["geometry"]
    panels = geometry["panels_per_surface"]
    for name, points in geometry["profiles_mm"].items():
        assert len(points) == 2 * panels + 1
        chord = max(point[0] for point in points) - min(point[0] for point in points)
        upper_te, lower_te = points[panels], points[panels + 1]
        assert upper_te[0] == lower_te[0] == max(point[0] for point in points)
        # Standard symmetric 0012 coefficients leave a nonzero trailing edge.
        assert upper_te[1] - lower_te[1] == pytest.approx(0.00252 * chord, abs=1e-8)
        area = polygon_area(points)
        assert area == pytest.approx(geometry["section_area_mm2"][name], abs=1e-8)
        sketch = next(op for op in card["ops"] if op.get("name") == name + " section")
        assert [line[:2] for line in sketch["props"]["lines"]] == points
        for expected in (card["expected"], card["revision"]["expected"]):
            body = next(body for body in expected["bodies"] if body["name"] == name)
            assert body["volume_mm3"] == pytest.approx(area * expected["span_mm"])
            assert body["bbox_mm"][2] == expected["span_mm"]


def test_wing_span_revision_drives_both_components() -> None:
    card = guidance.guide("cadagent_f1_wing")
    extrusions = {op["as"]: op for op in card["ops"] if op.get("kind") == "extrude"}
    assert len(extrusions) == 2
    assert all(op["props"]["operation"] == "new_component" for op in extrusions.values())
    drives = {
        op["id"]: op["props"]["expression"]
        for op in card["ops"]
        if op.get("op") == "set" and "expression" in op["props"]
    }
    parameters = {drives[f"@{alias}.feature"] for alias in extrusions}
    assert len(parameters) == 1
    assert parameters <= {
        op["name"] for op in card["revision"]["ops"] if op.get("op") == "param_set"
    }
    initial, revised = card["expected"], card["revision"]["expected"]
    assert revised["total_volume_mm3"] / initial["total_volume_mm3"] == pytest.approx(
        revised["span_mm"] / initial["span_mm"]
    )


def test_wishbone_through_cut_and_stock_share_the_revised_depth_driver() -> None:
    card = guidance.guide("cadagent_f1_wishbone")
    extrusions = {op["as"]: op for op in card["ops"] if op.get("kind") == "extrude"}
    drives = {
        op["id"]: op["props"]["expression"]
        for op in card["ops"]
        if op.get("op") == "set" and "expression" in op["props"]
    }
    stock = next(alias for alias, op in extrusions.items() if "operation" not in op["props"])
    cut = next(alias for alias, op in extrusions.items() if op["props"].get("operation") == "cut")
    assert drives[f"@{stock}.feature"] == drives[f"@{cut}.feature"]
    assert drives[f"@{stock}.feature"] in {op["name"] for op in card["revision"]["ops"]}
    for expected in (card["expected"], card["revision"]["expected"]):
        web = expected["web"]
        assert polygon_area(web["outer_vertices_xy_mm"]) == web["outer_area_mm2"]
        assert polygon_area(web["aperture_vertices_xy_mm"]) == web["aperture_area_mm2"]
        assert web["remaining_area_mm2"] == web["outer_area_mm2"] - web["aperture_area_mm2"]
        for boss, hole in zip(expected["bosses"], expected["holes"], strict=True):
            assert boss["centre_xy_mm"] == hole["centre_xy_mm"]
            assert boss["diameter_mm"] > hole["counterbore_diameter_mm"] > hole["diameter_mm"]
            assert 0 < hole["counterbore_depth_mm"] < expected["bbox_mm"][2]


def test_brake_oracle_accounts_for_curved_channel_mouths_and_asymmetric_revision() -> None:
    card = guidance.guide("cadagent_f1_brake")
    initial, revised = card["expected"], card["revision"]["expected"]
    assert revised["volume_mm3"] < initial["volume_mm3"]
    assert initial["centre_of_mass_mm"][2] == pytest.approx(initial["bbox_mm"][2] / 2)
    assert revised["centre_of_mass_mm"][2] < initial["centre_of_mass_mm"][2]
    for expected in (initial, revised):
        removed = 0.0
        for row in expected["rows"]:
            radius = row["radius_mm"]
            lower, upper = row["wall_generator_length_range_mm"]
            actual = row["removed_volume_per_channel_mm3"]
            # Curved rims make the void longer off-axis; a straight length*area
            # oracle systematically understates the removed volume.
            assert math.pi * radius**2 * lower < actual < math.pi * radius**2 * upper
            removed += row["count"] * actual
            assert radius < min(row["centre_height_mm"], 28 - row["centre_height_mm"])
        assert expected["removed_volume_mm3"] == pytest.approx(removed)
        assert expected["volume_mm3"] == pytest.approx(expected["stock_volume_mm3"] - removed)


@pytest.mark.parametrize("name", ["wing", "brake", "wishbone"])
def test_packaged_recipe_matches_its_pure_generator(name: str) -> None:
    repo = Path(__file__).resolve().parents[2]
    generator = repo / "benchmarks" / "fixtures" / f"generate_f1_{name}.py"
    spec = importlib.util.spec_from_file_location(f"f1_fixture_{name}", generator)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    packaged = json.loads(
        (repo / "server/src/tee/adapters/fusion/recipes" / f"cadagent_f1_{name}.json").read_text()
    )
    builder = module.build_recipe if name == "wing" else module.recipe
    assert builder() == packaged
