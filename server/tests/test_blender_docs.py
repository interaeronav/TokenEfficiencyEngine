"""BlenderDocs unit tests with a stubbed adapter (no DCC needed)."""

import pytest

from tee.adapters.blender.docs import BlenderDocs
from tee.kernel.adapter import AdapterInfo
from tee.kernel.errors import TeeError

ENTRIES = [
    {
        "path": "bpy.ops.object.shade_smooth_by_angle",
        "kind": "operator",
        "doc": "Set the sharpness of mesh edges based on the angle",
        "params": ["angle:float"],
    },
    {
        "path": "bpy.ops.mesh.primitive_cube_add",
        "kind": "operator",
        "doc": "Construct a cube mesh",
        "params": ["size:float", "location:float"],
    },
    {
        "path": "bpy.types.Modifier",
        "kind": "type",
        "doc": "Modifier affecting the geometry data of an object",
        "params": ["name:string", "type:enum"],
    },
]


class StubAdapter:
    def __init__(self):
        self.calls = 0

    def info(self):
        return AdapterInfo(id="blender", product="Blender", version="5.2.0 LTS", connected=True)

    def _call(self, code, timeout=None):
        self.calls += 1
        if "path = " in code:  # detail program
            if "shade_smooth_by_angle" in code:
                return {
                    "found": True,
                    "path": "bpy.ops.object.shade_smooth_by_angle",
                    "doc": "Set sharpness",
                    "properties": [{"name": "angle", "type": "float"}],
                }
            return {"found": False}
        return {"version": [5, 2, 0], "entries": ENTRIES}


@pytest.fixture()
def docs(tmp_path):
    return BlenderDocs(StubAdapter(), cache_dir=tmp_path)


def test_search_finds_by_words_and_is_compact(docs):
    out = docs.search("smooth angle")
    assert out["results"][0]["path"] == "bpy.ops.object.shade_smooth_by_angle"
    assert out["indexed_symbols"] == 3
    assert out["blender"] == "5.2.0"
    for item in out["results"]:
        assert len(item.get("doc", "")) <= 140


def test_search_no_match_gives_hint(docs):
    out = docs.search("quaternion garbage zzz")
    assert out["results"] == []
    assert "hint" in out


def test_index_cached_on_disk_and_reused(tmp_path):
    stub = StubAdapter()
    docs1 = BlenderDocs(stub, cache_dir=tmp_path)
    docs1.search("cube")
    assert stub.calls == 1  # one index build
    docs1.search("modifier")
    assert stub.calls == 1  # in-memory reuse

    stub2 = StubAdapter()
    docs2 = BlenderDocs(stub2, cache_dir=tmp_path)
    docs2.search("cube")
    assert stub2.calls == 0  # disk cache reused, no rebuild


def test_detail_found_and_unknown(docs):
    detail = docs.detail("bpy.ops.object.shade_smooth_by_angle")
    assert detail["found"] is True
    assert detail["properties"][0]["name"] == "angle"
    with pytest.raises(TeeError) as err:
        docs.detail("bpy.ops.object.no_such_thing")
    assert err.value.code == "unknown_api_symbol"
