# CLAUDE_A51_SCRIPT.md — faster boots, a camera that checks its own work, and PDFs that can spell

**Owner directive (2026-08-31, verbatim):** *"improve and optimize booting
time of headless blender; improve and train camera framing skills of the
local vision model; improve the pdf capabilities add more fonts, characters
and other attributes available to high end providers."*

Written for a fresh Opus session with no memory of the one that researched
it. Every number below was measured on this machine on 2026-08-31 — build
ON them, do not re-litigate them.

## Orientation for a cold session

- Repo `/Users/john/TokenEfficiencyEngine`, code in `server/`. Branch
  `claude/token-efficiency-engine-5jv1dj` ONLY. Read `docs/PROGRESS.md`
  first; real command output into it per phase; commit+push per item.
- Suite `uv run pytest -q -m "not dcc"` from `server/` — expect **1,153
  passing / 17 skipped**, ruff clean. Surface invariant: **17 always-loaded
  tools, 2,034 tok** (`surface:` line of `uv run --project server python
  benchmarks/run_benchmarks.py`), budget ±10 around 2,028.
- **Upgrade trap:** every `.mcpb` install wipes the extension venv's
  extras. Restore with `uv pip install --python "<extension venv>/bin/python"
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]'
  'tee-engine[extract]' 'tee-engine[pdf]'`. TEE names the loss since 0.13.0.
- Local shim on `127.0.0.1:4000` (LiteLLM). **It was DOWN at the end of the
  research session** — connection refused, probably evicted when the 65 GB
  Qwen3.6-35B loaded. Restart before P2:
  `litellm --config ~/.claude/qwen-local/litellm.yaml`. Every phase here
  must degrade honestly when it is down, never hang.
- Blender bridge usually live on 9876 (the chair scene, 45 objects).

---

## Area 1 — Blender boot: the engine is not the problem

**Measured, and it inverts the premise.**

```
bare headless Blender          0.42 - 0.75 s
+ the 3.8 MB chair scene       0.55 s
TEE bridge answering           ~0.30 s
what TEE actually WAITS        0.50 s   <- the benchmark's own stage timer
```

Blender is not slow. **The wait is quantised.** `benchmarks/run_benchmarks.py`
polls `wire.probe()` every `0.5 s`, so a bridge that is ready at 0.30 s is
not noticed until 0.50 s. `adapters/godot/adapter.py:384` does the same at
`0.4 s`. Nobody is waiting on an engine; they are waiting on a sleep.

### P0 — stop sleeping through the answer

Replace fixed-interval polling with a **tight backoff** (e.g. 20 ms
doubling to 200 ms, cap unchanged) everywhere a launcher waits for a
bridge: the benchmark harness, `GodotAdapter.ensure_bridge`, and any
Blender launch path that polls. Measure before and after on the SAME
machine state and record both.

*Acceptance:* the benchmark's `[battery] bridge up` line drops from 0.5 s
toward the ~0.3 s the bridge actually needs; no test starts flaking; the
60 s ceiling is untouched.

### P1 — the boot that is worth removing is the second one

The real saving is not 200 ms; it is **not booting at all**. Investigate
and report, then implement only what measures well:

- Is a bridge left running between TEE sessions, or re-launched each time?
  (`GodotAdapter.ensure_bridge` already returns `{"started": False,
  "reason": "already running"}` when it finds one — check whether
  Blender's path does the same, and whether anything reaps them.)
- A `--factory-startup` Blender launch skips user addons and prefs.
  Measure it: if it saves real time and the bridge does not need the
  user's addons, adopt it and say why in the docstring.
- The bridge's own import cost (`bridge_server`) — measure it before
  assuming it is free.

*Acceptance:* a numbers table in PROGRESS: cold boot, warm reuse, and
whichever of the above actually paid. **Do not adopt a change that saves
less than it complicates** — the honest outcome may be "boot is 0.55 s and
the only real win was the poll interval", and that is a finding, not a
failure.

---

## Area 2 — the camera cannot see its own framing

`codegen.program_capture_look` places the temp camera by:

```python
radius = bbox_diagonal/2 * distance      # distance defaults to 2.2
```

Three gaps, in order of how much they hurt:

1. **The fit ignores the lens and the aspect ratio.** No `cam_data.lens`
   is set, so Blender's default 50 mm applies, and a 16:9 frame is fitted
   with a formula that knows about neither. A tall subject and a wide
   subject at the same "distance" fill wildly different fractions of frame.
2. **Nothing checks the result.** The render is returned whatever it looks
   like. The subject can be cropped, or a speck, and TEE reports success.
3. **The subject filter is a guess:** `[o for o in meshes if _extent(o) <=
   6 * median]` drops outliers, which usually removes a backdrop and
   occasionally removes the subject.

**The research also produced a methodological finding worth keeping.** An
attempt to measure "how much of the frame is filled" with a brightness
threshold reported **100% fill at every distance** — it was measuring the
grey backdrop, not the subject. A pixel heuristic cannot judge framing on a
rendered scene. **The instrument that can is the vision model**, which is
also exactly what the owner asked to improve.

### P2 — a lens-aware fit (deterministic, no model needed)

Set the camera lens explicitly and solve the distance from the bounding box
and the sensor/aspect, so the subject occupies a target fraction of the
SHORTER frame axis (default ~0.8, so nothing touches the edge). Keep
`distance` as a multiplier ON TOP of the solved fit, so existing callers
keep working and `distance=1.0` means "fit exactly".
*Acceptance:* for a tall subject and a wide subject, the rendered subject
occupies a comparable fraction of frame — measured by rendering with a
plain background and thresholding, which IS valid when the background is
controlled. Record both numbers.

### P3 — `sense_frame`: the model grades the shot, and TEE re-aims

The loop the owner is asking for. Render → ask the local VLM a *structured*
question → adjust → re-render, at most N times (default 2 retries; each
render is seconds and each judgement is a model call, so the budget is
real):

```json
{"fill_percent": 12, "cropped": false, "verdict": "too far",
 "suggest": {"distance": 0.6}}
```

Take the model's verdict as ADVICE, not truth — it is a summary another
model wrote, per the A47 law. So: bound the retries, log every attempt with
its verdict in the answer, and if the loop does not converge, return the
best attempt WITH the fact that it did not converge. Never loop silently.

**This is "training" in the honest sense**: not fine-tuning weights, which
this machine cannot do for a 17 GB model in any reasonable time, but
building the feedback loop that makes the model's judgement actually steer
the camera. If a phase claims to "train" the model, it must say what was
trained, on what data, and show a before/after score — otherwise call it
what it is.

*Acceptance:* on the chair scene, a deliberately bad starting distance
(0.5 and 5.0) converges to a framing the model calls "good" within the
retry budget; the answer carries every attempt; with the shim DOWN the tool
refuses with the local_vlm fix line and does not hang.

---

## Area 3 — the PDF lane cannot write ordinary prose

**Measured against `pdf_compose` as shipped:**

```
ASCII                     OK
Latin-1 accents           OK    façade Ökonomie naïve Ångström
maths/units               OK    3.5 m², 45°, ±2 mm
curly quotes “ ” ’        FAIL  FPDFUnicodeEncodingException
em dash —                 FAIL
Greek α β Δ               FAIL
CJK 建築                   FAIL
emoji                     FAIL
```

The boundary is Latin-1, because the lane uses fpdf2's **core fonts**.
The damaging half is not CJK — it is **curly quotes and em dashes**, which
appear in almost any text an LLM writes or a user pastes from a document.
Today that does not degrade; it **raises**, so one smart quote destroys a
whole compose.

**The fix is proven, and it is nearly free.** 332 system TTF/TTC files
exist on this machine. Embedding `/System/Library/Fonts/Supplemental/Arial
Unicode.ttf`:

```
every probe round-trips: “as-built”  m²  建築  façade  α
resulting PDF: 21.7 KB   (the font on disk is 22.2 MB - fpdf2 SUBSETS
                          to the glyphs actually used)
```

**A trap that cost real probe time — do not rediscover it.** With an
embedded font, `multi_cell(0, h, text)` raises *"Not enough horizontal
space to render a single character"* on lines after the first. Passing the
width explicitly (`doc.epw`) works. Every `multi_cell` in `tee/pdf.py`
currently passes `0`.

### P4 — Unicode by default, with the font a declared choice

- `[pdf]` gains an optional `font` spec: a path, or a name resolved from
  the system font directories. **Do not vendor a font into the repo** —
  Arial Unicode is Apple-licensed and redistribution is not TEE's to grant;
  using a font already on the owner's machine is fine, and the licence
  position goes in DECISIONS.md alongside fpdf2's LGPL.
- Default behaviour when no font is given: keep core fonts (no new
  dependency, no behaviour change for existing callers) but **stop
  crashing** — either transliterate the handful of typographic characters
  that Latin-1 lacks (“ ” ’ — … → " " ' - ...) with a note in the answer
  saying so, or refuse with the exact fix. Decide from measurement:
  a refusal is right if silent substitution could mislead; a documented
  transliteration is right if it never changes meaning. **Say which was
  chosen and why.**
- Fix every `multi_cell(0, ...)` to pass an explicit width.

*Acceptance:* a compose containing curly quotes, an em dash, m², °, Greek
and CJK round-trips through pdfplumber with an embedded font; the same
compose without a font either transliterates with a stated note or refuses
with a fix; both paths tested.

### P5 — the attributes a high-end document has

fpdf2 2.8.8 offers **19 capabilities the lane does not use**. Add the ones
that earn their tokens, each as a block kind or a spec key, each tested:

- `table()` — a real table API with alignment, widths and headings,
  replacing the hand-drawn `cell` grid currently in `compose`
- `start_section()` — PDF bookmarks / outline, so a long report is
  navigable
- `set_author` / `set_subject` / `set_keywords` — document metadata
- `set_text_color` / `set_fill_color` / `set_draw_color` — a `style` key on
  blocks, and shaded table headers
- `set_link` / links — cross-references and URLs
- `header` / `footer` — running titles and **page numbers**
- `text_columns` — multi-column body text
- `write_html` — evaluate but be cautious: it is a second input language
  with its own failure modes; adopt only if it earns its surface

Keep the answer a summary (`{path, pages, bytes}`) — none of this changes
the rule that nobody gets a PDF inline. Keep `pdf_*` virtual: the surface
stays 17.

*Acceptance:* a single "site report" fixture exercising every new
attribute, read back with pdfplumber, plus `sense_describe` on a rendered
page confirming the visual attributes (colour, table shading) actually
landed — the senses lane checking the pdf lane, as A48 did for the stamp.

---

## Laws

1. Measured before and after, in the same units, in PROGRESS. A phase that
   cannot show a number did not happen.
2. Surface invariant: 17 always-loaded tools, 2,034 tok ±10.
3. No capability lost to gain another; no font vendored into the repo.
4. A refusal names its reason and the fix.
5. **Do not claim to have trained a model unless weights changed.** P3 is a
   feedback loop; call it one.
6. When a measurement contradicts the premise — as Area 1's did — say so
   plainly and record the real finding rather than optimising something
   that was never slow.

## Out of scope

Fine-tuning or LoRA-training any vision model; GPU/render-engine work
beyond setting a lens; PDF forms, signatures and encryption (still out
since A48); Blender addon management; and any change to the Godot or
senses lanes beyond the poll interval and the framing loop named above.
