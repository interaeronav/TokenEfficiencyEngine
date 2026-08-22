---
name: tee-usage
description: Drive Blender/Unreal through the TEE MCP server with minimal tokens - the macro-first, diff-based operating procedure. Use whenever a TEE server (tee_* tools) is connected and you are building, editing, furnishing, or verifying a 3D scene.
version: 1.0
license: MIT
---

# Using TEE

TEE's whole point is tokens-per-completed-task. The server enforces most
of it (budgets, diffs, shortlists); this skill is the operating
procedure that keeps YOU from working against it.

## Session shape

1. **Start**: `tee_recall` (project memory) and, if the host evicted
   older context, `tee_status(recap=true)` — a ≤500-token resume built
   from server state. Never re-ask the user what the server remembers.
2. **Read**: `tee_scene_summary` with filters/paging; `tee_entity_detail`
   for ONE entity; `tee_diff(epoch, revision)` for "what changed" —
   track the stamps from every response instead of re-reading scenes.
3. **Write**: `tee_batch` — N ops in one call, auto-checkpointed,
   answers with the diff. Never one op per call.
4. **End**: `tee_remember` durable facts (versions, conventions,
   decisions) so the next session starts warm.

## The macro-first rule

Any loop whose intermediate results you will not quote back — check ⇢
fix ⇢ recheck, iterate over entities, poll-and-adjust — goes in ONE
`tee_script` call. Its intermediate tool results never enter context
(measured: 63–76% saved on conformance fix loops, growing with loop
length). Reach for separate calls only when each step needs your
judgment on the previous step's output.

## Finding capability

The 16 always-loaded tools are the kernel. Everything else (~68 virtual
tools) is behind `tee_search_tools` → `tee_describe_tool` → `tee_call`:
`ex_*` extraction, `as_*` assets, `gd_*` design, modeling/physics
(`wall_with_openings`, `sim_settle`, `plaus_check`, `mat_assign`),
`uefn_*`. Search by capability words ("bake physics", "asset search",
"verse lint") — don't guess names.

## Text before pixels

Order of evidence: cached facts (`ex_facts`, `ex_search`) → geometric
checks (`as_verify`, `phys_tier0`, `bl_check_against_plan`) → ONE
budgeted `tee_capture` (max_kb small) only for a genuinely visual
question. A screenshot is ~500–2,700 tokens; a geometric assertion is a
few dozen. `tee_media` serves budgeted crops of ingested sources — facts
about the media are cheaper still.

## Trust the gates, relay the fixes

Structured refusals are design, not failures — do not retry around
them, and never ask the user to override what has no override:

- `license_blocked` (assets) and ethics `code` rows (design) are
  final. Pick another asset / design without the pattern.
- Scale-policy `reject`, placement `code` violations, `stale_api`
  firewall hits, `cost_confirmation_required`: each answer names the
  exact fix — apply it.
- Checkpoints are cheap and automatic; `tee_rollback` beats manual
  cleanup after a wrong turn.

## Honesty rules that flow through you

Report what the tools report: "rest-stable under settle", never
"structurally sound"; plausibility findings are findings, not
approvals; benchmark answers carry sources — quote them, don't round
them into folk wisdom.
