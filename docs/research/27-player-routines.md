# 27 — Player routines & engagement telemetry (2026-08-22)

Benchmark numbers with verification grades; every figure carries
source+year in the module's tables.

## Retention reality vs folklore

GameAnalytics 2026 (16k+ mobile games, data 2025): MEDIAN mobile D1 ~22%
/ D7 ~4% / D30 ~0.7%; the folk "healthy" 30/15/8 targets describe the
top DECILE. Top quartile ≈ 30% / 6-7% / 1.7%. PC (3,582 games, first
large public set): median D1 ~7% / D7 ~1.2% / D30 ~0.2% — PC is
depth-driven (median session ~18 min, 1.7/day, ~3× mobile playtime),
mobile frequency-driven (3-5 min, ~4/day). Genre grid (AppsFlyer Q3-2022,
stale-but-canonical): match/puzzle sticky (D30 7.2/5.4%),
hyper-casual/shooters leaky (1.4/1.8%). ~70% of installs are lost within
72 h; day-0 sessions average 1.65 — the first session IS the funnel.

Steam funnel (GameDiscoverCo): wishlist→first-week ≈ 0.15× median
(0.10× above $10); refunds mean 10.8% / median 9.5%; Steam 2025 Replay:
median user played 4 unique games; ~14% of playtime on current-year
releases; ~40% on 8+-year-old games.

## Playtime and churn laws

Total per-game playtime is Weibull-distributed; the urge to return
decays power-law; most games get <10 h per player (Sifa/Drachen 2014,
6M players). **Regularity (inter-session-interval entropy) beats volume
as a churn predictor** — habitual players outlast bingers at equal
hours; binge episodes independently predict harm. Churn is visible as
rhythm decay days before the last session; first-week cadence features
rival ML classifiers. FTUE: ~20% never complete the first tutorial quest
(deltaDNA, stale-canonical); working heuristics: core loop lands <60-90 s.

## Habit mechanics and live-ops norms

Best quantified streak evidence is Duolingo (+14% D14 in A/B; 7-day
streaks ~2.4× retention w/ selection caveats); in-game causal effect
sizes essentially unpublished → encode as adopted conventions with
mechanism (cadence targeting), not measured lifts. Three-layer loop:
daily reset (~24 h), weekly (Tuesday convention — Destiny 17:00 UTC),
season/pass 1-4 wk casual / 8-13 wk midcore (Apex ~90 days verified);
battle-pass adoption ~51-60% of top-grossing mobile.

## The responsible-design boundary (encode as code-severity rules)

FTC: Epic/Fortnite $245M dark-pattern settlement; Genshin 2025 (no loot
boxes to U16 without parental consent; no multi-hop currency price
obscuring). EU CPC 2025 virtual-currency principles (real-money price
display, no pressure tactics on children — enforced, Star Stable).
Belgium: paid loot boxes illegal. Australia 2024: paid loot boxes ⇒ M
minimum, simulated gambling ⇒ R18+. Brazil: U18 loot-box ban effective
Mar 2026. Evidence: loot-box spend ↔ problem gambling meta-analytic
r≈0.26 — the randomization itself is the risk factor (non-random IAP
η²=0.004). Module rules: disclosed odds; single-conversion transparent
pricing; streak repair/grace, never gate paid value; no countdown
pressure on minors; appointment mechanics reward presence, never punish
absence; binge detection triggers care, not upsells; no earned-content
deletion for lapsing.
