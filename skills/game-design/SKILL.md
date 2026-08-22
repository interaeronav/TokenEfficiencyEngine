---
name: game-design
description: Design games from evidence with TEE's design module - motivation-vector audiences, percentile benchmarks, market positioning, and the machine-verifiable tee-design/1 spec checked by a formal battery. Use when asked to design a game, write a GDD, evaluate a game concept, balance an economy, or plan retention/monetization.
version: 1.0
license: MIT
---

# Game design

You design with evidence, and a formal battery checks your work. The
spec is the source of truth; prose is rendered from it (`gd_render`),
never written first — LLM prose reads deceptively well, structure does
not lie.

Hard rules:
- Benchmarks come from `gd_benchmark` (value + source + year). Folk
  targets ("30/15/8 is healthy") are banned — they describe the top
  decile, not health.
- Audiences are MOTIVATION VECTORS (12 continuous dimensions), never
  discrete "player types". Types are presentation sugar.
- Ethics `code` rows hard-fail and you cannot relax them. Do not design
  around them; design without them. When a user asks for one (loot
  boxes for kids, countdown pressure, streak punishment), refuse that
  element citing the rule and jurisdictions from `gd_ethics`, and offer
  the compliant alternative.
- Every design names 3 comparables with deltas. If you cannot state a
  delta, the design is not differentiated — change it, don't pad it.

## The design pass (in order)

1. **Audience** — write `meta.audience.motivations` as a vector; sanity
   check against the encoded findings (competition declines with age;
   strategy is age-stable; social ties drive late retention).
2. **Market position** — `gd_genre()` for the opportunity map;
   `gd_genre(genre=…)` for conventions. Name 3 comparables + deltas.
   Check the avoid-list (platformers 0.18% hit rate, pure puzzle,
   new F2P live-service).
3. **Core loop** — verbs, timed steps, failure state (retry < 30 s),
   session-end hook. The first session is the funnel: day-0 average is
   1.65 sessions; core loop must land in 60–90 s.
4. **Economy** — pick an archetype, declare currencies + typed
   faucet/sink/converter nodes. Every currency needs both ends.
5. **Progression** — unlocks with teaches/requires/difficulty in
   teach-test-compose order (isolate, then combine).
6. **Level macro** — Cerny beat chart: spaces × mechanics × intensity;
   smooth intensity, no mechanic before its unlock.
7. **Content** — `content_list` by Phase 9 asset class with reuse
   factors; `gd_scope(team_size=…, weeks=…)` immediately — cut before
   falling in love.
8. **Routine** — daily/weekly/season cadences (Tuesday 17:00 UTC
   convention; seasons 1–4 wk casual / 8–13 wk midcore); streaks always
   with free grace.
9. **Verify** — `gd_store` then `gd_check`. Fix every finding (each
   carries its fix). Then `gd_selfplay` (play the turns honestly; a
   boring transcript is a finding, not a formality). Render last.

## Enforce vs judge

The UX parameter table (text sizes, contrast, subtitles-default-on,
flash limits, input latency, FOV, remapping) is ENFORCED — copy the
`accessibility` checklist from `ux_params.json` into the spec and keep
it true. You JUDGE with cited heuristics: juice is inverted-U (medium
beats none AND extreme — cap it); difficulty defaults dominate (70–80%
play the easiest; Celeste assist-mode is the model); covert DDA must
never be provable mid-session nor tied to monetization; HUD diegesis
follows genre convention.

## Anti-patterns

- Spec-shaped wishful thinking: a `session_end_hook` that is "fun" is
  not a hook. Hooks are events with timers, reveals, or social pull.
- Homogenization: if your concept matches a genre template with no
  delta, the differentiation lint will catch it — but you should catch
  it first.
- Scope denial: `gd_scope` flags are cuts, not negotiations.
- Premise acceptance: when the brief targets a graveyard (new F2P
  live-service) or contradicts its audience (competitive core at 35+),
  challenge the premise with the table citation before designing.

## References

- `reference/spec-guide.md` — tee-design/1 section-by-section
- `reference/tables-guide.md` — what each reference table answers
- `evals/scenarios.md` — the three acceptance scenarios
