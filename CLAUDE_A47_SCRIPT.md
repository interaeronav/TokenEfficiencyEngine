# CLAUDE_A47_SCRIPT.md — senses for blind hosts (drive the parked driver)

**Owner directive (2026-08-31):** *"deep research a new feature for tee
which is machine vision and sound to allow models that don't have this
feature to be able to use machine vision and sound. my particular case is
with the deep seek model on my machine, it does'nt have vision."* Clarified
same day: the case is **opencode in the terminal, DeepSeek running locally
as the HOST model driving TEE over MCP**, where TEE reported machine vision
as a feature it does not offer.

Design of record: `docs/research/66-senses-for-blind-models.md` (revised
edition). Inherits the A46/A35/A33 laws: measured before and after, no
capability lost, nothing claimed working that was not run.

---

## What the research established (all measured on this machine, 2026-08-31)

**TEE told the blind host the truth.** `tee_search_tools "describe what is
in an image, machine vision"` returns nothing that describes an image, and
two results advertise the opposite ("Pixel data is never returned").
Decision A9 makes the default extraction channel in-band — `ex_prepare`
hands the host file paths because *"it reads media with its own tools"* —
which assumed the host was Claude. `tee_media`/`tee_capture` return pixels,
useless to a blind host.

**The fix is already half-built, parked, and falsely advertised.**
`extract/vlm.py:158` contains a working `LocalVlmDriver` with
`caption_image` and `extract_document_page` on the local shim's Qwen3-VL.
`ex_prepare` even *reports* it — `"local_vlm_driver": "available (free,
on-machine)"` — but **no code path ever calls either method** (verified by
grep: zero invocations). A sign on a door with no door behind it.

**The providers work, measured:**

```
vision  qwen-vl reads an unguessable card exactly; 7.5 s on a 4K site
        frame, 2,065 local input tokens -> 63-token answer (33x, free)
context the VL model USES supplied context: given "drawings say gable G3
        is solid plastered", it answered the delta against the drawing
        spec in 4.0 s - so a sense call can carry the chore's context
audio   faster-whisper transcribes a spoken fixture VERBATIM:
        tiny 1.36 s / base 0.62 s, local, already in the extract extra
```

**The physics that must be priced:** on this 128 GB machine the 84 GB
session model and the 17 GB vision model cannot coexist (the owner's shim
hook proved it: 90 GB swap). An image request through the shim EVICTS the
session model; measured **~10.0 s per modality alternation vs 0.67–0.82 s
warm**. Borrowing vision while DeepSeek is the host costs the host a ~10 s
reload on its next turn. This is physics, not a bug — it must be stated in
every payload that incurs it, and batching must be the documented pattern.

**Trust:** `sense_*` has no family prefix, so an untabled sense tool is a
boot error — correct. Table the two names explicitly in `_EXPLICIT`
(A45's lesson: explicit tabling over family prefixes) on `read-extract`:
they read files and call 127.0.0.1; nothing mutates, nothing leaves the
machine.

---

## The law for A47

1. **Never silent.** Every sense answer names its provider, the fact that
   the asking model lacked the sense, and the swap cost if one was paid.
   The description says: *a description is a summary someone else wrote;
   the model reasoning over it never saw the pixels.*
2. **Refuse rather than improvise.** No provider -> a TeeError naming the
   exact fix. The failure this feature exists to kill is a confident
   answer about an image nobody looked at.
3. **Surface invariant holds:** 17 always-loaded tools / ~2,028 tokens.
   `sense_*` are VIRTUAL tools. Any always-loaded description edit must be
   token-neutral — measured before and after.
4. **No model weights in TEE's venv** (A46 P1). Providers are services
   TEE talks to, like ODM and Cube.
5. **Cache by exact content hash, never phash.** A near-duplicate's
   description is not this image's description — serving a cached card
   reading for a different card is precisely failure mode #2.
6. **A denial must teach.** Any refusal a first-contact host can hit
   (grants, senses, drivers) names the root cause and the owner's exact
   fix — the audit's lesson is that TEE was truthful but unteaching.
7. Local providers only by default; nothing here may route to a paid or
   off-machine engine, and `spend.py` must show `off_machine_calls: 0`
   for every sense call in the acceptance runs.

## P0 — declare the senses

Add sense-provider rows to `machine.ENGINES`: `qvl` (`senses:
["vision"]`, `footprint_gb: 17.0`, `evicts` naming the resident session
model, cost carrying the measured 7.5 s / 4.0 s), `whisper` (`senses:
["audio"]`, `footprint_gb: 0.5`, cost 0.62–1.36 s measured). Existing LLM
rows gain `senses: []` — the fact that dsflash/q27b are blind becomes a
declared fact. `tee doctor` gains a senses line: what this machine can
see and hear, and with what. Respect the one-profile-per-engine
uniqueness test (the A46 P3a lesson).
*Acceptance:* doctor names both providers with measured costs; suite green.

## P0.5 — the grantless host can find the door

The denial audit (research 66 addendum) showed the likely literal cause of
"denied access to all the tools": `serve --project` defaults to the
launching client's cwd, so a terminal host (opencode) boots from an
ungranted root and loses every mutation tier while the owner's grants sit
in `/Users/john/TEE/.tee/config.toml`. TEE never grants itself — the fix
is pure discoverability:

- `tee_status` states the loaded project root, the grants file path (or
  "none found"), and the granted/denied tier split in one compact block.
- `tee doctor` gains a first-contact check: serving from an ungranted
  root -> name the root, the file a grant would live in, and the two
  owner options (`--project /Users/john/TEE`, or a `[trust]` block here).
- `docs/` gains the terminal-host connection guide (opencode/DeepSeek):
  the launch line with `--project`, what works grantless, what needs
  grants.

*Acceptance:* a TeeApp at a fresh empty root reports its rootedness
honestly in status and doctor; nothing is auto-granted; suite green.

## P1 — `sense_describe` (drive the parked driver)

Virtual tool, explicit `_EXPLICIT` entry, `read-extract`. Args: `path`
(or an ingested source ref), `question`, optional `context` (proved to
work), `max_tokens` (default ~300, the token story is the answer text).
Rides `kernel/local_vlm.describe`. Returns the provenance block from
research 66: `answer`, `sense: "vision"`, `provided_by` (real model id),
`asked_of` omitted unless known, `cost` {provider_input_tokens if the shim
reports usage, answer_tokens, off_machine_calls: 0}, `swap_note` when the
call cold-started the VL server (wall time tells: >8 s cold vs <2 s warm —
measure and pick the real threshold), and the honesty `note`. Cache:
sha256(file bytes + question + context) -> answer, in `.tee` state;
`cached: true` on hits, provider untouched. HEIC works free via the
v0.11.0 `open_image` door — read bytes through it, never `open()` raw.
Refusals: absent file; unreachable shim (reuse `local_vlm`'s fix text);
oversized budget.
*Acceptance, all run live:* (a) `tee_search_tools "describe an image"` and
`"machine vision"` rank `sense_describe` top-3; (b) the unguessable-card
test passes THROUGH the tool with provenance naming qwen-vl; (c) second
identical call returns `cached: true` and the provider log shows one call;
(d) `report_spend` shows zero off-machine calls; (e) a `.heic` input
describes without conversion.

## P2 — `sense_transcribe`

Same shape, `sense: "audio"`, riding `extract/audio.py`'s existing
faster-whisper machinery (`extract_audio` / the WhisperModel pattern —
reuse, do not duplicate). Per-call model load is fine (0.8 s measured);
no sidecar. `model_size` arg defaulting to `base` (0.62 s, and the more
accurate of the two measured). Segments with timestamps opt-in;
default is the plain text, budgeted.
*Acceptance:* the spoken-fixture round trip verbatim through the tool;
refusal without the extract extra names `uv pip install
'tee-engine[extract]'`; search "transcribe audio" ranks it top-3.

## P3 — an extraction channel that works blind

`ex_prepare` gains `driver: "local"`: instead of handing the host file
paths it cannot read, TEE runs `LocalVlmDriver.caption_image` /
`extract_document_page` over the source's media AS THE JOB (async,
`tee_job` pollable — first VL call may pay the ~10 s swap), writes the
facts to the store exactly as `ex_store_facts` would, and returns the
compact fact summary. The packet's driver report stops advertising a
driver nothing can drive: each driver line now says HOW to invoke it.
In-band stays the default — a seeing host is still cheaper.
*Acceptance:* with `ANTHROPIC_API_KEY` unset, an image source extracts
end-to-end with the host never opening the file; facts land in the same
store shape as the in-band path; the A9 docstring is updated to name
three drivers.

## P4 — the pixel tools stop dead-ending blind hosts

`tee_media` and `tee_capture` descriptions gain the pointer: *"cannot
read images? sense_describe returns text."* Token-neutral: trim the same
description by at least as many tokens as added; measure the wire cost
before and after (`benchmarks` surface battery) and record both numbers.
*Acceptance:* surface still 17 tools and within ±10 tokens of 2,028.

## P5 — benchmark and record

`benchmarks/` gains an image-QA scenario: one question about one site
frame, (a) seeing host via `tee_media` pixels, (b) blind host via
`sense_describe`. Record tokens-per-task and wall time for both in
RESULTS.md — the 33x claim gets a reproducible number or gets corrected.
Re-measure the modality-alternation cost through the TOOL (not the raw
shim) and record the swap threshold chosen in P1.
*Acceptance:* RESULTS.md rows with real numbers; PROGRESS entry; version
bump + bundle; the extras trap note in the release text.

## Out of scope

Replacing or duplicating the owner's shim hook (it is the right transparent
bridge for Claude Desktop; TEE's job is to be callable and honest, not to
re-route). Serving an audio model on the shim. Diarization. Any paid or
off-machine sense provider. Batch scheduling of queued sense calls across
the swap (design sketched in research 66; build only if the measured
alternation cost in P5 says it matters for real workloads).
