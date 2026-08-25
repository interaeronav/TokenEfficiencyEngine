---
id: alibaba.qwen_agents
title: Using Qwen in agent systems — tool calling, MCP, RAG and honest limits
domain: 37_alibaba_and_qwen
tags: [qwen, agents, tool-calling, function-calling, mcp, qwen-agent, qwen-code, rag, qwen3-embedding, reranker, structured-output, context-management, evaluation, latency, privacy, local-llm]
jurisdiction: global
status: stable
confidence: medium
updated: 2026-08-25
sources:
  - {title: "QwenLM/Qwen-Agent README", url: "https://github.com/QwenLM/Qwen-Agent", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "QwenLM/Qwen3.8 README", url: "https://github.com/QwenLM/Qwen3.8", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "QwenLM GitHub organisation", url: "https://github.com/QwenLM", publisher: "Qwen Team, Alibaba Group", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3.8-27B tokenizer_config.json (chat template)", url: "https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen/Qwen3-Embedding-8B model card", url: "https://huggingface.co/Qwen/Qwen3-Embedding-8B", publisher: "Qwen / Alibaba Cloud", accessed: 2026-08-25}
  - {title: "Qwen documentation — framework integration", url: "https://qwen.readthedocs.io/en/latest/", publisher: "Qwen Team", accessed: 2026-08-25}
  - {title: "mlx-lm server source", url: "https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/server.py", publisher: "Apple / MLX contributors", accessed: 2026-08-25}
related: [alibaba.qwen_local, alibaba.qwen_models, alibaba.qwen_finetune, alibaba.open_weight_landscape]
---

# Using Qwen in agent systems — tool calling, MCP, RAG and honest limits

**Summary.** Qwen is now explicitly designed as an agent backend rather than a chat model: Qwen3.8's headline claims are agent execution, autonomous planning and "broader support for popular harnesses", and Alibaba ships its own agent stack (Qwen-Agent with MCP and code interpreter, Qwen Code as a terminal coding agent, Qwen-MM-Plugins to make any harness multimodal). Running that stack locally is entirely practical for tool-driven, bounded workflows — extraction, classification, routing, document QA, single-file code edits — and it is not yet a substitute for a frontier hosted model on long-horizon autonomous coding. This file covers what works, the specific integration details that break, and where the line actually is.

> ⚠️ **The single most important integration fact:** Qwen3.8's tool-call format is XML-ish, not JSON. A parser written for Qwen3 will silently fail. Details below.

## Key facts

| Item | Value |
|---|---|
| Qwen3.8 tool-call format | `<tool_call><function=name><parameter=k>v</parameter></function></tool_call>` |
| Qwen3 and earlier tool-call format | `<tool_call>{"name": ..., "arguments": {...}}</tool_call>` |
| vLLM/SGLang parsers | `--tool-call-parser qwen3_coder`, `--reasoning-parser qwen3` |
| Tool result role | Wrapped in `<tool_response>` inside a **user** message; no `tool` role on the wire |
| Qwen-Agent install | `pip install -U "qwen-agent[gui,rag,code_interpreter,mcp]"` |
| Qwen Code | Terminal coding agent, TypeScript, Apache 2.0, 27,000+ GitHub stars |
| Qwen3-Embedding-8B | 7,567,295,488 params, 32K context, up to 4,096 dims (MRL 32–4,096), 100+ languages, Apache 2.0 |
| Qwen3-Embedding MTEB multilingual | 70.58 mean, ranked #1 (as of June 2025, self-reported) |
| Qwen3-Reranker | 0.6B / 4B / 8B (8,188,548,096), Apache 2.0 |

## Qwen as a coding-agent backend

### What works locally

**Bounded, single-file edits.** "Add error handling to this function", "convert this class to use dataclasses", "write tests for this module". A Qwen3.8-27B at 4-bit handles these at a quality that is genuinely useful, and the round trip is fast enough to stay in flow.

**Code reading and explanation.** With a 262,144-token native context you can put a substantial module — or a whole small repository — in the prompt and ask questions about it. Prompt caching (`06`) makes repeated questions against the same codebase nearly free after the first.

**Mechanical transformation at scale.** Migrating a hundred files from one API to another, adding type annotations, normalising imports. These are exactly the tasks where a local model's zero marginal cost dominates: you can run it a thousand times overnight for the price of electricity.

**Tool-driven workflows.** Read a file, run a command, parse the output, decide the next step. Qwen3.8's post-training targets this explicitly ("stronger autonomous planning and better handling of environment feedback").

### What does not work locally, yet

**Long-horizon autonomous coding.** Twenty-plus tool calls, multiple files, holding a plan across a long session, recovering from a failed approach without human intervention. This is the frontier capability and it is where the gap between a local 27B and a hosted frontier model is largest and most obvious. Self-reported Qwen3.8-27B figures — SWE-bench Pro 61.7, Terminal Bench 73.0 — are respectable and not frontier, and self-reported numbers are optimistic (`08`).

**Subtle debugging.** Race conditions, memory issues, anything requiring holding several interacting constraints simultaneously.

**Anything where a wrong answer is expensive and unverified.** A local model that is right 90% of the time is excellent for tasks with a cheap verifier (tests, a compiler, a schema) and dangerous for tasks without one.

### Qwen Code

Alibaba's own terminal coding agent (`github.com/QwenLM/qwen-code`, TypeScript, Apache 2.0, 27,227 stars as of 25 August 2026), optimised for Qwen models. Positioned as "an open-source AI coding agent that lives in your terminal" for understanding large codebases and automating repetitive work. Companion projects: `qwen-code-docs` and `qwen-code-action` (a GitHub Action).

It defaults to QwenCloud but, being OpenAI-API-compatible, can be pointed at a local `mlx_lm.server` endpoint. Whether every feature degrades gracefully against a local model is `needs-verification`.

Related products (hosted, not local): **Qoder** — the agentic coding platform — and **QwenWork** — the enterprise workforce agent — both of which are the named examples in the Qwen3.8-Max License's "AI Work Assistant" carve-out (`04`).

## Tool calling — the details that matter

### The Qwen3.8 format

From the verified chat template, when `tools` are supplied the model receives a system message containing:

```
# Tools

You have access to the following functions:

<tools>
{"type":"function","function":{"name":"read_file","description":"...","parameters":{...}}}
{"type":"function","function":{"name":"run_shell","description":"...","parameters":{...}}}
</tools>

If you choose to call a function ONLY reply in the following format with NO suffix:

<tool_call>
<function=example_function_name>
<parameter=example_parameter_1>
value_1
</parameter>
<parameter=example_parameter_2>
This is the value for the second parameter
that can span
multiple lines
</parameter>
</function>
</tool_call>
```

followed by an `<IMPORTANT>` block reminding the model that the `<function=...>` block must nest inside `<tool_call>`, required parameters must be supplied, optional natural-language reasoning may precede but **not follow** the call, and it should not mention function calls when none are available.

Serialisation rule from the template: a string argument is emitted raw; anything else is `tojson`-encoded inside the `<parameter>` block. So a number appears as `42`, an object as `{"a":1}`, and a string as the string — **not quoted**. Your parser must know the schema to reconstruct types correctly.

Why they moved away from JSON: multi-line string arguments — a file's contents, a patch, a shell script — are painful inside a JSON string (escaping, newlines, embedded quotes) and are the dominant case for coding agents. The XML-ish form handles them natively. The cost is that it is not a standard the rest of the ecosystem parses.

### Tool results

Results come back as:

```
<|im_start|>user
<tool_response>
{result content}
</tool_response><|im_end|>
```

Consecutive tool results merge into a **single** user turn with multiple `<tool_response>` blocks. There is no `tool` role in the rendered prompt. If you are building message history by hand, use `{"role": "tool", "content": ...}` in the messages array and let the template do the conversion — do not hand-roll the wire format.

The template also detects whether the last user message is purely a tool response, and uses that to locate the "last real user query" for `preserve_thinking` purposes. Malformed tool-response wrapping breaks that detection.

### Getting reliable tool calls

1. **Use a server that parses for you.** `vllm serve ... --enable-auto-tool-choice --tool-call-parser qwen3_coder` or SGLang's equivalent. `mlx_lm.server` exposes OpenAI-compatible chat completions; verify how it surfaces tool calls for your model version before assuming.
2. **Keep the tool count low.** 5–10 tools is comfortable for a 27B; 30 tools degrades selection accuracy noticeably. Group related operations behind one tool with a mode parameter rather than exposing many.
3. **Write real descriptions.** Every parameter needs a description and, where applicable, an `enum`. The model reads them.
4. **Mark required parameters required.** The template explicitly reminds the model, and the reminder works.
5. **Set `reasoning_effort` appropriately.** For a routine tool call, `low` is faster and just as accurate. For planning which of several tools to use in a hard situation, `xhigh` earns its tokens.
6. **Validate and retry with the error.** Parse, validate against the schema, and on failure send the validation error back as a tool response. Qwen recovers well from explicit error messages.
7. **Cap `max_tokens` generously.** A truncated tool call is unparseable, and thinking blocks consume budget before the call is emitted.

### Reliability versus frontier closed models

Honest positioning, stated as a shape rather than a number since no independent measurement was run here:

- **Single tool call, clear situation:** a local Qwen3.8-27B is close to frontier. This case is essentially solved.
- **Tool selection among 10+ options:** noticeably worse. More wrong-tool selections, more parameter omissions.
- **Multi-step chains with error recovery:** clearly worse. The failure mode is repeating a failed call rather than trying a different approach.
- **Long sessions with accumulated state:** worst. Plans drift; earlier decisions are forgotten even within the context window.

The engineering response is to make the harness do more: constrain the tool set per step, validate aggressively, checkpoint state outside the context, and put a deterministic controller around the model rather than asking the model to be the controller.

## Qwen-Agent

Alibaba's own framework: *"Agent framework and applications built upon Qwen>=3.0, featuring Function Calling, MCP, Code Interpreter, RAG, Chrome extension, etc."*

```bash
pip install -U "qwen-agent[gui,rag,code_interpreter,mcp]"
# or from source
git clone https://github.com/QwenLM/Qwen-Agent.git && cd Qwen-Agent
pip install -e ./"[gui,rag,code_interpreter,mcp]"
```

Minimal agent:

```python
from qwen_agent.agents import Assistant

llm_cfg = {
    'model': 'Qwen3.8-27B',
    'model_server': 'http://127.0.0.1:8080/v1',   # your local mlx_lm.server
    'api_key': 'EMPTY',
}
bot = Assistant(llm=llm_cfg, function_list=['code_interpreter'])

for response in bot.run(messages=[{'role': 'user', 'content': 'Plot y = sin(x)/x for x in [-20, 20].'}]):
    print(response)
```

With a GUI:

```python
from qwen_agent.gui import WebUI
WebUI(bot).run()
```

Components: `BaseTool` for custom tools (subclass and register), `Assistant` and other prebuilt agents, a Gradio `WebUI`, a Docker-sandboxed code interpreter, a RAG pipeline, and a Chrome extension (Browser Assistant). Requirements: a DashScope key (`DASHSCOPE_API_KEY`) or any self-hosted OpenAI-compatible service; Docker for the code interpreter; Python 3.10+ for the GUI.

Also from the QwenLM organisation: **Qwen-MM-Plugins** ("Make any agent harness multimodal-native", 2,741 stars, Apache 2.0) — useful if your harness is text-only and you want to use Qwen3.5+'s native vision.

## MCP (Model Context Protocol)

Qwen-Agent supports MCP directly via the `[mcp]` extra, and MCP is the sanest way to give a local Qwen access to tools because it decouples tool implementation from harness.

Practical notes for MCP with a local Qwen:

- **Server tool descriptions become part of your prompt.** A verbose MCP server with 40 tools will eat several thousand tokens and degrade selection accuracy. Filter the tool set per task — most harnesses allow it.
- **Prompt caching pays for the tool block.** The MCP tool definitions are a stable prefix; `mlx_lm.server --prompt-cache-size` or `--prompt-cache-bytes` means you pay to encode them once rather than per turn.
- **Tool results are untrusted input.** An MCP server returning web content or another user's data is returning text that may contain instructions. Never let tool output alter the system prompt or the available tool set, and be more careful here with a local model than with a frontier one — smaller models are more susceptible to injection.
- **Schema translation matters.** MCP tool schemas are JSON Schema; Qwen's `<tools>` block takes them nearly verbatim, but deeply nested or `oneOf`-heavy schemas confuse smaller models. Flatten them.

## Prompt engineering for Qwen specifically

Things that are true of Qwen and not universally true:

- **Use the chat template.** Always `apply_chat_template`. Hand-rolled ChatML misses the `<think>` opening, the `reasoning_effort` injection and the tool-block structure.
- **The system message must come first**, and cannot contain images or videos — the template raises an exception otherwise.
- **Decide about thinking per task.** Structured extraction: `enable_thinking: false`. Routine tool calls: `reasoning_effort: low`. Hard reasoning: `xhigh` (the default). Leaving thinking on for a JSON extraction task costs latency and breaks naive parsers.
- **`preserve_thinking: false` for long agent loops.** Replaying every previous turn's reasoning fills the context with material the model does not need. Turning it off is often the difference between fitting and not fitting.
- **Use the published sampling parameters** (`06`). Temperature 1.0 with top_p 0.95 for thinking; 0.7/0.80 with `presence_penalty` 1.5 for instruct. Leave `repetition_penalty` at 1.0.
- **Qwen follows explicit format instructions well.** "Respond with only a JSON object, no prose, no markdown fences" works. It is less good at inferring format from context than a frontier model, so be explicit.
- **Multilingual prompting works.** Qwen3.5 claims 201 languages. Prompting in the target language often produces better output than prompting in English and asking for a translation.
- **Give it structure to hold.** Numbered steps, explicit state, and a required output template outperform open-ended instructions by a wider margin on a 27B than on a frontier model.

## Context management and long documents

Qwen3.5-generation models have a 262,144-token native window extensible to about 1,010,000. That does not mean you should fill it.

**The practical hierarchy:**

1. **Retrieval first.** Even with a million-token window, retrieving the relevant 5,000 tokens is faster, cheaper and usually more accurate than putting a million in.
2. **Prompt caching for a fixed corpus.** If you are asking many questions of one document, cache the prefill once (`mlx_lm.cache_prompt`) and pay only for the questions.
3. **Structured chunking for very long documents.** Map-reduce: summarise sections, then reason over summaries. Slower, but it degrades gracefully where a single enormous prompt does not.
4. **Watch the KV cache budget.** From `06`: Qwen3.8-27B costs 64 KiB per token of context. A 262,144-token prompt is 17.2 GB of cache on top of 16 GB of weights. `--kv-bits 8` halves it.
5. **Position matters.** All long-context models degrade on material in the middle of a very long context. Put the most important material at the start or the end, and state explicitly where the answer should be found if you know.
6. **YaRN is opt-in for a reason.** Enabling RoPE scaling to reach 1M tokens costs a little quality on short prompts. Do not enable it globally if most of your traffic is short.

## Structured output and JSON reliability

Ordered by reliability, as in `06`:

1. **Grammar/schema-constrained decoding** — llama.cpp `--json-schema`, vLLM/SGLang guided decoding. Malformed output becomes impossible. This is the correct answer whenever the runtime supports it.
2. **Tool calling as a schema mechanism** — define one function whose parameters are your schema. With Qwen3.8's delimiter-based format this is more robust than free-form JSON.
3. **Prompt, validate, retry** — works well with Qwen, which is a strong JSON generator. Feed the parser error back on failure.

Rules regardless of method:
- **Thinking off** for structured output.
- **No markdown fences** — say so explicitly; Qwen will otherwise sometimes wrap JSON in ```json.
- **Give a complete example** of the exact output in the system prompt.
- **Use `null`, not omission**, for missing fields, and say so — otherwise the model drops keys.
- **Validate every field, not just parseability.** Valid JSON with a hallucinated date is worse than a parse error.

## Embeddings and the retrieval stack

Alibaba ships a complete Apache-2.0 retrieval stack in the same family.

**Qwen3-Embedding** — 0.6B, 4B, 8B (7,567,295,488 params for the 8B). 32,000-token context. Embedding dimension up to 4,096 with **Matryoshka representation learning**, so you can truncate to any dimension from 32 to 4,096 and keep most of the quality — a real operational win, because you can store 256-dimension vectors and re-rank with 4,096 only where it matters. 100+ languages. Instruction-aware: prefixing the query with a task instruction improves results by a reported 1–5%. Self-reported MTEB multilingual mean 70.58 (ranked #1 as of June 2025), MTEB English v2 75.22, C-MTEB 73.84.

**Qwen3-Reranker** — 0.6B, 4B, 8B (8,188,548,096 for the 8B). A cross-encoder that scores query–document pairs directly. Far more accurate than embedding similarity and far more expensive, so it is used on the top-k from the first stage.

**Qwen3-VL-Embedding / -Reranker** (2B, 8B, January 2026) — multimodal retrieval over images and documents.

**A working local RAG stack on a Mac:**

| Stage | Model | Notes |
|---|---|---|
| Chunk | — | 300–800 tokens with overlap; respect document structure |
| Embed | `Qwen3-Embedding-0.6B` (GGUF or MLX) | Fast enough to index a large corpus locally; truncate to 512–1024 dims |
| Store | any vector DB, or `sqlite-vec` / FAISS locally | 1,000,000 chunks × 512 dims × 4 bytes ≈ 2 GB |
| Retrieve | top 50 by cosine | Add BM25 and fuse (hybrid) — this is usually the single biggest quality win |
| Rerank | `Qwen3-Reranker-0.6B` or `-4B` | Cut 50 → 5 |
| Generate | `Qwen3.8-27B-4bit` via `mlx_lm.server` | Thinking off or low for extraction; on for synthesis |

Everything in that table is Apache 2.0 and runs on a single machine.

Practical notes: use the **instruction prefix** for queries (the model is trained for it); embed documents without it. Keep embedding and reranking models loaded in a separate process from the generator so you are not reloading weights. Re-embed when you change model or dimension — vectors from different models are not comparable.

## Evaluating an agent built on a local model

You cannot evaluate an agent with a benchmark. Build a harness:

1. **Fix a task set.** 30–100 real tasks from your workload, each with a deterministic success check (a file that must exist, a test that must pass, a field that must match).
2. **Score end-to-end success**, not step quality. An agent that takes 15 steps to succeed beats one that takes 3 elegant steps and fails.
3. **Log every tool call.** The failure taxonomy you need: wrong tool, right tool with wrong arguments, correct call with mishandled result, loop, premature stop, format error. Each has a different fix and only the last is fixed by a better model.
4. **Cap steps and measure the distribution**, not just the mean. A p95 of 40 steps on a task that should take 5 tells you the model is thrashing.
5. **Run each task 5+ times.** Agent runs are high-variance; a single run tells you nothing.
6. **Track cost and latency per task** alongside success rate.
7. **Re-run on every change** — model version, quantisation, prompt, tool schema. Quantisation changes agent behaviour more than it changes chat quality, because errors compound across steps.
8. **Keep a frontier-model baseline** on the same harness. It tells you whether a failure is your harness or the model.

## Cost and latency versus API models

**Latency.** A local Qwen3.8-27B at 4-bit on Apple Silicon has near-zero time-to-first-token for a short prompt (no network) and a decode rate bounded by memory bandwidth. An API frontier model has 200–800 ms of network and queueing but much higher decode throughput. For short interactive turns local often *feels* faster; for long generations the API wins. Actual tokens/second on specific hardware is `needs-verification` — measure with `mlx_lm.benchmark`.

**Cost.** The local marginal cost per token is electricity — effectively zero at individual scale. The fixed cost is the machine. The crossover depends entirely on volume:

- **Low volume (a few hundred requests/day):** API is cheaper in total cost of ownership. Do not buy a Mac Studio to save on API bills.
- **High volume, especially batch:** local is dramatically cheaper. Processing 100,000 documents overnight costs nothing locally and real money via API.
- **Bursty/interactive:** API, unless privacy dictates otherwise.
- **The honest framing:** you do not run models locally to save money at small scale. You run them locally for privacy, availability, latency floor, unlimited experimentation, and the absence of a rate limit or a vendor deprecating your model.

**The cost that is usually forgotten:** thinking tokens. A `reasoning_effort: xhigh` response can emit thousands of tokens of `<think>` before the answer. Locally that is wall-clock time; via API it is billed output. Set effort deliberately.

## Privacy and data residency

The strongest arguments for local Qwen have nothing to do with capability:

- **Nothing leaves the machine.** No provider terms, no retention policy, no training-on-your-data question, no subprocessor list.
- **Regulatory fit.** Personal data under GDPR or comparable regimes, medical records, legal privilege, client confidentiality, defence and export-controlled material — a local model removes the transfer entirely rather than papering it with a DPA.
- **Availability.** No outage, no rate limit, no sudden pricing change, no model deprecation. A model you have downloaded works forever.
- **Reproducibility.** A fixed checkpoint with a fixed seed gives the same output next year. Hosted models change under you without notice.
- **Air-gapped operation.** Field work, secure facilities, poor connectivity.

> ⚠️ Local does not mean secure. The machine, the model files and the logs still need protecting, and a local model can still leak through the outputs you send elsewhere. "Local" removes one class of exposure, not all of them.

**A note specific to Chinese models:** running Qwen weights locally sends nothing to Alibaba. The weights are static files. The relevant residual concerns are (a) content-policy behaviour baked into the alignment, and (b) supply-chain trust in the artefact itself — mitigated by downloading from the official Hugging Face repository over TLS and checking the published hashes. Using Alibaba's *API* is an entirely different question with entirely different data-residency implications.

## The honest limits

A local Qwen will not be good enough when:

1. **The task is long-horizon and autonomous.** Twenty-plus dependent steps without supervision. Use a frontier model or restructure the task.
2. **A wrong answer is expensive and unverifiable.** Medical, legal, financial or safety decisions without a human check.
3. **The reasoning is genuinely hard.** Novel mathematics, subtle proofs, deep multi-constraint problems.
4. **You need the very latest world knowledge.** The weights have a training cutoff and no browsing. Retrieval fixes this; the model alone does not.
5. **Throughput must be high and concurrent.** One Mac serves one or a few concurrent sessions. A datacentre serves thousands.
6. **The context genuinely needs to be enormous *and* precisely recalled.** Long-context degradation is real in all models, and worse in smaller ones.
7. **You need multimodal capability at frontier quality.** Qwen3.5+ vision is good; it is not the best available.
8. **Content policy blocks your domain.** PRC-aligned refusal behaviour is a real constraint for some topics.

**The productive pattern is a hybrid.** Route by task: local Qwen for the high-volume, privacy-sensitive, latency-sensitive, easily-verified work — extraction, classification, routing, summarisation, embedding, first-draft code — and a frontier API for the small fraction of requests that genuinely need it. Measured on a real workload, that fraction is usually between 5% and 20%, which is exactly the shape that makes a local model worth running.

## Sources

- [QwenLM/Qwen-Agent README](https://github.com/QwenLM/Qwen-Agent) — framework description, installation extras, `Assistant` and `WebUI` usage, MCP and code-interpreter support, requirements
- [QwenLM/Qwen3.8 README](https://github.com/QwenLM/Qwen3.8) — agent execution claims, `reasoning_effort` and `preserve_thinking`, Qwen Code, Qoder, QwenWork, vLLM/SGLang parser flags
- [QwenLM GitHub organisation](https://github.com/QwenLM) — qwen-code (27,227 stars), qwen-code-action, Qwen-MM-Plugins (2,741 stars), repository dates
- [Qwen/Qwen3.8-27B tokenizer_config.json](https://huggingface.co/Qwen/Qwen3.8-27B/raw/main/tokenizer_config.json) — the exact tool-call instruction text, parameter serialisation rule, `<tool_response>` handling, system-message constraints
- [Qwen/Qwen3-Embedding-8B model card](https://huggingface.co/Qwen/Qwen3-Embedding-8B) — dimensions, MRL range, context, MTEB figures, instruction-awareness
- [Qwen documentation index](https://qwen.readthedocs.io/en/latest/) — framework integration section (Qwen-Agent, function calling, LlamaIndex, LangChain)
- [mlx-lm server.py](https://raw.githubusercontent.com/ml-explore/mlx-lm/main/mlx_lm/server.py) — prompt caching and concurrency flags
- Parameter counts from the [Hugging Face model API](https://huggingface.co/api/models?author=Qwen)

## Open questions

- Whether `mlx_lm.server` parses Qwen3.8's XML tool-call format into OpenAI-style `tool_calls` objects, or returns it as raw text, is `needs-verification` — the server source was inspected only for its CLI flags.
- Independent tool-calling accuracy measurements for Qwen3.8-27B versus frontier models are `needs-verification`; the qualitative ordering above is a reasoned expectation, not a measurement.
- Qwen Code's behaviour against a local (non-QwenCloud) endpoint is `needs-verification`.
- Qwen3-Embedding's MTEB ranking is from June 2025 and is certainly stale by August 2026; treat the #1 claim as historic.
- Whether a newer Qwen3.5-generation embedding/reranker exists (superseding Qwen3-Embedding) was not established — the most recent embedding releases found were Qwen3-VL-Embedding/-Reranker in January 2026.
- Measured tokens/second and time-to-first-token on specific Apple Silicon hardware are `needs-verification`.
