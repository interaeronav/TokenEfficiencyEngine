"""PartkilnAdapter: mechanical parts as a TEE scene, with zero new always-loaded tools.

A66 P4. A part is a scene: sketches, features, bodies, components, mates,
drawings and exports are entities with stable prefixed ids (D7), an edit is
a batch, and what changed is a diff - so `tee_scene_summary`, `tee_batch`,
`tee_diff`, `tee_checkpoint` and `tee_rollback` drive a CAD document the way
they drive Blender, and the 17-tool surface does not move (measured: 2,033
tok before and after). The seamkiln precedent, carried over whole.

Two kernels, one Protocol (D2). `LocalKernel` runs in this interpreter when
`find_spec("partkiln")` AND `find_spec("OCP")` both succeed (the repo dev
venv); otherwise `SidecarKernel` spawns `python -m partkiln.worker` in the
venv under `~/TEE/.tee/sidecars/partkiln`, which survives the extension wipe
and `tee_purge`. The adapter never learns which one it holds. Why a warm-up
JOB and not an import: `import OCP` costs 26 s COLD in a fresh venv and 0.29 s
warm (P0a, 2026-09-02). Law 17 says that never blocks a call, so `warm()` is
submitted at boot, `probe()` never waits, `list_entities()` and `snapshot()`
answer from an in-process mirror while it runs, and `execute()` refuses
`pk_warming` with the job id after a two-second grace.

Everything a batch can change reaches `Diff.upserts` (the SceneCache goes
blind otherwise - the A65 lesson); a failed command is ONE `TeeError` with
the kernel's own code, message and fix, and it says the batch rolled back,
because the kernel already did that (Law 16). The checkpoint is the script;
the `.brep` beside it is a cache (D3). No pixels: `capture()` refuses
`pk_capture_text_first` naming the three text routes AND, step by step, the
manual GLB-through-Blender route - which is manual because this process
serves one adapter and holds no Blender to import into.
"""

from __future__ import annotations

import contextlib
import json
import time
import weakref
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from tee.adapters.partkiln.wire import DEFAULT_TIMEOUT_S, INSTALL_LINE, SIDECAR_PY
from tee.kernel.adapter import AdapterInfo, Diff, Entity
from tee.kernel.errors import TeeError

# The dev route: OCP is ALREADY in server/.venv, and `cadquery-ocp-novtk`
# ships the same top-level `OCP/` package - installing `[brep]` there would
# clobber the VTK wheel (P0a row 3). So: no extra.
DEV_INSTALL = "uv pip install --python server/.venv/bin/python -e partkiln"
SIDECAR_INSTALL = INSTALL_LINE
INSTALL_HINT = (
    "partkiln is reachable by neither route. Dev venv (OCP is already there - never add "
    f"[brep], novtk would clobber it): {DEV_INSTALL} . Production sidecar (Python 3.11; "
    f"survives the extension wipe and tee_purge): {SIDECAR_INSTALL}"
)
READY_GRACE_S = 2.0  # execute() waits this long for a warm-up already in flight
COLD_IMPORT_S = 26.0  # measured P0a: `import OCP` in a fresh venv
WARM_IMPORT_S = 0.29  # measured P0a: the same import, second time

# D5: the closed wire vocabulary. `export` and `check` ride in a batch and are
# kernel verbs when the kernel registers them, `pk_*` methods otherwise.
_WIRE_OPS = ("create", "set", "delete", "param_set", "export", "check")
_DEFERRABLE = ("export", "check")
_BASE_VERBS = ("create", "delete", "param_set", "set")
# D7 id prefixes <-> entity kinds when a row carries no `kind`.
_KIND_OF_PREFIX = {
    "doc": "doc",
    "param": "param",
    "plane": "datum",
    "axis": "datum",
    "point": "datum",
    "sk": "sketch",
    "feat": "feature",
    "part": "body",
    "cmp": "component",
    "mate": "mate",
    "jt": "joint",
    "asm": "assembly",
    "dwg": "drawing",
    "vw": "view",
    "dim": "dimension",
    "sheet": "sheet",
    "export": "export",
    "obj": "object",
}


def _in_process_available() -> bool:
    """The dev route: both the kernel and OCP importable HERE. `find_spec`
    only - importing OCP is the 26 s this whole design keeps out of a call."""
    try:
        return find_spec("partkiln") is not None and find_spec("OCP") is not None
    except (ImportError, ValueError):
        return False


# A66 gap 2: every adapter built in THIS process, so a lane holding no
# adapter handle can ask whether an OCCT kernel is already warm here before
# it spawns a second one. A WeakSet, so registration never keeps an adapter
# alive and `close()` empties the kernel it would otherwise have offered.
_LIVE: weakref.WeakSet[PartkilnAdapter] = weakref.WeakSet()


def live_kernel() -> Any | None:
    """A partkiln kernel this process ALREADY holds warm, or None.

    The caller is `tee.fleet.cad`: with no in-process CadQuery, `cad_measure`
    spawns a one-shot interpreter that pays a fresh OCP import to read one
    volume - 1,531.2 ms measured on bracket.step (88,585 B, 2026-09-04)
    against 23.0 ms on a kernel that is already warm. Two OCCT processes
    where one would do.

    Nothing is started, warmed or respawned here, and that is the whole
    contract: a cold, warming, dead or absent kernel answers None and the
    caller keeps the route it had. `state == "warm"` is the gate rather than
    "a kernel object exists" because a `LocalKernel` imports OCP lazily, and
    a read-compute tool that silently paid the 26 s cold import would break
    Law 17 in the one place nobody would look for it.
    """
    for adapter in list(_LIVE):
        kernel = adapter._kernel
        if kernel is None or adapter._state != "warm":
            continue
        alive = getattr(kernel, "alive", None)
        if callable(alive) and not alive():
            continue
        return kernel
    return None


class PartkilnAdapter:
    """A mechanical CAD document, in-process or in the sidecar that survives upgrades."""

    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        workdir: str | Path | None = None,
        kernel: Any = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.workdir = Path(workdir or (self.project_root / ".tee" / "partkiln"))
        self.config = dict(config or {})
        self._kernel = kernel
        self._injected = kernel is not None
        self._spawned = False
        self._mode = "injected" if kernel is not None else None
        self._state = "cold"  # cold | warming | warm | error
        self._warm: dict[str, Any] | None = None
        self._warm_started: float | None = None
        self.warm_job: str | None = None
        self._verbs: tuple[str, ...] | None = None
        self._rows: list[dict[str, Any]] = []  # the D7 mirror: last known entity rows
        self._history: list[dict[str, Any]] = []  # the script mirror: every applied command
        self._doc_name = "untitled"
        self._notes: list[str] = []  # respawn notes, drained into the next diff
        self._epoch = 0
        _LIVE.add(self)

    # -- routes and the kernel ------------------------------------------------

    def _sidecar_python(self) -> Path:
        override = self.config.get("python")
        return Path(str(override)).expanduser() if override else SIDECAR_PY

    def _routes(self) -> dict[str, bool]:
        return {
            "injected": self._injected,
            "in-process": _in_process_available(),
            "sidecar": self._sidecar_python().is_file(),
        }

    def _need(self) -> None:
        """Refuse only when BOTH routes are absent; the hint names both."""
        routes = self._routes()
        if not any(routes.values()):
            raise TeeError("pk_kernel_absent", INSTALL_HINT, fix=INSTALL_HINT)

    def _select_kernel(self) -> Any:
        self._need()
        if _in_process_available():
            from partkiln.client import LocalKernel

            self._mode = "in-process"
            return LocalKernel(mode="local")
        from tee.adapters.partkiln.wire import SidecarKernel

        self._mode = "sidecar"
        timeout = float(self.config.get("batch_timeout_s") or DEFAULT_TIMEOUT_S)
        return SidecarKernel(
            self._sidecar_python(),
            timeout_s=timeout,
            stderr_path=self.workdir / "worker.log",
        )

    @property
    def mode(self) -> str:
        if self._mode is not None:
            return self._mode
        routes = self._routes()
        if routes["in-process"]:
            return "in-process"
        if routes["sidecar"]:
            return "sidecar"
        return "absent"

    @property
    def kernel(self) -> Any:
        """The kernel, selected on first use; a sidecar is (re)spawned here.

        A respawn after a death replays the script mirror (0.09-0.46 s per
        100 cuts, P0a) and leaves a note for the next diff - death is cheap
        because the state was never only in the worker (D2)."""
        if self._kernel is None:
            self._kernel = self._select_kernel()
        kernel = self._kernel
        alive = getattr(kernel, "alive", None)
        start = getattr(kernel, "start", None)
        if callable(alive) and callable(start) and not alive():
            ready = start()
            if self._spawned and self._history:
                kernel.apply([dict(c) for c in self._history])
                self._notes.append(
                    f"worker respawned (pid {ready.get('pid')}) and the script replayed: "
                    f"{len(self._history)} command(s)"
                )
            elif self._spawned:
                self._notes.append(f"worker respawned (pid {ready.get('pid')}); empty document")
            self._spawned = True
            if self._state == "warm" and not ready.get("warm"):
                self._state = "cold"  # a fresh process has not paid the import
        return kernel

    # -- warm-up (Law 17) -------------------------------------------------------

    def warm(self) -> dict[str, Any]:
        """Pay the OCP import, as a job. `{import_s, rss_mb, occt, mode, ocp}`."""
        self._need()
        self._state = "warming"
        self._warm_started = time.monotonic()
        try:
            report = dict(self.kernel.warm())
        except Exception as exc:
            self._state = "error"
            raise self._refusal(exc, "warm") from exc
        self._state = "warm"
        self._warm = report
        with contextlib.suppress(OSError, TypeError, ValueError):
            self.workdir.mkdir(parents=True, exist_ok=True)
            (self.workdir / "warm.json").write_text(
                json.dumps({**report, "mode": self.mode, "at": time.time()}, default=str)
            )
        return report

    def submit_warm(self, jobs: Any) -> str:
        """The boot hook: `_build_partkiln_app` submits the import as an
        interactive job so no call ever waits on it."""
        self.warm_job = jobs.submit("partkiln_warm", self.warm, qos="interactive")
        return self.warm_job

    @property
    def state(self) -> str:
        return self._state

    def _wait_ready(self) -> None:
        """Two seconds of grace for a warm-up in flight, then `pk_warming`."""
        if self._state != "warming":
            return
        deadline = time.monotonic() + READY_GRACE_S
        while self._state == "warming" and time.monotonic() < deadline:
            time.sleep(0.05)
        if self._state == "warming":
            elapsed = time.monotonic() - (self._warm_started or time.monotonic())
            job = self.warm_job or "partkiln_warm"
            raise TeeError(
                "pk_warming",
                f"the partkiln kernel is still importing OCP (job {job}, {elapsed:.1f} s so far; "
                f"measured {COLD_IMPORT_S:.0f} s cold, {WARM_IMPORT_S} s warm).",
                fix=f"poll tee_job(job='{job}') and retry the batch; tee_scene_summary, "
                "tee_checkpoint and pk_probe answer now from the in-process mirror.",
            )

    # -- Adapter protocol --------------------------------------------------------

    def info(self) -> AdapterInfo:
        routes = self._routes()
        connected = any(routes.values())
        version = "absent"
        if find_spec("partkiln") is not None:
            with contextlib.suppress(Exception):
                import partkiln

                version = str(getattr(partkiln, "__version__", "0.1.0"))
        elif self._kernel is not None:
            ready = getattr(self._kernel, "ready", None) or {}
            version = str(ready.get("partkiln") or version)
        rows = self._rows
        extra: dict[str, Any] = {
            "mode": self.mode,
            "state": self._state,
            "occt": (self._warm or {}).get("occt"),
            "parts": sum(1 for r in rows if str(r.get("id", "")).startswith("part:")),
            "assemblies": sum(1 for r in rows if str(r.get("id", "")).startswith("asm")),
            "drawings": sum(1 for r in rows if str(r.get("id", "")).startswith("dwg:")),
            "commands": len(self._history),
        }
        if self._kernel is not None and self._state != "warming":
            with contextlib.suppress(Exception):
                facts = self._kernel.info()
                extra["occt"] = facts.get("occt") or extra["occt"]
                for key in ("parts", "assemblies", "drawings", "commands"):
                    if isinstance(facts.get(key), int):
                        extra[key] = facts[key]
        if self.warm_job:
            extra["warm_job"] = self.warm_job
        if not connected:
            extra["fix"] = INSTALL_HINT
        return AdapterInfo(
            id="partkiln", product="partkiln", version=version, connected=connected, extra=extra
        )

    def probe(self) -> bool:
        """Alive or importable. Never a round trip, never an import."""
        if self._injected:
            probe = getattr(self._kernel, "probe", None)
            return bool(probe()) if callable(probe) else True
        return any(self._routes().values())

    def list_entities(self) -> list[Entity]:
        """The D7 rows, from the mirror while the kernel is warming."""
        if not self.probe():
            return []
        if self._state == "warming":
            return [_entity(row) for row in self._rows]
        try:
            rows = self.kernel.entities()
        except Exception as exc:
            if not self._recoverable(exc):
                raise self._refusal(exc, "entities") from exc
            rows = self.kernel.entities()  # the property respawned and replayed
        self._rows = [dict(row) for row in rows if isinstance(row, dict) and row.get("id")]
        return [_entity(row) for row in self._rows]

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        """Pure translation, ONE `apply` round trip, then a diff with upserts."""
        self._need()
        kernel = self.kernel
        self._wait_ready()
        commands: list[tuple[int, dict[str, Any]]] = []
        for index, op in enumerate(batch):
            commands.extend((index, command) for command in _translate(op, index))
        apply_cmds, deferred = _split(commands, self.verbs())
        diff = Diff()
        diff.notes.extend(self._drain_notes())
        if apply_cmds:
            try:
                outcome = kernel.apply([dict(c) for c in apply_cmds])
            except Exception as exc:
                raise self._refusal(exc, "apply") from exc
            self._history.extend(json.loads(json.dumps(c, default=str)) for c in apply_cmds)
            self._doc_name = _doc_name(apply_cmds, self._doc_name)
            _record(apply_cmds, outcome, diff)
        for index, verb, props in deferred:
            try:
                result = kernel.call(verb, dict(props))
            except Exception as exc:
                raise self._refusal(exc, f"{verb} (batch[{index}])") from exc
            _record_deferred(verb, props, result, diff)
        self._refresh_upserts(diff)
        self._epoch += 1
        return diff

    def snapshot(self, label: str) -> dict[str, Any]:
        """D3: the script (+ one .brep per body) under .tee/partkiln; scalars back."""
        self.workdir.mkdir(parents=True, exist_ok=True)
        if self._state == "warming" or (self._kernel is None and not self._history):
            return self._mirror_snapshot(label)
        try:
            payload = dict(self.kernel.snapshot(label, str(self.workdir)))
        except Exception as exc:
            if not self._recoverable(exc):
                raise self._refusal(exc, "snapshot") from exc
            payload = dict(self.kernel.snapshot(label, str(self.workdir)))
        payload["epoch"] = self._epoch
        payload.setdefault("brep", False)
        return payload

    def restore(self, payload: dict[str, Any]) -> None:
        """Reload the checkpoint: the .brep fast path when it matches, else replay."""
        self._need()
        try:
            self.kernel.restore(payload)
        except Exception as exc:
            raise self._refusal(exc, "restore") from exc
        self._history = self._script_commands()
        self._epoch += 1
        with contextlib.suppress(Exception):
            self._rows = [dict(r) for r in self.kernel.entities() if isinstance(r, dict)]

    def discard_snapshot(self, payload: dict[str, Any]) -> None:
        """Unlink the checkpoint's json AND the .brep caches it names."""
        if not isinstance(payload, dict):
            return
        path = Path(str(payload.get("path") or ""))
        if payload.get("path") and path.is_file():
            with contextlib.suppress(OSError, ValueError):
                data = json.loads(path.read_text(encoding="utf-8"))
                for entry in (data.get("parts") or {}).values():
                    brep = entry.get("brep") if isinstance(entry, dict) else None
                    if brep:
                        (path.parent / str(brep)).unlink(missing_ok=True)
            with contextlib.suppress(OSError):
                path.unlink()
        if self._kernel is not None and not payload.get("mirror"):
            with contextlib.suppress(Exception):
                self._kernel.discard(payload)

    def capture(self, view: str, max_bytes: int) -> bytes:
        """Refuse pixels, and name a route the caller can actually walk.

        A66 gap 3. The shipped refusal advertised "a JPEG through Blender is
        the P6 opt-in" and no such opt-in was ever built - a fix naming a
        door that is not there is worse than a plain no, because the reader
        goes looking for it. There is no in-adapter shortcut to build
        either: `cli._build_partkiln_app` serves ONE adapter, so this
        process holds no Blender adapter for `as_import` to run a batch on,
        and `capture()` receives no app handle to reach the asset lane with.
        So the honest ending is the manual route, step by step, in the order
        the acceptance session ran it (`examples/acceptance/run_tee.py`
        step 7), with every tool named exactly as it is registered.
        """
        raise TeeError(
            "pk_capture_text_first",
            "partkiln renders no pixels: the numbers are the evidence and a model's eye is advice.",
            fix="Text first: pk_drawing writes an SVG/DXF/PDF sheet (views and dimensions "
            "READ from the model); pk_measure answers mass, bbox, clearance and "
            "interference; tee_entity_detail answers one entity. For a JPEG, hand the part "
            "to Blender yourself - a TEE served on partkiln holds only that adapter, so "
            "nothing in this session can do it for you: (1) pk_export format=glb "
            "out=<dir>/<name>.glb "
            "target=blender, writing into a directory that holds that GLB alone (as_ingest "
            "keys a local asset by file STEM, so bracket.glb beside bracket.stl is one "
            "entry and the last one wins); (2) in a TEE served on Blender (tee serve "
            "--adapter blender, with the bridge add-on answering): as_ingest "
            "directory=<dir>; (3) as_import asset=local:<name> adapter=blender "
            "asset_class=model target_dims=[x, y, z] - metres and Z-up, which is "
            "pk_measure what=bbox / 1000, NOT the GLB manifest's Y-up extents - and it "
            "verifies the read-back dimensions; (4) tee_capture adapter=blender.",
        )

    def close(self) -> None:
        kernel, self._kernel = self._kernel, None
        if kernel is not None and not self._injected:
            with contextlib.suppress(Exception):
                kernel.shutdown()

    # -- the generic door for the pk_* tools --------------------------------------

    def call(self, method: str, args: dict[str, Any] | None = None) -> Any:
        """`kernel.call(method, args)` with the warming guard and the error map."""
        self._need()
        kernel = self.kernel
        self._wait_ready()
        try:
            return kernel.call(method, dict(args or {}))
        except Exception as exc:
            raise self._refusal(exc, method) from exc

    def health(self) -> dict[str, Any]:
        """`pk_probe`: never waits, never refuses - absent is an answer."""
        routes = self._routes()
        out: dict[str, Any] = {
            "mode": self.mode,
            "state": self._state,
            "routes": routes,
            "warm": self._warm,
            "warm_job": self.warm_job,
            "commands": len(self._history),
            "cold_import_s": COLD_IMPORT_S,
            "warm_import_s": WARM_IMPORT_S,
        }
        if not any(routes.values()):
            out["fix"] = INSTALL_HINT
            return out
        if self._kernel is not None and self._state != "warming":
            with contextlib.suppress(Exception):
                out["kernel"] = self._kernel.info()
            with contextlib.suppress(Exception):
                out["probe"] = self._kernel.call("probe", {})
        return out

    def verbs(self) -> tuple[str, ...]:
        """The kernel's verb set: asked once, else the closed base set."""
        if self._verbs is not None:
            return self._verbs
        found: list[str] = []
        with contextlib.suppress(Exception):
            answer = self.kernel.call("verbs", {})
            found = _verb_names(answer)
        if not found and find_spec("partkiln") is not None:
            with contextlib.suppress(Exception):
                from partkiln import document

                found = list(document.VERBS)
        self._verbs = tuple(sorted(set(found) or set(_BASE_VERBS)))
        return self._verbs

    # -- internals ---------------------------------------------------------------------

    def _drain_notes(self) -> list[str]:
        notes, self._notes = self._notes, []
        return notes

    def _recoverable(self, exc: Exception) -> bool:
        """A dead or killed worker: the kernel property respawns and replays."""
        code = getattr(exc, "code", None)
        if code not in ("pk_worker_dead", "pk_worker_down", "pk_worker_timeout"):
            return False
        return self._kernel is not None and callable(getattr(self._kernel, "start", None))

    def _refusal(self, exc: Exception, during: str) -> TeeError:
        """One TeeError carrying the kernel's code, message and fix (rule 6)."""
        if isinstance(exc, TeeError):
            fix = exc.fix or ""
            if during == "apply" and "rolled back" not in (exc.message + fix):
                fix = (fix + " " if fix else "") + "The kernel rolled the batch back."
            return TeeError(exc.code, exc.message, fix=fix or exc.message)
        code = str(getattr(exc, "code", None) or "pk_op_failed")
        message = str(getattr(exc, "message", None) or exc)
        fix = str(getattr(exc, "fix", None) or "")
        if not fix:
            _, sep, tail = message.partition(" Fix: ")
            fix = tail if sep else message
        if during == "apply" and "rolled back" not in message and "rolled back" not in fix:
            fix = f"{fix} The kernel rolled the batch back; the document is unchanged."
        return TeeError(code, message, fix=fix)

    def _script_commands(self) -> list[dict[str, Any]]:
        with contextlib.suppress(Exception):
            script = self.kernel.script()
            commands = script.get("commands") if isinstance(script, dict) else None
            if isinstance(commands, list):
                self._doc_name = str(script.get("name") or self._doc_name)
                return [dict(c) for c in commands if isinstance(c, dict)]
        return list(self._history)

    def _mirror_snapshot(self, label: str) -> dict[str, Any]:
        """While warming: the script IS the state (Law 16); restore replays it."""
        stem = "".join(ch if ch.isalnum() or ch in "_.-" else "_" for ch in label) or "checkpoint"
        path = self.workdir / f"{stem}-{self._epoch}-{int(time.time() * 1000)}.json"
        payload = {
            "partkiln_snapshot": 1,
            "label": label,
            "script": {
                "partkiln_script": 1,
                "name": self._doc_name,
                "commands": list(self._history),
            },
            "fingerprint": None,
            "parts": {},
        }
        path.write_text(json.dumps(payload, indent=1, default=str), encoding="utf-8")
        return {
            "label": label,
            "path": str(path),
            "epoch": self._epoch,
            "commands": len(self._history),
            "fingerprint": None,
            "brep": False,
            "mirror": True,
        }

    def _refresh_upserts(self, diff: Diff) -> None:
        """Every created/modified id reaches `Diff.upserts`, from the kernel's
        rows where it has one and from the diff's own details otherwise."""
        wanted = [eid for eid in (*diff.created, *diff.modified) if eid not in diff.deleted]
        if wanted:
            with contextlib.suppress(Exception):
                self._rows = [
                    dict(row)
                    for row in self.kernel.entities()
                    if isinstance(row, dict) and row.get("id")
                ]
        by_id = {row["id"]: row for row in self._rows}
        seen: set[str] = set()
        for eid in wanted:
            if eid in seen:
                continue
            seen.add(eid)
            row = by_id.get(eid)
            if row is None:
                row = {"id": eid, **(diff.details.get(eid) or {})}
            diff.upserts.append(_entity(row))
        for eid in diff.deleted:
            self._rows = [row for row in self._rows if row.get("id") != eid]


# -- pure translation (tested with no kernel at all) ------------------------------------


def _translate(op: dict[str, Any], index: int) -> list[dict[str, Any]]:
    """One wire op -> the kernel commands that carry it out. Never mutates `op`."""
    verb = op.get("op")
    if verb not in _WIRE_OPS:
        raise TeeError(
            "pk_bad_op",
            f"batch[{index}]: unknown op {verb!r}.",
            fix=f"partkiln accepts: {', '.join(_WIRE_OPS)}. pk_verbs lists every create kind "
            "with an example.",
        )
    raw_props = op.get("props")
    if raw_props is not None and not isinstance(raw_props, dict):
        raise TeeError(
            "pk_bad_request",
            f"batch[{index}]: props must be an object of field: value.",
            fix='write {"op": ..., "props": {"distance": "10mm"}}.',
        )
    props = dict(raw_props or {})
    if verb == "create":
        kind = op.get("kind")
        if not kind:
            raise TeeError(
                "pk_needs",
                f"batch[{index}]: create needs kind.",
                fix="kinds: part, sketch, extrude, revolve, sweep, loft, hole, fillet, chamfer, "
                "shell, draft, pattern, mirror, combine, split, plane, axis, point, component, "
                "mate, joint, drawing, sheet (pk_verbs has an example of each).",
            )
        command: dict[str, Any] = {"op": "create", "kind": str(kind), "props": props}
        if op.get("name") is not None:
            command["name"] = str(op["name"])
        if op.get("id") is not None and "part" not in props:
            command["props"]["part"] = _kernel_name(str(op["id"]), "part")
        return [command]
    if verb == "set":
        target = str(op.get("id") or op.get("kind") or "doc")
        if target.startswith("param:"):
            name = target[len("param:") :]
            if "value" not in props:
                raise TeeError(
                    "pk_needs",
                    f"batch[{index}]: set {target} needs props.value.",
                    fix=f'{{"op": "set", "id": "{target}", "props": {{"value": "12mm"}}}} or '
                    'op param_set with {"props": {"name": value}}.',
                )
            return [{"op": "param_set", "params": {name: props["value"]}}]
        if not props:
            raise TeeError(
                "pk_needs",
                f"batch[{index}]: set {target} needs props.",
                fix="any creation prop, suppressed, material or name; for doc: units, standard, "
                "angle, strict_units.",
            )
        return [{"op": "set", "id": target, "props": props}]
    if verb == "delete":
        target = op.get("id")
        if not target:
            raise TeeError(
                "pk_needs",
                f"batch[{index}]: delete needs id.",
                fix='{"op": "delete", "id": "feat:h", "props": {"cascade": true}}.',
            )
        command = {"op": "delete", "id": str(target)}
        if props.get("cascade"):
            command["cascade"] = True
        return [command]
    if verb == "param_set":
        inner = props.get("params")
        params = dict(inner) if isinstance(inner, dict) else props
        if not params:
            raise TeeError(
                "pk_needs",
                f"batch[{index}]: param_set needs {{name: value}} pairs.",
                fix='{"op": "param_set", "props": {"W": "120mm", "H": "W/2 - 5mm"}}.',
            )
        return [{"op": "param_set", "params": params}]
    return [{"op": str(verb), "props": props}]  # export / check


def _split(
    commands: list[tuple[int, dict[str, Any]]], verbs: tuple[str, ...]
) -> tuple[list[dict[str, Any]], list[tuple[int, str, dict[str, Any]]]]:
    """Kernel verbs go into the one `apply`; `export`/`check` the kernel does not
    register as verbs run as methods AFTER it (on the finished document)."""
    apply_cmds: list[dict[str, Any]] = []
    deferred: list[tuple[int, str, dict[str, Any]]] = []
    for index, command in commands:
        verb = command["op"]
        if verb in _DEFERRABLE and verb not in verbs:
            deferred.append((index, verb, dict(command.get("props") or {})))
        else:
            apply_cmds.append(command)
    return apply_cmds, deferred


def _kernel_name(entity_id: str, prefix: str) -> str:
    head, sep, tail = entity_id.partition(":")
    return tail if sep and head == prefix else entity_id


def _verb_names(answer: Any) -> list[str]:
    if isinstance(answer, dict):
        inner = answer.get("verbs", answer.get("ops"))
        if isinstance(inner, dict):
            return [str(k) for k in inner]
        if isinstance(inner, list | tuple):
            return [str(v) for v in inner]
        return [str(k) for k in answer if isinstance(k, str)]
    if isinstance(answer, list | tuple):
        return [str(v) for v in answer if isinstance(v, str)]
    return []


def _doc_name(commands: list[dict[str, Any]], current: str) -> str:
    for command in commands:
        if command.get("op") == "set" and command.get("id") == "doc":
            name = (command.get("props") or {}).get("name")
            if name:
                current = str(name)
    return current


# -- results -> diff --------------------------------------------------------------------------


def _touch(diff: Diff, eid: str) -> None:
    if eid and eid not in diff.created and eid not in diff.modified:
        diff.modified.append(eid)


def _lift_regen(result: dict[str, Any], diff: Diff) -> None:
    """Law 14: the blast radius the kernel answers under `regen` becomes
    `details[part:<n>]`, and every feature it changed is a modified id."""
    regen = result.get("regen")
    if not isinstance(regen, dict):
        return
    for part_id, report in regen.items():
        if not isinstance(report, dict):
            continue
        _touch(diff, str(part_id))
        diff.details[str(part_id)] = dict(report)
        for row in report.get("changed") or ():
            if isinstance(row, dict) and row.get("feature"):
                _touch(diff, f"feat:{row['feature']}")
        for row in report.get("failed") or ():
            if isinstance(row, dict) and row.get("feature"):
                _touch(diff, f"feat:{row['feature']}")
                diff.notes.append(f"feat:{row['feature']} failed: {row.get('error', '')}"[:200])


def _record(commands: list[dict[str, Any]], outcome: Any, diff: Diff) -> None:
    results = outcome.get("results") if isinstance(outcome, dict) else None
    if not isinstance(results, list):
        results = []
    for command, result in zip(commands, results, strict=False):
        if not isinstance(result, dict):
            continue
        verb = command.get("op")
        eid = result.get("id")
        part = result.get("part")
        if verb == "create":
            if eid:
                diff.created.append(str(eid))
                diff.details[str(eid)] = {k: v for k, v in result.items() if k != "regen"}
            if part and part != eid:
                _touch(diff, str(part))
        elif verb == "set":
            if eid:
                _touch(diff, str(eid))
                diff.details[str(eid)] = {k: v for k, v in result.items() if k != "regen"}
            if part and part != eid:
                _touch(diff, str(part))
        elif verb == "param_set":
            for row in result.get("changed") or ():
                if isinstance(row, dict) and row.get("name"):
                    pid = f"param:{row['name']}"
                    _touch(diff, pid)
                    diff.details[pid] = {"old": row.get("old"), "new": row.get("new")}
            for row in result.get("sketches") or ():
                if isinstance(row, dict) and row.get("id"):
                    _touch(diff, str(row["id"]))
                    diff.details[str(row["id"])] = {k: v for k, v in row.items() if k != "id"}
            if result.get("assumed"):
                diff.details.setdefault("doc", {})["assumed"] = result["assumed"]
        elif verb == "delete":
            gone = result.get("deleted")
            for item in gone if isinstance(gone, list) else [gone]:
                if item:
                    diff.deleted.append(str(item))
            for item in result.get("cascaded") or ():
                diff.deleted.append(str(item))
            if part:
                _touch(diff, str(part))
                report = {
                    k: v
                    for k, v in result.items()
                    if k in ("changed", "unchanged", "failed", "volume_mm3", "faces")
                }
                if report:
                    diff.details[str(part)] = report
        else:
            _record_deferred(str(verb), dict(command.get("props") or {}), result, diff)
        _lift_regen(result, diff)
        for note in result.get("notes") or ():
            if note and note not in diff.notes:
                diff.notes.append(str(note))
    for eid in list(diff.deleted):
        if eid in diff.created:
            diff.created.remove(eid)
        if eid in diff.modified:
            diff.modified.remove(eid)
        diff.details.pop(eid, None)


def _record_deferred(verb: str, props: dict[str, Any], result: Any, diff: Diff) -> None:
    payload = dict(result) if isinstance(result, dict) else {"result": result}
    if verb == "export":
        out = str(props.get("out") or payload.get("path") or "")
        eid = payload.get("id") or f"export:{Path(out).name or props.get('format', 'file')}"
        _touch(diff, str(eid))
        diff.details[str(eid)] = payload
        diff.notes.append(
            f"exported {payload.get('format', props.get('format', '?'))}: "
            f"{payload.get('path', out)} ({payload.get('bytes', '?')} B)"
        )
    else:
        diff.details["check"] = payload
        verdict = payload.get("verdict")
        if verdict is not None:
            violations = payload.get("violations") or []
            diff.notes.append(f"check: {verdict}, {len(violations)} violation(s)")


def _small(value: Any) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, list | tuple):
        return len(value) <= 12 and all(
            v is None or isinstance(v, str | int | float | bool) for v in value
        )
    if isinstance(value, dict):
        return len(value) <= 12 and all(
            v is None or isinstance(v, str | int | float | bool) for v in value.values()
        )
    return False


def _entity(row: dict[str, Any]) -> Entity:
    """A D7 row -> the kernel's Entity: identity in concise(), scalars in summary."""
    eid = str(row.get("id"))
    prefix, sep, rest = eid.partition(":")
    kind = str(row.get("kind") or _KIND_OF_PREFIX.get(prefix if sep else eid, prefix or eid))
    name = str(row.get("name") or (rest if sep else eid))
    parent = row.get("parent")
    if parent is None and prefix in ("feat", "cmp") and row.get("part"):
        parent = str(row["part"])
    # `tree` is bulk by intent - a short one would otherwise slip through
    # `_small` and be carried BESIDE its own length, which is a scene dump in
    # miniature. The tree itself is what pk_query(tree=true) is for.
    summary = {
        key: value
        for key, value in row.items()
        if key not in ("id", "kind", "name", "parent", "tree") and _small(value)
    }
    if isinstance(row.get("tree"), list) and "features" not in summary:
        summary["features"] = len(row["tree"])
    return Entity(id=eid, name=name, kind=kind, parent=parent, summary=summary)


__all__ = [
    "COLD_IMPORT_S",
    "DEV_INSTALL",
    "INSTALL_HINT",
    "READY_GRACE_S",
    "SIDECAR_INSTALL",
    "WARM_IMPORT_S",
    "PartkilnAdapter",
]
