"""Explicit alias capacity/rates are validated and recognized by the real worker."""

from __future__ import annotations

import copy
import json
import subprocess
from datetime import date
from pathlib import Path

import pytest

from tee.docagents import backends
from tee.docagents.model_metadata import aider_metadata
from tee.kernel.errors import TeeError


def declared() -> dict:
    return {
        "schema": 1,
        "model": "claude-qwen-max",
        "url": "http://127.0.0.1:4000/v1",
        "upstream_model": "qwen3.8-max",
        "upstream_url": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "verified_on": "2026-09-11",
        "valid_until": "2026-09-25",
        "capacity_source": "https://www.alibabacloud.com/help/en/model-studio/qwen3-8-max",
        "price_source": "https://www.alibabacloud.com/help/en/model-studio/model-pricing",
        "currency": "USD",
        "max_input_tokens": 983616,
        "max_output_tokens": 131072,
        "context_window": 1000000,
        "price_in_per_mtok": 2.0,
        "price_out_per_mtok": 6.0,
        "request_output_tokens": 2048,
    }


def profile() -> dict:
    return {
        "model": "claude-qwen-max",
        "url": "http://127.0.0.1:4000/v1",
        "paid": True,
        "docagent_metadata": declared(),
    }


def test_metadata_is_optional_and_rates_do_not_retarget_or_unpay():
    assert aider_metadata({}) is None
    selected = profile()
    before = copy.deepcopy(selected)
    metadata = aider_metadata(selected, today=date(2026, 9, 11))
    assert selected == before
    assert metadata["info"]["input_cost_per_token"] == 0.000002
    assert metadata["info"]["output_cost_per_token"] == 0.000006
    assert metadata["info"]["max_output_tokens"] == 131072
    assert metadata["settings"]["extra_params"]["max_tokens"] == 2048
    assert "list rates" in metadata["provenance"]["price_basis"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "other"),
        ("url", "http://127.0.0.1:8080/v1"),
        ("price_in_per_mtok", 0),
        ("price_out_per_mtok", 0),
        ("price_in_per_mtok", True),
        ("price_out_per_mtok", float("nan")),
        ("currency", "CNY"),
        ("verified_on", "2026-09-12"),
        ("valid_until", "2026-10-31"),
        ("valid_until", "2026-09-10"),
        ("verified_on", []),
        ("max_input_tokens", True),
        ("max_output_tokens", -1),
        ("context_window", 128),
        ("request_output_tokens", 100000),
        ("capacity_source", "https://user:password@example.org/doc"),
        ("price_source", "file:///private/prices.json"),
        ("upstream_model", None),
        ("extra_params", {"api_base": "https://wrong.example"}),
    ],
)
def test_invalid_stale_unpriced_or_retargeted_metadata_is_refused(field, value):
    selected = profile()
    selected["docagent_metadata"][field] = value
    with pytest.raises(
        TeeError,
        match=r"(?i)(metadata|model|price|budget|limit|date|USD|provenance|upstream|proxy)",
    ):
        aider_metadata(selected, today=date(2026, 9, 11))


def test_model_metadata_expires_and_remains_unfetched():
    with pytest.raises(TeeError, match="stale"):
        aider_metadata(profile(), today=date(2026, 9, 26))


def test_selected_profile_carries_its_metadata_without_changing_pin(tmp_path):
    from types import SimpleNamespace

    from tee.docagents.tools import DocumentationLane

    folder = tmp_path / ".tee"
    folder.mkdir()
    config = (
        '[llm.profiles.qmax]\nmodel="claude-qwen-max"\n'
        'url="http://127.0.0.1:4000/v1"\npaid=true\n'
        '[llm.profiles.qmax.docagent_metadata]\n'
        + "\n".join(f"{key}={json.dumps(value)}" for key, value in declared().items())
        + "\n"
    )
    (folder / "config.toml").write_text(config)
    pin = folder / "llm-profile.json"
    pin.write_text('{"active":"qmax","pinned":true,"ready":true}')
    before = pin.read_bytes()
    selected = DocumentationLane(SimpleNamespace(), tmp_path)._profile()
    assert selected["docagent_metadata"] == declared() and selected["paid"]
    assert pin.read_bytes() == before
    pin.write_text('{"active":"q14b","pinned":true,"ready":true}')
    local = DocumentationLane(SimpleNamespace(), tmp_path)._profile()
    assert "docagent_metadata" not in local and not local["paid"]


def test_generated_private_files_are_recognized_without_a_paid_call(tmp_path, monkeypatch):
    import tee.docagents.model_metadata as module

    original = module.aider_metadata
    monkeypatch.setattr(
        module, "aider_metadata", lambda value: original(value, today=date(2026, 9, 11))
    )
    monkeypatch.setattr(
        backends,
        "discover",
        lambda: {
            "aider": {"available": True, "executable": "/workers/aider", "version_verified": True}
        },
    )
    work = tmp_path / "work"
    work.mkdir()
    manifest = {
        "run_dir": str(tmp_path),
        "work_dir": str(work),
        "instruction": "Describe the fixture.",
        "inputs": {},
        "outputs": {"guide.md": None},
    }
    plan = backends.build_plan("aider", manifest, profile(), authorized=True)
    args = plan.commands[-1]
    metadata = Path(args[args.index("--model-metadata-file") + 1])
    settings = Path(args[args.index("--model-settings-file") + 1])
    for path in [metadata, settings, metadata.with_name("model-provenance.json")]:
        assert path.stat().st_mode & 0o777 == 0o600
    assert "--no-show-model-warnings" not in args and plan.env["BROWSER"] == "/usr/bin/true"
    for flag in ["--model", "--weak-model", "--editor-model"]:
        assert args[args.index(flag) + 1] == "openai/claude-qwen-max"
    assert plan.paid and plan.model == "claude-qwen-max"
    python = Path.home() / ".local/share/tee/docagents/aider-0.86.2/bin/python"
    if not python.exists():
        pytest.skip("Pinned actual Aider interpreter is not installed")
    code = """
import json, os, socket, sys
from types import SimpleNamespace
def blocked(*a, **kw): raise AssertionError('No network call is permitted in metadata recognition')
socket.socket.connect = blocked
from aider import models
models.model_info_manager._cache_loaded = True
models.model_info_manager.content = {'fixture-no-download': {'mode': 'chat'}}
models.register_litellm_models([sys.argv[1]])
models.register_models([sys.argv[2]])
alias='openai/claude-qwen-max'
model=models.Model(alias, weak_model=alias, editor_model=alias)
warnings=[]
io=SimpleNamespace(tool_warning=warnings.append, tool_output=lambda *a, **kw: None)
problem=models.sanity_check_models(io, model)
assert not problem and not warnings, warnings
assert model.info['max_input_tokens']==983616
assert model.info['input_cost_per_token']==0.000002
assert model.extra_params['max_tokens']==2048 and model.edit_format=='diff'
assert model.name==alias
del os.environ['OPENAI_API_KEY']
missing=models.Model(alias, weak_model=False, editor_model=False)
assert models.sanity_check_model(io,missing) and warnings
print(json.dumps({'metadata_recognized':True,'missing_key_warning_retained':True,'paid_calls':0,'browser_calls':0}))
"""
    env = {
        **plan.env,
        "OPENAI_API_KEY": "fixture-not-a-real-key",
        "LITELLM_LOCAL_MODEL_COST_MAP": "True",
    }
    result = subprocess.run(
        [str(python), "-c", code, str(metadata), str(settings)],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.splitlines()[-1])["metadata_recognized"] is True
