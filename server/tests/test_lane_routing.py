"""A68: the batch router - no lane is the hub.

An omitted adapter= on a multi-lane server resolves by what the batch
CONTAINS: an entity id goes where the entity lives, a create goes where its
kind is made, any other verb goes where it is accepted. One lane that takes
every op wins and the reply says so; several refuse naming them unless a
default was declared; none refuse naming, per op, the lanes that would.
Single-lane servers never change a byte."""

from __future__ import annotations

import json

import anyio
import pytest
from mcp.client import Client
from mcp.types import TextContent

from tee.app import Route, TeeApp
from tee.kernel.adapter import FakeAdapter, LaneVocab
from tee.kernel.errors import TeeError
from tee.server import build_server


class Lane(FakeAdapter):
    """A fake that declares a vocabulary and refuses outside it, the way a
    real lane does."""

    def __init__(self, name, ops=("create", "set", "delete"), kinds=None, kind_optional=True):
        super().__init__()
        self._name = name
        self._vocab = LaneVocab(
            ops=ops, kinds=kinds, kind_optional=kind_optional, purpose=f"the {name} lane"
        )

    def info(self):
        base = super().info()
        base.id = self._name
        return base

    def vocab(self):
        return self._vocab

    def execute(self, batch):
        for i, op in enumerate(batch):
            if not self._vocab.accepts(op):
                raise TeeError(
                    "bad_op",
                    f"batch[{i}]: {self._name} has no {op.get('op')}/{op.get('kind')}.",
                    fix=f"{self._name} accepts: {', '.join(self._vocab.ops)}.",
                )
        return super().execute(batch)


class Mute(FakeAdapter):
    """Declares nothing: the kit's default for an adapter without vocab()."""

    vocab = None


def _desk(tmp_path, **kw) -> TeeApp:
    return TeeApp(
        {
            "blender": Lane(
                "blender", ops=("create", "set", "delete", "import_file"), kinds=("cube", "light")
            ),
            "partkiln": Lane(
                "partkiln",
                ops=("create", "set", "delete", "param_set", "export"),
                kinds=("part", "sketch", "extrude"),
                kind_optional=False,
            ),
            "seamkiln": Lane(
                "seamkiln",
                ops=("create", "set", "delete", "drape", "export"),
                kinds=("panel", "seam", "block"),
                kind_optional=False,
            ),
        },
        project_root=tmp_path,
        **kw,
    )


@pytest.fixture
def desk(tmp_path):
    app = _desk(tmp_path)
    yield app
    app.shutdown()


PART = [{"op": "create", "kind": "part", "name": "bracket"}]
PANEL = [{"op": "create", "kind": "panel", "name": "front"}]


def test_an_explicit_adapter_is_honoured_as_given(desk):
    assert desk.route_batch(PART, "seamkiln") == Route("seamkiln", None)


def test_a_create_routes_by_kind_and_the_reply_declares_it(desk):
    route = desk.route_batch(PART, None)
    assert route == Route("partkiln", "kind")
    out = desk.run_batch(route.adapter, PART, routed=route.how)
    assert out["adapter"] == "partkiln"
    assert out["routed"] == "by kind; pass adapter= to pin"
    assert out["created"] == ["e1"]


def test_a_kindless_create_goes_to_the_lane_that_takes_one(desk):
    # Blender makes a cube of a bare create; partkiln and seamkiln refuse one
    assert desk.route_batch([{"op": "create", "name": "thing"}], None) == Route("blender", "kind")


def test_an_op_that_names_an_entity_goes_where_it_lives(desk):
    # Fakes number ids from e1 in every lane; real lanes never collide
    # (part:/panel:/b<uid>). The blender box is e1 there; the partkiln
    # entity this test names is that lane's e2, which blender does not hold.
    desk.run_batch("blender", [{"op": "create", "kind": "cube", "name": "box"}])
    desk.run_batch("partkiln", [{"op": "create", "kind": "sketch", "name": "base"}])
    made = desk.run_batch("partkiln", PART)
    eid = made["created"][0]
    assert desk.caches["blender"].get(eid) is None
    route = desk.route_batch([{"op": "set", "id": eid, "props": {"name": "arm"}}], None)
    assert route == Route("partkiln", "id")
    out = desk.run_batch(
        route.adapter, [{"op": "set", "id": eid, "props": {"name": "arm"}}], routed=route.how
    )
    assert out["adapter"] == "partkiln" and out["routed"] == "by id; pass adapter= to pin"


def test_an_unknown_entity_names_the_lanes_searched(desk):
    with pytest.raises(TeeError) as err:
        desk.route_batch([{"op": "set", "id": "nope", "props": {}}], None)
    assert err.value.code == "unknown_entity"
    for lane in ("blender", "partkiln", "seamkiln"):
        assert lane in err.value.message
    assert "adapter=" in err.value.fix


def test_a_verb_only_one_lane_speaks_routes_by_op(desk):
    assert desk.route_batch([{"op": "drape", "props": {}}], None) == Route("seamkiln", "op")
    assert desk.route_batch([{"op": "param_set", "props": {}}], None) == Route("partkiln", "op")


def test_a_verb_two_lanes_speak_refuses_naming_both(desk):
    with pytest.raises(TeeError) as err:
        desk.route_batch([{"op": "export", "props": {"format": "glb"}}], None)
    assert err.value.code == "adapter_required"
    assert "partkiln" in err.value.message and "seamkiln" in err.value.message
    assert "blender" not in err.value.message
    assert "--default-adapter" in err.value.fix


def test_a_declared_default_breaks_a_tie_and_says_so(tmp_path):
    app = _desk(tmp_path, default_adapter="partkiln")
    try:
        ops = [{"op": "export", "props": {"format": "glb"}}]
        route = app.route_batch(ops, None)
        assert route == Route("partkiln", "default")
        # ...but content still beats the default: a panel is seamkiln's
        assert app.route_batch(PANEL, None) == Route("seamkiln", "kind")
        out = app.run_batch("partkiln", PART, routed="default")
        assert out["routed"] == "declared default"
    finally:
        app.shutdown()


def test_a_batch_that_spans_lanes_refuses(desk):
    with pytest.raises(TeeError) as err:
        desk.route_batch(PART + PANEL, None)
    assert err.value.code == "batch_spans_lanes"
    assert "op 0 (create) fits partkiln" in err.value.message
    assert "op 1 (create) fits seamkiln" in err.value.message
    assert "one batch per lane" in err.value.fix


def test_an_op_no_lane_speaks_names_what_each_takes(desk):
    with pytest.raises(TeeError) as err:
        desk.route_batch([{"op": "frobnicate"}], None)
    assert err.value.code == "op_not_in_lane"
    assert "op 'frobnicate'" in err.value.message
    assert "partkiln: create, set, delete, param_set, export (kinds part, sketch, extrude)" in (
        err.value.fix
    )
    with pytest.raises(TeeError) as err:
        desk.route_batch([{"op": "create", "kind": "spaceship"}], None)
    assert err.value.code == "op_not_in_lane"
    assert "create kind 'spaceship'" in err.value.message


def test_a_single_lane_server_never_changes_a_byte(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        route = app.route_batch(PART, None)
        assert route == Route("fake", "sole")
        out = app.run_batch(route.adapter, PART, routed=route.how)
        assert "adapter" not in out and "routed" not in out
    finally:
        app.shutdown()


def test_a_lane_that_declares_nothing_stays_a_candidate(tmp_path):
    app = TeeApp(
        {"seamkiln": Lane("seamkiln", ops=("drape",)), "mute": Mute()}, project_root=tmp_path
    )
    try:
        with pytest.raises(TeeError) as err:
            app.route_batch([{"op": "drape"}], None)
        assert err.value.code == "adapter_required"
        assert "mute" in err.value.message and "seamkiln" in err.value.message
    finally:
        app.shutdown()


def test_the_kernel_names_the_lanes_that_take_a_refused_batch(desk):
    with pytest.raises(TeeError) as err:
        desk.run_batch("blender", PART)  # explicit, and wrong
    assert err.value.code == "bad_op"
    assert "Lanes that accept this batch: partkiln (pass adapter=partkiln)" in err.value.fix
    assert "rolled back" in err.value.fix


def test_a_runtime_failure_gets_no_lane_hint(desk):
    with pytest.raises(TeeError) as err:
        desk.run_batch("blender", [{"op": "set", "id": "ghost", "props": {}}])
    assert err.value.code == "unknown_entity"
    assert "Lanes that accept" not in err.value.fix


def _payload(result):
    block = result.content[0]
    assert isinstance(block, TextContent)
    return json.loads(block.text)


def test_tee_batch_routes_on_the_wire(desk):
    server = build_server(desk)

    async def go():
        async with Client(server) as client:
            routed = _payload(await client.call_tool("tee_batch", {"ops": PART}))
            refused = _payload(
                await client.call_tool("tee_batch", {"ops": [{"op": "export", "props": {}}]})
            )
            return routed, refused

    routed, refused = anyio.run(go)
    assert routed["ok"] and routed["adapter"] == "partkiln"
    assert routed["routed"] == "by kind; pass adapter= to pin"
    assert refused["ok"] is False and refused["error"]["code"] == "adapter_required"
