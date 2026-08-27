# Mac handoff — what only the physical machine can finish

**STATUS 2026-08-27: every section below (§1–§6) is closed with
recorded evidence in `docs/PROGRESS.md`; hosted Tripo/Meshy keys were
descoped by owner decision. Nothing remains on this list. Named
follow-ups live where they belong: the full research-48 battery matrix
in `voxkiln/BENCHMARKS.md`, the hip-roof straight-skeleton design
decision in §5.**

Everything cloud-buildable is built, tested and pushed. This file is the
single list of what remains, why it needs the M5 Mac, and how each item
proves itself done. Work it in a Claude Code session opened in this repo
on the Mac; update `docs/PROGRESS.md` with real command output as items
close, and keep the standing rules (develop on
`claude/token-efficiency-engine-5jv1dj`, commit with the project's
authorship convention, never assert success without output).

A one-paste prompt for the Mac session:

> Read docs/mac-handoff.md and docs/PROGRESS.md. Work the handoff list
> top to bottom, checking items off in PROGRESS.md with real evidence.
> Stop and report if any item's premise no longer holds.

## 1. OkongoSim: the `[kb]` config line (Phase 16 acceptance #4)

**DONE on the Mac 2026-08-27** — both OkongoSim commits made
(`47973f6fc` config, `58faa8a0a` docs) and the live `kb_search` →
`kb_read` proof exchange recorded in PROGRESS.md ("handoff §1").

OkongoSim lives only at `/Users/john/OkongoSim` (not on GitHub), so this
could not be done from the cloud. Two small commits there:

1. Append to the tracked `.tee/config.toml` (it already carries
   `[pins] namespace = "okongo_pin"`):

   ```toml
   [kb]
   root = "/Users/john/TokenEfficiencyEngine/knowledge-base"  # adjust to the clone
   ```

2. Add `docs/tee-kb.md` beside `docs/tee-pins.md` — copy the OkongoSim
   section of TEE's `docs/setup-kb.md` and point to it from OkongoSim's
   CLAUDE.md, same pattern as the pin handoff.

Proof: from a session driving OkongoSim, one `kb_search` for a site
question (e.g. paving spec) returns hits and one `kb_read` returns a
flagged, cited section. Record the exchange in PROGRESS.md.

## 2. Voxkiln live bring-up (Phase 13's second half)

**DONE on the Mac 2026-08-27** — evidence in PROGRESS.md ("handoff §2
(Voxkiln live bring-up) CLOSED") and `voxkiln/BENCHMARKS.md`.

The code is restored and green (server 41 voxkiln tests); the live lane
was never re-run after the delete/restore cycle.

- ~~Recreate the venv per `voxkiln/README.md`; reinstall into the server
  venv.~~ Recreated (`uv sync --extra model`); server venv imports
  voxkiln 0.1.0.
- ~~Re-fetch weights if they were cleaned (~15 GB); the gated DINOv3
  access is approved — verify the download actually succeeds now.~~
  Moot: the HF cache was never cleaned (~18 GB incl. TRELLIS.2-4B);
  `voxkiln doctor` shows gated DINOv3 `accessible: true`. Nothing
  downloaded.
- ~~First live generation on MPS; then same-seed determinism (two runs,
  same seed, hash the meshes).~~ First gen `state=done` in 1294 s
  (490,280 tris, T.png seed 7); two fresh-subprocess seed-42 runs both
  hashed `52b60b5bf50b3502` — deterministic on this device. Two real
  product bugs found and fixed en route (quadratic `_winding_for_fill`,
  `None` CLI params over `export_glb` defaults).
- ~~Stock-vs-ours defect battery into `voxkiln/BENCHMARKS.md`.~~ First
  tranche measured (4/4 rows, 2 images × seed 42 × both arms) with the
  honest finding that the arms are hash-identical on MPS: the gated
  decode head already runs fp32 there (measured), so the fp16-threshold
  fixes are no-ops on this backend and the "ours improves over stock"
  claim is scoped to fp16 backends. Full research-48 matrix stays open
  as future work, stated in BENCHMARKS.md — not silently sampled.

## 3. Install-validate the packaged artifacts (Phase 6 close-out)

All three artifacts BUILD anywhere and were built + structurally
validated in the cloud on 2026-08-27 (`cd server && make dist`). What
the Mac owes is the *install* half:

- ~~`tee-engine-0.1.0.mcpb`~~ — DONE on the Mac 2026-08-27: owner
  dragged the bundle into Claude Desktop (installed as
  `local.mcpb.interaeronav.token-efficiency-engine`); Desktop's
  `mcp-server-Token Efficiency Engine.log` shows the installed server
  answering the handshake (initialize → notifications/initialized →
  tools/list result, zero errors). `tee_status` answering on the
  manifest's exact command was proven in the 08-27 stdio rehearsal; an
  in-chat call wasn't log-captured (Desktop quit right after install)
  and is a 30-second optional check. Evidence in PROGRESS.md.
  *Later the same day:* the optional check happened for real — the
  0.1.1 bundle was re-dragged, the required `project_root` user-config
  gotcha was found and documented, and `tee_status` answered in situ
  through the Desktop-managed server (PROGRESS "§3 final acceptance").
- ~~`TeeToolset-0.1.0.zip`~~ — DONE on the Mac 2026-08-27: unzipped into
  a fresh UE 5.8 project (`~/Documents/Unreal Projects/TeeZipProbe`,
  plugin from the zip only), editor boot runs the plugin's
  `init_unreal.py` and registers
  `tee_toolset.toolsets.editor.TeeEditorTools` with zero Python
  errors/warnings; independently re-verified same day with a second
  clean boot from an owner-downloaded copy of the zip (extracted trees
  byte-identical). Evidence in PROGRESS.md. OkongoSim's source install
  was left untouched.
- ~~`tee_bridge-0.1.2.zip`~~ — DONE in cloud 2026-08-27: validated,
  installed (`blender --command extension install-file`), enabled, and a
  live wire round-trip served from the installed extension
  (`{'status': 'ok', 'result': {'v': '5.2.0 LTS', 'objs': 3}}`). Nothing
  left for the Mac on this artifact.

## 4. GPU/model lanes (Phase 9 + 7)

**DONE on the Mac 2026-08-27** — evidence in PROGRESS.md ("handoff §4
first pass", "§4 continued", "handoff §4 + §5 CLOSED").

- ~~Assets lanes 1–3 live on MPS: Z-Image, SDXL-tileable, Marigold-IID;
  `[assets-embed]` embeddings; the UE import path; Blender library
  authoring/`asset_listing` publishing.~~ All live with recorded output:
  Z-Image-Turbo via `as_generate` (83.4 s, provenance stamp), the
  SDXL-tileable driver written this day (seam_ratio 0.922, tileable
  true), Marigold-IID refinement written behind `as_photo_material`
  (live on a real drone frame), SigLIP-2 embeddings ranking sanely,
  voxkiln GLB → `as_ingest` → `as_import` into UE with exact read-back,
  and `as_publish_library` → Blender's own `asset_listing` index with
  licenses travelling per asset. Hosted Tripo/Meshy keys: DESCOPED by
  owner decision ("not interested").
- ~~Extract: Whisper/pyannote quality spot-check on real site audio.~~
  Whisper large-v3 on 8 real iPhone site clips: zero hallucinated
  segments, the walkthrough transcribed fluently; pyannote diarization
  live after the owner accepted the HF gate (three pyannote-4.x API
  drifts found and fixed en route). Quality: PASS.

## 5. UE live physics (Phase 11 leftovers)

**DONE on the Mac 2026-08-27** — evidence in PROGRESS.md ("handoff §4 +
§5 CLOSED").

~~UE physics/settle (SIE), fluid bake validation, CoACD proxy
integration.~~ `ue_settle` live against the real editor (settled true,
poses adopted, capture recorded); `sim_fluid` bake against the real
headless bridge (750-file cache written); `sim_proxy` (CoACD) written
with a hash-keyed cache and proven on the 491,888-tri generated mesh
(24 hulls, 60:1, cache hit on the second call). Hip roof stays blocked
on a straight-skeleton library — that is a design decision, not a Mac
task.

## 6. Dropbox sync-back (owner's call, 2 files)

**DONE on the Mac 2026-08-27** — both files copied and verified
byte-identical to the repo mirror (sha256 match); evidence in
PROGRESS.md ("handoff item 6").

The cloud session ran the corpus's own `00_meta/rebuild.py` over the
in-repo mirror and converged it: the mirror's `manifest.json` (one
corrected record) and `INDEX.md` (a stale "399 files" line) are now
correct while the Dropbox originals still carry the stale versions.
If you want Dropbox consistent, copy those two files from
`knowledge-base/` back to `Dropbox/02 Okongo Oneleiwa Project/12 Expert
Knowledge Base/`. Content files are untouched — the mirror is
byte-identical to Dropbox everywhere else.

The cloud session attempted this on 2026-08-27: the clean path (a file
request + browser upload of the exact bytes) was blocked by the
permission classifier, and regenerating 680 KB of file content inline
risks silent transcription corruption, so it was deliberately not
forced. On the Mac it is one command from the TEE clone:

```sh
cp knowledge-base/manifest.json knowledge-base/INDEX.md \
  ~/Dropbox/"02 Okongo Oneleiwa Project"/"12 Expert Knowledge Base"/
```

## Explicitly NOT owed

- Live-UEFN lanes: descoped 2026-08-22 (owner decision, no Windows
  machine).
- The dead Fortnite island test: removed 2026-08-27; the network lane
  now asserts the analytics error contract against an invalid island
  and depends on no specific creator island staying alive.
