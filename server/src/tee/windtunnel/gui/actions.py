"""The controls: each one builds `(tool_name, args)` and nothing else.

A click and a tool call are the same thing here, which is the point: a control
writes the arguments a model would send through `tee_call`, `shell.py` makes
the call, and there is no path through the window that a model could not take.
This module never touches a registry, a case store or an engine.

A control that cannot build its arguments raises `ValueError` naming the fix -
the same contract a refused tool call has, and the shell shows it without
calling anything.

Qt-free on purpose, and tested that way: PySide6 is not installed on the
machine this was written on, so a control whose logic lived in a widget would
have shipped unexercised.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

Row = Mapping[str, Any]
Cases = Sequence[Row]


@dataclass(frozen=True)
class Control:
    """One button, and the call it makes.

    `needs_case` is what the window greys out on, and `confirms` marks the
    controls that spend real time or open a window, so a shell can ask first.
    """

    key: str
    label: str
    tool: str | None  # None: the shell services it itself (see `cancel`)
    build: Callable[..., dict[str, Any]]
    needs_case: bool = True
    confirms: bool = False
    hint: str = ""


def _case(case_id: str) -> str:
    if not case_id:
        raise ValueError("Select a case first - the list on the left.")
    return case_id


def list_cases() -> dict[str, Any]:
    return {"action": "list"}


def show_case(case_id: str) -> dict[str, Any]:
    return {"action": "show", "case_id": _case(case_id)}


def mesh(case_id: str, **kw: Any) -> dict[str, Any]:
    args: dict[str, Any] = {"case_id": _case(case_id)}
    args.update({k: v for k, v in kw.items() if v not in (None, "")})
    return args


def run(case_id: str, *, cores: int | None = None, iters: int | None = None) -> dict[str, Any]:
    """A run always confirms its cost from the window.

    The gate exists so a model is asked once before spending an hour; a human
    who pressed Run has answered that question by pressing it, and the window
    says so on the button rather than raising a dialog the lane did not ask
    for.
    """
    args: dict[str, Any] = {"case_id": _case(case_id), "confirm_cost": True}
    if cores:
        args["cores"] = int(cores)
    if iters:
        args["iters"] = int(iters)
    return args


def status(case_id: str, run_id: str = "") -> dict[str, Any]:
    args: dict[str, Any] = {"case_id": _case(case_id)}
    if run_id:
        args["run_id"] = run_id
    return args


def result(case_id: str, run_id: str = "", *, allow_partial: bool = False) -> dict[str, Any]:
    args = status(case_id, run_id)
    if allow_partial:
        args["allow_partial"] = True
    return args


def cancel(job: str) -> dict[str, Any]:
    """Cancel is the one control with no virtual tool behind it.

    `tee_job` is an always-loaded MCP tool, not a `VirtualTool`, so it is not
    in the registry this panel calls. The job manager underneath it is the very
    same object (`app.jobs`), and the shell reaches it directly rather than
    pretending a tool exists that does not.
    """
    if not job:
        raise ValueError("Nothing is running - a job id comes from a run you started here.")
    return {"job": job}


def open_in(
    case_id: str, app: str = "paraview", *, view: str = "pressure", launch: bool = False
) -> dict[str, Any]:
    if app not in ("paraview", "openvsp"):
        raise ValueError("app is paraview (the fields) or openvsp (the .vsp3).")
    args: dict[str, Any] = {"case_id": _case(case_id), "app": app}
    if app == "paraview":
        args["view"] = view
    if launch:
        args["launch"] = True
    return args


CONTROLS: tuple[Control, ...] = (
    Control("refresh", "Refresh", "wt_case", list_cases, needs_case=False),
    Control("show", "Details", "wt_case", show_case),
    Control("mesh", "Mesh", "wt_mesh", mesh, confirms=True, hint="Builds the grid; a job."),
    Control("run", "Run", "wt_run", run, confirms=True, hint="Starts the solver; a job."),
    Control("status", "Status", "wt_status", status),
    Control("result", "Result", "wt_result", result),
    Control("cancel", "Cancel", None, cancel, needs_case=False, hint="Kills the solver."),
    Control(
        "open_paraview",
        "Open in ParaView",
        "wt_open",
        open_in,
        confirms=True,
        hint="Writes a state file; opens a window only if you ask it to.",
    ),
    Control(
        "open_openvsp",
        "Open in OpenVSP",
        "wt_open",
        lambda case_id, **kw: open_in(case_id, "openvsp", **kw),
        confirms=True,
        hint="Opens the .vsp3 geometry.",
    ),
)

BY_KEY: dict[str, Control] = {c.key: c for c in CONTROLS}


def control(key: str) -> Control:
    try:
        return BY_KEY[key]
    except KeyError:
        raise ValueError(f"'{key}' is not a control; one of: {', '.join(BY_KEY)}") from None


def case_rows(cases: Cases) -> list[dict[str, Any]]:
    """The case list as the window shows it: one flat row per case.

    Reads only what `wt_case action=list` puts on the wire - no store, no
    directory walk - so the window and a model see the same thing.
    """
    rows = []
    for c in cases:
        rows.append(
            {
                "case_id": c.get("case_id", ""),
                "kind": c.get("kind", ""),
                "engine": c.get("engine", ""),
                "runs": (
                    len(c.get("runs") or [])
                    if isinstance(c.get("runs"), list)
                    else c.get("runs", 0)
                ),
                "state": c.get("state", ""),
            }
        )
    return rows
