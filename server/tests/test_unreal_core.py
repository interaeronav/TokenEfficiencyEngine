"""Connector, summarizer and catalog tests that need no editor."""

from __future__ import annotations

import json

import pytest
from fixtures_unreal import TOOLSETS, FakeUnrealWire

from tee.adapters.unreal import summarize as S
from tee.adapters.unreal.catalog import ToolsetCatalog
from tee.adapters.unreal.wire import UnrealWire
from tee.kernel.errors import TeeError


@pytest.fixture()
def catalog():
    return ToolsetCatalog(FakeUnrealWire())


# -- summarizer --------------------------------------------------------------


def test_ref_boilerplate_collapses_to_one_token():
    schema = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]["tools"][0]["inputSchema"]
    assert S.type_label(schema["properties"]["owner"]) == "ref<Object>"


def test_type_labels_cover_the_converters_epic_ships():
    props = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]["tools"][1]["inputSchema"][
        "properties"
    ]
    assert S.type_label(props["location"]) == "vec3"
    assert S.type_label(props["tags"]) == "list[str]"
    enum = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]["tools"][0]["inputSchema"][
        "properties"
    ]["container_type"]
    assert S.type_label(enum) == "ARRAY|SET|MAP"


def test_signature_marks_required_and_unwraps_returnValue():
    tool = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]["tools"][0]
    sig = S.tool_signature(tool)
    assert sig.startswith("add_component(")
    assert "owner: ref<Object>!" in sig  # required
    assert "container_type: ARRAY|SET|MAP" in sig and "container_type: ARRAY|SET|MAP!" not in sig
    assert sig.endswith("-> ref<ActorComponent>")  # returnValue wrapper stripped


def test_summary_line_drops_the_args_block():
    doc = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]["tools"][0]["description"]
    assert S.summary_line(doc) == "Adds a component to an actor."


def test_expand_tool_is_lazy_and_names_alternatives():
    parsed = TOOLSETS["editor_toolset.toolsets.actor.ActorTools"]
    one = S.expand_tool(parsed, "add_component")
    assert one["input_schema"]["properties"]["owner"]["required"] == ["refPath"]
    with pytest.raises(TeeError) as err:
        S.expand_tool(parsed, "no_such_tool")
    assert err.value.code == "ue_unknown_tool"
    assert "add_component" in (err.value.fix or "")


# -- catalog -----------------------------------------------------------------


def test_toolset_names_resolve_by_suffix_never_hardcoded(catalog):
    """Fully-qualified module paths drift between point builds (research 07)."""
    assert catalog.resolve("ActorTools") == "editor_toolset.toolsets.actor.ActorTools"
    assert catalog.resolve("actortools") == "editor_toolset.toolsets.actor.ActorTools"
    assert (
        catalog.resolve("editor_toolset.toolsets.actor.ActorTools")
        == "editor_toolset.toolsets.actor.ActorTools"
    )


def test_unknown_toolset_fails_with_close_matches(catalog):
    with pytest.raises(TeeError) as err:
        catalog.resolve("ActorToolz")
    assert err.value.code == "ue_unknown_toolset"


def test_describe_toolset_is_fetched_at_most_once_per_session(catalog):
    catalog.summary("ActorTools")
    catalog.summary("ActorTools", name_contains="add")
    catalog.describe_tool("ActorTools", "add_component")
    assert catalog.fetches == 1
    described = [c for c in catalog.wire.calls if c[0] == "describe_toolset"]
    assert len(described) == 1


def test_call_tool_sends_qualified_toolset_and_unprefixed_tool(catalog):
    catalog.call("ActorTools", "editor_toolset.toolsets.actor.ActorTools.add_component", {"x": 1})
    name, args = catalog.wire.calls[-1]
    assert name == "call_tool"
    assert args["toolset_name"] == "editor_toolset.toolsets.actor.ActorTools"
    assert args["tool_name"] == "add_component"


def test_summary_never_contains_the_raw_boilerplate(catalog):
    """The acceptance in spirit: the model must never see a raw payload."""
    text = json.dumps(catalog.summary("ActorTools"))
    assert S.__dict__["_REF_DESC"] not in text
    assert "refPath" not in text
    assert "inputSchema" not in text


# -- wire transport ----------------------------------------------------------


def test_wire_decodes_plain_json_and_sse_identically():
    """5.8.1 answered plain JSON; research 07 documents SSE. Both are parsed
    rather than betting on either."""
    body = {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}
    plain = UnrealWire._decode(json.dumps(body).encode(), "application/json")
    sse = UnrealWire._decode(
        f"event: message\ndata: {json.dumps(body)}\n\n".encode(), "text/event-stream"
    )
    assert plain == sse == body


def test_wire_reports_an_unreachable_editor_with_a_fix():
    wire = UnrealWire(port=9, connect_timeout=0.5, call_timeout=0.5)
    assert wire.probe() is False
    with pytest.raises(TeeError) as err:
        wire.connect()
    assert err.value.code == "ue_unreachable"
    assert "-ModelContextProtocolStartServer" in (err.value.fix or "")


def test_wire_rejects_a_non_json_body():
    with pytest.raises(TeeError) as err:
        UnrealWire._decode(b"<html>not me</html>", "text/html")
    assert err.value.code == "ue_bad_response"


# -- batch codegen -----------------------------------------------------------


def test_batch_embeds_ops_as_parsed_json_not_python_source():
    """JSON null/true/false are not Python literals. Emitting the ops array
    straight into the script source NameErrors inside Epic's sandbox the
    moment an optional field is absent (hit live on 5.8.1)."""
    from tee.adapters.unreal import codegen

    script = codegen.program_batch(
        [{"op": "create", "name": "X", "props": {"asset_path": "/Engine/BasicShapes/Cube"}}], {}
    )
    ops_line = next(line for line in script.splitlines() if line.startswith("_OPS"))
    assert ops_line.startswith("_OPS = json.loads(")
    # the null lives inside a quoted JSON string, never as a bare name
    assert "actor_type" in ops_line
    for line in script.splitlines():
        assert not line.strip().startswith("_OPS = [")


def test_batch_program_defines_run_and_uses_no_get_default():
    """Sandbox constraints verified live: the script must define run(), and
    tool results are _StrictDict, which rejects .get(key, default)."""
    from tee.adapters.unreal import codegen

    script = codegen.program_batch(
        [{"op": "create", "name": "X", "props": {"asset_path": "/Engine/BasicShapes/Cube"}}], {}
    )
    assert "\ndef run():" in script
    assert '.get("location", {})' not in script
    assert '.get("refPath")' not in script


def test_unknown_op_is_rejected_before_touching_the_editor():
    from tee.adapters.unreal import codegen

    with pytest.raises(ValueError) as err:
        codegen.normalize_batch([{"op": "levitate", "id": "u1"}])
    assert "levitate" in str(err.value)
    with pytest.raises(ValueError) as err:
        codegen.normalize_batch([{"op": "create", "name": "X"}])
    assert "asset_path" in str(err.value)


def test_transform_props_map_to_epics_optional_converter():
    from tee.adapters.unreal import codegen

    [op] = codegen.normalize_batch(
        [
            {
                "op": "create",
                "name": "X",
                "props": {"asset_path": "/E/C", "location": [1, 2, 3], "scale": [2, 2, 2]},
            }
        ]
    )
    assert op["xform"] == {
        "location": {"x": 1.0, "y": 2.0, "z": 3.0},
        "scale": {"x": 2.0, "y": 2.0, "z": 2.0},
    }
    assert "rotation" not in op["xform"]  # omitted = unchanged, never guessed


# -- blueprint graph DSL verification ----------------------------------------


def test_dsl_parser_handles_quoted_pins_and_comments():
    from tee.adapters.unreal.blueprint import parse_sexpr

    forms = parse_sexpr('(fn F ()\n  ; a comment\n  (:"Pin Name" (return)))')
    assert forms[0][0] == "fn"
    assert forms[0][3][0] == ':"Pin Name"'  # one atom, not ':' + '"Pin Name"'


def test_dsl_parser_rejects_unbalanced_brackets():
    from tee.adapters.unreal.blueprint import DslSyntaxError, parse_sexpr

    with pytest.raises(DslSyntaxError):
        parse_sexpr("(fn F (")
    with pytest.raises(DslSyntaxError):
        parse_sexpr("(fn F ()))")


def test_verifier_tolerates_the_engines_own_normalization():
    """write_graph_dsl rewrites as it writes: Utilities|Operators|Add reads
    back as +. A textual compare would false-alarm on every graph."""
    from tee.adapters.unreal.blueprint import verify_written

    report = verify_written(
        "(fn AddTwo (A B)\n  (return (Utilities|Operators|Add :A A :B B)))",
        "(fn AddTwo (A B)\n  (return (+ A B)))",
    )
    assert report["ok"] is True
    assert report["forms_requested"] == report["forms_written"] == 5


def test_verifier_catches_silently_dropped_statements():
    """The gap this closes: Epic's write_graph_dsl drops forms it cannot
    resolve, returns success, and the Blueprint then compiles CLEAN."""
    from tee.adapters.unreal.blueprint import verify_written

    report = verify_written("(fn Broken ()\n  (return (NoSuch|Node|Here :A 1)))", "(fn Broken ())")
    assert report["ok"] is False
    assert report["dropped_forms"] == 2
    assert "NoSuch|Node|Here" in report["likely_unresolved"]
