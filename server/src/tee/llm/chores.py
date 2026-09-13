"""Chore templates over the local_llm seam (A34 M2).

The refine idiom (the as_photo_material pattern): every chore takes
refine='auto'|'local'|'off'. off -> None without a probe; auto -> run
when an endpoint answers, else None (the consumer's deterministic path
IS the degrade, visible because the chore's field simply never appears);
local -> required, absent endpoint raises the start-the-stack refusal.

Templates confine the model to evidence in-context (the A30 boundary,
sharpened for a code model): a fix that depends on an API name or
signature not present in the evidence must answer
confidence='needs_verification' and name what to check - inventing an
API is the exact failure TEE exists to kill, and the trap suite seeds
tracebacks to prove deferral.

Every result carries a provenance stamp: model 'tee-coder@<revision>'.
The revision names the TEMPLATE revision - bump it when any prompt or
schema here changes, so benchmark rows stay attributable.
"""

from __future__ import annotations

import ast
import re
import time
from collections import deque
from collections.abc import Mapping
from typing import Any

from tee.kernel import local_llm
from tee.kernel.errors import TeeError

# r1 intent clause; r2 kwarg-drift few-shot; r3 prompt diet (A38);
# r4 +phrase_deviation (A42 T4)
REVISION = "r4"
STAMP = f"tee-coder@{REVISION}"

_PROBE_TTL_S = 30.0

# W0: the last few reasoning traces, in memory, never on the wire. Bounded
# because deliberation is verbose by nature - the 27B produced 1,021 chars
# for a one-line diagnosis. This is the audit trail and the seed corpus for
# training an agent policy; it is deliberately NOT a client-facing surface.
_REASONING_LOG: deque[tuple[str, int, str]] = deque(maxlen=32)


def record_reasoning(profile: str | None, text: str) -> None:
    _REASONING_LOG.append((str(profile or "?"), len(text), text))


def reasoning_log() -> list[tuple[str, int, str]]:
    """Read the local reasoning trace (profile, chars, text)."""
    return list(_REASONING_LOG)


_probe_cache: dict[str, tuple[float, bool]] = {}

_BOUNDARY = (
    "Ground every claim only in the given evidence. If the answer depends "
    "on an API name, signature, or version not shown, say so instead of "
    "guessing - never invent an API."
)

_TRIAGE_SYSTEM = (
    "TEE's traceback-triage chore. From the failure evidence answer "
    'STRICT JSON {"diagnosis": <one line: what went wrong>, '
    '"fix": <one line: the exact change>, '
    '"confidence": "grounded"|"needs_verification"}. '
    "When the exact fix needs an API fact not in the evidence, use "
    "needs_verification and name what to check (docs, a live probe). "
    "A fix that drops what the code was trying to do (e.g. deleting an "
    "argument to silence the error) is not grounded - preserve intent "
    "or defer. " + _BOUNDARY + " "
    "Example - failure: TypeError: read_csv() got an unexpected keyword "
    "argument 'error_bad_lines' -> "
    '{"diagnosis": "This pandas version no longer accepts '
    '\'error_bad_lines\'.", "fix": "Verify the replacement parameter '
    "in the installed pandas docs, then update the call keeping the "
    'behavior.", "confidence": "needs_verification"} - the error names '
    "the old parameter, not its replacement."
)

_REPAIR_SYSTEM = (
    "TEE's script-repair chore. tee_script runs a restricted Python "
    "subset: assignments, if/for, comprehensions, f-strings; helpers "
    "call/batch/summary/detail/diff and len/sum/min/max/sorted/range/"
    "enumerate/zip/keys/items/get/append; NO import, while, def, "
    "lambda, try, or attribute access. Given the failing script and "
    "its validation error answer STRICT JSON "
    '{"repaired_code": <the corrected script>, '
    '"note": <one line on what changed>}. '
    "Change only what the error requires. " + _BOUNDARY
)

_LINT_SYSTEM = (
    "TEE's lint-explanation chore. The checker's finding is correct and "
    "final - never overrule or soften it. Answer STRICT JSON "
    '{"explanation": <ONE short sentence: the finding and the exact '
    "change>}. " + _BOUNDARY
)

_EXTRACT_SYSTEM = (
    "TEE's extract-refinement chore. Select the sentences of the text "
    "that answer the question. Answer STRICT JSON "
    '{"sentences": [<sentences copied VERBATIM from the text>]}. '
    "Copy exactly - never paraphrase or add words; only sentences that "
    "appear in the text."
)

_FACTS_SYSTEM = (
    "TEE's fact-structuring chore. Turn the text into typed facts: "
    'STRICT JSON {"facts": [{"kind": <dimension|material|constraint|'
    'preference|note>, "text": <one short fact>}]}. '
    "Only facts stated in the text; no inference, no invented names."
)

_RECAP_SYSTEM = (
    "TEE's recap-compression chore. Rewrite the JSON recap as one dense "
    'line a model can resume from: STRICT JSON {"summary": <one line, '
    "news only, no filler>}."
)

_RERANK_SYSTEM = (
    "TEE's kb-rerank chore. Order the candidate ids by how well each "
    'answers the query: STRICT JSON {"order": [<ids, best first>]}. '
    "Use every given id exactly once."
)

_DEVIATION_SYSTEM = (
    "TEE's deviation-phrasing chore. Turn each as-built deviation fact "
    "into ONE plain sentence a builder reads on site: STRICT JSON "
    '{"lines": [<one sentence per fact, same order>]}. Every number and '
    "unit from the fact must appear VERBATIM in its sentence; never "
    "round, convert, or invent values. " + _BOUNDARY
)


def _endpoint(cfg: dict[str, Any] | None) -> tuple[str, str, str | None]:
    """The active switch profile's endpoint (A37 P0-S); absent profile keys
    inherit [llm] config and its env defaults, so a profile-less setup
    behaves exactly as before."""
    from tee.llm import profiles

    resolved = profiles.resolve(cfg)
    return resolved["url"], resolved["model"], resolved["adapters"]


def _ready(refine: str, url: str, model: str | None = None) -> bool:
    """The refine gate. False means: use the deterministic path.

    Probed per (endpoint, model): an endpoint that answers while serving
    some OTHER model group is not this chore's engine, and pretending it
    is turns a clean degrade into a 400 mid-chore."""
    if refine == "off":
        return False
    now = time.monotonic()
    key = f"{url}|{model or ''}"
    stamp = _probe_cache.get(key)
    if stamp is None or now - stamp[0] > _PROBE_TTL_S:
        _probe_cache[key] = (now, local_llm.available(url=url, model=model))
    alive = _probe_cache[key][1]
    if refine == "local" and not alive:
        raise TeeError(
            "llm_unreachable",
            f"refine='local' but no local model answers at {url}.",
            fix=local_llm._UNREACHABLE_FIX,
        )
    return alive


def _run(
    system: str,
    prompt: str,
    *,
    refine: str,
    cfg: dict[str, Any] | None,
    max_tokens: int,
    validate,
    chore: str | None = None,
    thinking: bool | None = None,
    _measure_exact_budget: bool = False,
) -> dict[str, Any] | None:
    """Shared chore body: gate, complete, validate, stamp - or None."""
    if thinking:
        # Two evidential conditions. NEITHER is a proof of impossibility - see
        # the COVERAGE note above, corrected 2026-09-13 after external review.
        # The first says a verifier-driven retry has nothing to trigger on
        # here; the second says nothing has yet measured a benefit.
        ceiling = widening_ceiling(chore or "")
        seeds = COVERAGE_SEEDS.get(chore or "", 0)
        if ceiling <= 0.0:
            raise TeeError(
                "llm_widening_refused",
                f"{chore or 'this chore'} has no measured verifier signal to retry on: "
                f"its validator accepted all {seeds} seeded wrong answers, so a retry "
                f"driven by that validator has nothing to trigger on. This is coverage "
                f"of the seeded fault set, not a bound on what other methods could do.",
                fix="Strengthen the verifier and re-measure with "
                "test_a85_verifier_coverage.py, or bring a before/after row on task "
                "correctness that does not depend on this validator.",
            )
        if chore not in THINKING_ALLOWED:
            raise TeeError(
                "llm_widening_unproven",
                f"{chore} left {ceiling:.0%} of its {seeds} seeded faults detectable, but "
                f"no measurement shows thinking helps it. Permission to measure is not "
                f"evidence of benefit.",
                fix="Commit a before/after row on independently judged task correctness "
                "and cost, then add the chore to chores.THINKING_ALLOWED.",
            )
    if refine not in ("auto", "local", "off"):
        raise TeeError(
            "llm_bad_arg", f"refine='{refine}' is not a mode.", fix="Use auto, local, or off."
        )
    from tee.kernel import machine
    from tee.llm import profiles

    resolved = profiles.resolve(cfg)
    if not resolved["ready"]:
        # A managed switch is mid-load: answer at once, never hang (P0-S 2b).
        if refine == "local":
            raise TeeError(
                "llm_loading",
                profiles.loading_line(resolved),
                fix="Retry shortly, or type TEE/Q14B to switch back.",
            )
        return None
    url, model, adapters = resolved["url"], resolved["model"], resolved["adapters"]
    if resolved.get("paid"):
        # A43 (research 63 #4): a paid engine is still an EXIT. "Owner-
        # configured" does not mean "not an egress" - this content leaves
        # the machine and bills, so it needs the capability, and a tainted
        # task may not reach it at all.
        from tee.kernel import trust, trustctx

        grants = (cfg or {}).get("_grants") or trust.Grants()
        decision = trust.check(
            "call-paid-engine",
            caller=trustctx.caller(),
            grants=grants,
            taint=trustctx.taint(),
            consent=bool((cfg or {}).get("_consent")),
        )
        if not decision.allowed:
            if refine == "local":
                decision.raise_if_denied(f"chore on '{resolved['profile']}'")
            return None  # auto mode degrades to the deterministic path
    if not _ready(refine, url, model):
        return None

    # A45 P1: meter every engine call - free ones too, so a local-only
    # session can show a clean zero rather than an absent column (SI-B18).
    def _meter(payload, bytes_sent, seconds):
        from tee.kernel import spend

        u = spend.usage_from_payload(payload)
        spend.record(
            spend.PaidCall(
                profile=str(resolved.get("profile") or "?"),
                endpoint=spend.endpoint_of(url),
                model=str(model or "?"),
                paid=bool(resolved.get("paid")),
                bytes_sent=bytes_sent,
                seconds=seconds,
                price_in_per_mtok=resolved.get("price_in_per_mtok"),
                price_out_per_mtok=resolved.get("price_out_per_mtok"),
                currency=resolved.get("currency"),
                price_source=resolved.get("price_source"),
                **u,
            )
        )

    # A46 P3a. Every local engine on this machine is a REASONING model: it
    # spends output budget thinking before it answers. Measured 2026-08-31
    # on one snake_case rename at temperature 0 - at 64 tokens q27b returns
    # content="" with the text stranded in `reasoning_content`, and dsflash
    # emits its scratchpad as the answer; at 256 both answer cleanly. The
    # chores here asked for 160-220, i.e. under the floor, so a correct
    # engine looked like a model that answered badly. Raise, never lower:
    # a caller asking for MORE room knows something we do not.
    # Per-engine, not global: Qwen3.6-35B needs 1024 where dsflash needs
    # 256, because its reasoning pass alone is ~974 tokens. A shared floor
    # would have handed the 35B an empty answer on every chore.
    from tee.engines.table import matching_floors

    # ONE effective mode, used for the floor lookup and the wire below. The
    # gate above has already refused a request this chore may not make, so
    # this is exactly what the request carries.
    mode = wire_thinking(chore, requested=thinking, resolved=resolved)
    measured = matching_floors((cfg or {}).get("_state_dir"), resolved, thinking=mode)
    budget = max(int(max_tokens), machine.min_chore_tokens(resolved.get("profile"), measured))
    if _measure_exact_budget:
        # Only eng_audition's internal sweep requests this. Public chores keep
        # the floor; a floor measurement must send the rung it says it tested.
        budget = int(max_tokens)

    # W0: reasoning is a SIDE CHANNEL. It is recorded for audit and as the
    # training corpus, and never travels back to the client - which is what
    # makes a thinking engine free in tokens-per-task.
    thought: list[str] = []

    try:
        with profiles.REQUEST_LOCK:  # a managed stop waits for this chore
            raw = local_llm.complete_json(
                prompt,
                system=system,
                url=url,
                model=model,
                max_tokens=budget,
                adapters=adapters,
                # Chores default thinking OFF and must OPT IN, even on a
                # profile that declares thinking. Inheriting the profile's
                # flag was the wrong way round: measured 2026-09-13, thinking
                # costs 2.8-4.0x, is indistinguishable on the three chores
                # with real verifiers (8/8 either way), and is WORSE on the
                # one calibration chore (6/6 -> 5/6). Zero chores are
                # measured to benefit, so zero chores get it by default. The
                # profile's flag still declares the ENGINE's capability, for
                # callers outside the chore layer - see wire_thinking, which
                # is the only place that difference is resolved.
                thinking=mode,
                json_mode=str(resolved.get("json_mode") or "auto"),
                on_usage=_meter,
                on_reasoning=thought.append,
            )
    except TeeError:
        if refine == "local":
            raise
        _probe_cache.pop(f"{url}|{model or ''}", None)  # a dead engine re-probes next time
        return None
    if resolved.get("paid"):
        from tee.kernel import trustctx

        trustctx.add_taint(f"call-paid-engine:{resolved['profile']}")
    result = validate(raw)
    if result is None and refine == "local":
        raise TeeError(
            "llm_bad_shape",
            "The local model returned JSON outside the chore schema.",
            fix="A stronger TEE_LOCAL_LLM_MODEL helps; the deterministic path still works.",
        )
    if result is not None:
        result["model"] = STAMP
        if thought:
            # The TEXT goes to the local ring buffer; only its LENGTH rides
            # the wire. Putting the reasoning in `result` would ship it to
            # the client and undo the entire point of a thinking engine.
            record_reasoning(resolved.get("profile"), thought[0])
            result["reasoning_chars"] = len(thought[0])
    return result


# A short string constant in tee_script source is an op field or an entity
# name - "op", "create", "rotation", "Plate" - not prose. Intent lives in
# those as much as in identifiers, because the lane vocabulary is expressed as
# dict keys rather than kwargs. Longer strings are content and are ignored.
_TOKEN_STR_MAX = 40


def _identifiers(tree: ast.AST) -> set[str]:
    """Intent-bearing tokens: names, attributes, kwarg labels, short strings.

    Short string constants are included because tee_script writes its
    operations as dicts - `{'op': 'create', 'rotation': 0}` - so dropping a
    field is invisible to a check that only walks identifiers. That is exactly
    how a deletion-based repair slipped through the first version of this.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            found.add(node.arg)
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and 0 < len(node.value) <= _TOKEN_STR_MAX
        ):
            found.add(node.value)
    return found


def _error_tokens(error: str) -> set[str]:
    """Identifier-like tokens the supplied error evidence actually names.

    This is the contract a repair is allowed to cite. It is deliberately the
    RAW error text and nothing else: a rename is licensed by evidence the
    caller supplied, never by the model's own say-so.
    """
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", error or ""))


def _line(value: Any, limit: int) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return " ".join(value.split())[:limit]


# -- chore 1: traceback triage (the flagship) --------------------------------


def triage(
    failure: str,
    context: str = "",
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Failure text (+optional source/op context) -> one-line diagnosis +
    exact fix, or an explicit defer-to-verification."""

    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        diagnosis = _line(raw.get("diagnosis"), 220)
        fix = _line(raw.get("fix"), 300)
        confidence = raw.get("confidence")
        if not diagnosis or not fix or confidence not in ("grounded", "needs_verification"):
            return None
        return {"diagnosis": diagnosis, "fix": fix, "confidence": confidence}

    evidence = f"Failure evidence:\n{failure[:6000]}"
    if context:
        evidence += f"\n\nContext (source/op):\n{context[:2000]}"
    # MEASURED 2026-09-13, 27B on :8087 with this exact system prompt:
    # thinking ON scores 5/6, thinking OFF scores 6/6. The one failure is
    # kwarg_drift answered 'grounded' - an API fact asserted from weights,
    # the precise thing the A30 boundary forbids and the trap exists to
    # catch. Room to reason turned appropriate uncertainty into rationalised
    # certainty, and deferral IS the calibration this chore is for. So
    # triage pins thinking off whatever the profile says: the boundary
    # outranks the engine's default.
    return _run(
        _TRIAGE_SYSTEM,
        evidence,
        refine=refine,
        cfg=cfg,
        max_tokens=220,
        validate=validate,
        thinking=False,
    )


# -- chore 2: script repair draft --------------------------------------------


def repair_script(
    code: str,
    error: str,
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        repaired = raw.get("repaired_code")
        note = _line(raw.get("note"), 200)
        if not isinstance(repaired, str) or not repaired.strip() or not note:
            return None
        if len(repaired) > 4 * max(len(code), 200):  # a draft, not an essay
            return None
        # Measured 2026-09-13: with only the checks above this validator had a
        # false-accept rate of 100% - it waved through a deletion-based repair,
        # a bare `pass`, and wholly unrelated code. Its own system prompt names
        # "deleting an argument to silence the error" as the failure mode, and
        # nothing stopped it. Three deterministic checks, no execution:
        from tee.kernel.script import validate_script

        try:
            tree = validate_script(repaired)
        except TeeError:
            return None  # must parse and stay inside the script subset
        if not any(isinstance(n, (ast.Call, ast.Assign, ast.AugAssign)) for n in ast.walk(tree)):
            return None  # a stub that does nothing is not a repair
        # INTENT PRESERVATION. A correct repair may RENAME what broke, but it
        # may not simply drop it. A lost token must therefore be explained by
        # ONE of two things:
        #
        #   (a) a surviving token it overlaps - rotation -> rotation_euler; or
        #   (b) the supplied error evidence, which is the only contract the
        #       chore is given. A spelling repair has no overlap at all
        #       (tee_sttaus -> tee_status share no substring relation), so
        #       rule (a) alone rejected correct, evidence-backed renames.
        #       Found by review, 2026-09-13.
        #
        # (b) is deliberately narrow: the error must name BOTH the token being
        # dropped and at least one token the repair introduces. A deletion
        # introduces nothing, so it stays rejected however loudly the error
        # names the field it deleted - which is what keeps the degenerate fix
        # out.
        #
        # BLIND SPOT, stated rather than papered over: this cannot PAIR a
        # dropped token with its replacement. An error naming several
        # identifiers licenses a repair that renames one of them and quietly
        # drops another. Neither rule is a proof of preserved intent; both are
        # cheap necessary conditions. Semantic correctness is not established
        # here - only that the draft parses and did not silence the error by
        # deletion.
        try:
            before = _identifiers(ast.parse(code))
        except SyntaxError:
            before = set()  # the input was not parseable; nothing to preserve
        after = _identifiers(tree)
        evidence = _error_tokens(error)
        licensed = bool((after - before) & evidence)
        for lost in before - after:
            if any(lost in keep or keep in lost for keep in after):
                continue
            if licensed and lost in evidence:
                continue
            return None
        return {"repaired_code": repaired, "note": note}

    prompt = f"Failing script:\n```\n{code[:4000]}\n```\nValidation error:\n{error[:1000]}"
    return _run(_REPAIR_SYSTEM, prompt, refine=refine, cfg=cfg, max_tokens=500, validate=validate)


# -- chore 3: lint explanation (checkers stay the judges) --------------------


def explain_lint(
    finding: str,
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        explanation = _line(raw.get("explanation"), 260)
        return {"explanation": explanation} if explanation else None

    return _run(
        _LINT_SYSTEM,
        f"Finding:\n{finding[:2000]}",
        refine=refine,
        cfg=cfg,
        max_tokens=160,
        validate=validate,
    )


# -- chore 4: extract refinement, extractive by verification -----------------

_WS = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def refine_extract(
    text: str,
    question: str,
    max_tokens: int,
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Question-focused sentence selection with the extractive guarantee:
    every emitted sentence must appear (near-)verbatim in the source, else
    the whole chore abstains and the dumb-parser path stands (research 50
    chore 1 - a string check, cheap, absolute)."""

    haystack = _normalize(text)

    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        sentences = raw.get("sentences")
        if not isinstance(sentences, list):
            return None
        if not sentences:
            # A well-formed empty selection is honest abstention ("nothing
            # here answers this"), not a schema failure - even under
            # refine='local' the dumb path stands.
            return {"quote": ""}
        kept: list[str] = []
        for sentence in sentences:
            if not isinstance(sentence, str) or not sentence.strip():
                return None
            if _normalize(sentence) not in haystack:
                return None  # one invented sentence poisons the lot
            kept.append(" ".join(sentence.split()))
        quote = "\n".join(kept)
        if len(quote) > max_tokens * 5:  # budget discipline survives refinement
            return None
        return {"quote": quote}

    prompt = (
        f"Question: {question}\n\nText:\n{text[:12000]}\n\n"
        f"Select the sentences (verbatim) that answer the question, "
        f"within about {max_tokens} tokens."
    )
    result = _run(
        _EXTRACT_SYSTEM,
        prompt,
        refine=refine,
        cfg=cfg,
        max_tokens=min(2 * max_tokens, 1200),
        validate=validate,
    )
    if result is not None and not result["quote"]:
        return None  # abstained - the consumer's dumb path stands
    return result


# -- chores 5-7: fact structuring, recap compression, kb rerank --------------

_FACT_KINDS = {"dimension", "material", "constraint", "preference", "note"}

# -- verifier coverage, and the threshold it implies ------------------------
#
# MEASURED 2026-09-13 by fault injection (tests/test_a85_verifier_coverage.py):
# seeded plausible-but-wrong answers fed through each real chore, counting how
# many its validator ACCEPTS. Every chore also passes a true-accept control, so
# a low number means "catches errors", not "rejects everything".
#
# eps = false-accept rate = the fraction of wrong answers the verifier waves
# through. Detector coverage is c = 1 - eps.
#
# WHAT A BLIND VERIFIER COSTS - a model, and what it does and does not license.
#
# Under standby redundancy with imperfect detection, an often-quoted form is
#
#     P(fail after N) = eps*q + (1 - eps)*q**N
#
# and its first term is a FLOOR: errors the verifier cannot see are never
# retried, because nothing knows to retry them. That qualitative shape is the
# quantum threshold theorem's, and it is the useful part - concatenating an
# unreliable check buys nothing above the threshold.
#
# CORRECTED 2026-09-13 (external review). That expression is ONE model with
# unstated assumptions, not the general failure probability of repeated
# attempts under imperfect detection, and it is not conservative. Read it as
# "retry while the verifier rejects, up to N attempts, and count a false
# accept or exhaustion as failure" and the recurrence is
#
#     F_N = q*eps + q*(1 - eps)*F_(N-1),   F_1 = q
#
# which at q = eps = 0.5, N = 3 gives 0.34375 where the expression above gives
# 0.3125. The asymptotic floors differ too: q*eps/(1 - q*(1 - eps)) = 0.333
# against eps*q = 0.25. The simple form UNDERSTATES the floor - it was
# optimistic about retries, not pessimistic. Correlated attempts need further
# assumptions again, and the measured rung correlations here are not zero
# (rho = 0.53 across families on 17 and 22 failures).
#
# So `widening_ceiling` is a DIAGNOSTIC, not a bound:
#
#     widening_ceiling(chore) = 1 - eps
#       an optimistic, model-dependent estimate of how much of this chore's
#       seeded error a verifier-driven retry could remove. At eps = 1.0 it is
#       zero, meaning the seeded faults were ALL accepted, so a retry driven
#       by THIS verifier had nothing to trigger on.
#
# Three things it does NOT establish, each of which the refusals below used to
# assert and no longer do:
#
#   1. eps is not a population property. It is the false-accept fraction over
#      the seeded fault set recorded in COVERAGE_SEEDS - a different or larger
#      set moves it in either direction, and adding wrong answers the verifier
#      DOES reject lowers it.
#   2. A blind verifier does not prove that thinking cannot lower per-attempt
#      error q. A retry policy driven by a validator and a different
#      generation policy are different interventions; this measures only the
#      first.
#   3. A ceiling above zero is permission to MEASURE, never evidence of
#      benefit - and it is void if the widening itself raises q, which
#      thinking did on triage (traps 6/6 bare, 5/6 thinking).
#
# The gate below is therefore an EMPIRICAL ADOPTION GATE: thinking stays off
# until a committed before/after row shows a gain on independently judged task
# correctness at acceptable cost. A finite measurement can justify declining
# adoption without proving universal uselessness, and that is all it claims.

# How many seeded faults produced each figure in VERIFIER_COVERAGE. A bare
# fraction reads as a property of the chore; with its denominator it reads as
# what it is - coverage of a stated fault set at a stated sample size.
# test_w0_review_corrections.py fails on a coverage figure with no count.
COVERAGE_SEEDS: dict[str, int] = {
    "phrase_deviation": 4,
    "refine_extract": 3,
    "structure_facts": 3,
    "rerank": 3,
    "triage": 3,
    "repair_script": 5,
    "explain_lint": 3,
    "compress_recap": 3,
}

VERIFIER_COVERAGE: dict[str, float] = {
    # eps      chore              what the validator actually binds
    "phrase_deviation": 0.25,  # numerals survive per line; not their attachment
    "refine_extract": 0.33,  # sentences appear in the source; not relevance
    "structure_facts": 0.67,  # kind is in the enum; text is unchecked
    "rerank": 0.67,  # a permutation of the ids; not the ORDER, which is the job
    "triage": 1.00,  # non-empty strings + a legal enum
    # Was 1.00 until 2026-09-13, when its only correctness-adjacent gate was an
    # UPPER length bound and a deletion-based repair - the exact degenerate fix
    # its own system prompt warns about - shipped to the client. Now: must
    # parse under validate_script, must contain a call or assignment, and every
    # intent-bearing token the original had must survive, be echoed by a
    # rename, or be licensed by the supplied error evidence. What remains
    # uncaught is a repair that keeps every token and changes a VALUE, which is
    # why this is not 0.
    #
    # 0.25 over 4 seeds until the review round added a fifth (an argument
    # discarded that the error never named, which the validator rejects). The
    # figure MOVED, 0.25 -> 0.20, on a fault set that grew by one - which is
    # the clearest possible demonstration that eps is coverage of a stated set
    # and not a property of the chore.
    "repair_script": 0.20,
    "explain_lint": 1.00,  # one non-empty line
    "compress_recap": 1.00,  # one non-empty line
}


# Chores permitted to opt into thinking. SHIPS EMPTY, on purpose.
#
# THE ADOPTION GATE. A ceiling above zero is permission to MEASURE, not
# evidence of benefit, and nothing has yet measured a benefit: across every
# chore tested on 2026-09-13, thinking was one measured harm (triage, traps
# 6/6 -> 5/6), three measured no-ops at 2.8-4.0x cost, and zero measured
# gains. Those are finite results on small samples; they justify DECLINING
# adoption, and they do not prove thinking is useless here.
#
# Adding a name requires all three:
#   - a committed before/after row on independently judged task correctness,
#     not on validator acceptance (the validator is what eps says is blind);
#   - the cost delta, measured, and a stated regression criterion;
#   - a ceiling above zero.
# test_a85_verifier_coverage.py enforces the last and will fail on a name that
# cannot pass the first two.
THINKING_ALLOWED: frozenset[str] = frozenset()


def wire_thinking(
    chore: str | None, *, requested: bool | None, resolved: Mapping[str, Any]
) -> bool:
    """The thinking flag this request will ACTUALLY put on the wire.

    Engine capability is not request mode. A profile's `thinking` says the
    endpoint CAN deliberate; it never says this call will ask it to. Chores
    default off and opt in, so a chore on `q27b-think` still sends thinking
    off unless it asked.

    Everything that records or looks up a measurement must agree on this one
    value. It was measured on the wire mode and mislabelled with the profile
    capability, so `q27b-think` filed every floor it measured under an
    identity no request it makes ever has, and discarded them all. Found by
    review, 2026-09-13.
    """
    return bool(requested) and bool(resolved.get("thinking"))


def widening_ceiling(chore: str) -> float:
    """1 - eps: an optimistic, model-dependent estimate, not a bound.

    How much of this chore's SEEDED error a verifier-driven retry might
    remove. It is not a population bound, and it says nothing about
    interventions that change per-attempt error rather than retry on
    rejection - see the COVERAGE note above.

    Unknown chores return 0.0 - an unmeasured verifier is treated as blind,
    so a new chore cannot inherit permission it never earned.
    """
    return max(0.0, 1.0 - VERIFIER_COVERAGE.get(chore, 1.0))


# rerank ranks at most this many candidates. The prompt listing and the
# permutation the validator demands MUST derive from the same slice - see
# rerank's docstring for the bug that taught this.
RERANK_MAX = 20


def structure_facts(
    text: str,
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        facts = raw.get("facts")
        if not isinstance(facts, list) or not facts:
            return None
        out = []
        for fact in facts:
            if not isinstance(fact, dict) or fact.get("kind") not in _FACT_KINDS:
                return None
            line = _line(fact.get("text"), 200)
            if not line:
                return None
            out.append({"kind": fact["kind"], "text": line})
        return {"facts": out}

    return _run(
        _FACTS_SYSTEM,
        f"Text:\n{text[:8000]}",
        refine=refine,
        cfg=cfg,
        max_tokens=500,
        validate=validate,
    )


def compress_recap(
    recap: dict[str, Any] | str,
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        summary = _line(raw.get("summary"), 400)
        return {"summary": summary} if summary else None

    return _run(
        _RECAP_SYSTEM,
        f"Recap JSON:\n{str(recap)[:6000]}",
        refine=refine,
        cfg=cfg,
        max_tokens=160,
        validate=validate,
    )


def rerank(
    query: str,
    candidates: list[dict[str, str]],
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """candidates: [{id, title}] -> {"order": [ids]} - a permutation or
    nothing (a rerank that loses or invents ids is worse than none).

    Only the first RERANK_MAX candidates are ranked, and the contract is over
    exactly those. Before 2026-09-13 `ids` was built from ALL candidates while
    the prompt listed only the first 20, so with 21+ inputs the model was
    required to return ids it had never been shown and failed deterministically
    with llm_bad_shape - a truncation bug wearing a capability limit's clothes.
    The output budget agrees with the cap: 64 ids do not fit in max_tokens=160.
    """
    considered = candidates[:RERANK_MAX]
    ids = [c["id"] for c in considered]

    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        order = raw.get("order")
        if not isinstance(order, list) or sorted(map(str, order)) != sorted(ids):
            return None
        return {"order": [str(i) for i in order]}

    listing = "\n".join(f"- {c['id']}: {c.get('title', '')}" for c in considered)
    return _run(
        _RERANK_SYSTEM,
        f"Query: {query}\nCandidates:\n{listing}",
        refine=refine,
        cfg=cfg,
        max_tokens=200,
        validate=validate,
    )


def phrase_deviation(
    facts: list[str],
    *,
    refine: str = "auto",
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Deviation facts -> one builder-readable sentence each, with the
    extractive-numbers guarantee: every number in a fact must survive
    VERBATIM in its sentence or the whole result is discarded - the
    deterministic fact line stands (the lane never waits on a model)."""

    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        lines = raw.get("lines")
        if not isinstance(lines, list) or len(lines) != len(facts):
            return None
        phrased: list[str] = []
        for fact, line in zip(facts, lines, strict=True):
            sentence = _line(line, 240)
            if not sentence:
                return None
            for number in re.findall(r"-?\d+(?:\.\d+)?", fact):
                if number not in sentence:
                    return None
            phrased.append(sentence)
        return {"lines": phrased}

    listing = "\n".join(f"- {fact[:300]}" for fact in facts[:12])
    return _run(
        _DEVIATION_SYSTEM,
        f"Facts:\n{listing}",
        refine=refine,
        cfg=cfg,
        max_tokens=400,
        validate=validate,
    )
