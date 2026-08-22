# Claude Vision Mechanics & Structured Extraction

*Deep-research digest, 2026-08-22. Part of the TEE research corpus — see [00-index.md](00-index.md). Grounds Phase 7 (TEE Extract).*

## Summary

Claude vision is now patch-based: an image costs `ceil(w/28) x ceil(h/28)` visual tokens (28x28-px patches), with two resolution tiers — standard models cap at 1568 px long edge / 1568 tokens, while Claude 4.7+ models (Opus 5, Sonnet 5, Fable 5) cap at 2576 px / 4784 tokens — meaning any single image costs at most ~4,784 tokens (~$0.024 on Opus 5).

Images participate fully in prompt caching (`cache_control` on image/document blocks, 0.1x reads), but caching lowers price only, not context-window occupancy, and dies on 5-minute/1-hour TTLs and session restarts — so TEE's extract-once-to-structured-facts design is strictly better than cache-only for repeated agentic turns.

PDFs are processed natively as per-page image + extracted text (1,500–3,000 text tokens/page plus image cost). Pages are rasterized server-side at uncontrollable dimensions, so returned coordinates cannot be mapped back — rasterize pages yourself for grounding work.

Claude officially supports absolute-pixel bounding boxes (with a documented resize/pad algorithm and reference implementation to make coordinates line up), but Anthropic labels spatial output "approximate" and tells you to spot-check. Published benchmarks confirm frontier VLMs get only 0.40–0.55 accuracy on symbol counting in floor plans and 33–38% semantic accuracy on CAD floor-plan QA, while OCR-style text reading reaches ~0.95.

Structured outputs (`output_config.format` json_schema / `messages.parse` + Pydantic) guarantee schema-valid extraction JSON via constrained decoding and work alongside vision inputs; citations are incompatible with structured outputs, and changing the schema invalidates prompt cache.

Legibility math from the official formula shows a whole A1 architectural sheet at the 2576-px cap renders ~78 DPI (2.5 mm dimension text ~7.7 px tall — marginal), which quantitatively justifies TEE's tile/crop-then-extract pipeline over whole-sheet passes.

## Findings

### Image token formula (exact)

Claude views images in 28x28-pixel patches ("visual tokens"). Cost = `ceil(width/28) x ceil(height/28)`. Examples from the docs: 200x200 = 64 tokens; 1000x1000 = 1296; 1092x1092 = 1521; 1920x1080 = 2691 (high-res tier, not resized). The old `(w*h)/750` approximation is obsolete. Every image is padded up to the next multiple of 28 on the bottom/right edges; padding is perceived but content never occupies it — normalize by resized dims, not padded dims.

Source: [vision.md (Resolution and token cost)](https://platform.claude.com/docs/en/build-with-claude/vision.md) ; [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### Resolution tiers and auto-resize limits

Standard tier (models before Claude 4.7): max long edge 1568 px AND max 1568 visual tokens. High-resolution tier (Claude 4.7 and later, incl. Opus 5, Sonnet 5, Fable 5): max long edge 2576 px AND max 4784 visual tokens; automatic, no beta header. Oversized images are downscaled to the largest aspect-preserving size satisfying BOTH limits (the token limit usually binds; the edge limit binds only for elongated images like panoramas or tall screenshots).

Example: an A4 scan at 1075x1520 px is under 1568 px on both sides but costs 39x55 = 2145 tokens, so a standard-tier model silently resizes it to 924x1307 — the most common cause of misaligned coordinates. 3840x2160 (4K) → 2576x1449 = 4784 tokens on the high-res tier, 1456x819 = 1560 tokens on the standard tier. High-res can cost ~3x more tokens for the same image.

Source: [vision.md](https://platform.claude.com/docs/en/build-with-claude/vision.md) ; [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### Reference resize implementation (Python, load-bearing for TEE)

Official Python: `count_image_tokens(w, h) = math.ceil(w/28) * math.ceil(h/28)`; `resized_size()` binary-searches the long edge for the largest aspect-preserving size where `ceil(side/28)*28 <= max_edge` for both sides and token count <= `max_tokens` (defaults 1568/1568; pass 2576/4784 for the high-res tier). The short edge rounds half-to-even (banker's rounding) to match the live API. `resized_size(1075, 1520) == (924, 1307)`. Pre-resize with this exact function so returned coordinates map 1:1 to the image you sent; don't pad yourself.

Source: [vision-coordinates.md (Resize your image before uploading)](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### Hard image limits per request

Max dimensions: 8000x8000 px per image. Max images: 600 per API request on 1M-context models, 100 on 200k-context models, 20 per message on claude.ai. If a request has more than 20 image blocks (counting resent history and `tool_result` screenshots), a stricter per-image limit applies — keep every image <= 2000 px per side or <= 20 images, else `invalid_request_error` referencing "many-image requests". Max size per image: 10 MB base64 on the Claude API (5 MB on Bedrock/Google Cloud). Whole-request cap 32 MB — often hit before the 600-image count. Formats: JPEG/PNG/GIF/WebP; animations use the first frame only. Claude reads no image metadata (EXIF/geo is stripped — TEE must extract EXIF locally).

Source: [vision.md (Request limits, FAQ)](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Files API for images/PDFs

Upload once via `client.files.upload` (skill-cached docs say beta header `files-api-2025-04-14` on both upload and `messages.create`; the current vision doc examples show non-beta `client.files.upload`), reference as `{type:'file', file_id}`. Limits: 500 MB per file, 100 GB per organization. Only code-execution/skill-generated files are downloadable, not user uploads. Key benefit for agentic loops: history resends by `file_id` keep request payloads small (base64 re-sends full image bytes every turn — bandwidth/latency, though token billing is identical). Not available on Bedrock/Google Cloud (base64 only there).

Source: [Files API docs](https://platform.claude.com/docs/en/build-with-claude/files) ; claude-api skill `python/claude-api/files-api.md` (cached 2026-06) ; [vision.md (Files API image example)](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Images and prompt caching

Images DO participate in prompt caching: `cache_control {type:'ephemeral'}` goes on any content block, including image and document blocks. Economics: reads ~0.1x base input price; writes 1.25x (5-min TTL) or 2x (1-h TTL). Minimum cacheable prefix: 512 tokens (Opus 5/Fable 5), 1024 (Opus 4.8/Sonnet 5/Sonnet 4.6), 4096 (Opus 4.6/Haiku 4.5) — a single capped image (4784 tokens) exceeds all minimums. Invalidation tiers: changing images invalidates only the messages cache; tools and system caches survive. Critical caveat for TEE: caching reduces PRICE only — cached image tokens still occupy the context window at full token count every turn, and cache does not persist across sessions or TTL gaps (>5-min idle re-pays the 1.25x write).

Source: claude-api skill `shared/prompt-caching.md` (cached 2026-06) ; [prompt-caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

### PDF-native processing mechanics

When you send a PDF (document block: url, base64, or `file_id`), the system (1) converts each page into an image AND (2) extracts each page's text, providing both to Claude. Token cost = text tokens (typically 1,500–3,000 per page depending on density) + per-page image cost under the normal vision formula; no extra PDF fee. Limits: 32 MB request, 600 pages (100 when the request context window is <1M tokens), standard unencrypted PDFs, all active models. Bedrock Converse legacy datapoint: text-extraction-only mode ~1,000 tokens per 3-page PDF vs full visual mode ~7,000 tokens per 3-page PDF (~2,300/page). Best practices from the docs: place PDFs before text, upright orientation, standard fonts, split large PDFs, enable prompt caching for repeated analysis (`cache_control` on the document block is shown verbatim in the docs).

Source: [pdf-support.md](https://platform.claude.com/docs/en/build-with-claude/pdf-support.md)

### PDF coordinates are unusable — rasterize yourself

Verbatim: "For PDF support, pages are rasterized to images server-side at dimensions you don't control, so the returned coordinates can't be reliably mapped back onto the page. To work with coordinates on PDF content, rasterize the pages to images yourself and use the pre-resize approach." The document block also does not accept the `transformations`/`oversized_image` field. For TEE dimension-grounding on architectural PDF sheets: always rasterize locally (`pypdfium2`/`pdf2image`) at controlled DPI, pre-resize with the reference implementation, and send as image blocks — never as a PDF document block when box coordinates matter.

Source: [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### When to send PDF vs pre-extracted content

The docs' native PDF path double-bills every page (image + embedded text, ~1.5–3.5k+ tokens/page total) and is justified when charts/layout matter. For text-dominant docs, pre-extracted text alone is several times cheaper (Bedrock legacy numbers: ~333 vs ~2,333 tokens/page). Citations support: enable `citations:{enabled:true}` per document block; PDF citations return `page_location` (`start_page_number`/`end_page_number`, 1-indexed) — useful for provenance in extraction pipelines — but citations are incompatible with `output_config.format` structured outputs (returns 400), so a pipeline must choose per-call: cited prose extraction OR schema-constrained JSON, not both.

Source: [pdf-support.md](https://platform.claude.com/docs/en/build-with-claude/pdf-support.md) ; claude-api skill Document & File Input quick reference

### Bounding boxes / pixel coordinates from Claude (official support + caveats)

Anthropic now documents coordinate workflows: Claude returns absolute pixel coordinates in the coordinate space of the image it sees AFTER server-side resizing; origin top-left. Verbatim guidance: "Claude works best with absolute pixel coordinates. Ask for them explicitly... Claude does not work well when you ask for normalized coordinates, for example: Return bounding box coordinates between 0 and 1000." Recommended prompt: "Return the bounding box of each table as [x1, y1, x2, y2] (top-left and bottom-right corners) in pixel coordinates", ideally via a structured-outputs schema with an `[x1,y1,x2,y2]` array per element.

Accuracy is officially "approximate" — spot-check visually before scale processing. Small elements lose precision when downscaled: crop the region of interest and send the crop (offset coordinates by the crop origin), or use a high-res-tier model. Set `transformations:{oversized_image:'error'}` on image blocks to turn silent server resizing into a 400 error naming the exact target dimensions (also honored by `count_tokens` for embedded images).

Source: [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### Vision reliability limitations (official)

The docs list: hallucinations/mistakes on low-quality, rotated, or very small images under 200 px; counting is approximate, "especially with large numbers of small objects"; spatial reasoning outputs are approximate. Image quality guidance: make in-image text legible and not too small; don't crop out key visual context solely to enlarge text; account for server resizing making text less legible — "Consider pre-resizing your images, cropping them, or both"; lossy compression artifacts (multi-pass JPEG) measurably hurt performance — inspect the actual bytes sent.

Source: [vision.md (Limitations, Image quality guidance)](https://platform.claude.com/docs/en/build-with-claude/vision.md)

### Legibility math for architectural sheets (derived from the official formula)

An A1 sheet (841x594 mm) capped at 2576 px long edge = ~3.06 px/mm (~78 DPI): 2.5 mm dimension text renders ~7.7 px tall — marginal; on the 1568 px standard tier it is ~4.7 px — illegible. Whole-sheet passes therefore cannot reliably read dimension strings; tiles/crops at native scan resolution are required. Optimal tile: any tile <= 4784 visual tokens on the high-res tier (e.g., 1932x1932 max square = 69x69 patches; 2576x1288 for 2:1 strips) sent at 1:1 scan pixels. A 300-DPI A1 scan is 9933x7016 px → roughly 5x4 = 20 tiles at ~1988x1756, conveniently exactly the 20-image threshold before the stricter 2000-px per-image rule kicks in — tile grids should stay <= 20 tiles per request AND <= 2000 px per side to be safe.

Source: Derived from formulas/limits in [vision.md](https://platform.claude.com/docs/en/build-with-claude/vision.md) and [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md)

### Structured outputs for schema-driven extraction

`output_config:{format:{type:'json_schema', schema:...}}` uses constrained decoding (a compiled grammar) — 100% schema-compliant output, no `JSON.parse` retries. Python: `client.messages.parse(model=..., output_format=PydanticModel)` → `response.parsed_output` typed. Supported on Opus 5/4.8/4.7/4.6/4.5, Sonnet 5/4.6/4.5, Haiku 4.5, Fable/Mythos; works with vision inputs (no documented restriction). Schema subset: no recursive schemas, no external `$ref`, NO numeric `minimum`/`maximum`/`multipleOf`, no `minLength`/`maxLength` (the SDK moves such constraints into description text and validates locally). `strict:true` on tool definitions gives the same guarantee for tool-based extraction. Costs/caching: the first request pays grammar-compilation latency, the grammar is cached 24 h; changing `output_config.format` invalidates the prompt cache for the thread (keep one frozen extraction schema per TEE media type). Note the deprecated parameter name `output_format` at top level — the current API is `output_config.format`.

Source: [structured-outputs.md](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md) ; claude-api skill (Architecture, Common Pitfalls)

### Multi-pass verification patterns (evidence-based)

No official Anthropic "extract-then-verify" recipe exists, but the primitives are documented:

1. Constrained decoding guarantees syntax, not factual accuracy — cross-check numeric dimension strings against locally-run OCR or PDF vector text. (The PDF text layer is exactly what Claude's own PDF pipeline pairs with page images, so replicating that pairing locally — image tile + `pdfplumber`/OCR text of the same region in one prompt — mirrors the native mechanism.)
2. Citations with `page_location` give verifiable provenance for text claims (but exclude structured outputs in the same call — do a cite pass and a schema pass separately).
3. Crop-and-re-ask on regions of interest is the officially recommended remedy for small-element precision.
4. `count_tokens` is free (2,000–8,000 RPM by tier, separate rate-limit pool) for pre-flight cost checks and honors `oversized_image:'error'`.

The benchmarks below show symbol counting is the weak task — verify counts (doors/windows) with deterministic CV or human-in-the-loop, not a second LLM pass.

Source: [vision-coordinates.md](https://platform.claude.com/docs/en/build-with-claude/vision-coordinates.md) ; [pdf-support.md](https://platform.claude.com/docs/en/build-with-claude/pdf-support.md) ; [token-counting.md](https://platform.claude.com/docs/en/build-with-claude/token-counting.md) ; [structured-outputs.md](https://platform.claude.com/docs/en/build-with-claude/structured-outputs.md) ; [AECV-Bench arXiv:2601.04819](https://arxiv.org/abs/2601.04819)

### Published accuracy on architectural/engineering drawings

- AECV-Bench ([arXiv:2601.04819](https://arxiv.org/abs/2601.04819)): 120 floor plans (counting doors/windows/bedrooms/toilets) + 192 drawing-grounded QA pairs. State-of-the-art multimodal models reach up to 0.95 accuracy on text-centric/OCR tasks but only 0.40–0.55 on symbol-centric understanding (door/window counting "remains unsolved", substantial proportional errors); the paper recommends domain-specific representations and tool-augmented human-in-the-loop workflows.
- ArchPlanVQA (J. Computing in Civil Engineering, 2026, doi:10.1061/JCCEE5.CPENG-7571): general-purpose VLMs achieve only 33.03–37.88% semantic understanding accuracy on architectural floor-plan CAD drawings.
- GD&T extraction ([arXiv:2411.03707](https://arxiv.org/abs/2411.03707)): fine-tuned Florence-2 (open, ~0.23–0.77B params) on just 400 annotated drawings beat the best closed-source zero-shot model by +29.95% precision, +37.75% recall, +52.40% F1, with 43.15% lower hallucination — i.e., zero-shot frontier VLMs hallucinate heavily on dimension/tolerance callouts, supporting local specialized pre-extraction.
- Also relevant: the Enginuity benchmark ([arXiv:2606.03410](https://arxiv.org/abs/2606.03410)) and ParaCAD/PHT-CAD ([arXiv:2503.18147](https://arxiv.org/pdf/2503.18147)) with a dimension-based evaluation metric linking geometry and annotation layers.

Source: [arXiv:2601.04819](https://arxiv.org/abs/2601.04819) ; [doi:10.1061/JCCEE5.CPENG-7571](https://doi.org/10.1061/JCCEE5.CPENG-7571) ; [arXiv:2411.03707](https://arxiv.org/abs/2411.03707) ; [arXiv:2606.03410](https://arxiv.org/abs/2606.03410) ; [arXiv:2503.18147](https://arxiv.org/pdf/2503.18147)

### Set-of-Mark / mark-based prompting (published eval)

Set-of-Mark (SoM) prompting, Microsoft, arXiv:2310.11441 (code at github.com/microsoft/SoM): overlay images with alphanumeric marks/boxes/masks from off-the-shelf segmenters (SAM/SEEM); GPT-4V+SoM zero-shot outperformed fully fine-tuned SOTA referring-segmentation models on RefCOCOg. The paper also evaluates simpler partitioning: 3x3 grid cells with numeric marks at region centers (grid/SLIC/watershed variants) — the direct academic ancestor of "numbered grid cell" contact-sheet prompting. Follow-on: "GPT-4V is a Generalist Web Agent, if Grounded" (arXiv:2401.01614) confirms grounding via marks beats raw-coordinate output for GPT-class models. Note the tension with Anthropic guidance: Claude is explicitly documented to work best with direct absolute-pixel coordinates, so for Claude, marks are a complement (disambiguation, cell addressing) rather than a coordinate workaround.

Source: [arXiv:2310.11441](https://arxiv.org/abs/2310.11441) ; [github.com/microsoft/SoM](https://github.com/microsoft/SoM) ; [arXiv:2401.01614](https://arxiv.org/pdf/2401.01614) ; [som-gpt4v.github.io](https://som-gpt4v.github.io/)

### Contact-sheet prompting practice (community, no formal eval)

claude-real-video / crv (MIT, github.com/HUANGCHIHHUNGLeo/claude-real-video): scene-aware dedup keeps only frames that differ (e.g., 26 frames from a 58 s clip) and packs 9 consecutive keyframes per contact-sheet grid with per-cell timestamps, plus a text manifest the model references — pattern: grid image + manifest mapping cell → timestamp, ask the model to cite cells. Rationale published: "an LLM can afford about 150 images per video... which 150 you pick decides whether the model watched the video or just a slideshow." `vcsi` (PyPI, permissive) generates timestamped contact sheets locally. No peer-reviewed eval of contact sheets specifically was found — SoM (above) is the closest published evidence that cell/mark addressing improves grounding. Token math for sheets: the max square image on the high-res tier is 1932x1932 (4761 tokens), so a 3x3 sheet gives 644 px cells (scene gist only, never small text); per-frame cost ~529 tokens vs ~1296+ for individual 1000x1000 frames — roughly 2.4x cheaper per frame, plus fewer blocks toward the 20-image threshold.

Source: [claude-real-video](https://github.com/HUANGCHIHHUNGLeo/claude-real-video) ; [dev.to write-up](https://dev.to/renolu/claude-real-video-feeding-an-llm-the-frames-that-actually-matter-ge) ; [How LLMs watch video](https://leoaido.com/how-llms-watch-video/) ; [PyPI vcsi 7.0.14](https://pypi.org/project/vcsi/7.0.14/)

### Worked cost example: re-billing raw images vs TEE extract-once (Opus 5, $5/MTok input, $25/MTok output, high-res tier)

Assets for the house task: drawing sheet at cap 4,784 tok + satellite image at cap 4,784 tok + site photo 1920x1080 = 2,691 tok → 12,259 image tokens.

- (A) Naive 40-turn agentic Blender session resending images uncached: 40 x 12,259 = 490,360 tok = $2.45 image-only.
- (B) Same with prompt caching (5-min TTL, images in a stable prefix): write 12,259 x 1.25 + 39 reads x 12,259 x 0.1 = 63,134 token-equivalents = $0.32 — but it re-pays the 1.25x write after any >5-min gap and every new session, and the 12,259 tokens still occupy context every turn.
- (C) TEE extract-once: one extraction call ~12,259 in + ~3,000 structured-JSON out = $0.061 + $0.075 = ~$0.14 one-time; thereafter ~1,500 tokens of facts per turn: 40 x 1,500 = 60,000 tok = $0.30 uncached, or ~$0.04 cached (1,500 x 1.25 + 39 x 150 = 7,725 tok-equiv).

Across M sessions: raw-cached costs ~M x $0.32; TEE costs $0.14 + M x $0.04 — break-even inside the first session, ~8x cheaper per subsequent session, plus an 8x smaller context footprint (1.5K vs 12.3K tokens/turn). Per-image ceiling costs: any image <= $0.0239 on Opus 5 (4,784 x $5/M), <= $0.0143 on Sonnet 5, <= $0.0016 on Haiku 4.5 (standard tier, 1,568 cap). The docs' own examples: 1000x1000 ≈ $6.48/1000 images on Opus 5; 4K ≈ $23.92/1000.

Source: Computed from the [vision.md token table](https://platform.claude.com/docs/en/build-with-claude/vision.md), `shared/prompt-caching.md` economics (0.1x read / 1.25x write), and the claude-api skill pricing table (cached 2026-06-24)

### Token counting endpoint (free pre-flight)

`POST /v1/messages/count_tokens`: free to use, separate RPM pool from messages (Start 2,000 / Build 4,000 / Scale 8,000 RPM). Accepts images and PDFs; returns an estimate ("actual number... might differ by a small amount"); estimates image cost from dimensions without full processing, so a successful count does not guarantee the request passes Messages request limits. Rejects embedded images marked `oversized_image:'error'` exactly as Messages would. Tokenizer warning: Claude 4.7+ and Fable 5 tokenize ~30% more text tokens than earlier models — count against the exact model you will bill.

Source: [token-counting.md](https://platform.claude.com/docs/en/build-with-claude/token-counting.md)

### Image ordering and multi-image prompting (official)

Claude works best when images come BEFORE text (mirrors long-document-first prompting). For multiple images, label each with a short text block ("Image 1:", "Image 2:") so prompts and follow-up turns can reference them by name — the official, documented version of the "reference by id" pattern. In multi-turn conversations Claude retains access to all earlier images without resending them in the new turn's content (though the API client still resends them in history unless using `file_id` references).

Source: [vision.md (Tips, Multiple images)](https://platform.claude.com/docs/en/build-with-claude/vision.md)

## Recommendations for TEE

1. Build TEE Extract's tiler around the official `resized_size()` reference implementation (28-px patches, binary search, round-half-even): pre-resize every image locally so it is never server-resized, target <= 4784 tokens/tile for high-res-tier models, keep every tile <= 2000 px per side and <= 20 image blocks per request, and set `transformations:{oversized_image:'error'}` on every coordinate-bearing image so silent resizing becomes a hard failure.
2. Never send architectural PDFs as native document blocks when dimensions/coordinates matter: rasterize locally (controlled DPI), pair each tile with locally-extracted vector text (`pdfplumber`/OCR) in the same prompt — this replicates Claude's own image+text PDF mechanism while keeping coordinates mappable and avoiding the 1,500–3,000 text-token-per-page double-billing on every future turn.
3. Use one frozen Pydantic schema per media type with `client.messages.parse()` / `output_config.format` for extraction (guaranteed-valid JSON; no numeric min/max in the schema — validate ranges locally), and run provenance/citation passes as separate calls since citations and structured outputs are mutually exclusive per request.
4. Ask Claude for absolute pixel coordinates (`[x1,y1,x2,y2]`) on pre-resized images — never normalized 0–1000 coordinates; treat all returned boxes as approximate: verify dimension strings against local OCR/vector text, verify counts (doors/windows — benchmarked at only 0.40–0.55 accuracy) with deterministic CV or human review, and crop-and-re-ask for fine targets.
5. Position TEE Extract's cost story precisely: prompt caching cuts image re-billing to ~0.1x but not context occupancy and not across sessions/TTL gaps; extract-once to ~1.5K tokens of facts beats even perfectly-cached raw images (~8x cheaper per subsequent session in the worked example) — cite the worked math (12,259 image tokens/turn → $2.45 naive / $0.32 cached / $0.14 + $0.04–0.30 TEE per 40-turn session).
6. Adopt labeled-image prompting ("Image 1:", "Image 2:") and, for video/photo surveys, timestamped contact sheets (max useful square 1932x1932 = 4761 tokens, 9 cells of 644 px) with a cell → source manifest; borrow Set-of-Mark-style numbered marks for region addressing, but rely on pixel coordinates (not marks) for measurement grounding per Anthropic's guidance.
7. Use the free `count_tokens` endpoint in TEE's preprocessing to price every extraction batch before sending, counting against the exact target model (Claude 4.7+/Fable tokenizer inflates text ~30%), and prefer Files API `file_id` references in any multi-turn flow to keep request payloads small.
