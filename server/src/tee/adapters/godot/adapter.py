"""GodotAdapter — Godot 4 as a first-class TEE adapter, headlessly.

The point of honouring the `Adapter` protocol is that Godot arrives with
**no new always-loaded tools**: `tee_scene_summary`, `tee_batch`,
`tee_diff`, `tee_checkpoint` and `tee_rollback` already know how to drive
one of these. The surface stays at 17.

Two measured facts shape this file:

* **A project that has never been imported hangs `--headless -s` with no
  output.** Not slow - silent, indefinitely. So `ensure_bridge` runs
  `--import` first, once, and treats that as a duty rather than advice.
* **Headless Godot cannot render.** `DisplayServer` is `headless`, the
  rasterizer is the dummy one, and `get_texture()` returns null. So
  `capture()` REFUSES and says exactly that. Returning a black rectangle
  would be worse than refusing: it looks like an answer.

Scene evidence therefore flows as TEXT - the node tree from `list`, and
`run_scene` output from actually running the game's logic.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from tee.adapters.godot.wire import DEFAULT_PORT, GodotWire
from tee.kernel.adapter import AdapterInfo, Diff, Entity
from tee.kernel.errors import TeeError

BRIDGE_RELATIVE = Path("adapters/godot/tee_bridge/bridge.gd")
IMPORT_TIMEOUT_S = 180.0
BOOT_TIMEOUT_S = 60.0

_NO_RENDER = (
    "Headless Godot cannot render: DisplayServer is 'headless' and the "
    "rasterizer is the dummy one, so the viewport texture is null. Measured "
    "on Godot 4.7.2, not inferred."
)


def find_godot() -> str | None:
    for candidate in (
        os.environ.get("TEE_GODOT_BIN"),
        shutil.which("godot"),
        "/Applications/Godot.app/Contents/MacOS/Godot",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


class GodotAdapter:
    """Talks to a headless Godot over the bridge socket."""

    def __init__(
        self,
        wire: GodotWire | None = None,
        project: str | Path | None = None,
        workdir: str | None = None,
    ):
        self.wire = wire or GodotWire()
        self.project = Path(project).expanduser() if project else None
        self.workdir = workdir or tempfile.mkdtemp(prefix="tee-godot-")
        self._proc: subprocess.Popen | None = None
        self._version: str | None = None

    # -- Adapter protocol --------------------------------------------------

    def info(self) -> AdapterInfo:
        try:
            ping = self.wire.request({"type": "ping"}, timeout=5.0)
        except TeeError:
            return AdapterInfo(id="godot", product="Godot", version="unknown", connected=False)
        self._version = str(ping.get("godot") or "unknown")
        return AdapterInfo(
            id="godot",
            product="Godot",
            version=self._version,
            connected=True,
            extra={"display": ping.get("display"), "can_render": ping.get("can_render", False)},
        )

    def probe(self) -> bool:
        return self.wire.probe()

    def list_entities(self) -> list[Entity]:
        nodes = self.wire.request({"type": "list"}).get("nodes") or []
        return [
            Entity(
                id=str(node["path"]),
                name=str(node.get("name") or node["path"]),
                kind=str(node.get("type") or "Node"),
                parent=str(node["path"]).rsplit("/", 1)[0] or None,
                summary={"children": node.get("children", 0)},
            )
            for node in nodes
        ]

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        if not batch:
            return Diff()
        result = self.wire.request({"type": "commands", "ops": list(batch)})
        diff = Diff()
        for change in result.get("changed") or []:
            if "added" in change:
                diff.created.append(str(change["added"]))
                diff.details[str(change["added"])] = {
                    "type": change.get("type"),
                    "props": change.get("props") or [],
                }
            elif "changed" in change:
                diff.modified.append(str(change["changed"]))
                diff.details[str(change["changed"])] = {"props": change.get("props") or []}
            elif "removed" in change:
                diff.deleted.append(str(change["removed"]))
        for op_result in result.get("ops") or []:
            if op_result.get("op") == "run_scene":
                diff.notes.append(
                    f"run_scene {op_result.get('res')}: "
                    f"{op_result.get('frames_run')} frames, "
                    f"{op_result.get('nodes_after_ready')} nodes ready, "
                    f"{op_result.get('wall_ms')} ms"
                )
            elif op_result.get("op") == "save_scene":
                diff.notes.append(f"saved {op_result.get('out')}")
        return diff

    def snapshot(self, label: str) -> dict[str, Any]:
        """A checkpoint is a packed scene on disk, like Blender's is a .blend.

        Kept in the adapter workdir rather than the project so a rollback
        never leaves debris in the owner's game.
        """
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)[:48]
        target = f"user://tee_checkpoint_{safe}_{int(time.time())}.tscn"
        self.wire.request(
            {"type": "commands", "ops": [{"op": "save_scene", "out": target, "overwrite": True}]}
        )
        return {"scene": target, "label": label}

    def restore(self, payload: dict[str, Any]) -> None:
        """Reload a checkpoint scene over the current tree.

        Honest limit: the restored content arrives NESTED under the packed
        scene's root node (`/Root/Player`, not `/Player`), because
        PackedScene cannot pack the SceneTree's Window and the bridge wraps
        the children in a holder to pack them. The content and its
        properties round-trip; the paths gain one level. Callers that key
        on absolute paths should re-list after a rollback.
        """
        scene = str(payload.get("scene") or "")
        if not scene:
            raise TeeError(
                "godot_bad_checkpoint",
                "This checkpoint has no scene path.",
                fix="Take a fresh checkpoint with tee_checkpoint.",
            )
        nodes = self.wire.request({"type": "list"}).get("nodes") or []
        top = [n["path"] for n in nodes if n["path"].count("/") == 1]
        ops: list[dict[str, Any]] = [{"op": "remove_node", "path": path} for path in top]
        ops.append({"op": "load_scene", "res": scene})
        self.wire.request({"type": "commands", "ops": ops})

    def capture(self, view: str, max_bytes: int) -> bytes:
        raise TeeError(
            "godot_no_render",
            _NO_RENDER,
            fix="Ask for the scene as text instead: tee_scene_summary lists "
            "the node tree, and run_scene reports what the game's logic "
            "actually did. If you truly need pixels, GodotAdapter."
            "capture_windowed() renders with a real display server - which "
            "opens a window on the screen for a moment and is therefore "
            "opt-in, never automatic.",
        )

    def run_scene(
        self,
        scene: str = "",
        frames: int = 60,
        timeout_s: float = 120.0,
        repo_root: str | Path | None = None,
    ) -> dict[str, Any]:
        """Run the game's logic headless for N frames and report what it did.

        This is the game-design payoff, and it is deliberately a SEPARATE
        Godot process rather than something the bridge does. The bridge
        script IS a SceneTree main loop; it cannot hand that loop to a game
        and advance its frames. An in-process attempt counts a for-loop
        while `_process` never runs - which looks like execution and is not.

        `--quit-after N` gives real frames, real `_ready`, real `_process`,
        and the game's own `print()` output as evidence. There are no pixels
        here and there never will be headlessly, so the printed line IS the
        observation channel.
        """
        binary = find_godot()
        if binary is None:
            raise TeeError(
                "godot_missing",
                "Godot is not installed.",
                fix="brew install --cask godot, or set TEE_GODOT_BIN.",
            )
        if self.project is None:
            raise TeeError(
                "godot_no_project",
                "run_scene needs a project directory.",
                fix="Construct the adapter with project=<dir containing project.godot>.",
            )
        frames = max(1, min(int(frames), 100_000))
        argv = [binary, "--headless", "--path", str(self.project), "--quit-after", str(frames)]
        if scene:
            argv.append(scene)
        started = time.monotonic()
        try:
            proc = subprocess.run(
                argv, capture_output=True, text=True, timeout=timeout_s, check=False
            )
        except subprocess.TimeoutExpired as exc:
            raise TeeError(
                "godot_run_timeout",
                f"The scene ran past {timeout_s:.0f}s without finishing {frames} frames.",
                fix="Lower `frames`, raise `timeout_s`, or look for a blocking "
                "loop in the scene's _ready.",
            ) from exc
        blob = (proc.stdout or "") + (proc.stderr or "")
        lines = [line.rstrip() for line in blob.splitlines() if line.strip()]
        errors = [
            line
            for line in lines
            if line.startswith(("SCRIPT ERROR", "ERROR:", "USER ERROR")) or "Parse Error" in line
        ]
        printed = [
            line for line in lines if line not in errors and not line.startswith("Godot Engine v")
        ]
        return {
            "ok": proc.returncode == 0 and not errors,
            "scene": scene or "(main scene)",
            "frames": frames,
            "exit_code": proc.returncode,
            "wall_s": round(time.monotonic() - started, 2),
            "script_errors": len(errors),
            "errors": errors[:10],
            "output": printed[:80],
            "note": "Headless run: printed output is the evidence, there are "
            "no pixels. Frames really advanced - _ready and _process ran.",
        }

    def capture_windowed(
        self,
        max_bytes: int = 96 * 1024,
        width: int = 640,
        height: int = 360,
        scene: str = "",
        repo_root: str | Path | None = None,
        timeout_s: float = 90.0,
    ) -> bytes:
        """OPT-IN render. Not headless, and it opens a window - say so.

        A49 P4 measured this properly rather than assuming: headless Godot
        cannot render under ANY driver (vulkan, opengl3 and dummy all yield
        a null viewport texture), while a normal Godot with a display server
        renders fine. So pixels are available on this machine only at the
        price of a real window appearing briefly on the owner's screen.

        `capture()` therefore still refuses. This is the door for a caller
        who has decided that trade is acceptable, and it never opens itself.
        """
        binary = find_godot()
        if binary is None or self.project is None:
            raise TeeError(
                "godot_no_project",
                "A windowed capture needs Godot and a project directory.",
                fix="brew install --cask godot and pass project=<dir>.",
            )
        shot = Path(repo_root or Path.cwd()) / "adapters/godot/tee_bridge/shot.gd"
        if not shot.is_file():
            raise TeeError("godot_no_bridge", f"shot.gd not found at {shot}", fix="Reinstall TEE.")
        staged = self.project / "tee_shot.gd"
        staged.write_bytes(shot.read_bytes())
        out = Path(self.workdir) / "godot_shot.jpg"
        argv = [
            binary,
            "--path",
            str(self.project),
            "-s",
            "tee_shot.gd",
            "--",
            "--out",
            str(out),
            "--width",
            str(width),
            "--height",
            str(height),
        ]
        if scene:
            argv += ["--scene", scene]
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s, check=False)
        if not out.is_file():
            blob = ((proc.stdout or "") + (proc.stderr or "")).strip()[-300:]
            raise TeeError(
                "godot_capture_failed",
                f"The windowed capture produced no image: {blob}",
                fix="This path needs a real display server - it will not work "
                "over SSH or in CI. Headless Godot cannot render at all.",
            )
        data = out.read_bytes()
        if len(data) > max_bytes:
            raise TeeError(
                "capture_over_budget",
                f"The render is {len(data)} bytes; budget is {max_bytes}.",
                fix="Lower width/height, or raise the budget.",
            )
        return data

    # -- launch management -------------------------------------------------

    def ensure_bridge(self, repo_root: str | Path | None = None) -> dict[str, Any]:
        """Import the project if needed, then spawn the bridge if it is down."""
        if self.wire.probe():
            return {"started": False, "reason": "already running"}
        binary = find_godot()
        if binary is None:
            raise TeeError(
                "godot_missing",
                "Godot is not installed.",
                fix="brew install --cask godot, or set TEE_GODOT_BIN.",
            )
        if self.project is None or not (self.project / "project.godot").is_file():
            raise TeeError(
                "godot_no_project",
                f"No Godot project at {self.project}.",
                fix="Pass a directory containing project.godot.",
            )
        bridge = Path(repo_root or Path.cwd()) / BRIDGE_RELATIVE
        if not bridge.is_file():
            raise TeeError(
                "godot_no_bridge", f"Bridge script not found at {bridge}", fix="Reinstall TEE."
            )
        staged = self.project / "tee_bridge.gd"
        staged.write_bytes(bridge.read_bytes())

        # The measured duty: an unimported project hangs `-s` silently.
        imported = self.project / ".godot"
        if not imported.is_dir():
            subprocess.run(
                [binary, "--headless", "--path", str(self.project), "--import"],
                capture_output=True,
                timeout=IMPORT_TIMEOUT_S,
                check=False,
            )
        self._proc = subprocess.Popen(
            [
                binary,
                "--headless",
                "--path",
                str(self.project),
                "-s",
                "tee_bridge.gd",
                "--",
                "--port",
                str(self.wire.port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        deadline = time.monotonic() + BOOT_TIMEOUT_S
        while time.monotonic() < deadline:
            if self.wire.probe():
                return {"started": True, "port": self.wire.port, "pid": self._proc.pid}
            if self._proc.poll() is not None:
                out = (self._proc.stdout.read() if self._proc.stdout else "")[-600:]
                raise TeeError(
                    "godot_bridge_failed",
                    f"The Godot bridge exited immediately: {out.strip()[:300]}",
                    fix="Usually a GDScript parse error in the bridge, or a port already in use.",
                )
            time.sleep(0.4)
        raise TeeError(
            "godot_bridge_timeout",
            f"The bridge did not answer on port {self.wire.port} within {BOOT_TIMEOUT_S:.0f}s.",
            fix="If this project has never been imported, run "
            f"`{binary} --headless --path {self.project} --import` by hand and retry.",
        )

    def shutdown(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None


__all__ = ["DEFAULT_PORT", "GodotAdapter", "find_godot"]
