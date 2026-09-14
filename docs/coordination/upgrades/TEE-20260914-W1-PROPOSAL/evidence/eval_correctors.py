"""Evaluate deterministic correctors offline, on the stored answers.

No model calls: a syndrome is a function of (evidence, answer), so the study
runs once and every candidate corrector is free to score. Fitted on the TUNE
half, reported on the SCORE half.

Statistics, stated before looking: paired binary outcomes, so the effect lives
entirely in the discordant pairs.

    b = baseline wrong, corrected right      (true catches)
    c = baseline right, corrected wrong      (false rejects)

Under no effect b ~ Binomial(b+c, 1/2). A Clopper-Pearson lower bound on
p = b/(b+c) gives a conservative lower one-sided 95% bound on the paired
improvement, (2*p_lo - 1) * (b+c) / n. Positive means the corrector helped by
more than chance on held-out records; the W1 gate policy accepts nothing less.
"""
import json, math, re, sys
from pathlib import Path

RAW = Path("/Users/john/tee-w1-candidate/w1-lab/wide-study-raw.json")
sys.path.insert(0, "/Users/john/tee-w1-candidate/server/src")
from tee.llm import syndrome as S


# -- correctors --------------------------------------------------------------

_REMOVE = re.compile(r"\b(remov|delet|drop|omit|strip|take out|get rid)", re.I)
_UNEXPECTED = re.compile(r"unexpected keyword argument ['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
_NO_ATTR = re.compile(r"has no attribute ['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")
_CANNOT_IMPORT = re.compile(r"cannot import name ['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]")


def deletion_fix(evidence: str, answer: dict) -> dict | None:
    """The chore's OWN rule, made mechanical: 'a fix that drops what the code
    was trying to do (e.g. deleting an argument to silence the error) is not
    grounded - preserve intent or defer.'

    Fires only where the evidence names the thing the caller was trying to use
    AND the fix proposes removing that same named thing. Specified by the
    production system prompt, not derived from any failing case.
    """
    if answer.get("confidence") != "grounded":
        return None
    fix = str(answer.get("fix", ""))
    named = [m.group(1) for pat in (_UNEXPECTED, _NO_ATTR, _CANNOT_IMPORT)
             for m in pat.finditer(evidence)]
    if not named or not _REMOVE.search(fix):
        return None
    for token in named:
        if token in fix:
            return {**answer, "confidence": "needs_verification"}
    return None


def invented_identifier(evidence: str, answer: dict) -> dict | None:
    """The extractor already disabled at n=6. Re-scored here at n=70 so the
    decision rests on a sample instead of six cases."""
    syn = S.triage_syndrome(evidence, answer)
    return syn.corrected if syn.outcome == "corrected" else None


CORRECTORS = {"deletion_fix": deletion_fix, "invented_identifier": invented_identifier}


# -- statistics --------------------------------------------------------------

def _binom_cdf(k: int, n: int, p: float) -> float:
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def cp_lower(successes: int, trials: int, alpha: float = 0.05) -> float:
    """Clopper-Pearson one-sided lower bound on a binomial proportion."""
    if trials == 0 or successes == 0:
        return 0.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        # P(X >= successes | p=mid) = 1 - CDF(successes-1)
        if 1 - _binom_cdf(successes - 1, trials, mid) < alpha:
            lo = mid
        else:
            hi = mid
    return lo


def paired(rows, corrector):
    b = c = base_ok = corr_ok = 0
    detail = []
    for r in rows:
        ans = r.get("answer")
        if not ans:
            continue
        want = r["want"]
        was = ans.get("confidence") == want
        fixed = corrector(r["user"], ans)
        now = ((fixed or ans).get("confidence")) == want
        base_ok += was
        corr_ok += now
        if not was and now:
            b += 1
            detail.append(("caught", r["i"]))
        if was and not now:
            c += 1
            detail.append(("false_reject", r["i"]))
    n = sum(1 for r in rows if r.get("answer"))
    nd = b + c
    p_lo = cp_lower(b, nd) if nd else 0.0
    lower = (2 * p_lo - 1) * nd / n if n and nd else 0.0
    return {"n": n, "baseline_correct": base_ok, "corrected_correct": corr_ok,
            "true_catches": b, "false_rejects": c, "discordant": nd,
            "improvement": round((b - c) / n, 4) if n else 0.0,
            "lower95_improvement": round(lower, 4),
            "verdict": "accept" if lower > 0 else "reject",
            "detail": detail[:12]}


if __name__ == "__main__":
    raw = json.loads(RAW.read_text())
    for arm, data in raw["arms"].items():
        score = [r for r in data["rows"] if r["split"] == "score"]
        tune = [r for r in data["rows"] if r["split"] == "tune"]
        answered = sum(1 for r in data["rows"] if r["answer"])
        base = sum(1 for r in data["rows"]
                   if (r["answer"] or {}).get("confidence") == r["want"])
        print(f"\n=== {arm} ({data['model']})  answered {answered}/{len(data['rows'])}  "
              f"baseline {base}/{answered} correct  {data['wall_s']}s")
        for name, fn in CORRECTORS.items():
            t, s = paired(tune, fn), paired(score, fn)
            print(f"  {name}")
            print(f"    tune  : catches {t['true_catches']:>2} false {t['false_rejects']:>2}"
                  f"  {t['baseline_correct']}/{t['n']} -> {t['corrected_correct']}/{t['n']}")
            print(f"    SCORE : catches {s['true_catches']:>2} false {s['false_rejects']:>2}"
                  f"  {s['baseline_correct']}/{s['n']} -> {s['corrected_correct']}/{s['n']}"
                  f"  improvement {s['improvement']:+.4f}"
                  f"  lower95 {s['lower95_improvement']:+.4f}  -> {s['verdict'].upper()}")
