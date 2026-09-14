# GPT-6 — review W1: the thinking engine has never had a thinking budget

**Revision 1, 2026-09-14.** Prepared by Claude for the owner to hand to
GPT-6 / Codex. Repository: `/Users/john/TokenEfficiencyEngine`.
Protocol: `docs/upgrade-coordination-protocol.md`, version 1.0.1.

**This is a proposal, not a candidate.** No source is edited, no commit is
frozen, no package is built. W0 (`e6f9566`) remains the installed and accepted
runtime on both clients and is untouched by anything here. I am asking for a
review of the diagnosis and the proposed shape **before** writing code, because
the change lands in the frozen W0 payload and would otherwise arrive as a
surprise runtime candidate.

## 1. The finding, in one line

Every TEE chore that reasons runs on a budget measured for chores that do not,
and `rerank` is truncated on **100% of inputs**.

## 2. Two defects, and the second explains the first

### [P1] Per-chore caps do not cover thinking

Measured on the owner's Mac, 2026-09-14: seven chores, **five genuinely
different inputs each**, thinking on, against the 8-bit 27B through the shim,
recording real `usage.completion_tokens` via TEE's own `on_usage` hook.

| chore | effective budget | observed spread | max | truncated |
|---|---:|---|---:|---:|
| `rerank` | 256 | 299 – 496 | 496 | **5/5** |
| `repair_script` | 500 | 100 – 698 | 698 | 1/5 |
| `structure_facts` | 500 | 279 – 574 | 574 | 1/5 |
| `phrase_deviation` | 400 | 330 – 477 | 477 | 1/5 |
| `explain_lint` | 256 | 90 – 265 | 265 | 1/5 |
| `refine_extract` | 500 | 175 – 443 | 443 | 0/5 |
| `compress_recap` | 256 | 108 – 142 | 142 | 0/5 |
| `triage` | 220 | 86 | 86 | 0/5 |

"Effective budget" is `max(literal_cap, min_chore_tokens)`, and
`min_chore_tokens` resolves to the default **256** for every profile this
machine declares (§2b).

A truncated chore does not degrade quietly - it raises `llm_no_answer`, the
W0 code added for exactly this, after paying its full generation time. So the
current caps buy nothing and cost the whole call.

### [P2] The floor instrument cannot measure the mode that needs it

`min_chore_tokens` is the lever the design intends; `machine.py` says so:
*"A floor is a property of a model's appetite for thinking, so it belongs on
the model's row."* It cannot reach these chores, for two independent reasons.

**(a) The profiles have no `ENGINES` row.** `min_chore_tokens('27b')` and
`('27b4bit')` both return 256. `ENGINES` is payload-only - there is no config
overlay, unlike `[llm.profiles.*]`. The only row carrying a real floor is
`q35b` at 1024, whose model was deleted; the code already notes it "has never
once been reached."

**(b) `eng_audition` only ever measures thinking OFF.** Run against the 8-bit:

```json
{"engine":"q27b-think","thinking":false,"min_chore_tokens":64,
 "floor":{"passed":[1024,512,384,256,192,128,96,64],"first_failure":null,
          "bound":"at-or-below"}}
```

It sweeps `triage`, and `triage` pins thinking off. `audition.py` states it:
*"It calls the chore layer without a `thinking` argument, so it inherits the
chore default: OFF."* `matching_floors` then correctly refuses to apply that
measurement to a thinking-on request: *"A floor measured with thinking off does
not describe the same engine with thinking on - reasoning consumes the budget
the floor is about."*

**The mechanism is sound and the instrument covers one mode.** No measured
floor can reach a thinking-on chore today. That is the root cause of [P1], and
fixing only the caps would leave the instrument still blind.

## 3. Proposed change

Three parts. I have written none of them.

1. **Three cap tiers**, each at least 1.8x the observed max:
   `compress_recap` and `explain_lint` -> **512**; `refine_extract`,
   `structure_facts`, `rerank`, `phrase_deviation` -> **1024**;
   `repair_script` -> **1536**. `triage` unchanged at 220 - it pins thinking
   off and the project measured thinking making it worse there (5/6 vs 6/6).
2. **An `ENGINES` row per served 27B profile**, so a floor can attach at all.
3. **`eng_audition` sweeps both modes** and records the mode on the row, so the
   thinking floor becomes measurable rather than asserted. This is the part
   that stops the defect recurring; (1) is the symptom.

**Why raising a cap is close to free.** A cap is a ceiling, not a spend -
generation stops at EOS. The median path is unchanged; only runs that truncate
today behave differently, and those currently pay full time and then fail.

**The cost that is real.** Worst-case wall time rises with the ceiling: at the
observed ~40 tok/s, 1024 tokens is ~26 s and 1536 ~38 s. Both sit inside
`complete_json`'s 120 s timeout, but a chore runs inside `app.lock`, which
serialises every other tool call, on a server running `--scheduler-mode serial`.
**A bound on blocking is the thing being traded, and it deserves your view.**

## 4. What I did NOT do, and one thing I nearly got wrong

- No source edited, no commit, no build, no install, no client restart.
  `eng_adopt` was not run; it only prints a line to paste in any case.
- **The first measurement was wrong and is discarded.** Five repetitions of one
  prompt returned five identical token counts - the backend returns the same
  generation for the same prompt, so it was one sample counted five times.
  Perturbing the input moved `structure_facts` from 505 to 505-747. Every
  number in §2 comes from the corrected run with five distinct inputs.
  `variance_check.py` reproduces the distinction.
- **Sample size is five inputs per chore.** The "max" column is the largest of
  five, not a maximum. The tier headroom is what covers the gap, and I would
  rather you judge that than have me imply a bound I did not measure.
- Measured on the 8-bit only. The 4-bit is a different quantisation and may
  reason at a different length; I did not check.

## 5. Questions I would like answered before writing code

1. Are three tiers the right shape, or should each chore carry its own measured
   literal? Tiers are easier to defend and harder to keep true.
2. Should the thinking floor live on the `ENGINES` row (payload, reviewed) or
   become config-overridable like `[llm.profiles.*]` and `[senses]`? The latter
   would have let this be fixed today without touching a frozen candidate.
3. Is a ~38 s worst case acceptable inside `app.lock`, or should the fix bound
   blocking directly - a shorter chore timeout, or moving inference off the
   lock - with the caps sized to that instead?
4. Does `eng_audition` sweeping both modes belong in this change or its own?

## 6. Reproduction

```sh
cd /Users/john/TokenEfficiencyEngine/server
PYTHONPATH="$INSTALLED_SRC:$PWD/src" .venv/bin/python \
  ../docs/coordination/upgrades/TEE-20260914-W1-PROPOSAL/measure_chore_demand.py
```

Raw results: `measured-chore-demand.json`. The variance check that invalidated
the first attempt: `variance_check.py`.

## 7. Scope

Nothing was installed, restarted, re-targeted, dependency-synced, downloaded,
pushed or released. W0 `e6f9566` / `df974f78...a90b7` remains the accepted
runtime with both clients' functional evidence returned. Any candidate arising
from this proposal is a new identity requiring its own review, and completion
would still require receipts from both actual clients under protocol 1.0.1.
