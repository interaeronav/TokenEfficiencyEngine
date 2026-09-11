# Claude review passed — installation checks clarified

Update: TEE-20260910-A79-A80-01, revision 1.  
Acknowledges: TEE-20260910T211323Z-CLAUDE-08, received / review PASS.  
Frozen manifest: `1846119f418092dee3a3b76c39d9a920be21823c49bb3e1378a75773ccb5b469`.

Claude's independent candidate review is complete with no blocking defect.
Installation and both actual-client acceptance receipts remain pending. This
note clarifies the existing rollout checks; the reviewed installer, source,
frozen manifest, execution packet and accepted protocol are unchanged. No new
candidate or acknowledgment-only review cycle is needed.

## First check after installation: the selected project

Install `tee-engine-0.30.1-a79-a80-local.mcpb` through Claude Desktop, and select
the extension's project folder explicitly as:

**`/Users/john/TokenEfficiencyEngine`**, with TEE enabled.

The existing selection is `TokenEfficiencyEngine-a71`; the bundle's default is
`${HOME}/TEE`. Neither selects the intended main namespace. Preserve the old
namespace in place; do not merge its data or copy grants between projects.

After reconnecting Claude, make `tee_status` the first live verification call.
Check `rooted_at.project_root`, `llm_profile` and `rooted_at.granted`: they must
show the main project, `qmax`, and the existing sole extra `call-paid-engine`
grant, with `code_exec_enabled: false`. Verify the preserved pin from the main
profile state as the execution packet requires. If a value differs, record the
observed mismatch and resolve the selected project/profile within existing
authorization before proceeding to feature acceptance. Do not grant permissions
in a different namespace to make the check pass.

Then complete all source/artifact, dependency, core-schema, learning and lesson
checks in `execution.md`, and return the actual client receipt. Reconnect and
verify Codex separately. A matching tool count cannot establish a matching
project or model selection. Existing QMAX/paid-engine authorization persists;
no paid inference is needed to verify it. Refresh the private backup and check
for active work before cutover as already specified.

## Reproducing the canonical core-schema checksum

The frozen `contract.core_schema_sha256` is computed from the **entire list** of
core-tool objects in `evidence/core-schemas.json`, sorted by tool `name`. Include
every field present; do not reduce each object to its name, description and
input schema. The original objects came from MCP tool
`model_dump(by_alias=True, exclude_none=True)`.

Serialize that sorted list with Python `json.dumps`, `sort_keys=True`,
`ensure_ascii=True`, `separators=(",", ":")`; encode as UTF-8 with **no trailing
newline**, then compute lowercase SHA-256. No other normalization is performed.

```python
import hashlib
import json
from pathlib import Path

tools = json.loads(Path("evidence/core-schemas.json").read_text())
assert len({tool["name"] for tool in tools}) == len(tools) == 17
encoded = json.dumps(
    sorted(tools, key=lambda tool: tool["name"]),
    sort_keys=True,
    ensure_ascii=True,
    separators=(",", ":"),
).encode("utf-8")
print(hashlib.sha256(encoded).hexdigest())
```

Verified result:
`95373e1c2d9e171476c90c475d7046772bdaaa345990a4e3c4cf605730e32963`.

The ordinary SHA-256 of the formatted file's bytes is separately:
`60d31b76634865ea024a2d37d4e1e64c1297386c69bd28540bb5853a177f5e8c`.
That file hash includes its formatting and final newline. Claude independently
verified the file hash and reconstructed equivalent schemas from the candidate;
this clarification also makes the existing canonical checksum reproducible.

The candidate review does not itself perform installation, project selection
or a client restart. The attached receipt's recommendation is review evidence;
the owner-directed application steps remain those in the reviewed packet.
