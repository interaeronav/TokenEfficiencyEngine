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

The reader, its file, the view time, the camera and the colouring all survive. That is the whole mechanism the handoff needs, and it is verified rather than assumed.

### 2.6 OpenVSP takes the model as an argument

```
$ vsp --help
          Vehicle Sketch Pad 3.51.3
Usage: vsp [inputfile.vsp3]               Run interactively
     : vsp -script <vspscriptfile>        Run script
```

The GUI route is the positional argument; `-script` is the headless route the lane already drives. `vsp` and `vspviewer` are both on PATH here.

### 2.7 Writing a state needs no display

The state is produced by a render-free `pvpython` run, so `wt_open` works in exactly the environment where `wt_view` segfaults (doc 72 §3: the apt build cannot render without `xvfb-run`). A machine with no display can still prepare the handoff for a machine that has one.

### 2.8 A defect inherited from A72

`wt_export format=foam` refuses with `wt_no_results` until the case has a run:

```
tee.kernel.errors.TeeError: Case wt_70274f18dd has no runs yet.
```

But ParaView opens a meshed case with no solution perfectly well, and looking at a mesh before spending an hour solving on it is one of the better reasons to open ParaView at all. The stub is a property of the case, not of a run. A73 P1 ungates it.

### 2.9 What this machine has

`paraview` 5.11.2, `pvpython`, `vsp` and `vspviewer` 3.51.3 are present; **FreeCAD is not installed**, which is one reason CfdOF stays out of scope and its C2/C3 rows stay open.

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

## 5. Open questions

1. Does ParaView 6.1 on the owner's Mac accept a 5.11-written state file? States are versioned; the reverse direction is the one that usually breaks. The Mac session answers it, and until then the lane writes with whatever `pvpython` the machine has, which is the same install the GUI came from.
2. Does `open -a ParaView --args --state=<file>` pass the flag through on macOS as it does on Linux? Documented as the macOS idiom, not yet measured — a Mac row.
3. Should the panel show the polar plot a sweep produces? It would need a plotting widget, which is the thin end of a viewer. Deferred until asked for.
