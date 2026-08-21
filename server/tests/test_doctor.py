import json

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
    for client in ("claude-code", "claude-desktop", "cursor"):
        out = doctor.emit_config(client)
        assert "tee" in out
        assert "serve" in out
        # embedded JSON parses
        json_part = out[out.index("{") :]
        parsed = json.loads(json_part)
        assert parsed["mcpServers"]["tee"]["command"] == "uv"
