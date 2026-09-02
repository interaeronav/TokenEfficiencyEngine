# TASK E3 — conventions and campaign checklist (kernel lane)

## 1. Test organisation

**Kernel package suite** — `/Users/john/TokenEfficiencyEngine/seamkiln/tests/` (19 files, flat, no `conftest.py`).
- Imports are plain package imports (`from seamkiln.pattern import plot`, `seamkiln/tests/test_pattern.py:19`) resolved by `pythonpath = ["src"]` in `/Users/john/TokenEfficiencyEngine/seamkiln/pyproject.toml:71-77`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["src"]
  markers = [
      "slow: runs a full BS 5058 drape battery (minutes)",
      "dcc: needs a real DCC (Blender) on this machine; skips cleanly without one",
  ]
  ```
  No `addopts` — slow/dcc run by default here (unlike server).
- Optional tiers gated per-test or module-level by `pytest.importorskip` with a `reason` naming the extra: `test_body.py:132` `pytest.importorskip("anny", reason="seamkiln[body] not installed")`; `test_gui.py:27` `("PySide6", reason="seamkiln[gui] not installed")`; `test_examples.py:22` and `test_session_every_verb.py:17` `("numba", reason="the examples run the numba solver tier")`; `test_render_properties.py:110-111` (pypdf/fpdf).
- Markers used exactly twice each: `@pytest.mark.dcc` at `test_handoff.py:120`; `@pytest.mark.slow` at `test_physics.py:181` and `test_avatar.py:151`.
- Every test module opens with a docstring naming the phase and the claim ("The pattern kernel (A53 P1): geometry, model, allowance, DXF, plotting. / No Blender, no GPU, no network.").
- Licence gate is a test, not a note: `/Users/john/TokenEfficiencyEngine/seamkiln/tests/test_licences.py` — `BANNED: dict[str, tuple[str, str]]` (line 28) maps package → (why banned, permissive replacement); `NON_COMMERCIAL_MARKERS` scan; tests `test_no_banned_distribution_in_the_declared_closure` (120), `test_no_declared_dependency_carries_a_non_commercial_licence` (128), `test_banned_modules_are_not_importable_via_seamkiln` (139), `test_the_gate_actually_fires` (155, parametrized intruder — makes the gate fail on purpose), `test_licence_marker_scan_catches_a_non_commercial_string` (167), `test_anny_is_declared_without_its_smpl_extra` (179), `test_optional_extras_are_not_walked_into_the_closure` (197). The banned list is mirrored in a comment block at the top of `seamkiln/pyproject.toml:9-24`.

**Adapter suite (kernel required)** — `/Users/john/TokenEfficiencyEngine/server/tests/test_seamkiln_adapter.py` (262 lines). Module docstring states the surface promise; then:
```python
seamkiln = pytest.importorskip("seamkiln", reason="seamkiln is an optional extra")
COARSE = 25.0

@pytest.fixture
def app(tmp_path):
    return TeeApp({"seamkiln": SeamkilnAdapter(tmp_path)}, project_root=tmp_path)

@pytest.fixture
def adapter(app):
    return app.adapters["seamkiln"]
```
Module-level `importorskip` (recorded as A53 **Gap 3**, `docs/PROGRESS.md:9257-9261`: "they `importorskip("seamkiln")` instead, so a CI box without seamkiln skips 15 tests"). Notably **SeamkilnAdapter does NOT subclass `AdapterContract`** — only FreeCAD and the kit toys do (`server/tests/test_freecad_adapter.py:19`, `test_freecad_live.py:31`, `test_adapter_kit.py:110,115`). A new lane should not repeat this. Trust-table assertion pattern at `test_seamkiln_adapter.py:200-205` (`trust.capability_for("sk_blocks") == "read-scene"`), search-ranking pins at 235-246, surface pin at 249-252 (`from tee.server import _DESC; assert len(_DESC) == 17`).

**Adapter suite (NO kernel)** — `/Users/john/TokenEfficiencyEngine/server/tests/test_seamkiln_translate.py` (80 lines), added in A65 to part-pay Gap 3. Imports the adapter's private translation layer directly, no importorskip:
```python
from tee.adapters.seamkiln.adapter import _PASSTHROUGH, _WIRE_OPS, _panel_id, _translate
from tee.kernel.errors import TeeError
```
Tests are pure: op→command translation, entity naming, `TeeError` on unsettable props (`pytest.raises(TeeError, match="nothing settable")`), and a verb-completeness loop (`test_every_session_verb_added_since_a53_passes_straight_through`).

**Packaged contract suite** — `/Users/john/TokenEfficiencyEngine/server/src/tee/kernel/contract.py`, `class AdapterContract` (line 33), used as `class TestMyAdapterContract(AdapterContract): def make_adapter(self): ...`. Eleven inherited tests:
`test_info_payload_shape` (41), `test_probe_answers_a_bool` (49), `test_create_set_delete_roundtrip` (56), `test_diff_reports_changes_not_the_world` (76), `test_unknown_op_fails_rule6` (88), `test_unknown_entity_fails_rule6` (97), `test_execute_does_not_mutate_the_callers_batch` (103), `test_entity_ids_are_stable_across_listings` (114), `test_concise_rows_are_compact` (123), `test_snapshot_restore_roundtrip` (134), `test_capture_respects_the_byte_budget_or_refuses_loud` (148). Documented for third parties in `docs/adapter-kit.md:104-123`.

**server/tests/conftest.py** (240 lines) — adapter-relevant fixtures: `os.environ.setdefault("TEE_MACHINE_TOTAL_GB", "128")` at module import (hermetic machine capacity, line ~24); `blender_bridge` (session, parametrized `["official","tee"]`, launches headless Blender, skips without binary); `network` (session, skips offline); `StubBridge` (null-delimited JSON execute server); **`_fresh_turn` (autouse)** — resets `trustctx.CALLER`/`TAINT` to "content-derived" per test (A43 L2), so a virtual tool needing live-turn authority must say so; `pytest_sessionfinish` prints shadow-band denial counts. There is no per-adapter fixture file convention beyond `fixtures_<lane>.py` (e.g. `fixtures_freecad.py` supplying `FakeFcWire`) imported flat (`from fixtures_freecad import FakeFcWire`, `test_freecad_adapter.py:7`).

**server/pyproject.toml:143-159** — `[tool.pytest.ini_options] testpaths=["tests"]`, `timeout = 60`, markers `dcc`, `network`, `ml`, `llm`, and `addopts = "-m 'not dcc and not ml and not network and not llm'"`.

**CI** — `/Users/john/TokenEfficiencyEngine/.github/workflows/ci.yml`: single job `server`, `working-directory: server`, `uv sync --all-extras` (so `[cad]`/cadquery **is** installed in CI), then `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run pytest -q`. **CI never enters `seamkiln/` or `../benchmarks`** — the kernel package's suite and lint are local-only; a new lane inherits this hole unless the workflow is extended.

**Commands + last recorded pass counts** (`CLAUDE_A65_SCRIPT.md:24-27`, `docs/PROGRESS.md` tail):
| suite | command | last recorded |
|---|---|---|
| kernel | `cd seamkiln && PYTHONPATH=src uv run --project ../server python -m pytest -q tests/` | 260 passed / 8 skipped (PROGRESS:9852); 244/8 at A65 close (9622) |
| server | `uv run --project server python -m pytest server/tests -q` | 1,224 passed / 17 skipped / 97 dcc-deselected (9852); 1,214/10 at A65 close |
| server (from `server/`) | `uv run pytest -q -m "not dcc"` / `make test` | as above |
| lint | `uv run --project server ruff check server/ seamkiln/` → exit 0; `make lint` | clean |
| benchmarks/surface | `uv run --project server python benchmarks/run_benchmarks.py` (`run_surface_scenario()`) | `surface: 17 always-loaded tools = 2033 tok on the wire; 126 virtual tools` |
The kernel suite takes ~7 min (`CLAUDE_A65_SCRIPT.md:31-33`) — "run it in the background"; physics tests are converged-resolution by law.

## 2. Lint

`server/Makefile:52-60`:
```make
lint:
	uv run ruff check src tests ../benchmarks
	uv run ruff format --check src tests
format:
	uv run ruff format src tests
test:
	uv run pytest
check: lint test
```
The `../benchmarks` inclusion carries an SI-B20 comment (Makefile:46-51) explaining the code producing the project's numbers went unlinted for its whole life. Ruff config: `server/pyproject.toml:143-148` — `line-length = 100`, `target-version = "py311"`, `select = ["E","F","W","I","UP","B","SIM","RUF"]`. `seamkiln/pyproject.toml:64-69` — same line-length/target, `select = ["E","F","I","B","SIM","UP","RUF"]` (no `W`).

## 3. docs/PROGRESS.md entry format

Reverse-chronological append at the tail; `###` per phase, `##` per campaign block. A53 P4 heading + first paragraph (`docs/PROGRESS.md:9056-9062`):
> ### A53 P4 — seamkiln joins TEE without moving the surface (2026-09-01)
>
> `server/src/tee/adapters/seamkiln/`. Suite **1,213 passed / 17 skipped** (up 14),
> ruff clean, and the number that matters:
>
> ```
> surface: 17 always-loaded tools = 2033 tok on the wire; 118 virtual tools
> ```

A65 heading + first paragraph (`docs/PROGRESS.md:9578-9584`):
> ## A65 — the A53 script audited, and its acceptance debt paid (2026-09-02)
>
> Owner: *"Debug and improve the whole script — meant the A53 SCRIPT and follow
> up suggested and attempted improvements."* A53 was marked COMPLETE and then
> eleven campaigns (A54–A64) built on it outside any script, which CLAUDE.md
> forbids. `CLAUDE_A65_SCRIPT.md` is the amendment: every A53 phase and every
> follow-up audited against the tree, the tests, and a live `TeeApp`.

Closing pattern, both forms (9622-9623 and 9852-9854):
> **Suites at close:** seamkiln 244 passed / 8 skipped (from 229); server
> 1,214 passed / 10 skipped (from 1,206); lint clean.

> **Suites at close:** seamkiln 260 passed / 8 skipped (from 244); server 1,224 passed /
> 17 skipped / 97 dcc-deselected (from 1,214); lint clean on every file
> touched. Surface unchanged: 17 tools / 2,033 tok.

Older single-suite form: "Suite **1,194 passed / 17 skipped**, ruff clean." (8635). Campaign close-out also carries a **before/after fenced table** (9214-9221: `surface / virtual / TEE suite / <lane> / <lane> task`) and an explicit numbered **gaps list** ("Gap 1 — USD export is impossible through trimesh, measured", 9247+). Bold lead-ins per finding paragraph (`**The UV map was free, and exact.**`) are the house style; every claim carries a measured number.

## 4. docs/DECISIONS.md entry format

Newest entries use `## <campaign> — <topic> (<date>)` (older ones `## <date> — <A-number>: <decision> (owner decision)`). A53 (`docs/DECISIONS.md:1058-1065`):
> ## A53 — the garment lane (2026-09-01)
>
> **Build the solver; do not adopt the paper's.** GarmentCode/PyGarment is MIT,
> but GarmentCodeData drapes through a fork of NVIDIA Warp under the **NVIDIA
> Source Code Licence — non-commercial**. The best-documented open garment
> pipeline in the world therefore cannot ship, and copying its stack inherits
> that silently. seamkiln writes its own XPBD; mainline Warp (Apache-2.0) and
> C-IPC (Apache-2.0) stay available as backends.

Format per decision: **bold one-line ruling**, then the evidence and the alternative that was rejected, with the licence/measurement that decided it. A53 contains one paragraph per licence call plus measured-choice rulings ("The solver backend was chosen by measurement, and the GPU lost", "Compliance is relative, not the textbook alpha").

## 5. docs/research/ format and numbering

`/Users/john/TokenEfficiencyEngine/docs/research/67-garment-cad-lane.md` headings:
`# 67 — Garment CAD + drape lane: a Marvelous Designer / CLO3D-class tool (2026-09-01)` (H1 = number + title + date), then
`## 1. The parity target — what MD/CLO actually are` (7) · `## 2. The licence minefield — the finding that matters most` (42) · `## 3. The solver landscape, and the Apple Silicon reality` (77) · `## 4. Pattern interchange: DXF AAMA / ASTM` (103) · `## 5. Fabric parameters` (140) · `## 6. What this machine and this repo already have` (157) · `## 7. TEE-side reuse map (why this belongs here)` (173) · `## 8. Defect found while doing this research` (187) · `## 9. P0 answered these (2026-09-01 — measured, see PROGRESS)` (197) · `## 9b. Original open questions (kept for the record)` (220).

Numbering: strictly sequential by filename prefix; highest existing is **67**, so a new lane's research doc is **`docs/research/68-<slug>.md`**. `docs/research/00-index.md` has a `## Corpus` markdown table `| Doc | Covers |` whose rows look like:
> `| [52-fabrication-cad-lane.md](52-fabrication-cad-lane.md) | ... |`

— but the table **stops at 48** (`00-index.md:60`); docs 49–67 were never added (verified: zero matches for `49-web-lookup`, `52-fabrication`, `67-garment`). After the table come `## Architecture decisions (ADR)` (A1…An bullets with *Why:* and parenthesised source doc numbers) and `## Headline numbers worth remembering`. Adding the row is an outstanding convention debt a new lane can either follow (add its row) or knowingly skip.

## 6. CLAUDE.md campaign-script registration

Bullets live under `## How to work in this repo`. A53/A65 bullet (single bullet, verbatim):
> - The A53 build (`seamkiln`: a garment CAD + drape kernel with the same
>   core loop as Marvelous Designer / CLO3D, headless FIRST with the GUI as a
>   client of that same core) is **COMPLETE**, P0–P6, and was followed by
>   eleven owner-directed campaigns (A54–A64: …). **`CLAUDE_A65_SCRIPT.md` is now the plan of record for the
>   garment lane** … Research doc 67 remains the design of record for licences
>   and platform facts; `docs/seamkiln-lane.md` is the user-facing guide. The
>   licence audit is load-bearing and enforced by
>   `seamkiln/tests/test_licences.py` …

Shorter precedent form (A49): "The A49 build (Godot as a headless first-class adapter: socket bridge, declarative commands, the run-scene game lane) is driven by `CLAUDE_A49_SCRIPT.md`. Its design rests on measured facts recorded in the script itself — including that headless Godot CANNOT render…". Pattern = *(A-number) (one-line scope) is driven by `CLAUDE_A<n>_SCRIPT.md`; research doc N is its design of record; `docs/<lane>-lane.md` is the user guide; + the one load-bearing measured fact or trap.*

## 7. CLAUDE_A53_SCRIPT.md skeleton (the template)

H1 + owner directive block + "written for a fresh Opus session" preamble naming the design-of-record research doc, then H2s in order (no H3s at all):
1. `# CLAUDE_A53_SCRIPT.md — <package>: <one-line thesis>` + `**Owner directive (date, verbatim):** *"…"*`
2. `## Orientation for a cold session` — repo path + branch, PROGRESS first; suite command + expected counts; **surface invariant** and its measurement command; upgrade trap; where new code lives (root package, `voxkiln/` precedent) and where the adapter lives; "phases are independently shippable".
3. `## Measured facts (<date>, this machine — build ON them)` — numbered list (hardware, already-installed deps with versions, prior measurements).
4. `## Laws` — numbered 1–10 (see §11).
5. `## P0 — clear the path, then let the numbers choose (do this first)` — sub-items P0a/P0b/P0c as **bold lead-ins**, each with a bake-off table and an `*Acceptance:*` line; ends "Commit each of P0a/b/c separately."
6. `## P1 …` `## P2 …` `## P3 …` — kernel phases, each ending with `*Acceptance:*`.
7. `## P4 — the TEE adapter (server/src/tee/adapters/<name>/)` — Adapter protocol methods enumerated, declarative op set for `tee_batch`, long tail as `<xx>_*` virtual tools each an explicit trust-table entry, tool-search top-3 queries named, then `*Acceptance:* surface still 17 tools / ~2,034 tok; … a fake-adapter test suite means CI needs no solver. Add a `benchmarks/` scenario — "…" — and put the tokens-saved number in `benchmarks/RESULTS.md` with the others.`
8. `## P5 — the GUI shell (…, extras [gui])` — "The architecture is the feature", session recording, `*Acceptance:*` replay to identical hash + `import <pkg>` with no Qt.
9. `## P6 — evidence, interop, ship` — exports, tech pack, `docs/<lane>-lane.md`, DECISIONS entries per licence call, PROGRESS throughout, **version bump, bundle, clean-unzip MCP verify**.
10. `## Out of scope (say no to these in writing)` — explicit refusal list.

A65 (the amendment/audit script) adds `## What the audit found (<date>)`, `## Status of every feature the owner asked for`, `## Laws (A53's ten stand; these were learned since)`, phases tagged `(DONE in A65)` / `(ATTEMPTED …, BLOCKED)` / `(STILL OWED: cannot be done without them)`, and `## Out of scope (unchanged from A53, minus the owner's override)`.

## 8. Lane guide and setup doc structure

`docs/seamkiln-lane.md` — H1 `# The garment lane (A53, and the follow-ups A54–A65)`, opening paragraph naming the package and "**no new always-loaded tools**", an install/serve bash block (`uv pip install -e seamkiln` / `tee serve --adapter seamkiln --project ~/patterns`), the before/after surface sentence, then H2s: `## The loop` (18) · `## Verbs` (48) · `## Bodies, and which arrangement they get` (68) · `## Render properties on the card` (142) · `## The examples: the two shots, from the repo` (154) · `## The GUI` (178) · `## The tier-2 bake: attempted, blocked` (195).
Sibling lane docs: `docs/godot-lane.md` (`## The one rule that will bite you first` / `## Building scenes` / `## Running the game — the actual payoff` / `## Seeing it`), `docs/pdf-lane.md`, `docs/adapter-kit.md` (`## The shape of the seam` / `## The seven methods` / `## Prove it: the packaged contract suite` / `## Wire it in` / `## Session etiquette your adapter inherits`).
`docs/setup-freecad.md` — H1 `# FreeCAD setup — the fabrication lane (A37)`, then `## Install (once)` (10) · `## Serve` (22) · `## The typed ops` (33) · `## Drawings and exports (virtual tools)` (53) · `## The recorded acceptance (2026-08-29)` (69). `docs/setup-voxkiln.md` is the root-package precedent: `## Install (on the Mac)` · `## Use through TEE` · `## Standalone` · `## Status`.

## 9. CHANGELOG.md format

Preamble: "The `tee-engine` server versions here; the UE `TeeToolset` plugin and the Blender `tee_bridge` extension carry their own versions where noted." Latest entry (`CHANGELOG.md:6-45`):
> ## 0.18.0 — 2026-08-31
>
> **A smart quote no longer destroys a report, and a camera checks its own work.**
>
> ### PDFs can write ordinary prose
> …
> ### And the attributes a real document has
> ### `sense_frame` — the model grades the shot, TEE re-aims
> ### Faster launches

`## <semver> — <ISO date>`, a bold one-line release thesis, then user-facing `###` sections (feature name or the failure it fixes), prose with measured numbers, plus `### What it refuses, and why` where applicable. **Note: there is no 0.19.0 entry** — `server/pyproject.toml:3`, `packaging/mcpb_manifest.json:5` and `server/Makefile:8` all say 0.19.0 but CHANGELOG stops at 0.18.0. A new lane's ship step should add the missing entry rather than inherit the drift.

## 10. Packaging / version-bump procedure

Three files must move together (A53's close-out caught exactly this desync, `docs/PROGRESS.md:9231-9235`: "`server/pyproject.toml` said 0.19.0 while `Makefile`'s `TEE_SERVER_VERSION` and `packaging/mcpb_manifest.json` still said 0.18.0 — the bundle would have shipped named 0.18.0 with 0.19.0 inside it"):
1. `server/pyproject.toml:3` `version = "0.19.0"`
2. `server/Makefile:8` `TEE_SERVER_VERSION ?= 0.19.0`
3. `packaging/mcpb_manifest.json:5` `"version": "0.19.0"` (manifest_version 0.4, `server.type "uv"`, entry `src/tee/cli.py`, launch `uv run --directory ${__dirname} --no-dev tee serve …`)
4. `make dist` (uv build + Blender extension build + UE zip + `make mcpb`) or `make mcpb` alone → `dist/tee-engine-$(TEE_SERVER_VERSION).mcpb`. `mcpb` appends `[tool.uv] default-groups = []` to the bundle's pyproject copy (Desktop's plain `uv sync` otherwise pulls +58 MB of dev deps) and prints the extras-restore reminder.
5. **Clean-unzip MCP verify** (`CLAUDE_A53_SCRIPT.md:277`; evidence block at `docs/PROGRESS.md:9237-9250`): unzip the bundle fresh, launch over MCP stdio with the exact manifest command, and record the handshake + always-loaded tool list + a lane search + a virtual-tool call that must **refuse honestly** when the optional package is absent:
   ```
   handshake: {'name': 'tee', 'version': '0.19.0'}
   always-loaded tools: 17
   search 'sewing pattern' reaches sk_*: True
   sk_blocks called from the bundle -> REFUSED (seamkiln absent, as expected)
   ```
6. Upgrade trap to restate in the script: every `.mcpb` install wipes the extension venv's extras; restore with `uv pip install --python "<ext venv>/bin/python" 'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]' 'tee-engine[extract]' 'tee-engine[pdf]'` — `cad` is excluded on purpose (sidecar).

## 11. The laws / hard rules

**A53's ten laws** (`CLAUDE_A53_SCRIPT.md:78-107`), headings only:
1. **Measured before and after.** (a phase without a number did not happen)
2. **The licence minefield is enforced by a test, not by memory** (P0c).
3. **The GUI is a client of the headless core.**
4. **Zero new always-loaded TEE tools.**
5. **Diffs over snapshots, text over pixels.**
6. **A refusal names its reason and the fix.**
7. **Determinism is a feature.**
8. **The model's eye is advice, not measurement** (A51's finding).
9. **Feature parity, not container parity.** (open interchange only)
10. The metric is TEE's metric: **tokens per completed garment task**, measured in `benchmarks/`.

**A65's laws 11–20** (`CLAUDE_A65_SCRIPT.md:95-118`), one-liners:
11. Never rely on a coarse preview — an unconverged drape is a different answer, not a rougher one.
12. Cloth time is derived from fps; `frames_per_step` is not a free parameter.
13. Travel at the gait's own speed, or the feet skate.
14. The line you changed last beats the line that looks suspicious.
15. A constraint that learns its rest length from a wrong pose preserves the wrong pose.
16. `alpha` in this solver is a relative softening, not m/N.
17. A self-describing format is left alone (glTF states +Y up in metres).
18. Probe capability on the object you will assign to, never on the class RNA.
19. Use it, don't just test it — every A60–A64 defect survived a green suite.
20. An unclothable body reads as a broken cloth solver.

**CLAUDE.md `## Hard rules (token-efficiency dogma)` 1–6**, verbatim:
1. **Never return full scene dumps by default.** Tools return compact summaries with stable IDs; detail is opt-in via explicit query tools.
2. **Diffs over snapshots.** After a mutation, report what changed, not the new world state.
3. **Batch over chatter.** Prefer one macro-command / one code-execution call over N single-op tool calls.
4. **Text over pixels.** Screenshots are a last resort; structured text state is the default evidence.
5. **Small tool surface, progressive disclosure.** Keep the always-loaded tool schemas minimal; expose long-tail capability through a `run_python` / `run_console` escape hatch and searchable docs, not hundreds of tools.
6. **Fail loud and cheap.** Validation errors must come back in one short message with the exact fix, not a stack-trace novel.

---

# Campaign deliverables checklist (in order)

| # | Deliverable | Path / form | Convention source |
|---|---|---|---|
| 1 | Research doc | `docs/research/68-<slug>.md`; H1 `# 68 — <title> (<date>)`; numbered H2 sections ending with a licence-minefield section, a "what this machine already has" section, a "TEE-side reuse map", a defects-found section, and an open-questions section | `docs/research/67-garment-cad-lane.md` |
| 2 | Index row (optional, currently stale) | `docs/research/00-index.md` `## Corpus` table row `\| [68-…](68-…) \| covers … \|` | `00-index.md:12-60` (table stops at 48) |
| 3 | DECISIONS entry | `docs/DECISIONS.md` append `## A<n> — the <lane> lane (<date>)` + one bold-ruling paragraph per licence/architecture call (OCCT LGPL-2.1-with-exception, cadquery Apache-2.0, banned alternatives) | `DECISIONS.md:1058+` |
| 4 | Campaign script | `CLAUDE_A<n>_SCRIPT.md` with the ten H2s of §7 | `CLAUDE_A53_SCRIPT.md` |
| 5 | CLAUDE.md registration bullet | under `## How to work in this repo`: scope, `is driven by CLAUDE_A<n>_SCRIPT.md`, design-of-record research doc, user guide path, the load-bearing enforced fact | `CLAUDE.md` A53/A49 bullets |
| 6 | Kernel package | `/<name>/` at repo root: `pyproject.toml` (own name/version, permissive-deps comment block naming BANNED→replacement, extras incl. `gui`/`dev`, `[tool.ruff]` line-length 100, `[tool.pytest.ini_options]` with `pythonpath=["src"]` + `slow`/`dcc` markers), `README.md`, `src/<name>/`, `tests/`, `examples/`, `uv.lock` | `seamkiln/`, `voxkiln/` |
| 7 | Licence gate test | `<name>/tests/test_licences.py` — BANNED dict with reason+replacement, non-commercial marker scan, closure walk, ≥2 deliberate-failure cases, extras-not-walked case | `seamkiln/tests/test_licences.py` |
| 8 | Kernel test suite | `<name>/tests/test_*.py`, per-module docstring naming the phase; `importorskip(<extra>, reason="<pkg>[<extra>] not installed")`; `@pytest.mark.slow` for converged batteries, `@pytest.mark.dcc` for DCC handoff | `seamkiln/tests/` |
| 9 | Backend bake-off | measured table (ms/frame, peak RSS, determinism) per contender incl. a zero-new-code baseline, recorded in PROGRESS; the winner is a number, not a preference | `CLAUDE_A53_SCRIPT.md` P0b |
| 10 | TEE adapter | `server/src/tee/adapters/<name>/{__init__.py,adapter.py,tools.py}` — `Adapter` protocol (`info/probe/list_entities/execute/snapshot/restore/capture`), declarative enumerable op set, stable prefixed entity ids (`panel:FRONT`), pure `_translate` helper | `server/src/tee/adapters/seamkiln/` |
| 11 | Virtual tools | `register_<name>_tools(app)` registering `VirtualTool(name="<xx>_*", description, schema, handler, tags=[…], examples=[…])`; `_need()` raising `TeeError` with the exact install command; `_adapter(app)` raising `seamkiln_not_served`-style error | `adapters/seamkiln/tools.py:43,336` |
| 12 | Contract test | `server/tests/test_<name>_adapter.py` with `class Test<Name>AdapterContract(AdapterContract)` over a **fake/hermetic wire** (FreeCAD pattern, not seamkiln's importorskip) + `app`/`adapter` fixtures + trust-capability assertions + `assert len(_DESC) == 17` | `test_freecad_adapter.py:19`, `test_seamkiln_adapter.py` |
| 13 | No-kernel adapter test | `server/tests/test_<name>_translate.py` — translation/naming/refusal logic with the kernel absent | `test_seamkiln_translate.py` |
| 14 | Fixtures | `server/tests/fixtures_<name>.py` (fake wire), imported flat | `fixtures_freecad.py` |
| 15 | Tool-search ranking pins | test asserting named queries land the lane's tools top-3 (`app.registry.search(q, limit=3)`) | `test_seamkiln_adapter.py:235-246` |
| 16 | Surface invariant proof | `benchmarks/run_benchmarks.py` `run_surface_scenario()` line quoted into PROGRESS: `surface: 17 always-loaded tools = 2033 tok on the wire; N virtual tools`; plus `test_always_loaded_surface_delta_is_zero` (`server/tests/test_gateway.py:168`) | A53 P4 acceptance |
| 17 | Benchmark scenario | `run_<name>_scenario()` in `benchmarks/run_benchmarks.py` (naive arm = the reads a model must do without compact state; TEE arm = one batch + diff + one virtual-tool call), wired into `main()`/`_safe()` and the report writer | `run_benchmarks.py:1231,1305,1800` |
| 18 | RESULTS row | `benchmarks/RESULTS.md` `## <Lane>: <verbs> (A<n>)` + `\| arm \| tokens \| calls \|` table with a bold **saved %** row and a wall-clock/scale sentence | `RESULTS.md:248-280` |
| 19 | User guide | `docs/<name>-lane.md` — H1, "no new always-loaded tools" claim, install/serve bash block, before/after surface line, `## The loop` / `## Verbs` / … | `docs/seamkiln-lane.md` |
| 20 | Setup doc (if an external app/binary is involved) | `docs/setup-<name>.md` — `## Install (once)` / `## Serve` / `## The typed ops` / `## <exports> (virtual tools)` / `## The recorded acceptance (<date>)` | `docs/setup-freecad.md` |
| 21 | Examples | `<name>/examples/<shot>/` runnable `python -m examples.<shot> all --out …` with a `--probe` short mode; a CI-safe smoke test (`tests/test_examples.py`) that runs only the probe | `seamkiln/examples/`, `tests/test_examples.py` |
| 22 | PROGRESS entries | one `###` per phase during the work + a campaign `##` block; measured output pasted, bold lead-ins per finding, before/after fenced table, numbered honest gaps, closing `**Suites at close:** <kernel> N passed / M skipped (from X); server N passed / M skipped (from X); lint clean. Surface unchanged: 17 tools / 2,033 tok.` | `PROGRESS.md:9056,9578,9622,9852` |
| 23 | Version bump ×3 + bundle + clean-unzip verify | `server/pyproject.toml`, `server/Makefile` `TEE_SERVER_VERSION`, `packaging/mcpb_manifest.json`; `make mcpb`; stdio handshake evidence incl. "REFUSED (kernel absent, as expected)" | PROGRESS:9231-9250 |
| 24 | CHANGELOG entry | `## <semver> — <date>` + bold thesis + user-facing `###` sections (0.19.0 is currently missing and should be written) | `CHANGELOG.md:6` |
| 25 | Lint + CI | `make lint` exit 0 (`ruff check src tests ../benchmarks`) and `uv run --project server ruff check server/ <name>/`; note CI (`.github/workflows/ci.yml`) runs only `server/` — extending it to the new package is an explicit choice | `server/Makefile:52`, `ci.yml:19-24` |