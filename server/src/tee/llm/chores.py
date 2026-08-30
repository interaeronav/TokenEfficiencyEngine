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

import re
import time
from typing import Any

from tee.kernel import local_llm
from tee.kernel.errors import TeeError

# r1 intent clause; r2 kwarg-drift few-shot; r3 prompt diet (A38);
# r4 +phrase_deviation (A42 T4)
REVISION = "r4"
STAMP = f"tee-coder@{REVISION}"

_PROBE_TTL_S = 30.0
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
) -> dict[str, Any] | None:
    """Shared chore body: gate, complete, validate, stamp - or None."""
    if refine not in ("auto", "local", "off"):
        raise TeeError(
            "llm_bad_arg", f"refine='{refine}' is not a mode.", fix="Use auto, local, or off."
        )
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

    try:
        with profiles.REQUEST_LOCK:  # a managed stop waits for this chore
            raw = local_llm.complete_json(
                prompt,
                system=system,
                url=url,
                model=model,
                max_tokens=max_tokens,
                adapters=adapters,
                on_usage=_meter,
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
            "The local model answered outside the chore schema twice.",
            fix="A stronger TEE_LOCAL_LLM_MODEL helps; the deterministic path still works.",
        )
    if result is not None:
        result["model"] = STAMP
    return result


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
    return _run(_TRIAGE_SYSTEM, evidence, refine=refine, cfg=cfg, max_tokens=220, validate=validate)


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
    nothing (a rerank that loses or invents ids is worse than none)."""
    ids = [c["id"] for c in candidates]

    def validate(raw: dict[str, Any]) -> dict[str, Any] | None:
        order = raw.get("order")
        if not isinstance(order, list) or sorted(map(str, order)) != sorted(ids):
            return None
        return {"order": [str(i) for i in order]}

    listing = "\n".join(f"- {c['id']}: {c.get('title', '')}" for c in candidates[:20])
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
