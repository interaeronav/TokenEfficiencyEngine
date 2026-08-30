# CLAUDE_A45_SCRIPT.md — unblock, meter the money, and land the headless fleet

**Owner directive (2026-08-30), verbatim in substance:**

1. TEE's Python escape hatch is off and its tool surface has no camera /
   render-engine / shader controls — *"enable exec-code when it means the
   job can be done more efficiently and better"*.
2. *"build in metrics to measure payments and cost from the paid model/s"*.
3. *"fix permission issues that are slowing down TEE and just creating
   blockages for product developments and access to resources"*.
4. Add fifteen headless open resources (listed in P2).

This script supersedes nothing. A43 is closed at v0.8.0; A45 builds on
its trust kernel rather than around it.

## The standing law this campaign does NOT relax

The owner asked for fewer blockages, not for less defence. The line:

- **Friction goes.** Grants that need a restart, capabilities that can
  only be granted one at a time, refusals that do not name the fix, and
  re-deciding the same question on every call — all defects, all fixed.
- **The taint law stays.** Untrusted content (web pages, KB prose,
  fronted-backend output, paid-engine replies) may never cause a side
  effect. That is the rule that stops a scraped page from driving this
  machine, and it is not what is slowing the owner down.
- **TEE still never grants itself.** Every widening is a line the owner
  writes in his own config. Tools show the exact line; they do not write
  it (research 61, and it is why `tee_trust {action:"rollout"}` exists).
- **No live order execution, ever.** P2 adds trading *research* engines.
  Backtest, optimise, inspect — yes. Placing an order with real money is
  out of scope for an autonomous tool and is left deliberately unbuilt;
  the capability name is reserved so the absence is visible, not implied.

## P0 — permissions stop being blockages

- **P0a** Grants reload when the config changes. Today `Grants.from_config`
  runs once at `TeeApp` construction (`app.py:134`), so a config edit is
  invisible until Claude Desktop restarts — the owner hit this, and so did
  the session that wrote this script. Watch mtime; re-read on change.
- **P0b** `[trust] profile = "..."` presets so one line grants a coherent
  set (`readonly` / `build` / `workstation`), alongside the existing
  explicit `grants` list. `exec-code` becomes grantable this way and is
  documented as the escape hatch the kernel was designed to have.
- **P0c** Per-turn decision memo so the kernel answers each
  (capability, caller, taint) question once instead of on every call.
- **P0d** Every refusal names the file, the exact line to add, and the
  profile that would cover it. Extend `raise_if_denied`.
- **P0e** A new tool must still be tabled (that guard is correct), but
  the families gain the fleet prefixes so P2 does not touch the kernel
  once per tool.

Acceptance: config edit visible without restart (proved live); a suite
that asserts the taint law is unchanged; refusal text carries the fix.

## P1 — the money meter (closes SI-B16 spend half + SI-B18 egress half)

The measured fact that motivates it, from this machine: a four-word
prompt to the hosted engine billed **101 tokens**, 29 of them reasoning
tokens the caller never sees — ~14x its visible content, and invisible to
`report_savings` today.

- **P1a** Record per paid call: engine, profile, endpoint host, tokens
  sent, tokens returned, reasoning tokens when the provider reports them,
  wall time.
- **P1b** A price table (per-1M in/out, currency, dated, source named) and
  a spend estimate labelled an ESTIMATE, never a bill.
- **P1c** A `sent` column — bytes/tokens that LEFT the machine, per
  endpoint. A local-only session reads a clean zero, which is the
  reassurance.
- **P1d** Surface in `report_savings` and the recap block; zero
  always-loaded growth.

Acceptance: a real paid call through the owner's shim shows up with a
non-zero `sent`, a spend estimate, and a named endpoint.

## P2 — the headless fleet

All ship as **optional extras + virtual tools**: lazy imports, zero
always-loaded token cost, and an honest probe that names the exact
install command when a library is absent. TEE's bundle does not grow.

| group | resources |
|---|---|
| `solve` | HiGHS, Google OR-Tools, SCIP, COIN-OR Cbc |
| `quant` | skfolio, PyPortfolioOpt |
| `trade` | NautilusTrader, Jesse, Hummingbot, OpenAlgo — research/backtest/read-only |
| `cad2` | OpenSCAD, CadQuery |
| `medimg` | Orthanc (DICOM), MONAI Core, Qiber3D |
| `bi` | Cube (headless BI) |

New capabilities: `read-compute` (read tier — solvers change no bytes),
`read-medimg` (read tier), `call-service` (side-effecting + taint source:
a local service's output is quoted data, never instruction).
`place-order` is **reserved and unimplemented** on purpose.

Acceptance per resource: a real smoke test that solves/loads/queries
something and asserts a known answer, or — where the resource is a server
that is not running here — a probe that fails loudly with the exact fix
and a contract test against a fake. What is verified and what is merely
wired must be stated per row, never averaged.

## Rules inherited

A33/A35 rules apply: measure before and after, state wrong-way numbers in
place, real command output into `docs/PROGRESS.md`, small commits with a
why in the body, branch `claude/token-efficiency-engine-5jv1dj`.
