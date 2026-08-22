# 47 — AI-first generation product: prior art + interface design (2026-08-22)

Every prior-art claim verified against the named repo/docs on 2026-08-22.

## Prior art: how existing tools expose 3D generation to agents

**Meshy — official MCP server** (`meshy-dev/meshy-mcp-server`, npm `@meshy-ai/meshy-mcp-server`; https://github.com/meshy-dev/meshy-mcp-server, https://docs.meshy.ai/en/api/ai)

- 24 always-loaded tools: `meshy_text_to_3d`, `meshy_image_to_3d`, `meshy_multi_image_to_3d`, `meshy_remesh`, `meshy_retexture`, `meshy_rig`, `meshy_animate`, `meshy_convert`, `meshy_get_task_status`, `meshy_list_tasks`, `meshy_cancel_task`, `meshy_download_model`, `meshy_check_balance`, plus 3D-printing and image tools — a wide flat surface, every schema paid for on every turn.
- Async lifecycle per Meshy quickstart (https://docs.meshy.ai/en/api/quick-start): create returns task id; "Poll the same endpoint until `status` is `SUCCEEDED`"; sample code polls every 5 s. Completed payload: `status`, `progress`, `model_urls` (`glb`, `fbx`), `thumbnail_url`, `task_error.message`. SSE/webhooks exist at REST level but the MCP surface is get-status polling.
- Token waste: model-driven status calls (each a full request+response turn); per-model credit pricing (5–35 credits image-to-3D) exposed only via a separate `meshy_check_balance` call, not as an upfront estimate on submit.
- Copy: stable task ids; compact status enum; `task_error.message` as single error field; llms.txt for non-MCP agents. Avoid: 24-tool surface, agent-driven poll cadence.
- A community variant (pasie15/meshy-ai-mcp-server, https://github.com/pasie15/meshy-ai-mcp-server) is worse: 50+ tools (create/retrieve/list/stream/delete per task type). Another community server advertises a server-side `wait_for_task(task_type)` that "returns download URLs when done" (lobehub listing of gwizards-meshy-mcp-server — direct page 403, detail UNVERIFIED) — the one pattern worth copying.

**Tripo — official MCP** (`VAST-AI-Research/tripo-mcp`, alpha; https://github.com/VAST-AI-Research/tripo-mcp, src/server.py)

- 16 tools (bundles Blender scene tools + Tripo generation): `create_3d_model_from_text`, `create_3d_model_from_image`, `get_task_status`, `import_tripo_glb_model`, plus scene/PolyHaven tools.
- The docstring is the smoking gun, verbatim: "IMPORTANT: This tool initiates a 3D model generation task but does NOT wait for completion. After calling this tool, you MUST repeatedly call the get_task_status tool" — the polling burden placed entirely on the model, per docstring instruction. Each poll is a paid tool-call turn; a 2-minute generation at ~5 s cadence ≈ 20+ wasted turns.
- Result payload on SUCCESS: `pbr_model_url`, `base_model_url`, `model_url`, `rendered_image_url` — URLs only; zero mesh statistics, so the agent must import + inspect (more calls) to learn anything about what it got.

**blender-mcp Hyper3D/Hunyuan lanes** (`ahujasid/blender-mcp` src/blender_mcp/server.py; https://github.com/ahujasid/blender-mcp)

- 25 tools; generation lanes are `generate_hyper3d_model_via_text/_images` → `poll_rodin_job_status` → `import_generated_asset`, and `generate_hunyuan3d_model` → `poll_hunyuan_job_status` → `import_generated_asset_hunyuan`.
- Poll docstrings verbatim: "This is a polling API, so only proceed if the status are finally determined" (Rodin); Hunyuan "done if status is 'DONE' … in progress if 'RUN'". Model-driven loops again, doubled per provider (two parallel tool triplets for the same job shape).
- `get_scene_info` returns the full scene JSON via `json.dumps(result, indent=2)` — a full dump, pretty-printed (the indentation itself is token spend); `get_viewport_screenshot` (PNG, `max_size` default 1000 px) is the evidence channel. Violates TEE rules 1 and 4 simultaneously. Copy: the import-by-job-id step decoupled from generation. Avoid: everything about the polling and state reporting.

**ComfyUI TRELLIS/TRELLIS.2 nodes** — human-first graph UIs, not agent surfaces

- `PozzettiAndrea/ComfyUI-TRELLIS2` (https://github.com/pozzettiandrea/ComfyUI-TRELLIS2): node graph image→mesh with rmbg/T-pose preprocessing; install requires experimental `comfy-env` + pixi package manager — evidence that TRELLIS.2's CUDA-extension stack does not pip-install cleanly. Also `visualbruno/ComfyUI-Trellis2`, `if-ai/ComfyUI-IF_Trellis` (8 GB-VRAM-optimized TRELLIS 1), `smthemex/ComfyUI_TRELLIS`.
- For an agent, a ComfyUI graph means submitting an entire workflow JSON (hundreds of node/link tokens) to change one parameter; state comes back as images. Nothing to copy for the interface; the VRAM-optimization lineage is useful.

**TRELLIS/TRELLIS.2 wrappers in the wild**

- Upstream `microsoft/TRELLIS.2` (https://github.com/microsoft/TRELLIS.2): MIT; 4B params; weights `microsoft/TRELLIS.2-4B` on HF; 512³–1536³; min 24 GB VRAM, NVIDIA-only, Linux-only tested, CUDA 12.4; pure Python pipeline (`Trellis2ImageTo3DPipeline.from_pretrained('microsoft/TRELLIS.2-4B')` → `pipeline.run(image)`) + Gradio demos; **no CLI, no REST API, no MPS support** — the interface vacuum this product fills.
- `vaibhavpandeyvpz/trellis-image-to-3d` (https://github.com/vaibhavpandeyvpz/trellis-image-to-3d): Gradio on HF Spaces (ZeroGPU T4), synchronous 2–5 min wait, GLB + Gaussian .ply, TRELLIS 1. Human-first; nothing machine-readable comes back.
- `IgorAherne/TRELLIS.2-stableprojectorz` (https://github.com/IgorAherne/TRELLIS.2-stableprojectorz): fork consumed by the StableProjectorz Unity app; local server started via `app.py`; fp16/int32 slimming to fit 8 GB GPUs even at 1024³; one-click Windows installer (Python 3.11, CUDA 12.8, Torch 2.8). Proof that (a) a local-server packaging of TRELLIS.2 for a non-human client works, (b) big VRAM cuts vs upstream's 24 GB are achievable. Its API surface is undocumented (UNVERIFIED beyond `app.py`).
- **fal.ai `fal-ai/trellis-2`** (https://fal.ai/models/fal-ai/trellis-2/api) — the closest existing thing to a right-shaped machine interface: input `{image_url, seed, resolution: 512|1024|1536, texture_size: 1024|2048|4096, decimation_target (default 500000 vertices), remesh: bool, ...}`; queue endpoints `submit` (returns `request_id`) / `status` / `result`, webhooks offered; output `{model_glb: {url}}`; pricing $0.25/$0.30/$0.35 by resolution (fal search page). Copy: seed + decimation budget as first-class inputs, submit/status/result separation, priced-by-resolution upfront. Missing: mesh stats, validation verdict, provenance. Replicate `firtoz/trellis` (https://replicate.com/firtoz/trellis) is TRELLIS 1, similar shape.

## Requirements: what "optimized for AI" means, each grounded

1. **Single bounded wait, server-side polling.** `generate()` returns `job_id` immediately; one `await_result(job_id, timeout_s)` call blocks server-side and returns the final report (or a resumable timeout checkpoint). Grounds: Tripo's "you MUST repeatedly call get_task_status", blender-mcp's twin poll tools, TEE "batch over chatter". fal's submit/status/result proves the queue shape; we collapse status into the wait.
2. **Compact machine report, never renders.** Completion returns JSON: `{asset_id, files:{glb}, stats:{tris, verts, watertight, bbox_m, materials:[basecolor,normal,rough,metal], uv_coverage}, repairs:[...], verdict:{accepted, violations:[{rule, got, limit, fix}]}, provenance:{...}, timings, peak_mem}`. Grounds: Tripo/Meshy return bare URLs + thumbnails (pixels); TEE rules 1 & 4; blender-mcp's screenshot habit.
3. **Caller-supplied budget → accept/reject with exact fix in one message.** Request carries `budget:{max_tris, require_watertight, target_size_m, max_texture}`; reject reads like `"tris 812k > budget 100k; retry with decimation_target=100000"`. Grounds: TEE "fail loud and cheap"; fal's `decimation_target` shows budgets are pipeline-native; no prior tool validates against caller intent.
4. **Deterministic seeds + full provenance manifest.** `{generator, generator_version, upstream_commit, model_repo, model_revision (full commit hash), input_image_sha256, seed, params, "ai_generated": true}` written beside every asset — TEE's provenance flag requirement; HF `revision=` pinning makes model identity verifiable (full-length hash required per HF docs).
5. **Input-hash cache: same request never generates twice.** Key = sha256(image) + params + model revision → return prior report instantly. No surveyed tool does this; hosted APIs bill you again instead (Meshy credits, fal per-request).
6. **Cost/time/feasibility estimate on submit.** Echo `{est_seconds, est_peak_mem_gb, queue_position}` in the submit ack — local analogue of fal's per-resolution pricing and Meshy's credit table, which agents otherwise discover post-hoc.
7. **Degraded-mode honesty.** No CUDA/MPS or insufficient RAM → immediate structured refusal `{error:"no_backend", fix:"requires Apple Silicon ≥X GB or NVIDIA ≥Y GB; hosted fallback: tripo/meshy"}` — never a hang or a stack trace. Grounds: upstream is NVIDIA/Linux/24 GB-only; ComfyUI wrappers fail at env level; TEE rule 6.
8. **Tiny tool surface, progressive disclosure.** ≤4 MCP tools vs Meshy's 24 / pasie15's 50+ / blender-mcp's 25. Long tail (format conversion, retexture-only, param exotica) goes through the params dict + docs, per TEE rule 5.

## Interface surfaces

- **Python API (4 calls):** `submit(image, params, budget) -> Job{id, est}`; `wait(job_id, timeout_s) -> Report`; `generate(...) -> Report` (submit+wait sugar, the one agents use); `query(asset_id|job_id) -> Report|Manifest` (cache lookup, provenance, re-fetch stats).
- **CLI:** `<name> gen input.png --seed 7 --max-tris 100k --watertight --out ./assets --json` (single blocking command, JSON report on stdout, exit 0/1 = verdict — pipeline- and agent-friendly); `<name> jobs` / `<name> show <asset_id>`; `<name> doctor` (backend/VRAM/weights check, mirrors requirement 7); `<name> fetch-weights [--revision <hash>]`.
- **MCP (≤4 tools):** `gen3d_generate` (image path/b64 + params + budget → report; internally bounded-waits, returns checkpoint token on timeout), `gen3d_wait` (resume a checkpoint), `gen3d_query` (asset/job by id — stats, provenance, cache hits), `gen3d_status` (engine health: backend, VRAM, queue, weights revision). **Stays OUT of MCP:** weight download management, format converters, retexture/rig/animate verbs, per-stage sampler knobs (live in the `params` dict), any screenshot/render tool, cancel/list/delete task CRUD (Meshy's mistake).

## Packaging as a separate product

- **Install:** `uv tool install` / `uvx` for the CLI+server shell (uv docs: https://docs.astral.sh/uv/; uvx runs ephemeral, `uv tool install` puts it on PATH). Caveat verified via ComfyUI-TRELLIS2's pixi/comfy-env escape hatch: the CUDA lane's compiled extensions won't ride a plain wheel — ship pure-Python core + backend extras (`[cuda]`, `[mps]`), compile-on-first-run or prebuilt wheels per backend; the Apple-first lane has the cleaner path.
- **Weights:** fetch on first run via `huggingface_hub.snapshot_download(repo_id="microsoft/TRELLIS.2-4B", revision=<pinned full commit hash>)`; default cache `~/.cache/huggingface/hub` (`HF_HOME`, `HF_HUB_CACHE` override; `HF_HUB_OFFLINE=1` for air-gapped runs; `allow_patterns` to skip unneeded files; `dry_run` for size preflight). Docs: https://huggingface.co/docs/huggingface_hub/guides/download, /package_reference/environment_variables. Do not vendor weights; do record the resolved revision hash into every provenance manifest.
- **Versioning:** product `0.x.y` with each release pinning the upstream TRELLIS.2 commit (submodule or recorded hash), following the verified llama-cpp-python convention of release notes naming the vendored llama.cpp commit (https://github.com/abetlen/llama-cpp-python/releases). Manifest carries both product version and upstream commit.
- **License:** MIT requires only that "The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software" (https://choosealicense.com/licenses/mit/). So: keep Microsoft's copyright + MIT text in the vendored/forked tree; a NOTICE file and change-log are Apache-2.0 ideas, not MIT obligations — optional courtesy. MIT grants no trademark rights: don't ship under a name containing "TRELLIS"; "built on Microsoft TRELLIS.2 (MIT)" in README is fine.
- **Repo shape:** separate repo, not a TEE subpackage — different release cadence (tracks upstream model drops), huge dependency graph (torch/CUDA) that must never infect TEE's lightweight server env, independently useful to non-TEE users; TEE consumes it as an optional dependency behind an adapter. For a solo owner the coordination cost of two repos is one pinned version string in TEE.

## Name candidates (collision-checked 2026-08-22)

- **Voxkiln** — no software hits found; evokes O-Voxel + baking images into solids. Cleanest.
- **Meshkiln** — no hits; adjacent to `codeofaxel/Kiln` (MCP 3D-printing server) and Kiln AI, but distinct compound.
- **Ovoxel** — no product collision found, but derives from Microsoft's "O-Voxel" term (confusion risk with upstream tech; weakest differentiation).
- **Ingot3d / Ingot** — no 3D-software hits for "ingot3d"; bare "Ingot" unchecked (UNVERIFIED).
- Rejected on collision: Meshsmith (Smithsonian dpo-meshsmith + GitHub org), Solidgen (TMLR paper + solidgen.io — an existing TRELLIS.2 image-to-3D service), Shapeforge (GitHub org), VoxForge (speech corpus), Kiln (taken twice).

## Implications for the build

1. One-shot `generate` = submit + server-side bounded wait; model-driven poll loops are banned (the Tripo/blender-mcp anti-pattern is the product's reason to exist).
2. Completion payload is the compact machine report (stats + repairs + verdict + provenance), never a render or bare URL.
3. Caller budget in, accept/reject + exact-fix out, one message (TEE rule 6 as an API contract).
4. Determinism + provenance manifest with pinned model revision (full HF commit hash) and `ai_generated: true` — required by TEE's asset-provenance rules.
5. Input-hash cache before any GPU work; cache hit returns the stored report verbatim.
6. Submit ack carries est_seconds / est_peak_mem / queue position (upfront cost honesty, the local analogue of fal's pricing table).
7. `doctor`/`status` + structured refusal when no capable backend — never hang (Apple-first reality: upstream is CUDA-only today).
8. MCP surface frozen at 4 tools; everything else via params dict, CLI, or Python API (progressive disclosure).
9. Separate repo, uv-tool-installable shell, weights via `snapshot_download` into the HF cache on first run, product 0.x pinned to upstream commit llama-cpp-python-style.
10. MIT compliance = retain Microsoft copyright + license text; name must not contain "TRELLIS"; leading name candidate **Voxkiln** (fallbacks Meshkiln, Ovoxel).
