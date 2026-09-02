"""The kernel behind every client: one Protocol, one in-process implementation.

Two kernels serve the same thirteen methods (A66 D2). `LocalKernel` runs
here, over ONE `Document`, and is what the sidecar worker wraps; TEE's
`SidecarKernel` speaks the same method set over NDJSON to that worker. The
adapter never knows which one it holds, so a test can drive the adapter on
a `LocalKernel` with no process and production can run the kernel in the
interpreter that survives the extension venv wipe.

Why the split exists is a measured number: `import OCP` costs 26 s COLD in a
fresh venv and 0.29 s warm (P0a, 2026-09-02). Law 17 says that import never
blocks a call, so `warm()` is a job, `probe()` never waits, and everything
that can answer from the command mirror (`entities`, `snapshot`) does so
before the B-rep exists. Importing this module loads no OCP: `warm()` is
the ONLY place the import happens, and it happens on purpose.

`call(method, params)` is the generic door for the `pk_*` tool backends:
other modules `register_method` into `KERNEL_METHODS` (checks, exchange,
drawings) and the worker dispatches every request through the same table,
so a method added to the kernel is on the wire with no worker change.
"""

from __future__ import annotations

import json
import os
import platform
import re
import resource
import sys
import time
from collections.abc import Callable
from importlib.metadata import PackageNotFoundError, packages_distributions
from importlib.metadata import version as dist_version
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from partkiln import __version__
from partkiln._errors import KernelError
from partkiln.document import CommandError, Document

MethodHandler = Callable[["LocalKernel", dict[str, Any]], Any]

# The method table: name -> handler(kernel, params). Filled at the bottom of
# this module with the Protocol's own methods, and by any module that
# registers a `pk_*` backend. Hidden entries answer but are not advertised.
KERNEL_METHODS: dict[str, MethodHandler] = {}
_HIDDEN: set[str] = set()


def register_method(name: str, *, hidden: bool = False) -> Callable[[MethodHandler], MethodHandler]:
    """Add a wire method by importing the module that defines it.

    `hidden` keeps test hooks (the worker's `echo_stdout`, `sleep`) out of the
    list a `pk_bad_op` refusal prints, without a second dispatch path.
    """

    def wrap(handler: MethodHandler) -> MethodHandler:
        KERNEL_METHODS[name] = handler
        if hidden:
            _HIDDEN.add(name)
        else:
            _HIDDEN.discard(name)
        return handler

    return wrap


def known_methods() -> tuple[str, ...]:
    """Every advertised method, sorted - the list a refusal names."""
    return tuple(sorted(name for name in KERNEL_METHODS if name not in _HIDDEN))


# -- process facts --------------------------------------------------------------


def rss_mb() -> float:
    """Peak resident set of this process in MB, from `getrusage`.

    `ru_maxrss` is the PEAK, not the instant, and that is the number the
    `rss_cap_mb` restart policy wants: OCCT's allocator rarely hands memory
    back, so a worker that once ballooned stays ballooned. Darwin reports
    bytes, Linux kibibytes - the one platform seam in this module.
    """
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
    return round(peak / divisor, 1)


def ocp_loaded() -> bool:
    """True once this process has paid the OCP import."""
    return "OCP" in sys.modules


_occt: str | None = None


def occt_version() -> str | None:
    """The OCCT version behind the OCP wheel ("7.9.3"), or None without one.

    Read from the loaded module when there is one, else from the carrier
    distribution's metadata - so `info()` can name the kernel version
    BEFORE `warm()` has paid the import. Both wheels version as
    `<occt>.<build>` (7.9.3.1.1), hence the cut to three components.
    """
    global _occt
    if _occt is not None:
        return _occt
    raw = getattr(sys.modules.get("OCP"), "__version__", None)
    if not raw:
        for dist in packages_distributions().get("OCP") or ():
            try:
                raw = dist_version(dist)
                break
            except PackageNotFoundError:
                continue
    if not raw:
        return None
    _occt = ".".join(str(raw).split(".")[:3])
    return _occt


# -- the Protocol -------------------------------------------------------------------


@runtime_checkable
class KernelClient(Protocol):
    """What the TEE adapter holds: thirteen methods, two implementations.

    Every result is plain JSON-able data (dicts, lists, scalars) because the
    sidecar sends it down a pipe; a `LocalKernel` returns the same shapes so
    nothing upstream can tell the two apart. Refusals are `CommandError`
    (with `.code`, and `.fix` on a `KernelError`) in-process and
    `{code, message, fix}` on the wire.
    """

    def probe(self) -> bool:
        """Alive or importable. Never waits, never imports."""
        ...

    def info(self) -> dict[str, Any]:
        """Mode, interpreter, OCP availability and the document's compact state."""
        ...

    def warm(self) -> dict[str, Any]:
        """Pay the OCP import; `{import_s, rss_mb, occt, mode, ocp}`."""
        ...

    def apply(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply a batch atomically; `{results, fingerprint, commands}`."""
        ...

    def entities(self) -> list[dict[str, Any]]:
        """The D7 entity rows, from the command mirror when the B-rep is absent."""
        ...

    def detail(self, entity_id: str) -> dict[str, Any]:
        """One entity, opt-in (hard rule 1)."""
        ...

    def call(self, method: str, params: dict[str, Any]) -> Any:
        """The generic door: dispatch through `KERNEL_METHODS`."""
        ...

    def script(self) -> dict[str, Any]:
        """The replayable script - the state itself (Law 16)."""
        ...

    def fingerprint(self) -> str:
        """16 hex over the rounded model."""
        ...

    def snapshot(self, label: str, dir: str | Path) -> dict[str, Any]:
        """Write a checkpoint; `{label, path, commands, fingerprint, brep}`."""
        ...

    def restore(self, payload: dict[str, Any]) -> None:
        """Reload the checkpoint `snapshot()` described."""
        ...

    def discard(self, payload: dict[str, Any]) -> None:
        """Unlink the checkpoint's files."""
        ...

    def shutdown(self) -> None:
        """Release whatever the kernel holds."""
        ...


# -- the in-process kernel ---------------------------------------------------------


class LocalKernel:
    """The kernel in this interpreter, over ONE `Document`.

    `document` is the live handle: every method reads and mutates it in
    place, and `restore()` transplants the replayed state INTO it rather than
    swapping the object, so a reference taken at construction stays true.
    """

    def __init__(self, document: Document | None = None, *, mode: str = "local") -> None:
        self.document: Document = document if document is not None else Document()
        self.mode = mode
        self._warm: dict[str, Any] | None = None

    # -- liveness and facts ---------------------------------------------------------

    def probe(self) -> bool:
        return True

    def info(self) -> dict[str, Any]:
        from partkiln.brep import ocp_available

        state = self.document.summary()
        return {
            "mode": self.mode,
            "pid": os.getpid(),
            "python": platform.python_version(),
            "partkiln": __version__,
            "ocp": ocp_available(),
            "occt": occt_version(),
            "warm": ocp_loaded(),
            "name": state.get("name"),
            "commands": state.get("commands", 0),
            "fingerprint": state.get("fingerprint"),
            "sketches": len(state.get("sketches") or ()),
            "parts": state.get("parts", 0),
            "assemblies": state.get("assemblies", 0),
            "drawings": state.get("drawings", 0),
            "sheets": state.get("sheets", 0),
        }

    def warm(self) -> dict[str, Any]:
        """Pay the OCP import here, once, and report what it cost.

        This is the 26 s (cold) / 0.29 s (warm) that Law 17 keeps out of
        every call: the adapter submits it as a job at boot and refuses
        `pk_warming` for a call that lands inside it. A second `warm()` is a
        report, not a second import. With no OCP wheel the answer is
        `ocp: false` - a fact for `_need()` to act on, not a refusal, because
        the command mirror still answers without it.
        """
        if self._warm is not None:
            return {**self._warm, "cached": True}
        from partkiln import brep

        started = time.perf_counter()
        available = brep.ocp_available()
        if available:
            import OCP  # noqa: F401 - the measured cold import, paid on purpose

            import partkiln.brep.shapes  # noqa: F401 - the kernel's own module, warmed with it
        report = {
            "import_s": round(time.perf_counter() - started, 3),
            "rss_mb": rss_mb(),
            "occt": occt_version() if available else None,
            "mode": self.mode,
            "ocp": available,
        }
        self._warm = report
        return dict(report)

    # -- commands ----------------------------------------------------------------------

    def apply(self, commands: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply the batch as one transaction.

        `Document.apply` already restores itself when ONE command refuses;
        a batch must do the same for the commands before the failing one
        (Law 16: a failed batch never advances state; P4 acceptance: a failed
        3rd op rolls back to the pre-batch fingerprint). The mark uses the
        document's own snapshot when it has one and falls back to truncating
        the history and `regen()` - public API - when it does not.
        """
        if not isinstance(commands, list):
            raise CommandError(
                "apply takes commands: a list of {op, ...} objects.", code="pk_bad_op"
            )
        doc = self.document
        mark = _mark(doc)
        results: list[dict[str, Any]] = []
        for index, raw in enumerate(commands):
            try:
                results.append(doc.apply(raw))
            except Exception as exc:
                _rollback(doc, mark)
                raise _batch_error(exc, index, raw, len(commands)) from exc
        return {
            "results": results,
            "fingerprint": doc.fingerprint(),
            "commands": len(doc.history),
        }

    def entities(self) -> list[dict[str, Any]]:
        """D7 rows. Delegates to `Document.entities()` once P2 gives it one;
        until then the rows come from `summary()` plus the containers, so a
        part created while the B-rep is still warming is already listed."""
        doc = self.document
        own = getattr(doc, "entities", None)
        if callable(own):
            return [dict(row) for row in own()]
        state = doc.summary()
        rows: list[dict[str, Any]] = [
            {"kind": "sketch", **row} for row in state.get("sketches") or ()
        ]
        for attr, prefix in _CONTAINERS:
            container = getattr(doc, attr, None) or {}
            for name in sorted(container):
                row: dict[str, Any] = {"id": f"{prefix}:{name}", "kind": prefix}
                row.update(_describe(container[name]))
                row["id"] = f"{prefix}:{name}"
                rows.append(row)
        return rows

    def detail(self, entity_id: str) -> dict[str, Any]:
        doc = self.document
        for name in ("detail", "entity_detail"):
            own = getattr(doc, name, None)
            if callable(own):
                return dict(own(entity_id))
        eid = str(entity_id)
        if eid == "doc":
            return {"id": "doc", **doc.summary()}
        prefix, _, name = eid.partition(":")
        container = _BY_PREFIX.get(prefix)
        item = (getattr(doc, container, None) or {}).get(name) if container and name else None
        if item is None:
            known = ", ".join(row["id"] for row in self.entities()) or "(none)"
            raise CommandError(f"no entity {eid!r}. Entities: {known}.", code="pk_ref_unknown")
        out = {"id": eid, **_describe(item)}
        coordinates = getattr(item, "coordinates", None)
        if callable(coordinates):
            out["coordinates"] = coordinates()
        return out

    def call(self, method: str, params: dict[str, Any]) -> Any:
        handler = KERNEL_METHODS.get(str(method))
        if handler is None:
            raise KernelError(
                f"unknown method {method!r}. The kernel answers: {', '.join(known_methods())}.",
                fix="call one of those, or register_method() the one you meant.",
                code="pk_bad_op",
            )
        if params is not None and not isinstance(params, dict):
            raise CommandError(f"{method}: params must be an object.", code="pk_bad_op")
        return handler(self, dict(params or {}))

    def script(self) -> dict[str, Any]:
        return self.document.script()

    def fingerprint(self) -> str:
        return self.document.fingerprint()

    # -- checkpoints (D3: the script is the state, the B-rep is a cache) ----------

    def snapshot(self, label: str, dir: str | Path) -> dict[str, Any]:
        doc = self.document
        own = getattr(doc, "snapshot", None)
        if callable(own):
            return dict(own(label, dir))
        directory = Path(dir)
        directory.mkdir(parents=True, exist_ok=True)
        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(label)).strip("._-") or "checkpoint"
        path = directory / f"{stem}-{int(time.time() * 1000)}.json"
        bump = 0
        while path.exists():
            bump += 1
            path = directory / f"{stem}-{int(time.time() * 1000)}-{bump}.json"
        script = doc.script()
        fingerprint = doc.fingerprint()
        path.write_text(
            json.dumps({"script": script, "fingerprint": fingerprint}, sort_keys=True),
            encoding="utf-8",
        )
        return {
            "label": label,
            "path": str(path),
            "commands": len(script.get("commands") or ()),
            "fingerprint": fingerprint,
            "brep": False,
        }

    def restore(self, payload: dict[str, Any]) -> None:
        doc = self.document
        own = getattr(doc, "restore", None)
        if callable(own):
            fresh = own(payload)
            if isinstance(fresh, Document) and fresh is not doc:
                self._adopt(fresh)
            return
        path = (
            Path(str(payload.get("path")))
            if isinstance(payload, dict) and payload.get("path")
            else None
        )
        if path is None:
            raise CommandError(
                "restore needs the payload snapshot() returned (it carries the path).",
                code="pk_needs",
            )
        if not path.is_file():
            raise CommandError(
                f"checkpoint {path.name} is gone from {path.parent}. It was purged or never "
                "written; take a new checkpoint (tee_checkpoint) - tee_purge is what removes them.",
                code="pk_checkpoint_missing",
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        script = data.get("script") if isinstance(data, dict) else None
        if not isinstance(script, dict):
            raise CommandError(
                f"{path.name} holds no script. Take a new checkpoint.", code="pk_checkpoint_missing"
            )
        fresh = Document.replay(script)
        self._adopt(fresh)
        expected = data.get("fingerprint")
        got = doc.fingerprint()
        if expected and got != expected:
            raise CommandError(
                f"the replayed checkpoint fingerprints {got}, not the {expected} it was taken at. "
                "The document now holds the replayed script; the replay is not deterministic - "
                "report it with the script.",
                code="pk_checkpoint_mismatch",
            )

    def discard(self, payload: dict[str, Any]) -> None:
        if not isinstance(payload, dict):
            return
        paths = [payload.get("path"), *(payload.get("files") or ()), *(payload.get("breps") or ())]
        for raw in paths:
            if not raw:
                continue
            target = Path(str(raw))
            try:
                target.unlink()
            except FileNotFoundError:
                continue

    def shutdown(self) -> None:
        return None

    def _adopt(self, fresh: Document) -> None:
        """Move `fresh`'s state into the live document, keeping its identity."""
        try:
            vars(self.document).clear()
            vars(self.document).update(vars(fresh))
        except TypeError:  # a slotted Document some day: swap the handle instead
            self.document = fresh


# The P2+ containers and their id prefixes (D6/D7); sketches are `sk:` via summary().
_CONTAINERS: tuple[tuple[str, str], ...] = (
    ("parts", "part"),
    ("assemblies", "asm"),
    ("drawings", "drw"),
    ("sheets", "sheet"),
)
_BY_PREFIX: dict[str, str] = {"sk": "sketches", **{prefix: attr for attr, prefix in _CONTAINERS}}


def _describe(item: Any) -> dict[str, Any]:
    """Whatever compact report the object offers, never geometry."""
    for attr in ("summary", "report", "as_dict"):
        method = getattr(item, attr, None)
        if callable(method):
            out = method()
            if isinstance(out, dict):
                return dict(out)
    return {"repr": repr(item)[:200]}


def _mark(doc: Document) -> tuple[int, Any]:
    take = getattr(doc, "_snapshot", None)
    return len(doc.history), take() if callable(take) else None


def _rollback(doc: Document, mark: tuple[int, Any]) -> None:
    length, snapshot = mark
    put = getattr(doc, "_restore", None)
    del doc.history[length:]
    if snapshot is not None and callable(put):
        put(snapshot)
    else:
        doc.regen()


def _batch_error(exc: Exception, index: int, raw: Any, total: int) -> CommandError:
    op = raw.get("op") if isinstance(raw, dict) else raw
    message = getattr(exc, "message", None) or str(exc)
    code = getattr(exc, "code", "pk_op_failed")
    fix = getattr(exc, "fix", "") or ""
    return KernelError(
        f"command {index} of {total} ({op}): {message} Nothing applied: the whole batch "
        "rolled back and the document is unchanged.",
        fix=fix,
        code=code,
    )


def _need(params: dict[str, Any], key: str, method: str) -> Any:
    if key not in params:
        raise CommandError(f"{method} needs {key}.", code="pk_needs")
    return params[key]


# -- the Protocol's own methods, on the table so the worker has one dispatch -----


@register_method("ping")
def _m_ping(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return {"alive": True, "pid": os.getpid()}


@register_method("probe")
def _m_probe(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return {"alive": kernel.probe()}


@register_method("info")
def _m_info(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.info()


@register_method("warm")
def _m_warm(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.warm()


@register_method("apply")
def _m_apply(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.apply(_need(params, "commands", "apply"))


@register_method("entities")
def _m_entities(kernel: LocalKernel, params: dict[str, Any]) -> list[dict[str, Any]]:
    return kernel.entities()


@register_method("detail")
def _m_detail(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.detail(str(_need(params, "id", "detail")))


@register_method("script")
def _m_script(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.script()


@register_method("fingerprint")
def _m_fingerprint(kernel: LocalKernel, params: dict[str, Any]) -> str:
    return kernel.fingerprint()


@register_method("snapshot")
def _m_snapshot(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    return kernel.snapshot(
        str(_need(params, "label", "snapshot")), _need(params, "dir", "snapshot")
    )


@register_method("restore")
def _m_restore(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    kernel.restore(params.get("payload") or params)
    return {"restored": True, "fingerprint": kernel.fingerprint()}


@register_method("discard")
def _m_discard(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    kernel.discard(params.get("payload") or params)
    return {"discarded": True}


@register_method("shutdown")
def _m_shutdown(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    kernel.shutdown()
    return {"shutdown": True}


__all__ = [
    "KERNEL_METHODS",
    "KernelClient",
    "LocalKernel",
    "known_methods",
    "occt_version",
    "ocp_loaded",
    "register_method",
    "rss_mb",
]
