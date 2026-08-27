# Mac handoff — what only the physical machine can finish

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

The code is restored and green (server 41 voxkiln tests); the live lane
was never re-run after the delete/restore cycle.

- Recreate the venv per `voxkiln/README.md`; reinstall into the server
  venv.
- Re-fetch weights if they were cleaned (~15 GB); the gated DINOv3
  access is approved — verify the download actually succeeds now.
- First live generation on MPS; then same-seed determinism (two runs,
  same seed, hash the meshes).
- Stock-vs-ours defect battery into `voxkiln/BENCHMARKS.md`.

## 3. Install-validate the packaged artifacts (Phase 6 close-out)

All three artifacts BUILD anywhere and were built + structurally
validated in the cloud on 2026-08-27 (`cd server && make dist`). What
the Mac owes is the *install* half:

- `tee-engine-0.1.0.mcpb` → drag into Claude Desktop, confirm the
  server starts and `tee_status` answers.
- `TeeToolset-0.1.0.zip` → unzip into a UE 5.8 project's `Plugins/`,
  confirm the toolset registers (OkongoSim already runs it from source;
  this validates the zip path for a fresh project).
- `tee_bridge-0.1.2.zip` → install as a Blender extension, confirm the
  bridge serves.

## 4. GPU/model lanes (Phase 9 + 7)

- Assets lanes 1–3 live on MPS: Z-Image, SDXL-tileable, Marigold-IID;
  `[assets-embed]` embeddings; the UE import path; Blender library
  authoring/`asset_listing` publishing.
- Extract: Whisper/pyannote quality spot-check on real site audio.

## 5. UE live physics (Phase 11 leftovers)

UE physics/settle (SIE), fluid bake validation, CoACD proxy
integration. Hip roof stays blocked on a straight-skeleton library —
that is a design decision, not a Mac task.

## 6. Dropbox sync-back (owner's call, 2 files)

The cloud session ran the corpus's own `00_meta/rebuild.py` over the
in-repo mirror and converged it: the mirror's `manifest.json` (one
corrected record) and `INDEX.md` (a stale "399 files" line) are now
correct while the Dropbox originals still carry the stale versions.
If you want Dropbox consistent, copy those two files from
`knowledge-base/` back to `Dropbox/02 Okongo Oneleiwa Project/12 Expert
Knowledge Base/`. Content files are untouched — the mirror is
byte-identical to Dropbox everywhere else.

## Explicitly NOT owed

- Live-UEFN lanes: descoped 2026-08-22 (owner decision, no Windows
  machine).
- The dead Fortnite island test: removed 2026-08-27; the network lane
  now asserts the analytics error contract against an invalid island
  and depends on no specific creator island staying alive.
