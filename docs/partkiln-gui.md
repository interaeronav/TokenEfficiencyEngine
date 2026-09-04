# The partkiln shell (A66 gap 1)

A window over the same kernel the headless lane drives. Headless-first was the
owner's decision and it still is: this is a **client** of `partkiln.document`,
added after the kernel shipped, and the kernel does not know it exists.

```bash
uv pip install --python server/.venv/bin/python -e 'partkiln[gui]'
PYTHONPATH=partkiln/src server/.venv/bin/python -m partkiln.gui.app
```

`partkiln[gui]` is the only place PySide6 appears. Nothing is registered as a
console script — a kernel that installs a window on your PATH is not
headless-first — and **TEE gains no tool from this**: the surface is still
17 always-loaded tools / 2,033 tok. This is a package, not a tool.

## The one law

**A control builds a command; it never touches the model.**

Every button constructs the same `{op, kind, name, props}` dict a model sends
through `tee_batch` (A66 D5), hands it to the kernel, and shows the **diff the
kernel answered with** — volume, delta, faces, `assumed`, `resolved` — not a
re-read of the world. So there is no path through this window that a batch
cannot take, and "save script" is not an export feature: it is handing over the
history that was being kept anyway.

That is why the shell is testable with Qt absent, and why it is tested that
way. PySide6 is not installed on the machine that wrote it; `actions.py`,
`shell.py` and `preview.py` are Qt-free, `app.py` imports PySide6 inside its
functions, and `partkiln/tests/test_gui.py` drives all sixteen controls,
asserts the kernel's own numbers, and checks that `import partkiln` still loads
neither PySide6 nor OCP.

## What the window shows

| Pane | Source | Never |
| --- | --- | --- |
| Feature tree | `entities()` — the D7 rows | a shape, a mesh, a coordinate |
| Parameter table | the `param:` rows: value, unit, expression, `used_by` | a second copy of the model |
| Last diff | the answer to the last command | a re-read after the mutation |
| Preview | the SVG partkiln itself wrote | a second renderer |

**There is no 3D viewport and there will not be one from this package.** The
kernel ships no renderer, `pk_export` hands a body to Blender, and a
second-rate GL widget inside Qt would be a worse picture and a whole new
surface to maintain — the same call seamkiln's shell made, with the same honest
cost: you cannot orbit it. What you get instead is 2D and exact: the active
sketch, drawn through `partkiln.drawing.svg`'s own element emitters and
stylesheet, and the drawing sheet as the SVG file the kernel wrote, byte for
byte, at 1 user unit = 1 mm.

## The sixteen controls

Press them in order and you have driven the v1 loop. Each row is the command
the button emits.

| Button | Command |
| --- | --- |
| Parameters | `param_set` W H T PX PY R C |
| New part | `create part` (material `steel_s275`) |
| Sketch | `create sketch` — `rect [W, H]` on XY |
| Extrude | `create extrude` — `distance: T` |
| Fillet | `create fillet` — `edges: "<ex>:edges(dir=Z)"`, `r: R` |
| Chamfer | `create chamfer` — `edges: "<ex>:edges(of=end, loop=outer)"`, `d: C` |
| Hole | `create hole` — `on: "<ex>.end"`, `std: "M6 clearance normal"` |
| Pattern | `create pattern` — `of` the hole, `dx: PX`, `nx: 2` |
| Midplane | `create plane` — XZ offset `-H/2` |
| Mirror | `create mirror` — `of` the hole, about `plane:mid1` |
| Edit fillet | `set feat:fl1 {r: "R*1.6"}` |
| Set W | `param_set {W: "140mm"}` — the part family in one press |
| Delete last | `delete` the last feature, `cascade: true` |
| Check spec | `check` the built body against the **declared** W/H/T |
| Draw sheet | `create drawing` — two views, three dims, hole table |
| Export STEP | `export` AP242, round-trip verified |
| Save script | the history, as JSON, replayable to the same fingerprint |

Every length is a parameter or an expression over one, so the script the window
hands you is a part family, not one part.

Two commands do **not** land in the script, on purpose: `check` is a read and
`export` writes a file — neither changes the model. `create drawing` does land;
the SVG/DXF/PDF files are written by a separate render step, which is why
pressing Draw sheet twice does not add two sheets.

## What the shell does NOT do

Asserted, not remembered: `test_gui.py` checks these lists against
`document.VERBS`, `document.KINDS` and `client.known_methods()`, so a kind
added to the kernel and to neither list fails the test the same day.

**Coverage, measured 2026-09-04: 4 of 4 verbs, 10 of 37 `create` kinds, 12 of
25 kernel methods.** (35 became 37 the same day, when `coil` and `thread`
landed in the kernel and the test above failed until both were listed — which
is the point of asserting the list against the kernel rather than typing it.)

- **Verbs: all four.** `create`, `param_set`, `set`, `delete`.
- **Kinds with no button (27).** `revolve`, `sweep`, `loft`, `shell`, `draft`,
  `combine`, `split`, `import`, `sheet`, `object`; the datums `axis` and
  `point`; and the whole assembly layer — `component`, `insert`, `joint`,
  `mate`, plus the mate kinds `angle`, `flush`, `planar`, `tangent` and the
  joint kinds `ball`, `cylindrical`, `revolute`, `rigid`, `slider`.
  **There is no assembly in this window at all**: no components, no mates, no
  joints, no DOF, no interference, no BOM.
- **Kernel methods with no button (13).** `bom`, `flat` (sheet metal),
  `import`, `lint`, `materials`, `measure`, `query`, `standards`, `verbs`, and
  the checkpoint set `snapshot` / `restore` / `discard` — so the window cannot
  take or roll back to a checkpoint. `ping` is the worker's liveness probe.
- **No sketch editing.** You cannot drag a point, add a constraint, or
  re-dimension: the Sketch button emits one parametric rectangle. Everything
  else is a batch.
- **No selection.** Faces and edges are named by selector strings the controls
  write (D6). Nothing is pickable, because nothing is drawn in 3D.
- **One part per document.** A second part is refused with the fix.
- **No undo.** `delete` and `set` are the edits; the script is the history.

## The two honest refusals

**No kernel, no geometry.** With no OCP wheel the command mirror still answers,
so Parameters, New part, Sketch and Midplane work, and the geometry buttons
refuse once:

```
! [pk_kernel_absent] Extrude needs the B-rep kernel, and this one has no OCP.
  Install it with: uv pip install 'partkiln[brep]'
  (parameters, sketches, datums and the script work without it).
```

**No coordinates on the wire.** The sketch preview needs solved points, and D7
deliberately does not carry them (hard rule 1). On the in-process kernel it
draws; on a sidecar it refuses `pk_not_served` and tells you to read the
sketch's counts from its entity row, rather than growing a geometry channel for
a picture.

A control that cannot build its command names the button that comes first —
"no part yet: press New part.", "no datum plane yet: press Midplane first." —
and the document is untouched, the same contract as a refused command.

## Licence

PySide6 is LGPL-3.0 for the Qt modules it wraps, dynamically linked through the
published wheel, never vendored, and confined to the `gui` extra — the same
posture `partkiln[pdf]` takes with fpdf2. The core never imports it, and the
licence gate keeps the core's dependency list permissive.
