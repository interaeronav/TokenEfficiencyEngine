import pytest

from tee.kernel.errors import TeeError
from tee.kernel.registry import ToolRegistry, VirtualTool


def make_tool(name="bl_create_cube", tags=None):
    return VirtualTool(
        name=name,
        description="Create a cube mesh.\nLonger help text here.",
        schema={
            "type": "object",
            "properties": {
                "size": {"type": "number"},
                "name": {"type": "string"},
            },
            "required": ["size"],
        },
        handler=lambda args: {"created": args.get("name", "Cube"), "size": args["size"]},
        tags=tags or ["blender", "mesh"],
    )


def test_register_rejects_duplicates_and_non_object_schemas():
    reg = ToolRegistry()
    reg.register(make_tool())
    with pytest.raises(ValueError):
        reg.register(make_tool())
    with pytest.raises(ValueError):
        reg.register(
            VirtualTool(name="bad", description="x", schema={"type": "array"}, handler=lambda a: {})
        )


def test_search_ranks_name_and_tag_matches():
    reg = ToolRegistry()
    reg.register(make_tool("bl_create_cube"))
    reg.register(make_tool("bl_assign_material", tags=["blender", "material"]))
    reg.register(make_tool("ue_spawn_actor", tags=["unreal", "actor"]))
    hits = reg.search("blender material")
    assert hits[0]["name"] == "bl_assign_material"
    assert all(set(h) == {"name", "summary"} for h in hits)
    assert "\n" not in hits[0]["summary"]


def test_describe_and_call_happy_path():
    reg = ToolRegistry()
    reg.register(make_tool())
    desc = reg.describe("bl_create_cube")
    assert desc["schema"]["required"] == ["size"]
    result = reg.call("bl_create_cube", {"size": 2.0, "name": "Box"})
    assert result == {"created": "Box", "size": 2.0}


def test_call_validation_errors_are_short_and_actionable():
    reg = ToolRegistry()
    reg.register(make_tool())
    with pytest.raises(TeeError) as err:
        reg.call("bl_create_cube", {})
    assert err.value.code == "missing_argument"
    with pytest.raises(TeeError) as err:
        reg.call("bl_create_cube", {"size": "big"})
    assert err.value.code == "bad_argument_type"
    with pytest.raises(TeeError) as err:
        reg.call("bl_create_cube", {"size": 1, "colour": "red"})
    assert err.value.code == "unknown_argument"
    with pytest.raises(TeeError) as err:
        reg.call("bl_create_cube", {"size": True})
    assert err.value.code == "bad_argument_type"  # bool is not a number


def test_unknown_tool_suggests_closest():
    reg = ToolRegistry()
    reg.register(make_tool())
    with pytest.raises(TeeError) as err:
        reg.call("bl_create_cub", {"size": 1})
    assert err.value.code == "unknown_tool"
    assert "bl_create_cube" in (err.value.fix or "")
