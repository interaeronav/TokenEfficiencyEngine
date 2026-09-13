"""The four findings of Codex's W0 review (2026-09-13), pinned as behaviour.

Each test fails on the defect as it was found. Together they say:

1. the committed candidate imports only committed source;
2. a repair the supplied evidence licenses is accepted, and every deletion
   control still fails;
3. a token floor is filed and found under the mode the WIRE carried, not the
   mode the profile declares;
4. thinking stays off by default, and the gate that keeps it off rests on
   measured coverage of a stated fault set - not on a claim of impossibility.
"""

from __future__ import annotations

import ast
import json
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest
from fixtures_llm import fake_llm_server

from tee.engines import audition, table
from tee.llm import chores, profiles

REPO = Path(__file__).resolve().parents[2]


# -- 1. the candidate must be self-contained ---------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout


def test_committed_source_imports_only_committed_source() -> None:
    """A committed module whose subject is untracked passes here and fails on a clone.

    `c306138` committed `test_blender_lessons.py` and `learning/service.py`
    while `adapters/blender/guidance.py` and `learning/model.py` stayed
    untracked. The dirty working tree supplied both, so the suite was green
    while a `git archive` of the same head could not collect - and
    `service.py`'s four call sites are LAZY imports, which no collection
    check would have caught even then. Only an inventory check sees this.

    It reads COMMITTED content, never the working tree: half this repo's
    tracked files carry other sessions' uncommitted edits, and those edits'
    imports are not the candidate's problem.
    """
    if not (REPO / ".git").exists():  # pragma: no cover - not a checkout
        pytest.skip("not a git checkout")
    tracked = set(_git("ls-files").split())
    dirty = {line[3:] for line in _git("status", "--porcelain").splitlines() if line[3:] in tracked}
    prefixes = {f"{rel[len('server/src/') : -3]}" for rel in tracked if rel.endswith(".py")}

    def resolves(module: str) -> bool:
        rel = module.replace(".", "/")
        if rel in prefixes or f"{rel}/__init__" in prefixes:
            return True
        # an implicit namespace package: no __init__, but tracked files inside
        return any(p.startswith(f"{rel}/") for p in prefixes)

    broken: list[str] = []
    for rel in sorted(tracked):
        # server/ and benchmarks/ are what `make lint` covers and what ships;
        # archived evidence under docs/ and output/ is a copy of a past run,
        # never imported and deliberately frozen.
        if not rel.endswith(".py") or not rel.startswith(("server/", "benchmarks/")):
            continue
        source = _git("show", f"HEAD:{rel}") if rel in dirty else (REPO / rel).read_text()
        try:
            tree = ast.parse(source)
        except SyntaxError:  # pragma: no cover - unparseable committed file
            continue
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                modules.add(node.module)
                modules.update(f"{node.module}.{a.name}" for a in node.names)
        for module in sorted(modules):
            # `from tee.x import name` adds tee.x.name, which is usually a
            # symbol rather than a submodule; only flag it if nothing tracked
            # supplies the PARENT either, or if an untracked file does supply
            # it as a module - the shape that actually breaks a clone.
            if not module.startswith("tee.") or resolves(module):
                continue
            parent = module.rsplit(".", 1)[0]
            if (
                resolves(parent)
                and not (REPO / f"server/src/{module.replace('.', '/')}.py").exists()
            ):
                continue  # a name inside a tracked module, not a submodule
            broken.append(f"{rel} imports {module}")
    assert not broken, "committed source depends on work that is not committed:\n  " + "\n  ".join(
        broken
    )


# -- 2. evidence-backed renames ----------------------------------------------


def _repair_verdict(code: str, error: str, repaired: str) -> dict[str, Any] | None:
    """Run the REAL repair_script validator over one proposed repair."""
    seen: dict[str, Any] = {}

    def fake_run(system, prompt, *, refine, cfg, max_tokens, validate, **kw):
        seen["verdict"] = validate({"repaired_code": repaired, "note": "n"})
        return seen["verdict"]

    real, chores._run = chores._run, fake_run
    try:
        chores.repair_script(code, error)
    finally:
        chores._run = real
    return seen["verdict"]


_SCRIPT = "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate', 'rotation': 0}])"
_SCRIPT_ERR = "bad_op: unknown operation field 'rotation'"
_TYPO = 'result = call("tee_sttaus", {})'
_TYPO_ERR = "Unknown tool tee_sttaus; use tee_status"


def test_a_rename_the_error_evidence_licenses_is_accepted() -> None:
    """The case the substring rule could not express: a corrected spelling.

    `tee_sttaus` and `tee_status` have no substring relation in either
    direction, so intent preservation read the fix as a deletion.
    """
    assert _repair_verdict(_TYPO, _TYPO_ERR, 'result = call("tee_status", {})') is not None


@pytest.mark.parametrize(
    ("label", "code", "error", "repaired"),
    [
        (
            "deletes the field the error names",
            _SCRIPT,
            _SCRIPT_ERR,
            "batch([{'op': 'create', 'kind': 'cube', 'name': 'Plate'}])",
        ),
        ("a stub that does nothing", _SCRIPT, _SCRIPT_ERR, "pass"),
        ("wholly unrelated code", _SCRIPT, _SCRIPT_ERR, "summary()"),
        (
            "discards an argument the error never mentions",
            _SCRIPT,
            _SCRIPT_ERR,
            "batch([{'op': 'create', 'kind': 'cube', 'rotation': 0}])",
        ),
        (
            "renames as evidenced BUT drops a second field",
            'result = call("tee_sttaus", {"scope": "all"})',
            _TYPO_ERR,
            'result = call("tee_status", {})',
        ),
    ],
)
def test_deletion_controls_still_fail(label: str, code: str, error: str, repaired: str) -> None:
    assert _repair_verdict(code, error, repaired) is None, label


def test_evidence_is_the_supplied_error_and_not_the_models_say_so() -> None:
    """The same rename, with the error text withheld, is refused.

    Rule (b) is a licence granted by the CALLER's evidence. Without it the
    only remaining rule is substring overlap, which this repair does not
    satisfy - so the acceptance above cannot be reused as a general escape.
    """
    assert _repair_verdict(_TYPO, "", 'result = call("tee_status", {})') is None


# -- 3. floors bind to the mode actually executed -----------------------------


def _profile_cfg(url: str, state_dir: Path, *, thinking: bool) -> dict[str, Any]:
    return {
        "_profile": "cand",
        "_state_dir": str(state_dir),
        "profiles": {
            "cand": {
                "url": url,
                "model": "fake-27b",
                "adapters": "",
                "thinking": thinking,
                "json_mode": "off",
            }
        },
    }


def test_capability_is_not_request_mode() -> None:
    """A thinking-capable profile still sends thinking off unless asked."""
    capable = {"thinking": True}
    assert chores.wire_thinking("triage", requested=None, resolved=capable) is False
    assert chores.wire_thinking("triage", requested=False, resolved=capable) is False
    assert chores.wire_thinking("triage", requested=True, resolved=capable) is True
    # and asking cannot conjure a capability the engine does not have
    assert chores.wire_thinking("triage", requested=True, resolved={"thinking": False}) is False


def test_a_chore_on_a_thinking_profile_sends_thinking_off_on_the_wire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Assert the OUTBOUND flag, not the configuration value.

    `q27b-think` declares thinking; its chores do not ask for it. The wire is
    the only place that difference is observable.
    """
    chores._probe_cache.clear()
    reply = json.dumps({"explanation": "one line"})
    with fake_llm_server([reply], models=("fake-27b",)) as (url, calls):
        cfg = _profile_cfg(url, tmp_path, thinking=True)
        assert profiles.resolve(cfg)["thinking"] is True  # the CAPABILITY is on
        assert chores.explain_lint("a finding", refine="local", cfg=cfg)
    posts = [c for c in calls if "messages" in c]
    assert posts, "the chore never reached the endpoint"
    assert posts[-1]["chat_template_kwargs"]["enable_thinking"] is False


def test_an_audition_row_records_the_mode_it_measured_and_a_chore_consumes_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole loop: measure -> persist -> match -> raise a real chore's budget.

    Before the fix `audition()` omitted `thinking`, `matching_floors` read the
    missing key as False and compared it against the profile's True, so
    `q27b-think` discarded every floor it had just measured and no production
    chore ever saw one.
    """
    chores._probe_cache.clear()
    monkeypatch.setitem(table.ENGINES, "cand-engine", {"profile": "cand"})
    triage = json.dumps({"diagnosis": "d", "fix": "f", "confidence": "needs_verification"})

    # (a) MEASURE - a row produced by the real audition path
    with fake_llm_server([triage], models=("fake-27b",)) as (url, calls):
        cfg = _profile_cfg(url, tmp_path, thinking=True)
        row = audition.audition(cfg, engine="cand-engine", url=url, model="fake-27b", samples=1)
        measured_wire = [c for c in calls if "messages" in c][-1]["chat_template_kwargs"][
            "enable_thinking"
        ]

    assert "thinking" in row, "the row must record the mode it was measured at"
    assert row["thinking"] == measured_wire, "the row must not mislabel its own measurement"

    # (b) PERSIST it as an exact-wire floor, exactly as the sweep would
    floor = 768
    table.save_measured(
        tmp_path,
        {
            "cand-engine": {
                **row,
                "min_chore_tokens": floor,
                "floor": {"min_chore_tokens": floor, "budget_mode": "exact-wire"},
            }
        },
    )

    # (c) CONSUME - a real chore on the same profile must send that budget
    chores._probe_cache.clear()
    with fake_llm_server([json.dumps({"explanation": "x"})], models=("fake-27b",)) as (url2, c2):
        cfg2 = _profile_cfg(url2, tmp_path, thinking=True)
        # the floor was measured against the audition endpoint; re-point it so
        # only the MODE identity is under test here
        stored = table.load_measured(tmp_path)
        stored["cand-engine"]["url"] = url2
        table.save_measured(tmp_path, stored)
        assert chores.explain_lint("a finding", refine="local", cfg=cfg2)
        post = [c for c in c2 if "messages" in c][-1]

    assert post["max_tokens"] == floor, (
        f"the chore sent max_tokens={post['max_tokens']}, not the measured floor {floor} - "
        "the row it measured was filed under an identity the request never has"
    )
    assert post["chat_template_kwargs"]["enable_thinking"] is measured_wire


def test_a_floor_is_found_by_the_wire_mode_and_not_by_the_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same-mode matches; a genuinely different mode does not reuse the floor."""
    url = "http://local/v1"
    monkeypatch.setitem(table.ENGINES, "cand-engine", {"profile": "cand"})
    floor_row = {
        "url": url,
        "model": "fake-27b",
        "adapters": None,
        "thinking": False,  # measured with thinking OFF
        "measured_at": time.time(),
        "min_chore_tokens": 768,
        "floor": {"min_chore_tokens": 768, "budget_mode": "exact-wire"},
    }
    table.save_measured(tmp_path, {"cand-engine": floor_row})
    resolved = profiles.resolve(_profile_cfg(url, tmp_path, thinking=True))

    # the capability is True, but the request mode is what decides
    matched = table.matching_floors(tmp_path, resolved, thinking=False)
    assert matched["cand-engine"]["min_chore_tokens"] == 768, (
        "a chore running with thinking off must consume a floor measured with "
        "thinking off, even on a profile that declares thinking"
    )
    assert table.matching_floors(tmp_path, resolved, thinking=True) == {}, (
        "a thinking request must NOT reuse a floor measured without thinking"
    )


def test_matching_floors_refuses_to_guess_the_mode() -> None:
    """No default: the caller must state the mode it is asking about."""
    with pytest.raises(TypeError):
        table.matching_floors(None, {})  # type: ignore[call-arg]


# -- 4. the gate rests on measured coverage, not on impossibility -------------


def test_thinking_ships_disabled_for_every_chore() -> None:
    assert frozenset() == chores.THINKING_ALLOWED


def test_coverage_is_recorded_with_its_sample_count() -> None:
    """eps is a measurement of a stated fault set, so the set must be stated.

    A bare fraction reads as a population property. Every chore with a
    coverage figure must say how many seeded faults produced it.
    """
    for chore, eps in chores.VERIFIER_COVERAGE.items():
        seeds = chores.COVERAGE_SEEDS.get(chore)
        assert isinstance(seeds, int) and seeds > 0, f"{chore} has eps={eps} and no sample count"


def test_the_refusal_does_not_claim_a_universal_impossibility() -> None:
    """The gate may cite what it measured; it may not claim what cannot exist.

    `eps*q + (1-eps)*q**N` is one model with unstated assumptions. Under the
    retry-until-N reading the recurrence gives 0.34375 at q = eps = 0.5,
    N = 3, where that expression gives 0.3125 - and understates the floor. A
    seeded false-accept fraction also cannot prove that a different
    generation policy leaves per-attempt error unchanged.
    """
    blind = next(c for c, e in chores.VERIFIER_COVERAGE.items() if e >= 1.0)
    assert chores.widening_ceiling(blind) == 0.0
    with pytest.raises(Exception) as caught:
        chores._run(
            "s",
            "p",
            refine="local",
            cfg=None,
            max_tokens=64,
            validate=lambda raw: raw,
            chore=blind,
            thinking=True,
        )
    message = str(getattr(caught.value, "message", caught.value)).lower()
    assert "seeded" in message or "measured" in message, (
        "the refusal must cite the measurement it rests on"
    )
    for overclaim in ("cannot improve", "at any budget", "provably useless", "impossible"):
        assert overclaim not in message, f"refusal still claims universality: {overclaim!r}"


def test_a_surviving_positive_label_is_schema_acceptance_not_correctness() -> None:
    """The learner is fed validator acceptance. Say so, and keep it bounded.

    The router withholds positives only where the verifier is fully blind. The
    positives that survive still carry that chore's measured false-accept
    fraction - they are not correctness labels, and nothing downstream may
    treat them as such. This pins the two facts that claim depends on.
    """
    from tee.llm.chores import VERIFIER_COVERAGE, widening_ceiling

    blind = {c for c, e in VERIFIER_COVERAGE.items() if e >= 1.0}
    assert blind, "the guard is pointless if no verifier is blind"
    for chore in blind:
        assert widening_ceiling(chore) <= 0.0, f"{chore} must have its positives withheld"

    sighted = {c: e for c, e in VERIFIER_COVERAGE.items() if 0.0 < e < 1.0}
    assert sighted, (
        "if no chore is partially sighted the residual note in router._observe_hop "
        "is stale and should be removed"
    )
    for chore, eps in sighted.items():
        assert widening_ceiling(chore) > 0.0, (
            f"{chore} keeps its positive labels while accepting {eps:.0%} of its "
            "seeded wrong answers - that residual must stay documented"
        )
