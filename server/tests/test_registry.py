import pytest

from tee.kernel.errors import TeeError
from tee.kernel.registry import ToolRegistry, VirtualTool


def make_tool(name="bl_create_cube", tags=None):
    return VirtualTool(
        capability="read-session",
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
            VirtualTool(
                name="bad",
                description="x",
                schema={"type": "array"},
                handler=lambda a: {},
                capability="read-session",
            )
        )


def test_search_ranks_name_and_tag_matches():
    reg = ToolRegistry()
    reg.register(make_tool("bl_create_cube"))
    reg.register(make_tool("bl_assign_material", tags=["blender", "material"]))
    reg.register(make_tool("ue_spawn_actor", tags=["unreal", "actor"]))
    result = reg.search("blender material")
    hits = result["items"]
    assert hits[0]["name"] == "bl_assign_material"
    assert all(set(h) == {"name", "summary"} for h in hits)
    assert "\n" not in hits[0]["summary"]
    # name/tag hits scored well: no weak-match note rides along
    assert "note" not in result


def test_search_flags_weak_matches():
    # SI-B2: description-only grazes and empty results carry a note; name/tag
    # hits do not (covered in the ranking test above).
    reg = ToolRegistry()
    reg.register(make_tool("bl_create_cube"))
    weak = reg.search("help")  # matches description text only, weight 1.0
    assert weak["items"][0]["name"] == "bl_create_cube"
    assert "no strong match" in weak["note"]
    none = reg.search("frobnicate")
    assert none["items"] == []
    assert "no strong match" in none["note"]


def test_one_line_caps_paragraph_descriptions():
    long_first_line = (
        "Search the Expert Knowledge Base by keyword with optional exact "
        "filters. Returns ranked hits only with ids and one-line summaries "
        "so a session can pick a file to read without paying for content it "
        "never opens, and flags ride along verbatim."
    )
    tool = VirtualTool(
        name="kb_demo",
        description=long_first_line,
        schema={"type": "object", "properties": {}},
        handler=lambda a: {},
    )
    assert len(tool.one_line) <= 151
    assert tool.one_line.endswith((".", "..."))
    short = make_tool()
    assert short.one_line == "Create a cube mesh."


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


def test_register_rejects_required_keys_missing_from_properties():
    reg = ToolRegistry()
    with pytest.raises(ValueError, match="permanently uncallable"):
        reg.register(
            VirtualTool(
                capability="read-session",
                name="broken",
                description="x",
                schema={
                    "type": "object",
                    "properties": {"frames": {"type": "integer"}},
                    "required": ["target"],
                },
                handler=lambda a: {},
            )
        )
