# Claude receipt 12 — candidate review, TEE-20260911-A82-HF2 rev 1

```text
Receipt ID / UTC / recipient: TEE-20260911T082148Z-CLAUDE-12 / 2026-09-11T08:21:48Z /
  Claude (Fable 5.1, Claude Code)
Scope: runtime-upgrade
Protocol version / document SHA-256: 1.0.1 / ac74807a…fc9c
Update ID / frozen manifest SHA-256: TEE-20260911-A82-HF2 revision 1 /
  68fe44947e9ff174678dbfed1d3b581171ef2e4bd56c4f9fd93e16413f507d26
Stage: received      Review outcome: PASS — no blocking defect
Received artifact/source identity:
  claude/tee-engine-0.30.1-a82-hf2-local.mcpb, sha256
  1bd87459cddd5e86641f806e8dae09236aef232322725bb853cd1ba4d2757ca9,
  1,141,293 bytes; payload tee-payload-v1 c0f95e83…811e, 294 files / 3,435,983 B
Running source origin / payload identity / TEE and wrapper versions:
  UNCHANGED — this client still serves accepted A82 (ac6474ba…, 293 files).
  Nothing installed by this review.
Interpreter / selected project / adapters: unchanged — borrowed checkout venv;
  /Users/john/TokenEfficiencyEngine; five adapters
Required feature and dependency checks / evidence: verification table below;
  184/184 docagents tests reproduced against the extracted payload
Continuity checks / preserved grants and model selection (live before-record,
  2026-09-11T08:21:48Z): qmax pinned; grants call-paid-engine, exec-code, run-adhoc,
  run-declared-step, run-doc-agent; code_exec_enabled true; 261 virtual;
  no jobs/checkpoints; Fusion NOW CONNECTED (2705.1.15, "Untitled", empty)
Differences or failures / next action / responsible agent: three non-blocking
  notes below. Next: GPT-6 runs execution.md steps 2–5; then John installs;
  then Claude's runtime receipt.
```

## Independent verification — recomputed, not read from evidence

| Check | Declared | Measured | |
|---|---|---|---|
| `release-manifest.json` self-checksum | `68fe4494…7d26` | same | ✅ |
| protocol | `ac74807a…fc9c` | = accepted 1.0.1 | ✅ |
| Claude artifact | `1bd87459…7ca9` | same, 1,141,293 B | ✅ |
| Codex artifact | `1c08499f…57f1` | same, 1,572,125 B | ✅ |
| HF2 payload (mcpb) | `c0f95e83…811e` 294 | same | ✅ |
| HF2 payload (Codex zip) | same | **identical to mcpb** | ✅ |
| baseline | `ac6474ba…ea52` 293 | = live checkout = installed | ✅ freeze holds |
| rollback artifacts | A82's `98f5116f…` / `e908840f…` | = the artifacts I accepted in receipt 11 | ✅ |
| delta | 3 files | +`model_metadata.py`, ~`backends.py`, ~`tools.py` — my diff and `source-delta.json` agree | ✅ |
| launcher | — | `launch.py` byte-identical to `packaging/launch.py` | ✅ |
| config identity | `metadata_sha256` `d158cc6d…` | = `qmax-docagent-metadata.json`; TOML = `common_files[5]` | ✅ |
| their harness | — | `VERIFY_FROZEN.py`: verified true, `runtime_acceptance: false` | ✅ honest |
| tests | 184 in 4.74 s | **184 passed in 4.52 s**, my rerun on the extracted payload | ✅ |

## The patch, read rather than trusted

**`backends.py` — the browser fix is narrow and correct.** Aider's
`--yes-always` also accepts `io.offer_url()`, so an unknown alias walked into
`webbrowser.open`. The fix sets `BROWSER` **only in the Aider child**, to
`/usr/bin/true` or `/bin/true`, and only after checking the resolved path is in
that allowlist, a regular file, uid 0, not group/world-writable, executable.
It deliberately does **not** use `--no-show-model-warnings`, which would also
silence missing-credential diagnostics — the right refusal, and the evidence
file says why. Unsupported platforms refuse rather than launch anything.

**On this Mac the precondition holds:** `/usr/bin/true` is root-owned, mode
0755, a regular file, and passes the patch's exact predicate. `/bin/true` is
absent here; the first candidate suffices.

**`model_metadata.py` — fails closed.** Exact schema-1 key set, route-bound
(`model`/`url` must equal the profile's), HTTPS provenance URLs recorded and
never fetched, dated with a ≤30-day window, bounded integers, limits within the
context window, output budget 128–8192 within provider capacity, USD only, and
**a zero price on a paid profile is refused** — which is exactly the guard
against promoting the proxy's reported `0` cost. `tools.py` just surfaces the
table through `doc_status`. Three lines.

## Three notes, none blocking

**1. The metadata expires on 2026-09-25, and the failure will look unrelated.**
`valid_until = "2026-09-25"`. From 2026-09-26, `aider_metadata()` raises
`docagent_model_metadata` ("stale…") and every `doc_run` on Aider/QMAX refuses.
That is the designed fail-closed behaviour, and correct — but two weeks from now
nobody will remember this table exists. Suggest `doc_status` surface the
`valid_until` date and days remaining, so the refusal has a visible cause before
it happens.

**2. `proposal.md` contradicts itself on the pin.** Paragraph 1: "TEE q14b is
now pinned; do not switch it." Final paragraph and `execution.md`: QMAX pinned.
Live state settles it — `llm_profile: "qmax"`, `pinned: true`. The candidate
is unaffected; the stale sentence should not be carried into the outcome record.

**3. The checkout is at baseline, not HF2.** HF2 source exists only in the
deliveries; `execution.md` step 3 applies the three files from the Codex
archive. That is as intended, and it is why the freeze holds — noted so nobody
reads the checkout's `ac6474ba…` as a stale delivery.

## Continuity facts for cutover

Grants went from one at receipt 11 (06:19Z) to five — the owner's
`worker-permission-approved` at 06:29Z; recorded, not questioned. `code_exec_enabled`
is true and is grant-derived; `environment-before.json`'s `allow_code_exec=false`
is a legacy field, as the packet says. Fusion is connected with an unsaved, empty
"Untitled" design — nothing to lose on reconnect; Blender holds 13 objects in its
snapshot `.blend`, which survives.

**Recommendation: proceed.** No installation, grant, pin or configuration
change was made by this review.
