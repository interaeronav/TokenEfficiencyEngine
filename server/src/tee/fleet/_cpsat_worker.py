"""A45 P2a — CP-SAT in its own process, because it cannot share one with HiGHS.

Measured on this machine: `ortools` and `highspy` each bundle their own
build of HiGHS, and the dynamic linker resolves OR-Tools' symbols against
whichever `libhighs` is already loaded. So:

    import ortools ; import highspy    -> fine
    import highspy ; import ortools    -> ImportError, symbol not found
                                          (__Z19setLocalOptionValue...)

Import ORDER decides it. A long-lived MCP server dispatching tools in
whatever order the model asks cannot guarantee that ordering, and a server
whose correctness depends on which tool was called first is not correct.
So CP-SAT runs here, in a fresh interpreter with a clean linker namespace.

Deliberately standalone: it imports nothing from `tee`, so the parent can
invoke it by path without any import machinery, and it works the same in a
venv, an editable install and the .mcpb bundle.

Contract: JSON spec on stdin, one JSON object on stdout, always. Native
banners are swallowed at the fd level so they can never corrupt that.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time


def _solve(spec: dict) -> dict:
    from ortools.sat.python import cp_model

    variables = dict(spec.get("variables") or {})
    if not variables:
        return {"error": "no_variables", "message": "No variables declared."}
    m = cp_model.CpModel()
    vs = {}
    for name, d in variables.items():
        d = dict(d or {})
        vs[name] = m.NewIntVar(int(d.get("lb", 0)), int(d.get("ub", 100)), str(name))
    for i, c in enumerate(spec.get("constraints") or []):
        c = dict(c or {})
        expr = sum(int(k) * vs[n] for n, k in dict(c.get("lhs") or {}).items())
        rhs = int(c.get("rhs", 0))
        op = str(c.get("op", "<="))
        if op == "<=":
            m.Add(expr <= rhs)
        elif op == ">=":
            m.Add(expr >= rhs)
        elif op in ("==", "="):
            m.Add(expr == rhs)
        else:
            return {"error": "bad_op", "message": f"constraint {i}: op '{op}' is unknown."}
    obj = dict(spec.get("objective") or {})
    if obj:
        e = sum(int(k) * vs[n] for n, k in obj.items())
        if str(spec.get("sense", "min")).lower() == "max":
            m.Maximize(e)
        else:
            m.Minimize(e)

    solver = cp_model.CpSolver()
    if spec.get("time_limit"):
        solver.parameters.max_time_in_seconds = float(spec["time_limit"])
    started = time.monotonic()
    st = solver.Solve(m)
    wall = round(time.monotonic() - started, 4)

    names = {
        cp_model.OPTIMAL: "optimal",
        cp_model.FEASIBLE: "feasible",
        cp_model.INFEASIBLE: "infeasible",
        cp_model.MODEL_INVALID: "invalid",
        cp_model.UNKNOWN: "unknown",
    }
    status = names.get(st, str(st))
    out: dict = {"status": status, "wall_s": wall, "n_variables": len(vs)}
    if status in ("optimal", "feasible"):
        out["values"] = {n: int(solver.Value(v)) for n, v in vs.items()}
        if obj:
            out["objective"] = float(solver.ObjectiveValue())
    return out


def main() -> int:
    try:
        spec = json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        sys.stdout.write(json.dumps({"error": "bad_json", "message": str(exc)}))
        return 0

    # Swallow anything the native side prints, at the descriptor level, so
    # the single JSON object below is the only thing on stdout.
    saved = os.dup(1)
    log = ""
    try:
        with tempfile.TemporaryFile(mode="w+b") as tmp:
            os.dup2(tmp.fileno(), 1)
            try:
                result = _solve(spec)
            finally:
                sys.stdout.flush()
                os.dup2(saved, 1)
                try:
                    tmp.seek(0)
                    log = tmp.read().decode("utf-8", errors="replace")
                except Exception:
                    log = ""
    except Exception as exc:  # a solver crash is data, not a traceback
        os.dup2(saved, 1)
        result = {"error": type(exc).__name__, "message": str(exc)[:400]}
    finally:
        os.close(saved)

    result["solver_log"] = log.strip()
    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
