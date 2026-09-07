# The engine lane (`eng_*`)

Truth about the local models TEE routes work to — what is actually answering,
what the weights actually are, and how fast an engine actually is on this
machine today.

Design of record: `docs/research/77-engine-lane.md`. Plan of record:
`CLAUDE_A76_SCRIPT.md`. Evidence: `docs/research/77-evidence/`.

## Why it exists

`kernel/machine.py::ENGINES` is the table the cascade sorts on. It **declares**
capability, footprint, latency, senses and token floors, and
`llm/router.py::_ladder()` orders the rungs on those numbers — which are
hand-copied literals stamped with the date of the session that produced them.
Nothing has ever reconciled them against what is running.

The measurement that made the case, on the owner's own stack:

```
:4000 advertises 8 routes | produce text 2 | 200-but-empty 4 | errored 1
```

Four of eight advertised routes answer **HTTP 200 with empty content and a usage
block claiming completion tokens**. `local_llm.available()` asks
`GET /v1/models` and would call all eight healthy. A check reading the HTTP
status would call six healthy. Only reading the **content** is telling the
truth — which is why `eng_ask` exists and why it is not called `eng_check`.

## The loop

```
eng_scan → eng_reconcile          (what is running, and where the registry is wrong)
        ↘ eng_ask                  (does this one route actually produce text)
        ↘ eng_senses               (what do the weights say about themselves)
        ↘ eng_audition → eng_adopt (measure it, then let the ladder sort on it)
```

| tool | what it does |
|---|---|
| `eng_scan` | every endpoint TEE knows → `GET /v1/models`: who answered, how fast, which server software. Lists only; never generates. Caches the result. |
| `eng_reconcile` | **the digest.** `ENGINES` × profiles × the cached scan × the measured file, one verdict and one remedy per row. Never probes. |
| `eng_ask` | one completion, and it reads the **content**. Reports `answers` or `empty-200`, with a conformance block. |
| `eng_senses` | resolves a model id to its weights by stdlib path arithmetic, reads `config.json` for vision/audio, sums the tensor files for a real footprint. |
| `eng_audition` | runs TEE's own triage chore against the engine, graded by that chore's own validator: warm and cold latency, verified rate, and the token floor by descending sweep. A job. |
| `eng_adopt` | writes a measured row where the ladder reads it. Refuses a paid engine. Never writes your config. |

## What a reply looks like

```
eng_reconcile
  endpoints 2 scanned / 2 answering        measured rows 1
  q14b+a2     unmeasured            reachable, never measured: eng_audition
  q27b-bare   live                  measured and current
  dsflash     declared-not-served   no profile declares 'dsflash': no model id,
                                    so nothing routes here. Declare it or drop the row
```

375 tokens for the whole picture, against **21,979** to read `machine.py`,
`profiles.py`, `router.py`, `llm/tools.py`, `local_llm.py`, the head of
`chores.py`, your config and the shim's — a **59×** saving, and that read does
not even answer the question, because the empty-200 table above is in none of
those files.

## The laws it is built to

1. **TEE serves no model.** Client and witness only; a test asserts the package
   opens no listening socket.
2. **The lane measures; the owner declares.** It never writes
   `.tee/config.toml` — it prints the line to paste.
3. **Never start or stop anything**, and never touch `PROTECTED_PORTS`
   (`8080, 8090, 4000` — your chat stack).
4. **Never call a paid engine** — refused by name, not gated behind consent.
   Measuring a hosted model would bill you to learn a number the router is
   forbidden to use.
5. **Never download weights.** It reads what is on disk and talks to what is
   running.
6. **Senses come from the weights' own `config.json`, never from behaviour** —
   a shim that reroutes image requests makes every model look like it can see.
7. **A latency without a warm/cold label is a lie.** Both are reported; the
   ladder sorts on warm.
8. **The digest never probes.** Probing is a tool you choose.

## What an audition is worth

Measured on this machine against `mlx-community/Qwen3.8-27B-bf16`:

```
cold 47.1 s   warm [44.3, 45.0]   verified 1.0   floor <= 64 tokens
```

The registry declares that engine at `[3.07, 9.69]` — about **five times faster
than it is today**. Adopting the measured row moves it from third on the ladder
to last, which is the whole point: the number the lane measures becomes the
number the cascade sorts on.

Note the `<=`. The sweep passed every rung down to 64 and never failed, so 64 is
an **upper bound** on the floor, not the floor. Calling it the floor would be a
declaration dressed as a measurement.

## What it will not tell you

A model served from a content-addressed store (oMLX keeps `~/.omlx/cache/0..f`)
has no recoverable identity, so its senses come back `unverified` with the
reason rather than a guess. And a row is a fact about **an endpoint serving a
model**, not about the weights: a proxy in front adds its own latency, so the
row records the url and the server fingerprint beside the number.
