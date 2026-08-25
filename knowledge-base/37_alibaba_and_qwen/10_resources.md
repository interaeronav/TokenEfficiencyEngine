---
id: alibaba.resources
title: Alibaba and Qwen — tested link register
domain: 37_alibaba_and_qwen
tags: [qwen, alibaba, resources, links, arxiv, huggingface, modelscope, mlx, documentation, leaderboards, investor-relations, quantisation]
jurisdiction: global
status: stable
confidence: high
updated: 2026-08-25
sources:
  - {title: "Qwen organisation on Hugging Face", url: "https://huggingface.co/Qwen", publisher: "Hugging Face", accessed: 2026-08-25}
  - {title: "QwenLM GitHub organisation", url: "https://github.com/QwenLM", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen documentation", url: "https://qwen.readthedocs.io/en/latest/", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "arXiv API metadata query for Qwen technical reports", url: "http://export.arxiv.org/api/query", publisher: "arXiv", accessed: 2026-08-25}
  - {title: "Alibaba Group investor news and filings", url: "https://www.alibabagroup.com/en-US/ir-news-filings", publisher: "Alibaba Group", accessed: 2026-08-25}
related: [alibaba.overview, alibaba.qwen_models, alibaba.qwen_local, alibaba.qwen_finetune, alibaba.qwen_agents]
---

# Alibaba and Qwen — tested link register

**Summary.** Every URL below was requested on **25 August 2026** and returned HTTP 200, or — for `github.com` HTML pages, which this research environment's proxy blocks with a 403 for plain HTTP clients — was verified by fetching `https://raw.githubusercontent.com/<org>/<repo>/<branch>/README.md` and confirming the repository exists. arXiv identifiers were verified against the arXiv API, which returned matching titles and publication dates. Where a link is dynamic (a leaderboard, a search) the retrieved value is quoted with its date.

> ⚠️ Link rot in this domain is fast. Qwen shipped four generations in eighteen months and renames its documentation sites as it goes. Anything dated before 2026 should be re-checked before being relied on.

## Official Qwen — models and code

| Resource | URL | Notes |
|---|---|---|
| Qwen homepage | https://qwen.ai/ | Marketing and blog entry point (JavaScript SPA; blog posts are at `qwen.ai/blog?id=<slug>`) |
| Qwen Studio (chat) | https://chat.qwen.ai/ | Free consumer chat interface |
| QwenCloud (API) | https://www.qwencloud.com | OpenAI- and Anthropic-compatible API |
| QwenWork | https://qwenwork.cn | Enterprise workforce agent platform |
| Qoder | https://qoder.com/ | Agentic coding platform |
| Legacy blog | https://qwenlm.github.io/blog/ | Posts through September 2025; superseded by `qwen.ai/blog` |
| Documentation | https://qwen.readthedocs.io/en/latest/ | Quickstart, inference, deployment, quantisation, training, framework integration |
| GitHub organisation | https://github.com/QwenLM | 50 repositories |
| Discord | https://discord.gg/CV4E9rpNSD | Community |

### GitHub repositories (all verified to exist, 25 Aug 2026)

| Repository | URL | What it is |
|---|---|---|
| Qwen3.8 | https://github.com/QwenLM/Qwen3.8 | **Current main repo** — covers Qwen3.5, 3.6 and 3.8; dated release news; deployment commands |
| Qwen3.5 | https://github.com/QwenLM/Qwen3.5 | Qwen3.5 series |
| Qwen3 | https://github.com/QwenLM/Qwen3 | Qwen3 and Qwen3-2507; news back to Qwen1.5 |
| Qwen2.5 | https://github.com/QwenLM/Qwen2.5 | Qwen2.5 series |
| Qwen2 / Qwen | https://github.com/QwenLM/Qwen2 · https://github.com/QwenLM/Qwen | Historic |
| Qwen3-VL | https://github.com/QwenLM/Qwen3-VL | Vision-language |
| Qwen2.5-VL | https://github.com/QwenLM/Qwen2.5-VL | Vision-language |
| Qwen3-Coder | https://github.com/QwenLM/Qwen3-Coder | Code models |
| Qwen3-Omni | https://github.com/QwenLM/Qwen3-Omni | Omni-modal |
| Qwen3-Embedding | https://github.com/QwenLM/Qwen3-Embedding | Embedding and reranker |
| Qwen-Agent | https://github.com/QwenLM/Qwen-Agent | Agent framework: function calling, MCP, code interpreter, RAG, GUI |
| qwen-code | https://github.com/QwenLM/qwen-code | Terminal coding agent, TypeScript, Apache 2.0, 27,227 stars |
| qwen-code-docs | https://qwenlm.github.io/qwen-code-docs/ | Qwen Code documentation |
| Qwen-MM-Plugins | https://github.com/QwenLM/Qwen-MM-Plugins | "Make any agent harness multimodal-native", 2,741 stars |
| FlashQLA | https://github.com/QwenLM/FlashQLA | Linear-attention kernel library on TileLang, MIT, 643 stars |

### Documentation deep links

| Page | URL |
|---|---|
| MLX LM on Apple Silicon | https://qwen.readthedocs.io/en/latest/run_locally/mlx-lm.html |
| Function calling | https://qwen.readthedocs.io/en/latest/framework/function_call.html |
| vLLM Qwen recipes | https://recipes.vllm.ai/Qwen |
| SGLang docs | https://docs.sglang.io/ |
| Unsloth Qwen3.8 guide | https://unsloth.ai/docs/models/qwen3.8 |

## Model hosts

| Resource | URL | Notes |
|---|---|---|
| Qwen on Hugging Face | https://huggingface.co/Qwen | 462 repositories, 36 collections (25 Aug 2026) |
| Qwen on ModelScope | https://www.modelscope.cn/organization/Qwen | Alibaba's own hub; use when Hugging Face is unreachable. `SGLANG_USE_MODELSCOPE=true` / `VLLM_USE_MODELSCOPE=true` |
| Qwen3.8 collection | https://huggingface.co/collections/Qwen/qwen38 | |
| Qwen3.5 collection | https://huggingface.co/collections/Qwen/qwen35 | |
| Qwen3.8-27B | https://huggingface.co/Qwen/Qwen3.8-27B | Apache 2.0, 27,781,427,952 params |
| Qwen3.8-2.4T-A95B | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B | Qwen3.8-Max License, 2,446,182,725,504 params |
| Qwen3.5-27B | https://huggingface.co/Qwen/Qwen3.5-27B | Apache 2.0 |
| Qwen3-Embedding-8B | https://huggingface.co/Qwen/Qwen3-Embedding-8B | Apache 2.0, MRL 32–4,096 dims |
| Model index API | https://huggingface.co/api/models?author=Qwen | Machine-readable: dates, exact parameter counts, licences |
| Licence file (Max) | https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B/raw/main/LICENSE | Read this before commercial use |
| Licence file (Qwen 2024) | https://huggingface.co/Qwen/Qwen2.5-72B-Instruct/raw/main/LICENSE | The 19 Sep 2024 Qwen License Agreement |

## arXiv technical reports

All identifiers verified against the arXiv API on 25 August 2026; titles and dates as returned.

| Paper | arXiv ID | First submitted | URL |
|---|---|---|---|
| Qwen Technical Report | 2309.16609 | 2023-09-28 | https://arxiv.org/abs/2309.16609 |
| Qwen-VL | 2308.12966 | 2023-08-24 | https://arxiv.org/abs/2308.12966 |
| Qwen-Audio | 2311.07919 | 2023-11-14 | https://arxiv.org/abs/2311.07919 |
| Qwen2 Technical Report | 2407.10671 | 2024-07-15 | https://arxiv.org/abs/2407.10671 |
| Qwen2-Audio Technical Report | 2407.10759 | 2024-07-15 | https://arxiv.org/abs/2407.10759 |
| Qwen2-VL | 2409.12191 | 2024-09-18 | https://arxiv.org/abs/2409.12191 |
| Qwen2.5-Math Technical Report | 2409.12122 | 2024-09-18 | https://arxiv.org/abs/2409.12122 |
| Qwen2.5-Coder Technical Report | 2409.12186 | 2024-09-18 | https://arxiv.org/abs/2409.12186 |
| Qwen2.5 Technical Report | 2412.15115 | 2024-12-19 | https://arxiv.org/abs/2412.15115 |
| Qwen2.5-1M Technical Report | 2501.15383 | 2025-01-26 | https://arxiv.org/abs/2501.15383 |
| Qwen2.5-VL Technical Report | 2502.13923 | 2025-02-19 | https://arxiv.org/abs/2502.13923 |
| **Qwen3 Technical Report** | **2505.09388** | 2025-05-14 | https://arxiv.org/abs/2505.09388 |
| Qwen3 Embedding | 2506.05176 | 2025-06-05 | https://arxiv.org/abs/2506.05176 |
| Qwen3-Omni Technical Report | 2509.17765 | 2025-09-22 | https://arxiv.org/abs/2509.17765 |
| Qwen3-VL Technical Report | 2511.21631 | 2025-11-26 | https://arxiv.org/abs/2511.21631 |
| Qwen3-Coder-Next Technical Report | 2603.00729 | 2026-02-28 | https://arxiv.org/abs/2603.00729 |
| Qwen3.5-Omni Technical Report | 2604.15804 | 2026-04-17 | https://arxiv.org/abs/2604.15804 |
| Qwen-Image Technical Report | 2508.02324 | 2025-08-04 | https://arxiv.org/abs/2508.02324 |
| Qwen-AgentWorld | 2606.24597 | 2026-06-23 | https://arxiv.org/abs/2606.24597 |

**Not on arXiv as of 25 August 2026:** Qwen1.5, Qwen3-Next, **Qwen3.5**, Qwen3.6, **Qwen3.8**. For those generations the model cards, config files and the Qwen3.8 README are the only primary documentation.

Author-search shortcut: `http://export.arxiv.org/api/query?search_query=au:%22Qwen%20Team%22&sortBy=submittedDate&sortOrder=descending`

## Local inference — runtimes

| Tool | URL | Platform |
|---|---|---|
| **MLX** | https://github.com/ml-explore/mlx | Apple Silicon — the array framework |
| **mlx-lm** | https://github.com/ml-explore/mlx-lm | Apple Silicon — LLM inference and fine-tuning. Current: 0.31.3 (PyPI) |
| mlx-lm LoRA guide | https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/LORA.md | |
| mlx-lm example LoRA config | https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/examples/lora_config.yaml | |
| mlx-vlm | https://github.com/Blaizzy/mlx-vlm | Apple Silicon — vision-language |
| mlx-examples | https://github.com/ml-explore/mlx-examples | Reference implementations |
| mlx-my-repo (convert in-browser) | https://huggingface.co/spaces/mlx-community/mlx-my-repo | HF Space |
| llama.cpp | https://github.com/ggml-org/llama.cpp | Cross-platform, GGUF (default branch `master`) |
| Ollama — qwen3 | https://ollama.com/library/qwen3 | 58 variants, 0.6b–235b |
| Ollama — qwen3.5 search | https://ollama.com/search?q=qwen3.5 | 0.8b–122b, 64 tags |
| LM Studio | https://lmstudio.ai/ | GUI over llama.cpp and MLX; `lms` CLI |
| vLLM | https://github.com/vllm-project/vllm | Linux/CUDA server |
| SGLang | https://github.com/sgl-project/sglang | Linux/CUDA server |

## Quantisation providers

| Provider | URL | What they publish |
|---|---|---|
| **mlx-community** | https://huggingface.co/mlx-community | MLX 4/5/6/8-bit affine, `mxfp4`, `nvfp4`, `mxfp8`, `OptiQ`/`oQ4`/`oQ6`, MTP draft heads. **The primary source for Apple Silicon.** |
| **Unsloth** | https://huggingface.co/unsloth | GGUF including the `UD-` dynamic quants (IQ1 through Q8_K_XL), `mmproj` vision projectors, MTP draft GGUFs |
| **bartowski** | https://huggingface.co/bartowski | GGUF with imatrix calibration; long-standing community standard |
| Qwen first-party | https://huggingface.co/Qwen | `-FP8`, `-GPTQ-Int4`, `-GPTQ-Int8`, `-AWQ`, and some `-GGUF` and `-MLX` |

MLX search shortcuts: https://huggingface.co/models?search=mlx-community%20Qwen3.8 · https://huggingface.co/models?search=mlx-community%20Qwen3.5

## Fine-tuning frameworks

| Tool | URL | Platform |
|---|---|---|
| mlx-lm (`mlx_lm.lora`) | https://github.com/ml-explore/mlx-lm | Apple Silicon |
| Unsloth | https://github.com/unslothai/unsloth | CUDA; also a desktop app |
| LLaMA-Factory | https://github.com/hiyouga/LLaMA-Factory | CUDA; SFT/DPO/PPO/pretraining + web UI |
| MS-SWIFT | https://github.com/modelscope/ms-swift | CUDA; ModelScope/Alibaba's own |
| Axolotl | https://github.com/axolotl-ai-cloud/axolotl | CUDA; YAML-driven |
| TRL | https://github.com/huggingface/trl | The HF training primitives |
| PEFT | https://github.com/huggingface/peft | LoRA/DoRA/adapters, adapter merging |

## Benchmarks and leaderboards

Use these for orientation only — see `08` on why they are unreliable.

| Resource | URL | What it measures |
|---|---|---|
| LMArena | https://lmarena.ai/ | Blind pairwise human preference (Elo-style) |
| LMArena leaderboard (HF mirror) | https://huggingface.co/spaces/lmarena-ai/chatbot-arena-leaderboard | |
| MTEB leaderboard | https://huggingface.co/spaces/mteb/leaderboard | Text embedding — relevant to Qwen3-Embedding |
| LiveBench | https://livebench.ai/ | Contamination-resistant, monthly-refreshed questions |
| SWE-bench | https://www.swebench.com/ | Real GitHub issue resolution |

## Alibaba corporate and financial

| Resource | URL | Notes |
|---|---|---|
| Investor news and filings | https://www.alibabagroup.com/en-US/ir-news-filings | Press releases with dates; PDFs live on `data.alibabagroup.com` |
| Quarterly results index | https://www.alibabagroup.com/en-US/ir-financial-reports-quarterly-results | |
| **June Quarter 2026 results (PDF)** | https://data.alibabagroup.com/ecms-files/1532295521/fa5d65fc-9b3e-4e82-a8fc-4ce1c3e2c407/Alibaba%20Group%20Announces%20June%20Quarter%202026%20Results.pdf | Segment tables, capex, AI revenue |
| **Form 20-F, FY2026** | https://www.sec.gov/Archives/edgar/data/1577552/000119312526231755/baba-20260331.htm | Filed 20 May 2026; the authoritative source for everything corporate |
| SEC submissions index (JSON) | https://data.sec.gov/submissions/CIK0001577552.json | All filings, machine-readable |
| SEC XBRL — Revenues | https://data.sec.gov/api/xbrl/companyconcept/CIK0001577552/us-gaap/Revenues.json | Audited FY series |
| SEC XBRL — Operating income | https://data.sec.gov/api/xbrl/companyconcept/CIK0001577552/us-gaap/OperatingIncomeLoss.json | |
| SEC XBRL — Net income | https://data.sec.gov/api/xbrl/companyconcept/CIK0001577552/us-gaap/NetIncomeLoss.json | |
| Alizila (Alibaba newsroom) | https://www.alizila.com/ | Alibaba's own news site — product and model announcements |

> ⚠️ `data.alibabagroup.com` rejects requests without a browser user-agent (`denied by UA ACL = blacklist`). Pass a normal `User-Agent` header when scripting PDF downloads. `sec.gov` requires a `User-Agent` identifying you with contact details.

## Alibaba silicon and RISC-V

| Resource | URL | Notes |
|---|---|---|
| T-Head open-source cores | https://github.com/T-head-Semi | `openc910`, `openc906` and related XuanTie RTL |
| T-Head (background) | https://en.wikipedia.org/wiki/T-Head | Founding, chip timeline — secondary source |
| RISC-V (XuanTie context) | https://en.wikipedia.org/wiki/RISC-V | C910/C920/C930, RVA23, China policy — secondary source |
| Alibaba Cloud (background) | https://en.wikipedia.org/wiki/Alibaba_Cloud | Founding, international timeline — secondary source |
| Alibaba Group (background) | https://en.wikipedia.org/wiki/Alibaba_Group | Founding, IPO, antitrust — secondary source |



## Key facts

| Item | Value (checked 25 Aug 2026) |
|---|---|
| Primary code repository | `github.com/QwenLM/Qwen3.8` — covers Qwen3.5, 3.6 and 3.8 |
| Primary weight host | `huggingface.co/Qwen` — 462 repositories, 36 collections |
| Mirror for users without HF access | `modelscope.cn/organization/Qwen` |
| Apple Silicon quantisations | `huggingface.co/mlx-community` |
| GGUF quantisations | `huggingface.co/unsloth` and `huggingface.co/bartowski` |
| Last Qwen generation with an arXiv technical report | **Qwen3** (arXiv:2505.09388, 14 May 2025) |
| Authoritative corporate source | Form 20-F FY2026, SEC EDGAR, filed 20 May 2026 |
| Legacy blog status | `qwenlm.github.io/blog/` frozen at September 2025 |
| Current blog | `qwen.ai/blog?id=<slug>` — JavaScript SPA, not fetchable by scripts |

## Reading order for a newcomer

If you are coming to this domain cold and want the shortest path to competence:

1. **The Qwen3.8 README** (https://github.com/QwenLM/Qwen3.8) — ten minutes, and it gives you the current model list, the dated release history back to Qwen3-Next, and working deployment commands for four runtimes.
2. **One model card in full** — https://huggingface.co/Qwen/Qwen3.8-27B. Model cards in this family carry the architecture breakdown, sampling recommendations, benchmark tables and licence, and are more current than any paper.
3. **The Qwen3 Technical Report** (arXiv:2505.09388) — the last generation with a proper paper, and the one that explains thinking-mode fusion, thinking budgets and strong-to-weak distillation. Still the best single technical document in the family.
4. **The mlx-lm README and LORA.md** — the whole practical surface for Apple Silicon, in two files.
5. **Alibaba's most recent quarterly results PDF** — twenty pages that tell you more about why any of this exists than any amount of commentary.

Skip, for now: the Qwen 1 and Qwen2 technical reports (superseded), and every third-party "Qwen vs X" comparison article.

## Community and learning resources

| Resource | URL | What it is good for |
|---|---|---|
| Hugging Face model search — Qwen | https://huggingface.co/models?search=qwen | 290,280 matches (25 Aug 2026). Filter by `Libraries: MLX` to find Apple Silicon builds |
| Hugging Face MLX filter | https://huggingface.co/models?library=mlx | Every MLX-format model, not just Qwen |
| Qwen Discord | https://discord.gg/CV4E9rpNSD | Direct line to the Qwen team; release announcements land here first |
| Qwen Code docs | https://qwenlm.github.io/qwen-code-docs/ | Terminal agent setup, including pointing it at a non-Qwen endpoint |
| MLX community org | https://huggingface.co/mlx-community | Also the place to request a conversion |
| vLLM Qwen recipes | https://recipes.vllm.ai/Qwen | Tested server configurations per model |
| SGLang cookbook | https://docs.sglang.io/ | Ditto, for SGLang |

### What is *not* a good resource

- **Any blog post about "the best local LLM" older than three months.** In this domain that is two generations ago.
- **Benchmark tables reproduced from a model card into a third-party article.** They lose the self-reporting caveat in transit and acquire an air of independence they never had.
- **Parameter counts quoted from model *names*.** `Qwen3.5-397B-A17B` actually has 403,397,928,944 parameters and `Qwen3.5-122B-A10B` has 125,086,497,008. Use the safetensors index.
- **"Qwen3.7" open weights.** There are none — Qwen3.7-Max was API-only. Anything claiming to distribute them is not what it says it is.

## How to keep this domain current

The Qwen release cadence has been roughly one significant generation every three to four months since April 2025, with point releases and specialist lines in between. A quarterly refresh is the minimum; a monthly check of two endpoints is cheap:

**1. New models.** Run the Hugging Face model-index command below and diff the top twenty against `04`'s register. Anything new gets a row: date, exact parameter count, licence.

**2. New licence terms.** If a new top-tier model appears, `curl` its `LICENSE` file. Alibaba changed its licensing posture materially with Qwen3.8-Max, and it may change it again.

**3. Runtime support.** Check whether `mlx-lm` has a model file for the new architecture:

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/models/qwen4.py
```

A 200 means the architecture is supported and `mlx-community` quants will follow within days.

**4. Financials.** Alibaba reports quarterly; the 20-F lands in May. The SEC XBRL endpoints below give the audited series without reading a document.

**5. Architecture.** The `config.json` of any new flagship tells you most of what a technical report would, and it arrives months earlier. Read `layer_types`, `full_attention_interval`, `num_key_value_heads`, `head_dim`, `partial_rotary_factor`, `num_experts`, `num_experts_per_tok`, `vocab_size` and `max_position_embeddings`, and you can recompute the memory arithmetic in `06` for the new model in five minutes.

## Useful machine-readable endpoints

For keeping this domain current without manual browsing:

```bash
# every Qwen model with creation date, licence and exact parameter count
curl -s "https://huggingface.co/api/models?author=Qwen&sort=createdAt&direction=-1&limit=1000" \
  | jq -r '.[] | [.createdAt[0:10], .modelId, (.cardData.license // "?"), (.safetensors.total // "?")] | @tsv'

# repository byte size of a specific quantisation
curl -s "https://huggingface.co/api/models/mlx-community/Qwen3.8-27B-4bit?blobs=true" \
  | jq '[.siblings[].size] | add / 1e9'

# GGUF file sizes
curl -s "https://huggingface.co/api/models/unsloth/Qwen3.8-27B-GGUF?blobs=true" \
  | jq -r '.siblings[] | select(.rfilename|endswith(".gguf")) | "\(.rfilename)\t\(.size/1e9)"'

# architecture facts straight from the config
curl -s "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/config.json" | jq '.text_config'

# the chat template, verbatim
curl -s "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json" | jq -r '.chat_template'

# Qwen technical reports on arXiv
curl -s "http://export.arxiv.org/api/query?search_query=au:%22Qwen+Team%22&sortBy=submittedDate&sortOrder=descending&max_results=50"

# Alibaba's audited annual revenue series
curl -s -A "you you@example.com" \
  "https://data.sec.gov/api/xbrl/companyconcept/CIK0001577552/us-gaap/Revenues.json" \
  | jq -r '.units.CNY[] | select(.form=="20-F" and (.end|endswith("-03-31"))) | "\(.start) \(.end) \(.val)"'
```

## Sources

- [Qwen organisation on Hugging Face](https://huggingface.co/Qwen) and the [model index API](https://huggingface.co/api/models?author=Qwen)
- [QwenLM GitHub organisation](https://github.com/QwenLM) — repository list, star counts and update dates retrieved 25 August 2026
- [Qwen documentation](https://qwen.readthedocs.io/en/latest/) — table of contents used to build the deep-link list
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — official links to Qwen Studio, QwenCloud, Qoder, QwenWork, Qwen Code, Discord, ModelScope
- arXiv API (`http://export.arxiv.org/api/query`) — all identifiers, titles and submission dates verified 25 August 2026
- [Alibaba investor news and filings](https://www.alibabagroup.com/en-US/ir-news-filings); [SEC EDGAR submissions for CIK 0001577552](https://data.sec.gov/submissions/CIK0001577552.json)
- HTTP status checks: all non-GitHub URLs above returned 200 on 25 August 2026; GitHub repositories were confirmed via `raw.githubusercontent.com/<repo>/<branch>/README.md` returning 200

## Open questions

- `github.com` HTML pages return 403 to plain HTTP clients from this research environment, so the GitHub links were verified by repository existence rather than by rendering the page. They resolve normally in a browser.
- The `qwen.ai` blog is a JavaScript single-page application; `qwen.ai/blog?id=<slug>` URLs return 200 but yield no content to a non-browser fetcher. Individual release blogs (e.g. `qwen.ai/blog?id=qwen3.5`, `?id=qwen3.8`, `?id=qwen3.6-27b`, `?id=qwen3.6-35b-a3b`, `?id=qwen3-next`) are cited in the official README but could not be read here; their content is `needs-verification`.
- `qwenlm.github.io/blog/` appears frozen at September 2025 and may be deprecated rather than merely stale.
- TokenSpeed (https://github.com/lightseekorg/tokenspeed) is named as a supported inference engine in the Qwen3.8 README but was not independently verified here.
- ModelScope collection deep links (`modelscope.cn/collections/Qwen/Qwen38`) were not individually status-checked; only the organisation page was.
- Ollama's `qwen3.8` library entry did not exist at the time of checking; re-check before citing an Ollama tag for that generation.
