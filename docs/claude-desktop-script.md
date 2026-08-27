# Claude Desktop script — finishing the Mac items (for a non-technical owner)

Open Claude Desktop (or Claude Code) on the Mac, start a new
conversation, and paste the block below as one message. Claude does the
work; it only asks when a step needs human hands (dragging a file,
approving a large download).

```
I need you to finish the remaining setup for my TokenEfficiencyEngine
project. I am not technical, so do everything yourself, explain progress
in plain English, and only ask me when a step genuinely needs my hands.

FIRST, get oriented:
1. Find the TokenEfficiencyEngine folder on this Mac (likely in my home
   folder; if you can't find it, clone it:
   git clone https://github.com/interaeronav/TokenEfficiencyEngine).
2. Inside it, run: git pull
3. Read docs/mac-handoff.md and docs/PROGRESS.md. The handoff file is
   the authoritative to-do list, with rules and proof requirements. If
   anything below disagrees with it, the handoff file wins.

THEN work these items in this order (quick wins first):

A. Dropbox sync (30 seconds): copy knowledge-base/manifest.json and
   knowledge-base/INDEX.md into my Dropbox folder at
   "02 Okongo Oneleiwa Project/12 Expert Knowledge Base/", replacing
   the two old ones. Verify afterwards that the copied files are
   byte-identical to the ones in the repo.

B. OkongoSim knowledge-base hookup: the OkongoSim project is at
   /Users/john/OkongoSim (search for it if not there). Follow section 1
   of docs/mac-handoff.md exactly: add the [kb] section to its
   .tee/config.toml pointing at the TokenEfficiencyEngine
   knowledge-base folder, add docs/tee-kb.md there, commit both. Then
   prove it works: ask the knowledge base one question (kb_search for a
   paving specification) and show me the cited answer.

C. Install checks: build the installers with "make dist" in the server
   folder, then walk me through the two 1-minute manual steps
   one at a time, in plain words:
   - dragging tee-engine-0.1.0.mcpb into Claude Desktop's settings
   - putting TeeToolset-0.1.0.zip into the Unreal project's Plugins
   After each, verify it actually works and show me the proof.

D. Voxkiln (the 3D generator): follow section 2 of docs/mac-handoff.md.
   IMPORTANT: before downloading the ~15 GB of model weights, tell me
   how much disk space I have free and ask me to confirm. Then do the
   first generation, the determinism check, and the benchmark battery.

E. If time and disk allow, continue with sections 4 and 5 of the
   handoff (GPU lanes, audio check, Unreal physics). Ask me before any
   other large download.

RULES (also in the handoff file):
- Work on the git branch claude/token-efficiency-engine-5jv1dj only.
- After each finished item, update docs/PROGRESS.md with the real
  command output as evidence, commit, and push.
- Never tell me something worked unless you actually saw it work.
- If an item fails, tell me simply what happened and move to the next
  one rather than getting stuck.
- At the end, give me a short plain-English summary: what's done,
  what's left, and whether anything needs to be bought/installed.
```

What to expect while it runs:

- Item C has the only two hands-on moments: dragging one file into
  Claude Desktop's settings window, and dropping one folder into the
  Unreal project. Claude talks you through each, one at a time.
- Item D downloads ~15 GB of model weights. Claude checks disk space
  and asks first; "skip for now" is a fine answer and everything else
  still completes.
- If Claude ever seems lost mid-run, say: "read docs/mac-handoff.md
  again and continue from the next unfinished item".
