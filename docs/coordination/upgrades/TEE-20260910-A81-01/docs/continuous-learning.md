# Local continuous learning

TEE learns small numerical models from observed work in each project. A trained
logistic model predicts the chance that an attempt passes its recorded check;
separate regression weights predict elapsed cost in log space. The weights
change as labelled observations accumulate. This is local supervised learning,
with no model download, cloud training call or foundation-model fine-tuning.

The loop covers registered tools throughout TEE, direct typed batches, background
job completion and the existing deterministic chore router. Fusion, Blender and
CADAgent lessons enter through those shared boundaries. It learns execution
patterns and reported quality; it does not autonomously rewrite a lesson,
change geometry, invent a verifier or expand its permissions.

## Use the five tools

Discover them with `tee_search_tools(query="continuous learning")`, then invoke
them through the existing `tee_call` tool. They add no always-loaded tools.

| Tool | Use |
|---|---|
| `learn_status` | Read storage health, active models, evaluation results and optional recent observation IDs. |
| `learn_feedback` | Attach one quality judgement to an existing observation. |
| `learn_recommend` | Rank 2–12 already-relevant registered tool alternatives using current evidence. |
| `learn_evaluate` | Fit and evaluate candidates now; promote only if every gate passes. |
| `learn_control` | Pause, resume or roll back learning. |

Start with a compact status call:

```python
tee_call(name="learn_status", args={"recent": 5})
```

`recent` accepts 0–20. A new project normally has no active model and zero
observations; reading status does not create a learning database. After carrying
out a task, use the returned observation's actual `event_id` for feedback:

```python
tee_call(name="learn_feedback", args={"event_id": observed_event_id, "success": True})
```

Report whether that result met the task requirements. A failed dimensional
inspection or an unsuitable material should receive `success=False` even if
the script ran successfully. Each retained observation accepts one feedback
entry; feedback cannot be attached to another feedback entry. An observation
that has aged out of the bounded store cannot receive new feedback.

For a Fusion API lookup where both indexed search and a known symbol's detail
are appropriate alternatives, a recommendation request looks like this:

```python
tee_call(name="learn_recommend", args={
    "candidates": ["fu_search_docs", "fu_api_detail"],
    "domain": "execution"
})
```

Only pass candidates that suit the task. They must be registered, enabled and
share an execution capability. The recommendation does not check whether they
solve the same problem. `domain="reported"` asks for the separately trained
caller-quality model. Predictions are advisory; the call executes no candidate
and supplies no permission to use one. With missing, sparse or stale evidence,
`applied=False` preserves the supplied order and gives a reason. A usable model
sorts by predicted reliability first, then predicted elapsed cost.

Evaluation and controls use the same surface:

```python
tee_call(name="learn_evaluate", args={})
tee_call(name="learn_control", args={"action": "pause"})
tee_call(name="learn_control", args={"action": "resume"})
tee_call(name="learn_control", args={"action": "rollback"})
```

These are independent examples. `pause` stops observations, fitting and learned
recommendations. `resume` re-enables the loop and clears a promotion pause.
`rollback` restores the previous usable model in each domain, or static fallback
when none exists, and pauses learning. Read `learn_status` before deciding to
resume. Feedback, evaluation and controls use the existing `write-state` trust
capability; status and recommendations are reads.

## What the labels mean

| Domain | Evidence | Meaning |
|---|---|---|
| `execution` | The execution boundary's outcome and elapsed time | Operational completion or failure. It does not certify task quality. |
| `verified` | An existing chore's deterministic validator | Acceptance by that particular check. A valid JSON shape can pass without establishing semantic correctness. |
| `reported` | Explicit feedback on an observation | Caller-reported task quality, kept separate from verifier evidence. |

Queued, cancelled, refused, skipped and unreachable attempts carry no passing
quality label. An arbitrary script returning `passed=True` cannot manufacture
a trusted verifier result. Check a CAD lesson's measured geometry or a texture's
intended appearance before supplying quality feedback.

The automatic decision change is deliberately narrow: calls already using
`tee.llm.router.route` may reorder currently eligible, unpinned local engines.
Existing model pins, capability checks, machine eligibility, verifiers and
fallbacks still govern execution. Some local chores call their model directly
and do not use that router. TEE-wide tool recommendations remain advisory.

## When a model becomes active

Ordinary observations trigger evaluation after 32 new labelled records per
domain, once enough data exists, with a five-second throttle between automatic
evaluations. No timer or daemon keeps work running while TEE is idle. A manual
`learn_evaluate` asks for an immediate bounded evaluation. When it has enough
data to complete an evaluation, it resets the automatic label/time watermark
too: another automatic fit needs 32 new labelled records and at least five
seconds after that evaluation.

Each candidate needs at least 64 training observations and 16 later held-out
observations. Related recorded groups stay together across the split, and the
training window keeps at most 512 observations without splitting a group.
Router retries share a group; unrelated top-level tool calls receive separate
groups. The client cannot infer that an entire multi-call design task was held
out merely because individual execution groups were separated.

The candidate must improve Brier loss by at least 0.01 against a constant
training-set success rate, avoid a log-cost error regression, and avoid
regression against the active model on the same held-out observations. Every
held-out context/choice/version needs at least six training observations.
Repeated evaluation needs fresh later groups. Insufficient evidence leaves the
current ordering in place; a completed evaluation does not imply promotion.

Recommendations also need exact support for every candidate and recent evidence.
A model or a candidate's latest labelled evidence older than 30 days causes
abstention. A rolling monitor compares the active model with its fixed baseline
on 16 later predictions. If Brier loss exceeds the baseline by more than 0.08,
it restores a previous model or static fallback and pauses promotion. This is
an operational drift heuristic, not a statistical guarantee.

`brier` is probability error and `cost_log_mae` is error in `log1p(elapsed_ms)`
(the natural logarithm of one plus elapsed milliseconds). Smaller values
describe better predictions on the reported observations;
they are not measured seconds or tokens saved on completed user tasks. Stored
token counts at generic tool boundaries estimate response size only. Router
attempts without measured token usage leave tokens unknown.

## Storage, settings and deployment

State is project-local at `.tee/learning/state.sqlite`, created lazily on the
first observation or state-changing control. SQLite retains at most 2,000
observations and six model snapshots across the three domains. It stores bounded
identifiers, version hashes, labels, times and scalar costs. It does not retain
prompts, scripts, outputs, scene dumps, file pointers, URLs or error messages in
the learning store. Other existing TEE logs have their own contracts.

Both settings default to `true`. If the owner chooses to override them, the
project configuration section is:

```toml
[learning]
enabled = true
auto_promote = true
```

`enabled=false` disables observation and learned recommendations.
`auto_promote=false` continues collecting and evaluating evidence while refusing
new promotions; it does not discard an already active model. Use `pause` when
the intent is to stop learned recommendations too. Configuration is loaded when
the app starts, so restart the server after changing these settings. The runtime
controls persist in the learning store without editing project configuration.

Existing server processes need a restart to load new learning code. A source
checkout uses the updated source when restarted; an installation from a wheel
needs a wheel containing these changes installed before restart. This guide
does not imply that an already-running or separately installed server has been
updated. The campaign leaves the owner's project configuration unchanged.

The algorithm, primary sources and measured campaign evidence are in
[research 81](research/81-continuous-learning.md); the implementation plan is
[A80](../CLAUDE_A80_SCRIPT.md).
