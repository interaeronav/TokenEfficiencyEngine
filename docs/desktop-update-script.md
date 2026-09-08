# Claude Desktop script — updating TEE on the Mac (for a non-technical owner)

[`claude-desktop-script.md`](claude-desktop-script.md) is the **first-time**
setup. This is the one to use **every time after that**, when a new version of
TEE is ready and you want the Claude Desktop extension to be running it.

It exists because updating has one trap that is free to avoid and expensive to
miss: **installing a new bundle silently deletes the fleet extras.** Claude
Desktop provisions the extension with `uv sync`, which rebuilds its Python
environment strictly from the lock file and discards anything installed on top
of it — and the extras are installed on top *by design*, because keeping them
out is what holds the base install to 586 MB instead of 2.2 GB.

The failure is quiet rather than loud. Nothing errors. The tools just start
reporting `{"installed": false}`, which reads as *you never set this up*
rather than *your upgrade removed it* — so you go looking for a mistake you
never made. Measured three times running (0.9.0 → 0.10.0, → 0.11.0, → 0.12.0),
each upgrade dropped the environment from about 1.1 GB back to 34 MB.

Open Claude Desktop (or Claude Code) on the Mac, start a new conversation, and
paste the block below as one message.

```
I need you to update my TokenEfficiencyEngine install in Claude Desktop to the
current version. I am not technical, so do everything yourself, explain
progress in plain English, and only ask me when a step genuinely needs my
hands.

FIRST, get oriented:
1. The repo is at /Users/john/TokenEfficiencyEngine (search for it if it has
   moved). Work there.
2. Run: git pull
3. Read docs/setup-fleet.md. Note the version in server/pyproject.toml — that
   is the version we are installing. Tell me what it is, and what is installed
   right now, before we change anything.

THEN work these steps in order. Do not skip step 4; it is the whole reason
this script exists.

1. BUILD the bundle:
       cd server && make mcpb
   It prints the file it wrote, e.g. dist/tee-engine-<version>.mcpb. Tell me
   that filename. (Use `make mcpb`, not `make dist` — `dist` also repackages
   the Blender and Unreal add-ons, which an update to Claude Desktop does not
   need.)

2. RECORD what is installed now, BEFORE I replace it:
       bash docs/research/74-evidence/mac-upgrade-check.sh
   Keep the output. Section B lists the extras that must still be there when
   we finish, reading the EXTENSION's environment — the one this update is
   about to rebuild. It also prints, ready to paste, the completeness command
   step 5 needs, with the group list already filled in. Keep that line.

3. HANDS-ON, and the only one in this script. I drag the bundle into Claude
   Desktop. Talk me through it one step at a time, and wait for me:
     - open Claude Desktop → Settings → Extensions
     - drag in the .mcpb file from step 1
     - tell me what version it now shows, so we both see it took
     - quit Claude Desktop completely and reopen it
   Do not continue until I confirm it is done.

4. RESTORE the extras. Installing the bundle just deleted them.

   Do NOT retype a list of groups out of any document. Every hand-typed copy
   of that list in this repo has been stale at some point, and at least one is
   stale today. Derive it from the version that is actually installed:

       EXTPY="$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/python"

       "$EXTPY" - <<'EOF'
       from importlib.util import find_spec
       from tee.kernel.extras import WITNESS, NOT_IN_TEE_VENV

       missing = [g for g, w in sorted(WITNESS.items())
                  if not find_spec(w) and g not in NOT_IN_TEE_VENV]
       print(" ".join("'tee-engine[%s]'" % g for g in missing) or "nothing missing")
       EOF

   That reads the map out of the bundle you just installed, so it cannot go
   out of date the way a written list does. Install exactly what it prints:

       uv pip install --python "$EXTPY" <the groups it printed>

   Two rules about that command, both of which cost something to learn:
     - Use the NAME form, 'tee-engine[group]'. It works even though tee-engine
       is not published on PyPI, because the bundle you just installed is
       already in that environment — only the extra's dependencies get added.
     - NEVER use the path form '.[group]'. It uninstalls the extension's own
       copy of tee-engine and repoints it at the repo, which breaks the
       extension. It looks like it is doing the same thing. It is not.

   If a group is refused with "does not have an extra named <group>", the
   order got reversed: that error means the tee-engine metadata in the
   environment is OLDER than the group you are asking for. Install the new
   bundle first (step 3), then restore. Never the other way round.

5. VERIFY, and be stricter than the obvious check. Step 4 proves each group
   can be IMPORTED, not that it is COMPLETE — a group can pass its witness
   import while other packages it needs are still missing. Ask for the real
   answer with a dry run, which installs nothing. Pass EVERY group, not just
   the ones that were missing — the check in step 2 printed this command with
   the list already filled in, so use that rather than typing groups:

       uv pip install --dry-run --python "$EXTPY" \
         'tee-engine[assets]' 'tee-engine[extract]' 'tee-engine[flightdyn]' \
         'tee-engine[medimg]' 'tee-engine[pdf]' 'tee-engine[pointcloud]' \
         'tee-engine[quant]' 'tee-engine[solve]' 'tee-engine[windtunnel]'

   "Would install N packages" means the restore is NOT finished — run it for
   real without --dry-run, then dry-run again. Only "Would make no changes"
   means done.

   Then confirm the product agrees, using the EXTENSION's own copy:
       "$HOME/Library/Application Support/Claude/Claude Extensions/local.mcpb.interaeronav.token-efficiency-engine/.venv/bin/tee" doctor

   And finally ask TEE one real question in Claude Desktop that uses a lane
   you just restored, and show me the answer. An install log saying
   "installed" is not proof. An answer is.

6. REPORT in plain English: the old version, the new version, which extras
   were deleted and restored, and anything still missing or broken.

RULES:
- Work on the git branch claude/token-efficiency-engine-5jv1dj only.
- Never tell me something worked unless you actually saw it work.
- If a step fails, tell me plainly what happened and carry on with the next
  one rather than getting stuck.
- Nothing in this script downloads model weights or anything large. If
  something starts to, stop and ask me first.
```

## What to expect while it runs

- **Step 3 is the only hands-on moment** — one drag, then quit and reopen
  Claude Desktop. Everything else Claude does itself.
- **Step 4 downloads a few hundred MB** of ordinary Python packages, not model
  weights. It takes a minute or two on a normal connection.
- **`cad` will always show as missing, and that is correct.** CadQuery lives in
  its own sidecar at `~/TEE/.tee/sidecars/cad`, which an update never touches.
  The script already excludes it; if some other list tells you to reinstall it
  into the extension, that list is wrong.
- If Claude seems lost mid-run, say: *"re-read docs/desktop-update-script.md
  and continue from the next unfinished step."*

## Why the script derives the list instead of printing one

Because the written lists keep going stale, and each time they do, a lane
comes back silently half-installed.

`docs/setup-fleet.md` carried five groups from 0.10.0 until 2026-09-08, by
which time three more lanes had shipped their own extra — `pointcloud` (A67),
`windtunnel` (A72) and `flightdyn` (A75). A restore run from that list would
have brought back everything it named and still left `pc_*` and `fd_*`
refusing on every call, with nothing saying why.

That was fixed. It is also, as of this writing, **still happening**: both the
list in `setup-fleet.md` and the reminder printed by `make mcpb` name eight
groups, and the real number is nine. `assets` is missing from both.

The measured consequence on this machine, 2026-09-08: the `assets` group
passes its witness import (`imagehash` is there) while `astral` — the library
behind sun azimuth and elevation for a GPS datum and a timestamp — is not
installed at all. One package short out of 114, and the gap traces exactly to
the group that never reached the restore line. Nothing reported it, because
the witness said the group was present.

Hence the two rules baked into the script above: **derive the group list from
the installed package, and verify completeness with a dry run rather than with
the witness import.** A witness proves a group is reachable. It does not prove
it is whole.
