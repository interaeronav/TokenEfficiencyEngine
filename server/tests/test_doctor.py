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


def test_web_check_reports_posture(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".tee").mkdir()
    (tmp_path / ".tee" / "config.toml").write_text("[web]\nallow_local = true\n")
    check = doctor.check_web()
    assert check.status == "ok"
    assert "allow_local=TRUE" in check.detail


def test_llm_check_down_is_a_state_with_the_setup_fix(tmp_path, monkeypatch):
    from tee.kernel import local_llm, local_vlm

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(local_llm, "available", lambda *a, **k: False)
    monkeypatch.setattr(local_vlm, "available", lambda *a, **k: False)
    check = doctor.check_llm()
    assert check.status == "ok"
    assert "down" in check.detail
    assert "setup-local-llm" in (check.fix or "")


def test_llm_check_up_needs_no_fix(tmp_path, monkeypatch):
    from tee.kernel import local_llm, local_vlm

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(local_llm, "available", lambda *a, **k: True)
    monkeypatch.setattr(local_vlm, "available", lambda *a, **k: False)
    check = doctor.check_llm()
    assert "chores UP" in check.detail
    assert check.fix is None


def test_state_check_reports_sizes_caps_and_staging(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    staging = tmp_path / ".tee" / "kb-staging"
    staging.mkdir(parents=True)
    (staging / "draft.md").write_text("# pending")
    cache = tmp_path / ".tee" / "web" / "cache"
    cache.mkdir(parents=True)
    (cache / "a.body").write_bytes(b"x" * 2048)
    check = doctor.check_state()
    assert check.status == "ok"
    assert "web cache capped 50 MB / 14 d" in check.detail
    assert "1 kb-staging draft(s)" in check.detail


def test_state_check_without_tee_dir_is_plain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    check = doctor.check_state()
    assert check.status == "ok"
    assert "no .tee/" in check.detail


def _fake_sidecar(tmp_path, line: str):
    """A stand-in for the sidecar interpreter that answers the probe with
    `line`. The check only ever reads the probe's stdout, so a shell script
    is a faithful double and needs no 250 MB venv to exist."""
    fake = tmp_path / "python"
    fake.write_text(f"#!/bin/sh\necho '{line}'\n")
    fake.chmod(0o755)
    return fake


def test_partkiln_check_names_the_occt_version_of_the_sidecar(tmp_path, monkeypatch):
    """A66 P6 acceptance: the doctor line must name the KERNEL version, not
    just "installed" - two OCP wheels and two interpreters can disagree."""
    from tee.adapters.partkiln import wire

    monkeypatch.setattr(wire, "SIDECAR_PY", _fake_sidecar(tmp_path, "3.11.15 True True 7.9.3"))
    check = doctor.check_partkiln()
    assert check.status == "ok"
    assert "mode sidecar" in check.detail
    assert "OCCT 7.9.3" in check.detail
    assert "server python" in check.detail  # both interpreters, always


def test_partkiln_check_survives_a_sidecar_that_answers_the_old_probe(tmp_path, monkeypatch):
    """A sidecar venv installed before the probe grew its fourth field still
    answers three tokens; that is unknown OCCT, never an IndexError."""
    from tee.adapters.partkiln import wire

    monkeypatch.setattr(wire, "SIDECAR_PY", _fake_sidecar(tmp_path, "3.11.15 True True"))
    check = doctor.check_partkiln()
    assert check.status == "ok"
    assert "OCCT ?" in check.detail


def test_partkiln_check_warns_with_both_install_routes_when_absent(tmp_path, monkeypatch):
    """partkiln is a separate install by design, so absence is a warn whose
    fix names the dev venv AND the sidecar that survives an upgrade."""
    from tee.adapters.partkiln import wire

    monkeypatch.setattr(wire, "SIDECAR_PY", tmp_path / "nothing-here")
    check = doctor.check_partkiln()
    if check.status == "ok":  # a dev checkout with `-e partkiln` installed
        assert "mode in-process" in check.detail
        assert "OCCT" in check.detail
    else:
        assert check.status == "warn"
        assert check.fix is not None
        assert "sidecars/partkiln" in check.fix


def test_partkiln_check_is_not_fooled_by_the_source_directory(tmp_path, monkeypatch):
    """`partkiln/` sits at the repo ROOT, so any interpreter whose path
    includes that root gets a NAMESPACE package of the same name and a bare
    `find_spec` says yes to a kernel that cannot import. Running the doctor
    from the checkout must not claim the lane works."""
    from importlib.util import find_spec

    from tee.adapters.partkiln import wire

    try:  # order-dependent: another module may already have imported the kernel
        import partkiln.client  # noqa: F401
    except ImportError:
        pass
    else:
        pytest.skip("the real kernel is importable in this interpreter - no shadow to test")
    (tmp_path / "partkiln").mkdir()  # the shadow: a directory, no module
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setattr(wire, "SIDECAR_PY", tmp_path / "no-sidecar")
    assert find_spec("partkiln") is not None  # the trap is armed
    check = doctor.check_partkiln()
    assert check.status == "warn"
    assert "kernel absent" in check.detail
