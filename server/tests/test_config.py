from pathlib import Path

import pytest

from tee.app import TeeApp
from tee.config import ProjectConfig
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool


def write_config(root: Path, text: str) -> None:
    (root / ".tee").mkdir(parents=True, exist_ok=True)
    (root / ".tee" / "config.toml").write_text(text)


def test_missing_config_gives_defaults(tmp_path):
    config = ProjectConfig.load(tmp_path)
    assert config.disabled_tools == set()
    assert config.allow_code_exec is None
    assert config.blender_port is None
    assert config.warning is None


def test_valid_config_parses(tmp_path):
    write_config(
        tmp_path,
        '[tools]\ndisabled = ["bl_render", "bl_execute_python"]\n'
        "[server]\nallow_code_exec = true\n"
        "[blender]\nport = 9999\n",
    )
    config = ProjectConfig.load(tmp_path)
    assert config.disabled_tools == {"bl_render", "bl_execute_python"}
    assert config.allow_code_exec is True
    assert config.blender_port == 9999
    assert config.warning is None


def test_malformed_toml_degrades_with_warning(tmp_path):
    write_config(tmp_path, "[tools\nbroken")
    config = ProjectConfig.load(tmp_path)
    assert config.disabled_tools == set()
    assert "malformed" in config.warning


def test_wrong_types_degrade_per_field(tmp_path):
    write_config(
        tmp_path,
        '[tools]\ndisabled = "bl_render"\n'  # not a list
        "[server]\nallow_code_exec = 1\n"  # not a bool
        "[blender]\nport = 80\n",  # out of range
    )
    config = ProjectConfig.load(tmp_path)
    assert config.disabled_tools == set()
    assert config.allow_code_exec is None
    assert config.blender_port is None
    assert "disabled" in config.warning
    assert "allow_code_exec" in config.warning
    assert "port" in config.warning


@pytest.fixture()
def app_with_disabled(tmp_path):
    write_config(tmp_path, '[tools]\ndisabled = ["demo_tool"]\n')
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    for name in ("demo_tool", "other_tool"):
        app.registry.register(
            VirtualTool(
                capability="read-session",
                name=name,
                description=f"{name} does demo things.",
                schema={"type": "object", "properties": {}},
                handler=lambda args: {"ran": True},
                tags=["demo"],
            )
        )
    yield app
    app.shutdown()


def test_disabled_tool_hidden_from_search(app_with_disabled):
    hits = app_with_disabled.registry.search("demo")["items"]
    names = [h["name"] for h in hits]
    assert "other_tool" in names
    assert "demo_tool" not in names


def test_disabled_tool_call_names_the_config(app_with_disabled):
    with pytest.raises(TeeError) as err:
        app_with_disabled.registry.call("demo_tool", {})
    assert err.value.code == "tool_disabled"
    assert "config.toml" in err.value.fix
    with pytest.raises(TeeError):
        app_with_disabled.registry.describe("demo_tool")


def test_status_surfaces_disabled_and_code_exec(tmp_path):
    write_config(tmp_path, '[tools]\ndisabled = ["x"]\n[server]\nallow_code_exec = true\n')
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        status = app.status()
        assert status["disabled_tools"] == ["x"]
        assert status["code_exec_enabled"] is True  # from config, no CLI flag
    finally:
        app.shutdown()


def test_cli_flag_wins_over_absent_config(tmp_path):
    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path, allow_code_exec=True)
    try:
        assert app.allow_code_exec is True
    finally:
        app.shutdown()
