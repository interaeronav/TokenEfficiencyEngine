# tee-design/1, section by section

Authoritative schema: `server/src/tee/design/spec.py` (validate names the
exact fix for every shape error). This is the intent guide.

## meta
Audience is a motivation vector over 12 dimensions (destruction,
excitement / competition, community / challenge, strategy / completion,
power / fantasy, story / design, discovery) — values 0..1, continuous.
`comparables`: exactly the "like X but Y" list; 3 minimum, each with a
delta. `min_age` drives ethics gates. `team_size` feeds scope.

## core_loop
`verbs` are what the player does; `steps` the timed loop; both feed
self-play. `failure_state` must state what failure costs (and keep the
retry loop under 30 s). `session_end_hook` is the comeback reason —
an event, reveal, or social pull, not an adjective.

## economy
`currencies` + `nodes` (faucet/sink/converter with per-session rates).
`archetype` selects the sink/faucet band the simulation enforces
(premium_session 0.6–1.1, player_market 0.9–1.05, …). `personas`
optional — defaults are casual/core/dedicated.

## progression
`unlocks`: {id, at, teaches, requires, difficulty}. `at` aligns with
beat numbers so teach-before-use is checkable. `pity` (if any random
rewards): base/soft_start/increment/hard — the hazard function is
recomputed and checked against your declared expected_pulls.

## level_macro
Cerny beats: {space, mechanics, exotics, intensity, content_classes}.
Intensity is a 1–10 curve; jumps > 3 are flagged. content_classes must
exist in content_list.

## content_list
{class, count, reuse} with Phase 9 asset classes — this section IS the
bridge to the asset module (as_search consumes the classes) and the
scope estimator input.

## routine
daily/weekly/season strings + `streak: {grace_days: >=1}`. Absence
penalties are an ethics violation, not a retention mechanic.

## monetization
model, loot_boxes, odds_disclosed, currency_hops, virtual_currency,
real_price_display, countdown_offers, binge_offers — the ethics checker
reads exactly these fields; leaving them out means defaults are assumed
conservative (minors reachable unless min_age >= 18).
