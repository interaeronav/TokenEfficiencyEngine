# 73 — the wind-tunnel GUI handoff: what the applications actually accept

Design of record for **A73** (`CLAUDE_A73_SCRIPT.md` is the plan). Written 2026-09-07. Every number below was measured in this container or read at a primary source on that date; nothing here is remembered.

## 1. What is being closed

A72 shipped the wind-tunnel lane headless and deferred one thing by owner decision: *"headless only for now"* — no `wt_open`, no `.pvsm` state files, no Qt panel. The deferral was written as gap 1 in `docs/PROGRESS.md` and as open question 5 of doc 72, both of which said the same thing: *the case directory, the `.foam` stub and the `.vsp3` are exactly the files those GUIs open*. This campaign is that gap, with the owner's three answers of 2026-09-07: prepare always and launch on request, the panel is in scope, and the applications are ParaView and OpenVSP.

The premise held. Nothing about the case directory had to change for a GUI to read it — which is the point of having made the directory the interface in the first place.

## 2. The measured facts

### 2.1 ParaView refuses to be interrogated without a display

```
$ unset DISPLAY; paraview --help; echo "rc=$?"
qt.qpa.xcb: could not connect to display
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
paraview:3605 terminated with signal 6 at PC=... Backtrace:
  ... QGuiApplicationPrivate::createPlatformIntegration ...
rc=1
```

The client constructs its `QApplication` **before** it parses arguments, so even `--help` dies. Two consequences, and both are design constraints rather than annoyances:

- The lane cannot discover ParaView's options by asking ParaView. They come from documentation, cited with a date.
- `wt_open` must decide about the display *before* it spawns, because a spawn that fails this way reports a Qt plugin error, not a useful one.

### 2.2 The startup flag, from the source

`--state TEXT` — *"State file (`.pvsm` or `.py`) to load when the application starts. Excludes: `--script`, `--data`, `filenames`."* Read 2026-09-07 at <https://docs.paraview.org/en/latest/UsersGuide/commandLineArguments.html>, which documents the 6.1 line the owner's Mac runs; the container has 5.11.2, where the flag is long-standing. A value may follow a space or an `=`. `--data-directory` exists but is *"Directory containing input data files for tests"* — not a state remap.

### 2.3 The Python side has a remap the client does not

```
SaveState(filename)
LoadState(statefile, data_directory=None, restrict_to_data_directory=False, filenames=None, *args, **kwargs)
```

Both present in the installed `paraview.simple` (5.11.2). So a state whose data has moved can be re-pointed from Python, while the GUI's own `--state` takes it as written. This is why TEE writes the state next to the case it describes.

### 2.4 A state file is big, and names its case once

| pipeline | bytes |
|---|---:|
| reader only, `internalMesh` | 177,402 |
| reader + coloured surface + scalar bar + camera + time | 203,042 |

Both over the same 16,000-cell NACA 0012 case. The absolute path of `case.foam` appears **exactly once** in the XML. Two conclusions: a state never travels in a tool reply (the reply carries its path and size), and relocating a case is a single string rewrite rather than a regeneration.

### 2.5 A state round-trips between processes

Written by one `pvpython` and read by a fresh one:

```
proxies restored: 1
  case.foam: OpenFOAMReader file=/.../cases/wt_268ad05e37/openfoam/case.foam
view time: 0.0 | camera: [0.5, 0.0, 273.224]
coloured by: ['POINTS', 'p']
```

The reader, its file, the camera and the colouring all survive. That is the whole mechanism the handoff needs, and it is verified rather than assumed.

**Read that `view time: 0.0` again.** The case has one time directory, 197, and the state came back at 0. It was written down as a success and it was the defect §2.10 found five days' work later, on a real solved case: printing a number is not the same as checking it.

### 2.6 OpenVSP takes the model as an argument

```
$ vsp --help
          Vehicle Sketch Pad 3.51.3
Usage: vsp [inputfile.vsp3]               Run interactively
     : vsp -script <vspscriptfile>        Run script
```

The GUI route is the positional argument; `-script` is the headless route the lane already drives. `vsp` and `vspviewer` are both on PATH here.

### 2.7 A state that carries a view needs a display; a pipeline-only state does not

This was measured after being assumed wrongly, which is the reason it is written out in full.

| script | display | result |
|---|---|---|
| reader + `Show` + `ColorBy` + camera + `Render` | none, plain `pvpython` | **SIGSEGV**, rc 139 |
| the same | none, `--force-offscreen-rendering` | **SIGSEGV**, rc 139 |
| the same | `xvfb-run -a` | 203,042 bytes, rc 0 |
| reader + arrays + time, no `Show`, no `Render` | none, plain `pvpython` | **16,545 bytes, rc 0** |

The fault is the one doc 72 §3 already recorded for the apt build: a render view without a display segfaults, and the offscreen flag does not save it. But a state does not have to carry a view. A pipeline-only state - the reader, its mesh regions, its arrays, its time - is an eighth of the size, writes anywhere, and still opens the case in ParaView with everything selected; the human colours it in two clicks.

So `wt_open` writes the richer state where it can render (a display, or `xvfb-run` on Linux) and the pipeline-only state where it cannot, and the reply says which it wrote. The tool therefore works on a headless container, which is exactly where a model driving TEE usually is.

### 2.8 A defect inherited from A72

`wt_export format=foam` refuses with `wt_no_results` until the case has a run:

```
tee.kernel.errors.TeeError: Case wt_70274f18dd has no runs yet.
```

But ParaView opens a meshed case with no solution perfectly well, and looking at a mesh before spending an hour solving on it is one of the better reasons to open ParaView at all. The stub is a property of the case, not of a run. A73 P1 ungates it.

### 2.9 What this machine has

`paraview` 5.11.2, `pvpython`, `vsp` and `vspviewer` 3.51.3 are present; **FreeCAD is not installed**, which is one reason CfdOF stays out of scope and its C2/C3 rows stay open.

### 2.10 What running it on the real applications found (P2, 2026-09-07)

The hermetic tests drive a fake `pvpython` that accepts any script it is given, so they prove the lane's plumbing and nothing about ParaView. Running P2 against the real one found **three defects**, all in code that had already shipped:

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | `wt_open view=mesh` on a meshed case **fails**: `RuntimeError: invalid association string 'NONE'` | `ColorBy(d, None)` — the documented way to turn colouring off — re-reads the representation's *current* association, and that is `'NONE'` when the data carries no array to auto-colour by | `ColorBy(d, ('CELLS', None))`: names a valid association, unsets the array, works with fields and without |
| 2 | The state opens at **t=0** rather than at the solution | `rv.ViewTime` is not what a state carries; the animation scene is, and `SaveState` writes the scene's time | `GetAnimationScene()` → `UpdateAnimationUsingDataTimeSteps()` → `AnimationTime = ts[-1]`, in both state kinds |
| 3 | `wt_open` on an **SU2** case dies: `NameError: name 'ts' is not defined` | `paraview._reader_lines` binds `ts` in its `.foam` branch and not in its `.vtu` one, while `state_script` reads it in both — so the handoff worked for one engine and crashed for the other | the `.vtu` branch binds `ts = list(getattr(src, 'TimestepValues', []) or [])`; a single `.vtu` has no time steps, and an empty list is the honest value |

Defect 1 bites exactly the case the mesh view exists for — looking at a grid *before* spending an hour solving on it — and it could not have been found any other way: `wt_view` cannot reach that code path, because it refuses without a run. Defect 2 is the worst of the three: a state that opens the initial field is not an error, it is a wrong answer that looks like a right one. Defect 3 is the plainest: half the lane's engines had never had this tool run against them at all, and one `NameError` is what a whole engine's handoff was worth. All three are pinned twice now - by the live tests that found them, and by hermetic assertions on the generated script text, which is the only guard that runs where ParaView is not installed.

With all three fixed, measured on ParaView 5.11.2 + xvfb over the 16,000-cell NACA 0012 case at 197 iterations:

| what | bytes | write | read back |
|---|---:|---:|---:|
| `full`, solved case, `view=pressure` | 206,584 | 4.5 s | 3.6 s |
| `full`, meshed case, no run, `view=mesh` | 179,725 | 3.1 s | 3.5 s |
| `pipeline`, solved case, **no display either way** | 17,233 | 2.7 s | 2.8 s |

and what the fresh `pvpython` reports after `LoadState`:

```
reader OpenFOAMReader   file .../runs/run_001/case.foam   cells 16000
view time 197.0   scene time 197.0   timesteps [197.0]
colour ['CELLS', 'p']   representation 'Surface'   camera [0.5, 0.0, 273.2237]
```

`relocate()` replaced **1** occurrence over a copied run, and the relocated state loaded 16,000 cells at t=197 from the new path — so the "the path appears exactly once" law of §2.4 holds for a state ParaView wrote, not only for one we predicted.

An SU2 `.vtu` source now writes both kinds too: **198,796 bytes** full, **12,089 bytes** pipeline, and the reload reports `XMLUnstructuredGridReader` on the file it was given.

The OpenVSP route was verified by asking OpenVSP rather than by the file existing: `vsp -script` on a script that reads the `.vsp3` the command line names reports `GEOMS=1`, `WingGeom`, type `Wing`, from an 86,830-byte model. The AngelScript name is `FindGeoms()`; `GetGeomIDs` does not exist.

A72's own live tier was re-run on this build after the fixes — `wt_probe_field` render-free, the presets rendered offscreen, the cancel, the parallel run, the adoption smoke and the two verification cases — and is unchanged.

**Why `paraview.py` keeps `ColorBy(d, None)`.** The same call sits in `render_script`, and it is left alone deliberately: `wt_view` reaches it only through `_volume_source`, which refuses without a run, and a run always writes fields — so the association is never `'NONE'` there. `wt_open` is the one path that deliberately works without a run (`_open_source` exists for that reason), which is why the defect is the handoff's and not the renderer's.

## 3. Why the handoff is shaped this way

**Prepare and launch are separated because they fail differently.** Preparing needs a case and pvpython; launching needs a display and a human at it. Splitting them means the common case — a model driving TEE on a machine the owner is not sitting at — still produces something useful: the state file, and the command to open it. This is the owner's decision of 2026-09-07, and it also happens to be the only shape that works over a remote session.

**Spawning is an escalation, so it is asked for.** No code in this repository has ever opened a window: every `subprocess` in `server/src/tee` is a headless child. `kernel/handoff_import.py` set the precedent for a tool that wants to do more than its capability — it calls `registry.require` in as many words rather than exercising the stronger one silently. `wt_open` follows it: writing the state is `write-artifacts`, and `launch=true` asks for the spawn by name.

**The panel is a control surface, not a viewer.** A67 ruled TEE builds no viewer, and partkiln refused a 3-D pane on the ground that a second-rate GL widget would be *"a worse picture and a whole new surface to maintain"*. The panel lists cases, starts and cancels runs, shows the verdict, and hands off. The picture belongs to ParaView.

**The panel copies partkiln's split, not seamkiln's.** Three Qt-free modules and one Qt module, Qt imported inside functions, composition over subclassing, launched by `python -m` with no console script. partkiln's own notes give the reason: logic that lives in widgets ships untested, *"which is exactly how seamkiln's follow-up buttons went eleven campaigns unexercised."*

## 4. What this campaign does not do

- **FreeCAD and CfdOF** (owner decision): the C2/C3 rows of the A72 Mac checklist stay open.
- **A render pane, ever.** See above.
- **SimFlow**: still not integrable as software; a case it writes is adoptable like any other.
- **Remote or client/server ParaView** (`pvserver`, `--url`): out of scope; the handoff is to an application on the same machine as the case.
- **A state that regenerates itself** when a case moves: the path appears once, so a later campaign can rewrite it if the need is real.

## 4b. ParaView: the instability was ours (2026-09-07)

Raised while this campaign was being built: ParaView was proving unstable —
*"would just refuse to start"* — and the owner's local session went looking for
a replacement. It found the cause instead, on the owner's Mac, and **the cause
was this lane**:

> `pvpython` imports its own modules from INSIDE the signed `.app` bundle, and
> CPython caches bytecode next to the source: **201 `.pyc` files** written into
> a notarized bundle on one run (measured 2026-09-07). Files added to a sealed
> bundle invalidate its code signature — `codesign` then reports *"a sealed
> resource is missing or invalid"* — and macOS refuses to launch the
> application. Every `wt_probe_field` and `wt_view` call was damaging the
> owner's install until the GUI would not start.

`PYTHONDONTWRITEBYTECODE=1` in `paraview.run_script`'s environment is the fix
(base commit `c082dae`): 0 `.pyc` and `codesign` exit 0 with it, 201 and exit 1
without. Deleting the `__pycache__` directories inside the bundle restores the
seal; no reinstall. The handoff inherits the guard without doing anything,
because `state.write()` drives the same `run_script` — so writing a state has
never been able to write into the bundle since that commit landed.

So no swap is being made. This section stays, for two reasons.

The first is precision about what this campaign *did* measure. The three
instabilities below were **measured here**, not reported — a declaration is a
claim and a measurement is evidence (A65) — and they remain true of the tool.
They are also the reason the lane is shaped as it is: the display check in
`wt_open`, the two state kinds, and `xvfb-run` in `argv_for` all exist because
of them. But **none of them was the fault above.** A tool that aborts without a
display is behaving badly; a tool that will not start at all was a tool we had
broken, and reading the first as evidence for the second would have been the
wrong conclusion drawn from real data.

1. **It cannot be asked anything without a display.** The client builds its Qt
   application before parsing arguments, so `paraview --help` aborts on signal
   6 (§2.1). No other tool in this repo behaves that way.
2. **A render view without a display segfaults**, and
   `--force-offscreen-rendering` does not save it - only `xvfb-run` does
   (§2.7, and doc 72 §3 recorded the same for `wt_view`).
3. **A trivial state file is 200 KB of XML** whose schema is versioned against
   the writing application (§2.4, open question 1).

The second is the specification the search produced. It is worth keeping
whether or not it is ever used, because it is the shortest true statement of
what this lane needs from a viewer - a much shorter list than what ParaView
does:

| need | why | ParaView's answer |
|---|---|---|
| open an OpenFOAM case directory | the case directory is the interface | `.foam` stub + OpenFOAMReader |
| open an SU2 volume file | the other engine | `.vtu` reader |
| be told what to show, from the command line | a handoff is one command | `--state` |
| sample a line and a slice to CSV, render-free | `wt_probe_field` | `PlotOverLine`, `SaveData` |
| write a PNG offscreen | `wt_view` | `SaveScreenshot` under xvfb |

Anything that covers those five rows can replace it without touching the tool
surface: `wt_open`'s `app` is an enum, the ParaView-specific parts are
confined to `state.py` and `paraview.py`, and the panel calls the registry
rather than any application. The two candidates worth measuring first are
**glvis/VisIt-class viewers** and **PyVista/trame with an offscreen backend** -
but neither has been measured here, and this table is the specification to
measure them against, not a recommendation.

**What the resolution changed, and what it did not.** Nothing in the lane was
bent toward the search while it was open - no ParaView-specific capability was
deepened while a replacement was in question - and nothing is being unbent now.
What it unblocked is P2: the live tier ran in full on the real ParaView instead
of the narrowed OpenVSP-only route, which is how the three defects in §2.10
were found. The narrowing would have cost the campaign all three.

There is a lesson in the pairing. The lane spent this campaign measuring
ParaView's faults and shipped three of its own into the same tool; the
`.pyc` fault was invisible from here because this container's ParaView is an
apt install with nothing to seal, and the state defects were invisible because
the fake `pvpython` accepts any script. Both needed the real application, on a
real machine, doing the real thing.

## 5. Open questions

1. Does ParaView 6.1 on the owner's Mac accept a 5.11-written state file? States are versioned; the reverse direction is the one that usually breaks. The Mac session answers it, and until then the lane writes with whatever `pvpython` the machine has, which is the same install the GUI came from.
2. Does `open -a ParaView --args --state=<file>` pass the flag through on macOS as it does on Linux? Documented as the macOS idiom, not yet measured — a Mac row.
3. Should the panel show the polar plot a sweep produces? It would need a plotting widget, which is the thin end of a viewer. Deferred until asked for.
