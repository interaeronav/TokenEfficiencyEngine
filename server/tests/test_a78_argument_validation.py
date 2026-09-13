from __future__ import annotations

import pytest

from tee.kernel.errors import TeeError
from tee.kernel.registry import ToolRegistry, VirtualTool


def registry():
    calls = []
    reg = ToolRegistry()
    reg.register(
        VirtualTool(
            "example",
            "A bounded nested request.",
            {
                "type": "object",
                "properties": {
                    "mode": {"type": "string", "enum": ["corner", "straight"]},
                    "rows": {
                        "type": "array",
                        "maxItems": 2,
                        "items": {
                            "type": "object",
                            "required": ["width"],
                            "properties": {
                                "width": {"type": "number"},
                            },
                        },
                    },
                },
            },
            lambda args: calls.append(args) or {"ok": True},
            capability="read-session",
        )
    )
    return reg, calls


@pytest.mark.parametrize(
    ("args", "path"),
    [
        ({"mode": "invented"}, "mode"),
        ({"rows": [{"width": "2 mm"}]}, "rows[0].width"),
        ({"rows": [{"width": True}]}, "rows[0].width"),
        ({"rows": [{}]}, "rows[0].width"),
        ({"rows": [{"width": 1}] * 3}, "rows"),
    ],
)
def test_schema_failure_names_the_nested_location_without_calling_handler(args, path):
    reg, calls = registry()
    with pytest.raises(TeeError) as error:
        reg.call("example", args)
    assert path in error.value.message
    assert error.value.fix and calls == []


def test_enum_error_supplies_choices_without_another_describe_call():
    reg, calls = registry()
    with pytest.raises(TeeError) as error:
        reg.call("example", {"mode": "invented"})
    assert "corner" in error.value.fix and "straight" in error.value.fix
    assert calls == []


def test_valid_nested_values_and_existing_optional_null_contract():
    reg, calls = registry()
    assert reg.call("example", {"mode": "corner", "rows": [{"width": 2.5}]})["ok"]
    assert reg.call("example", {"mode": None})["ok"]
    assert len(calls) == 2
