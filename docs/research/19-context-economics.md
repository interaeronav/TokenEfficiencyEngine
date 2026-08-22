# 19 — Context economics: script lane, eviction, encodings (2026-08-22)

Research + simulation pass grounding Phase 8. Simulations ran against the
real TEE machinery (FakeAdapter where the DCC is irrelevant); economics use
Fable-5 API rates ($10/$50 per MTok; cache read $1, write $12.50).

## API-side landscape (verified against the current Claude API reference)

- **Programmatic tool calling** (`code_execution_20260120` +
  `allowed_callers`): Claude scripts its tool calls; intermediate results
  return to the running code, not to model context. **Incompatible with MCP
  tools** — so TEE implements the pattern app-side (`tee_script`, A11).
- **Context editing** (`clear_tool_uses_20250919`): hosts clear old tool
  results. Affordable for TEE specifically because every response is
  re-derivable from the scene cache / fact store / checkpoints — the
  eviction-safe contract + `tee_status(recap=true)` makes it explicit.
- **Tool search / deferred schemas** is now how Claude Code loads MCP tools
  — independently validates the progressive-disclosure registry (A6/P4).
  Keep tool definitions byte-stable for prompt caching.

## Simulation results

| Sim | What was measured | Result |
|---|---|---|
| A | 120-turn session economics, keep-last-10 eviction + script lane | today $6.28 → eviction $4.93 (-21%) → +script lane $2.42 (**-61%**); peak context 62k → 33k |
| B | columnar re-encoding, real payloads via project estimator | 100-entity scene summary 1,272 → 739 tok (**-42%**); 11 heterogeneous facts −1% → threshold, not blanket |
| C | fact search at 611 facts (real + modeled distractors), labeled queries | current substring-count **9/10**; naive BM25 **7/10 (regression)**; substring+IDF hybrid 9/10 (no gain) |
| D | Phase-7 conformance fix loop, rounds vs one scripted call | 5 rounds / 464 tok → 1 round / 63 tok (**-86%**), end state conformant; built and re-measured with the REAL executable script: flat ~173-tok script vs ~130 tok/conflict rounds → 17.7%/63.2%/76.3% saved at 1/3/5 conflicts (the 86% assumed a sketch-length script) |

## The negative result that matters

Swapping `ExtractStore.search` for BM25 — the "obvious" upgrade — was
simulated and **regressed** relevance: token-exact matching loses "room"
inside "Living Room" and gets diluted by keyframe/transcript distractors,
while cheap substring containment holds 9/10 at realistic scale. Search
stays as is (A12). Known limit: bare-numeral queries ("dimension 8") tie
against hex/float noise; the covered path is `ex_facts(kind="dimension")`.

## Caption-once arithmetic

A 1568-capped frame re-view ≈ 2,200 tokens, every time; a stored ≤20-word
caption ≈ 30 tokens, once, and makes the frame text-searchable. Break-even
on the first avoided re-view.
