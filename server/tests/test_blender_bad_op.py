"""A68: a foreign op is a structured refusal before the wire, not a traceback.

Until now an unknown op reached Blender, raised a Python ValueError, and came
back as `blender_error` with a compacted traceback whose fix said "roll back
with tee_rollback" - and nothing named the lane that accepts it. Blender now
checks the batch against its own vocabulary first; nothing hits the wire;
and on a multi-lane server the kernel appends the lanes that would take it."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tee.adapters.blender.adapter import BlenderAdapter
from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter, LaneVocab
from tee.kernel.errors import TeeError

EMPTY_DIFF = {"created": [], "modified": [], "deleted": [], "details": {}, "entities": []}


class QuietWire:
    """Answers every program the adapter sends and records it."""

    def __init__(self):
        self.executed: list[str] = []

    def probe(self):
        return True

    def execute(self, code, *, strict_json=True, timeout=None):
        self.executed.append(code)
        if "save_as_mainfile" in code:  # a checkpoint: Blender would write the .blend
            path = json.loads(re.search(r"filepath=(\"[^\"]+\")", code).group(1))
            Path(path).touch()
            return {"status": "ok", "result": {"path": path}}
        if '"entities"' in code and "_ent(o) for o in bpy.data.objects" in code:
            return {"status": "ok", "result": {"entities": []}}
        if "_OPS = " in code:
            return {"status": "ok", "result": dict(EMPTY_DIFF)}
        if "version_string" in code:  # the info program, asked by every checkpoint
            return {
                "status": "ok",
                "result": {
                    "version": [5, 2, 0],
                    "version_string": "5.2.0",
                    "background": True,
                    "filepath": "",
                    "objects": 0,
                },
            }
        return {"status": "ok", "result": {"ok": True, "path": "/nowhere"}}


@pytest.fixture
def blender(tmp_path):
    return BlenderAdapter(wire=QuietWire(), workdir=str(tmp_path))


def test_an_unknown_op_is_refused_before_the_wire(blender):
    with pytest.raises(TeeError) as err:
        blender.execute([{"op": "drape", "props": {}}])
    assert err.value.code == "bad_op"
    assert "Blender has no op 'drape'" in err.value.message
    assert "modeling ops: wall_with_openings" in err.value.fix
    assert blender.wire.executed == []


def test_an_unknown_kind_is_refused_before_the_wire(blender):
    with pytest.raises(TeeError) as err:
        blender.execute([{"op": "create", "kind": "extrude", "name": "plate"}])
    assert err.value.code == "bad_kind"
    assert "cannot create kind 'extrude'" in err.value.message
    assert "omit kind for a cube" in err.value.fix
    assert blender.wire.executed == []


def test_an_unsupported_import_is_refused_before_the_wire(blender):
    with pytest.raises(TeeError) as err:
        blender.execute([{"op": "import_file", "path": "/x/bracket.step"}])
    assert err.value.code == "bad_op" and "'step'" in err.value.message
    assert "export glb" in err.value.fix
    assert blender.wire.executed == []


def test_a_batch_blender_speaks_reaches_the_wire(blender):
    diff = blender.execute([{"op": "create", "name": "box"}, {"op": "create", "kind": "light"}])
    assert diff.is_empty() and len(blender.wire.executed) == 1


class _Partkiln(FakeAdapter):
    def vocab(self):
        return LaneVocab(
            ops=("create", "set", "delete"),
            kinds=("part", "extrude"),
            kind_optional=False,
            renders=False,
            purpose="parts",
        )


def test_the_kernel_adds_the_lane_hint_only_when_another_lane_is_served(tmp_path):
    alone = TeeApp(
        {"blender": BlenderAdapter(wire=QuietWire(), workdir=str(tmp_path))}, project_root=tmp_path
    )
    try:
        with pytest.raises(TeeError) as err:
            alone.run_batch("blender", [{"op": "create", "kind": "extrude"}])
        assert err.value.code == "bad_kind" and "Lanes that accept" not in err.value.fix
    finally:
        alone.shutdown()

    both = TeeApp(
        {
            "blender": BlenderAdapter(wire=QuietWire(), workdir=str(tmp_path)),
            "partkiln": _Partkiln(),
        },
        project_root=tmp_path,
    )
    try:
        with pytest.raises(TeeError) as err:
            both.run_batch("blender", [{"op": "create", "kind": "extrude"}])
        assert err.value.code == "bad_kind"
        assert "Lanes that accept this batch: partkiln (pass adapter=partkiln)" in err.value.fix
        assert "rolled back" in err.value.fix
    finally:
        both.shutdown()
