# 77-evidence — what produced the numbers in research doc 77

Produced on the **owner's Mac** on 2026-09-07 against the owner's own running
stack: a LiteLLM shim on `:4000`, `mlx_vlm.server` on `:8081`, and `:8080` /
`:8082` / `:8090` down. Nothing here starts, stops or configures anything —
`PROTECTED_PORTS` is the lane's law and it applies to its evidence too.

```bash
python3 shim-truth.py                       # the default endpoint
python3 shim-truth.py http://127.0.0.1:8081/v1
```

| file | what |
|---|---|
| `shim-truth.py` | asks every advertised route for six tokens and reads what comes back — stdlib only, no TEE import, so it runs anywhere |
| `shim-truth-2026-09-07.log` | what it printed: **advertised 8, produce text 2, 200-but-empty 4, errored 1** |
| `shim-truth.json` | the machine-readable rows |

**The fact the file exists for.** Four of eight advertised routes answer HTTP
200 with **empty content and a usage block claiming completion tokens**. A
liveness check that reads `/v1/models` — which is what `local_llm.available()`
does — sees eight healthy engines. A check that reads the HTTP status sees six.
Only reading the content is telling the truth.

That is the whole argument for the lane in one table, and it is why `eng_check`
asserts on content rather than on a status code.

**A caveat this evidence carries.** The stack changed twice during the session
that produced it: doc 77 §2 recorded *"nothing is answering at all"*, and by the
time of this run `:4000` and `:8081` were up. A re-run will not reproduce this
log, and should not be expected to — that volatility is the thing being
measured, not noise around it.
