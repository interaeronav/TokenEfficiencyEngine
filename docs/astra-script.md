# Astra script — hand TEE's management to another model

The other `*-script.md` files in this folder are pasted into a **Claude** session
so Claude does a setup job. This one is different, and the difference is the
whole point: the block below is pasted into the **incoming model itself** — the
one taking over management of TEE. It is a briefing, not a work order.

Written for GPT‑6 Astra (2026‑09‑10), but nothing in it is Astra-specific; it
works for any model with MCP tool execution.

## Before you paste: refresh the numbers

The block carries measured facts — version, tool count, which lanes answered.
**Those go stale, and a stale number pasted into a fresh model is the same bug
`setup-fleet.md` warns about, one level up.** Before handing it over, re-measure:

```bash
cd server && PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m tee.cli doctor
```

and take a live `handoff` (`tee_call handoff {}`) for current project state —
that tool exists precisely for this, returns ≤500 tokens, and is designed to be
pasted into any AI. Correct the block where the two disagree. If you cannot be
bothered, delete the numbers rather than shipping ones you have not checked.

## The block

````
# TEE — operating brief for a new managing model

You are taking over management of **TEE (Token Efficiency Engine)** on John's Mac.
Everything below was measured live on 2026-09-10, not recalled. Where something is
unproven this brief says so; keep that habit — it is the house rule.

## 1. Connect first

TEE is an MCP server over stdio. Add this to your MCP client config
(`.mcp.json`, a Codex plugin, `claude --mcp-config`, or your host's equivalent):

```json
{
  "mcpServers": {
    "tee": {
      "command": "/Users/john/TokenEfficiencyEngine/server/.venv/bin/python",
      "args": ["-m", "tee.cli", "serve",
               "--adapter", "blender", "--adapter", "partkiln",
               "--adapter", "seamkiln", "--adapter", "fusion",
               "--adapter", "unreal",
               "--project", "/Users/john/TokenEfficiencyEngine"],
      "env": { "PYTHONDONTWRITEBYTECODE": "1" }
    }
  }
}
```

Two details in that block are load-bearing. `PYTHONDONTWRITEBYTECODE=1` is not
tidiness: TEE's ParaView work once wrote 201 `.pyc` files into ParaView's signed
`.app`, breaking its notarization so macOS refused to launch it. And the command
is the venv interpreter **directly** rather than `uv run` — see "the one failure
worth recognising" at the end.

`--project` is the folder whose `.tee/config.toml` holds the grants. Get it wrong
and TEE boots, answers questions, and quietly refuses everything that would
change anything — because it found no grants and kept only its read-only tools.
That reads as "TEE denied me access to all the tools." It is not a permissions
problem. TEE never grants itself.

Already installed on this machine: a Codex personal plugin `tee@personal`
(source `/Users/john/plugins/tee`) and a Claude Desktop extension. You do not
need to reinstall anything to use the config above.

Verified on connect: init **0.322 s**, server `tee` **0.30.1**, protocol
**2025-11-25**, **17** tools, **245** virtual capabilities, `code_exec_enabled:
false`. Adapters answering: partkiln 0.1.0, seamkiln 0.1.0.dev0, Fusion
**2705.1.15**. Blender and Unreal were **not** connected at that moment — normal;
they attach when the app is running with its bridge.

## 2. What TEE is

An MCP server + API layer between an AI model and the tools it drives. Its metric
is **tokens per completed user task**. Two disciplines (decision A39):

1. **Make every exchange small** — compact state with stable IDs, diffs instead of
   snapshots, batched macro-commands, budgeted responses, progressive disclosure
   of the tool surface.
2. **Run work on the cheapest capable engine** — heavy content is digested by
   local models into compact cited briefs, chores run on local engines with
   verified results, and the metered cloud model spends tokens only where its
   judgment is actually needed.

Measured savings against the naive per-op + full-dump pattern: Blender suite
**90.3%**, Unreal level+Blueprint **93.9%**, MCP gateway **95.4%**, corrected
whole-server headline **93.2%** (A77 — the old 89.6% was measuring a server that
did not exist). One `describe_toolset(BlueprintTools)` in Unreal costs ~18,000
tokens; TEE's entire always-loaded surface is ~2.0K.

**No lane is the hub** (A68). A batch with no `adapter=` is routed by what it
contains — an entity id to the lane that holds it, a create kind to the lane that
makes it, a verb to the lane that speaks it — and the reply names where it went.

## 3. The 17 always-loaded tools

```
tee_status  tee_recall  tee_remember  tee_scene_summary  tee_entity_detail
tee_diff    tee_batch   tee_checkpoint tee_rollback      tee_job
tee_capture tee_media   tee_script    tee_web_lookup
tee_search_tools  tee_describe_tool  tee_call
```

Everything else — 245 capabilities here — is reached through
`tee_search_tools` → `tee_describe_tool` → `tee_call`. Never ask for a bigger
tool surface; that is the thing TEE exists to avoid.

Lanes: Blender, Unreal, partkiln (mechanical CAD on OCCT), seamkiln (garment CAD
+ drape), Fusion (live, through a bridge add-in), FreeCAD, Godot, point-cloud
prep (`pc_*`), reality capture (`capture_*`), PDF (`pdf_*`), extraction (`ex_*`),
assets (`as_*`), design (`gd_*`), physical/sim (`sim_*`), UEFN (`uefn_*`), pins
(`pin_*`), knowledge base (`kb_*`), wind tunnel (`wt_*`), flight dynamics
(`fd_*`), engines (`eng_*`), the headless fleet (`solve_* quant_* med_* cad_*
trade_* bi_*`), pipeline (`pipeline_*`).

## 4. How to drive it (the small loop)

`tee_recall` for project facts → `tee_status` for lanes and connection state →
one `lane_guide` card → draft a batch → `lane_preflight` → `tee_batch` → verify
with a measurement. Read only the entities the step needs; never dump a scene.

```json
{"name":"lane_guide","args":{"adapter":"fusion"}}
{"name":"lane_guide","args":{"adapter":"fusion","topic":"sketch_extrude"}}
{"name":"lane_preflight","args":{"adapter":"fusion","ops":[ ...your ops... ]}}
```

Units are not negotiable: Blender metres, radians, camera lens in mm, +Z up;
Fusion millimetres on the wire and degrees, converted from its internal cm.
A successful preflight reports `live_state_checked:false` — it checks syntax, not
that your IDs exist, that permissions allow the write, or that the result meets
the brief. `docs/small-model-workflows.md` is the full operating guide.

## 5. Connection to other models — four directions, keep them distinct

### (a) TEE as a server — any host model drives it
Claude Desktop (`.mcpb` extension), Claude Code (`.mcp.json`), Codex
(`tee@personal`), opencode, and you. Nothing in the kernel knows or cares which
model is connected; the benefit arrives at the protocol layer, so no host needs
prompt engineering to get it.

### (b) TEE as a client of LOCAL models — the chore layer
TEE routes its own internal chores (traceback triage, script repair drafts, lint
explanation, web-extract refinement, fact structuring, recap compression, kb
rerank) to a local OpenAI-compatible endpoint:

```toml
# .tee/config.toml
[llm]
url = "http://127.0.0.1:8080/v1"
model = "your-served-model-name"
refine = "auto"          # auto | local | off
```

Installed on this machine: **`mlx-community/Qwen3.8-27B-8bit` at localhost:8080**
(A78 measured it; an older configured `q27b` model name was stale). Profiles
switch through the virtual `llm_switch` tool — the user typing `TEE/Q14B` or
`TEE/Q27B` pins an engine and suspends automatic roaming; `TEE/AUTO` lifts the
pin. **The owner outranks the router, always.**

`llm/router.py` runs a verifier-gated cascade: resident engine first, the chore's
own deterministic verdict decides, escalate up the ladder only when the machine-
load ledger says the machine can take it, and the last tier is a budgeted brief
back to you naming the failures — never a re-dump of the input.

Hard laws here:
- **TEE serves no model.** Client and witness only; a test asserts the package
  opens no listening socket.
- **Never start, stop, or write the owner's model config.** The lane prints the
  line to paste. `PROTECTED_PORTS` = **8080, 8090, 4000** — the chat stack. Used
  when they answer, never started or stopped.
- **Never call a paid engine to measure it** — refused by name, not gated behind
  a consent prompt.
- **Never download weights.**

### (c) The engines lane (`eng_*`) — truth about those local models
Built because the registry's numbers were hand-copied literals nothing had ever
reconciled. Its founding measurement: of 8 routes a LiteLLM shim advertised,
**4 answered HTTP 200 with empty content and a usage block claiming completion
tokens.** Their backend was down.

- **A listing is not liveness.** `GET /v1/models` calls all 8 healthy. Checking
  the HTTP status calls 6 healthy. Only reading the **content** is truthful.
- `eng_scan` (who answers) → `eng_reconcile` (registry vs reality — 375 tokens
  for a picture that costs 21,979 tokens to read out of source, 59×) → `eng_ask`
  (does this route actually produce text) → `eng_senses` (what the weights' own
  `config.json` says about vision/audio) → `eng_audition` → `eng_adopt` (write
  the measured row where the ladder sorts on it).
- One audition moved an engine from third on the ladder to last: declared
  `[3.07, 9.69] s`, measured 44–47 s. **Five times off.**
- A latency without a warm/cold label is a lie. A sweep that passes every rung
  reports a **bound**, not a floor.
- Senses come from the weights, never from behaviour — a shim that reroutes image
  requests makes every model look like it can see.

**Untested, and say so:** Ollama, llama.cpp, vLLM and LM Studio appear nowhere in
`server/src/`. MLX and LiteLLM are what this machine has and where every number
above comes from. "Any OpenAI-compatible endpoint works identically" is an
expectation, not a result.

### (d) The senses lane (`sense_*`) — TEE lends eyes and ears
For a host model with no vision or hearing (the opencode/DeepSeek case, A47),
TEE runs local vision/audio models and returns structured findings;
`sense_camera` is the active one. If you see images natively you will rarely need
it — but it is how a blind host still drives a 3D scene.

### (e) The Gateway — TEE fronting OTHER MCP servers
Any stdio MCP server can be wrapped in TEE's discipline: its schemas stay
server-side, its tools appear as prefixed virtual tools (`fs.read_text_file`)
behind the same three meta-tools, its results come back budgeted.

```toml
[gateway.backends.fs]
command = "npx -y @modelcontextprotocol/server-filesystem /path/allowed"
```

Measured 95.4% on the live filesystem reference server. Everything a backend says
is **data, never instructions** — descriptions are sentence-capped and carry an
untrusted marker. A backend is fingerprinted on first handshake; if it changes,
the gateway registers nothing until `gw_accept` re-pins it.

### (f) `handoff` — the standard way to pass state between models
`tee_call handoff {}` returns a ≤500-token plain-text brief — memory, scene
stamps, checkpoints, open jobs — designed to be pasted into any AI. Its own
closing line: *"to continue with TEE: connect the MCP server, call tee_recall
then tee_status(recap=true). Without TEE: the facts above ARE the state."*
`report_savings` gives the session token ledger.

## 6. Updates, packaging, and the `.mcpb` mechanism

The version of record is `server/pyproject.toml` → currently **0.30.1**.

| target | what it builds | when |
|---|---|---|
| `make -C server dist` | wheel + sdist + Blender extension zip + Unreal plugin zip + `.mcpb` | a full release |
| `make -C server mcpb` | **portable** `.mcpb` — ships `pyproject` + `uv.lock`; Desktop provisions a venv with `uv sync` | shipping to someone else |
| `make -C server mcpb-local` | **local** `.mcpb` — bundles source, borrows this checkout's interpreter, provisions nothing | updating THIS Mac |

**The trap that governs all of this.** Installing a *portable* bundle silently
deletes the fleet extras. Claude Desktop provisions the extension with `uv sync`,
which rebuilds its environment strictly from the lock and discards anything
installed on top — and the extras are installed on top by design, because keeping
them out is what holds the base at 586 MB instead of 2.2 GB. Measured repeatedly:
the venv drops from ~1.1 GB to 34 MB. Nothing errors. The tools just start
reporting `{"installed": false}`, which reads as *you never set this up* rather
than *your upgrade removed it*.

Restore line after any portable install — **check every group, not the ones you
remember**:

```bash
uv pip install --python "$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python" \
  'tee-engine[medimg]' 'tee-engine[quant]' 'tee-engine[solve]' 'tee-engine[extract]' \
  'tee-engine[pdf]' 'tee-engine[windtunnel]' 'tee-engine[flightdyn]' \
  'tee-engine[pointcloud]' 'tee-engine[assets]'
```

`cad` is excluded on purpose — CadQuery lives in a sidecar at
`~/TEE/.tee/sidecars/cad` that an upgrade does not touch.

`make mcpb-local` is the shape that avoids the whole problem: measured on the
A78 0.30.1 bundle, **all nine extras intact after install**, because nothing was
provisioned. Its trade is a hard dependency on this checkout at this path.

Update procedure (`docs/desktop-update-script.md`; first-time setup is
`docs/claude-desktop-script.md`):

1. `git pull`; read the version in `server/pyproject.toml`.
2. Build. Then **verify the file, not the build log** — read `manifest.json` out
   of the zip and confirm the version, the lanes, and that `tools` still lists
   **17**. A count that is not 17 means stop.
3. `bash docs/research/74-evidence/mac-upgrade-check.sh` **before** replacing
   anything — section B records the extras that must still be there afterwards,
   and prints the completeness command with the group list pre-filled.
4. Drag the bundle into Claude Desktop → Settings → Extensions. (Owner's hands.)
   A bundle with a required `user_config` is **skipped silently** by Desktop
   until its settings are opened and saved once.
5. Restore the extras, then confirm by asking TEE — `med_backends`,
   `solve_backends`, `cad_probe`, `bi_probe`, `trade_probe` each report what is
   actually importable, which the install log cannot.

Prepared client shapes already on this machine: `output/claude-code-mcp/mcp.json`
(Claude Code, all 11 other MCP entries preserved), `output/claude-code-mcp/
tee-update.mcp` (byte-identical copy), and `output/claude-desktop-package/
tee-engine-0.30.1-a78-macos.mcpb` (959,226 bytes, 260 files, MCPB 2.1.2
schema-validated; UI install not yet done).

**The standing rule when you add an optional dependency:** it goes into
`docs/setup-fleet.md` *and* the `mcpb` target's printed reminder **in the same
commit as the extra itself**. Three lanes (pointcloud, windtunnel, flightdyn)
shipped without reaching that restore line and were quietly dead after every
upgrade.

## 7. The laws you inherit

Token dogma: never return full scene dumps; diffs over snapshots; batch over
chatter; text over pixels; small surface with progressive disclosure; fail loud
and cheap, with the exact fix in one short line.

Epistemic laws, each of which was paid for:
- **A measurement outranks a declaration.** A real Optitex file declared metres
  over inches; the control piece labelled `10"X10"` won.
- **A declaration is a claim; a measurement is evidence.** Applies to model
  registries, branch state, and licence metadata (JSBSim's wheel ships GPL-3
  files while PyPI declares LGPLv2+ — the gate reads file headers).
- **A branch you have not fetched is a declaration** — and unpushed work on the
  machine you are on is still part of the state.
- **A check that samples a grid is not a check.** `min_wall` passed a 0.600 mm
  web because it only sampled UV cell centres.
- **An unmanaged metric is not biased toward its author — it is simply unread.**
  The stale benchmark drifted *against* TEE by 3.6 points.
- **A measurement that is not pinned is not a measurement** (threaded cfMesh
  builds a different mesh every run).
- API facts from model weights are **banned** — a fix depending on a signature
  not present in the evidence must answer `confidence: needs_verification`.

Trust kernel (A43/A45): ONE capability model, **default deny**, taint-aware. The
read tier is open; side-effecting capabilities are granted per project and never
by TEE to itself. Escalations are requested by name through `registry.require`.
`place-order` is a reserved capability no config can ever grant — its absence is
the guard, so there is no tool to argue with. Code-exec is opt-in
(`--allow-code-exec`), currently **off**. Bridges bind localhost only: never
port-forward, never bind 0.0.0.0, never tunnel them off the machine.

## 8. State on handover (2026-09-10)

- Branch `claude/token-efficiency-engine-5jv1dj`, level with origin, **84
  uncommitted files** in the working tree — live in-flight work, mostly the
  OkongoSim reliability/texture campaign. Do not blow it away.
- Test suite last full run: **2,153 passed, 20 skipped, 141 deselected**.
- Open quality debt (A78): full AETHER-equivalent creation by the installed 27B
  is **unproven** and the composed visual benchmark **failed** — 95 mm where
  94 mm was asked, inward winding, unrealized materials, faceting. Guidance took
  the strict typed pilot from **0/6 to 6/6**, but did **not** reduce raw token
  totals (baseline 4,213 vs guided 5,536). There is no defensible savings
  multiple from that six-case pilot. Do not claim local-model parity, and do not
  score a replay of the finished AETHER scripts as independent local creation.
- Where the truth lives: `docs/PROGRESS.md` (the ledger — read at session start,
  update before session end), `docs/DECISIONS.md`, `CLAUDE_A*_SCRIPT.md` (plans
  of record), `docs/research/` (designs of record), `CLAUDE.md` (house rules).

## 9. How to behave here

Update `docs/PROGRESS.md` with real command output as evidence when you close
something, and commit. Never report that something worked unless you watched it
work. If an item fails, say plainly what happened and move to the next thing.
The owner is non-technical about the internals and explicitly wants plain
English, the work done for him, and to be asked only when a step genuinely needs
his hands.
````

## What "working" looks like

The incoming model connects, `tee_status` reports `rooted_at` pointing at the
folder holding the grants, and the lanes are listed. Lanes showing as
disconnected are normal — Fusion, Blender and Unreal connect only while those
applications are running with their bridge.

## The one failure worth recognising — and it is not hypothetical

`tee doctor --emit` (claude-code | claude-desktop | cursor | qwen-code |
opencode) writes its config as **`uv --directory server run tee serve …`**, not
as the venv interpreter directly. A bare `uv run` **syncs the environment to
`uv.lock` first**, and this project's engine extras (medimg, quant, solve,
extract, pdf, OCP, jsbsim, meshio and the rest) are installed *on top* of the
locked set with `uv pip install`. That is why every target in `server/Makefile`
passes `--no-sync`, and why the comment there calls it load-bearing rather than
tidy.

**It took opencode down on 2026-09-10.** The config was edited at 19:19 and
`opencode.log` recorded `message="server unavailable" key=tee type=local
status=failed` at 19:23:48; TEE had been answering normally at 13:26 the same
day. Measured with `uv sync --dry-run` against that exact command:

```
Would uninstall 112 packages
  - seamkiln==0.1.0.dev0   ← the lane itself
  - faster-whisper, highspy, jsbsim, meshio, pydicom, scipy, trimesh, …
```

Every launch asked uv to tear out 112 packages — slow enough to blow opencode's
30,000 ms timeout, and destructive whenever it did finish. The fix was to swap
only the launcher, keeping every argument after `serve`:

```json
"command": ["/Users/john/TokenEfficiencyEngine/server/.venv/bin/python",
            "-m", "tee.cli", "serve",
            "--adapter","blender","--adapter","partkiln",
            "--adapter","seamkiln","--adapter","fusion",
            "--project","/Users/john/TEE"]
```

After: initialize in **0.32 s**, 17 tools, 228 virtual capabilities,
`rooted_at.project_root = /Users/john/TEE` with its six grants intact — 0.54 s
end to end against a 30 s budget.

So prefer the direct-interpreter shape everywhere: it is what the Codex plugin
uses and what every smoke test in this document ran against. If you do use an
emitted config, check the fleet extras afterwards (`solve_backends`,
`med_backends`, `cad_probe`) rather than assuming. The emitter itself still
needs fixing — `--no-sync`, or the interpreter path — and until it is, an
emitted config is a loaded gun on this machine.

## After an update

Re-measure before re-briefing. `tee doctor` for the version and lanes,
`tee_call handoff {}` for project state, then correct the block. A brief whose
numbers were true a month ago teaches the incoming model to trust numbers that
are not.
