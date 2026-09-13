"""A78: one repair can find every stale idiom, before a scene checkpoint."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

from tee.adapters.blender import codegen
from tee.adapters.blender.adapter import BlenderAdapter
from tee.adapters.blender.shim import firewall_check, strip_comments
from tee.adapters.blender.tools import register_blender_tools
from tee.app import TeeApp
from tee.kernel.errors import TeeError

V52 = (5, 2, 0)


def test_all_occurrences_keep_source_lines_with_comments_and_crlf():
    code = (
        "# material.use_nodes = True\r\n"
        "\r\n"
        "material.use_nodes = True  # old.use_nodes = False\r\n"
        "# another.use_nodes = True\r\n"
        "world.use_nodes = True; other.use_nodes = False\r\n"
    )
    stripped = strip_comments(code)
    assert len(stripped) == len(code)
    assert [i for i, char in enumerate(stripped) if char == "\n"] == [
        i for i, char in enumerate(code) if char == "\n"
    ]
    [hit] = firewall_check(code, V52)
    assert hit["code"] == "use_nodes_write_banned"
    assert "delete the assignment" in hit["hint"]
    assert hit["lines"] == [3, 5]
    assert hit["occurrences"] == 3
    assert hit["line_count"] == 2
    assert "material" not in json.dumps(hit)  # no source snippets in the reply


def test_locations_are_bounded_but_all_matches_are_counted():
    code = "# world.use_nodes = True\n" + "world.use_nodes = True\n" * 40
    [hit] = firewall_check(code, V52)
    assert hit["lines"] == list(range(2, 10))
    assert hit["occurrences"] == hit["line_count"] == 40
    assert len(json.dumps(hit)) < 500


def test_multiline_pattern_locates_the_token_after_blank_lines():
    hits = firewall_check("\n# import bgl\n\nimport bgl\n\nfrom bgl import glClear\n", V52)
    [hit] = [hit for hit in hits if hit["code"] == "bgl_removed"]
    assert hit["lines"] == [4, 6]
    assert hit["occurrences"] == 2


class RecordingWire:
    """Only the wire is fake: real guard, handler, checkpoint, diff and cache.

    User test programs edit an ordinary dictionary, so the before/after
    state is produced by executing the program, not a canned success row.
    """

    def __init__(self):
        self.events = []
        self.entity = {"id": "b1", "name": "before", "kind": "mesh"}
        self.snapshots = []

    def probe(self):
        self.events.append("probe")
        return True

    def execute(self, code, *, strict_json=True, timeout=None):
        if not strict_json:
            self.events.append("execute")
            namespace = {"entity": self.entity}
            exec(code, namespace)
            return {"status": "ok", "result": namespace["result"]}
        if code == codegen.program_info():
            self.events.append("info")
            return {
                "status": "ok",
                "result": {
                    "version": list(V52),
                    "version_string": "5.2.0",
                    "background": True,
                    "filepath": "",
                    "objects": 1,
                },
            }
        if code == codegen.program_list_entities():
            self.events.append("list")
            return {"status": "ok", "result": {"entities": [copy.deepcopy(self.entity)]}}
        if "save_as_mainfile" in code:
            self.events.append("snapshot")
            self.snapshots.append(copy.deepcopy(self.entity))
            path = json.loads(re.search(r'filepath=("[^"]+")', code).group(1))
            Path(path).touch()
            return {"status": "ok", "result": {"path": path}}
        pytest.fail("unexpected wire program")


@pytest.fixture
def app(tmp_path):
    # Grant only this temporary project's test escape hatch. The product's
    # registration and trust gates still run through the actual registry.
    (tmp_path / ".tee").mkdir()
    (tmp_path / ".tee" / "config.toml").write_text('[trust]\ngrants = ["exec-code"]\n')
    workdir = tmp_path / "blender"
    workdir.mkdir()
    adapter = BlenderAdapter(wire=RecordingWire(), workdir=str(workdir))
    application = TeeApp({"blender": adapter}, project_root=tmp_path, allow_code_exec=True)
    register_blender_tools(application, adapter, docs_cache_dir=tmp_path / "docs-cache")
    try:
        yield application
    finally:
        application.shutdown()


@pytest.mark.parametrize(
    ("code", "error_code"),
    [
        ("world.use_nodes = True", "stale_api"),
        ("bpy.ops.wm.quit_blender()", "refused"),
        ("bpy.ops.wm.read_factory_settings()", "refused"),
        ("sys.exit(0)", "refused"),
    ],
)
def test_cached_version_bad_program_never_warms_or_checkpoints(app, monkeypatch, code, error_code):
    adapter = app.adapters["blender"]
    adapter._version = V52
    monkeypatch.setattr(app, "warm", lambda name: pytest.fail("invalid program warmed scene"))
    with pytest.raises(TeeError) as error:
        app.registry.call("bl_execute_python", {"code": code})
    assert error.value.code == error_code
    assert adapter.wire.events == []
    assert app.checkpoints.list() == []
    assert not list(Path(adapter.workdir).glob("*.blend"))
    assert adapter.wire.entity["name"] == "before"


def test_unknown_version_only_probes_info_before_refusing(app, monkeypatch):
    adapter = app.adapters["blender"]
    assert adapter._version is None
    monkeypatch.setattr(app, "warm", lambda name: pytest.fail("invalid program warmed scene"))
    with pytest.raises(TeeError) as error:
        app.registry.call("bl_execute_python", {"code": "world.use_nodes = True"})
    assert error.value.code == "stale_api"
    assert adapter.wire.events == ["info"]
    assert app.checkpoints.list() == []


def test_direct_adapter_calls_still_guard_all_occurrences(app):
    adapter = app.adapters["blender"]
    adapter._version = V52
    code = "# mat.use_nodes = True\nmat.use_nodes = True\n\nworld.use_nodes = True\n"
    with pytest.raises(TeeError) as error:
        adapter.execute_python(code)
    assert error.value.code == "stale_api"
    assert "use_nodes_write_banned (2 occurrence(s); lines 2, 4)" in error.value.message
    assert "delete the assignment" in error.value.fix
    assert adapter.wire.events == []
    assert "mat.use_nodes = True" not in error.value.message


def test_error_names_omitted_lines_without_echoing_source(app):
    adapter = app.adapters["blender"]
    adapter._version = V52
    with pytest.raises(TeeError) as error:
        adapter.validate_python("world.use_nodes = True\n" * 100)
    assert "100 occurrence(s); lines 1, 2, 3, 4, 5, 6, 7, 8 (+92 more lines)" in error.value.message
    assert len(json.dumps(error.value.to_payload())) < 600


def test_valid_program_still_checkpoints_before_execution_and_reports_real_diff(app):
    adapter = app.adapters["blender"]
    out = app.registry.call(
        "bl_execute_python",
        {"code": 'entity["name"] = "after"\nresult = {"renamed": entity["name"]}'},
    )
    assert adapter.wire.events == ["info", "probe", "list", "snapshot", "execute", "list"]
    assert adapter.wire.snapshots == [{"id": "b1", "name": "before", "kind": "mesh"}]
    assert app.checkpoints.list()[0]["id"] == out["checkpoint"]
    assert out["result"] == {"renamed": "after"}
    assert out["modified"] == ["b1"]
    assert app.cache("blender").get("b1").name == "after"


def test_legacy_allowed_assignment_still_executes_on_its_supported_version(app):
    adapter = app.adapters["blender"]
    adapter._version = (4, 5, 0)
    out = adapter.execute_python(
        "from types import SimpleNamespace\n"
        "world = SimpleNamespace()\n"
        "world.use_nodes = True\n"
        "result = {'enabled': world.use_nodes}"
    )
    assert out["result"] == {"enabled": True}
    assert adapter.wire.events == ["execute"]
