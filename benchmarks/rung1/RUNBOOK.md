# Rung-1 runbook — the triage "motivation pack" (A34 M4, owner-approved)

Goal: an adapter that makes Qwen2.5-Coder-14B pass the FULL trap suite
(deferral on API drift, grounded on evidence-complete failures) without
regressing the M3 rows. Adoption re-registers `llm_triage` and bumps
`chores.REVISION` to name the adapter.

Preconditions (all must hold before starting):
- Machine quiet: no UnrealEditor / voxkiln battery / other model servers
  (`pgrep -f "Engine/Binaries/Mac/UnrealEdito[r]"` empty; the §2 lesson).
- An overnight-class window: training is hours; nothing else scheduled.
- `mlx_lm.lora --help` READ FIRST and flags verified against what this
  runbook assumes — the mlx-lm CLI drifts between releases (A30
  discipline applies to tool APIs too). Verify the expected dataset
  format (chat-format messages JSONL) while there.

Sequence:

1. Generate data (CPU, can pre-run any time):
   `python benchmarks/rung1/gen_distill.py --per-family 400`
   → 2,280 train / 120 valid across 3 drift + 3 grounded families;
   eval-suite fixtures are blacklisted from the vocabulary.

2. Train (overnight; flags verified per precondition):
   `mlx_lm.lora --train --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit \
      --data benchmarks/rung1/data --iters 600 --batch-size 4 \
      --adapter-path benchmarks/rung1/adapters/tee-triage-a1`
   Watch valid loss; stop early on plateau. The adapter dir is the
   artifact (tens of MB) — version it `tee-triage-a1`, `-a2`, ...

3. Evaluate — the gates, in order (each blocks the next):
   a. Serve with the adapter:
      `mlx_lm.server --model mlx-community/Qwen2.5-Coder-14B-Instruct-4bit \
         --adapter-path benchmarks/rung1/adapters/tee-triage-a1 --port 18080`
   b. FULL trap suite: `TEE_LOCAL_LLM_URL=http://127.0.0.1:18080/v1 \
      TEE_LOCAL_LLM_MODEL=<model> uv run pytest tests/test_llm_traps.py -m llm`
      → must be 6/6 (all traps defer, all controls grounded).
   c. M3 latency re-run (`run_m3_llm.py latency`) → no chore above ~2 s.
   d. M3 quality re-run (`run_m3_llm.py quality` + grader) → refined
      still never-worse; abstention rate not degraded.
   e. A held-out sanity: 5 fresh hand-written failures (not from the
      generator vocabulary) triaged by eye.

4. Adopt or record:
   - PASS: commit the adapter, bump `chores.REVISION` to `r3+tee-triage-a1`,
     re-register `llm_triage` (tee/llm/tools.py carries the block note to
     remove), update docs/setup-local-llm.md (+ adapter-path serving
     line), append the rows to RESULTS.md, PROGRESS entry, tee_remember.
   - FAIL: record the rows and the failure mode in PROGRESS; iterate
     data/iters at most twice before declaring rung-1 insufficient
     (also a valid, recorded outcome per the script).

5. Idle-unload: stop every server; leave nothing resident.
