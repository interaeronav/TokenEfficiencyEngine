import json

import pytest
from conftest import StubBridge

from tee import doctor
from tee.doctor import Check


def test_check_python_passes_here():
    check = doctor.check_python()
    assert check.status == "ok"
    assert check.required is True


def test_check_bpy_wheel_abi_reports_this_interpreter():
    check = doctor.check_bpy_wheel_abi()
    assert check.status in ("ok", "warn")
    assert "python 3." in check.detail


def test_bridge_check_warns_when_nothing_listens():
    check = doctor.check_blender_bridge(port=1)  # nothing listens on port 1
    assert check.status == "warn"
    assert "boot_background.py" in check.fix


def test_bridge_check_ok_against_protocol_stub():
    def responder(request):
        return json.dumps({"status": "ok", "result": {"v": "5.2.0", "bg": True}}).encode() + b"\0"

    bridge = StubBridge(responder)
    try:
        check = doctor.check_blender_bridge(port=bridge.port)
        assert check.status == "ok"
        assert "5.2.0" in check.detail
        assert "background" in check.detail
    finally:
        bridge.close()


def test_render_exit_code_only_fails_on_required():
    ok = [Check("a", "ok", "fine", required=True), Check("b", "warn", "meh", fix="do x")]
    text, code = doctor.render(ok)
    assert code == 0
    assert "fix: do x" in text
    bad = [Check("a", "fail", "broken", fix="fix it", required=True)]
    _, code = doctor.render(bad)
    assert code == 1
    soft = [Check("a", "fail", "broken", required=False)]
    _, code = doctor.render(soft)
    assert code == 0


def test_emit_config_shapes():
    for client in ("claude-code", "claude-desktop", "cursor", "qwen-code"):
        out = doctor.emit_config(client)
        assert "tee" in out
        assert "serve" in out
        # embedded JSON parses
        json_part = out[out.index("{") :]
        parsed = json.loads(json_part)
        assert parsed["mcpServers"]["tee"]["command"] == "uv"


def test_emit_config_qwen_names_its_settings_file():
    out = doctor.emit_config("qwen-code")
    assert ".qwen/settings.json" in out


def test_emit_config_rejects_an_unknown_client():
    with pytest.raises(ValueError, match="qwen-code"):
        doctor.emit_config("codex")


def test_unreal_check_rejects_a_stranger_on_the_port(monkeypatch):
    """A listening port is not proof the endpoint is Unreal's MCP server, so
    the check does the handshake and says so when it fails."""
    import socket

    from tee import doctor

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)
        port = sock.getsockname()[1]
        monkeypatch.setattr(doctor, "EPIC_MCP_PORT", port)
        monkeypatch.setattr(doctor, "find_unreal", lambda: None)
        check = doctor.check_unreal()
    assert check.status == "warn"
    assert "did not answer as Unreal" in check.detail
    assert "holds that port" in (check.fix or "")


def test_unreal_check_warns_when_nothing_is_there(monkeypatch):
    from tee import doctor

    monkeypatch.setattr(doctor, "EPIC_MCP_PORT", 9)
    monkeypatch.setattr(doctor, "find_unreal", lambda: None)
    check = doctor.check_unreal()
    assert check.status == "warn"
    assert "AllToolsets" in (check.fix or "") or "ModelContextProtocol" in (check.fix or "")
