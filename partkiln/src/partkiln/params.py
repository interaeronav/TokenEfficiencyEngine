"""Named parameters and the expression evaluator behind them.

A parameter is what makes a part a FAMILY: `W = 120mm`, `H = W/2 - 5mm`,
and every sketch dimension written as `"W"` follows when `W` changes. The
evaluator is deliberately not `eval`: it parses with `ast` in `'eval'` mode
and walks an explicit whitelist - arithmetic, unary sign, numbers, unit
suffixed literals, other parameter names, `pi`, and seven functions. A
model that writes `__import__('os')` into a dimension gets a refusal naming
what IS allowed, not a shell. `^` means power (the CAD spelling), never XOR.

Every parameter value is stored in kernel units (mm / deg) with its kind, so
`W/2` is a length, `A + 15deg` is an angle, and `W + A` is a refusal.
"""

from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from typing import Any

from partkiln.document import CommandError
from partkiln.units import ANGLE_TO_DEG, LENGTH_TO_MM, canonical_unit

LENGTH = "length"
ANGLE = "angle"
SCALAR = "scalar"

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# A number followed by a unit suffix, inside an expression. The optional
# "/denominator" keeps `3/8in` a single literal; `W/8in` does not match
# (the numerator must be a number) and reads as W divided by 8 inches.
_UNIT_LITERAL = re.compile(
    r"(?<![A-Za-z0-9_.])(\d+(?:\.\d*)?|\.\d+)(?:\s*/\s*(\d+(?:\.\d*)?))?\s*"
    r"(mm|cm|m|in|ft|mil|deg|rad)\b"
)

_FUNCTIONS: dict[str, Any] = {
    "min": min,
    "max": max,
    "abs": abs,
    "sqrt": math.sqrt,
    "sin": lambda a: math.sin(math.radians(a)),
    "cos": lambda a: math.cos(math.radians(a)),
    "tan": lambda a: math.tan(math.radians(a)),
}
_CONSTANTS: dict[str, float] = {"pi": math.pi}
RESERVED: frozenset[str] = frozenset({*_FUNCTIONS, *_CONSTANTS, *LENGTH_TO_MM, *ANGLE_TO_DEG})

ALLOWED = (
    "numbers, + - * / ^ ( ), unit suffixes (12mm 0.5in 3/8in 30deg), other parameter "
    "names, pi, and min max abs sqrt sin cos tan (trig in degrees)"
)


@dataclass(frozen=True, slots=True)
class Evaluated:
    value: float
    kind: str
    depends_on: tuple[str, ...]


@dataclass(slots=True)
class Param:
    name: str
    value: float
    unit_kind: str
    expr: str
    depends_on: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": round(self.value, 6),
            "unit": {LENGTH: "mm", ANGLE: "deg"}.get(self.unit_kind, ""),
            "expr": self.expr,
            "depends_on": list(self.depends_on),
        }


@dataclass(frozen=True, slots=True)
class Change:
    name: str
    old: float | None
    new: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "old": None if self.old is None else round(self.old, 6),
            "new": round(self.new, 6),
        }


@dataclass(slots=True)
class _Value:
    """An intermediate during evaluation: a number and what kind it is."""

    value: float
    kind: str


class _Evaluator(ast.NodeVisitor):
    def __init__(self, params: Params, literals: dict[str, tuple[float, str]], expr: str) -> None:
        self.params = params
        self.literals = literals
        self.expr = expr
        self.depends: list[str] = []

    def refuse(self, what: str) -> CommandError:
        return CommandError(
            f"{self.expr!r}: {what}. A parameter expression may use {ALLOWED}.",
            code="pk_bad_expr",
        )

    def generic_visit(self, node: ast.AST) -> Any:
        raise self.refuse(f"{type(node).__name__.lower()} is not allowed")

    def visit_Expression(self, node: ast.Expression) -> _Value:
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant) -> _Value:
        if isinstance(node.value, bool) or not isinstance(node.value, int | float):
            raise self.refuse(f"{node.value!r} is not a number")
        return _Value(float(node.value), SCALAR)

    def visit_Name(self, node: ast.Name) -> _Value:
        name = node.id
        if name in self.literals:
            value, kind = self.literals[name]
            return _Value(value, kind)
        if name in _CONSTANTS:
            return _Value(_CONSTANTS[name], SCALAR)
        param = self.params._table.get(name)
        if param is None:
            known = ", ".join(sorted(self.params._table)) or "(none yet)"
            raise CommandError(
                f"{self.expr!r}: unknown name {name!r}. Parameters: {known}. "
                f"Define it first with param_set {{{name}: value}}.",
                code="pk_bad_expr",
            )
        self.depends.append(name)
        return _Value(param.value, param.unit_kind)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> _Value:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return _Value(-operand.value, operand.kind)
        if isinstance(node.op, ast.UAdd):
            return operand
        raise self.refuse(f"unary {type(node.op).__name__.lower()} is not allowed")

    def visit_BinOp(self, node: ast.BinOp) -> _Value:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add | ast.Sub):
            kind = self._additive_kind(left, right)
            lv, rv = self._promote(left, kind), self._promote(right, kind)
            return _Value(lv + rv if isinstance(op, ast.Add) else lv - rv, kind)
        if isinstance(op, ast.Mult):
            if left.kind == SCALAR:
                kind = right.kind
            elif right.kind == SCALAR:
                kind = left.kind
            else:
                kind = SCALAR  # an area, a ratio of lengths: dimensionless to the kernel
            return _Value(left.value * right.value, kind)
        if isinstance(op, ast.Div):
            if right.value == 0.0:
                raise self.refuse("division by zero")
            kind = left.kind if right.kind == SCALAR else SCALAR
            return _Value(left.value / right.value, kind)
        if isinstance(op, ast.Pow):
            if left.value < 0 and right.value != int(right.value):
                raise self.refuse("a negative number to a fractional power is not real")
            try:
                return _Value(float(left.value**right.value), SCALAR)
            except (OverflowError, ZeroDivisionError) as exc:
                raise self.refuse(f"{exc}") from exc
        raise self.refuse(f"operator {type(op).__name__.lower()} is not allowed")

    def _additive_kind(self, left: _Value, right: _Value) -> str:
        if left.kind == right.kind:
            return left.kind
        if left.kind == SCALAR:
            return right.kind
        if right.kind == SCALAR:
            return left.kind
        raise self.refuse(f"cannot add a {left.kind} to an {right.kind}")

    def _promote(self, value: _Value, kind: str) -> float:
        """A bare number meeting a length is in the document unit (Law 12)."""
        if value.kind == kind or kind == SCALAR:
            return value.value
        if kind == LENGTH:
            return value.value * LENGTH_TO_MM[self.params.default_unit]
        return value.value * ANGLE_TO_DEG[self.params.default_angle_unit]

    def visit_Call(self, node: ast.Call) -> _Value:
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise self.refuse("only min, max, abs, sqrt, sin, cos and tan may be called")
        if node.keywords:
            raise self.refuse("keyword arguments are not allowed")
        name = node.func.id
        args = [self.visit(a) for a in node.args]
        if not args:
            raise self.refuse(f"{name}() needs an argument")
        if name in ("sin", "cos", "tan"):
            if len(args) != 1 or args[0].kind == LENGTH:
                raise self.refuse(f"{name}() takes one angle in degrees")
            return _Value(_FUNCTIONS[name](args[0].value), SCALAR)
        if name == "sqrt":
            if len(args) != 1 or args[0].value < 0:
                raise self.refuse("sqrt() takes one non-negative number")
            return _Value(math.sqrt(args[0].value), SCALAR)
        if name == "abs":
            if len(args) != 1:
                raise self.refuse("abs() takes one argument")
            return _Value(abs(args[0].value), args[0].kind)
        kinds = {a.kind for a in args} - {SCALAR}
        if len(kinds) > 1:
            raise self.refuse(f"{name}() mixes a length and an angle")
        kind = kinds.pop() if kinds else SCALAR
        values = [self._promote(a, kind) for a in args]
        return _Value(float(_FUNCTIONS[name](values)), kind)


def _tokenise(expr: str) -> tuple[str, dict[str, tuple[float, str]]]:
    """Replace unit literals with placeholder names and `^` with `**`."""
    literals: dict[str, tuple[float, str]] = {}

    def swap(match: re.Match[str]) -> str:
        numerator, denominator, suffix = match.groups()
        magnitude = float(numerator)
        if denominator:
            if float(denominator) == 0.0:
                raise CommandError(f"{expr!r} divides by zero.", code="pk_bad_expr")
            magnitude /= float(denominator)
        unit = canonical_unit(suffix, LENGTH if suffix in LENGTH_TO_MM else ANGLE)
        if unit in LENGTH_TO_MM:
            value, kind = magnitude * LENGTH_TO_MM[unit], LENGTH
        else:
            value, kind = magnitude * ANGLE_TO_DEG[unit], ANGLE
        key = f"_lit{len(literals)}"
        literals[key] = (value, kind)
        return key

    return _UNIT_LITERAL.sub(swap, expr).replace("^", "**"), literals


class Params:
    """The parameter table, in dependency order.

    `default_unit` is the document unit: what a bare number means when it is
    added to a length inside an expression (`W - 5` is `W - 5mm` in a mm
    document). The document keeps it in step with `set doc units`.
    """

    def __init__(self, default_unit: str = "mm", default_angle_unit: str = "deg") -> None:
        self.default_unit = default_unit
        self.default_angle_unit = default_angle_unit
        self._table: dict[str, Param] = {}
        self.users: dict[str, set[str]] = {}  # param -> ids outside the table using it

    # -- reading ----------------------------------------------------------

    def __contains__(self, name: object) -> bool:
        return name in self._table

    def __iter__(self):
        return iter(self._table.values())

    def __len__(self) -> int:
        return len(self._table)

    def names(self) -> list[str]:
        return sorted(self._table)

    def get(self, name: str) -> Param:
        param = self._table.get(name)
        if param is None:
            known = ", ".join(sorted(self._table)) or "(none yet)"
            raise CommandError(
                f"no parameter {name!r}. Parameters: {known}. "
                f"Define it with param_set {{{name}: value}}.",
                code="pk_ref_unknown",
            )
        return param

    def value(self, name: str) -> float:
        return self.get(name).value

    def used_by(self, name: str) -> list[str]:
        """Who depends on `name`: other parameters and registered outside users."""
        self.get(name)
        dependents = [p.name for p in self._table.values() if name in p.depends_on]
        return sorted({*dependents, *self.users.get(name, ())})

    def as_dict(self) -> dict[str, Any]:
        return {name: self._table[name].as_dict() for name in sorted(self._table)}

    # -- evaluation -------------------------------------------------------

    def evaluate(self, expr: str | float) -> Evaluated:
        """Evaluate an expression against the current table. Never mutates."""
        if isinstance(expr, bool):
            raise CommandError(f"{expr!r} is not a value.", code="pk_bad_expr")
        if isinstance(expr, int | float):
            return Evaluated(float(expr), SCALAR, ())
        text = str(expr).strip()
        if not text:
            raise CommandError("an empty expression has no value.", code="pk_bad_expr")
        source, literals = _tokenise(text)
        try:
            tree = ast.parse(source, mode="eval")
        except SyntaxError as exc:
            raise CommandError(
                f"{text!r} is not an expression ({exc.msg}). A parameter expression may use "
                f"{ALLOWED}.",
                code="pk_bad_expr",
            ) from exc
        walker = _Evaluator(self, literals, text)
        result = walker.visit(tree)
        if not math.isfinite(result.value):
            raise CommandError(
                f"{text!r} does not evaluate to a finite number.", code="pk_bad_expr"
            )
        return Evaluated(result.value, result.kind, tuple(dict.fromkeys(walker.depends)))

    # -- writing ----------------------------------------------------------

    def set(self, name: str, expr: str | float) -> list[Change]:
        """Create or redefine one parameter; re-evaluate everything downstream.

        Returns every parameter whose VALUE changed, the target included,
        each with its old and new value - the "blast radius" Law 14 asks
        an edit to report. A cycle or a bad expression leaves the table
        exactly as it was.
        """
        return self.set_many({name: expr})["changes"]

    def set_many(self, assignments: dict[str, str | float]) -> dict[str, Any]:
        if not assignments:
            raise CommandError(
                "param_set needs {name: value} pairs, e.g. {W: '120mm', H: 'W/2'}.",
                code="pk_needs",
            )
        before = {n: p.value for n, p in self._table.items()}
        snapshot = {
            n: Param(p.name, p.value, p.unit_kind, p.expr, p.depends_on)
            for n, p in self._table.items()
        }
        try:
            for name, expr in assignments.items():
                self._define(str(name), expr)
            order = self._order()
            for name in order:
                param = self._table[name]
                evaluated = self.evaluate(param.expr)
                param.value = evaluated.value
                param.unit_kind = evaluated.kind
                param.depends_on = evaluated.depends_on
        except CommandError:
            self._table = snapshot
            raise
        changes = [
            Change(name, before.get(name), p.value)
            for name, p in self._table.items()
            if name not in before or before[name] != p.value
        ]
        changes.sort(key=lambda c: c.name)
        return {"changes": changes, "unchanged": len(self._table) - len(changes)}

    def delete(self, name: str) -> None:
        users = self.used_by(name)
        if users:
            raise CommandError(
                f"{name!r} is used by {', '.join(users)}. Change those first, or set "
                f"{name} to a value instead of deleting it.",
                code="pk_delete_blocked",
            )
        del self._table[name]

    def _define(self, name: str, expr: str | float) -> None:
        if not _NAME.match(name):
            raise CommandError(
                f"{name!r} is not a parameter name. Use letters, digits and _ , "
                "starting with a letter (W, hole_dia, T2).",
                code="pk_bad_expr",
            )
        if name in RESERVED:
            raise CommandError(
                f"{name!r} is reserved (a function, pi, or a unit). Pick another name.",
                code="pk_bad_expr",
            )
        if isinstance(expr, bool) or expr is None:
            raise CommandError(f"{name}: {expr!r} is not a value.", code="pk_bad_expr")
        text = str(expr).strip() if isinstance(expr, str) else repr(float(expr))
        evaluated = self.evaluate(text)  # validates the expression against the CURRENT table
        if name in evaluated.depends_on:
            raise CommandError(
                f"{name} = {text!r} refers to itself. A parameter cannot depend on its own value.",
                code="pk_bad_expr",
            )
        self._table[name] = Param(name, evaluated.value, evaluated.kind, text, evaluated.depends_on)

    def _order(self) -> list[str]:
        """Dependency order (Kahn, names sorted at each level). Cycles refuse."""
        deps = {n: set(p.depends_on) & set(self._table) for n, p in self._table.items()}
        remaining = dict(deps)
        order: list[str] = []
        while remaining:
            ready = sorted(n for n, d in remaining.items() if not d - set(order))
            if not ready:
                cycle = " -> ".join(self._trace_cycle(remaining))
                raise CommandError(
                    f"parameters form a cycle: {cycle}. Break it by giving one of them a value.",
                    code="pk_bad_expr",
                )
            for name in ready:
                order.append(name)
                del remaining[name]
        return order

    @staticmethod
    def _trace_cycle(remaining: dict[str, set[str]]) -> list[str]:
        start = sorted(remaining)[0]
        path = [start]
        seen = {start}
        node = start
        while True:
            nxt = sorted(d for d in remaining[node] if d in remaining)
            if not nxt:
                return path
            node = nxt[0]
            if node in seen:
                return [*path, node]
            seen.add(node)
            path.append(node)


__all__ = [
    "ALLOWED",
    "ANGLE",
    "LENGTH",
    "RESERVED",
    "SCALAR",
    "Change",
    "Evaluated",
    "Param",
    "Params",
]
