"""A79: Blender instruction stays opt-in, portable and scoped to known resources.

These gates audit the packaged lessons, not arbitrary untrusted Python. The
production execution policy and version firewall remain the actual tool guards.
"""

from __future__ import annotations

import ast
import builtins
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tee.adapters.blender import guidance
from tee.adapters.blender.adapter import BlenderAdapter
from tee.kernel.errors import TeeError

LESSONS = {
    "cadagent_enclosure": "enclosure",
    "cadagent_flange": "flange",
    "cadagent_joint": "joint",
    "cadagent_f1_wing": "f1_wing",
    "cadagent_f1_brake": "f1_brake",
    "cadagent_f1_wishbone": "f1_wishbone",
    "house": "house",
    "textures": "textures",
    "fabric": "fabric",
}
STAGES = ("build", "revise", "inspect")
BASIC = ("create", "material", "camera", "render")
# Guide-only topics: listed in the index and answerable as a card, but with no
# authored build/revise/inspect program behind them. `cadagent_architecture`
# (A82/A83) is one - it routes to the architecture lane through ak_guide rather
# than shipping a lesson. It is kept in its OWN set rather than folded into
# BASIC, which would call it basic, or into LESSONS, which would demand stages
# it does not have. The duplication of the production list is deliberate:
# adding a topic should require a deliberate edit here, and this entry is the
# drift that proves it works.
GUIDE_ONLY = ("cadagent_architecture",)
RESOURCE_DIR = Path(guidance.__file__).with_name("recipes")
# The largest authored program is presently under 30 kB. This is an explicit
# ceiling for opt-in whole stages; it does not widen the default guide budget.
MAX_STAGE_BYTES = 30000


def test_index_and_overviews_never_read_programs(monkeypatch):
    def forbidden_read(*_args, **_kwargs):
        pytest.fail("Listing guidance must not read a lesson program")

    monkeypatch.setattr(Path, "read_text", forbidden_read)
    index = guidance.guide()
    assert len(json.dumps(index)) < 1200
    assert set(index["topics"]) == set(LESSONS) | set(BASIC) | set(GUIDE_ONLY)
    for topic in (*LESSONS, *BASIC, *GUIDE_ONLY):
        card = guidance.guide(topic)
        assert len(json.dumps(card)) < 2600
        if topic in LESSONS:
            assert card["stages"] == {stage: f"{topic}.{stage}" for stage in STAGES}
            assert "call" not in card


@pytest.mark.parametrize(
    "topic",
    [
        "unknown",
        "house.destroy",
        "house.build.extra",
        "house.",
        "house..build",
        "house.inspect/../../secret",
        "../house.build",
        "textures/../../secret.build",
        "textures.__class__",
        "textures.BUILD",
        "cadagent_joint.revise\nimport os",
        "cadagent_enclosure.build\x00",
        "cadagent_f1_wing.inspect?path=secret",
        "create.build",
        "/tmp/house.py",
    ],
)
def test_unknown_stage_or_path_refuses_before_file_io(monkeypatch, topic):
    def forbidden_read(*_args, **_kwargs):
        pytest.fail("Unrecognized guide input reached the filesystem")

    monkeypatch.setattr(Path, "read_text", forbidden_read)
    with pytest.raises(TeeError) as error:
        guidance.guide(topic)
    assert error.value.code == "guide_topic"


@pytest.mark.parametrize("topic", LESSONS)
def test_a_stage_reads_only_its_whitelisted_resource(monkeypatch, topic):
    reads = []
    original = Path.read_text

    def record_read(path, *args, **kwargs):
        reads.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", record_read)
    guidance.guide(topic + ".inspect")
    assert reads == [RESOURCE_DIR / (LESSONS[topic] + ".py")]


@pytest.mark.parametrize("stage", STAGES)
@pytest.mark.parametrize("topic", LESSONS)
def test_complete_stage_compiles_passes_production_guard_and_carries_correct_hash(topic, stage):
    source = (RESOURCE_DIR / (LESSONS[topic] + ".py")).read_text()
    card = guidance.guide(f"{topic}.{stage}")
    assert card["call"]["name"] == "bl_execute_python"
    code = card["call"]["args"]["code"]
    assert len(code.encode()) < MAX_STAGE_BYTES
    assert source in code
    assert card["source_sha256"] == hashlib.sha256(source.encode()).hexdigest()
    compiled = compile(code, f"<lesson:{topic}.{stage}>", "exec")
    assert compiled is not None
    adapter = BlenderAdapter(wire=object())
    adapter._version = (5, 2, 0)
    adapter.validate_python(code)  # A wire-less object makes accidental execution fail.
    last = ast.parse(code).body[-1]
    assert isinstance(last, ast.Assign)
    assert [target.id for target in last.targets] == ["result"]
    assert isinstance(last.value, ast.Call)
    assert isinstance(last.value.func, ast.Name) and last.value.func.id == stage
    assert not last.value.args and not last.value.keywords


@pytest.mark.parametrize("topic", LESSONS)
def test_guidance_never_imports_blender_in_the_server(monkeypatch, topic):
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"bpy", "bmesh", "mathutils"}:
            pytest.fail("Guidance tried importing a native Blender runtime")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for stage in STAGES:
        assert guidance.guide(f"{topic}.{stage}")["stage"] == stage


@pytest.mark.parametrize("topic", LESSONS)
def test_stage_version_gate_precedes_resource_import_and_scene_access(topic):
    card = guidance.guide(topic + ".build")
    imports = []

    def fake_import(name, *_args, **_kwargs):
        imports.append(name)
        assert name == "bpy", "Old Blender reached the lesson's native imports"
        return SimpleNamespace(app=SimpleNamespace(version=(5, 1, 9)))

    environment = {"__builtins__": {**vars(builtins), "__import__": fake_import}}
    with pytest.raises(RuntimeError, match=r"Blender 5\.2"):
        exec(card["call"]["args"]["code"], environment)
    assert imports == ["bpy"]
    assert "build" not in environment


@pytest.mark.parametrize("topic", LESSONS)
def test_returned_guides_are_detached_even_after_nested_mutation(topic):
    overview = guidance.guide(topic)
    stage = guidance.guide(topic + ".build")
    expected_overview = json.dumps(overview, sort_keys=True)
    expected_stage = json.dumps(stage, sort_keys=True)
    overview["units"]["length"] = "wrong"
    overview["stages"].clear()
    stage["call"]["args"]["code"] = "broken"
    stage["next"].clear()
    assert json.dumps(guidance.guide(topic), sort_keys=True) == expected_overview
    assert json.dumps(guidance.guide(topic + ".build"), sort_keys=True) == expected_stage


@pytest.mark.parametrize("topic", LESSONS)
def test_resource_load_only_defines_functions_and_constants(topic):
    source = (RESOURCE_DIR / (LESSONS[topic] + ".py")).read_text()
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert set(STAGES) <= functions
    for statement in tree.body:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(statement, ast.FunctionDef):
            assert not statement.decorator_list
            assert all(
                not isinstance(node, ast.Call)
                for default in statement.args.defaults
                for node in ast.walk(default)
            )
            continue
        if isinstance(statement, ast.Expr):
            assert isinstance(statement.value, ast.Constant)
            assert isinstance(statement.value.value, str)
            continue
        assert isinstance(statement, ast.Assign), "Executable top-level lesson statement"
        assert all(isinstance(target, ast.Name) for target in statement.targets)
        # Generated constant tuples may use range/tuple; no Blender attribute
        # evaluation or arbitrary helper call may run merely by loading source.
        for node in ast.walk(statement.value):
            assert not isinstance(node, ast.Attribute)
            if isinstance(node, ast.Call):
                assert isinstance(node.func, ast.Name) and node.func.id in {"tuple", "range", "str"}

    class NoSceneAccess:
        def __getattr__(self, name):
            raise AssertionError("Loading a resource accessed Blender: " + name)

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in {"bpy", "bmesh"}:
            return NoSceneAccess()
        if name.startswith("mathutils"):
            return SimpleNamespace(Vector=object, BVHTree=object)
        return original_import(name, *args, **kwargs)

    environment = {"__builtins__": {**vars(builtins), "__import__": fake_import}}
    exec(compile(source, "<definitions-only>", "exec"), environment)
    assert all(callable(environment[stage]) for stage in STAGES)
    assert "result" not in environment


@pytest.mark.parametrize("topic", LESSONS)
def test_packaged_resources_have_no_file_network_or_dynamic_execution_capability(topic):
    tree = ast.parse((RESOURCE_DIR / (LESSONS[topic] + ".py")).read_text())
    imports = set()
    forbidden_calls = {"open", "exec", "eval", "compile", "__import__", "breakpoint"}
    forbidden_attributes = {
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "save_render",
        "save_as_mainfile",
        "open_mainfile",
        "read_factory_settings",
        "quit_blender",
        "load",
        "save",
        "connect",
        "urlopen",
        "system",
        "popen",
        "run_path",
        "run_module",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_attributes
    # hashlib compares the house's fixed authored driver signatures; it has no
    # file/network access and must not broaden the execution/import surface.
    assert imports <= {"math", "hashlib", "bpy", "bmesh", "mathutils"}
