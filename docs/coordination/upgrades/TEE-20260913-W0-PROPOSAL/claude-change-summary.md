# W0 change summary — input for a GPT-6 execution packet

Author: Claude (Opus 5), 2026-09-13. **This is not a packet and not an upgrade.**
Protocol 1.0.1 reserves packet authorship to GPT-6; this is the change
description that packet would describe. Nothing has been built, versioned,
installed or delivered.

## 1. Source identity

| | |
|---|---|
| Repository | `/Users/john/TokenEfficiencyEngine` |
| Branch | `claude/token-efficiency-engine-5jv1dj` |
| Version in tree | **0.30.1** (unchanged — no version cut taken; that decision is the owner's) |
| Head | `73a76e1b26a99bf134785b4d33158b7787a6a3e9` |

Three commits, in order:

```
091eb77  Commit the architecture lane, and fix the six defects its tests exposed
c306138  Take three in-flight files under version control, with two small W0 edits
73a76e1  W0: a thinking engine, and a measured gate on when extra effort can help
```

**The tree is NOT clean and must not be released from as-is.** 114 untracked and
39 modified files remain, all concurrent A80–A84 work from other sessions. Two of
the three commits above disclose mixed authorship in their messages: `c306138` is
1,468 lines of which ~11 are W0's, and `73a76e1` includes `router.py`, `chores.py`
and three shared docs that already carried other sessions' uncommitted edits that
git cannot separate. A release build should come from a clean worktree at a
chosen commit, not from this working directory.

## 2. What changes for a client

**Served surface is unchanged: 17 always-loaded tools / 2,129 wire tokens.**
W0 adds no tool. Virtual tools stand at 232 (36,159 flat, 94.1% progressive
saving) — that count reflects the A82/A83/A84 lanes, not W0.

Behaviour a client could notice:

- **Chores can now actually run on this machine.** The active profile previously
  resolved to `:8080`, which is not answering, so every chore had been degrading
  silently to its deterministic path. The new `q27b-think` profile names its own
  endpoint and answers.
- **`response_format` is negotiated per endpoint** instead of sent
  unconditionally. Previously TEE could not talk to a vLLM backend at all: it
  refuses the field with HTTP 400 where the MLX server accepts and ignores it.
- **Three new error codes** a client may see: `llm_no_answer` (a model spent its
  budget reasoning and produced nothing), `vlm_no_answer` (same on the vision
  seam), `llm_widening_refused` / `llm_widening_unproven` (a chore asked for
  thinking that its verifier cannot benefit from).
- **Chore replies may carry `reasoning_chars`**, an integer. The reasoning TEXT
  never crosses the wire.

## 3. Machine-local state, which is NOT part of a package

These were changed on the owner's machine and would not travel with, or be
restored by, an extension install:

- `.tee/llm-profile.json` — active profile moved `q14b` → `q27b-think`
  (`pinned: true` preserved). Backup at `llm-profile.json.bak-w0`.
- **Weights deleted**: `mlx-community/Qwen2.5-Coder-14B-Instruct-4bit` (7.7 GB)
  and `mlx-community/Qwen3.5-9B-MLX-4bit` (5.6 GB), at owner instruction.
- `.tee/config.toml` was **not** modified. Its `[llm] url = :8080` still points at
  a dead endpoint; the active profile overrides it.

`profiles.DEFAULT_ACTIVE` remains `q14b` — deliberately. Setting it to the 27B was
tried and reverted: it is the fallback for a *fresh install with no state*, and
claiming every install should default to a 28 GB model it will not have broke 24
tests that reasonably treat the shipped default as ground truth.

## 4. Continuity checks the packet must include

1. **Fleet extras are wiped by every `.mcpb` install** (venv rebuilt from the
   lock). Restore set captured from the venv *before* any install — 18
   distributions installed but absent from `uv.lock`:

   `cloudpickle colorlog embreex huggingface_hub importlib_resources lxml
   manifold3d mapbox_earcut pdfminer.six pillow_heif pycollada pydantic_core
   rtree seamkiln==0.1.0.dev0 svg.path typing_extensions vhacdx xxhash`

   `seamkiln==0.1.0.dev0`, `manifold3d`, `embreex`, `vhacdx`, `pycollada` and
   `rtree` are load-bearing — the garment lane and trimesh's mesh backends.
2. **Verify the served surface after install** is still 17 / 2,129. W0 adds no
   tool, so any change is a regression or another lane's arrival.
3. **Verify a chore answers**, not merely that the server boots. The failure this
   release fixes was silent degradation, which a boot check cannot see. A trap
   suite run is the honest check: it scored 6/6 in 13.4 s on `q27b-think`.
4. **Do not verify against `pytest -m "not dcc"`.** That REPLACES `pyproject`'s
   `addopts` rather than narrowing it, re-selecting `cfd`/`ml`/`network`/`llm`
   tests the project excludes — 3,042 collected against the default 3,001, and
   five times slower. The canonical command is `uv run --no-sync pytest`.

## 5. Rollback

Code rolls back by commit — `091eb77^` predates all three. Machine state does not:

- restore `.tee/llm-profile.json` from `llm-profile.json.bak-w0`
- the deleted weights need re-downloading (`hf download
  mlx-community/Qwen2.5-Coder-14B-Instruct-4bit`, ~7.7 GB); the `q14b` profile,
  its `ENGINES` row and the `tee-triage-a2` adapter are all still wired for it
- reinstall the 18 extras above

## 6. Evidence

Suite: **2,983 passed, 22 skipped, 141 deselected** on the canonical invocation,
3m07s. 26 new tests. Measurements and their caveats are recorded in
`benchmarks/RESULTS.md` and `docs/PROGRESS.md`; the rulings are in
`docs/DECISIONS.md`.

Two figures a packet should quote carefully:

- **ρ = 1.00** between the two 27B rungs rests on **one failure each**. With a
  single failure per rung the φ coefficient can only be 1.00 or negative — a
  directionally confirmed prediction, not a tight estimate. The robust figure is
  ρ = 0.53 between different model families, on 17 and 22 failures.
- **`THINKING_ALLOWED` ships empty.** No chore is measured to benefit from
  thinking. The engine exists and is gated, not adopted.

## 7. Open, and the owner's to decide

- The version cut (0.30.1 → ?) and whether W0 warrants one.
- Whether to release before or after the A82–A84 work is committed.
- `tee-triage-a2` is stranded: 14B-trained, and the 14B is deleted. The 27B
  passes the traps 6/6 bare, so nothing depends on it.
