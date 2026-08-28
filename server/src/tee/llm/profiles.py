"""Chore-engine switch profiles (A37 P0-S): TEE/Q14B <-> TEE/Q27B.

Named profiles map to (endpoint, model, adapters, note); the active choice
persists in `.tee/llm-profile.json` so it survives restarts. q14b - the
adopted 14B + tee-triage-a2 - is THE default: fresh config, missing or
stale state, and every failed or ambiguous fallback resolve to it
(owner rule, 2026-08-28).

Managed lifecycle is config-opt-in (`[llm] managed = true`) and guarantees
single occupancy: profiles declare what they OWN (start command, port,
process pattern), ownership is established ONLY by a pid this module
started and recorded, and the switch sequence is stop-before-start with
the stop verified (pid gone = RSS released, asserted via ps, not hoped).
Processes a profile did not start are never touched - the owner's chat
stack (:8080/:8090/:4000 by default) is out of bounds; a profile whose
endpoint already answers USES it and owns nothing, and switching away
from it stops nothing.

Continuity: the stop is synchronous and fast; a cold target loads behind
a job token (the tee_job pattern) with an ETA, chores called before
readiness degrade to their deterministic paths with a one-line status
("q27b loading, ~Ns - retry or TEE/Q14B") instead of hanging, and an
in-flight chore finishes on the old profile first (REQUEST_LOCK). A
failed start restarts the previous profile automatically and says so.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import shlex
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from tee.kernel import local_llm
from tee.kernel.errors import TeeError

DEFAULT_ACTIVE = "q14b"
STATE_FILE = "llm-profile.json"
# The owner's chat stack; a managed profile may USE an endpoint here but
# never start or stop anything on these ports. Override: [llm] protected_ports.
PROTECTED_PORTS = (8080, 8090, 4000)
# The section-2 lesson: never load a model while these run. Override:
# [llm] pressure_processes. The editor pattern is anchored so Epic's idle
# UnrealEditorServices daemon (always resident) is not a false positive -
# found by the P0-S live run, invisible to the fakes.
PRESSURE_PATTERNS = ("MacOS/UnrealEditor( |$)", "voxkiln")

# Builtin profiles; [llm.profiles.<name>] config overlays per-key and may
# add new names. An EXPLICIT empty adapters ("") means bare-on-purpose.
BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "q14b": {
        # url/model/adapters absent = inherit [llm]/env - the adopted setup
        "note": "the adopted default: 14B + tee-triage-a2 (traps 6/6, chores 0.76-1.77 s)",
        "rss_gb": 9.0,
        "eta_s": 30,
    },
    "q27b": {
        "model": "mlx-community/Qwen3.8-27B-bf16",
        "adapters": "",  # bare on purpose: tee-triage-a2 is 14B-trained
        "note": "traps pass bare (6/6); ~4-6x chore latency, 3.11-10.12 s measured",
        "rss_gb": 55.0,  # bf16 27B weights resident
        "eta_s": 90,
    },
}

# Held for the duration of one chore completion and for the managed stop:
# an in-flight chore finishes on the old profile before its server dies.
REQUEST_LOCK = threading.Lock()


def profiles(cfg: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Builtins overlaid per-key by [llm.profiles.*]; config may add names."""
    merged = {name: dict(spec) for name, spec in BUILTIN_PROFILES.items()}
    for name, spec in dict((cfg or {}).get("profiles") or {}).items():
        if isinstance(spec, dict):
            merged.setdefault(str(name), {}).update(spec)
    return merged


def _state_path(cfg: dict[str, Any] | None) -> Path | None:
    state_dir = (cfg or {}).get("_state_dir")
    return Path(state_dir) / STATE_FILE if state_dir else None


def load_state(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """The persisted choice, q14b on anything missing/invalid/stale (rule 4).

    A not-ready state whose load window has long passed is a switch that
    died mid-flight (server restart, killed job): resolve it to q14b
    rather than guessing - failed/ambiguous always lands on the default."""
    fallback = {"active": DEFAULT_ACTIVE, "ready": True}
    path = _state_path(cfg)
    if path is None or not path.is_file():
        return fallback
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return fallback
    if not isinstance(state, dict) or state.get("active") not in profiles(cfg):
        return fallback
    if not state.get("ready", True):
        eta = float(state.get("eta_s") or 0)
        since = float(state.get("since") or 0)
        if time.time() - since > eta * 2 + 60:
            state = {**fallback, "note": "previous switch never became ready"}
            save_state(cfg, state)
    return state


def save_state(cfg: dict[str, Any] | None, state: dict[str, Any]) -> None:
    path = _state_path(cfg)
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state), encoding="utf-8")
    tmp.replace(path)


def resolve(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """The chore-facing view: endpoint/model/adapters of the active profile.

    Absent profile keys inherit [llm] url/model/adapters and their env
    defaults; an explicit empty string pins 'none on purpose' (q27b bare)."""
    cfg = cfg or {}
    state = load_state(cfg)
    spec = profiles(cfg).get(state["active"], {})
    url = spec.get("url") or cfg.get("url") or local_llm.DEFAULT_URL
    model = spec.get("model") or cfg.get("model") or local_llm.DEFAULT_MODEL
    if "adapters" in spec:
        adapters = str(spec["adapters"]) or None
    else:
        adapters = cfg.get("adapters") or local_llm.DEFAULT_ADAPTERS
        adapters = str(adapters) if adapters else None
    out = {
        "profile": state["active"],
        "url": str(url),
        "model": str(model),
        "adapters": adapters,
        "ready": bool(state.get("ready", True)),
    }
    if not out["ready"]:
        eta = float(state.get("eta_s") or 0)
        since = float(state.get("since") or time.time())
        out["eta_left_s"] = max(1, round(eta - (time.time() - since)))
    return out


def loading_line(resolved: dict[str, Any]) -> str:
    return (
        f"{resolved['profile']} loading, ~{resolved.get('eta_left_s', '?')} s - retry or TEE/Q14B"
    )


def status_line(cfg: dict[str, Any] | None) -> str:
    """One token-cheap line for tee_status."""
    resolved = resolve(cfg)
    if resolved["ready"]:
        return resolved["profile"]
    return f"{resolved['profile']} (loading, ~{resolved['eta_left_s']} s left)"


# -- managed lifecycle -------------------------------------------------------


class Procs:
    """The real process seam (ps/pgrep/Popen); tests inject a fake."""

    def pid_alive(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            return False

    def pid_command(self, pid: int) -> str:
        try:
            out = subprocess.run(
                ["ps", "-o", "command=", "-p", str(pid)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return out.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return ""

    def pid_rss_mb(self, pid: int) -> float | None:
        """None once the process is gone - the RSS-released assertion."""
        try:
            out = subprocess.run(
                ["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True, timeout=5
            )
            text = out.stdout.strip()
            return round(int(text) / 1024, 1) if text else None
        except (OSError, subprocess.SubprocessError, ValueError):
            return None

    def stop(self, pid: int) -> None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.kill(pid, signal.SIGTERM)

    def port_free(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex(("127.0.0.1", int(port))) != 0

    def endpoint_answers(self, url: str) -> bool:
        return local_llm.available(url=url, timeout=2.0)

    def start(self, command: str, log_path: Path) -> int:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "ab") as log:
            proc = subprocess.Popen(
                shlex.split(command), stdout=log, stderr=log, start_new_session=True
            )
        return proc.pid

    def find(self, pattern: str) -> list[int]:
        try:
            out = subprocess.run(
                ["pgrep", "-f", pattern], capture_output=True, text=True, timeout=5
            )
            return [int(p) for p in out.stdout.split()]
        except (OSError, subprocess.SubprocessError, ValueError):
            return []

    def free_ram_gb(self) -> float:
        """Free + inactive pages via vm_stat (darwin); generous elsewhere."""
        try:
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5)
            page_size = 16384
            match = re.search(r"page size of (\d+)", out.stdout)
            if match:
                page_size = int(match.group(1))
            pages = 0
            for kind in ("Pages free", "Pages inactive", "Pages speculative"):
                match = re.search(rf"{kind}:\s+(\d+)", out.stdout)
                if match:
                    pages += int(match.group(1))
            return round(pages * page_size / 1024**3, 1)
        except (OSError, subprocess.SubprocessError):
            return float("inf")  # no vm_stat: the guard cannot judge, don't block


def _protected_ports(cfg: dict[str, Any]) -> set[int]:
    raw = cfg.get("protected_ports", PROTECTED_PORTS)
    return {int(p) for p in raw} if isinstance(raw, (list, tuple)) else set(PROTECTED_PORTS)


def _pressure(cfg: dict[str, Any], procs: Procs) -> str | None:
    patterns = cfg.get("pressure_processes", PRESSURE_PATTERNS)
    for pattern in patterns:
        if procs.find(str(pattern)):
            return str(pattern)
    return None


def _verified_stop(
    procs: Procs, pid: int, port: int | None, timeout_s: float = 20.0
) -> dict[str, Any]:
    """SIGTERM, then wait until the pid is gone (ps says no RSS) and the
    owned port is free. Returns the evidence, never hope."""
    procs.stop(pid)
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        gone = not procs.pid_alive(pid)
        port_ok = port is None or procs.port_free(int(port))
        if gone and port_ok:
            return {"stopped_pid": pid, "rss_after": procs.pid_rss_mb(pid), "port_free": True}
        time.sleep(0.25)
    return {
        "stopped_pid": pid,
        "rss_after": procs.pid_rss_mb(pid),
        "port_free": port is None or procs.port_free(int(port)),
        "warning": "stop not confirmed within timeout",
    }


def switch(
    cfg: dict[str, Any] | None,
    target_name: str,
    *,
    jobs=None,
    procs: Procs | None = None,
) -> dict[str, Any]:
    """The llm_switch core. Unmanaged: persist + one honest line. Managed:
    pressure guard -> synchronous verified stop of the OWNED leaver ->
    warm-use or (memory guard -> start -> readiness job with fallback)."""
    cfg = dict(cfg or {})
    known = profiles(cfg)
    target_name = str(target_name or "").strip().lower()
    if target_name not in known:
        names = ", ".join(sorted(known))
        raise TeeError(
            "llm_unknown_profile",
            f"'{target_name}' is not a chore-engine profile.",
            fix=f"Profiles: {names}. The chat phrases TEE/Q14B and TEE/Q27B map to q14b/q27b.",
        )
    spec = known[target_name]
    state = load_state(cfg)
    note = str(spec.get("note") or "")
    resolved_target = _resolve_spec(cfg, spec)
    if state["active"] == target_name:
        if not state.get("ready", True):
            resolved = resolve(cfg)
            return {
                "ok": True,
                "profile": target_name,
                "report": f"{target_name} still loading (~{resolved.get('eta_left_s', '?')} s "
                "left) - poll tee_job or TEE/Q14B to go back",
            }
        # Managed with a dead endpoint and a start command (e.g. after a
        # reboot): the phrase means "get my engine running" - fall through
        # to the start machinery instead of a useless "already active".
        restartable = (
            cfg.get("managed")
            and spec.get("start")
            and not (procs or Procs()).endpoint_answers(resolved_target["url"])
        )
        if not restartable:
            return {
                "ok": True,
                "profile": target_name,
                "report": f"{target_name} already active - {note}",
            }

    if not cfg.get("managed"):
        save_state(cfg, {"active": target_name, "ready": True, "switched_at": time.time()})
        answering = local_llm.available(url=resolved_target["url"], timeout=2.0)
        health = (
            "endpoint answering"
            if answering
            else "endpoint not answering - chores degrade until it starts "
            "(docs/setup-local-llm.md) or TEE/Q14B"
        )
        return {
            "ok": True,
            "profile": target_name,
            "report": f"{target_name} active ({resolved_target['model']}): {health}; {note}",
        }

    procs = procs or Procs()
    pressure = _pressure(cfg, procs)
    if pressure:
        raise TeeError(
            "llm_memory_pressure",
            f"'{pressure}' is running - not loading a model beside it (the shared-machine rule).",
            fix="Finish or stop that workload, then re-run the switch. Nothing was changed.",
        )

    leaver_name = state["active"]
    leaver_spec = known.get(leaver_name, {})
    owned = dict(state.get("owned") or {})
    evidence: dict[str, Any] = {}

    # Stop the leaver ONLY if this module started it (pid ownership) - the
    # out-of-bounds guard: a chat-stack server that merely answered our
    # requests was never ours and is not touched.
    leaver_owned = owned.get(leaver_name)
    if leaver_owned and procs.pid_alive(int(leaver_owned["pid"])):
        pattern = str(leaver_spec.get("process") or "")
        command = procs.pid_command(int(leaver_owned["pid"]))
        if pattern and pattern not in command:
            evidence["leaver"] = (
                f"owned pid {leaver_owned['pid']} no longer matches '{pattern}' - not stopping it"
            )
        else:
            with REQUEST_LOCK:  # an in-flight chore finishes first
                evidence["leaver"] = _verified_stop(
                    procs, int(leaver_owned["pid"]), leaver_spec.get("port")
                )
            owned.pop(leaver_name, None)
    elif leaver_owned:
        owned.pop(leaver_name, None)  # already gone

    # Warm target (chat-owned or externally started): use it, own nothing.
    if procs.endpoint_answers(resolved_target["url"]):
        save_state(
            cfg,
            {"active": target_name, "ready": True, "owned": owned, "switched_at": time.time()},
        )
        return {
            "ok": True,
            "profile": target_name,
            "report": f"{target_name} active ({resolved_target['model']}): endpoint already "
            f"serving - used, not owned; {note}",
            "evidence": evidence,
        }

    start_cmd = str(spec.get("start") or "")
    port = spec.get("port")
    if not start_cmd:
        # Managed but nothing declared to start: behave like unmanaged-cold.
        save_state(
            cfg,
            {"active": target_name, "ready": True, "owned": owned, "switched_at": time.time()},
        )
        return {
            "ok": True,
            "profile": target_name,
            "report": f"{target_name} active ({resolved_target['model']}): endpoint not "
            f"answering and no [llm.profiles.{target_name}] start command declared - "
            f"start it yourself or TEE/Q14B; {note}",
            "evidence": evidence,
        }
    if port is not None and int(port) in _protected_ports(cfg):
        _fallback(cfg, procs, known, leaver_name, owned, evidence)
        raise TeeError(
            "llm_protected_port",
            f"Port {port} belongs to the chat stack - TEE never starts or stops servers there.",
            fix="Declare a free port in [llm.profiles."
            f"{target_name}] or drop 'managed'. Previous profile restored.",
        )

    free_gb = procs.free_ram_gb()
    need_gb = float(spec.get("rss_gb") or 0)
    if need_gb and free_gb < need_gb:
        _fallback(cfg, procs, known, leaver_name, owned, evidence)
        raise TeeError(
            "llm_memory_pressure",
            f"~{free_gb} GB free but {target_name} needs ~{need_gb} GB resident.",
            fix="Free memory (quit heavy apps / other models), then re-run. "
            "Previous profile restored.",
        )

    eta = int(spec.get("eta_s") or 60)
    state_dir = Path(cfg.get("_state_dir") or ".")
    pid = procs.start(start_cmd, state_dir / f"llm-{target_name}.log")
    owned[target_name] = {"pid": pid, "started_at": time.time()}
    save_state(
        cfg,
        {
            "active": target_name,
            "ready": False,
            "eta_s": eta,
            "since": time.time(),
            "owned": owned,
        },
    )

    def wait_ready() -> dict[str, Any]:
        deadline = time.time() + eta * 2 + 30
        while time.time() < deadline:
            if load_state(cfg)["active"] != target_name:
                # A later switch took over (e.g. TEE/Q14B mid-load) and owns
                # the state now - this poller must not fight it.
                return {"profile": target_name, "report": "superseded by a later switch"}
            if procs.endpoint_answers(resolved_target["url"]):
                fresh = load_state(cfg)
                fresh.update({"ready": True, "switched_at": time.time()})
                save_state(cfg, fresh)
                return {
                    "profile": target_name,
                    "report": f"{target_name} ready ({resolved_target['model']}); {note}",
                    "evidence": evidence,
                }
            if not procs.pid_alive(pid):
                break
            time.sleep(1.0)
        if load_state(cfg)["active"] != target_name:
            return {"profile": target_name, "report": "superseded by a later switch"}
        # Failed start: stop the corpse, restart the previous profile, say so.
        if procs.pid_alive(pid):
            _verified_stop(procs, pid, port)
        owned.pop(target_name, None)
        fallback_report = _fallback(cfg, procs, known, leaver_name, owned, evidence)
        raise TeeError(
            "llm_start_failed",
            f"{target_name} never became ready (see llm-{target_name}.log).",
            fix=fallback_report,
        )

    if jobs is not None:
        job_id = jobs.submit(f"llm_switch {target_name}", wait_ready)
        return {
            "ok": True,
            "profile": target_name,
            "job": job_id,
            "eta_s": eta,
            "report": f"{target_name} loading (~{eta} s): chores answer their deterministic "
            f"paths meanwhile; poll tee_job or TEE/Q14B to go back; {note}",
            "evidence": evidence,
        }
    result = wait_ready()  # no job manager (tests/CLI): block bounded
    return {"ok": True, "profile": target_name, **result}


def _resolve_spec(cfg: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    url = spec.get("url") or cfg.get("url") or local_llm.DEFAULT_URL
    model = spec.get("model") or cfg.get("model") or local_llm.DEFAULT_MODEL
    return {"url": str(url), "model": str(model)}


def _fallback(
    cfg: dict[str, Any],
    procs: Procs,
    known: dict[str, dict[str, Any]],
    previous: str,
    owned: dict[str, Any],
    evidence: dict[str, Any],
) -> str:
    """Land on the previous profile, restarting it if we had stopped an
    owned server; on anything ambiguous land on q14b (rule 4)."""
    name = previous if previous in known else DEFAULT_ACTIVE
    spec = known.get(name, {})
    resolved = _resolve_spec(cfg, spec)
    report = f"fell back to {name}"
    if not procs.endpoint_answers(resolved["url"]) and spec.get("start"):
        try:
            pid = procs.start(
                str(spec["start"]), Path(cfg.get("_state_dir") or ".") / f"llm-{name}.log"
            )
            owned[name] = {"pid": pid, "started_at": time.time()}
            report = f"fell back to {name} (restarted, pid {pid})"
        except (OSError, ValueError) as exc:
            name = DEFAULT_ACTIVE
            report = f"fell back to {DEFAULT_ACTIVE} (restart failed: {exc})"
    save_state(
        cfg,
        {
            "active": name,
            "ready": True,
            "owned": owned,
            "note": "fallback",
            "switched_at": time.time(),
        },
    )
    evidence["fallback"] = report
    return report
