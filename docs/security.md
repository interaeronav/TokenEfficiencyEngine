# Security notes

TEE's threat model is simple and worth stating plainly: **the DCC-side
sockets execute code and have no authentication.** Everything else
follows from that.

## The floor (decision A7)

- **Localhost binds only.** The Blender bridge (:9876), Epic's UE MCP
  (:8000), and UEFN's MCP (:8000) all listen on 127.0.0.1 and speak
  unauthenticated protocols that ultimately run Python or editor
  commands. **Never port-forward them, never bind them to 0.0.0.0,
  never tunnel them off the machine.** Anyone who can reach the socket
  can run code as you.
- **Code-exec is opt-in and screened.** `bl_execute_python` exists only
  when served with `--allow-code-exec` (or `[server] allow_code_exec` in
  `.tee/config.toml`). Every snippet passes the version firewall and a
  denylist (`wm.quit_blender`, factory resets, `sys.exit`) before
  execution, and typed batches auto-checkpoint so failures roll back.
  The typed tool surface — batches, tier-2 ops, sims — adds no
  capability beyond itself and is not gated.
- **The script lane is not code-exec.** `tee_script` runs an
  AST-whitelisted interpreter over the same typed tools (no imports, no
  attribute access, hard budgets); it deliberately adds no new
  capability, which is why it is always on.
- **Isolation is the mitigation, not sandboxing.** Official Blender/Epic
  docs say the same: run DCC automation on machines/VMs you trust with
  the project data on them.

## Data-handling posture

- Media never leaves the machine by default: extraction is
  deterministic-local; the in-band VLM path sends only the budgeted
  tiles you explicitly request.
- Asset backends are contacted read-only over HTTPS; downloads are
  license-gated fail-closed, checksums verified where published, and
  archives checked against zip-slip/path traversal before a byte is
  written.
- Hosted generation (Tripo/Meshy) and the public Fortnite Data API are
  opt-in, keyed via environment variables, and cost-confirmed before
  any paid call.
- Verse digests are parsed from the local UEFN install and never
  redistributed (they are Epic-copyrighted); a repo test enforces that
  no digest text is bundled.
- `.tee/` holds project memory, checkpoints, and caches in plain files —
  treat it as project data (it is gitignored by default; commit nothing
  from it).

## Reporting

TEE is pre-release. Security issues: open a GitHub issue on the
repository marked security, or contact the maintainer directly.
