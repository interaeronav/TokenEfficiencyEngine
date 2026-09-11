from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from tee.docagents import backends
from tee.kernel.errors import TeeError


@pytest.fixture
def manifest(tmp_path: Path) -> dict:
    work = tmp_path / "work"
    work.mkdir()
    return {
        "run_dir": str(tmp_path),
        "work_dir": str(work),
        "instruction": "Explain the parser and preserve its limitations.",
        "inputs": {"parser.py": "hash", "guide.md": "hash"},
        "outputs": {"guide.md": "hash", "docs/new.md": None},
    }


@pytest.fixture
def installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backends,
        "discover",
        lambda: {
            name: {"available": True, "executable": f"/workers/{name}", "version_verified": True}
            for name in backends.VERSIONS
        },
    )


def profile(**overrides: object) -> dict:
    return {
        "url": "http://127.0.0.1:4000/v1",
        "model": "claude-qwen-max",
        "paid": True,
        "active": "qmax",
        "pinned": True,
        **overrides,
    }


def test_discover_never_invokes_programs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_spawn(*args: object, **kwargs: object) -> None:
        raise AssertionError("discovery must not execute a program")

    import subprocess

    monkeypatch.setattr(subprocess, "run", no_spawn)
    monkeypatch.setattr(backends, "_install_root", lambda name: tmp_path / name)
    monkeypatch.setattr(backends.shutil, "which", lambda name: None)
    assert all(not value["available"] for value in backends.discover().values())


def test_discover_uses_managed_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backends, "_install_root", lambda name: tmp_path / name)
    for name in backends.VERSIONS:
        executable = backends._known_executable(name)
        executable.parent.mkdir(parents=True)
        executable.write_text("never executed")
        executable.chmod(0o700)
    metadata = tmp_path / "cline/node_modules/cline/package.json"
    metadata.parent.mkdir()
    metadata.write_text('{"version":"3.0.61"}')
    metadata = tmp_path / "aider/lib/python3.11/site-packages/aider_chat-0.86.2.dist-info/METADATA"
    metadata.parent.mkdir(parents=True)
    metadata.write_text("Name: aider-chat\nVersion: 0.86.2\n")
    result = backends.discover()
    assert all(row["version_verified"] for row in result.values())


@pytest.mark.parametrize("backend", ["aider", "cline"])
def test_plan_preserves_pin_paid_and_hides_key(
    backend: str,
    manifest: dict,
    installed: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "owner-cloud-key")
    monkeypatch.setenv("OPENAI_API_KEY", "owner-default-key")
    monkeypatch.setenv("AIDER_MODEL", "cloud-default")
    monkeypatch.setenv("HTTP_PROXY", "https://external.example")
    monkeypatch.setenv("CLINE_HOOKS_DIR", "/owner/hooks")
    original_home = os.environ.get("HOME")
    route = profile(api_key="explicit-worker-secret")
    before = dict(route)
    plan = backends.build_plan(backend, manifest, route, authorized=True)
    assert route == before
    assert plan.model == "claude-qwen-max"
    assert plan.paid is True
    assert "explicit-worker-secret" not in repr(plan.commands)
    assert "explicit-worker-secret" not in repr(plan)
    assert "owner-cloud-key" not in repr(plan)
    assert os.environ.get("HOME") == original_home
    assert Path(plan.env["HOME"]).is_relative_to(Path(manifest["run_dir"]))
    assert (
        not {"ANTHROPIC_API_KEY", "AIDER_MODEL", "HTTP_PROXY", "CLINE_HOOKS_DIR"} & plan.env.keys()
    )
    assert plan.cwd == Path(manifest["work_dir"])


def test_aider_exact_local_roles_and_scope(manifest: dict, installed: None) -> None:
    plan = backends.build_plan("aider", manifest, profile(), timeout_s=123, authorized=True)
    args = plan.commands[-1]
    for flag in ("--model", "--weak-model", "--editor-model"):
        assert args[args.index(flag) + 1] == "openai/claude-qwen-max"
    assert args[args.index("--timeout") + 1] == "123"
    assert args[args.index("--openai-api-base") + 1] == "http://127.0.0.1:4000/v1"
    assert args[args.index("--read") + 1] == str(plan.cwd / "parser.py")
    assert args[args.index("--") + 1 :] == [
        str(plan.cwd / "docs/new.md"),
        str(plan.cwd / "guide.md"),
    ]
    for flag in (
        "--no-git",
        "--no-auto-lint",
        "--no-auto-test",
        "--no-suggest-shell-commands",
        "--no-check-update",
        "--no-analytics",
        "--yes-always",
    ):
        assert flag in args
    assert plan.stdin is None


def test_cline_config_matches_observed_schema(manifest: dict, installed: None) -> None:
    plan = backends.build_plan(
        "cline", manifest, profile(api_key="private-secret"), authorized=True
    )
    args = plan.commands[-1]
    settings = Path(args[args.index("--data-dir") + 1]) / "settings/providers.json"
    content = json.loads(settings.read_text())
    assert content["version"] == 1 and content["lastUsedProvider"] == "openai-compatible"
    assert content["providers"]["openai-compatible"]["updatedAt"].endswith("Z")
    assert content["providers"]["openai-compatible"]["settings"] == {
        "provider": "openai-compatible",
        "apiKey": "private-secret",
        "model": "claude-qwen-max",
        "baseUrl": "http://127.0.0.1:4000/v1",
    }
    assert settings.stat().st_mode & 0o777 == 0o600
    assert settings.parent.stat().st_mode & 0o777 == 0o700
    assert args[args.index("--auto-approve") + 1] == "true"
    assert plan.env["CLINE_SESSION_BACKEND_MODE"] == "local"
    assert plan.env["CLINE_NO_AUTO_UPDATE"] == "1"
    assert json.loads(plan.env["CLINE_COMMAND_PERMISSIONS"])["deny"] == ["*"]
    assert "Explain the parser" in plan.stdin


def test_default_does_not_auto_approve(manifest: dict, installed: None) -> None:
    aider = backends.build_plan("aider", manifest, profile())
    cline = backends.build_plan("cline", manifest, profile())
    assert "--yes-always" not in aider.commands[-1]
    args = cline.commands[-1]
    assert args[args.index("--auto-approve") + 1] == "false"
    assert "Explain the parser" not in repr(args)


def test_private_git_discovery_boundary(manifest: dict, installed: None) -> None:
    plan = backends.build_plan("aider", manifest, profile())
    git_dir = Path(plan.env["GIT_DIR"])
    assert git_dir.is_relative_to(Path(manifest["run_dir"]))
    assert plan.commands[0][1:] == ["init", "--bare", "--quiet", str(git_dir)]
    assert plan.env["GIT_CONFIG_NOSYSTEM"] == "1"
    assert plan.env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert plan.env["GIT_CONFIG_SYSTEM"] == os.devnull


@pytest.mark.parametrize(
    "url",
    [
        "https://api.openai.com/v1",
        "http://127.0.0.1.example/v1",
        "http://user:secret@127.0.0.1:4000/v1",
        "http://127.0.0.1/v1?token=secret",
        "http://127.0.0.1/v1#secret",
        "http://192.168.1.1:4000/v1",
        "file:///v1",
        "http://127.0.0.1:4000",
        "http://[invalid/v1",
    ],
)
def test_refuse_remote_or_ambiguous_endpoint(url: str, manifest: dict, installed: None) -> None:
    with pytest.raises(TeeError, match="loopback"):
        backends.build_plan("aider", manifest, profile(url=url))


@pytest.mark.parametrize("url", ["http://localhost:8080/v1", "http://[::1]:8080/v1/"])
def test_allow_explicit_loopback(url: str, manifest: dict, installed: None) -> None:
    assert backends.build_plan("aider", manifest, profile(url=url, paid=False)).paid is False


def test_refuse_unverified_path_worker(manifest: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        backends,
        "discover",
        lambda: {
            "aider": {"available": True, "executable": "/unknown/aider", "version_verified": False}
        },
    )
    with pytest.raises(TeeError) as caught:
        backends.build_plan("aider", manifest, profile())
    assert caught.value.code == "docagent_version"


def test_private_state_symlink_refused(manifest: dict, installed: None, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "backend").symlink_to(outside, target_is_directory=True)
    with pytest.raises(TeeError) as caught:
        backends.build_plan("cline", manifest, profile())
    assert caught.value.code == "docagent_state_path"
    assert not list(outside.iterdir())


@pytest.mark.parametrize(
    "event,expected",
    [
        ({"type": "run_result", "finishReason": "completed"}, True),
        ({"type": "run_result", "finishReason": "aborted"}, False),
        ({"type": "run_result", "finishReason": "error"}, False),
        ({"type": "say", "text": "Task complete"}, False),
    ],
)
def test_cline_requires_terminal_result(event: dict, expected: bool, tmp_path: Path) -> None:
    log = tmp_path / "final.log"
    log.write_text(json.dumps(event) + "\n")
    assert backends.final_success(log, 0, backend="cline")["ok"] is expected


def test_cline_abort_and_numeric_usage_only(tmp_path: Path) -> None:
    log = tmp_path / "final.log"
    log.write_text(
        json.dumps(
            {
                "type": "run_result",
                "finishReason": "completed",
                "usage": {
                    "inputTokens": 25,
                    "outputTokens": 12,
                    "totalCost": 0.02,
                    "cacheReadTokens": float("nan"),
                    "cacheWriteTokens": True,
                    "secret": "private",
                },
            }
        )
    )
    assert backends.final_success(log, 0, backend="cline")["usage"] == {
        "inputTokens": 25,
        "outputTokens": 12,
        "totalCost": 0.02,
    }
    with log.open("a") as stream:
        stream.write('\n{"type":"run_aborted"}\n')
    assert not backends.final_success(log, 0, backend="cline")["ok"]


@pytest.mark.parametrize(
    "message,expected",
    [
        ("Applied edit to guide.md\n", True),
        ("", False),
        ("litellm.AuthenticationError: invalid token", False),
        ("SEARCH/REPLACE block failed", False),
    ],
)
def test_aider_completion_is_not_quality_claim(
    message: str, expected: bool, tmp_path: Path
) -> None:
    log = tmp_path / "final.log"
    log.write_text(message)
    result = backends.final_success(log, 0, backend="aider")
    assert result["ok"] is expected
    assert result["usage"] is None
    if expected:
        assert result["reason"] == "aider_exited_requires_document_validation"


def test_nonzero_and_oversized_output_refused(tmp_path: Path) -> None:
    log = tmp_path / "final.log"
    assert not backends.final_success(log, 1, backend="aider")["ok"]
    log.write_text("x" * (backends.MAX_LOG_BYTES + 1))
    assert backends.final_success(log, 0, backend="aider")["reason"] == "worker_log_limit"
