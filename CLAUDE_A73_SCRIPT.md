# CLAUDE_A73_SCRIPT.md — the wind-tunnel GUI handoff: `wt_open`, ParaView state files, and a panel

**Owner directive (2026-09-07):** *"now do the GUI handoff"* — gap 1 of A72, deferred on 2026-09-06 with the words *"headless only for now"*. The deferral named its own contents: `wt_open`, ParaView `.pvsm` state files, a panel.

**Owner decisions (2026-09-07, this campaign's three questions):**

1. **Prepare always, launch on request.** `wt_open` always writes the state file and the `.foam` stub and returns the exact command; it spawns the application only for `launch=true`, and refuses with a named fix where there is no display. Nothing in TEE has ever opened a window before, so the spawn is opt-in.
2. **The panel is in scope.** Built on partkiln's pattern, not seamkiln's.
3. **ParaView and OpenVSP.** FreeCAD/CfdOF is NOT in this campaign; the C2/C3 rows stay open.

Campaign **A73**; research doc **73** the design of record; server **0.23.0 → 0.24.0**. `73` was free in both series when this was written, and no other branch was mid-flight with it — a check A72 learned the hard way, having been built as A68 and renumbered before merge. Phases are independently shippable: stopping at a boundary must leave the tree green and the feature honest about what it does not do.

## Orientation for a cold session

- Repo `/home/user/TokenEfficiencyEngine`, branch **`claude/wind-tunnel-aerodynamic-integration-hcsa7u` ONLY**, restarted from the base after A72's pull requests merged. Read `docs/PROGRESS.md` first (the A72 block and its gap list are at the tail); paste real command output into it per phase; commit and push per item; stage only this campaign's own paths, never `git add -A`.
- Suites: `cd server && uv run --no-sync pytest -q` (hermetic; 1,833 passed at the start of A73) · `uv run --no-sync pytest -q -m cfd` (the real-binary tier) · `make lint` (`ruff check src tests ../benchmarks` + `ruff format --check src tests`). Never `uv sync` in `server/` — it drops the pip-installed extras.
- **Surface invariant: 17 always-loaded tools.** A73 adds ZERO. `wt_open` is a `VirtualTool` reached through `tee_search_tools` / `tee_describe_tool` / `tee_call`, and the panel is a package launched by `python -m`, never a tool and never a console script — partkiln's law: *a kernel that installs a window on the PATH is not headless-first*.
- The lane lives at `server/src/tee/windtunnel/`. Engines are separate processes found at call time; registration is unconditional, because a tool that vanishes when its engine is missing is indistinguishable from one that never existed.

## Measured facts (2026-09-07, this container — build ON them)

1. **ParaView cannot be asked anything without a display.** The client builds a `QApplication` *before* it parses arguments: with `DISPLAY` unset, `paraview --help` prints `qt.qpa.xcb: could not connect to display`, aborts on signal 6 and exits **1**. So the lane can never learn its flags from the binary, and `wt_open` must decide about the display *before* it spawns anything.
2. **`--state TEXT`** loads a `.pvsm` or `.py` at startup, and *"Excludes: `--script`, `--data`, `filenames`"* — verified 2026-09-07 at `https://docs.paraview.org/en/latest/UsersGuide/commandLineArguments.html`, which documents the 6.1 line the owner's Mac runs. A value may follow a space or an `=`.
3. **`SaveState(filename)` and `LoadState(statefile, data_directory=…, restrict_to_data_directory=…, filenames=…)`** both exist in the installed ParaView Python (5.11.2 here). The remap arguments are a Python-side facility, not a client flag: `--data-directory` is for tests.
4. **A state file is a disk artefact, never an answer.** A one-reader state over a 16,000-cell case is **177,402 bytes**; a realistic one — reader, coloured surface, scalar bar, camera, time — is **203,042 bytes**. It names the case's absolute path **exactly once**, so relocating a case is a one-string rewrite rather than a re-generation.
5. **A state round-trips.** Written by one process and loaded by a fresh `pvpython`, the reader comes back with its `FileName`, the view with `ViewTime` 0.0 and `CameraPosition` `[0.5, 0.0, 273.224]`, and the representation still coloured by `['POINTS', 'p']`.
6. **`vsp [inputfile.vsp3]`** opens the model in the OpenVSP GUI — the model is a positional argument, and `vsp -script` is the headless route the lane already uses. `vsp` and `vspviewer` are both on PATH here (3.51.3).
7. **Writing a state needs no display at all.** It is XML on disk, produced by a render-free `pvpython` run. So `wt_open` succeeds in exactly the environment where `wt_view` fails — which is the strongest argument for the tool.
8. **A defect this campaign inherits:** `wt_export format=foam` refuses with `wt_no_results` until the case has a run, yet ParaView opens a *meshed* case perfectly well. The stub the GUI needs is gated behind a solve. P1 ungates it.
9. This container has `paraview`, `pvpython`, `vsp` and `vspviewer`; **FreeCAD is absent**, which is one reason CfdOF is out of scope.

## Prior art in this repo (copy these, do not reinvent)

- **`partkiln/src/partkiln/gui/`** is the panel's pattern: `actions.py` builds command dicts, `shell.py` applies them and formats what came back, `preview.py` draws — all three Qt-free and tested with PySide6 absent — and `app.py` is the ONLY Qt module, importing PySide6 *inside* its functions behind a `_require_qt()` gate, holding a `QMainWindow` by composition rather than subclassing it. Follow partkiln, not seamkiln: partkiln's own notes say a shell whose logic lived in the widgets *"would have shipped untested — which is exactly how seamkiln's follow-up buttons went eleven campaigns unexercised."*
- **Neither the panel nor ParaView gets a render pane.** partkiln refused a 3-D viewport on the ground that *"a second-rate GL widget inside Qt would be a worse picture and a whole new surface to maintain"*, and A67 ruled TEE builds no viewer. ParaView **is** the viewer; the panel drives the lane and hands off.
- **`kernel/handoff_import.py::land()`** is the escalation precedent: a `write-artifacts` tool that wants to do more asks the trust kernel in as many words (`registry.require(...)`) rather than exercising the stronger capability silently.
- **Refusal shapes to match:** `capture/apply.py`'s `capture_apply_staged` (*"needs its application live"*), the FreeCAD wire's `_START_FIX`, and `godot_missing`'s install line.
- **`windtunnel/paraview.py`** already holds `_reader_lines()` (a `.foam` stub or a `.vtu`, else `wt_field_missing`), `run_script()` (requires exit 0 **and** the literal `OK`), `argv_for()` (the xvfb rule) and `foam_stub()`. The state writer reuses all four rather than growing a second way to talk to pvpython.

## Design of record (doc 73 carries the detail)

### `wt_open` — one tool, two halves

| half | what it does | needs a display? |
|---|---|---|
| **prepare** (always) | ensures the `.foam` stub, writes `<case>/views/<name>.pvsm` through a render-free pvpython, returns `{app, state, target, command, bytes, launched: false}` | no |
| **launch** (`launch=true`) | spawns the application detached and returns `launched: true` with its pid | yes, or it refuses |

`app` is `paraview` (default: the results) or `openvsp` (the `.vsp3`). `view` picks the preset the state opens on, reusing `wt_view`'s names so one vocabulary serves both. The command is returned as an argv list and a copy-pasteable string, so a human on a machine TEE cannot reach still gets the answer.

Refusals: `wt_paraview_missing` / `wt_openvsp_missing` (install line), `wt_no_display` (the fix names the platform's way), `wt_no_geometry` for an OpenVSP open with no `.vsp3`, `wt_state_failed` (last lines of pvpython's own output), and `wt_bad_action` for an unknown `app`.

**Trust:** `wt_open` is tabled `write-artifacts` — a state file on disk is the same category as `wt_view`'s PNG — and there is still **no `wt_` family row**. The spawn is the escalation, so `launch=true` calls `registry.require` for it by name before anything is started.

### The panel — `server/src/tee/windtunnel/gui/`

`actions.py` (Qt-free) turns each control into a command dict; `shell.py` (Qt-free) applies them through the registry and formats the case list, the run's status line, the verdict and the refusal text; `app.py` is the only Qt module. It shows the cases, the runs under one, and four buttons: run, cancel, open in ParaView, open in OpenVSP. It never renders a field and never polls a solver itself — `tee_job` already answers that.

Launch: `python -m tee.windtunnel.gui.app --project <dir>`. Extra: `[gui]` (PySide6, LGPL-3.0, imported inside functions). Tests drive `shell` with no window at all, and a fresh interpreter asserts PySide6 never reaches `sys.modules` when the Qt-free modules are imported.

## Phases

- **P0** — the measurements above, the superseding ruling in `docs/DECISIONS.md` (quoting *"headless only for now"* as A72 wrote it), this script and doc 73. *Acceptance:* every fact carries the command that produced it; the ruling names the three owner decisions verbatim.
- **P1** — `state.py`, `wt_open`, the trust row, the `.foam` ungating, fake ParaView and OpenVSP GUI binaries in the fixtures, and a hermetic test per refusal. *Acceptance:* the whole tool exercised with no real GUI; `launch=true` refuses without a display; the surface is still 17 tools.
- **P2** — the `cfd` tier: a state written over a really solved case and loaded back in a fresh `pvpython`, asserting reader, file, time, camera and coloured array; a state over a meshed case with no run; the OpenVSP route on a real `.vsp3`. *Acceptance:* byte sizes and wall times recorded in PROGRESS.
- **P3** — the panel. *Acceptance:* every control tested through the shell with Qt absent; the fresh-interpreter test; the window opens on a machine that has PySide6, or refuses by naming the extra.
- **P4** — `docs/windtunnel-gui.md` on the `docs/partkiln-gui.md` template, the lane guide and setup doc, doc 72 §9 item 5 marked closed, the `CLAUDE.md` bullet, CHANGELOG, PROGRESS, the search-budget re-measure (`wt_open` joins the registry), the version bump ×3, the bundle, and a draft pull request. *Acceptance:* the recall table re-measured rather than reasoned about, and the closing `**Suites at close:**` line.

## Laws

1. **TEE builds no viewer.** ParaView is the viewer; the panel is a control surface.
2. **A state file is disk, never an answer** — 200 KB of XML; the reply carries its path and byte count.
3. **Prepare always, spawn only when asked**, and never behind the caller's back.
4. **The display is decided before the spawn**, because ParaView aborts rather than reporting.
5. **One vocabulary**: the panel and `wt_open` use `wt_view`'s preset names.
6. **The GUI is a client of the same case directory** — no second store, no second format.
7. Zero always-loaded tools; `wt_open` tabled individually; no family row.
