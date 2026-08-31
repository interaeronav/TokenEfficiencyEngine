# 66 — Senses for models that lack them: the modality bridge (2026-08-31)

> **Revised the same day, after the owner supplied the topology.** The first
> draft assumed DeepSeek was a chore engine *inside* TEE, reached through the
> LiteLLM shim. It is not. The owner's case is **opencode in the terminal,
> DeepSeek running locally as the HOST model, driving TEE over MCP** — and
> TEE told him machine vision was not a feature it offered. That is a
> different and more serious defect than the one first written up, and the
> shim findings below, while true, are about a path his case never takes.
> The root cause is in section "The actual defect (revised)".

Verification basis: everything below was measured on this machine today,
against the owner's own LiteLLM shim and local models. No claim here rests
on documentation or recall. The owner's ask, verbatim: *"a new feature for
tee which is machine vision and sound to allow models that don't have this
feature to be able to use machine vision and sound. my particular case is
with the deep seek model on my machine, it does'nt have vision."*

## The actual defect (revised)

**TEE's extraction architecture assumes the host model can see.** From
`extract/vlm.py`, decision A9, verbatim:

> *the DEFAULT driver is in-band: `ex_prepare` hands the host model file
> paths (**it reads media with its own tools**), a schema fragment and
> storing instructions; the host writes back via `ex_store_facts`.*

That was written when the host was always Claude. With a blind host, both
shipped drivers fail:

| driver | outcome with DeepSeek as host |
|---|---|
| in-band (default) | the host IS the model that cannot see |
| `ApiDriver` | needs `ANTHROPIC_API_KEY` — a paid cloud call, which defeats the point of running locally |

Meanwhile `kernel/local_vlm.py` — a working local vision client, free,
already measured at 7.5 s on a real site frame — is reachable from
**`web/media.py` and `web/tools.py` only**. It is never exposed as a tool
and never offered as an extraction driver.

**Reproduced from the host's side.** Asking TEE's own tool search
`"describe what is in an image, machine vision, look at a photo"` returns
`as_photo_material`, `med_instance_tags`, `med_volume_stats`, `ex_estimate`,
`quant_optimize`, `trade_backtest`. Nothing describes an image, and two
results advertise the opposite — *"Pixel data is never returned"*, *"Never
the voxel array"*. A blind host reading that surface correctly concludes
TEE offers no machine vision. **It was right.**

`tee_capture` and `tee_media` make it worse in a quiet way: both return
*pixels* (`tee_media`: "a small inline JPEG sized to max_tokens"). To a
seeing host that is the efficient answer. To a blind one it is a payload it
cannot read, spending tokens to deliver nothing.

**The fix is a third driver, not new machinery.** `LocalVlmDriver` on the
existing `local_vlm` client gives the in-band channel a fallback that is
local, free, and already written. Plus one plain tool — `sense_describe` —
so a blind host can ask for a description directly rather than being handed
pixels.

## Secondary finding: the shim already bridges vision (a path this case does not take)

**The vision bridge already exists, and the owner built it.** Not in TEE —
in the LiteLLM pre-call hook at `~/.claude/qwen-local/normalize_for_qwen.py`,
whose own docstring says:

> *Lazy vision: requests carrying images route to claude-qwen-vl; the VL
> server (17 GB resident) is only started when the first image arrives.*

Proved rather than assumed. A card was rendered reading `PLINTH K-4713 /
CURE 21 DAYS` — content no model could guess — and every route read it
back exactly:

```
claude-deepseek-flash   'PLINTH K-4713 CURE 21 DAYS'
claude-qwen-vl          'PLINTH K-4713 CURE 21 DAYS'
claude-qwen-27b         'PLINTH K-4713 CURE 21 DAYS'
```

`claude-qwen-27b` is a text-only checkpoint. It "read" the card because the
hook silently rerouted the request. **DeepSeek does not have vision; the
owner's system gives it vision without telling anyone.** The premise of the
request is right about the model and wrong about the system, and the reason
it is wrong is the feature TEE should add.

An earlier reading in this investigation was wrong and is recorded as such:
two models returned near-identical text and it looked like the image was
being ignored and hallucinated over. A different image (an orange office
chair, same question) produced a correctly different answer, which killed
that hypothesis. The identity probe then confirmed DeepSeek and Qwen-VL are
genuinely different models, not one backend behind two names.

## What the bridge actually costs

The hook cannot run both models at once, and says so:

> *DeepSeek (~84 GB in oMLX) + VL (17 GB) cannot share this machine
> (proved: 90 GB swap, pressure critical). Park oMLX first.*

So every image request **evicts the session model**. Measured as a real
alternating sequence:

```
1. text   (deepseek)              10.05 s     <- reload, evicted by an earlier image
2. IMAGE  (kills oMLX, uses VL)    2.59 s
3. image  (VL warm)                0.82 s
4. text   (reloads deepseek)      10.00 s     <- the swap back
5. text   (deepseek warm)          0.67 s
```

**Warm, same modality: 0.67–0.82 s. A modality switch: ~10 s.** Roughly a
15x penalty, paid on every alternation. A task that goes text → image →
text → image pays it four times: ~40 s of pure swapping, invisible in every
individual response.

TEE has a `MachineLedger` built precisely to reason about residency and
swap cost — `may_swap`, `record_swap`, `footprint_gb`, a refusal path while
a registered job holds the machine. It is not consulted here, because
nothing in TEE knows this swap exists.

## The token case, which is the stronger one

A vision bridge is usually argued as a capability. On TEE's own metric it
is better argued as compression. Measured on an Okongo drone frame:

```
image into qwen-vl        2,065 input tokens   (local, free, unmetered)
text answer handed back      63 output tokens
```

**33x**, and the 2,065 tokens are spent on a model that bills nothing. This
is the same shape as the existing lanes: `extract/audio.py` already states
*"Claude has no audio input — local transcription is the ONLY channel"*,
and `kernel/local_vlm.py` already states *"a viewport question answered
here costs the host model only the answer text (tens of tokens)"*. The
pattern has been implemented twice for two specific gaps. It has never been
made general.

## What is genuinely missing

1. **No engine declares its senses.** `machine.ENGINES` gives every LLM
   `capability: ["chores"]`. Nothing records that `dsflash` is blind,
   that `qvl` can see, or that nothing on this machine hears. The router
   cannot make a modality-aware decision because there is nothing to
   decide on.

2. **The bridge is silent, which is why the owner did not know it existed.**
   An answer from `claude-deepseek-flash` about an image did not come from
   DeepSeek. Nothing in the response says so. This session has spent its
   whole length on provenance — a chore that reports which engine answered,
   an ODM run that reports how many images reconstructed — and this is the
   same defect: a result whose true source is unstated.

3. **The ~10 s swap is unpriced.** It does not appear in any cost table,
   any ledger entry, or any answer. A caller cannot know that reordering
   two requests would save ten seconds.

4. **There is no audio bridge at all.** No audio model is served on the
   shim. `faster-whisper` is installed and works — measured, against speech
   whose content was known in advance:

   ```
   spoken:  "The gable brickwork is complete but the roof sheeting has
             not been installed."
   tiny  1.36 s  'The Gable brickwork is complete, but the roof sheeting
                  has not been installed.'
   base  0.62 s  'The gable brick work is complete, but the roof sheeting
                  has not been installed.'
   ```

   Verbatim, sub-second, local. But it is reachable only from inside the
   extract lane's ingest path, not as a sense a chore can call.

## Proposed design — `sense`, a kernel-level modality bridge

**One idea: a model's senses are declared, and a missing sense is borrowed
from a local provider, out loud.**

### Declare the senses

Extend `machine.ENGINES` so capability carries modalities, and add
providers as first-class engine rows:

```python
"dsflash":  {"capability": ["chores"], "senses": []},
"q27b":     {"capability": ["chores"], "senses": []},
"qvl":      {"capability": ["chores", "sense-vision"], "senses": ["vision"],
             "footprint_gb": 17.0, "evicts": ["dsflash"]},
"whisper":  {"capability": ["sense-audio"], "senses": ["audio"],
             "footprint_gb": 0.5},
```

`evicts` is the fact the hook already knows and TEE does not: on a 128 GB
machine an 84 GB session model and a 17 GB vision model are mutually
exclusive. Declaring it lets `MachineLedger.may_swap` price a modality
switch the same way it already prices an engine swap.

### Borrow the sense

`sense_describe(path, question)` and `sense_transcribe(path)`: media in, a
budgeted text fact out, always carrying its provenance —

```json
{ "answer": "Stepped solid-brick gable, plastered walls, no roof sheeting.",
  "sense": "vision",
  "provided_by": "qvl (Qwen3-VL-30B-4bit, local)",
  "asked_of": "dsflash, which has no vision",
  "cost": {"provider_input_tokens": 2065, "answer_tokens": 63,
           "off_machine_calls": 0, "swap_s": 10.0},
  "note": "A description, not the image. The model reasoning about this
           never saw the pixels." }
```

The last line is the honest part. A description is lossy in ways the reader
cannot see, and a model reasoning over one is reasoning over a summary
someone else wrote. Saying so is the difference between a bridge and a
disguise.

### Batch across the swap

The ~10 s penalty is per *alternation*, not per image. So the scheduler's
job is to group: answer every pending vision question while VL is resident,
then switch back once. This is exactly what `MachineLedger` exists for, and
it converts a 4-alternation task from ~40 s of swapping to ~10 s.

### Refuse rather than guess

If no provider for a sense is available, `sense_*` refuses with the install
line — it never falls back to letting a blind model improvise. The failure
mode this feature exists to prevent is a confident answer about an image
nobody looked at.

## What NOT to build

- **Not a vision model in TEE's venv.** A46 P1 cut the venv from 2.2 GB to
  586 MB by moving weight out. A 17 GB model goes nowhere near it; the
  provider is a service TEE talks to, exactly as ODM and Cube are.
- **Not a replacement for the shim hook.** The hook works and is the right
  place for transparent routing. TEE's job is to *know* about it, price it,
  and say so — not to duplicate it.
- **Not silent rerouting.** That is the defect, not the feature.

## Open questions for the build

1. Does the hook's reroute preserve enough of the original prompt for the
   answer to be useful, or does the VL model lose the chore's context?
   Untested.
2. Whisper is installed but unserved. Serve it (a small always-resident
   0.5 GB sidecar) or spawn per call? Its 0.62 s warm time suggests a
   sidecar is not needed.
3. Can `sense_describe` cache by content hash? The same frame asked twice
   costs 2,065 tokens twice today. `phash` dedupe already exists in
   `extract/images.py`.

## Addendum (same day): the full denial audit for a local host

The owner asked what ELSE denies a local host model access to TEE's tools.
Audited live, not from memory. Five classes found, one suspected class
cleared.

**Class 1 — the grantless root (almost certainly the owner's literal
experience).** `tee serve --project` defaults to `.`, the launching
client's cwd. The owner's grants (`workstation` profile) live in
`/Users/john/TEE/.tee/config.toml` — the Desktop project. An opencode
connection that does not pass `--project /Users/john/TEE` boots from an
ungranted root. Probed with no grants, caller live-turn:

```
read-scene / read-extract / read-compute / write-state   ALLOWED
exec-code  mutate-scene  run-declared-step  run-adhoc    denied
call-service  call-paid-engine  place-order              denied
```

So a terminal host keeps reads and memory but loses **the entire mutation
surface** — `tee_batch` mutations, `tee_script`, pipelines, service calls.
Combined with class 2 (no way to see media), "TEE denies access to all the
tools" is a fair user-level summary of what DeepSeek experienced. This is
the A43 kernel working as designed — the gap is *discoverability*: nothing
tells a first-contact host which root was loaded, which file grants would
come from, and what one line would fix it. TEE must never grant itself
(A45 law), but it can say precisely where the owner grants.

**Class 2 — in-band media homework** (the A9 family, core of this doc):
`ex_prepare` hands file paths; `tee_media`/`tee_capture` return pixels;
`extract/images.py` contact sheets are labeled IMAGES to look at; the
FreeCAD adapter returns base64 previews. All dead ends for a blind host.
Notably the UE lane already solved this for itself — `adapters/unreal/
vision.py` answers viewport questions through `local_vlm`, "costs the host
model only the answer text". **The borrowed-eye pattern now counts three
prior implementations** (web, UE, and the parked extract driver); A47
generalizes what three lanes each built privately.

**Class 3 — the only cloud escape is Anthropic-shaped.** `ApiDriver`
requires `ANTHROPIC_API_KEY` + the `anthropic` sdk — the sole off-session
extraction path assumes the host's vendor. (A47 P3 fixes this with the
local driver; no other `import anthropic` exists in the tree.)

**Class 4 — image token budgeting assumes Claude's tokenizer.**
`extract/images.py` prices every image at `ceil(w/28) x ceil(h/28)` —
PATCH=28 is Claude's patch economics. Budgets handed to a *seeing*
non-Claude host are mis-calibrated. Minor today (the blind host never gets
that far); worth one honest line in the budget notes.

**Class 5 — guidance delivery assumes the client shows MCP instructions.**
TEE's epoch/diff discipline rides the server `instructions` block; clients
that do not surface it (terminal hosts vary) leave the host without the
"track (epoch, revision), prefer tee_diff" contract. Tool descriptions must
carry enough to survive an instructions-blind client.

**Cleared — consent is host-agnostic.** Suspected that consent flowed from
a Claude-only UI. It does not: consent is expressed in-band (`_consent` in
config, or an explicit TEE/Q switch phrase counting as the owner asking).
No denial class here; recorded so it is not re-suspected.
