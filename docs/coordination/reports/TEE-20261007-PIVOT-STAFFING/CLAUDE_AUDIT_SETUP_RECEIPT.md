# Claude audit-team setup receipt — TEE pivot

Verified: 2026-10-07T05:27:57Z (UTC, from the clock). Executed from `CLAUDE_AUDIT_TEAM_SETUP.md` by the existing Claude Code chat acting as setup coordinator only.
Registry: [`claude-audit-sessions.json`](claude-audit-sessions.json).

**Superseded result line follows; current state is in “Desktop sessions”. Result (updated 2026-10-07T05:32:57Z): 8 definitions on the 5.5 models, 8 active sessions READY on 5.5, 0 BLOCKED; the 8 original 5.0 sessions were deleted with `claude rm` at 2026-10-07T05:36:22Z on owner instruction.** Standby only — no audit, implementation, acceptance or release is assigned or claimed.

## Desktop sessions, renamed to match the Codex peers (2026-10-07T05:45:10Z)

Owner instruction: the auditors must be visible in, and run from, the Claude desktop app. CLI background sessions never appear in the desktop sidebar.

- Imported each 5.5 CLI session with the desktop app's own deep link `claude://resume?session=<uuid>`. Each became desktop session `local_<uuid>` with the same transcript, keeping its model.
- Renamed each to its Codex peer's title + ` · Claude Audit`, using the app's session-title tool. An in-place CLI `/rename` was tried on WS0 first: it reverted when the session woke with its saved `--name`, so it was abandoned.
- Set effort and plan mode per session, and filed all eight under the sidebar section “TEE Pivot — Claude Audit” (`cg-1ac8ffda-5db8-46ce-8dcd-9f70899eeac7`).
- The desktop app does not apply the CLI `--agent` system prompt. Each session was therefore asked to read its own definition file once and reply READY. Every transcript shows exactly one `Read` of that file, the pinned model and effort, and READY. All eight file hashes were re-verified here. WS3 and WS6 noted that they couldn't hash the file themselves with Read alone.
- The CLI background copies were stopped before import and are not running.
- 2026-10-07T05:50:40Z: on owner instruction, the eight stopped CLI background entries were deleted with `claude rm`. The transcripts were backed up first and afterwards compared byte-identical: the desktop sessions share them and were unaffected.

| WS | Desktop title | Codex peer (thread) | Desktop session | Model / effort observed | Status |
|---|---|---|---|---|---|
| WS0 | TEE Pivot — WS0 Scope and Baseline · Claude Audit | TEE Pivot — WS0 Scope and Baseline (`01a114c8-a1a6-7c81-a4a6-cd6dd4e02f98`) | `local_4f7015c5-bc48-469d-b787-2d3fbc94a42a` | claude-sonnet-5-5 / medium | READY |
| WS1 | TEE Pivot — WS1 Protocol and Supply Chain · Claude Audit | TEE Pivot — WS1 Protocol and Supply Chain (`01a114c8-a57d-7c62-b3b4-5dafa0cb1c15`) | `local_c0730186-c6c1-4065-a440-4856e9707a7e` | claude-opus-5-5 / high | READY |
| WS2 | TEE Pivot — WS2 Benchmark and Metering · Claude Audit | TEE Pivot — WS2 Benchmark and Metering (`01a114c8-ac5b-7802-804b-4a13c9d4dab0`) | `local_aa98fecf-abb3-4408-b028-29951176d9bd` | claude-sonnet-5-5 / high | READY |
| WS3 | TEE Pivot — WS3 Code Verification and Memory · Claude Audit | TEE Pivot — WS3 Code Verification and Memory (`01a114c8-b90a-7680-a403-d0fc53be5b58`) | `local_52ea5d4c-825f-4c13-9e60-ed85bc81fa6b` | claude-opus-5-5 / high | READY |
| WS4 | TEE Pivot — WS4 Undo Policy and Audit · Claude Audit | TEE Pivot — WS4 Undo Policy and Audit (`01a114c8-c783-7c41-8946-1d9cfa79baf2`) | `local_0444e920-49e9-439d-841c-66f5661e10bc` | claude-opus-5-5 / high | READY |
| WS5 | TEE Pivot — WS5 Blender and Unreal Pro · Claude Audit | TEE Pivot — WS5 Blender and Unreal Pro (`01a114c8-d06c-7e40-93f1-45b7ca878553`) | `local_20f8467e-8d48-4457-988c-0b8bf9f2b4ea` | claude-sonnet-5-5 / high | READY |
| WS6 | TEE Pivot — WS6 Revit MATLAB and Fusion · Claude Audit | TEE Pivot — WS6 Revit MATLAB and Fusion (`01a114c8-daa0-79f0-9cc5-410a3164e4f6`) | `local_a5124cec-e823-499c-a970-6fe0b9f21fde` | claude-opus-5-5 / high | READY |
| WS7 | TEE Pivot — WS7 Licensing and Distribution · Claude Audit | TEE Pivot — WS7 Licensing and Distribution (`01a114c8-e300-7542-81bc-94e732acf3e1`) | `local_c70da1ed-85bf-41ee-97f8-b3af26ff0ece` | claude-sonnet-5-5 / medium | READY |

The Codex titles stored for WS1 and WS3 are cut off with “…” in Codex (see below); the Claude titles use the full intended names.

## Labels checked against the Codex peers (2026-10-07T05:38:00Z)

Each live Claude title (`claude agents --json --all`) is `TEE Pivot — Audit WS<n> <topic>`, using the Codex peer's topic word for word. All eight match the Codex titles in `sessions.json` and PLAN.md's naming rule; WS numbers line up 1:1 with the Codex thread IDs there.

On the Codex side, the stored thread names for two peers are cut off (read-only from `~/.codex/state_5.sqlite` and `session_index.jsonl`; not modified):
- WS1 `01a114c8-a57d-7c62-b3b4-5dafa0cb1c15`: “TEE Pivot — WS1 Protocol and Supply…” (intended “…Supply Chain”)
- WS3 `01a114c8-b90a-7680-a403-d0fc53be5b58`: “TEE Pivot — WS3 Code Verification and…” (intended “…and Memory”)

Renaming them is for the Codex coordinator or the owner, in Codex.

## Model update to 5.5 (owner, 2026-10-07: “use latest 5.5 models”)

- The Homebrew cask `claude-code` was upgraded from 2.1.267 to **2.1.285**, which meets the ≥2.1.284 requirement for Sonnet 5.5 (Opus 5.5 needs ≥2.1.280). The desktop app's bundled clients were not touched. This is a CLI update. The upgrade-coordination protocol covers TEE extension/runtime upgrades, so it does not apply here; the earlier setup reply said otherwise, and that was wrong.
- The definitions' `model:` field is now `claude-opus-5-5` / `claude-sonnet-5-5`. Effort levels are unchanged.
- How the sessions moved: `claude stop <old id>`, then `claude --bg --resume <old uuid> --agent … --name … --model <5.5 id> --effort … --permission-mode plan "<model-update ack prompt>"`. The client keeps a background session's saved options, so new flags start a **copy carrying the full conversation** under a new id; the client printed that note for each one. For WS2, WS5 and WS7 it said the original was still running when the copy started. All eight originals then showed as `stopped` with no live process. On owner instruction they were then deleted with `claude rm <id>` (2026-10-07T05:36:22Z); `claude agents --json --all` no longer lists them, and the 5.5 sessions were unaffected. Their eight transcript files were then moved to `~/.Trash/tee-pivot-audit-5.0-transcripts-20261007T053707Z/` (2026-10-07T05:37:13Z), also on owner instruction; emptying the Trash is the owner's step.
- Evidence: in each copy's own transcript, the latest assistant turn has `model` = the pinned 5.5 ID, the requested effort and zero tool calls.

| WS | Agent | Session title | Bg id | Session UUID | Requested model / effort | Observed model / effort | Status | Superseded 5.0 session (deleted) |
|---|---|---|---|---|---|---|---|---|
| WS0 | `tee-pivot-audit-ws0` | TEE Pivot — Audit WS0 Scope and Baseline | `4f7015c5` | `4f7015c5-bc48-469d-b787-2d3fbc94a42a` | claude-sonnet-5-5 / medium | claude-sonnet-5-5 / medium | READY | `bd79003c` (deleted) |
| WS1 | `tee-pivot-audit-ws1` | TEE Pivot — Audit WS1 Protocol and Supply Chain | `c0730186` | `c0730186-c6c1-4065-a440-4856e9707a7e` | claude-opus-5-5 / high | claude-opus-5-5 / high | READY | `5452d6c5` (deleted) |
| WS2 | `tee-pivot-audit-ws2` | TEE Pivot — Audit WS2 Benchmark and Metering | `aa98fecf` | `aa98fecf-abb3-4408-b028-29951176d9bd` | claude-sonnet-5-5 / high | claude-sonnet-5-5 / high | READY | `4999a8e9` (deleted) |
| WS3 | `tee-pivot-audit-ws3` | TEE Pivot — Audit WS3 Code Verification and Memory | `52ea5d4c` | `52ea5d4c-825f-4c13-9e60-ed85bc81fa6b` | claude-opus-5-5 / high | claude-opus-5-5 / high | READY | `28dae72f` (deleted) |
| WS4 | `tee-pivot-audit-ws4` | TEE Pivot — Audit WS4 Undo Policy and Audit | `0444e920` | `0444e920-49e9-439d-841c-66f5661e10bc` | claude-opus-5-5 / high | claude-opus-5-5 / high | READY | `468db7e4` (deleted) |
| WS5 | `tee-pivot-audit-ws5` | TEE Pivot — Audit WS5 Blender and Unreal Pro | `20f8467e` | `20f8467e-8d48-4457-988c-0b8bf9f2b4ea` | claude-sonnet-5-5 / high | claude-sonnet-5-5 / high | READY | `5e0bbed1` (deleted) |
| WS6 | `tee-pivot-audit-ws6` | TEE Pivot — Audit WS6 Revit MATLAB and Fusion | `a5124cec` | `a5124cec-e823-499c-a970-6fe0b9f21fde` | claude-opus-5-5 / high | claude-opus-5-5 / high | READY | `9c08e714` (deleted) |
| WS7 | `tee-pivot-audit-ws7` | TEE Pivot — Audit WS7 Licensing and Distribution | `c70da1ed` | `c70da1ed-85bf-41ee-97f8-b3af26ff0ece` | claude-sonnet-5-5 / medium | claude-sonnet-5-5 / medium | READY | `34a3d58e` (deleted) |

### 5.5 readiness acknowledgements

- WS0 (`4f7015c5`, 2026-10-07T05:31:16+00:00): “READY — WS0 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`
- WS1 (`c0730186`, 2026-10-07T05:32:09+00:00): “READY — WS1 — awaiting an admitted frozen phase handoff” — tool calls 0; client status `idle` / state `blocked`
- WS2 (`aa98fecf`, 2026-10-07T05:32:10+00:00): “READY — WS2 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`
- WS3 (`52ea5d4c`, 2026-10-07T05:32:12+00:00): “READY — WS3 — awaiting an admitted frozen phase handoff” — tool calls 0; client status `idle` / state `blocked`
- WS4 (`0444e920`, 2026-10-07T05:32:15+00:00): “READY — WS4 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`
- WS5 (`20f8467e`, 2026-10-07T05:32:18+00:00): “READY — WS5 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`
- WS6 (`a5124cec`, 2026-10-07T05:32:21+00:00): “READY — WS6 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`
- WS7 (`c70da1ed`, 2026-10-07T05:32:25+00:00): “READY — WS7 — awaiting an admitted frozen phase handoff.” — tool calls 0; client status `idle` / state `blocked`

### Current definition hashes

- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws0.md` — sha256 `5183229db205f8bcb71e28c1c4fcec4c4a2dddc3c4636814a0ec4daebb277940` (5.0 version was `8074d094d2902d9b…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws1.md` — sha256 `68445601b07d0ff1fb4e20ec2b155aeb17927d3926ace12c0dc93b3423e58079` (5.0 version was `2349adff83d4ab98…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws2.md` — sha256 `4e44ae2c05c6107508f2b4b8da8bb973304b6731308f5af687c7d4f7de5b67e4` (5.0 version was `d9854ecf0d5a9e1f…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws3.md` — sha256 `e7c2333cb4b4002602ef0996a12c5c506c79f28773334dd0015d635b972ca81b` (5.0 version was `df481ff5c5c0049c…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws4.md` — sha256 `c49caaa962a2232a735e3c12d88ede15cfe41ea8838e85d1800e85645bab1a7e` (5.0 version was `457bd601c1931454…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws5.md` — sha256 `f3d1d77e968d4f66276961828ac76cd206cc241404f10a19de7cbd40c2d44f22` (5.0 version was `85fc02c455ae2f6d…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws6.md` — sha256 `231cc7048794621240123654da7042e0ab0d9b7bd3a05ffa231fcde557142fce` (5.0 version was `ffdb91e134c45e24…`)
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws7.md` — sha256 `102f84eca8f3409c22d7f5ba59df5d04c624251c3ce989b8928713c3863df506` (5.0 version was `52f9e267b8ee2a6b…`)

### Attach / resume (current)

- WS0: `claude attach 4f7015c5` · `claude --resume 4f7015c5-bc48-469d-b787-2d3fbc94a42a`
- WS1: `claude attach c0730186` · `claude --resume c0730186-c6c1-4065-a440-4856e9707a7e`
- WS2: `claude attach aa98fecf` · `claude --resume aa98fecf-abb3-4408-b028-29951176d9bd`
- WS3: `claude attach 52ea5d4c` · `claude --resume 52ea5d4c-825f-4c13-9e60-ed85bc81fa6b`
- WS4: `claude attach 0444e920` · `claude --resume 0444e920-49e9-439d-841c-66f5661e10bc`
- WS5: `claude attach 20f8467e` · `claude --resume 20f8467e-8d48-4457-988c-0b8bf9f2b4ea`
- WS6: `claude attach a5124cec` · `claude --resume a5124cec-e823-499c-a970-6fe0b9f21fde`
- WS7: `claude attach c70da1ed` · `claude --resume c70da1ed-85bf-41ee-97f8-b3af26ff0ece`

---

## Original setup record (5.0, client 2.1.267) — superseded

## Client and model profile

- Installed client: `/opt/homebrew/bin/claude` → Caskroom `2.1.267` (Claude Code). Local help confirms `--bg`, `--agent`, `--name`, `--model`, `--effort`, `--permission-mode plan`, `agents --json --all`, `logs`, `attach`.
- 2.1.267 falls in the script's 2.1.267–2.1.283 band, so Opus roles are pinned to `claude-opus-5` and Sonnet roles to `claude-sonnet-5`. The client was not updated; PLAN.md's recommended 5.5 models need ≥2.1.284 and were not used.
- Each session was pinned individually; global defaults and the coordinator's model are unchanged. No Max/Ultra, escalation, local models or subagents.

## Sessions

| WS | Agent | Session title | Bg id | Session UUID | Requested model / effort | Observed model / effort | Status |
|---|---|---|---|---|---|---|---|
| WS0 | `tee-pivot-audit-ws0` | TEE Pivot — Audit WS0 Scope and Baseline | `bd79003c` | `bd79003c-0210-4963-8894-2a48d4687bfc` | claude-sonnet-5 / medium | claude-sonnet-5 / medium | READY |
| WS1 | `tee-pivot-audit-ws1` | TEE Pivot — Audit WS1 Protocol and Supply Chain | `5452d6c5` | `5452d6c5-58f3-4506-a305-0d6ff1582184` | claude-opus-5 / high | claude-opus-5 / high | READY |
| WS2 | `tee-pivot-audit-ws2` | TEE Pivot — Audit WS2 Benchmark and Metering | `4999a8e9` | `4999a8e9-2b0a-4f3c-98cc-b0190b35897a` | claude-sonnet-5 / high | claude-sonnet-5 / high | READY |
| WS3 | `tee-pivot-audit-ws3` | TEE Pivot — Audit WS3 Code Verification and Memory | `28dae72f` | `28dae72f-7c1f-4ed4-9d8b-44b1913b83eb` | claude-opus-5 / high | claude-opus-5 / high | READY |
| WS4 | `tee-pivot-audit-ws4` | TEE Pivot — Audit WS4 Undo Policy and Audit | `468db7e4` | `468db7e4-851a-475a-b0d5-3182ae7934ea` | claude-opus-5 / high | claude-opus-5 / high | READY |
| WS5 | `tee-pivot-audit-ws5` | TEE Pivot — Audit WS5 Blender and Unreal Pro | `5e0bbed1` | `5e0bbed1-71a5-4e47-95d6-84102b718f25` | claude-sonnet-5 / high | claude-sonnet-5 / high | READY |
| WS6 | `tee-pivot-audit-ws6` | TEE Pivot — Audit WS6 Revit MATLAB and Fusion | `9c08e714` | `9c08e714-9cb2-4ff1-8de4-39564c4185b0` | claude-opus-5 / high | claude-opus-5 / high | READY |
| WS7 | `tee-pivot-audit-ws7` | TEE Pivot — Audit WS7 Licensing and Distribution | `34a3d58e` | `34a3d58e-4d03-48bc-befc-8377ad1e8348` | claude-sonnet-5 / medium | claude-sonnet-5 / medium | READY |

Observed model = the `model` field of the session's own assistant message in its transcript (`~/.claude/projects/-Users-john-TokenEfficiencyEngine/<uuid>.jsonl`); observed effort = that transcript's recorded effort. The TUI headers agree (e.g. “Opus 5 with high effort”, “Sonnet 5 with medium effort”) and show the `@tee-pivot-audit-wsN` agent loaded. Model acceptance here proves only that the API served the pinned ID for this account; it says nothing about future quota.

## Readiness acknowledgements

- WS0 (`bd79003c`, 2026-10-07T05:26:24+00:00): “READY — WS0 — awaiting an admitted frozen phase handoff.” — Cooked for 4s · done 8:26 AM; tool calls 0; client status `idle` / state `blocked`
- WS1 (`5452d6c5`, 2026-10-07T05:26:48+00:00): “READY — WS1 — awaiting an admitted frozen phase handoff” — Cogitated for 4s · done 8:26 AM; tool calls 0; client status `idle` / state `blocked`
- WS2 (`4999a8e9`, 2026-10-07T05:26:49+00:00): “READY — WS2 — awaiting an admitted frozen phase handoff.” — Baked for 10s · done 8:27 AM; tool calls 0; client status `idle` / state `blocked`
- WS3 (`28dae72f`, 2026-10-07T05:26:50+00:00): “READY — WS3 — awaiting an admitted frozen phase handoff” — Cogitated for 5s · done 8:27 AM; tool calls 0; client status `idle` / state `blocked`
- WS4 (`468db7e4`, 2026-10-07T05:26:52+00:00): “READY — WS4 — awaiting an admitted frozen phase handoff.” — Sautéed for 6s · done 8:27 AM; tool calls 0; client status `idle` / state `blocked`
- WS5 (`5e0bbed1`, 2026-10-07T05:26:54+00:00): “READY — WS5 — awaiting an admitted frozen phase handoff.” — Worked for 17s · done 8:27 AM; tool calls 0; client status `busy` / state `working`
- WS6 (`9c08e714`, 2026-10-07T05:26:56+00:00): “READY — WS6 — awaiting an admitted frozen phase handoff.” — Baked for 5s · done 8:27 AM; tool calls 0; client status `idle` / state `blocked`
- WS7 (`34a3d58e`, 2026-10-07T05:26:59+00:00): “READY — WS7 — awaiting an admitted frozen phase handoff.” — Crunched for 4s · done 8:27 AM; tool calls 0; client status `idle` / state `blocked`

Each launched with `claude --bg --agent … --name … --model … --effort … --permission-mode plan "<init prompt>"`, sequentially, as a structured argv (no shell interpolation). Each launch returned rc 0 and a `backgrounded · <id>` line. No fork of any existing conversation.

## Definitions

Project-scoped, YAML frontmatter `name` / `description` (“…Use only when explicitly assigned this pivot audit.”) / `model` / `effort`, parsed with PyYAML and then loaded by the client at launch (TUI shows the agent). Bodies embed the prepared brief, the absolute packet path, the four preconditions, independence, the write boundary, PASS/FAIL/N/A + BLOCKING/FIX-BEFORE-RELEASE/NOTE output, separate acceptance layers with protocol 1.0.1's two-client receipts, and the prohibitions; WS5 and WS7 add the Opus security-audit route for new cryptographic/authentication logic. No `tools` allowlist was set, and none is claimed to block Bash writes.

- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws0.md` — sha256 `8074d094d2902d9bc72feeece49a848afdbdb0b03124cf79ada5abd3353373a3`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws1.md` — sha256 `2349adff83d4ab9801afdd18caa1d35e408312853867798f6ff27402694b7406`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws2.md` — sha256 `d9854ecf0d5a9e1ff66e1e1d3042d2a7b52c25178ef1d3f4a5da58fe22d8115a`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws3.md` — sha256 `df481ff5c5c0049cdddbb435c9d9d5339bb9861f212e6eaf480484f4e9336768`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws4.md` — sha256 `457bd601c1931454d338bd56fba9642c00811fdd887924756527ac869f32b37d`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws5.md` — sha256 `85fc02c455ae2f6db4d3c4890c9cf3da2467e474c13f510c0692994efa961f14`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws6.md` — sha256 `ffdb91e134c45e2454362ce1fe45de08d75628238345018725283dd6d24cef4c`
- `/Users/john/TokenEfficiencyEngine/.claude/agents/tee-pivot-audit-ws7.md` — sha256 `52f9e267b8ee2a6bc0d579b160e2f259d2e7dfff3ea1f97ee9c6f7fda3e70937`

## Limitations and exceptions (none blocking)

- Every session logged non-blocking `SessionStart:startup` and `UserPromptSubmit` hook errors: the carta-investors, carta-crm and carta-cap-table plugins' `dispatch.sh` return “Permission denied”. Pre-existing user plugin cache state; not touched by this setup.
- WS1 and WS3 replies omit the requested trailing period; wording otherwise exact.
- `claude agents --json --all` reports every session `status: idle`, `state: blocked`. Recorded verbatim; the client does not document the meaning and it is not inferred here.
- The eight sessions stay resident as idle background processes (PIDs in the registry) until stopped. `claude --resume <uuid>` works once a session is stopped (client help); `claude attach <id>` works while it runs.
- `.claude/agents/` and the two new packet files are uncommitted in the shared dirty tree.

## Resume / attach

- WS0: `claude attach bd79003c` · `claude --resume bd79003c-0210-4963-8894-2a48d4687bfc`
- WS1: `claude attach 5452d6c5` · `claude --resume 5452d6c5-58f3-4506-a305-0d6ff1582184`
- WS2: `claude attach 4999a8e9` · `claude --resume 4999a8e9-2b0a-4f3c-98cc-b0190b35897a`
- WS3: `claude attach 28dae72f` · `claude --resume 28dae72f-7c1f-4ed4-9d8b-44b1913b83eb`
- WS4: `claude attach 468db7e4` · `claude --resume 468db7e4-851a-475a-b0d5-3182ae7934ea`
- WS5: `claude attach 5e0bbed1` · `claude --resume 5e0bbed1-71a5-4e47-95d6-84102b718f25`
- WS6: `claude attach 9c08e714` · `claude --resume 9c08e714-9cb2-4ff1-8de4-39564c4185b0`
- WS7: `claude attach 34a3d58e` · `claude --resume 34a3d58e-4d03-48bc-befc-8377ad1e8348`

## Unresolved prerequisites before any audit

- An owner-admitted phase for the workstream, with a frozen candidate snapshot (hash) that includes every required dirty/untracked dependency — a clean HEAD checkout may omit the candidate.
- A complete handoff (scope, identities, read set, versions, commands, raw outputs, limits) and an assigned evidence directory plus isolated audit environment, budget/expiry and resource limits.
- Execution permissions reconciled with the admitted packet: sessions currently sit in `plan` mode.
- PLAN.md's open items: new campaign IDs (A84–A86 are taken), owner lane dispositions, and the issues listed under “Issues the PDF must resolve before execution”.
- The 5.5 models, if wanted, need a client ≥2.1.284 under the upgrade-coordination protocol; that is a separate owner decision.
