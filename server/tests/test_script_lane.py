"""tee_script (Phase 8, A11): sandbox rejections, budgets, atomic rollback,
and the composed-loop payoff measured with the project estimator."""

from __future__ import annotations

import pytest

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.kernel.script import run_script, validate_script


@pytest.fixture()
def app(tmp_path):
    application = TeeApp({"fake": FakeAdapter()}, project_root=tmp_path)
    yield application
    application.shutdown()


# -- sandbox -----------------------------------------------------------------


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        "from os import path",
        "while True: pass",
        "def f(): pass",
        "class C: pass",
        "f = lambda: 1",
        "x = [].__class__",
        "x = (1).__class__",
        "open('/etc/passwd')",  # open isn't defined, but attribute-free: name error at runtime
        "_secret = 1",
        "with open('x') as f: pass",
        "try:\n    pass\nexcept Exception:\n    pass",
        "assert True",
        "raise ValueError('x')",
        "x = 1; del x",
        "global x",
        "x = (y := 2)",
    ],
)
def test_forbidden_constructs_rejected(code):
    if code == "open('/etc/passwd')":
        pytest.skip("covered by test_unknown_name_is_runtime_error")
    with pytest.raises(TeeError) as err:
        validate_script(code)
    assert err.value.code in ("script_forbidden", "script_syntax")


def test_unknown_name_is_runtime_error(app):
    with pytest.raises(TeeError) as err:
        run_script(app, "x = open('/etc/passwd')")
    assert err.value.code == "script_error"
    assert "open" in err.value.message


def test_helper_reassignment_rejected(app):
    with pytest.raises(TeeError) as err:
        run_script(app, "call = 1")
    assert err.value.code == "script_forbidden"


def test_attribute_access_rejected():
    with pytest.raises(TeeError) as err:
        validate_script("x = call('tool').result")
    assert err.value.code == "script_forbidden"
    assert "Attribute" in err.value.message


# -- budgets -----------------------------------------------------------------


def test_step_budget_bounds_hot_loops(app):
    with pytest.raises(TeeError) as err:
        run_script(app, "x = 0\nfor i in range(100000):\n    x = x + 1")
    assert err.value.code == "script_budget_exceeded"
    assert "steps" in err.value.message


def test_call_budget(app):
    app.registry.register(
        VirtualTool(
            name="noop",
            description="noop",
            schema={"type": "object", "properties": {}},
            handler=lambda args: {"ok": True},
        )
    )
    with pytest.raises(TeeError) as err:
        run_script(app, "for i in range(500):\n    call('noop', {})")
    assert err.value.code == "script_budget_exceeded"
    assert "tool calls" in err.value.message


def test_source_length_cap(app):
    with pytest.raises(TeeError) as err:
        validate_script("x = 1\n" * 5000)
    assert err.value.code == "script_too_long"


# -- language subset behaves --------------------------------------------------


def test_pure_computation(app):
    out = run_script(
        app,
        "xs = [i * i for i in range(6) if i % 2 == 0]\n"
        "d = {str(x): x for x in xs}\n"
        "result = {'sum': sum(xs), 'keys': sorted(keys(d)), 'top': max(xs)}\n",
    )
    assert out["ok"] is True
    assert out["result"] == {"sum": 20, "keys": ["0", "16", "4"], "top": 16}
    assert out["calls_made"] == 0
    assert "checkpoints" not in out  # nothing touched, nothing checkpointed


def test_fstrings_and_subscripts(app):
    out = run_script(
        app,
        "d = {'a': [1, 2, 3]}\n"
        "d['b'] = d['a'][1:]\n"
        "result = f\"got {len(d['b'])} and {d['a'][0]:03d}\"\n",
    )
    assert out["result"] == "got 2 and 001"


def test_last_expression_is_fallback_result(app):
    assert run_script(app, "1 + 2")["result"] == 3


# -- composition over real tools ----------------------------------------------


def test_batch_loop_composes_and_returns_only_final(app):
    out = run_script(
        app,
        "made = batch([{'op': 'create', 'kind': 'cube', 'name': f'B{i}'}\n"
        "              for i in range(20)])\n"
        "moved = 0\n"
        "for eid in made['created']:\n"
        "    e = detail(eid)\n"
        "    if get(e, 'name') > 'B15':\n"
        "        moved = moved + 1\n"
        "result = {'created': len(made['created']), 'gt15': moved}\n",
    )
    # lexicographic: B16-B19 plus B2..B9 - matches real Python semantics
    assert out["result"] == {"created": 20, "gt15": 12}
    assert out["calls_made"] == 21
    assert "fake" in out["checkpoints"]
    # the response is compact: no per-entity payloads leaked into it
    assert estimate_tokens(out) < 150
    assert app.cache("fake").summary()["total"] == 20


def test_error_mid_script_rolls_back_everything(app):
    with pytest.raises(TeeError) as err:
        run_script(
            app,
            "batch([{'op': 'create', 'kind': 'cube', 'name': 'Kept1'}])\n"
            "batch([{'op': 'create', 'kind': 'cube', 'name': 'Kept2'}])\n"
            "boom = nonexistent_helper()\n",
        )
    assert err.value.code == "script_error"
    assert "rolled back" in (err.value.fix or "")
    # both successful batches were undone: script scope is atomic
    assert app.cache("fake").summary()["total"] == 0


def test_inner_teeerror_keeps_code_and_reports_rollback(app):
    with pytest.raises(TeeError) as err:
        run_script(
            app,
            "batch([{'op': 'create', 'kind': 'cube', 'name': 'A'}])\n"
            "batch([{'op': 'delete', 'id': 'no-such-id'}])\n",
        )
    assert "rolled back" in (err.value.fix or "")
    assert app.cache("fake").summary()["total"] == 0
