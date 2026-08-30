"""Switch profiles (A37 P0-S): q14b default, persistence across restarts,
chores provably on the active profile, and the managed lifecycle on a fake
process manager - single occupancy, out-of-bounds guard, job-token loading,
failed-start fallback. The live 14B/27B round trip is a recorded session,
not a test."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fixtures_llm import fake_llm_server

from tee.kernel.errors import TeeError
from tee.llm import chores, profiles

TRIAGE_REPLY = json.dumps({"diagnosis": "d", "fix": "f", "confidence": "grounded"})


@pytest.fixture(autouse=True)
def _fresh_probe_cache():
    chores._probe_cache.clear()
    yield
    chores._probe_cache.clear()


def base_cfg(tmp_path: Path, **extra: Any) -> dict[str, Any]:
    return {"_state_dir": str(tmp_path / ".tee"), **extra}


def managed_cfg(tmp_path: Path, **extra: Any) -> dict[str, Any]:
    return base_cfg(
        tmp_path,
        managed=True,
        url="http://127.0.0.1:9414/v1",
        profiles={
            "q14b": {
                "url": "http://127.0.0.1:9414/v1",
                "start": "mlx serve 14B --port 9414",
                "port": 9414,
                "process": "14B",
                "rss_gb": 9,
            },
            "q27b": {
                "url": "http://127.0.0.1:9427/v1",
                "start": "mlx serve 27B --port 9427",
                "port": 9427,
                "process": "27B",
                "rss_gb": 55,
                "eta_s": 5,
            },
        },
        **extra,
    )


class FakeProcs:
    """The fake process manager the P0-S fixtures run on."""

    def __init__(self) -> None:
        self.alive: set[int] = set()
        self.answering: set[str] = set()
        self.answer_on_start: dict[str, str] = {}  # command substring -> url
        self.events: list[tuple] = []
        self.commands: dict[int, str] = {}
        self.free_gb = 100.0
        self.pressure: list[str] = []
        self.start_dies = False
        self._next_pid = 200  # clear of the seeded pid 100

    def pid_alive(self, pid: int) -> bool:
        return pid in self.alive

    def pid_command(self, pid: int) -> str:
        return self.commands.get(pid, "")

    def pid_rss_mb(self, pid: int) -> float | None:
        return 8300.0 if pid in self.alive else None

    def stop(self, pid: int) -> None:
        self.events.append(("stop", pid))
        self.alive.discard(pid)
        # the owned server's endpoint dies with it
        for sub, url in self.answer_on_start.items():
            if sub in self.commands.get(pid, ""):
                self.answering.discard(url)

    def port_free(self, port: int) -> bool:
        return True

    def endpoint_answers(self, url: str, model: str | None = None) -> bool:
        return url in self.answering

    def start(self, command: str, log_path: Path) -> int:
        self.events.append(("start", command))
        pid = self._next_pid
        self._next_pid += 1
        self.commands[pid] = command
        if not self.start_dies:
            self.alive.add(pid)
            for sub, url in self.answer_on_start.items():
                if sub in command:
                    self.answering.add(url)
        return pid

    def find(self, pattern: str) -> list[int]:
        return [42] if pattern in self.pressure else []

    def free_ram_gb(self) -> float:
        return self.free_gb


class FakeJobs:
    def __init__(self) -> None:
        self.fns: dict[str, Any] = {}

    def submit(self, label: str, fn) -> str:
        job_id = f"job{len(self.fns) + 1}"
        self.fns[job_id] = fn
        return job_id


# -- defaults + persistence (rule 4) ----------------------------------------


def test_default_is_q14b_on_fresh_state(tmp_path) -> None:
    resolved = profiles.resolve(base_cfg(tmp_path))
    assert resolved["profile"] == "q14b"
    assert resolved["ready"] is True


def test_unmanaged_switch_persists_across_restart(tmp_path) -> None:
    cfg = base_cfg(tmp_path, adapters="/lora/tee-triage-a2")
    out = profiles.switch(cfg, "q27b")
    assert out["ok"] is True and "q27b" in out["report"]
    # a fresh process (new cfg dict over the same .tee) sees the choice
    resolved = profiles.resolve(base_cfg(tmp_path, adapters="/lora/tee-triage-a2"))
    assert resolved["profile"] == "q27b"
    assert resolved["model"] == "mlx-community/Qwen3.8-27B-bf16"
    assert resolved["adapters"] is None  # bare on purpose: a2 is 14B-trained


def test_invalid_state_falls_back_to_q14b(tmp_path) -> None:
    cfg = base_cfg(tmp_path)
    state_file = tmp_path / ".tee" / profiles.STATE_FILE
    state_file.parent.mkdir(parents=True)
    state_file.write_text("{not json", encoding="utf-8")
    assert profiles.resolve(cfg)["profile"] == "q14b"
    state_file.write_text(json.dumps({"active": "gone-profile"}), encoding="utf-8")
    assert profiles.resolve(cfg)["profile"] == "q14b"


def test_unknown_profile_is_rule6_listing_profiles(tmp_path) -> None:
    with pytest.raises(TeeError) as excinfo:
        profiles.switch(base_cfg(tmp_path), "q99")
    assert excinfo.value.code == "llm_unknown_profile"
    assert "q14b" in excinfo.value.fix and "q27b" in excinfo.value.fix
    assert "TEE/Q14B" in excinfo.value.fix


# -- chores provably use the active profile ---------------------------------


def test_chores_use_active_profile_model_and_adapters(tmp_path) -> None:
    served = ("m14", "mlx-community/Qwen3.8-27B-bf16")
    with fake_llm_server([TRIAGE_REPLY, TRIAGE_REPLY], models=served) as (url, calls):
        cfg = base_cfg(tmp_path, url=url, model="m14", adapters="/lora/tee-triage-a2")
        assert chores.triage("boom", cfg=cfg) is not None
        assert calls[-1]["model"] == "m14"
        assert calls[-1]["adapters"] == "/lora/tee-triage-a2"
        profiles.switch(cfg, "q27b")
        chores._probe_cache.clear()
        assert chores.triage("boom", cfg=cfg) is not None
        assert calls[-1]["model"] == "mlx-community/Qwen3.8-27B-bf16"
        assert "adapters" not in calls[-1]  # the 14B-trained LoRA never rides


# -- managed lifecycle on the fake process manager --------------------------


def seed_owned_q14b(cfg: dict, procs: FakeProcs) -> None:
    procs.alive.add(100)
    procs.commands[100] = "mlx serve 14B --port 9414"
    procs.answering.add("http://127.0.0.1:9414/v1")
    profiles.save_state(cfg, {"active": "q14b", "ready": True, "owned": {"q14b": {"pid": 100}}})


def test_managed_switch_is_stop_before_start_single_occupancy(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    seed_owned_q14b(cfg, procs)
    procs.answer_on_start["27B"] = "http://127.0.0.1:9427/v1"
    out = profiles.switch(cfg, "q27b", procs=procs)
    assert out["profile"] == "q27b" and "ready" in out["report"]
    stop_index = procs.events.index(("stop", 100))
    start_index = next(i for i, e in enumerate(procs.events) if e[0] == "start")
    assert stop_index < start_index  # stop-before-start, always
    assert 100 not in procs.alive  # old engine gone...
    assert out["evidence"]["leaver"]["rss_after"] is None  # ...RSS released, asserted
    state = profiles.load_state(cfg)
    assert "q14b" not in state["owned"] and state["owned"]["q27b"]["pid"] == 200


def test_managed_restart_of_dead_active_engine(tmp_path) -> None:
    # After a reboot the state says q14b but nothing serves: the phrase
    # means "get my engine running", not "already active".
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    procs.answer_on_start["14B"] = "http://127.0.0.1:9414/v1"
    out = profiles.switch(cfg, "q14b", procs=procs)
    assert "ready" in out["report"]
    assert any(e[0] == "start" and "14B" in e[1] for e in procs.events)
    assert profiles.load_state(cfg)["owned"]["q14b"]["pid"] == 200


def test_switching_away_from_used_not_owned_stops_nothing(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    # q27b active but owned by the chat stack (we merely used it)
    procs.answering.update({"http://127.0.0.1:9427/v1", "http://127.0.0.1:9414/v1"})
    profiles.save_state(cfg, {"active": "q27b", "ready": True, "owned": {}})
    out = profiles.switch(cfg, "q14b", procs=procs)
    assert out["profile"] == "q14b"
    assert all(event[0] != "stop" for event in procs.events)  # out of bounds held


def test_warm_target_is_used_not_owned(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    seed_owned_q14b(cfg, procs)
    procs.answering.add("http://127.0.0.1:9427/v1")  # chat-owned 27B already up
    out = profiles.switch(cfg, "q27b", procs=procs)
    assert "used, not owned" in out["report"]
    assert all(event[0] != "start" for event in procs.events)
    assert "q27b" not in profiles.load_state(cfg)["owned"]


def test_pressure_process_refuses_with_nothing_touched(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    seed_owned_q14b(cfg, procs)
    procs.pressure.append("MacOS/UnrealEditor( |$)")
    with pytest.raises(TeeError) as excinfo:
        profiles.switch(cfg, "q27b", procs=procs)
    assert excinfo.value.code == "llm_memory_pressure"
    assert profiles.load_state(cfg)["active"] == "q14b"
    assert procs.events == []  # nothing stopped, nothing started


def test_memory_guard_refuses_and_restores_previous(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    seed_owned_q14b(cfg, procs)
    procs.free_gb = 8.0  # < q27b's 55
    with pytest.raises(TeeError) as excinfo:
        profiles.switch(cfg, "q27b", procs=procs)
    assert excinfo.value.code == "llm_memory_pressure"
    assert "restored" in excinfo.value.fix
    state = profiles.load_state(cfg)
    assert state["active"] == "q14b" and state["ready"] is True


def test_protected_port_start_refused(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    cfg["profiles"]["q27b"]["port"] = 8080  # the chat stack's
    procs = FakeProcs()
    seed_owned_q14b(cfg, procs)
    with pytest.raises(TeeError) as excinfo:
        profiles.switch(cfg, "q27b", procs=procs)
    assert excinfo.value.code == "llm_protected_port"


def test_cold_load_returns_job_token_and_chores_answer_one_line(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    jobs = FakeJobs()
    seed_owned_q14b(cfg, procs)
    out = profiles.switch(cfg, "q27b", procs=procs, jobs=jobs)
    assert out["job"] == "job1" and out["eta_s"] == 5
    assert profiles.load_state(cfg)["ready"] is False
    # chores during the load: deterministic path at once, loud when required
    assert chores.triage("boom", cfg=cfg) is None
    with pytest.raises(TeeError) as excinfo:
        chores.triage("boom", cfg=cfg, refine="local")
    assert excinfo.value.code == "llm_loading"
    assert "q27b loading" in excinfo.value.message and "TEE/Q14B" in excinfo.value.message
    # the endpoint comes up; the job lands the ready state
    procs.answering.add("http://127.0.0.1:9427/v1")
    result = jobs.fns["job1"]()
    assert "ready" in result["report"]
    assert profiles.load_state(cfg)["ready"] is True


def test_failed_start_falls_back_to_previous_profile(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    procs = FakeProcs()
    jobs = FakeJobs()
    seed_owned_q14b(cfg, procs)
    procs.start_dies = True
    procs.answering.discard("http://127.0.0.1:9414/v1")
    out = profiles.switch(cfg, "q27b", procs=procs, jobs=jobs)
    procs.answering.discard("http://127.0.0.1:9414/v1")  # old engine stopped above
    with pytest.raises(TeeError) as excinfo:
        jobs.fns[out["job"]]()
    assert excinfo.value.code == "llm_start_failed"
    assert "fell back to q14b" in excinfo.value.fix
    state = profiles.load_state(cfg)
    assert state["active"] == "q14b" and state["ready"] is True
    assert any("14B" in e[1] for e in procs.events if e[0] == "start")  # restarted


def test_stale_mid_load_state_resolves_to_q14b(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    profiles.save_state(
        cfg, {"active": "q27b", "ready": False, "eta_s": 5, "since": 0, "owned": {}}
    )
    resolved = profiles.resolve(cfg)  # the load window is long past
    assert resolved["profile"] == "q14b" and resolved["ready"] is True


def test_status_line_reports_profile_and_loading(tmp_path) -> None:
    cfg = managed_cfg(tmp_path)
    assert profiles.status_line(cfg) == "q14b"
    procs = FakeProcs()
    jobs = FakeJobs()
    seed_owned_q14b(cfg, procs)
    profiles.switch(cfg, "q27b", procs=procs, jobs=jobs)
    assert profiles.status_line(cfg).startswith("q27b (loading")


def test_llm_switch_tool_and_tee_status_integration(tmp_path) -> None:
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter
    from tee.llm.tools import register_llm_tools

    app = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    try:
        register_llm_tools(app, tmp_path)
        assert app.status()["llm_profile"] == "q14b"
        with pytest.raises(TeeError) as excinfo:
            app.registry.call("llm_switch", {"profile": "q99"})
        assert excinfo.value.code == "llm_unknown_profile"
        described = app.registry.describe("llm_switch")
        assert "TEE/Q14B" in described["description"]  # the chat phrase contract
    finally:
        app.shutdown()
