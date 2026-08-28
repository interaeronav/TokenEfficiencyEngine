# Commercial readiness audit (A33 SI-4)

Dated 2026-08-28, on the M5 Mac. The question this document answers
honestly: what would shipping TEE to strangers require, what already
holds with evidence, what a session may fix, and what only the owner
decides. Every claim links to recorded evidence (PROGRESS.md dates /
commits); nothing here is asserted from memory.

## What already holds (evidence-linked)

| Requirement | State | Evidence |
|---|---|---|
| Install: wheel | **Rehearsed cold**, twice | 2026-08-22 clean-venv + MCP round-trip; 2026-08-28 fresh clone + scratch venv, `tee 0.1.1`, 16 tools over stdio (SI-3 entry) |
| Install: `.mcpb` (Claude Desktop) | **Rehearsed + user-installed** | 0.1.1 dragged in, `tee_status` answered in situ (2026-08-27 §3 close-out); required-user_config gotcha documented in PROGRESS + fixed manifest |
| Install: UE `TeeToolset` zip | **Rehearsed cold, twice** | Fresh BP-only project, plugin from zip only, toolset registered, doctor saw "56 toolsets + TEE toolset" (2026-08-27, verified independently same day) |
| Install: Blender extension zip | **Built + validated + installed** | 0.1.2 rebuilt after the macOS teardown fix, enable→serve→disable silent, busy-port remedy verified live (2026-08-22) |
| License / attribution | **Lint-enforced, fail-safe** | server + voxkiln license lints green (re-run 2026-08-28); `VENDOR.md` present; CC0/CC-BY credits rendered by `as_credits`; unreadable manifests now fail to attribution-required (ba84e85). LICENSE file was MISSING despite the pyproject MIT declaration — added 2026-08-28 |
| Security posture | **Documented + explicit** | docs/security.md: A7 floor (localhost-only, code-exec gated, script lane non-capability), data-handling posture, and (added 2026-08-28) the explicit no-telemetry statement |
| Failure-path quality | **Fault-injected** | 23-fault table across every family, one short message + exact fix each (SI-2.4, 2026-08-27) |
| Support surface | **Present** | docs/troubleshooting.md (doctor-derived); issue templates added 2026-08-28; `tee doctor` names a fix for every red state it can reach |
| Versioning / changelog | **Partial → fixed today** | CHANGELOG.md added 2026-08-28 (0.1.0 / 0.1.1 / Unreleased); discipline gap noted below (tags) |
| CI | **Workflow added 2026-08-28** | `.github/workflows/ci.yml`: ruff + full fake-adapter suite on every push; first green run must be observed after this push |
| Platform matrix (honest) | **Stated** | Measured: macOS 26 arm64 (M5/MPS) end-to-end incl. live Blender 5.2 + UE 5.8.1; Linux x64 (cloud) for the fake-adapter suite + headless Blender. CUDA paths: supported by code, NOT measured on this machine. UEFN live lanes: descoped (no Windows). |
| Telemetry | **None, stated** | security.md sentence; no phone-home code path exists |

## Gaps a session could fix — fixed this session

LICENSE file (was absent with MIT declared), CHANGELOG.md, issue
templates, CI workflow, explicit telemetry statement, quickstart's
stale wheel filename / surface cost / tool counts (each found by
executing the doc word-for-word).

## Fixable, still open (named blockers)

- **Tags**: `v0.1.0` exists only locally (cloud push was credential-
  refused, 2026-08-22); `v0.1.1` was never tagged. One command each on
  a full-permission checkout — listed in the RC checklist.
- **CI first run**: observe green after this push; until then the
  workflow is written, not proven.
- **Version bump**: the tree is behaviorally ahead of the installed
  0.1.1 (schemas, responses, kb_status, adapter default) while `make
  dist` would still name artifacts 0.1.1 — do not distribute anything
  until RC step 1 lands.
- **SI-2 leftover**: the repair stage (71 s) is unprofiled (two runs
  died to memory pressure); profile on a quiet machine before quoting
  export wall-times externally.

## Owner decisions — ADOPTED 2026-08-28 (owner: "go with best
recommendations; at this stage I'm the only user")

Each recommendation below is now the decision, with the sole-user
context applied:

1. Version: 0.2.0 shipped; the next bump is **0.3.0** (breaking `items`
   rename + the A34 surface) — announced by the build session when the
   directed work lands green.
2. Name: **keep `tee-engine` / `tee`**; the coreutils-collision line is
   now in the README; PyPI name availability checked at publish time.
3. Publishing: **PyPI-first stands, deferred** while the owner is the
   only user — revisit at the first external user.
4. Licensing: **MIT stands**; any commercial licensing decision still
   precedes publication (deferred with it).
5. Repo split: **monorepo kept** until after the first external release.
6. Support: the **"pre-release, best-effort via GitHub issues"** line is
   now in the README (harmless ahead of publish).

## The original recommendations (kept for the record)

1. **Next version number**: recommend **0.2.0** (surface-visible
   changes; CHANGELOG's Unreleased section is written for it).
2. **Name / trademark**: distribution is `tee-engine`, binary `tee`
   (collides with coreutils `tee` in shell contexts — doctor --emit
   already avoids the trap; recommend keeping both names and
   documenting the collision line in README on first publish).
   PyPI name availability must be checked at publish time.
3. **Publishing**: PyPI (`tee-engine`) and/or the Desktop-extension
   channel once an RC passes; recommend PyPI first (smallest surface).
4. **Licensing/pricing**: MIT is declared and now shipped; any
   commercial licensing decision must precede PyPI publication.
5. **Repo split** (voxkiln as its own distribution): recommend keeping
   the monorepo until after the first external release.
6. **Support commitment**: recommend stating "pre-release, best-effort
   via GitHub issues" in the README at first publish.

## Release-candidate checklist (for the next version)

1. Bump `server/pyproject.toml` + `tee/__init__.py` (+`uv.lock`),
   `TEE_SERVER_VERSION` in server/Makefile; stamp CHANGELOG's
   Unreleased section; `npx @anthropic-ai/mcpb validate` the manifest.
2. `make -C server check` green; full benchmark suite run with live
   DCCs; suites incl. `-m dcc`.
3. `make -C server dist` — five artifacts, wheel audit includes
   LICENSE + all data files.
4. Rehearse each artifact the way its user installs it: wheel in a
   clean venv (16 tools over stdio), `.mcpb` fresh-extract launch with
   the manifest's exact command, UE zip into a fresh project, Blender
   extension validate.
5. Owner: `git tag -a vX.Y.Z && git push origin vX.Y.Z`; re-drag the
   `.mcpb`; publishing decisions from the list above.
