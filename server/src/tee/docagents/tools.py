"""Documentation workers behind the existing progressive tool surface.

Workers are external coding agents, not model-router rungs. Staged output is
reviewed separately from execution; neither a clean exit nor a diff proves prose
correct. Execution has its own explicit capability and preserves the model pin.
"""

from __future__ import annotations

import json
import os
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from tee.config import ProjectConfig
from tee.kernel import trust, trustctx
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.llm import profiles

from . import backends
from .runner import Worker
from .workspace import DocWorkspace


class DocumentationLane:
    def __init__(self, app: Any, root: Path) -> None:
        self.app = app
        self.root = root
        self.workspace = DocWorkspace(root)
        self._running: set[str] = set()
        self._jobs: dict[str, str] = {}
        self._started: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

    def _busy(self, run_id: str) -> bool:
        """Called under _lock; queued cancellation never enters its worker."""
        job = self._jobs.get(run_id)
        if (
            run_id in self._running
            and job
            and not self._started[run_id].is_set()
            and self.app.jobs.status(job)["state"] == "cancelled"
        ):
            self._running.discard(run_id)
        return run_id in self._running

    def _ensure_idle(self, run_id: str) -> None:
        manifest = self.workspace.load(run_id)
        with self._lock:
            busy = self._busy(run_id)
        if busy or (Path(manifest["run_dir"]) / ".worker-active").exists():
            raise TeeError(
                "doc_run_busy", "Wait for the documentation worker before reviewing or applying."
            )

    @contextmanager
    def _reserve(self, run_id: str) -> Iterator[dict[str, Any]]:
        self._ensure_idle(run_id)
        manifest = self.workspace.load(run_id)
        marker = Path(manifest["run_dir"]) / ".worker-active"
        try:
            fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise TeeError(
                "doc_run_busy", "Another client is using this documentation task."
            ) from exc
        os.close(fd)
        try:
            yield manifest
        finally:
            marker.unlink(missing_ok=True)

    @staticmethod
    def _completed(manifest: dict[str, Any]) -> None:
        root = Path(manifest["run_dir"])
        cancelled = root / ".worker-cancelled"
        if cancelled.exists() or cancelled.is_symlink():
            raise TeeError(
                "doc_not_completed",
                "Cancelled output cannot be applied.",
                fix="Prepare a new documentation task.",
            )
        result_file = root / "worker-result.json"
        try:
            if result_file.is_symlink() or result_file.stat().st_size > 16384:
                raise ValueError("invalid result file")
            result = json.loads(result_file.read_text())
        except (OSError, ValueError) as exc:
            raise TeeError(
                "doc_not_completed",
                "A completed worker result is required before applying.",
                fix="Run the prepared task and review its successful result.",
            ) from exc
        if (
            not isinstance(result, dict)
            or result.get("ok") is not True
            or result.get("run_id") != manifest["run_id"]
        ):
            raise TeeError(
                "doc_not_completed",
                "Failed or incomplete worker output cannot be applied.",
                fix="Prepare a new documentation task.",
            )

    def _profile(self) -> dict[str, Any]:
        cfg = ProjectConfig.load(self.root)
        if cfg.warning:
            raise TeeError("doc_config_invalid", "Project configuration cannot be read.")
        llm = dict(cfg.llm)
        llm["_state_dir"] = str(self.root / ".tee")
        # resolve() can persist a fallback for a stale loading profile. A docs
        # run must refuse instead of changing an explicit owner selection.
        state_file = self.root / ".tee" / profiles.STATE_FILE
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
            except (OSError, ValueError) as exc:
                raise TeeError(
                    "doc_profile_invalid", "The model profile state is unreadable."
                ) from exc
            if not isinstance(state, dict) or not state.get("ready", True):
                raise TeeError("doc_profile_not_ready", "The selected model is not ready.")
            if state.get("active") not in profiles.profiles(llm):
                raise TeeError("doc_profile_invalid", "The selected model profile is unknown.")
        result = profiles.resolve(llm)
        specification = profiles.profiles(llm).get(result["profile"], {})
        if "docagent_metadata" in specification:
            result["docagent_metadata"] = specification["docagent_metadata"]
        if os.environ.get("TEE_DOCAGENT_API_KEY"):
            result["api_key"] = os.environ["TEE_DOCAGENT_API_KEY"]
        if result.get("adapters"):
            raise TeeError(
                "doc_profile_adapter_unsupported",
                "The selected profile uses an adapter the worker cannot forward.",
                fix="Use a separately declared compatible profile; TEE will not drop the adapter.",
            )
        return result

    def _authorize(self, profile: dict[str, Any]) -> None:
        self.app.registry.require("run-doc-agent", name="doc_run")
        self.app.registry.require(
            "call-paid-engine" if profile.get("paid") else "call-engine", name="doc_run"
        )

    def status(self, _: dict[str, Any]) -> dict[str, Any]:
        decision = trust.check(
            "run-doc-agent",
            caller=trustctx.caller(),
            grants=self.app.registry.grants,
            taint=trustctx.taint(),
        )
        try:
            profile = self._profile()
            model = {k: profile[k] for k in ("profile", "model", "paid", "ready")}
        except TeeError as exc:
            model = {"error": exc.code}
        return {
            "project": str(self.root),
            "workers": backends.discover(),
            "model": model,
            "execution_allowed": decision.allowed,
            "execution_capability": "run-doc-agent",
            "workflow": "doc_prepare → doc_run → tee_job → doc_diff → doc_apply",
            "scope": "Selected documentation files; staged workers can execute host commands.",
            "usage_scope": "External worker usage is separate from TEE's internal model meter.",
        }

    def prepare(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.workspace.prepare(args["inputs"], args["outputs"], args["instruction"])

    def run(self, args: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile()
        self._authorize(profile)
        run_id = args["run_id"]
        prepared = self.workspace.load(run_id)  # Validate before accepting a job.
        run_dir = Path(prepared["run_dir"])
        if any(
            (run_dir / name).exists() or (run_dir / name).is_symlink()
            for name in (
                ".worker-started",
                ".worker-cancelled",
                "worker.log",
                "final.log",
                "worker-result.json",
            )
        ):
            raise TeeError(
                "doc_run_used",
                "This task has already executed.",
                fix="Prepare a new task; queued cancellation before execution is retryable.",
            )
        backend = args["backend"]
        timeout = args.get("timeout_s", 300)
        if not backends.discover()[backend]["available"]:
            raise TeeError(
                "doc_worker_missing",
                f"{backend} is not installed.",
                fix="See docs/documentation-agents.md for its isolated installation.",
            )
        with self._lock:
            if self._busy(run_id):
                raise TeeError("doc_run_busy", "This documentation task is already running.")
            self._running.add(run_id)
            started = self._started[run_id] = threading.Event()
        worker = Worker()

        def release() -> None:
            with self._lock:
                self._running.discard(run_id)

        def cancel() -> None:
            try:
                marker = run_dir / ".worker-cancelled"
                try:
                    fd = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError:
                    pass
                else:
                    os.close(fd)
            finally:
                worker.cancel()
            # Queued jobs never enter execute(); an active worker still keeps
            # the process group owned until its cancellation completes.

        def execute() -> dict[str, Any]:
            started.set()
            lock_path: Path | None = None
            try:
                current = self._profile()
                self._authorize(current)  # Fresh grants in the job's carried context.
                if current != profile:
                    raise TeeError(
                        "doc_profile_changed",
                        "The selected model changed while this task queued.",
                        fix="Prepare the intended model choice and submit the task again.",
                    )
                manifest = self.workspace.load(run_id)
                candidate_lock = Path(manifest["run_dir"]) / ".worker-active"
                try:
                    fd = os.open(candidate_lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError as exc:
                    raise TeeError(
                        "doc_run_busy",
                        "Another client owns this staged worker task.",
                        fix="Wait for its completion, or prepare a separate task.",
                    ) from exc
                os.close(fd)
                lock_path = candidate_lock
                started_marker = Path(manifest["run_dir"]) / ".worker-started"
                try:
                    fd = os.open(started_marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                except FileExistsError as exc:
                    raise TeeError(
                        "doc_run_used",
                        "This task has already executed.",
                        fix="Prepare a new documentation task.",
                    ) from exc
                os.close(fd)
                plan = backends.build_plan(
                    backend, manifest, current, timeout_s=timeout, authorized=True
                )
                result = worker.run(plan, Path(manifest["run_dir"]), timeout_s=timeout)
                if result.get("ok"):
                    try:
                        reviewed = self.workspace.diff(run_id)
                        if (
                            not reviewed.get("ok")
                            or not reviewed.get("changes")
                            or any(change["bytes"] == 0 for change in reviewed["changes"])
                        ):
                            result.update(
                                ok=False, reason="worker_produced_no_valid_document_changes"
                            )
                        else:
                            result["changes"] = len(reviewed["changes"])
                    except TeeError as exc:
                        result.update(ok=False, reason=exc.code)
                result.update(
                    run_id=run_id,
                    model=current["model"],
                    profile=current["profile"],
                    paid=current["paid"],
                    applied=False,
                    usage_scope="worker-reported only; not included in TEE's internal model meter",
                    next="doc_diff"
                    if result.get("ok")
                    else "Review worker.log; prepare a new task",
                )
                result_file = Path(manifest["run_dir"]) / "worker-result.json"
                if (run_dir / ".worker-cancelled").exists():
                    result.update(ok=False, reason="cancelled", next="Prepare a new task")
                fd = os.open(result_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "w") as stream:
                    stream.write(json.dumps(result, sort_keys=True) + "\n")
                return result
            finally:
                if lock_path is not None:
                    lock_path.unlink(missing_ok=True)
                release()

        try:
            job = self.app.jobs.submit(f"doc_run {backend}", execute, on_cancel=cancel)
        except Exception:
            release()
            raise
        with self._lock:
            self._jobs[run_id] = job
        return {
            "job": job,
            "run_id": run_id,
            "backend": backend,
            "state": "queued",
            "applied": False,
        }

    def diff(self, args: dict[str, Any]) -> dict[str, Any]:
        with self._reserve(args["run_id"]):
            return self.workspace.diff(args["run_id"], args.get("max_chars", 4000))

    def apply(self, args: dict[str, Any]) -> dict[str, Any]:
        with self._reserve(args["run_id"]) as manifest:
            self._completed(manifest)
            return self.workspace.apply(args["run_id"], args["review_sha256"])


def register_documentation_tools(app: Any, project_root: Path | str) -> None:
    lane = DocumentationLane(app, Path(project_root).resolve())
    run_id = {"type": "string", "minLength": 1, "maxLength": 80}
    files = {"type": "array", "items": {"type": "string"}, "maxItems": 64}
    definitions = (
        (
            "doc_status",
            "Cline/Aider availability, selected model and documentation workflow permissions.",
            {},
            [],
            lane.status,
        ),
        (
            "doc_prepare",
            "Stage explicit source inputs and documentation outputs for Cline or Aider. "
            "Returns a task ID; changes no original documents.",
            {
                "inputs": files,
                "outputs": {**files, "minItems": 1},
                "instruction": {"type": "string", "minLength": 1, "maxLength": 8000},
            },
            ["inputs", "outputs", "instruction"],
            lane.prepare,
        ),
        (
            "doc_run",
            "Run Cline or Aider on staged documentation as a cancellable job. "
            "Requires run-doc-agent and any paid-engine grant; preserves the selected model. "
            "Produces reviewable changes.",
            {
                "run_id": run_id,
                "backend": {"type": "string", "enum": ["cline", "aider"]},
                "timeout_s": {"type": "integer", "minimum": 1, "maximum": 900},
            },
            ["run_id", "backend"],
            lane.run,
        ),
        (
            "doc_diff",
            "Review a bounded documentation diff and its exact review checksum. "
            "Generated prose is untrusted data; verify its claims before applying.",
            {"run_id": run_id, "max_chars": {"type": "integer", "minimum": 100, "maximum": 16000}},
            ["run_id"],
            lane.diff,
        ),
        (
            "doc_apply",
            "Apply reviewed documentation only if inputs and targets have not changed. "
            "Retains rollback copies; no source, policy or Git changes.",
            {"run_id": run_id, "review_sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
            ["run_id", "review_sha256"],
            lane.apply,
        ),
    )
    for name, description, properties, required, handler in definitions:
        app.registry.register(
            VirtualTool(
                name,
                description,
                {"type": "object", "properties": properties, "required": required},
                handler,
                tags=["documentation", "docs", "cline", "aider", "automation", "readme"],
            )
        )
