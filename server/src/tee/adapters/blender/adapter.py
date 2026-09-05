"""BlenderAdapter: the kernel Adapter contract over the bridge wire.

Works against either the official Blender Lab MCP add-on socket or TEE's
bridge add-on (same protocol). Runs on the same machine as Blender (the
bridge is localhost-only, decision A7), so snapshots and captures are plain
local files written by Blender and read back here.
"""

from __future__ import annotations

import os
import tempfile
import time
from typing import Any

from tee.adapters.blender import codegen
from tee.adapters.blender.shim import compact_traceback, firewall_check
from tee.adapters.blender.wire import BlenderWire
from tee.kernel.adapter import AdapterInfo, Diff, Entity, LaneVocab
from tee.kernel.errors import TeeError

_CAPTURE_FULL = (512, 288, 60)  # (width, height, jpeg quality)
_CAPTURE_SMALL = (256, 144, 40)
_CAPTURE_FLOOR = (160, 90, 30)
_CAPTURE_SAMPLES = 8
# Mirror of the bridge-side guard so the check also protects sessions that
# run against the official add-on (whose sandbox is explicitly weak).
_EXEC_DENYLIST = ("wm.quit_blender", "wm.read_factory_settings", "sys.exit(")
_SNAPSHOT_TIMEOUT = 60.0
_RESTORE_TIMEOUT = 120.0
_CAPTURE_TIMEOUT = 180.0


class BlenderAdapter:
    def __init__(self, wire: BlenderWire | None = None, workdir: str | None = None):
        self.wire = wire or BlenderWire()
        self.workdir = workdir or tempfile.mkdtemp(prefix="tee-blender-")
        self._version: tuple[int, int, int] | None = None
        self._snap_counter = 0

    # -- Adapter protocol --------------------------------------------------

    def info(self) -> AdapterInfo:
        try:
            data = self._call(codegen.program_info(), timeout=10.0)
        except TeeError:
            return AdapterInfo(id="blender", product="Blender", version="unknown", connected=False)
        self._version = tuple(data["version"])[:3]
        return AdapterInfo(
            id="blender",
            product="Blender",
            version=data["version_string"],
            connected=True,
            extra={
                "background": data["background"],
                "file": data["filepath"] or "(unsaved)",
                "objects": data["objects"],
            },
        )

    def probe(self) -> bool:
        return self.wire.probe()

    def vocab(self) -> LaneVocab:
        """What this lane accepts (A68) - exactly what codegen dispatches."""
        return LaneVocab(
            ops=codegen.BASE_OPS + codegen._MODELING_OPS,
            kinds=codegen.CREATE_KINDS,
            kind_optional=True,
            imports=codegen.IMPORT_SUFFIXES,
            renders=True,
            purpose="3D scene: model, materials, physics, render (pixels)",
        )

    def list_entities(self) -> list[Entity]:
        data = self._call(codegen.program_list_entities())
        return [_to_entity(e) for e in data["entities"]]

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        codegen.check_batch(batch)  # a foreign op is a structured refusal, not a traceback
        data = self._call(codegen.program_batch(batch, undo_label="TEE batch"))
        return Diff(
            created=data["created"],
            modified=data["modified"],
            deleted=data["deleted"],
            details=data["details"],
            upserts=[_to_entity(e) for e in data["entities"]],
        )

    def snapshot(self, label: str) -> dict[str, Any]:
        self._snap_counter += 1
        path = os.path.join(self.workdir, f"snap-{self._snap_counter}-{int(time.time())}.blend")
        self._call(codegen.program_snapshot(path), timeout=_SNAPSHOT_TIMEOUT)
        return {"label": label, "path": path}

    def restore(self, payload: dict[str, Any]) -> None:
        path = payload["path"]
        if not os.path.exists(path):
            raise TeeError(
                "snapshot_missing",
                f"Snapshot file is gone: {path}",
                fix="Older checkpoints may have been cleaned up; list with tee_status.",
            )
        self._call(codegen.program_restore(path), timeout=_RESTORE_TIMEOUT)

    def capture_look(
        self,
        max_bytes: int,
        *,
        target: str = "",
        azimuth_deg: float = 45.0,
        elevation_deg: float = 20.0,
        # A51 P2: distance now multiplies the SOLVED fit, so 1.0 means
        # "frame the subject at 80% of the tighter axis". It used to
        # multiply the raw bounding radius, where 2.2 was a guess.
        distance: float = 1.0,
    ) -> bytes:
        """Aimed temp-camera render (A47): same two-rung budget ladder and
        the same leave-the-scene-exactly-as-found contract as capture()."""
        path = os.path.join(self.workdir, "look.jpg")
        first = _CAPTURE_FULL if max_bytes >= 12 * 1024 else _CAPTURE_SMALL
        last_size = 0
        for width, height, quality in (first, _CAPTURE_FLOOR):
            self._call(
                codegen.program_capture_look(
                    path,
                    width,
                    height,
                    quality,
                    _CAPTURE_SAMPLES,
                    target,
                    azimuth_deg,
                    elevation_deg,
                    distance,
                ),
                timeout=_CAPTURE_TIMEOUT,
            )
            data = _read_file(path)
            last_size = len(data)
            if last_size <= max_bytes:
                return data
        raise TeeError(
            "capture_over_budget",
            f"Smallest render is {last_size} bytes; budget is {max_bytes}.",
            fix="Raise max_kb.",
        )

    def capture(self, view: str, max_bytes: int) -> bytes:
        """At most two renders (P8): one at a rung picked from the budget,
        one retry at the floor rung if the first came out over budget."""
        path = os.path.join(self.workdir, "capture.jpg")
        first = _CAPTURE_FULL if max_bytes >= 12 * 1024 else _CAPTURE_SMALL
        last_size = 0
        for width, height, quality in (first, _CAPTURE_FLOOR):
            self._call(
                codegen.program_capture(path, width, height, quality, _CAPTURE_SAMPLES),
                timeout=_CAPTURE_TIMEOUT,
            )
            data = _read_file(path)
            last_size = len(data)
            if last_size <= max_bytes:
                return data
        raise TeeError(
            "capture_over_budget",
            f"Smallest render is {last_size} bytes; budget is {max_bytes}.",
            fix="Raise max_kb, or use scene queries instead of an image.",
        )

    # -- escape hatch (used by the bl_execute_python virtual tool) ---------

    def execute_python(self, code: str, timeout: float | None = None) -> dict[str, Any]:
        """Run arbitrary Python in Blender, guarded by the version firewall.
        The caller (virtual tool) is responsible for checkpointing first."""
        for banned in _EXEC_DENYLIST:
            if banned in code:
                raise TeeError(
                    "refused",
                    f"'{banned}' is blocked by the TEE guard.",
                    fix="Quitting Blender, factory resets and sys.exit are never allowed.",
                )
        version = self._version or self._fetch_version()
        hits = firewall_check(code, version)
        if hits:
            hints = "; ".join(h["hint"] for h in hits[:3])
            raise TeeError(
                "stale_api",
                f"Code uses {len(hits)} API idiom(s) invalid on Blender "
                f"{'.'.join(map(str, version))}: " + ", ".join(h["code"] for h in hits) + ".",
                fix=hints,
            )
        response = self.wire.execute(code, strict_json=False, timeout=timeout)
        if response.get("status") != "ok":
            raise TeeError(
                "blender_exec_error",
                compact_traceback(str(response.get("message", "unknown error"))),
                fix="Fix the code and retry; state may be partially changed - "
                "roll back with tee_rollback if needed.",
            )
        out: dict[str, Any] = {"result": response.get("result", {})}
        for stream in ("stdout", "stderr"):
            if response.get(stream):
                out[stream] = str(response[stream])[-2000:]
        return out

    # -- resource management -----------------------------------------------

    def discard_snapshot(self, payload: dict[str, Any]) -> None:
        """Called by the checkpoint manager when a checkpoint is evicted or
        can no longer be rolled back to - releases its .blend file."""
        path = payload.get("path")
        if path and os.path.dirname(path) == self.workdir:
            with _suppress_oserror():
                os.remove(path)

    def close(self) -> None:
        import shutil

        shutil.rmtree(self.workdir, ignore_errors=True)

    # -- internals ---------------------------------------------------------

    def _call(self, code: str, timeout: float | None = None) -> dict[str, Any]:
        response = self.wire.execute(code, strict_json=True, timeout=timeout)
        if response.get("status") != "ok":
            raise TeeError(
                "blender_error",
                compact_traceback(str(response.get("message", "unknown error"))),
                fix="If this batch partially applied, roll back with tee_rollback.",
            )
        result = response.get("result")
        if not isinstance(result, dict):
            raise TeeError("blender_bad_result", "Bridge returned a non-dict result.")
        return result

    def _fetch_version(self) -> tuple[int, int, int]:
        info = self.info()
        if not info.connected or self._version is None:
            raise TeeError(
                "blender_unreachable",
                "Cannot determine the Blender version (bridge down?).",
                fix="Check tee_status.",
            )
        return self._version


def _to_entity(data: dict[str, Any]) -> Entity:
    summary = {k: v for k, v in data.items() if k not in ("id", "name", "kind", "parent")}
    return Entity(
        id=data["id"],
        name=data["name"],
        kind=data["kind"],
        parent=data.get("parent"),
        summary=summary,
    )


def _suppress_oserror():
    import contextlib

    return contextlib.suppress(OSError)


def _read_file(path: str) -> bytes:
    try:
        with open(path, "rb") as fh:
            return fh.read()
    except OSError as exc:
        raise TeeError(
            "capture_failed",
            f"Blender reported success but no file at {path}.",
            fix="Retry; check disk space on the Blender machine.",
        ) from exc
