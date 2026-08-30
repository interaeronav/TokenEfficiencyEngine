"""A45 P2a — linear and mixed-integer programming, compactly.

One normalised problem spec over three interchangeable engines (HiGHS,
SCIP, COIN-OR Cbc) through PuLP's modelling layer, plus OR-Tools CP-SAT
for the genuinely different paradigm of pure constraint programming.
Verified on this machine: all three agree on the reference problem
(objective 38.0 at x=10, y=2), which is also the smoke test.

Token discipline is the whole design. A solver's natural output is a full
solution vector - thousands of variables, nearly all zero - and dumping it
is exactly the failure this project exists to prevent. So an answer is:
status, objective, the binding constraints, and the top handful of
non-zero variables, with a `solution_id`. Everything else is a second,
explicit `solve_detail` call. A 5,000-variable model answers in ~120
tokens instead of ~60,000.

Every solve runs inside `quiet.muted_stdout`: these are native libraries
and they write banners straight to fd 1, which would corrupt TEE's
JSON-RPC stream (see fleet/quiet.py - `redirect_stdout` does NOT stop it).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from tee.fleet.probe import need, probe_rows
from tee.fleet.quiet import muted_stdout
from tee.kernel.errors import TeeError

BACKENDS = ("highs", "scip", "cbc")
DEFAULT_SHOW = 12
SHOW_CAP = 200
_STORE: dict[str, dict[str, Any]] = {}
_STORE_CAP = 24
_SEQ = [0]


def _remember(payload: dict[str, Any]) -> str:
    _SEQ[0] += 1
    sid = f"sol_{_SEQ[0]}"
    _STORE[sid] = payload
    while len(_STORE) > _STORE_CAP:
        _STORE.pop(next(iter(_STORE)))
    return sid


def _pulp():
    return need("pulp", "solve", what="the LP/MIP modelling layer")


def _solver(pulp, backend: str, time_limit: float | None):
    kw: dict[str, Any] = {"msg": False}
    if time_limit:
        kw["timeLimit"] = float(time_limit)
    if backend == "cbc":
        return pulp.PULP_CBC_CMD(**kw)
    if backend == "scip":
        need("pyscipopt", "solve", what="the SCIP engine")
        return pulp.SCIP_PY(**kw)
    if backend == "highs":
        need("highspy", "solve", what="the HiGHS engine")
        return pulp.HiGHS(**kw)
    raise TeeError(
        "solve_bad_backend",
        f"'{backend}' is not a solver backend.",
        fix=f"Use one of: {', '.join(BACKENDS)}.",
    )


def _build(pulp, spec: dict[str, Any]):
    sense = str(spec.get("sense", "min")).lower()
    if sense not in ("min", "max"):
        raise TeeError(
            "solve_bad_spec", f"sense='{sense}' is not min or max.", fix="Use 'min' or 'max'."
        )
    variables = dict(spec.get("variables") or {})
    if not variables:
        raise TeeError(
            "solve_bad_spec",
            "No variables declared.",
            fix='variables: {"x": {"lb": 0, "ub": 10, "type": "cont|int|bin"}}',
        )
    prob = pulp.LpProblem("tee", pulp.LpMaximize if sense == "max" else pulp.LpMinimize)
    kinds = {"cont": "Continuous", "int": "Integer", "bin": "Binary"}
    vs: dict[str, Any] = {}
    for name, d in variables.items():
        d = dict(d or {})
        kind = str(d.get("type", "cont")).lower()
        if kind not in kinds:
            raise TeeError(
                "solve_bad_spec",
                f"variable '{name}': type '{kind}' is unknown.",
                fix="Use cont, int or bin.",
            )
        lb = d.get("lb", 0)
        ub = d.get("ub")
        vs[name] = pulp.LpVariable(name, lb, ub, kinds[kind])

    obj = dict(spec.get("objective") or {})
    unknown = set(obj) - set(vs)
    if unknown:
        raise TeeError(
            "solve_bad_spec",
            f"objective names undeclared variables: {sorted(unknown)}",
            fix="Declare every name under `variables` first.",
        )
    prob += pulp.lpSum(float(c) * vs[n] for n, c in obj.items()) if obj else 0

    ops = {"<=": "le", ">=": "ge", "==": "eq", "=": "eq"}
    cons = list(spec.get("constraints") or [])
    for i, c in enumerate(cons):
        c = dict(c or {})
        lhs = dict(c.get("lhs") or {})
        unknown = set(lhs) - set(vs)
        if unknown:
            raise TeeError(
                "solve_bad_spec",
                f"constraint {i} names undeclared variables: {sorted(unknown)}",
                fix="Declare every name under `variables` first.",
            )
        op = str(c.get("op", "<="))
        if op not in ops:
            raise TeeError(
                "solve_bad_spec",
                f"constraint {i}: op '{op}' is unknown.",
                fix="Use <=, >= or ==.",
            )
        name = str(c.get("name") or f"c{i}")
        expr = pulp.lpSum(float(k) * vs[n] for n, k in lhs.items())
        rhs = float(c.get("rhs", 0))
        prob += (expr <= rhs if op == "<=" else expr >= rhs if op == ">=" else expr == rhs), name
    return prob, vs, cons


def solve(spec: dict[str, Any]) -> dict[str, Any]:
    """Solve one LP/MIP and answer compactly."""
    pulp = _pulp()
    backend = str(spec.get("backend") or "highs").lower()
    show = max(0, min(int(spec.get("show") or DEFAULT_SHOW), SHOW_CAP))
    prob, vs, cons = _build(pulp, spec)
    solver = _solver(pulp, backend, spec.get("time_limit"))

    started = time.monotonic()
    with muted_stdout() as sink:
        prob.solve(solver)
    wall = round(time.monotonic() - started, 4)

    status = pulp.LpStatus[prob.status].lower()
    values = {}
    for name, v in vs.items():
        val = v.value()
        values[name] = 0.0 if val is None else round(float(val), 9)
    nonzero = {k: v for k, v in values.items() if abs(v) > 1e-9}
    ranked = sorted(nonzero.items(), key=lambda kv: -abs(kv[1]))

    binding: list[str] = []
    for c in cons:
        cname = str(c.get("name") or "")
        lhs = dict(c.get("lhs") or {})
        got = sum(float(k) * values.get(n, 0.0) for n, k in lhs.items())
        if abs(got - float(c.get("rhs", 0))) <= 1e-7:
            binding.append(cname or "(unnamed)")

    objective = pulp.value(prob.objective)
    payload = {
        "values": values,
        "status": status,
        "objective": None if objective is None else round(float(objective), 9),
        "backend": backend,
        "solver_log": sink.text.strip(),
    }
    sid = _remember(payload)

    out: dict[str, Any] = {
        "ok": status == "optimal",
        "status": status,
        "objective": payload["objective"],
        "backend": backend,
        "wall_s": wall,
        "n_variables": len(vs),
        "n_constraints": len(cons),
        "n_nonzero": len(nonzero),
        "solution_id": sid,
    }
    if ranked:
        out["nonzero"] = dict(ranked[:show])
        if len(ranked) > show:
            out["shown"] = show
            out["note"] = (
                f"{len(ranked) - show} more non-zero variables - "
                f"solve_detail {{solution_id: '{sid}'}} pages them"
            )
    if binding:
        out["binding"] = binding[:12]
    if status != "optimal":
        out["fix"] = _status_fix(status)
    return out


def _status_fix(status: str) -> str:
    return {
        "infeasible": "No point satisfies every constraint. Relax one, or "
        "call solve_detail for the model shape.",
        "unbounded": "The objective can grow without limit - a variable is "
        "missing an upper bound, or a constraint is missing.",
        "undefined": "The solver stopped without a verdict; a time_limit may have expired.",
        "not solved": "The solver did not run. Check the backend is installed.",
    }.get(status, "See solve_detail for the solver's own log.")


def detail(solution_id: str, offset: int = 0, limit: int = 50, log: bool = False):
    """Page the full solution vector, or fetch the solver's own log."""
    payload = _STORE.get(str(solution_id))
    if payload is None:
        raise TeeError(
            "solve_unknown_solution",
            f"No solution '{solution_id}' in this session.",
            fix=f"Known: {', '.join(_STORE) or '(none yet)'}. Re-run solve_lp / solve_mip.",
        )
    if log:
        return {
            "solution_id": solution_id,
            "backend": payload["backend"],
            "solver_log": payload["solver_log"] or "(the engine printed nothing)",
        }
    items = sorted(payload["values"].items())
    offset = max(0, int(offset))
    limit = max(1, min(int(limit), 500))
    page = items[offset : offset + limit]
    return {
        "solution_id": solution_id,
        "status": payload["status"],
        "objective": payload["objective"],
        "offset": offset,
        "returned": len(page),
        "total": len(items),
        "values": dict(page),
    }


def cpsat(spec: dict[str, Any]) -> dict[str, Any]:
    """OR-Tools CP-SAT: integer constraint programming - combinatorial
    feasibility and scheduling, a different paradigm from LP.

    Runs in a SUBPROCESS, and that is not fussiness. `ortools` and `highspy`
    bundle different builds of HiGHS, and the dynamic linker resolves
    OR-Tools' symbols against whichever libhighs loaded first. Measured
    here: importing highspy before ortools raises ImportError (symbol
    __Z19setLocalOptionValue... not found). A server that dispatches tools
    in model-chosen order cannot control that, so CP-SAT gets a clean
    interpreter. Cost is one process spawn; the alternative is a solver
    that works or not depending on which tool ran first.
    """
    need("ortools", "solve", what="the CP-SAT engine")
    worker = Path(__file__).parent / "_cpsat_worker.py"
    show = max(0, min(int(spec.get("show") or DEFAULT_SHOW), SHOW_CAP))
    timeout = float(spec.get("time_limit") or 0) + 60.0

    started = time.monotonic()
    try:
        proc = subprocess.run(
            [sys.executable, str(worker)],
            input=json.dumps(spec),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise TeeError(
            "solve_timeout",
            f"CP-SAT did not finish within {timeout:.0f}s.",
            fix="Set a smaller time_limit, or reduce the model.",
        ) from exc
    wall = round(time.monotonic() - started, 4)

    if proc.returncode != 0 or not proc.stdout.strip():
        raise TeeError(
            "solve_worker_failed",
            f"The CP-SAT worker exited {proc.returncode} without an answer.",
            fix=(proc.stderr or "").strip()[-300:] or "Check the ortools install.",
        )
    try:
        raw = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise TeeError(
            "solve_worker_failed",
            "The CP-SAT worker did not return JSON.",
            fix="Something wrote to its stdout; report this - the worker mutes fd 1.",
        ) from exc
    if raw.get("error"):
        raise TeeError(
            "solve_bad_spec", str(raw.get("message") or raw["error"]), fix="Check the spec shape."
        )

    status = str(raw.get("status", "unknown"))
    out: dict[str, Any] = {
        "ok": status in ("optimal", "feasible"),
        "status": status,
        "backend": "cp-sat",
        "wall_s": wall,
        "n_variables": int(raw.get("n_variables") or 0),
    }
    values = {k: float(v) for k, v in dict(raw.get("values") or {}).items()}
    if out["ok"]:
        nonzero = {k: v for k, v in values.items() if abs(v) > 1e-9}
        sid = _remember(
            {
                "values": values,
                "status": status,
                "objective": raw.get("objective"),
                "backend": "cp-sat",
                "solver_log": str(raw.get("solver_log") or ""),
            }
        )
        out["solution_id"] = sid
        out["n_nonzero"] = len(nonzero)
        if raw.get("objective") is not None:
            out["objective"] = round(float(raw["objective"]), 9)
        ranked = sorted(nonzero.items(), key=lambda kv: -abs(kv[1]))
        out["nonzero"] = {k: (int(v) if float(v).is_integer() else v) for k, v in ranked[:show]}
        if len(ranked) > show:
            out["note"] = (
                f"{len(ranked) - show} more - solve_detail {{solution_id: '{sid}'}} pages them"
            )
    else:
        out["fix"] = _status_fix(status)
    return out


def backends() -> dict[str, Any]:
    """Which engines are actually installed, and which is the default."""
    rows = probe_rows(
        {
            "highs": "highspy",
            "scip": "pyscipopt",
            "cbc": "pulp",
            "cp-sat": "ortools",
            "modelling (pulp)": "pulp",
        }
    )
    ready = [k for k, v in rows.items() if v.get("installed")]
    return {
        "backends": rows,
        "ready": ready,
        "default": "highs"
        if rows.get("highs", {}).get("installed")
        else (ready[0] if ready else None),
        "fix": None if ready else "uv pip install 'tee-engine[solve]'",
    }
