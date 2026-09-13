"""Threshold analysis of TEE's router cascade.

The router walks a ladder of engine rungs, cheapest first, and escalates when a
chore's deterministic verifier rejects the answer. That is concatenated error
correction, and the quantum threshold theorem's preconditions apply to it:

  (1) RECURSION   - each rung's rejection feeds the next. Yes.
  (2) DETECTION   - the verifier. Imperfect: measured false-accept rate eps per
                    chore in chores.VERIFIER_COVERAGE.
  (3) INDEPENDENCE- failures across rungs must be uncorrelated. THIS IS THE ONE
                    THE CASCADE VIOLATES: q27b-think and q27b-bare are the same
                    base weights at different quantisation, on different
                    backends. A prompt that defeats one very likely defeats the
                    other.
  (4) CROSSOVER   - the question this file answers.

The per-rung outcome, for rung error rate q and verifier coverage c = 1 - eps:

    ship a WRONG answer   with probability   eps * q      (verifier waved it through)
    escalate              with probability   (1 - eps) * q
    ship a RIGHT answer   with probability   (1 - q)

so a cascade ships a wrong answer with

    P(wrong) = SUM_i  [ PROD_{j<i} (1 - eps) * q_j ] * eps * q_i

Two consequences fall straight out, and the simulation quantifies both:

  * At eps = 1 every wrong answer is accepted at the FIRST rung. P(wrong) = q_1
    regardless of ladder depth - extra rungs are unreachable, not merely
    unhelpful. This is the above-threshold regime.
  * Correlation collapses the escalation benefit: if rung i+1 fails whenever
    rung i failed, the second rung contributes nothing to the cases that
    actually reached it - which are, by construction, exactly the hard ones.

Failures are drawn through a one-factor Gaussian copula so correlation is a
parameter rather than an assumption: each rung fails when
`sqrt(rho)*Z + sqrt(1-rho)*E_i` exceeds that rung's threshold, with Z shared.

Deterministic: seeded, stdlib only, no model, no network.
"""

from __future__ import annotations

import math
import random

TRIALS = 40_000
SEED = 20260913

# Measured 2026-09-13, server/tests/test_a85_verifier_coverage.py
EPS = {
    "phrase_deviation": 0.25,
    "repair_script": 0.25,
    "refine_extract": 0.33,
    "structure_facts": 0.67,
    "rerank": 0.67,
    "triage": 1.00,
    "explain_lint": 1.00,
    "compress_recap": 1.00,
}

# The live ladder, cheapest first (router._ladder on this machine).
LADDER = ("q14b+a2", "dsflash", "q27b-think", "q27b-bare", "q35b")

# Rungs sharing base weights. q27b-think and q27b-bare are the same Qwen3.8-27B
# at different quantisation on different backends: near-total correlation.
SHARED = {("q27b-think", "q27b-bare")}


def _norm_cdf_inv(p: float) -> float:
    """Acklam's inverse normal CDF - good to ~1e-9, and stdlib only."""
    a = (
        -3.969683028665376e01,
        2.209460984245205e02,
        -2.759285104469687e02,
        1.383577518672690e02,
        -3.066479806614716e01,
        2.506628277459239e00,
    )
    b = (
        -5.447609879822406e01,
        1.615858368580409e02,
        -1.556989798598866e02,
        6.680131188771972e01,
        -1.328068155288572e01,
    )
    c = (
        -7.784894002430293e-03,
        -3.223964580411365e-01,
        -2.400758277161838e00,
        -2.549732539343734e00,
        4.374664141464968e00,
        2.938163982698783e00,
    )
    d = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00, 3.754408661907416e00)
    lo, hi = 0.02425, 1 - 0.02425
    if p < lo or p > hi:
        t = p if p < lo else 1 - p
        q = math.sqrt(-2 * math.log(t))
        num = ((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]
        den = (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1
        return num / den if p < lo else -num / den
    q = p - 0.5
    r = q * q
    num = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q
    den = ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1
    return num / den


def simulate(
    q: list[float], eps: float, rho: float, trials: int = TRIALS, seed: int = SEED
) -> dict:
    """Walk the cascade `trials` times. Returns outcome shares and rung credit."""
    rng = random.Random(seed)
    # q = 0 and q = 1 have no finite normal threshold, and MEASURED rungs hit
    # both: measure_rung_correlation.py found the two 27B rungs at q = 0.0 on
    # 35 labelled tasks, which drove _norm_cdf_inv(1.0) into log(0). A rung
    # that never fails is +inf (the latent never exceeds it); one that always
    # fails is -inf.
    infinity = float("inf")
    thresholds = [
        infinity if qi <= 0.0 else (-infinity if qi >= 1.0 else _norm_cdf_inv(1 - qi))
        for qi in q
    ]
    root, rest = math.sqrt(rho), math.sqrt(1 - rho)
    wrong = escalated = right = 0
    credit = [0] * len(q)  # which rung supplied the shipped-correct answer
    for _ in range(trials):
        z = rng.gauss(0, 1)
        shipped = False
        for i, thr in enumerate(thresholds):
            fails = (root * z + rest * rng.gauss(0, 1)) > thr
            if not fails:
                right += 1
                credit[i] += 1
                shipped = True
                break
            if rng.random() < eps:  # verifier waved the wrong answer through
                wrong += 1
                shipped = True
                break
        if not shipped:
            escalated += 1  # every rung failed and was caught -> back to client
    n = float(trials)
    return {
        "wrong": wrong / n,
        "right": right / n,
        "escalated": escalated / n,
        "credit": [c / n for c in credit],
    }


# The live ladder's measured costs: (latency median s, load s). From
# kernel/machine.py ENGINES, measured rows only.
COSTS = {
    "q14b+a2": (1.74, 1.1),
    "dsflash": (4.41, 3.0),
    "q27b-think": (7.66, 46.0),
    "q27b-bare": (9.69, 18.0),
    "q35b": (16.70, 0.0),
}


def walk_cost(order: list[str], q: float, eps: float, resident: str, trials: int, seed: int):
    """Expected wall-clock of one route() call, and where it ends.

    A rung that is attempted costs its latency, plus its load unless it is
    already resident. The walk stops when a rung answers and the verifier
    accepts it - rightly or wrongly.
    """
    rng = random.Random(seed)
    total = 0.0
    wrong = 0
    for _ in range(trials):
        for engine in order:
            latency, eta = COSTS[engine]
            total += latency + (0.0 if engine == resident else eta)
            if rng.random() >= q:  # answered correctly
                break
            if rng.random() < eps:  # wrong, and the verifier let it pass
                wrong += 1
                break
    return total / trials, wrong / trials


def _bar(x: float, width: int = 26) -> str:
    return "#" * round(x * width)


def main() -> None:
    print(__doc__.split("Deterministic:")[0].strip()[:0] or "", end="")
    print("=" * 78)
    print("TEE ROUTER CASCADE - THRESHOLD ANALYSIS")
    print("=" * 78)
    print(f"ladder: {' -> '.join(LADDER)} -> client")
    print(f"trials: {TRIALS:,}  seed: {SEED}\n")

    # Per-rung error rates. Uniform, so the ONLY thing varying below is the
    # verifier and the correlation - the two preconditions under test.
    q = [0.30] * len(LADDER)

    print("A. VERIFIER COVERAGE decides whether depth is reachable at all")
    print("   (rho = 0: perfectly independent rungs, the best case)\n")
    print(f"   {'chore':<18}{'eps':>5}  {'ship WRONG':>11}  {'to client':>10}   depth used")
    for chore, eps in sorted(EPS.items(), key=lambda kv: kv[1]):
        r = simulate(q, eps, rho=0.0)
        used = sum(1 for c in r["credit"] if c > 0.001)
        row = (
            f"   {chore:<18}{eps:>5.0%}  {r['wrong']:>10.1%}  {r['escalated']:>9.1%}"
            f"   {used} of {len(LADDER)} rungs  {_bar(r['wrong'])}"
        )
        print(row)

    print("\n   At eps = 1.00 the first rung's wrong answers are ALL accepted, so")
    print("   P(ship wrong) = q1 and no rung below the first is ever reached on a")
    print("   failure. Depth is unreachable, not merely unhelpful.\n")

    print("B. INDEPENDENCE decides whether depth buys anything")
    print("   (eps = 0.25, phrase_deviation - the best verifier measured)\n")
    cols = f"   {'rho':>5}  {'ship WRONG':>11}  {'to client':>10}  rung credit (share answered)"
    print(cols)
    for rho in (0.0, 0.5, 0.9, 0.99):
        r = simulate(q, 0.25, rho=rho)
        cr = "  ".join(f"{c:.0%}" for c in r["credit"])
        print(f"   {rho:>5.2f}  {r['wrong']:>10.1%}  {r['escalated']:>9.1%}  {cr:<38}")
    print("\n   q27b-think and q27b-bare are the same base weights, so their pair sits")
    print("   near rho = 1: the second contributes almost nothing to the cases that")
    print("   reached it, because those are exactly the ones the first could not do.\n")

    print("C. WHAT DEPTH ACTUALLY TRADES (eps = 0.25, the best verifier measured)")
    print("   Truncating the ladder to k rungs. Watch all three columns, not one:\n")
    head = (
        f"   {'k':>2}  {'RIGHT':>7}  {'ship WRONG':>11}  {'to client':>10}   net effect of rung k"
    )
    print(head)
    prev = None
    for k in range(1, len(LADDER) + 1):
        r = simulate(q[:k], 0.25, rho=0.0)
        if prev is None:
            note = "baseline"
        else:
            note = (
                f"+{r['right'] - prev['right']:.1%} right, "
                f"+{r['wrong'] - prev['wrong']:.1%} wrong, "
                f"{r['escalated'] - prev['escalated']:+.1%} client"
            )
        print(
            f"   {k:>2}  {r['right']:>6.1%}  {r['wrong']:>10.1%}  {r['escalated']:>9.1%}   {note}"
        )
        prev = r
    print("\n   THE COUNTERINTUITIVE RESULT, and it is the threshold theorem's:")
    print("   depth raises RIGHT answers (70% -> 90%) but ALSO raises silently-WRONG")
    print("   ones (7.7% -> 9.6%), because every extra rung is another draw against")
    print("   an imperfect verifier. It pays for both out of the SAME pool - the")
    print("   escalations - and escalation is the one tier that is never wrong.")
    print("   So the cascade converts a known unknown into a mix of right answers")
    print("   and confident errors. Whether that trade is good depends entirely on")
    print("   what a wrong answer costs relative to asking the client.\n")

    print("\nD. THE CROSSOVER - what a rung must beat to be worth adding")
    print("   A rung helps only on cases that (a) reached it and (b) it can do.")
    print("   Reaching it requires every rung above to FAIL AND BE CAUGHT:\n")
    for eps in (0.25, 0.67, 1.00):
        share = (1 - eps) * 0.30
        solves = (1 - 0.9) * (1 - 0.30)
        print(
            f"   eps={eps:>4.0%}  sees {share:>5.1%} of traffic;"
            f" at rho=0.9 solves ~{solves * 100:>4.1f}% of it"
            f" -> {share * solves:.2%} of all tasks"
        )
    print("\n   Below roughly 1% recovered, a rung is paying full latency for noise.")

    print("E. ORDERING THE TAIL: latency alone vs finish time (latency + load)")
    print("   The resident is tried first either way; this is about the REST.\n")
    resident = "q14b+a2"
    tail = [e for e in LADDER if e != resident]
    by_latency = [resident, *sorted(tail, key=lambda e: COSTS[e][0])]
    by_finish = [resident, *sorted(tail, key=lambda e: COSTS[e][0] + COSTS[e][1])]
    print(f"   latency-ordered: {' -> '.join(by_latency)}")
    print(f"   finish-ordered : {' -> '.join(by_finish)}\n")
    print(f"   {'q (per-rung error)':<22}{'latency-ord':>13}{'finish-ord':>13}{'saved':>10}")
    for qq in (0.20, 0.30, 0.50, 0.70):
        a, _ = walk_cost(by_latency, qq, 0.25, resident, TRIALS // 10, SEED)
        b, _ = walk_cost(by_finish, qq, 0.25, resident, TRIALS // 10, SEED)
        print(f"   {qq:<22.0%}{a:>12.2f}s{b:>12.2f}s{a - b:>9.2f}s")
    print("\n   The gap is small while the resident usually answers and grows with q,")
    print("   because it is only paid on the escalations that get past it. It is a")
    print("   LATENCY fix, not a correctness one: both orders ship the same answers.")
    print("   q27b-think is why - 7.66 s to answer, 46 s to load, so latency alone")
    print("   ranks it second in the tail and finish time ranks it last.\n")

    print("=" * 78)
    print("CONCLUSIONS")
    print("=" * 78)
    print("1. eps gates DEPTH. Three chores (eps=1.00) cannot use the cascade at all:")
    print("   their first wrong answer is accepted and shipped.")
    print("2. rho gates VALUE. Two rungs on shared weights are one rung with extra")
    print("   latency - the independence precondition, and the cascade violates it.")
    print("3. Depth is not free even when it works: it converts escalations into a")
    print("   MIX of right answers and silent errors. With eps=0.25 the ladder buys")
    print("   +20 points of right answers and +1.9 points of wrong ones.")
    print("4. The one tier that is always safe is the LAST: returning to the client")
    print("   is a genuinely independent solver, it is free, and it is never a")
    print("   silent error - it is an explicit hand-back. The cascade should be")
    print("   read as spending correctness-certainty to avoid asking.")


if __name__ == "__main__":
    main()
