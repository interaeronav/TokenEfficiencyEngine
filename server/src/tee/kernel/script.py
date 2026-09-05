"""tee_script: the app-side script lane (Phase 8, decision A11).

Programmatic tool calling keeps intermediate tool results out of model
context but excludes MCP tools, so TEE implements the same pattern here:
one bounded script composes many typed tool calls in a single round-trip
and only its `result` returns. This is NOT a code-exec escape hatch - the
script can reach exactly the tools the model could already call, so it adds
no capability, it removes round-trips (and is therefore not gated by
allow_code_exec).

Safety model: the source is parsed and every AST node checked against a
whitelist (no imports, no attribute access, no while, no defs/lambdas, no
underscore names), then interpreted by the tree-walker below - never
exec()'d - under three hard budgets (tool calls, interpreter steps, wall
clock). Mutations are atomic at script scope: the touched adapter is
checkpointed at first use and rolled back on any uncaught error.
"""

from __future__ import annotations

import ast
import contextlib
import time
from typing import Any

from tee.kernel.errors import TeeError

MAX_CALLS = 200
MAX_STEPS = 10_000
MAX_SECONDS = 120.0
MAX_SOURCE_CHARS = 20_000

_ALLOWED_STMT = (
    ast.Assign,
    ast.AugAssign,
    ast.Expr,
    ast.If,
    ast.For,
    ast.Break,
    ast.Continue,
    ast.Pass,
)
_ALLOWED_EXPR = (
    ast.Constant,
    ast.Name,
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    ast.Call,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Subscript,
    ast.Slice,
    ast.IfExp,
    ast.ListComp,
    ast.DictComp,
    ast.comprehension,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.keyword,
    # operator / context leaf nodes
    ast.Load,
    ast.Store,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)

_BIN_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.Pow: lambda a, b: a**b,
}
_CMP_OPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
    ast.Is: lambda a, b: a is b,
    ast.IsNot: lambda a, b: a is not b,
}

_SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    # no attribute access in the subset, so dict/list methods become helpers
    "keys": lambda d: list(d.keys()),
    "items": lambda d: [[k, v] for k, v in d.items()],
    "get": lambda d, k, default=None: d.get(k, default),
    "append": lambda lst, x: (lst.append(x), lst)[1],
}


def validate_script(code: str) -> ast.Module:
    if len(code) > MAX_SOURCE_CHARS:
        raise TeeError(
            "script_too_long",
            f"Script exceeds {MAX_SOURCE_CHARS} characters.",
            fix="Split the work into smaller scripts.",
        )
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise TeeError(
            "script_syntax",
            f"Line {exc.lineno}: {exc.msg}.",
            fix="tee_script runs a Python subset; assign the final value to `result`.",
        ) from exc
    allowed = _ALLOWED_STMT + _ALLOWED_EXPR + (ast.Module,)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise TeeError(
                "script_forbidden",
                f"Line {getattr(node, 'lineno', '?')}: "
                f"{type(node).__name__} is not allowed in tee_script.",
                fix=(
                    "Allowed: assignments, if/for, list/dict literals and "
                    "comprehensions, f-strings, and calls to the helper "
                    "functions. No import/while/def/lambda/attribute access."
                ),
            )
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise TeeError(
                "script_forbidden",
                f"Line {node.lineno}: names starting with '_' are not allowed.",
            )
    return tree


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Interp:
    def __init__(self, env: dict[str, Any]):
        self.env = env
        self.steps = 0
        self.deadline = time.monotonic() + MAX_SECONDS

    def _tick(self, node: ast.AST) -> None:
        self.steps += 1
        if self.steps > MAX_STEPS:
            raise TeeError(
                "script_budget_exceeded",
                f"Script exceeded {MAX_STEPS} interpreter steps "
                f"(line {getattr(node, 'lineno', '?')}).",
                fix="Do less per script; batch ops instead of per-item calls.",
            )
        if time.monotonic() > self.deadline:
            raise TeeError(
                "script_budget_exceeded",
                f"Script exceeded {MAX_SECONDS:.0f}s (line {getattr(node, 'lineno', '?')}).",
            )

    # -- statements --------------------------------------------------------

    def run(self, body: list[ast.stmt]) -> Any:
        last = None
        for stmt in body:
            last = self.exec_stmt(stmt)
        return last

    def exec_stmt(self, node: ast.stmt) -> Any:
        self._tick(node)
        if isinstance(node, ast.Expr):
            return self.eval(node.value)
        if isinstance(node, ast.Assign):
            value = self.eval(node.value)
            for target in node.targets:
                self._assign(target, value)
            return None
        if isinstance(node, ast.AugAssign):
            if not isinstance(node.target, ast.Name):
                raise TeeError(
                    "script_forbidden",
                    f"Line {node.lineno}: augmented assignment only to plain names.",
                )
            op = _BIN_OPS.get(type(node.op))
            if op is None:
                raise TeeError("script_forbidden", f"Line {node.lineno}: operator not allowed.")
            self.env[node.target.id] = op(self._load(node.target.id, node), self.eval(node.value))
            return None
        if isinstance(node, ast.If):
            branch = node.body if self.eval(node.test) else node.orelse
            return self.run(branch)
        if isinstance(node, ast.For):
            iterable = self.eval(node.iter)
            for item in iterable:
                self._tick(node)
                self._assign(node.target, item)
                try:
                    self.run(node.body)
                except _Break:
                    break
                except _Continue:
                    continue
            return None
        if isinstance(node, ast.Break):
            raise _Break()
        if isinstance(node, ast.Continue):
            raise _Continue()
        if isinstance(node, ast.Pass):
            return None
        raise TeeError("script_forbidden", f"{type(node).__name__} is not allowed.")

    def _assign(self, target: ast.expr, value: Any) -> None:
        if isinstance(target, ast.Name):
            if target.id in _SAFE_BUILTINS or target.id in (
                "call",
                "batch",
                "summary",
                "detail",
                "diff",
            ):
                raise TeeError(
                    "script_forbidden",
                    f"Line {target.lineno}: cannot reassign helper '{target.id}'.",
                )
            self.env[target.id] = value
        elif isinstance(target, ast.Tuple):
            values = list(value)
            if len(values) != len(target.elts):
                raise TeeError(
                    "script_error",
                    f"Line {target.lineno}: cannot unpack {len(values)} values "
                    f"into {len(target.elts)} names.",
                )
            for t, v in zip(target.elts, values, strict=True):
                self._assign(t, v)
        elif isinstance(target, ast.Subscript):
            container = self.eval(target.value)
            container[self.eval(target.slice)] = value
        else:
            raise TeeError(
                "script_forbidden",
                f"Line {target.lineno}: cannot assign to {type(target).__name__}.",
            )

    def _load(self, name: str, node: ast.AST) -> Any:
        if name in self.env:
            return self.env[name]
        raise TeeError(
            "script_error",
            f"Line {getattr(node, 'lineno', '?')}: name '{name}' is not defined.",
        )

    # -- expressions -------------------------------------------------------

    def eval(self, node: ast.expr) -> Any:
        self._tick(node)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return self._load(node.id, node)
        if isinstance(node, ast.BinOp):
            op = _BIN_OPS.get(type(node.op))
            if op is None:
                raise TeeError("script_forbidden", f"Line {node.lineno}: operator not allowed.")
            return op(self.eval(node.left), self.eval(node.right))
        if isinstance(node, ast.UnaryOp):
            value = self.eval(node.operand)
            if isinstance(node.op, ast.USub):
                return -value
            if isinstance(node.op, ast.UAdd):
                return +value
            return not value
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value = True
                for part in node.values:
                    value = self.eval(part)
                    if not value:
                        return value
                return value
            for part in node.values:
                value = self.eval(part)
                if value:
                    return value
            return value
        if isinstance(node, ast.Compare):
            left = self.eval(node.left)
            for op, comparator in zip(node.ops, node.comparators, strict=True):
                right = self.eval(comparator)
                if not _CMP_OPS[type(op)](left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise TeeError(
                    "script_forbidden",
                    f"Line {node.lineno}: only direct helper calls are allowed.",
                )
            fn = self._load(node.func.id, node)
            args = [self.eval(a) for a in node.args]
            kwargs = {}
            for kw in node.keywords:
                if kw.arg is None:
                    raise TeeError(
                        "script_forbidden", f"Line {node.lineno}: ** expansion not allowed."
                    )
                kwargs[kw.arg] = self.eval(kw.value)
            return fn(*args, **kwargs)
        if isinstance(node, ast.List):
            return [self.eval(e) for e in node.elts]
        if isinstance(node, ast.Tuple):
            return tuple(self.eval(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            out = {}
            for key, value in zip(node.keys, node.values, strict=True):
                if key is None:
                    raise TeeError(
                        "script_forbidden", f"Line {node.lineno}: ** expansion not allowed."
                    )
                out[self.eval(key)] = self.eval(value)
            return out
        if isinstance(node, ast.Subscript):
            return self.eval(node.value)[self.eval(node.slice)]
        if isinstance(node, ast.Slice):
            lower = self.eval(node.lower) if node.lower else None
            upper = self.eval(node.upper) if node.upper else None
            step = self.eval(node.step) if node.step else None
            return slice(lower, upper, step)
        if isinstance(node, ast.IfExp):
            return self.eval(node.body) if self.eval(node.test) else self.eval(node.orelse)
        if isinstance(node, ast.ListComp):
            return list(self._comp(node.generators, lambda: self.eval(node.elt)))
        if isinstance(node, ast.DictComp):
            return dict(
                self._comp(node.generators, lambda: (self.eval(node.key), self.eval(node.value)))
            )
        if isinstance(node, ast.JoinedStr):
            parts = []
            for part in node.values:
                if isinstance(part, ast.Constant):
                    parts.append(str(part.value))
                else:  # FormattedValue
                    parts.append(self._format(part))
            return "".join(parts)
        raise TeeError("script_forbidden", f"{type(node).__name__} is not allowed.")

    def _format(self, node: ast.FormattedValue) -> str:
        value = self.eval(node.value)
        spec = self.eval(node.format_spec) if node.format_spec else ""
        return format(value, spec)

    def _comp(self, generators: list[ast.comprehension], produce):
        def rec(index: int):
            if index == len(generators):
                yield produce()
                return
            gen = generators[index]
            for item in self.eval(gen.iter):
                self._tick(gen.iter)
                self._assign(gen.target, item)
                if all(self.eval(cond) for cond in gen.ifs):
                    yield from rec(index + 1)

        yield from rec(0)


def run_script(app, code: str, default_adapter: str | None = None) -> dict[str, Any]:
    """Validate, interpret, and atomically apply one script. Returns only the
    script's `result` (or its last expression) plus a compact side-effect
    summary - intermediate tool outputs never leave the server.

    `default_adapter` is the lane tee_script was called with, or None (A68):
    then batch() routes each batch by content and the reads resolve the lane
    lazily, so a script on a multi-lane server binds to no lane it did not
    name."""
    tree = validate_script(code)

    calls = {"n": 0}
    touched: dict[str, str] = {}  # adapter -> script-scope checkpoint id

    def _lane(adapter: str | None) -> str:
        """The lane a read or a guard means: the one named, else the script's,
        else what the app resolves (the sole lane, or a declared default)."""
        return app.resolve_adapter(adapter or default_adapter)

    def _spend_call(label: str) -> None:
        calls["n"] += 1
        if calls["n"] > MAX_CALLS:
            raise TeeError(
                "script_budget_exceeded",
                f"Script exceeded {MAX_CALLS} tool calls (at {label}).",
                fix="Batch ops instead of per-item calls.",
            )

    def _guard(adapter_name: str) -> None:
        """Checkpoint an adapter once, before the script first acts on it."""
        if adapter_name in touched:
            return
        adapter = app.adapters.get(adapter_name)
        if adapter is None or not adapter.probe():
            return
        cache = app.cache(adapter_name)
        cp = app.checkpoints.create(adapter, "auto:script", cache.revision, lane=adapter_name)
        touched[adapter_name] = cp.id

    def call(name: str, args: dict | None = None):
        _spend_call(f"call('{name}')")
        # Guard the lane this script is bound to, when there is one. A
        # multi-lane script bound to none guards nothing here: which lane a
        # virtual tool touches is its own metadata (A68 P1d), and a batch it
        # runs takes its own checkpoint.
        with contextlib.suppress(TeeError):
            _guard(_lane(None))
        return app.registry.call(name, args or {})

    def batch(ops: list, adapter: str | None = None, label: str | None = None):
        _spend_call(f"batch({len(ops)} ops)")
        route = app.route_batch(ops, adapter or default_adapter)  # A68: by content
        _guard(route.adapter)
        # the script-scope checkpoint from _guard owns atomicity here; an
        # inner per-batch checkpoint would be redundant dispatches (A35 P2)
        return app.run_batch(
            route.adapter,
            ops,
            label,
            checkpoint=route.adapter not in touched,
            routed=route.how,
        )

    def summary(adapter: str | None = None, **kwargs):
        _spend_call("summary()")
        if adapter is None and default_adapter is None and app.unbound():
            return app.overview()  # A68: the lanes at a glance
        lane = _lane(adapter)
        app.warm(lane)
        return app.cache(lane).summary(**kwargs)

    def detail(entity_id: str, adapter: str | None = None):
        _spend_call("detail()")
        if adapter is None and default_adapter is None and app.unbound():
            lane = app.locate(entity_id)  # A68: found where it lives
        else:
            lane = _lane(adapter)
        ent = app.cache(lane).get(entity_id)
        if ent is None:
            raise TeeError("unknown_entity", f"No entity '{entity_id}' in '{lane}'.")
        return ent.detailed()

    def diff(epoch: int, revision: int, adapter: str | None = None):
        _spend_call("diff()")
        return app.cache(_lane(adapter)).diff_since(epoch, revision)

    env: dict[str, Any] = {
        **_SAFE_BUILTINS,
        "call": call,
        "batch": batch,
        "summary": summary,
        "detail": detail,
        "diff": diff,
    }
    interp = _Interp(env)
    try:
        last = interp.run(tree.body)
    except TeeError as exc:
        rolled = _rollback_all(app, touched)
        fix = (exc.fix + " " if exc.fix else "") + rolled
        raise TeeError(exc.code, exc.message, fix=fix.strip()) from exc
    except Exception as exc:  # plain python error inside the script
        rolled = _rollback_all(app, touched)
        raise TeeError(
            "script_error",
            f"{type(exc).__name__}: {exc}",
            fix=rolled.strip() or None,
        ) from exc

    payload: dict[str, Any] = {
        "ok": True,
        "result": env.get("result", last),
        "calls_made": calls["n"],
        "steps": interp.steps,
    }
    if touched:
        payload["checkpoints"] = dict(touched)
        payload["scene"] = {name: app.cache(name).stamp() for name in touched}
    return payload


def _rollback_all(app, touched: dict[str, str]) -> str:
    if not touched:
        return ""
    outcomes = []
    for adapter_name, cp_id in touched.items():
        try:
            app.rollback(adapter_name, cp_id)
            outcomes.append(f"{adapter_name} rolled back to {cp_id}")
        except Exception:
            app.cache(adapter_name).invalidate()
            outcomes.append(
                f"{adapter_name} rollback failed - state may be partial; "
                "run tee_scene_summary(refresh=true)"
            )
    return "Script " + "; ".join(outcomes) + "."
