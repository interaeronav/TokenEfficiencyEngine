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
- **TEE sends no telemetry.** There is no analytics, crash reporting, or
  phone-home code path anywhere in the server or adapters; the only
  network traffic is what the bullets above name, each user-initiated.

## The web lane (A34)

`tee_web_lookup` is the one tool that reaches the open internet, and it
is read-only by construction:

- **SSRF**: http/https only, ports 80/443 (config-opt-in otherwise), no
  userinfo URLs. Hostnames are resolved first and every address checked
  against loopback / RFC-1918 / link-local (cloud metadata) / ULA /
  multicast / reserved ranges; the fetcher then connects to the exact
  validated IP (never re-resolving), which closes the DNS-rebinding
  race. Redirects are never auto-followed: each hop is re-validated,
  max 3. `[web] allow_local` is the explicit operator opt-out.
- **Prompt injection**: fetched content is untrusted data. The extractor
  strips hidden channels (script/style/template/comments, hidden and
  zero-size elements, zero-width and bidi controls); what remains is
  returned as a budgeted quote inside a fixed schema, labeled untrusted
  in the tool description itself. Nothing a page says can make TEE fetch
  another URL, call a tool, or touch config — an injection that
  "succeeds" has nothing to move. Server-side mitigation cannot make the
  *client* model immune to a quoted instruction it chooses to obey; TEE's
  ceiling is content that arrives inert, tiny, labeled, and cited — a
  strictly smaller residual than any whole-page fetch tool.
- **URL search**: `web_search` backends are operator configuration
  (a self-hosted SearXNG may legitimately be private; the Brave key
  is env-only) — trusted destinations, unlike model-supplied URLs,
  which always face the full guard at lookup time. Engine-page
  scraping is rejected as an anti-goal.
- **Copyright + etiquette**: short cited extracts only (no full-page
  copies stored beyond a private, TTL'd, local fetch cache with ETag
  revalidation); robots.txt and Crawl-delay honored via stdlib
  robotparser; per-host rate limit; honest versioned UA
  (`TEE-web/<version>`); 429/503 backoff honoring Retry-After; 5 MB text
  cap. Paywalls are never circumvented and streaming-platform ripping is
  an anti-goal enforced by tests.

## Reporting

TEE is pre-release. Security issues: open a GitHub issue on the
repository marked security, or contact the maintainer directly.
