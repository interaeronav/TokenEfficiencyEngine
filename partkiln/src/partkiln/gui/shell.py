"""The controller: build a command, apply it through the kernel, show the diff.

This is the whole shell minus its pixels, and it is where A53 Law 3 is actually
kept. It holds no model of its own - no feature list, no volumes, no cached
shape. It presses a control, the control builds a command dict, the kernel
applies it, and what gets displayed is the DIFF the kernel answered with
(volume, delta, faces, assumed, resolved), never a re-read of the world. The
feature tree and the parameter table come from `entities()`, the D7 rows, which
is the same compact state a model gets. Hard rules 1 and 2, in the GUI.

Everything here is Qt-free and tested with PySide6 absent. That is not a
convenience: PySide6 was not installed on the machine this was written on, so a
shell whose logic lived in the widgets would have shipped untested - which is
exactly how seamkiln's follow-up buttons went eleven campaigns unexercised.

Two honesty rules the window inherits:

- **No kernel, no geometry.** With no OCP wheel the command mirror still
  answers - parameters, sketches, datums, the script - so those controls work
  and the geometry ones refuse ONCE with `pk_kernel_absent` and the install
  line, instead of each one dying inside OCCT.
- **No coordinates on the wire.** The sketch preview needs the solved points,
  and D7 deliberately does not carry them, so it is available on the
  in-process kernel and refuses `pk_not_served` on a sidecar.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from partkiln._errors import KernelError
from partkiln.client import LocalKernel
from partkiln.document import CommandError
from partkiln.gui.actions import CONTROLS, Control

MAX_LOG = 500

# What `press` catches from a factory: a control that cannot build its command
# on the document as it stands (no part yet, no datum plane) is a refusal, not
# a crash - the same contract the kernel keeps.
BUILD_ERRORS = (CommandError, KernelError, ValueError, KeyError, IndexError, TypeError)


class PartkilnShell:
    """A window's worth of behaviour, with no window attached."""

    def __init__(
        self,
        kernel: Any = None,
        *,
        workdir: str | Path | None = None,
    ) -> None:
        self.kernel = kernel if kernel is not None else LocalKernel()
        self.workdir = Path(workdir or tempfile.mkdtemp(prefix="partkiln-gui-"))
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.log: list[str] = []
        self.last: dict[str, Any] = {}
        self.controls: tuple[Control, ...] = CONTROLS
        self.state: list[dict[str, Any]] = []
        self.refresh()

    # -- the kernel, as the shell sees it -------------------------------------

    def status(self) -> dict[str, Any]:
        """Mode, OCCT version, warm state, fingerprint - the title bar's facts."""
        info = dict(self.kernel.info())
        info["alive"] = bool(self.kernel.probe())
        return info

    def brep_available(self) -> bool:
        """Whether this kernel can build geometry at all. One `info()` call, so
        a shell driving a sidecar asks the process that would do the work."""
        return bool(self.status().get("ocp"))

    def warm(self) -> dict[str, Any]:
        """Pay the OCP import on purpose, once (measured 0.28-1.2 s warm).

        A desktop shell can afford to block on this at start-up and say so in
        the log; the TEE call path cannot, which is why Law 17 makes it a job
        there and a plain method here.
        """
        report = dict(self.kernel.warm())
        self._say(
            f"= kernel {report.get('mode')} ocp={report.get('ocp')} "
            f"occt={report.get('occt')} import {report.get('import_s')} s"
        )
        return report

    def close(self) -> None:
        self.kernel.shutdown()

    # -- the only way anything changes ----------------------------------------

    def press(self, control: Control) -> dict[str, Any]:
        """A button: build the command from the state as it is, then run it."""
        try:
            command = control.build(self.state, self.workdir)
        except BUILD_ERRORS as exc:
            return self._refuse(getattr(exc, "code", "pk_needs"), f"{control.label}: {exc}")
        if control.needs_brep and not self.brep_available():
            return self._refuse(
                "pk_kernel_absent",
                f"{control.label} needs the B-rep kernel, and this one has no OCP. "
                "Install it with: uv pip install 'partkiln[brep]' "
                "(parameters, sketches, datums and the script work without it).",
            )
        return self.run(command)

    def run(self, command: dict[str, Any]) -> dict[str, Any]:
        """Apply one command through the kernel and keep what came back.

        The routing is the vocabulary's own: a D5 op the document owns goes
        through `apply` and lands in the script; an op the kernel answers as a
        method (`check`, `export`) is a read or an artefact and does not. Both
        shapes are the same dict a model would send.
        """
        op = str(command.get("op", ""))
        try:
            route = _route(op)
        except CommandError as exc:
            return self._refuse(exc.code, str(exc))
        try:
            if route == "command":
                answer = self.kernel.apply([command])
                results = answer.get("results") or [{}]
                diff = dict(results[0])
                diff.setdefault("fingerprint", answer.get("fingerprint"))
            else:
                diff = _as_dict(self.kernel.call(op, _params_of(command)))
        except (CommandError, KernelError) as exc:
            return self._refuse(getattr(exc, "code", "pk_op_failed"), f"{op}: {exc}")
        self.last = {"op": op, "command": command, "route": route, "diff": diff}
        self._say(f"> {json.dumps(command, default=str)}")
        for line in self.diff_lines():
            self._say(f"  {line}")
        self.refresh()
        return diff

    def refresh(self) -> list[dict[str, Any]]:
        """Re-read the D7 rows. The ONLY state this object keeps, and it is a
        copy of the kernel's, never a parallel model."""
        self.state = [dict(row) for row in self.kernel.entities()]
        return self.state

    def _refuse(self, code: str, message: str) -> dict[str, Any]:
        self.last = {"error": message, "code": code}
        self._say(f"! [{code}] {message}")
        return {"error": message, "code": code}

    def _say(self, line: str) -> None:
        self.log.append(line)
        del self.log[:-MAX_LOG]

    # -- what the panes show ---------------------------------------------------

    def diff_lines(self) -> list[str]:
        """The last answer, as text. The kernel's numbers, not a re-read."""
        last = self.last
        if not last:
            return ["nothing applied yet"]
        if "error" in last:
            return [f"[{last.get('code')}] {last['error']}"]
        diff = last["diff"]
        lines: list[str] = []
        head = str(diff.get("id") or last["op"])
        kind = diff.get("kind") or last["command"].get("kind") or last["op"]
        lines.append(f"{head}  {kind}")
        if "delta_mm3" in diff or "volume_mm3" in diff:
            lines.append(
                f"  volume {_mm3(diff.get('volume_mm3'))}   delta {_mm3(diff.get('delta_mm3'))}"
            )
        counts = [f"{k} {diff[k]}" for k in ("faces", "edges", "solids", "instances") if k in diff]
        if counts:
            lines.append("  " + "  ".join(counts))
        for row in diff.get("changed") or []:
            lines.append(
                f"  changed {row.get('feature', row.get('name'))} "
                f"delta {_mm3(row.get('delta_mm3'))} faces {row.get('faces')}"
            )
        for key in ("unchanged", "deleted", "failed", "verdict", "checked", "bytes", "path"):
            if key in diff:
                lines.append(f"  {key} {_short(diff[key])}")
        for row in diff.get("violations") or []:
            lines.append(f"  ! {row.get('rule')}: got {row.get('got')} vs {row.get('limit')}")
            lines.append(f"    fix {row.get('fix')}")
        resolved = diff.get("resolved") or {}
        for selector, count in resolved.items():
            lines.append(f"  resolved {selector} -> {count}")
        assumed = diff.get("assumed") or {}
        if assumed:
            lines.append("  assumed " + ", ".join(f"{k}={_short(v)}" for k, v in assumed.items()))
        for note in diff.get("notes") or []:
            lines.append(f"  note {note}")
        if diff.get("fingerprint"):
            lines.append(f"  fingerprint {diff['fingerprint']}")
        return lines

    def tree_lines(self) -> list[str]:
        """The feature tree: parts with their features under them, then the
        sketches, datums and sheets. Straight off the D7 rows."""
        lines: list[str] = []
        for row in self.state:
            eid = str(row.get("id", ""))
            if eid.startswith("part:"):
                lines.append(
                    f"{eid}  {row.get('material') or 'no material'}  "
                    f"{_mm3(row.get('volume_mm3'))}  faces {row.get('faces')}  "
                    f"{_short(row.get('mass_g'))} g"
                )
            elif eid.startswith("feat:"):
                lines.append(
                    f"    {eid:<16} {row.get('kind')!s:<9} "
                    f"delta {_mm3(row.get('delta_mm3')):>16}  faces {row.get('faces')}"
                    + ("  SUPPRESSED" if row.get("suppressed") else "")
                )
            elif eid.startswith("sk:"):
                lines.append(
                    f"{eid}  {row.get('plane')}  dof {row.get('dof')} {row.get('status')}  "
                    f"{'closed' if row.get('closed') else 'open'}  {row.get('area_mm2')} mm2"
                )
            elif eid.startswith(("plane:", "axis:", "point:", "dwg:", "sheet:", "asm")):
                lines.append(f"{eid}  {row.get('kind')}")
        return lines or ["empty document"]

    def param_rows(self) -> list[dict[str, Any]]:
        """The parameter table: name, value, unit, expression, and how many
        things would move if it changed."""
        return [
            {
                "name": row.get("name"),
                "value": row.get("value"),
                "unit": row.get("unit"),
                "expr": row.get("expr"),
                "used_by": row.get("used_by"),
            }
            for row in self.state
            if row.get("kind") == "param"
        ]

    def doc_row(self) -> dict[str, Any]:
        for row in self.state:
            if row.get("id") == "doc":
                return dict(row)
        return {}

    # -- pictures ---------------------------------------------------------------

    def sketch_names(self) -> list[str]:
        return [str(r["id"])[3:] for r in self.state if str(r.get("id", "")).startswith("sk:")]

    def drawing_names(self) -> list[str]:
        return [str(r["id"])[4:] for r in self.state if str(r.get("id", "")).startswith("dwg:")]

    def sketch_svg(self, name: str | None = None) -> str:
        """The active sketch as SVG, through partkiln's own writer.

        Needs the in-process document: solved coordinates are not D7 rows and
        never will be (hard rule 1), so a sidecar kernel refuses here rather
        than growing a geometry channel for a picture.
        """
        from partkiln.gui import preview

        names = self.sketch_names()
        if not names:
            raise CommandError("no sketch to preview: press Sketch.", code="pk_ref_empty")
        wanted = name or names[-1]
        document = getattr(self.kernel, "document", None)
        if document is None:
            raise CommandError(
                "the sketch preview needs the in-process kernel: solved coordinates are not "
                "on the wire (hard rule 1). Run the shell on a LocalKernel, or read the "
                "sketch's counts from its entity row.",
                code="pk_not_served",
            )
        sketch = document.sketches.get(wanted)
        if sketch is None:
            raise CommandError(
                f"no sketch {wanted!r}. Sketches: {', '.join(names)}.", code="pk_ref_unknown"
            )
        return preview.sketch_svg(sketch)

    def render_drawing(self, name: str | None = None) -> Path:
        """Write the sheet the document already holds and hand back the SVG.

        A render, not a model change: `create drawing` put the sheet in the
        script, this only asks the kernel to draw it into `workdir`.
        """
        names = self.drawing_names()
        if not names:
            raise CommandError("no drawing to render: press Draw sheet.", code="pk_ref_empty")
        wanted = name or names[-1]
        answer = _as_dict(
            self.kernel.call(
                "drawing",
                {"name": wanted, "formats": ["svg"], "out_dir": str(self.workdir)},
            )
        )
        path = (answer.get("files") or {}).get("svg")
        if not path:
            raise CommandError(f"the kernel wrote no SVG for {wanted!r}.", code="pk_op_failed")
        return Path(path)

    # -- the script is the product ------------------------------------------------

    def save_script(self, path: str | Path | None = None) -> Path:
        """Hand over the history that was being kept anyway (A66 Law 16)."""
        destination = Path(path or (self.workdir / "session.json"))
        script = self.kernel.script()
        destination.write_text(json.dumps(script, indent=2), encoding="utf-8")
        self._say(f"= script saved: {destination} ({len(script.get('commands', []))} commands)")
        return destination

    def fingerprint(self) -> str:
        return str(self.kernel.fingerprint())

    def detail(self, entity_id: str) -> dict[str, Any]:
        """One entity in full - the opt-in second look (D7), never the default."""
        return _as_dict(self.kernel.detail(entity_id))


# -- routing --------------------------------------------------------------------


def _route(op: str) -> str:
    """`command` for a D5 verb the document owns, `method` for one the kernel
    answers. Read off the kernel's live tables, so a verb added tomorrow routes
    without a second list here."""
    from partkiln import document
    from partkiln.client import known_methods

    document.load_verb_modules()
    if op in set(document.VERBS):
        return "command"
    methods = known_methods()
    if op in set(methods):
        return "method"
    raise CommandError(
        f"unknown op {op!r}. Verbs: {', '.join(document.VERBS)}. "
        f"Kernel methods: {', '.join(methods)}.",
        code="pk_bad_op",
    )


def _params_of(command: dict[str, Any]) -> dict[str, Any]:
    """A method's params from a D5 command dict: `props` merged over the rest.

    The same folding `Command.from_dict` does, so one wire shape serves both
    routes and a control never has to know which one it is on.
    """
    from partkiln.document import Command

    return dict(Command.from_dict(command).args)


def _as_dict(answer: Any) -> dict[str, Any]:
    return dict(answer) if isinstance(answer, dict) else {"value": answer}


def _mm3(value: Any) -> str:
    return f"{value:,.3f} mm3" if isinstance(value, int | float) else "-"


def _short(value: Any) -> str:
    if value is None:
        return "-"
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= 120 else text[:117] + "..."


__all__ = ["BUILD_ERRORS", "MAX_LOG", "PartkilnShell"]
