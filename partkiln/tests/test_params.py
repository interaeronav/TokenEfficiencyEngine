"""P1 acceptance for parameters: the whitelisted evaluator and the dependency graph."""

from __future__ import annotations

import math

import pytest

from partkiln.document import CommandError, Document
from partkiln.params import ANGLE, LENGTH, SCALAR, Params


def fresh() -> Params:
    p = Params()
    p.set("W", "120mm")
    p.set("H", "80mm")
    return p


def test_expression_with_units_and_names() -> None:
    p = fresh()
    ev = p.evaluate("W/2 - 5mm")
    assert ev.value == pytest.approx(55.0)
    assert ev.kind == LENGTH
    assert ev.depends_on == ("W",)


def test_bare_number_added_to_a_length_is_the_document_unit() -> None:
    p = fresh()
    assert p.evaluate("W - 5").value == pytest.approx(115.0)
    p.default_unit = "in"
    assert p.evaluate("W - 1").value == pytest.approx(120.0 - 25.4)
    assert p.evaluate("2 * W").value == pytest.approx(240.0)  # a factor, not a length


def test_fractions_power_and_functions() -> None:
    p = fresh()
    assert p.evaluate("3/8in").value == pytest.approx(9.525)
    assert p.evaluate("2^3").value == 8.0
    assert p.evaluate("sqrt(16)").value == 4.0
    assert p.evaluate("sin(30deg)").value == pytest.approx(0.5)
    assert p.evaluate("cos(60)").value == pytest.approx(0.5)  # trig is in degrees
    assert p.evaluate("max(W, H, 1000mm)").value == 1000.0
    assert p.evaluate("min(W, H)").kind == LENGTH
    assert p.evaluate("abs(-3mm)").value == 3.0
    assert p.evaluate("pi").value == math.pi
    assert p.evaluate("W * H").kind == SCALAR  # an area is dimensionless to the kernel
    assert p.evaluate("90deg + 0.5rad").kind == ANGLE


@pytest.mark.parametrize(
    "bad",
    [
        "__import__('os')",
        "().__class__",
        "W.real",
        "W[0]",
        "lambda: 1",
        "open('x')",
        "'abc'",
        "W if H else 1",
        "1 < 2",
        "W and H",
        "W % 3",
        "import os",
    ],
)
def test_anything_outside_the_whitelist_refuses(bad: str) -> None:
    p = fresh()
    with pytest.raises(CommandError) as excinfo:
        p.evaluate(bad)
    assert "sqrt" in str(excinfo.value)  # the allowed list rides along with the refusal


def test_undefined_name_refuses_with_the_fix() -> None:
    p = fresh()
    with pytest.raises(CommandError) as excinfo:
        p.evaluate("W + T")
    message = str(excinfo.value)
    assert "'T'" in message and "param_set" in message and "W" in message


def test_length_plus_angle_refuses() -> None:
    p = fresh()
    p.set("A", "30deg")
    with pytest.raises(CommandError, match="cannot add"):
        p.evaluate("W + A")


def test_division_by_zero_refuses() -> None:
    p = fresh()
    with pytest.raises(CommandError, match="division by zero"):
        p.evaluate("W / 0")


def test_set_returns_changes_in_dependency_order_with_old_and_new() -> None:
    p = fresh()
    p.set("half", "W/2")
    p.set("quarter", "half/2")
    changes = p.set("W", "200mm")
    assert [(c.name, c.old, c.new) for c in changes] == [
        ("W", 120.0, 200.0),
        ("half", 60.0, 100.0),
        ("quarter", 30.0, 50.0),
    ]
    assert p.value("quarter") == 50.0
    assert p.used_by("W") == ["half"]
    assert p.used_by("half") == ["quarter"]


def test_set_many_reports_unchanged() -> None:
    p = fresh()
    out = p.set_many({"W": "120mm", "T": "6mm"})
    assert [c.name for c in out["changes"]] == ["T"]
    assert out["unchanged"] == 2  # W (same value) and H


def test_cycle_refuses_and_leaves_the_table_untouched() -> None:
    p = fresh()
    p.set("A", "W + 1mm")
    p.set("B", "A + 1mm")
    with pytest.raises(CommandError) as excinfo:
        p.set("A", "B + 1mm")
    assert "cycle" in str(excinfo.value)
    assert p.value("A") == 121.0  # rolled back
    p.set("C", "1mm")
    with pytest.raises(CommandError, match="itself"):
        p.set("C", "C + 1")


def test_bad_names_and_reserved_words_refuse() -> None:
    p = fresh()
    for name in ("1W", "W-2", "pi", "sin", "mm"):
        with pytest.raises(CommandError):
            p.set(name, "1")


def test_delete_is_blocked_by_users() -> None:
    p = fresh()
    p.set("half", "W/2")
    with pytest.raises(CommandError, match="used by half"):
        p.delete("W")
    p.delete("half")
    p.delete("W")
    assert "W" not in p


def test_as_dict_is_compact_and_rounded() -> None:
    p = fresh()
    p.set("third", "W/3")
    row = p.as_dict()["third"]
    assert row == {"name": "third", "value": 40.0, "unit": "mm", "expr": "W/3", "depends_on": ["W"]}


def test_param_set_refuses_a_value_that_is_not_a_scalar() -> None:
    """DEFECT 7: a list or a dict fell through `float(expr)` as a raw TypeError.

    Rule 5/D8: user input never comes back as a bare TypeError - the refusal
    carries a code and says what a parameter value may be.
    """
    p = fresh()
    for value in ([1, 2], {"a": 1}, None, (3, 4), True):
        with pytest.raises(CommandError) as excinfo:
            p.set("X", value)  # type: ignore[arg-type]
        assert excinfo.value.code == "pk_bad_expr"
        message = str(excinfo.value)
        assert "TypeError" not in message
        assert "number" in message and "expression" in message
    assert "X" not in p
    # and through the verb the model actually writes, still not a TypeError
    doc = Document()
    with pytest.raises(CommandError) as excinfo:
        doc.apply({"op": "param_set", "params": {"W": [1, 2]}})
    assert excinfo.value.code == "pk_bad_expr"
    assert doc.history == [] and doc.params.names() == []
