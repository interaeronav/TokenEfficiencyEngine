# 30 — Design logic: frameworks, math, patterns (2026-08-22)

## Frameworks standing

MDA most-cited but analytic-not-generative; DDE academic successor
without industry adoption; Schell lenses = review prompts. The
operational core for an agent: **Cook's loops/arcs + skill atoms**
(practitioner-native vocabulary) and **Machinations economy notation**
(Dormans' PhD thesis is open access — the notation is freely encodable;
the machinations.io TOOL is proprietary SaaS whose free-tier diagrams
are public-by-default — an IP-hygiene warning to surface to users).

## Encodable mathematics (goes straight into checkers)

- Economy balance identity: Δ(money supply) = Σfaucets − Σsinks per
  currency per period; inflation = faucet volume outrunning sinks. EVE
  Monthly Economic Reports = best public corpus of real faucet/sink
  accounting; PoE: currency-as-consumable gives intrinsic sinks; league
  resets = scheduled economy resets.
- Progression curve families: linear / polynomial a·L^b (b≈2-3) /
  exponential A·r^L; RuneScape's 2^(n/7) doubling (L99 = 13,034,431 XP;
  L92 = the halfway point) as the canonical worked example.
- Idle math: generator cost_n = base·r^n (r 1.07-1.15); bulk-buy
  geometric sum; linear production vs exponential cost → logarithmic
  real-time progress, reset by multiplicative prestige.
- Gacha pity as a hazard function h(n): Genshin 0.6% base, soft pity
  from 74 (+~6 pp/pull), hard 90, consolidated 1.605%, E[N]≈62-63.
- Balance: cost curves for transitive content; payoff matrices +
  mixed-strategy equilibria for intransitive mechanics (Schreiber's free
  Game Balance Concepts course covers the methods).

## Level design and procgen

Hullett & Whitehead FPS pattern catalog (free author PDF, empirically
validated) = seed catalog; Totten's prospect/refuge + weenies
wayfinding; heatmap diagnostics (Halo 3 / Valve precedent). Licenses:
**WFC MIT, Tracery Apache-2.0** (embeddable); cyclic dungeon generation
METHOD free (Unexplored's implementation proprietary).

## Documentation practice 2026

Monolithic GDDs are dead. The artifact set: **one-pager (Librande) +
Cerny macro chart** (spreadsheet: levels/spaces × mechanics/exotics,
committed before production, publishable-first-playable gate) + living
wiki + per-feature briefs. This aligns exactly with TEE's
diffs-over-snapshots dogma — and is what the module emits.

## Computational design: usable vs academic

Usable now: discrete-time Monte Carlo simulation of source/sink economy
graphs (Machinations semantics; GEEvo 2024 demonstrates evolutionary
balancing over such graphs); closed-form math above; cost-curve/payoff
solvers. Out of scope: RL playtesting (EA SEED research-grade).
Restricted: **Ludii CC-BY-NC-ND (excluded), BGG mechanism taxonomy
(commercial license required)**; methods/ideas encodable in TEE's own
words (17 USC 102(b)), never verbatim book text.
