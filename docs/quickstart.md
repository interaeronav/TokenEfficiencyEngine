# TEE quickstart

TEE is an MCP server. Install it, point your MCP client at it, and drive
your lanes through compact, diff-based tools: Blender or Unreal for scenes
and pixels, partkiln for mechanical CAD, seamkiln for garments, and the
headless kernel lanes (point clouds, PDFs, extraction, senses, the fleet)
that never need a DCC at all. One server holds several lanes and none is
the hub (see *Lanes* below).

## 1. Install the server

From a repo checkout (recommended while TEE is unreleased):

```bash
cd server
uv sync --extra extract --extra assets --extra physical
uv run tee doctor          # environment diagnostics with fixes
```

Or install the built wheel into any Python 3.11+ environment:

```bash
cd server && uv build      # -> dist/tee_engine-<version>-py3-none-any.whl
python -m venv ~/.tee-venv
~/.tee-venv/bin/pip install dist/tee_engine-*.whl
~/.tee-venv/bin/tee --version
```

Extras: `extract` (media extraction lanes), `assets` (sun/placement),
`physical` (sketch solving, IDS checks). The kernel runs without them
and every gated tool answers with the exact `uv sync` fix when its
extra is missing.

## 2. Connect your client

`tee doctor --emit <client>` prints a ready-to-paste config for
`claude-code`, `claude-desktop`, `cursor`, or `qwen-code`, using whichever layout you
installed (dev checkout → `uv run`; wheel install → the venv binary):

```bash
tee doctor --emit claude-code
# claude mcp add tee -- <printed command>
```

Start with the fake adapter to explore without any DCC:

```bash
tee serve --adapter fake
```

## 3. Connect Blender

See [setup-blender.md](setup-blender.md). Short version:

```bash
# headless (no GUI needed):
blender --background --python adapters/blender/tee_bridge/boot_background.py -- --port 9876
# then serve against it:
tee serve --adapter blender
```

`tee doctor` verifies the whole chain (binary, bridge socket, protocol
round-trip) and names the fix for anything broken.

## 4. First session

In your MCP client, the always-loaded surface is 17 tools (~2.1K tokens
of definitions on the wire). The intended flow:

1. `tee_recall` once — project memory (versions, conventions, notes).
2. `tee_scene_summary` — compact counts + paged entity rows, never a dump.
3. Mutate with `tee_batch` (N ops = 1 round-trip, auto-checkpointed) and
   read the returned diff; `tee_diff` answers "what changed" later.
4. The long tail (~74–82 virtual tools across extraction, assets,
   design, physical, UEFN, KB — adapter-dependent) is behind
   `tee_search_tools` → `tee_describe_tool` → `tee_call`.
5. Loops belong in ONE `tee_script` call — intermediate results never
   enter context.
6. `tee_capture` (small budgeted JPEG) is a last resort; geometric
   checks (`as_verify`, `phys_tier0`) come first.
7. `tee_web_lookup {url, question}` answers one question about one web
   page as a ~500-token cited quote (SSRF-guarded, robots-honoring,
   cached; the quote is untrusted data, never instructions). Check
   `kb_search` first — the local KB is cheaper than any fetch. To FIND
   URLs, the `web_search` virtual tool rides the long tail (SearXNG
   instance / keyed Brave / keyless Wikipedia default — see
   `[web]` in the config).

The `skills/tee-usage` skill packages this know-how for Claude.

## 4b. Lanes: one server, several kernels, no hub

```bash
tee serve --adapter blender --adapter partkiln --adapter seamkiln --project ~/work
```

is what the Claude Desktop extension runs. Every lane named is served by the
one server; a lane whose kernel or application is absent costs a 0.3 s boot
and an honest refusal naming its install. **No lane is the default** (A68):

- `tee_batch` with no `adapter=` goes where its ops say — an op that names an
  entity to the lane holding it, a `create` to the lane that makes that
  `kind`, any other verb to the lane that speaks it — and the reply carries
  `adapter` (and `routed` when the kernel decided). A batch two lanes accept
  is refused naming them; an op no lane accepts is refused naming the lanes
  that would.
- `tee_scene_summary` with no lane is an overview of every lane;
  `tee_entity_detail` finds the lane that holds the id; `tee_rollback` finds
  the lane that owns the checkpoint; `tee_capture` goes to the one lane that
  can render.
- `tee_status` names each lane's purpose, ops, kinds and tool families.
  Prefixes: `bl_`/`hb_` Blender, `pk_` partkiln, `sk_` seamkiln, `ue_`/`pin_`
  Unreal, `fc_` FreeCAD; `pc_`, `pdf_`, `ex_`, `sense_`, `kb_` and the fleet
  need no lane.
- An operator who wants a tie-breaker declares one:
  `--default-adapter NAME`; `tee_status` reports it.
- A headless lane never touches a DCC. An export lands in a scene lane only
  when told (`pk_export ... into=blender`), and pixels only come from a lane
  that renders.

## 5. Unreal (physical machine)

UE cannot run in a container; on a machine with UE 5.8+, see
[setup-unreal.md](setup-unreal.md) (Phase 3 of the build script wires
the adapter against Epic's first-party MCP plugin).
