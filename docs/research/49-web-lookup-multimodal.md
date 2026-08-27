# 49 — Web lookup with vision + sound on local AI infrastructure: viability (2026-08-28)

Verification basis: live measurements run this session on the M5 Max
(every number below came from a command executed 2026-08-28 unless it
cites a dated PROGRESS/BENCHMARKS row); source reads of
`server/src/tee/kernel/local_vlm.py`, `server/src/tee/assets/http.py`,
`server/src/tee/extract/audio.py`, the kb module, and the owner's
`~/.local/bin/claude-qwen` launcher. Token counts use TEE's canonical
`estimate_tokens` (the research-B4 caveat about the measure's separators
applies here exactly as it does to the surface figure).

## The question (owner ask, 2026-08-28)

Is a TEE `web_lookup` tool viable — budgeted, cited answers from the
open web, with **vision** (images understood server-side) and **sound**
(audio transcribed server-side), powered by **custom local AI
infrastructure** rather than client tokens or hosted APIs?

## Measured token economics — text (this session)

Three real public pages, fetched with stdlib urllib (TEE-style, honest
User-Agent), tag-stripped with a ~30-line stdlib parser, then cut to a
kb_read-style 500-token budget:

| Page | raw HTML | visible text | 500-tok extract | saving vs raw |
|---|---|---|---|---|
| Blender manual, bmesh | 102,809 tok | 22,797 | 497 | 99.5% |
| Wikipedia, block paving | 54,656 tok | 5,102 | 471 | 99.1% |
| PyPI, trimesh | 345,604 tok | 11,964 | 488 | 99.9% |

Fetches took 0.4–1.5 s. Even against clean visible text (what a good
host-side fetch tool delivers), the budgeted extract saves 90–96%. A
naive "give the model the page" is 2–7× the token cost of an entire
TEE session's always-loaded surface — per page.

## Measured — vision (this session, live)

Chain exercised end to end: web image → `local_vlm.describe()` →
LiteLLM shim (:4000) → mlx-vlm server (:8081, lazy-started, ~17 GB,
`claude-qwen-vl`).

- Input: Poly Haven `corrugated_iron_02` 720 px thumbnail (639 KB) —
  literally an `as_search` result class of image.
- Question: material + suitability as a weathered-roof texture
  reference. Answer in **5.9 s** (warm path; the shim itself came up in
  6 s; cold adds the VL lazy-start — Phase 17 recorded 18.2 s including
  it on a trivial image): "The material shown is corrugated metal,
  which is suitable as a weathered-roof texture reference due to its
  ribbed pattern and metallic appearance."
- Client cost: **41 tok** answer (+ ~15 tok question). Inlining the
  same 720 px image to the client costs ~691 tok before it says a word
  — a 94% saving on the vision step, and the reasoning itself ran at
  zero API cost on the owner's hardware.

## Measured — sound (this session, live)

Web MP3 (archive.org test file, 194 KB, 12 s speech) → faster-whisper
**large-v3** int8 on CPU: model load 1.7 s, transcribe **10.9 s**
(~1.1× real-time), correct English transcript, **31 tok** to the
client. Quality precedent at scale: the §4 spot-check (PROGRESS
2026-08-27) — 8 real ambient iPhone clips with **zero hallucinated
segments** and a fluent accented-English walkthrough; diarization live
via pyannote 4.x. The extract store's ingest-once-query-forever pattern
(93.1% measured saving) applies unchanged to web-fetched media.

## What already exists in-tree (verified by read)

- **Fetch + cache**: `assets/http.py` — stdlib fetch, hashed
  `CatalogCache`; five live-tested asset backends prove the pattern.
- **The answer contract**: `kb_read` — token-budgeted, section-
  addressed, citation and flags travel with every answer (96.6%
  measured saving). `web_lookup` is this contract pointed at a URL.
- **Vision client**: `kernel/local_vlm.py` — stdlib-only OpenAI-style
  client, `available()` probe, env-configurable endpoint/model,
  structured "start the local stack" hint when absent.
- **Audio**: extract lane with faster-whisper + pyannote, facts store,
  `ex_search`. **Provenance**: the `ai_generated`/sources-block
  stamping machinery.
- **Infra seam**: the owner's launcher (mlx_lm.server :8080 / oMLX
  :8090 / small sidecar :8082 / LiteLLM shim :4000 with VL lazy-start)
  — personal infrastructure, but TEE already talks to it through ONE
  generic contract: any OpenAI-compatible endpoint.

## Viability verdict, per arm

- **Text: viable now.** Static and documentation-class pages (the
  dominant lookup need) fetch and extract cleanly with stdlib alone at
  90–96% savings vs even clean text. Known limits, to be refused
  loudly with the fix named (rule 6): JS-only SPAs (a headless-browser
  dep is a Playwright-class ~300 MB addition — out of MVP), paywalls,
  robots.txt disallows.
- **Vision: viable where a local VLM endpoint answers**, and it
  measurably beats inline images (41 vs 691 tok). Degradation contract
  when no endpoint: fall back to budgeted inline via the existing
  `tee_media`, or the one-line structured refusal `local_vlm` already
  ships. Never silently skip.
- **Sound: viable now** for direct media files, size-capped and
  cost-gated like `sim_fluid` (confirm before big downloads).
  **Anti-goal**: ripping from streaming platforms (YouTube etc.) —
  ToS-violating; direct files and owner-provided media only.
- **Search (finding URLs, not reading them): not viable in-tree** —
  needs a backend (local SearXNG, or a keyed API à la the dormant
  Tripo/Meshy pattern with cost confirmation). Owner decision. The MVP
  is URL-in → answer-out, routed **KB-first**: `kb_search` answers
  before the web is touched (the paving question needed no web at all).

## The custom-AI-infrastructure angle (this is the A32 story)

Every web token processed locally costs the client ~0; the client pays
only question + answer (~50–100 tok per lookup, measured above). Two
distinct value cases:

1. **Clients with no web access** (many MCP hosts): `web_lookup` is a
   new capability, not a duplicate — and it arrives pre-disciplined.
2. **Clients with web access** (Claude): the value is the budget, the
   citation, the cache, and the vision/sound arms their fetch lacks.

Packaging honestly: the owner's stack is personal. The product shape is
"TEE speaks to any OpenAI-compatible local endpoint" (exactly
`local_vlm.py`'s contract today — env-configured URL + model), with
bring-your-own-model docs; Whisper ships as a normal dependency (models
auto-fetch, <3 GB, under the download-confirmation threshold). TEE
should **not** ship or manage model servers itself in the MVP.

## Risks that gate a build

- **Prompt injection**: fetched content is untrusted data. The tool
  description must say so; extracts are returned as quoted material
  with provenance, and nothing in TEE may treat page text as
  instructions. This is a hard contract, tested with a hostile-page
  fixture before ship.
- **SSRF**: server-side fetch of model-supplied URLs must refuse
  non-http(s) schemes, private/link-local/loopback ranges, and
  redirects into them — with the one-line fix, like every TEE error.
- **Copyright/licensing**: short cited extracts only; no full-page
  copies stored by default; transcripts stored as facts with source
  URL (same posture as extract's site media). Add to the SI-4
  commercial review. Extractor upgrade path (readability-lxml,
  trafilatura) goes through the license lint before adoption — the
  stdlib parser already measured 90–96% and is license-trivial.
- **Etiquette**: robots.txt respected, rate-limited, honest UA, cache
  by URL-hash + ETag so repeat lookups cost zero fetches.

## Recommended MVP, if directed (would be decision A34)

One tool + one reuse: `web_lookup {url, question, max_tokens=500,
media=auto|off}` → SSRF-guarded cached fetch → budgeted cited extract;
images only when the question needs them and an endpoint answers
(top-N captioned server-side); audio/video files size-gated through
the extract lane. Rare pixel needs reuse `tee_media`. Always-loaded
cost: one schema, ~60–120 tok at SI-1 discipline. First deliverable
after the tool: a research-48-style benchmark scenario ("answer five
documentation questions"), naive vs TEE, before any tuning.

## Verdict

**Viable.** Text is viable today on stdlib alone at 99%+ savings vs
raw pages; vision and sound are viable and measured wherever the local
endpoint runs, with honest structured degradation elsewhere; URL
*search* and JS-heavy rendering are the two named gaps, both
owner-decision-gated. The strongest framing is A32's: TEE hands any AI
client budgeted, cited, multimodal web reading at ~100 client-tokens
per lookup, powered by the user's own hardware. Build awaits the
owner's word.
