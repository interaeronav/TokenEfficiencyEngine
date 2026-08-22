# 31 — AI game-designer prior art & module architecture (2026-08-22)

## The gap is real

No shipping product or engine encodes design expertise as of Aug 2026:
Ludo.ai = ideation/market scans; Layer.ai = art ops; Rosebud/Bitmagic =
prompt-to-prototype toys; GDD generators = prose templates with no
verification. Platform AI is execution-level only: Roblox's Apr-2026
agentic Assistant (planning mode + playtesting agent — the closest
analog to TEE's loop), Unity AI (Muse retired Oct 2025). ROADMAP FACT:
**UE 5.8 ships a first-party Experimental Unreal MCP plugin (June 2026),
extended into UEFN on 2026-08-20**; UE6 (EA target end-2027) merges
UE5+UEFN around Verse — directly validates TEE's A4 proxy architecture.

## The winning pattern: LLM proposes, formal system verifies

Everywhere generation succeeded it was harnessed: GAVEL (130/185
playable WITH an evolution loop + engine validation), Mortar
(skill-ordering preservation as a cheap automated metric), ScriptDoctor
(LLM + tree search), RuleSmith (self-play + Bayesian optimization),
DreamGarden (hierarchical plan → UE submodules). Documented raw-LLM
failure modes: **homogenization** (2-8× less collective diversity than
humans — force differentiation with market-position tables and novelty
checks); difficulty-calibration and structural-coherence failures;
**prose GDDs read deceptively well** (GPT-4 GDDs outscored a human
expert 4.71 vs 3.29 in a small-n study) — which is exactly why prose
review is an unreliable gate and the machine-verifiable spec must be the
source of truth; redundancy (fixed with curated lexicons = fact tables).

## Knowledge encoding (A16)

RAG beats fine-tuning for knowledge injection (EMNLP 2024), and
fine-tunes are per-model — structurally wrong for an MCP server. The
three-layer split: (1) **curated reference tables** — the "building
code": benchmark percentile grids, genre conventions, economy
archetypes, scope-cost weights, UX parameter tables, all versioned with
source+as_of; (2) **one `game-design` skill** (Agent Skills standard)
carrying judgment: the design-pass order (loop → economy → progression →
content), anti-patterns, differentiation forcing-moves, when to
challenge the premise; (3) **executable checkers** run via the script
lane. RAG optional long-tail only; no fine-tune.

## Verification battery (cost-ordered)

design-lint (near-free; "core loop undefined", "currency with no sink",
"no session-end hook", "mechanic introduced never composed", "boss
before mechanic taught" — a genuine novelty: no game-design linter
exists in the literature; requirements-smells detection hits 89% P/R in
the software analog) → scope/effort estimate (content list ×
asset-class weights) → economy timestep simulation (~200-line
source/sink solver replicates Machinations' useful 80%; per-persona
runs) → progression validator (monotonicity, time-to-unlock bounds,
teach-test-compose ordering) → bounded LLM paper-prototype self-play
(one transcript) → in-engine playtest last.

## The spec artifact (A17)

Existing GDLs disqualified: VGDL (2D-only, dormant), Ludii
(CC-BY-NC-ND), PuzzleScript (tile-only). TEE defines `tee-design/1`
(versioned JSON, stable IDs): `core_loop` (verbs, step durations,
failure state, session-end hook) / `economy` (typed faucet-sink-converter
graph with rates) / `progression` (unlock+difficulty tables, ordering) /
`level_macro` (Cerny-style beat chart) / `content_list` (assets by class
+ count + reuse — feeds the scope estimator AND Phase 9's asset module)
/ `open_questions` (deliberately un-auto-decided judgment items). Every
section is independently consumable by a checker and by a downstream
build phase; the prose GDD is a rendered VIEW, never the source.
