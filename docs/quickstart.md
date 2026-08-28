# TEE quickstart

TEE is an MCP server. Install it, point your MCP client at it, connect a
DCC (Blender today; Unreal on machines with UE 5.8+), and drive the
scene through compact, diff-based tools.

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
   `kb_search` first — the local KB is cheaper than any fetch.

The `skills/tee-usage` skill packages this know-how for Claude.

## 5. Unreal (physical machine)

UE cannot run in a container; on a machine with UE 5.8+, see
[setup-unreal.md](setup-unreal.md) (Phase 3 of the build script wires
the adapter against Epic's first-party MCP plugin).
