"""Pin lane: tag encoding, and the tool logic driven against a fake editor.

The editor programs are generated text, so the fake below parses the payload
each program embeds and simulates the actor tags it would write. That covers
upsert-merge, list rows, and the fill loop without a running editor; the
programs themselves are exercised on hardware (see docs/PROGRESS.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.pins import model
from tee.pins.tools import register_pin_tools

NS = "okongo_pin"


# -- tag encoding ------------------------------------------------------------


def test_tags_round_trip_including_a_colon_inside_an_asset_key():
    pin = {
        "id": "market-03",
        "name": "Market stall 3",
        "category": "table",
        "notes": "North side; keep the walkway clear",
        "wishlist": ["market stall table", "wooden trestle"],
        "asset": "polyhaven:bar_chair_round_01",
        "filled_by": "PinFill_market-03",
    }
    tags = model.encode_tags(NS, pin)
    assert tags[0] == NS
    back = model.decode_tags(NS, tags)
    for key, value in pin.items():
        assert back[key] == value


def test_decode_ignores_actors_that_are_not_pins():
    assert model.decode_tags(NS, ["okongo_light", "okongo_circuit:LT-E1"]) is None


def test_foreign_tags_on_a_pin_survive_as_extra():
    back = model.decode_tags(NS, [NS, f"{NS}_id:x", "okongo_light"])
    assert back["extra_tags"] == ["okongo_light"]


def test_ids_are_lowercase_slugs_because_fname_compares_case_insensitively():
    assert model.validate_id("market-03") == "market-03"
    for bad in ("Market-03", "market 03", "", "a" * 49, "-lead"):
        with pytest.raises(TeeError) as exc:
            model.validate_id(bad)
        assert exc.value.code == "bad_pin_id"


def test_the_list_separator_is_rejected_in_free_text():
    with pytest.raises(TeeError) as exc:
        model.encode_tags(NS, {"id": "a", "notes": "one | two"})
    assert exc.value.code == "bad_pin_field"


def test_merge_keeps_unmentioned_fields_and_clears_explicit_empties():
    existing = {"id": "a", "name": "A", "notes": "keep", "wishlist": ["x"]}
    merged = model.merge(existing, {"wishlist": ["y"], "notes": ""})
    assert merged == {"id": "a", "name": "A", "notes": "", "wishlist": ["y"]}


def test_target_dims_round_trip_as_floats():
    tags = model.encode_tags(NS, {"id": "a", "target_dims": [0.45, 0.45, 0.9]})
    assert model.decode_tags(NS, tags)["target_dims"] == [0.45, 0.45, 0.9]


# -- fake editor -------------------------------------------------------------


def payload_of(code: str) -> dict:
    """Every program embeds its arguments as `_A = json.loads("...")`."""
    prefix = "_A = json.loads("
    line = next(ln for ln in code.splitlines() if ln.startswith(prefix))
    return json.loads(json.loads(line[len(prefix) : -1]))


class FakePinEditor(FakeAdapter):
    """FakeAdapter + the pin programs' editor-side effects."""

    def __init__(self) -> None:
        super().__init__()
        self.actors: dict[str, dict] = {}  # label -> {tags, loc_m, yaw}
        self.destroyed: list[str] = []

    def editor_python(self, code: str, label: str = "") -> dict:
        args = payload_of(code)
        if "mesh" in args:
            return self._upsert(args)
        if "remove_fill" in args:
            return self._remove(args)
        if set(args) == {"label_of_fill"}:
            return self._clear(args)
        rows = []
        for name, a in self.actors.items():
            if NS not in a["tags"]:
                continue
            pin_id = next((t.split(":", 1)[1] for t in a["tags"] if t.startswith(NS + "_id:")), "")
            rows.append(
                {
                    "label": name,
                    "tags": a["tags"],
                    # the READ program already reports the SPOT, not the
                    # marker centre, so this mirrors its output
                    "location_m": list(a["loc_m"]),
                    "yaw": a["yaw"],
                    "fill_present": ("PinFill_" + pin_id) in self.actors,
                }
            )
        return {"pins": rows}

    def _upsert(self, args: dict) -> dict:
        label = args["label"]
        created = label not in self.actors
        if created and args["location_cm"] is None:
            return {"error": "no_location"}
        actor = self.actors.setdefault(label, {"tags": [], "loc_m": [0, 0, 0], "yaw": 0.0})
        if args["location_cm"] is not None:
            actor["loc_m"] = [v / 100.0 for v in args["location_cm"]]
        if args["yaw"] is not None:
            actor["yaw"] = args["yaw"]
        actor["tags"] = list(args["tags"])
        return {
            "created": created,
            "label": label,
            "tags": actor["tags"],
            "location_m": actor["loc_m"],
            "yaw": actor["yaw"],
            "marker_base_z_m": actor["loc_m"][2],
            "marker_size_m": [0.18, 0.18, 0.5],
            "collision": "<CollisionEnabled.NO_COLLISION: 0>",
            "editor_only": True,
        }

    def _remove(self, args: dict) -> dict:
        label = f"Pin_{args['id']}"
        if label not in self.actors:
            return {"removed": False}
        del self.actors[label]
        fill = None
        if args["remove_fill"] and args["label_of_fill"] in self.actors:
            del self.actors[args["label_of_fill"]]
            fill = 1
        return {"removed": True, "label": label, "removed_fill": fill}

    def _clear(self, args: dict) -> dict:
        label = args["label_of_fill"]
        if label not in self.actors:
            return {"removed": 0}
        del self.actors[label]
        self.destroyed.append(label)
        return {"removed": 1}


@pytest.fixture()
def app(tmp_path: Path):
    dcc = FakePinEditor()
    app = TeeApp({"unreal": dcc}, project_root=tmp_path)
    app.config.pins = {"namespace": NS}
    register_pin_tools(app, tmp_path)
    return app


def call(app, _tool, **args):
    return app.registry.call(_tool, args)


# -- tools -------------------------------------------------------------------


def test_a_new_pin_needs_a_location_and_says_so(app):
    with pytest.raises(TeeError) as exc:
        call(app, "pin_set", id="market-03")
    assert exc.value.code == "pin_needs_location"
    assert "metres" in (exc.value.fix or "").lower()


def test_create_then_read_back_through_the_pin_tools(app):
    out = call(
        app,
        "pin_set",
        id="market-03",
        name="Market stall 3",
        category="table",
        notes="North side",
        wishlist=["market stall table"],
        location=[10.7, 15.1, 0.0],
        yaw=90.0,
    )
    assert out["created"] is True
    shown = call(app, "pin_show", id="market-03")["pin"]
    assert shown["name"] == "Market stall 3"
    assert shown["wishlist"] == ["market stall table"]
    assert shown["position_m"] == [10.7, 15.1, 0.0]
    assert shown["yaw"] == 90.0
    rows = call(app, "pin_list")
    assert rows["count"] == 1
    assert rows["pins"][0]["id"] == "market-03"
    assert "filled" not in rows["pins"][0]


def test_update_is_an_upsert_that_keeps_untouched_fields(app):
    call(app, "pin_set", id="p1", name="One", category="chair", location=[1, 2, 0])
    call(app, "pin_set", id="p1", notes="added later")
    pin = call(app, "pin_show", id="p1")["pin"]
    assert pin["name"] == "One" and pin["notes"] == "added later"
    assert pin["position_m"] == [1, 2, 0]


def test_unknown_pin_names_the_pins_that_do_exist(app):
    call(app, "pin_set", id="p1", location=[0, 0, 0])
    with pytest.raises(TeeError) as exc:
        call(app, "pin_show", id="nope")
    assert exc.value.code == "unknown_pin"
    assert "p1" in (exc.value.fix or "")


def test_pins_refuse_adapters_without_actor_tags(tmp_path: Path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    register_pin_tools(app, tmp_path)
    with pytest.raises(TeeError) as exc:
        app.registry.call("pin_list", {"adapter": "fake"})
    assert exc.value.code == "pins_unsupported_adapter"


# -- the fill loop -----------------------------------------------------------


def _stub_assets(app, *, hits, imported):
    app.registry.register(
        VirtualTool(
            "as_search",
            "stub",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "asset_class": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
            lambda args: {"results": {"model": hits}},
        )
    )
    calls: list[dict] = []

    def _import(args):
        calls.append(args)
        return imported

    app.registry.register(
        VirtualTool(
            "as_import",
            "stub",
            {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "adapter": {"type": "string"},
                    "asset_class": {"type": "string"},
                    "target_dims": {"type": "array"},
                    "location": {"type": "array"},
                    "name": {"type": "string"},
                },
            },
            _import,
        )
    )
    return calls


def test_fill_without_a_pick_returns_a_shortlist_from_the_wishlist(app):
    _stub_assets(
        app,
        hits=[
            {"id": "polyhaven:a", "name": "A", "license": "CC0-1.0", "dims_m": [1, 1, 1]},
            {"id": "polyhaven:a", "name": "A duplicate hit", "license": "CC0-1.0"},
        ],
        imported={},
    )
    call(app, "pin_set", id="p1", category="chair", wishlist=["stool", "bench"], location=[1, 2, 0])
    out = call(app, "pin_fill", id="p1")
    assert out["searched"] == ["stool", "bench"]
    assert [row["asset"] for row in out["shortlist"]] == ["polyhaven:a"]
    assert out["at_m"] == [1, 2, 0]


def test_fill_with_a_pick_imports_at_the_pin_and_records_the_key(app):
    calls = _stub_assets(
        app,
        hits=[],
        imported={
            "created": ["u9"],
            "scale_band": "accept",
            "license": "CC0-1.0",
            "checkpoint": "cp1",
            "verify": {"read_back": [0.5, 0.5, 0.9]},
        },
    )
    call(app, "pin_set", id="p1", category="chair", wishlist=["stool"], location=[1, 2, 0])
    out = call(app, "pin_fill", id="p1", pick="polyhaven:stool")
    assert calls[0]["location"] == [1, 2, 0]
    assert calls[0]["asset_class"] == "chair"
    assert calls[0]["name"] == "PinFill_p1"
    assert out["filled_with"] == "polyhaven:stool"
    pin = call(app, "pin_show", id="p1")["pin"]
    assert pin["asset"] == "polyhaven:stool"
    assert pin["filled_by"] == "PinFill_p1"
    row = call(app, "pin_list")["pins"][0]
    assert row["filled"] == "polyhaven:stool"


def test_refilling_clears_what_stood_there_before(app):
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    call(app, "pin_fill", id="p1", pick="polyhaven:one")
    app.adapter("unreal").actors["PinFill_p1"] = {"tags": [], "loc_m": [1, 2, 0], "yaw": 0.0}
    out = call(app, "pin_fill", id="p1", pick="polyhaven:two")
    assert out["replaced"] == "polyhaven:one"
    assert app.adapter("unreal").destroyed == ["PinFill_p1"]


def test_fill_clears_by_label_even_when_the_pin_has_no_record_of_it(app):
    """A recreated marker has no okongo_pin_asset tag, but the spot may still
    be occupied by an earlier fill - clearing must go by the label
    convention, or two props end up stacked (hit live on 2026-08-22)."""
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    dcc = app.adapter("unreal")
    dcc.actors["PinFill_p1"] = {"tags": [], "loc_m": [1, 2, 0], "yaw": 0.0}
    call(app, "pin_fill", id="p1", pick="polyhaven:one")
    assert dcc.destroyed == ["PinFill_p1"]


def test_fill_refuses_when_nothing_can_judge_the_scale(app):
    _stub_assets(app, hits=[], imported={})
    call(app, "pin_set", id="p1", category="market stall", location=[1, 2, 0])
    with pytest.raises(TeeError) as exc:
        call(app, "pin_fill", id="p1", pick="polyhaven:x")
    assert exc.value.code == "pin_no_scale_reference"
    assert "target_dims" in (exc.value.fix or "")


def test_target_dims_on_the_pin_are_passed_to_the_import(app):
    calls = _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", target_dims=[0.4, 0.4, 1.2], location=[1, 2, 0])
    call(app, "pin_fill", id="p1", pick="polyhaven:x")
    assert calls[0]["target_dims"] == [0.4, 0.4, 1.2]
    assert "asset_class" not in calls[0]


def test_fill_without_a_wishlist_says_how_to_give_it_one(app):
    _stub_assets(app, hits=[], imported={})
    call(app, "pin_set", id="p1", location=[1, 2, 0])
    with pytest.raises(TeeError) as exc:
        call(app, "pin_fill", id="p1")
    assert exc.value.code == "pin_no_wishlist"


def test_remove_leaves_the_placed_asset_unless_asked(app):
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    call(app, "pin_fill", id="p1", pick="polyhaven:x")
    dcc = app.adapter("unreal")
    dcc.actors["PinFill_p1"] = {"tags": [], "loc_m": [1, 2, 0], "yaw": 0.0}
    out = call(app, "pin_remove", id="p1")
    assert out["removed"] is True and out["removed_asset"] is None
    assert "PinFill_p1" in dcc.actors
    assert call(app, "pin_list")["count"] == 0


# -- export / import ---------------------------------------------------------


def test_export_writes_a_stable_sorted_snapshot(app, tmp_path: Path):
    call(app, "pin_set", id="b-pin", name="B", category="chair", location=[1, 2, 0])
    call(
        app,
        "pin_set",
        id="a-pin",
        name="A",
        category="table",
        notes="note",
        wishlist=["x", "y"],
        location=[3, 4, 0.5],
        yaw=90,
    )
    out = call(app, "pin_export")
    assert out["pins"] == 2
    doc = json.loads(Path(out["path"]).read_text())
    assert doc["version"] == 1 and doc["namespace"] == NS
    assert [p["id"] for p in doc["pins"]] == ["a-pin", "b-pin"]
    assert doc["pins"][0]["wishlist"] == ["x", "y"]
    assert doc["pins"][0]["position_m"] == [3, 4, 0.5]
    assert doc["pins"][0]["yaw"] == 90
    # exporting again writes the same bytes: this file lives in a repo
    before = Path(out["path"]).read_bytes()
    call(app, "pin_export")
    assert Path(out["path"]).read_bytes() == before


def test_import_restores_pins_a_level_rebuild_dropped(app):
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(
        app,
        "pin_set",
        id="p1",
        name="One",
        category="chair",
        wishlist=["stool"],
        location=[1, 2, 0],
    )
    call(app, "pin_fill", id="p1", pick="polyhaven:stool")
    path = call(app, "pin_export")["path"]

    dcc = app.adapter("unreal")
    dcc.actors.clear()  # the commandlet rebuilt the level from data files
    assert call(app, "pin_list")["count"] == 0

    out = call(app, "pin_import")
    assert out["restored"] == ["p1"] and out["filled"] == ["p1"]
    pin = call(app, "pin_show", id="p1")["pin"]
    assert pin["name"] == "One"
    assert pin["wishlist"] == ["stool"]
    assert pin["asset"] == "polyhaven:stool"
    assert pin["position_m"] == [1, 2, 0]
    assert Path(path).exists()


def test_import_does_not_re_place_a_prop_that_is_already_standing(app):
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    call(app, "pin_fill", id="p1", pick="polyhaven:stool")
    call(app, "pin_export")
    dcc = app.adapter("unreal")
    dcc.actors["PinFill_p1"] = {"tags": [], "loc_m": [1, 2, 0], "yaw": 0.0}
    dcc.destroyed.clear()

    out = call(app, "pin_import")
    assert out["filled"] == []
    assert out["already_standing"] == ["p1"]
    assert dcc.destroyed == []


def test_import_reports_pins_the_file_does_not_know_about(app):
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    call(app, "pin_export")
    call(app, "pin_set", id="p2", category="chair", location=[5, 6, 0])
    out = call(app, "pin_import", fill=False)
    assert out["in_level_not_in_file"] == ["p2"]
    assert out["updated"] == ["p1"]


def test_import_refuses_a_file_from_another_namespace(app, tmp_path: Path):
    path = tmp_path / "other.json"
    path.write_text(json.dumps({"version": 1, "namespace": "other_pin", "pins": []}))
    with pytest.raises(TeeError) as exc:
        call(app, "pin_import", path=str(path))
    assert exc.value.code == "pin_namespace_mismatch"


def test_import_refuses_a_future_file_version(app, tmp_path: Path):
    path = tmp_path / "v99.json"
    path.write_text(json.dumps({"version": 99, "namespace": NS, "pins": []}))
    with pytest.raises(TeeError) as exc:
        call(app, "pin_import", path=str(path))
    assert exc.value.code == "pin_file_version"


def test_import_says_where_the_missing_file_should_be(app):
    with pytest.raises(TeeError) as exc:
        call(app, "pin_import", path="nope/pins.json")
    assert exc.value.code == "pin_file_missing"
    assert "pin_export" in (exc.value.fix or "")


def test_list_flags_a_pin_whose_prop_is_gone(app):
    _stub_assets(app, hits=[], imported={"created": ["u9"]})
    call(app, "pin_set", id="p1", category="chair", location=[1, 2, 0])
    call(app, "pin_fill", id="p1", pick="polyhaven:stool")
    dcc = app.adapter("unreal")
    dcc.actors["PinFill_p1"] = {"tags": [], "loc_m": [1, 2, 0], "yaw": 0.0}
    assert "missing" not in call(app, "pin_list")["pins"][0]
    del dcc.actors["PinFill_p1"]
    assert call(app, "pin_list")["pins"][0]["missing"] is True


def test_a_marker_that_would_collide_is_refused(app):
    """A marker that blocks the player is worse than no marker."""
    dcc = app.adapter("unreal")
    original = dcc._upsert

    def colliding(args):
        out = original(args)
        out["collision"] = "<CollisionEnabled.QUERY_AND_PHYSICS: 3>"
        return out

    dcc._upsert = colliding
    with pytest.raises(TeeError) as exc:
        call(app, "pin_set", id="p1", location=[1, 2, 0])
    assert exc.value.code == "pin_marker_collides"
