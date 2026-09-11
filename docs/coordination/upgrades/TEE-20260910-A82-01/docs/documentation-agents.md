# Documentation with Cline and Aider

TEE can prepare documentation work for either Cline or Aider in any project
selected by the connecting client. It copies the chosen source files and
documentation targets, runs the selected worker as a job, and presents a diff
before applying changes to the original project.

Start with `tee_call(name="doc_status", args={})`. This reports the two optional
workers, the selected TEE model, and whether this project permits execution.
The long tail adds five tools; the always-loaded MCP contract remains 17.

## One documentation task

Prepare a small, explicit set of evidence and target files. Paths are relative
to the connected project; existing uncommitted files are included as they are.

```json
{
  "name": "doc_prepare",
  "args": {
    "inputs": ["src/api.py", "tests/test_api.py"],
    "outputs": ["README.md", "docs/api.md"],
    "instruction": "Document the public API and add a usage example supported by the source and tests. Mark anything not demonstrated as unverified."
  }
}
```

Use the returned `run_id` in `doc_run`:

```json
{"name":"doc_run","args":{"run_id":"<returned ID>","backend":"aider","timeout_s":300}}
```

Choose `"cline"` for the other worker. Poll the returned job through `tee_job`;
cancel through the same job interface when needed. A successful worker result
reports proposed changes and `applied: false`. Review them with:

```json
{"name":"doc_diff","args":{"run_id":"<returned ID>","max_chars":12000}}
```

The result names each changed file, its hash and a bounded patch. If `truncated`
is true, inspect the remaining staged files locally before approving the whole
checksum. Check statements and examples against their supplied evidence; the
worker's completion status does not establish documentation correctness.

Apply the exact reviewed version:

```json
{"name":"doc_apply","args":{"run_id":"<returned ID>","review_sha256":"<checksum returned by doc_diff>"}}
```

TEE refuses if any original input/target changed after preparation, or if the
staged files changed after review. It retains original files in a per-run
backup and attempts to restore them if application fails. A subsequent user
edit is preserved rather than overwritten during recovery. A client can repeat
this workflow whenever a project change needs documentation.

## Execution permission and model selection

The worker process requires the explicit **`run-doc-agent`** capability. Cline
and Aider are coding agents capable of executing host commands; a staging
directory is not an operating-system sandbox. Cline shell commands are denied
by its worker configuration, and Aider's automatic lint/test/commit steps are
disabled. These controls do not turn either agent into a sandbox.

An owner enables this capability in the selected project's `.tee/config.toml`,
preserving other grants. For the main TEE project, the proposed grant list is:

```toml
[trust]
grants = ["call-paid-engine", "run-doc-agent"]
```

Implementation and installation do not add this grant. The existing paid-engine
grant by itself does not permit running an external coding agent. TEE rechecks
execution and model permissions when a queued job starts, and refuses tainted
execution. Its general `code_exec_enabled` setting stays independent.

When upgrading existing clients, reconnect **both** to the new runtime before
adding the approved capability. An older TEE version does not recognize its
name and would reject the changed grant configuration. The coordinator's
update packet orders these steps and preserves the old grant list until then.

The worker uses TEE's selected profile, including QMAX when pinned. Version 1
supports an explicit loopback OpenAI-compatible `/v1` endpoint. A local proxy
may still represent a paid model: QMAX's paid classification and paid grant
are preserved. There is no automatic provider fallback, pin change, server
startup or weight download. Profiles requiring unsupported model adapters or a
direct remote endpoint are refused. An explicit `TEE_DOCAGENT_API_KEY` in the
TEE process environment can supply a key to the isolated worker; it is never
placed in command arguments or status output.

Child home/config/cache directories are private to the task. Ambient API keys,
project agent hooks and user CLI configuration are not inherited. Cline's own
completion usage, when available, is labelled worker-reported. Aider usage is
unknown in this integration. External worker calls are **not included in TEE's
internal model token/spend meter**; an unknown count is not zero cost.

## Scope and installed workers

Each task allows at most 64 explicitly named UTF-8 files and 1 MiB of initial
content. Documentation outputs may use `.md`, `.rst`, `.txt` or `.adoc`. Source
files remain evidence inputs. Traversal, symbolic/hard links, hidden state,
credentials, agent instructions and upgrade-coordination records are excluded.
Unexpected worker files or changes to input-only files fail validation.

Worker logs are private and bounded to 1 MiB. The total job deadline is at most
900 seconds. Cancellation stops the owned process group; deliberately detached
processes require stronger OS isolation. Tasks, logs and backups live under
the selected project's `.tee/docagents/` and are never part of an update payload.
No automatic Git commit or publication is performed.

On this Mac the verified optional installations are separate from TEE's shared
Python environment:

- Cline 3.0.61: `~/.local/share/tee/docagents/cline-3.0.61/node_modules/.bin/cline`;
  Node.js 22 or newer for npm installation. On this Mac npm links the managed
  command directly to the native arm64 executable, which also runs without
  Node on the worker's PATH.
- Aider 0.86.2: `~/.local/share/tee/docagents/aider-0.86.2/bin/aider`;
  its own Python 3.11 environment. Package constraints allow Python 3.10–3.12.

`doc_status` reads availability and managed package metadata without executing
a worker. An arbitrary version found on PATH is reported but refused for
execution until its interface is verified. For another machine, install the
same pinned versions in those private locations; do not add Aider's dependencies
to TEE's shared runtime.

```sh
python3.11 -m venv "$HOME/.local/share/tee/docagents/aider-0.86.2"
uv pip install --python "$HOME/.local/share/tee/docagents/aider-0.86.2/bin/python" 'aider-chat==0.86.2'
npm install --prefix "$HOME/.local/share/tee/docagents/cline-3.0.61" --save-exact cline@3.0.61
```

Primary interface sources and measured evidence are in
[research 82](research/82-documentation-agents.md). Existing learning hooks
record execution outcomes; they do not invent labels for prose quality.
