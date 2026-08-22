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


def test_a_partial_set_reads_the_transform_back_before_writing_it():
    """Epic's transform converter documents omitted fields as "unchanged" and
    then writes them as ZERO: a rotation-only set teleported an imported chair
    to the world origin (verified live on 5.8.1). The interpreter must fill the
    gaps from the current transform."""
    from tee.adapters.unreal import codegen

    script = codegen.program_batch(
        [{"op": "set", "id": "u1", "props": {"rotation": [0, 90, 0]}}],
        {"u1": "/Game/X.X:PersistentLevel.A"},
    )
    compile(script, "<program>", "exec")
    assert '_set_xform(ref, _complete(ref, op["xform"]))' in script
    assert "def _complete(actor, xform):" in script


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


def test_description_bullets_are_not_mistaken_for_toolsets(catalog):
    """list_toolsets descriptions contain their own '- ' bullet lists. A naive
    line filter invents toolsets: it counted 67 on live 5.8.1 where there are
    55, so the model could be handed names that do not exist."""
    names = catalog.load_toolsets()
    assert set(names) == {"ActorTools"}
    assert all(" " not in n for n in names)
    listing = catalog.list_summary()
    assert listing["total"] == 1


# -- schema-driven defaults + vision budget ----------------------------------


def test_default_for_builds_the_smallest_valid_value():
    """Epic rejects omitted object params with 'needs a default value' even
    when their own description says optional, so callers must materialise
    one."""
    from tee.adapters.unreal.summarize import default_for

    schema = {
        "type": "object",
        "properties": {
            "location": {
                "type": "object",
                "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                "required": ["x", "y"],
            },
            "label": {"type": "string"},
            "mode": {"type": "string", "enum": ["A", "B"]},
            "flags": {"type": "array"},
            "on": {"type": "boolean"},
        },
        "required": ["location", "label", "mode", "flags", "on"],
    }
    assert default_for(schema) == {
        "location": {"x": 0, "y": 0},
        "label": "",
        "mode": "A",
        "flags": [],
        "on": False,
    }


def test_missing_default_param_is_read_from_the_servers_own_message():
    from tee.adapters.unreal.summarize import missing_default_param

    msg = 'Function "CaptureViewport", input param "annotations" needs a default value.'
    assert missing_default_param(msg) == "annotations"
    assert missing_default_param("some other failure") is None


def test_capture_shrinks_until_it_fits_the_budget():
    """CaptureViewport has no resolution parameter and returns whatever the
    viewport is, so the budget has to be enforced client-side."""
    import base64
    import io

    from PIL import Image

    from tee.adapters.unreal.vision import encode_within_budget

    big = Image.new("RGB", (2744, 1820))
    for x in range(0, 2744, 7):  # noise so it does not compress to nothing
        for y in range(0, 1820, 7):
            big.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))
    buf = io.BytesIO()
    big.save(buf, format="PNG")
    png_b64 = base64.b64encode(buf.getvalue()).decode()

    data, meta = encode_within_budget(png_b64, 16 * 1024)
    assert len(data) <= 16 * 1024
    assert data[:2] == b"\xff\xd8"  # JPEG
    assert meta["source_px"] == [2744, 1820]
    assert meta["sent_px"][0] <= 1024


def test_capture_refuses_rather_than_blowing_the_budget():
    import base64
    import io

    from PIL import Image

    from tee.adapters.unreal.vision import encode_within_budget
    from tee.kernel.errors import TeeError

    img = Image.new("RGB", (2000, 2000))
    for x in range(0, 2000, 3):
        for y in range(0, 2000, 3):
            img.putpixel((x, y), (x % 256, y % 256, (x * y) % 256))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    with pytest.raises(TeeError) as err:
        encode_within_budget(base64.b64encode(buf.getvalue()).decode(), 200)
    assert err.value.code == "capture_over_budget"


def test_editor_python_without_the_plugin_explains_how_to_install_it(catalog):
    """The escape hatch degrades to a one-line remediation, not a stack trace,
    on the far more common case of the plugin not being installed."""
    from tee.adapters.unreal.adapter import UnrealAdapter
    from tee.kernel.errors import TeeError

    adapter = UnrealAdapter(wire=catalog.wire)
    assert adapter.has_tee_toolset() is False
    with pytest.raises(TeeError) as err:
        adapter.editor_python("result = {}")
    assert err.value.code == "tee_toolset_missing"
    assert "TeeToolset" in (err.value.fix or "")
    assert "ue_script" in (err.value.fix or "")


# -- SIE settle --------------------------------------------------------------


def test_max_delta_treats_a_missing_actor_as_unknown_not_still():
    """An empty or partial pose reading must never read as 'nothing moved',
    or a scene is declared settled before the play world has spawned."""
    from tee.adapters.unreal.simulate import max_delta

    a = {"Box": [0.0, 0.0, 100.0, 0, 0, 0]}
    assert max_delta(a, a) == 0.0
    assert max_delta(a, {"Box": [0.0, 0.0, 95.0, 0, 0, 0]}) == 5.0
    assert max_delta({}, {}) == float("inf")
    assert max_delta(a, {}) == float("inf")
    assert max_delta(a, {"Other": [0.0, 0.0, 100.0, 0, 0, 0]}) == float("inf")


def test_settle_programs_are_self_contained():
    """Programs run in the plugin's namespace, which provides only `unreal`
    and `result` - anything else must be imported by the program itself."""
    from tee.adapters.unreal import simulate

    adopt = simulate.adopt_program({"Box": [1.0, 2.0, 3.0, 0.0, 0.0, 0.0]})
    assert "import json" in adopt
    assert "import unreal" in adopt
    for program in (simulate.START, simulate.STOP, simulate.poll_program(["Box"])):
        assert "import unreal" in program
        assert "result =" in program


def test_settle_poll_program_does_not_wait_inside_the_call():
    """The editor cannot tick while a Python call runs, so a sleep or wait
    loop inside the poll would freeze the simulation permanently."""
    from tee.adapters.unreal import simulate

    program = simulate.poll_program(["Box"])
    for forbidden in ("time.sleep", "while ", "import time"):
        assert forbidden not in program, forbidden
