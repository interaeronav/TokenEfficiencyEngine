"""The controller: press a control, call the tool, format what came back.

It holds no model of its own. There is no cached case list, no remembered
verdict, no second copy of anything the lane already knows: every panel of the
window is the last answer a tool gave, which is the same compact state a model
sees. Hard rules 1 and 2 in a window.

Qt-free and tested with PySide6 absent, for partkiln's reason: a shell whose
logic lived in the widgets would ship unexercised.

The one thing it adds over a bare tool call is honesty about time. A run and a
mesh are jobs, so pressing them returns a job id and the window polls
`tee_job`; a refusal is caught and shown as the message and fix the lane wrote,
never as a traceback.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.windtunnel.gui import actions

MAX_LOG = 200


class WindTunnelShell:
    """Everything the window does, with no window.

    Takes a live `TeeApp` - the same object `tee serve` builds - so the panel
    drives the registry a model drives, trust kernel included. A control that
    the trust table refuses here is refused there.
    """

    def __init__(self, app: Any) -> None:
        self.app = app
        self.log: list[str] = []
        self.case_id: str = ""
        self.job: str = ""

    # -- plumbing ------------------------------------------------------------

    def _say(self, line: str) -> str:
        self.log.append(line)
        del self.log[:-MAX_LOG]
        return line

    def call(self, key: str, **kw: Any) -> dict[str, Any]:
        """Build the control's arguments and make the call.

        Every failure comes back the same way - `{"error": code, "message",
        "fix"}` - whether the control could not build its arguments or the lane
        refused them, because a window that renders one kind of failure and
        crashes on the other is a window you cannot trust.
        """
        try:
            control = actions.control(key)
            args = control.build(**kw)
        except ValueError as exc:
            return {"error": "gui_bad_input", "message": str(exc), "fix": str(exc)}
        if control.tool is None:  # serviced here; see actions.cancel
            return self._service(control, args)
        try:
            out = self.app.registry.call(control.tool, args)
        except TeeError as exc:
            self._say(f"{control.label}: {exc.code} - {exc.message}")
            return {"error": exc.code, "message": exc.message, "fix": exc.fix}
        self._say(f"{control.label}: ok")
        if isinstance(out, dict) and out.get("job"):
            self.job = str(out["job"])
        return out if isinstance(out, dict) else {"result": out}

    def _service(self, control: actions.Control, args: dict[str, Any]) -> dict[str, Any]:
        """The controls with no tool behind them - today, only cancel.

        The job manager is the same object `tee_job` drives; the panel is an
        in-process client of the app, so it asks that object rather than
        inventing a virtual tool for it.
        """
        try:
            out = self.app.jobs.cancel(str(args["job"]))
        except Exception as exc:  # the manager's own shapes, kept out of the window
            self._say(f"{control.label}: {exc}")
            return {"error": "job_cancel_failed", "message": str(exc)[:200], "fix": "Poll first."}
        self._say(f"{control.label}: ok")
        return out if isinstance(out, dict) else {"cancelled": bool(out)}

    # -- what the window shows -----------------------------------------------

    def cases(self) -> list[dict[str, Any]]:
        out = self.call("refresh")
        if out.get("error"):
            return []
        return actions.case_rows(out.get("cases") or [])

    def select(self, case_id: str) -> dict[str, Any]:
        self.case_id = case_id
        return self.call("show", case_id=case_id)

    def start_run(self, **kw: Any) -> dict[str, Any]:
        return self.call("run", case_id=self.case_id, **kw)

    def build_mesh(self, **kw: Any) -> dict[str, Any]:
        return self.call("mesh", case_id=self.case_id, **kw)

    def cancel(self) -> dict[str, Any]:
        return self.call("cancel", job=self.job)

    def hand_off(self, app: str = "paraview", **kw: Any) -> dict[str, Any]:
        key = "open_openvsp" if app == "openvsp" else "open_paraview"
        return self.call(key, case_id=self.case_id, **kw)

    def poll(self) -> dict[str, Any]:
        """One tick of the window's clock: the job first, the run second.

        The job manager owns whether the work is finished; `wt_status` owns
        what the solver is doing. Asking the second without the first is how a
        window ends up reporting `running` for a job that died.

        It asks `app.jobs` directly, for the reason `_service` gives: `tee_job`
        is an always-loaded MCP tool registered on the server, NOT a virtual
        tool in this registry. Calling it here returned
        `{"error": "unknown_tool"}` on every tick and the pane never showed a
        job at all - measured 2026-09-07, after the same trap was found in the
        Mac evidence script. Cancel had already been moved off this door; the
        clock had quietly stayed on it.
        """
        out: dict[str, Any] = {}
        if self.job:
            try:
                out["job"] = self.app.jobs.status(self.job)
            except TeeError as exc:
                out["job"] = {"error": exc.code, "message": exc.message}
        if self.case_id:
            out["status"] = self.call("status", case_id=self.case_id)
        return out

    # -- formatting (the only place strings are made) -------------------------

    @staticmethod
    def status_line(status: dict[str, Any]) -> str:
        if status.get("error"):
            return f"{status['error']}: {status.get('message', '')}"
        state = status.get("state", "?")
        bits = [str(state)]
        if status.get("iter") is not None:
            bits.append(f"iter {status['iter']}")
        if status.get("elapsed_s") is not None:
            bits.append(f"{status['elapsed_s']} s")
        coeffs = status.get("coeffs") or {}
        if coeffs.get("cl") is not None:
            bits.append(f"cl {coeffs['cl']}")
        if coeffs.get("cd") is not None:
            bits.append(f"cd {coeffs['cd']}")
        if status.get("verdict_so_far"):
            bits.append(str(status["verdict_so_far"]))
        return "  ".join(bits)

    @staticmethod
    def result_line(result: dict[str, Any]) -> str:
        """A result is never shown without what qualifies it.

        The lane's second law: no bare coefficient. If the verdict or the
        uncertainty label is missing from the answer, the line says so rather
        than printing numbers that look more certain than they are.
        """
        if result.get("error"):
            return f"{result['error']}: {result.get('message', '')}"
        verdict = (result.get("verdict") or {}).get("state", "?")
        trust = (result.get("uncertainty") or {}).get("trust", "?")
        nums = "  ".join(
            f"{k} {result[k]}" for k in ("cl", "cd", "cm", "l_over_d") if result.get(k) is not None
        )
        return f"{nums or 'no coefficients'}   [{verdict}, {trust}]"

    @staticmethod
    def handoff_line(out: dict[str, Any]) -> str:
        if out.get("error"):
            return f"{out['error']}: {out.get('message', '')}"
        if out.get("launched"):
            return f"{out.get('app')} opened (pid {out.get('pid')})"
        where = out.get("state") or out.get("target") or ""
        return f"prepared: {where}\n{out.get('command_line', '')}"
