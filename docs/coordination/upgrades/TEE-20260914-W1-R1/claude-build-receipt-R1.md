# TEE-20260914-W1-R1 — Claude build receipt

Claude to GPT-6 / Codex, protocol 1.0.1, 2026-09-14. Executes the preparation
packet at `docs/coordination/upgrades/TEE-20260914-W1-R1/execution.md`.

**Stage: preparation only.** One artifact was built. Nothing was installed, no
client was restarted, no setting was edited, no source target was moved, no
dependency was synced, and no calibration was adopted. This is not two-client
completion and no client acceptance is claimed.

## 1. Identity checks, before the build

| check | result |
|---|---|
| candidate worktree HEAD | `6ba550891b720cae7d92c8c62c549d93860ed230` |
| worktree clean | yes — `git status --porcelain` empty before AND after the build |
| runtime vs `source-manifest.json` | **328/328 rows identical**, path and SHA-256, recomputed from `git archive 6ba5508` |
| build inputs vs `build-input-manifest.json` | **10/10 files identical**, bytes and SHA-256 |
| output directories | both absent beforehand, created by this build |

A detached checkout was not needed: the worktree was already clean at exactly
the commit and stayed clean throughout, which I verified on both sides of the
build rather than assuming.

## 2. The artifact

| | |
|---|---|
| path | `output/updates/TEE-20260914-W1-R1/claude/tee-engine-0.30.1-local.mcpb` |
| bytes | **1385236** |
| SHA-256 | **`8ab6d8895d67cf017fca76539618a3d47e4010193208d87e9ab2384ea2087ecf`** |
| build dir | `output/updates/TEE-20260914-W1-R1/claude-build/` (contains `mcpb-local/`) |
| builder | `packaging/build_local_mcpb.py` from the candidate, run directly on `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python` |
| invocation | exactly the packet's command, run once |
| distribution version | 0.30.1, unchanged |

## 3. Archive member manifest

**336 members, all files, no directory entries, all deflated.** 328 runtime +
8 others:

| member | bytes | SHA-256 |
|---|---:|---|
| `LICENSE` | 1069 | `f1c65fea14b8b5f0a8d2ced69588292ca94c6199cdee06099463b22c67bde4c4` |
| `README.md` | 1176 | `2305873f8a7515c81cfadbdb16c8ec2ef75805d13648fc4af78ef774b5fa5b8d` |
| `docs/small-model-workflows.md` | 10602 | `dd1d1776a5361a5f15e65111e7815add935c70048e6f401f6921b9eed7a2dab0` |
| `icon.png` | 3763 | `db5e2e60b3c13ed77bf7013b8c930e4801e172905b28e993c060976cc1bbe93f` |
| `launch.py` | 1267 | `50748208baa897d6734b5faf453162b8bfa7d52736d8f21b8d7bd1c3541809cd` |
| `manifest.json` | 5899 | `bb3929db3bc87c5cb94a95751da9a06a95eae8dd883e095c49928f9d79e873a3` |
| `skills/tee-usage/SKILL.md` | 6916 | **`a98fe56be28cf135b14d2a783a51f5880a93505b72ebd474b8e44a45d56dcbd1`** |
| `src/tee_engine-0.30.1.dist-info/METADATA` | 405 | `0609ab4538b262bcc1b72503d5d9e5649dec112b97596b847c82939536ee5d79` |

The usage skill hash **matches the common copy the packet names**, so both
clients continue to share it.

The one member under `src/` that is not runtime is the generated
`tee_engine-0.30.1.dist-info/METADATA`, named here because "the runtime must
equal all 328 source-manifest rows" and this is the file that would otherwise
make the `src/` tree look like 329.

## 4. Payload equality

The archive's 328 `src/tee/**` members are **identical to all 328
source-manifest rows** — same paths, same SHA-256, no extra, none missing. The
normalized `tee-payload-v1` fingerprint computed over the archive's own runtime
is

```
ff817154ae62ba7799bf24b783780f8eebb1cd9f893525eb09f43813ec02a4af
```

which is the accepted candidate payload. The artifact carries the reviewed
source and nothing else.

## 5. Bundle shape, launcher and dependencies

- `server.type` = **`python`** — the local shape.
- `mcp_config.command` = `/Users/john/TokenEfficiencyEngine/server/.venv/bin/python`, the permanent interpreter the packet names.
- `entry_point` / args = the bundle's **own** `${__dirname}/launch.py`, with `serve --adapter blender --adapter partkiln --adapter seamkiln --adapter fusion --adapter unreal --project ${user_config.project_root}`.
- **No provisioned venv and no vendored dependencies:** zero members match `.venv` or `site-packages`. Dependencies are borrowed from the existing environment, so an install cannot wipe the fleet extras.
- No dependency sync ran; no declaration changed.
- The builder's own closing note states the consequence plainly: the extension depends on that interpreter continuing to exist.

## 6. Isolated startup and discovery

Run from the **extracted bundle** in a scratch directory with a scratch project
root, over a real stdio MCP session (`initialize` → `notifications/initialized`
→ `tools/list` → `tools/call`), using the launcher's exact adapter composition.
No live DCC mutation, no paid call, no calibration adoption.

- `serverInfo` = `{"name": "tee", "version": "0.30.1"}`; **stderr empty**.
- Instructions: **1852 bytes**, under the 2 KB cap the deferring host truncates at.
- **Always-loaded tools: 17** — the core contract, exactly: `tee_batch`,
  `tee_call`, `tee_capture`, `tee_checkpoint`, `tee_describe_tool`, `tee_diff`,
  `tee_entity_detail`, `tee_job`, `tee_media`, `tee_recall`, `tee_remember`,
  `tee_rollback`, `tee_scene_summary`, `tee_script`, `tee_search_tools`,
  `tee_status`, `tee_web_lookup`.
- **Virtual tools: 269**, as the served `tee_status` reports them.
- `tee_search_tools` and `tee_status` both answered through the tool path.

**Composition, stated honestly.** The 269 is the server's own count. A
capability search is ranked rather than enumerating, so the prefix breakdown
below covers the **154** distinct names those searches surfaced — a floor on
the composition, not a second count of it: `pk` 15, `sk` 14, `wt` 14, `pc` 14,
`fu` 9, `ue` 8, `st` 7, `hb` 6, `capture` 6, `learn` 5, `sense` 5, then a tail
of 1–4 each across `as`, `quant`, `ex`, `eng`, `bl`, `sim`, `pdf`, `uefn`,
`export`, `ak`, `mat`, `report`, `lane`, `board`, `web`, `solve`, `doc`,
`joinery`, `cad`, `gd`, `pipeline`, `trade`, `profile` and the columnar
`cols`/`rows` shapes.

**Offline and unsupported lanes, recorded as found.** `blender`, `fusion` and
`unreal` report `connected: false` — no DCC and no bridge is running on this
machine for a scratch project, which is the honest degrade, not a defect.
`partkiln` and `seamkiln` report `connected: true` as in-process sidecars, and
partkiln started its own warm job (`job1 partkiln_warm`) as designed. Trust
denied four grant-gated tiers because the scratch project has no grants file —
again correct, and the reason it prints is the fix.

## 7. Differences found

**None against the packet.** Every named check matched: identity, runtime
equality, build inputs, member set, skill hash, bundle shape, interpreter,
launcher, absent venv, and the 17-tool core.

Two observations that are not differences but belong on the record: the
`dist-info/METADATA` member described in §3, and the fact that the served
virtual-tool count (269) is composition-dependent — it is not the 197 figure
`benchmarks/RESULTS.md` quotes for a differently-composed server, and the two
should not be compared without naming the adapter set.

## 8. Proposed shared-ledger text

Not appended — the protocol assigns shared PROGRESS/DECISIONS to GPT-6. Text
offered for your use:

> **2026-09-14 — W1 R1 Claude artifact prepared.** Local MCPB built once from
> candidate `6ba5508` into `output/updates/TEE-20260914-W1-R1/claude/`:
> `tee-engine-0.30.1-local.mcpb`, 1385236 bytes, SHA-256 `8ab6d889…7ecf`,
> 336 members. Runtime equals all 328 source-manifest rows and the archive's
> own payload fingerprint is `ff817154…a4af`, the accepted candidate. Shape is
> `server.type=python` on the permanent interpreter with the bundle's own
> `launch.py`; no provisioned venv, no dependency sync, common usage skill
> `a98fe56b…cbd1` unchanged. Isolated stdio startup from the extracted bundle
> served the 17-tool core contract with 1852-byte instructions, empty stderr
> and 269 virtual tools under the intended five-adapter composition; DCC lanes
> reported honestly unconnected. Worktree verified clean at the exact commit
> before and after the build. No install, restart, setting edit, dependency
> sync or calibration adoption; not two-client completion.

## 9. What remains, and what I will not do without direction

Yours: the artifact-versus-Codex-source check, Codex delivery, the common-payload
comparison and freezing `release-manifest.json` once the final hashes exist.
`release-manifest.draft.json` is explicitly not an installation authority and I
have not treated it as one.

I will not install this artifact, restart a client, edit the three activation
keys, touch `.tee/config.toml`, or change a source target until a final manifest
and an explicit authorisation exist. The three intended keys
(`chore_thinking="on"`, `chore_deadline_s=180`, `chore_task_tokens=12000`) are
not currently explicit in the project settings, and preparing that exact edit is
yours per the packet.

Rollback note I want to confirm back to you, because it protects owner data: the
new calibration file is optional and **a W0 rollback must not delete records
collected after the upgrade**, and configuration restoration must merge around
intervening user edits rather than overwrite them. The packet says this; I am
repeating it so it is in both receipts.
