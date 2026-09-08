# Desktop update script — put the current TEE in Claude Desktop (for a non-technical owner)

Open Claude Code on the Mac, start a new conversation, and paste the block
below as one message. Claude does the work and explains it in plain English.
One step needs your hands — dragging the built file into Claude Desktop — and
it will stop and tell you when.

Use this whenever the extension is behind. The version moves fast: it went
0.23.0 → 0.30.0 in a day.

```
Update my Claude Desktop TEE extension to the current version. I am not
technical, so do all of it yourself, explain in plain English, and only stop
when you genuinely need my hands or my decision.

RULES that matter more than speed:
- Read the restore command out of THIS version's own Makefile. Do not use one
  you remember or find in an older document: the list of extras changes
  between versions, and a stale line fails on an extra that does not exist yet.
- Do not change the version, the manifest, or anything else in the repo. This
  is a build-and-install job, not a code change.
- If the suite fails, tell me what failed before building anything, and say
  whether it looks like my machine or a real defect.

STEP 1 - get the current code.
Find the TokenEfficiencyEngine folder (likely in my home folder), then:
  git checkout claude/token-efficiency-engine-5jv1dj
  git pull
Tell me which version it is now on (server/pyproject.toml) and roughly what
has changed since the version Claude Desktop currently runs - the CHANGELOG
headings are enough.

STEP 2 - install what the build needs, and prove the code is sound.
  cd server
  uv sync --extra extract --extra assets --extra physical --extra quant \
          --extra pdf --extra medimg --extra pointcloud --extra windtunnel \
          --extra solve --extra flightdyn
  uv run pytest -q
  make lint
The suite should be fully green. If a test about a solver, OpenSCAD, OpenFOAM
or a DCC fails, it is probably a missing engine on this machine rather than a
defect - say which you think it is and show me the failure rather than
carrying on quietly.

STEP 3 - build the bundle.
  make mcpb
It writes server/dist/tee-engine-<version>.mcpb. Then check the file ITSELF
rather than trusting the build log: open the zip, read manifest.json, and
confirm the version, that it serves blender, partkiln, seamkiln and fusion,
and that it declares 17 tools. Tell me those four facts.

STEP 4 - my hands.
Tell me the full path of the .mcpb file and stop. I will drag it into Claude
Desktop (Settings, Extensions) and tell you when it is installed.

STEP 5 - restore the fleet extras, which the install wipes.
Claude Desktop rebuilds its own environment from the lock file when it
installs, which silently removes the optional extras. Run `make mcpb` again
and read the REMINDER it prints, or read the same line in server/Makefile,
and run THAT command - it names the right extras for this version. Do not
reuse an older one.

STEP 6 - check it works, then tell me:
  - the version now installed
  - that TEE answers in Claude Desktop (ask it for its status in a new chat)
  - which lanes are connected, and which are simply not running - lanes showing
    as disconnected is NORMAL, they connect only when that application is open
  - anything you had to decide, or could not do
```

## Why the restore step exists

Installing an extension makes Claude Desktop rebuild its Python environment
from the lock file, which drops anything installed on top of it — including
every optional extra. Tools that need one then refuse with an install line
instead of working. The Makefile prints the correct command for the version
you just built; that list has grown (`windtunnel`, `flightdyn` and
`pointcloud` were all missing from it until A75–A77), which is exactly why the
script reads it fresh rather than from memory.

## What "working" looks like

TEE answers in Claude Desktop and reports its four lanes. Lanes listed as
disconnected are normal — Blender, Fusion and the rest connect only while
those applications are running.

## This has nothing to do with opencode

The `.mcpb` bundle is Claude Desktop only. opencode runs TEE straight from the
checkout — see [opencode-script.md](opencode-script.md), where updating is
`git pull`, `uv sync`, and restarting opencode.
