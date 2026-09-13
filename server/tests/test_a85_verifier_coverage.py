"""Measure what each chore's verifier actually catches, and gate on it.

TEE's chores are guarded by their own `validate()` closures, and the router
labels a rejection `llm_bad_shape` as though it were a verification failure.
`router.py` says in its own source that for triage this is only a schema check
and never evidence the answer is right - but nothing enforced that, so any
"retry harder" mechanism (a thinking pass, best-of-N sampling) could be pointed
at a chore whose verifier cannot tell a better answer from a differently-wrong
one.

This suite turns that judgement into a number. For each chore it feeds seeded
plausible-but-wrong answers through the real chore path and counts how many the
validator ACCEPTS - the false-accept rate, eps. Detector coverage is 1 - eps.

Why it is a gate and not a report. With per-attempt error q over N attempts,
standby redundancy with imperfect detection gives

    P(fail after N) = eps*q + (1 - eps)*q**N

whose first term is a floor no N crosses: errors the verifier cannot see are
never retried, because nothing knows to retry them. At eps = 1 that is
P(fail) = q for every N - widening is provably useless, not merely unproven.
So `1 - eps` is the WIDENING CEILING: the most any amount of extra effort could
ever buy. It is the quantum threshold theorem's shape, and it is why four of
these eight chores are refused outright.

Every chore also gets a TRUE-ACCEPT control. Without it a validator that
rejects everything would score a perfect eps of 0 and look ideal.

Runs offline: no model, no network, no DCC.
"""

from __future__ import annotations

import contextlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from tee.kernel.errors import TeeError
from tee.llm import chores, profiles


@contextlib.contextmanager
def _endpoint(reply: str):
    class H(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            b = json.dumps({"data": [{"id": "fake"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_POST(self) -> None:
            self.rfile.read(int(self.headers["Content-Length"]))
            b = json.dumps(
                {"choices": [{"message": {"role": "assistant", "content": reply}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def log_message(self, *a: object) -> None:
            return

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}/v1"
    finally:
        srv.shutdown()
        srv.server_close()


def _accepts(chore: str, reply: str, **kwargs) -> bool:
    """True when the chore's validator lets this answer through."""
    with _endpoint(reply) as url:
        profiles.BUILTIN_PROFILES["_cov"] = {"url": url, "model": "fake", "adapters": ""}
        try:
            out = getattr(chores, chore)(refine="local", cfg={"_profile": "_cov"}, **kwargs)
            return out is not None
        except TeeError:
            return False
        finally:
            profiles.BUILTIN_PROFILES.pop("_cov", None)


J = json.dumps
_SRC = (
    "The plate is 137 mm wide. The header sits at 350 mm. Rotations in bpy are "
    "radians. Gravity is -9.81 on Z."
)
# repair_script is reached ONLY from the tee_script failure handler
# (server.py:467), so its input is tee_script source - a restricted AST subset
# with no attribute access. Seeding it with bpy code, as a first pass here did,
# measures the validator against input it never receives.
_CODE = "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate', 'rotation': 0}])"
_CANDS = [{"id": f"t{i}", "title": f"item {i}"} for i in range(5)]
_FACTS = ["plate 137 mm wide and header at 350 mm", "gap is 12 mm"]

# chore -> (call kwargs, [wrong answers], correct answer)
CASES: dict[str, tuple[dict, list[str], str]] = {
    "triage": (
        dict(
            failure="TypeError: primitive_cube_add() got an unexpected keyword argument 'rotation'",
            context="",
        ),
        [
            J(
                {
                    "diagnosis": "Blender 2.8 removed the rotation kwarg.",
                    "fix": "Set rotation_euler after creation.",
                    "confidence": "grounded",
                }
            ),
            J(
                {
                    "diagnosis": "Bad argument.",
                    "fix": "Remove the rotation argument.",
                    "confidence": "grounded",
                }
            ),
            J(
                {
                    "diagnosis": "Blender is out of memory.",
                    "fix": "Restart Blender.",
                    "confidence": "grounded",
                }
            ),
        ],
        J(
            {
                "diagnosis": "The signature does not accept 'rotation'.",
                "fix": "Verify the current signature in the docs first.",
                "confidence": "needs_verification",
            }
        ),
    ),
    "repair_script": (
        dict(code=_CODE, error="bad_op: unknown operation field 'rotation'"),
        [
            # the degenerate fix its own prompt warns about: drop the field
            J(
                {
                    "repaired_code": "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate'}])",
                    "note": "dropped the field",
                }
            ),
            J({"repaired_code": "pass", "note": "simplified"}),
            J({"repaired_code": "summary()", "note": "fixed"}),
            # preserves every token and changes the VALUE - the case a
            # token-preservation check cannot see, kept so eps stays honest
            J(
                {
                    "repaired_code": (
                        "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate',"
                        " 'props': {'rotation_euler': [9, 9, 9]}}])"
                    ),
                    "note": "kept rotation",
                }
            ),
        ],
        # a real repair re-expresses the intent instead of deleting it
        J(
            {
                "repaired_code": (
                    "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate',"
                    " 'props': {'rotation_euler': [0, 0, 0]}}])"
                ),
                "note": "moved rotation into props",
            }
        ),
    ),
    "explain_lint": (
        dict(finding="use_nodes accessed on a material with nodes disabled"),
        [
            J({"explanation": "This finding is spurious; ignore the checker."}),
            J({"explanation": "It means the mesh has no UV map."}),
            J({"explanation": "Blender uses metres."}),
        ],
        J({"explanation": "The material has nodes disabled, so use_nodes cannot be read."}),
    ),
    "refine_extract": (
        dict(text=_SRC, question="How wide is the plate?", max_tokens=60),
        [
            J({"sentences": ["Rotations in bpy are radians."]}),
            J({"sentences": ["The plate measures one hundred and thirty-seven millimetres."]}),
            J({"sentences": ["The plate is 200 mm wide."]}),
        ],
        J({"sentences": ["The plate is 137 mm wide."]}),
    ),
    "structure_facts": (
        dict(text=_SRC),
        [
            J({"facts": [{"kind": "dimension", "text": "The plate is 999 mm wide."}]}),
            J({"facts": [{"kind": "dimension", "text": "The header sits at 35 mm."}]}),
            J({"facts": [{"kind": "colour", "text": "The plate is red."}]}),
        ],
        J({"facts": [{"kind": "dimension", "text": "The plate is 137 mm wide."}]}),
    ),
    "compress_recap": (
        dict(recap=["plate 137 mm wide", "header at 350 mm", "baked 40 frames"]),
        [
            J({"summary": "Some work was done on the plate."}),
            J({"summary": "Plate 731 mm wide; header at 503 mm."}),
            J({"summary": "The render finished."}),
        ],
        J({"summary": "Plate 137 mm wide; header at 350 mm; baked 40 frames."}),
    ),
    "rerank": (
        dict(query="item 0", candidates=_CANDS),
        [
            J({"order": ["t4", "t3", "t2", "t1", "t0"]}),
            J({"order": ["t2", "t0", "t4", "t1", "t3"]}),
            J({"order": ["t0", "t1", "t2", "t3"]}),
        ],
        J({"order": ["t0", "t1", "t2", "t3", "t4"]}),
    ),
    "phrase_deviation": (
        dict(facts=_FACTS),
        [
            J({"lines": ["plate is 350 mm wide", "header at 137 mm"]}),
            J({"lines": ["plate 350 mm wide and header at 137 mm", "gap is 12 mm"]}),
            J({"lines": ["plate 137 mm wide and header at 351 mm", "gap is 12 mm"]}),
            J({"lines": ["plate 137 mm wide and header at 350 mm"]}),
        ],
        J({"lines": ["plate 137 mm wide and header at 350 mm", "gap is 12 mm"]}),
    ),
}


@pytest.mark.parametrize("chore", sorted(CASES))
def test_a_good_answer_is_accepted(chore):
    """Without this, a validator that rejects everything scores a perfect eps."""
    kwargs, _, control = CASES[chore]
    assert _accepts(chore, control, **kwargs), (
        f"{chore} rejected a correct answer, so its false-accept rate means nothing"
    )


@pytest.mark.parametrize("chore", sorted(CASES))
def test_the_declared_coverage_is_what_the_verifier_actually_does(chore):
    kwargs, wrong, _ = CASES[chore]
    accepted = [w for w in wrong if _accepts(chore, w, **kwargs)]
    measured = len(accepted) / len(wrong)
    declared = chores.VERIFIER_COVERAGE[chore]
    assert abs(measured - declared) < 0.01, (
        f"{chore}: declared eps={declared:.0%}, measured {measured:.0%} over "
        f"{len(wrong)} seeds. Re-measure and correct the table — a coverage "
        f"figure nobody re-runs is a declaration with a date on it."
    )


def test_every_chore_is_measured():
    assert set(chores.VERIFIER_COVERAGE) == set(CASES), (
        "a chore with no measured verifier coverage cannot be gated"
    )


def test_widening_is_refused_where_the_ceiling_is_zero():
    """eps = 1 means P(fail) = q for every N. Not unproven — impossible."""
    blind = [c for c, e in chores.VERIFIER_COVERAGE.items() if e >= 1.0]
    assert blind, "the gate is pointless if nothing is blind"
    for chore in blind:
        with pytest.raises(TeeError) as caught:
            chores._run(
                "s",
                "p",
                refine="off",
                cfg=None,
                max_tokens=50,
                validate=lambda r: r,
                chore=chore,
                thinking=True,
            )
        assert caught.value.code == "llm_widening_refused"


def test_an_unmeasured_chore_is_blind_by_default():
    with pytest.raises(TeeError) as caught:
        chores._run(
            "s",
            "p",
            refine="off",
            cfg=None,
            max_tokens=50,
            validate=lambda r: r,
            chore="not_a_chore",
            thinking=True,
        )
    assert caught.value.code == "llm_widening_refused"


def test_a_ceiling_above_zero_is_permission_to_measure_not_a_benefit():
    seeing = [c for c, e in chores.VERIFIER_COVERAGE.items() if e < 1.0]
    assert seeing, "some verifier must see something"
    for chore in seeing:
        with pytest.raises(TeeError) as caught:
            chores._run(
                "s",
                "p",
                refine="off",
                cfg=None,
                max_tokens=50,
                validate=lambda r: r,
                chore=chore,
                thinking=True,
            )
        assert caught.value.code == "llm_widening_unproven"


def test_the_allow_set_cannot_contain_a_provably_useless_chore():
    for chore in chores.THINKING_ALLOWED:
        assert chores.widening_ceiling(chore) > 0.0, (
            f"{chore} is allow-listed for thinking but its verifier catches "
            f"nothing; no budget can help it"
        )


def test_thinking_off_is_never_gated():
    """The gate must cost the happy path nothing."""
    with pytest.raises(TeeError) as caught:
        chores._run(
            "s",
            "p",
            refine="local",
            cfg=None,
            max_tokens=50,
            validate=lambda r: r,
            chore="triage",
            thinking=False,
        )
    assert caught.value.code != "llm_widening_refused"


def test_a_blind_verifiers_acceptance_is_not_learned_from():
    """A learner fed labels uncorrelated with correctness gets confident, not right.

    `verified=True` means only that a chore's validate() accepted. For the
    chores measured at eps = 1.0 that is nearly always true and nearly
    uncorrelated with quality, so the row must be kept for latency and
    coverage but its success label withheld - the same treatment A76 gave an
    unreachable engine, and for the same reason.
    """
    from tee.learning import service as learning_service
    from tee.llm import router

    seen: list[dict] = []

    class Spy:
        def observe(self, **kw):
            seen.append(kw)

    blind = next(c for c, e in chores.VERIFIER_COVERAGE.items() if e >= 1.0)
    sighted = next(c for c, e in chores.VERIFIER_COVERAGE.items() if e < 1.0)

    for chore in (blind, sighted):
        router._observe_hop(
            Spy(),
            f"chore:{chore}",
            chore,
            lambda _c: None,
            {},
            "q14b+a2",
            "g1",
            True,
            12.0,
            version="v1",
        )

    by_chore = {row["context"]: row for row in seen}
    assert by_chore[f"chore:{blind}"]["success"] is None, (
        f"{blind} accepts every wrong answer; its acceptance is not a quality label"
    )
    assert by_chore[f"chore:{blind}"]["category"] == "unverifiable"
    assert by_chore[f"chore:{sighted}"]["success"] is True, (
        f"{sighted} catches some errors, so its verdict still carries information"
    )
    assert "unverifiable" in learning_service.UNLABELLED, (
        "the category must be unlabelled at the store too, not only at the caller"
    )


def test_every_category_the_router_emits_is_registered():
    """`observe()` is fail-open, so an unregistered category vanishes silently.

    Adding "unverifiable" to UNLABELLED without also adding it to CATEGORIES
    made `_validate` raise, `observe` swallow it, and the observation
    disappear - no error, no row, no signal. Telemetry that fails open loses
    data quietly, so the categories the router can emit are pinned here.
    """
    import ast
    from pathlib import Path

    from tee.learning.service import CATEGORIES

    src = Path(__file__).resolve().parents[1] / "src/tee/llm/router.py"
    emitted = {
        node.value
        for node in ast.walk(ast.parse(src.read_text()))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    # Only the ones actually passed as a category= argument matter; intersecting
    # with CATEGORIES' vocabulary keeps this from asserting on unrelated strings.
    known = {"completed", "skipped", "unreachable", "unverifiable", "unknown"} & emitted
    missing = known - CATEGORIES
    assert not missing, (
        f"router.py emits categories the learning store will reject and then "
        f"silently drop: {sorted(missing)}"
    )


def test_the_trap_suites_duty_cycle_is_declared_not_assumed():
    """A detector's coverage is its power TIMES its duty cycle.

    `test_llm_traps.py` is the only detector TEE has for the failure CLAUDE.md
    names as the #1 friction this project exists to fix - a model inventing an
    API instead of deferring. It works by grading DEFERRAL, so it needs no
    knowledge of the right fix, and it discriminated four models.

    But it carries `pytestmark = pytest.mark.llm`, and pyproject's addopts
    deselect `llm`. So its duty cycle in a default run is ZERO, and effective
    coverage is power x duty cycle = 0. By the standby-redundancy form
    P(fail) = (1-c)q + c*q^N, c = 0 leaves the floor at the full error rate q:
    the detector contributes nothing to any pipeline that does not invoke it
    explicitly with `-m llm`.

    That is not an argument for un-marking it - it needs a live endpoint, and a
    default suite must stay hermetic. It is an argument for the fact being
    WRITTEN DOWN next to every "6/6" claim, and for a cheap always-on check
    that the expensive detector still exists. This is that check: it costs
    nothing, runs every time, and fails if the trap suite is emptied, renamed
    or silently unmarked.
    """
    import re
    from pathlib import Path

    import fixtures_llm

    assert fixtures_llm.TRAPS and fixtures_llm.CONTROLS, (
        "the trap suite is the only detector for invented APIs; it must not be emptied"
    )
    assert len(fixtures_llm.CONTROLS) >= len(fixtures_llm.TRAPS) - 1, (
        "controls stop a model scoring well by always deferring; keep them balanced"
    )

    server = Path(__file__).resolve().parents[1]
    traps = (server / "tests/test_llm_traps.py").read_text()
    assert "pytest.mark.llm" in traps, "the marker is load-bearing; a live endpoint is needed"

    addopts = re.search(r"addopts\s*=\s*\"([^\"]+)\"", (server / "pyproject.toml").read_text())
    assert addopts and "not llm" in addopts.group(1), (
        "this test documents that the trap suite does NOT run by default. If that "
        "changed, the duty-cycle note in this docstring is now wrong - update it."
    )


def test_unlabelled_categories_are_all_registered():
    """The general form of the silent-drop trap, enforced at import.

    UNLABELLED and CATEGORIES were independent literals in learning/service.py,
    and `observe()` is fail-open: a category missing from CATEGORIES fails
    validation, the exception is swallowed, and the observation disappears with
    no error and no row. Adding "unverifiable" to UNLABELLED alone did exactly
    that. service.py now refuses to import in that state; this asserts the
    invariant holds and documents why it is a boot-time refusal rather than a
    warning - telemetry that fails open loses data quietly, so the check has to
    be somewhere it cannot be skipped.
    """
    from tee.learning.service import CATEGORIES, UNLABELLED

    assert UNLABELLED <= CATEGORIES, sorted(UNLABELLED - CATEGORIES)
    assert "unverifiable" in UNLABELLED and "unverifiable" in CATEGORIES
