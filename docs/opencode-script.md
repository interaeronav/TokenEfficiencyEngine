# opencode script — point opencode at TEE (for a non-technical owner)

Open Claude Code (or Claude Desktop) on the Mac, start a new conversation,
and paste the block below as one message. Claude does the work and explains
it in plain English; it only stops if something genuinely needs a decision.

Nothing here touches your Fusion, Blender or project files. It updates the
TEE checkout and adds one entry to opencode's settings.

```
Set up opencode on this Mac to use TEE. I am not technical, so do all of it
yourself, explain what you are doing in plain English, and only ask me when
something genuinely needs my decision.

RULES, which matter more than speed:
- Never overwrite my opencode config. If one exists, back it up first and
  MERGE the new entry in, leaving every other setting and MCP server alone.
- Never invent a path. If a folder is not where you expect, look for it, and
  if you still cannot find it, stop and ask me.
- The .mcpb extension bundles are for Claude Desktop only. They have no role
  here: opencode runs TEE straight from the checkout.

STEP 1 - find TEE and bring it up to date.
Find the TokenEfficiencyEngine folder (likely in my home folder). Then:
  git checkout claude/token-efficiency-engine-5jv1dj
  git pull
  cd server
  uv sync --extra extract --extra assets --extra physical
  uv run tee --version
Tell me the version it prints. If `git pull` reports local changes that would
be overwritten, stop and show me what they are rather than discarding them.

STEP 2 - work out the two paths the config needs, and CHECK they exist.
  a) the server folder: the `server` directory inside the checkout.
  b) my project root: the folder whose `.tee/config.toml` holds my grants.
     Look for `~/TEE/.tee/config.toml` first. If it is somewhere else, find
     the file rather than guessing, and tell me where it was.
This second path is the one that goes wrong quietly, so do not skip the check.

STEP 3 - write the opencode config.
First try TEE's own emitter, which knows opencode's format:
  uv run tee doctor --emit opencode \
    --emit-adapter blender --emit-adapter partkiln \
    --emit-adapter seamkiln --emit-adapter fusion \
    --emit-adapter unreal \
    --emit-project <the project root from step 2>
If that command errors with "unknown client", this checkout predates the
emitter - in that case build the same JSON yourself, in opencode's shape:
top-level key `mcp`, entry named `tee`, `"type": "local"`, `"enabled": true`,
and command plus every argument as ONE flat array. It is NOT the `mcpServers`
shape other clients use; that shape silently does nothing in opencode.

Merge it into `~/.config/opencode/opencode.json`, creating the folder if
needed, backing up any existing file to `.bak` first, and preserving every
other key. If the existing file has a syntax error, stop and show me - do not
rewrite it.

STEP 4 - prove it actually works, before telling me it does.
  a) Run the exact command from the config by hand and confirm the server
     starts and answers - it should list 17 tools. Then stop it.
  b) Quit opencode completely and start it again, so it picks up the change.
  c) In opencode, ask for TEE's status. Check the reply's `rooted_at` shows
     the project root from step 2. If it shows anything else, the `--project`
     argument did not take: fix it and repeat.
  d) Confirm the five lanes appear: blender, partkiln, seamkiln, fusion,
     unreal. Any of them showing as disconnected is FINE and expected - they
     connect only when that application or kernel is running.

STEP 5 - tell me, in plain English:
  - the TEE version now installed
  - where the config was written, and whether anything was backed up
  - what `rooted_at` says
  - which lanes are connected and which are simply not running
  - anything you had to decide or could not do
```

## What "working" looks like

TEE answers in opencode, and its status reports `rooted_at` pointing at the
folder holding your grants. Lanes listed as disconnected are normal — Fusion,
Blender and the rest connect only while those applications are running.

## The one failure worth recognising

If TEE answers questions but refuses everything that would *change* anything,
the `--project` path is wrong. TEE then boots from whatever folder opencode
started in, finds no grants file there, and quietly keeps only its read-only
tools. Research doc 66 recorded this the first time it happened; it reads as
"TEE denies access to all the tools". The fix is step 2 and step 4c, not a
permissions change — TEE never grants itself.

## After an update

Updating TEE for opencode is `git pull`, then `uv sync`, then quit and reopen
opencode so it restarts the server. The config itself only needs revisiting if
the checkout moves.
