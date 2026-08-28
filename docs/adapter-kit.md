# Adapter kit — bring your own DCC to TEE (A37 P3)

An adapter is the seam between TEE's kernel and one tool with mutable
state (a DCC, a CAD package, a simulator). You implement **seven
synchronous methods**; the kernel supplies everything token-shaped on
top: automatic checkpoints, diffs, compact scene summaries with paging,
change tracking (`tee_diff`), budgeted capture, async jobs, and the
meta-tool surface. The contract is small on purpose — and it ships as a
runnable test suite, so "done" is a green pytest run, not a review.

**Already have an MCP server for your tool?** You may not need an
adapter: the [Gateway](setup-gateway.md) fronts any MCP stdio server
through TEE's meta-tools with budgets and a drift firewall. Build a
native adapter when you want TEE's *state* semantics — checkpoints,
diffs, the scene cache — which no fronted server provides.

## The shape of the seam

Batches of **typed operations** come in; **diffs** go out:

```python
[{"op": "create", "kind": "object", "name": "wall_a", "props": {...}},
 {"op": "set",    "id": "e7", "props": {"height_m": 2.4}},
 {"op": "delete", "id": "e9"}]
```

Rules the whole product stands on (each is enforced by a contract test):

1. **Diffs over dumps.** `execute()` reports what changed — created /
   modified / deleted ids plus compact per-id details. Never the world.
2. **Stable ids.** An entity keeps its id for the DCC session (Blender
   uses `session_uid`; Unreal the object path). Everything keys on it.
3. **Fail loud and cheap.** Any failure raises
   `TeeError(code, message, fix=...)` — one short structured answer
   naming the exact fix. No stack-trace novels, no silent skips.
4. **Compact rows.** `Entity.concise()` is identity only; scalar facts
   ride `Entity.summary` (bounds, counts, flags — never geometry).
5. **Budgets are law.** `capture()` returns JPEG bytes under
   `max_bytes`, or refuses with a structured error.

## The seven methods

Copy this skeleton (types from `tee.kernel.adapter`):

```python
from tee.kernel.adapter import AdapterInfo, Diff, Entity
from tee.kernel.errors import TeeError


class MyAdapter:
    """Speak to your tool however it wants (RPC, pipe, in-process) -
    the kernel only sees these seven methods."""

    def info(self) -> AdapterInfo:
        # id: short slug; connected: is the tool reachable NOW
        return AdapterInfo(id="mytool", product="MyTool", version="1.0",
                           connected=True)

    def probe(self) -> bool:
        # cheap liveness; called often; must never hang
        return True

    def list_entities(self) -> list[Entity]:
        # full listing, used ONLY for cache (re)sync - the model never
        # sees it raw. Return copies, not live references.
        ...

    def execute(self, batch: list[dict]) -> Diff:
        # apply ops in order; build the Diff as you go:
        #   diff.created/modified/deleted: ids
        #   diff.details[id]: compact change info (the model reads this)
        #   diff.upserts: created/modified Entity objects (cache-internal,
        #                 never serialized to the model)
        # Unknown op / unknown id: raise TeeError with the fix.
        # Do not mutate the caller's op dicts (checkpoint replay reuses them).
        ...

    def snapshot(self, label: str) -> dict:
        # opaque checkpoint payload; keep it small or spill to disk and
        # return the pointer. restore(payload) must round-trip it.
        ...

    def restore(self, payload: dict) -> None:
        ...

    def capture(self, view: str, max_bytes: int) -> bytes:
        # JPEG under max_bytes, or raise TeeError(code, msg, fix=...)
        raise TeeError("capture_unsupported", "MyTool has no viewport.",
                       fix="Use entity summaries; there is nothing to render.")
```

`FakeAdapter` in `tee/kernel/adapter.py` is the annotated reference
implementation of exactly these semantics (~120 lines); read it once
before writing your own. Two of its behaviors are *reference niceties*,
not contract: netting a same-batch create+delete to an empty diff, and
extra adapter-specific ops (`assign_material`) — add your own ops
freely; only the three core ops and the failure shapes are demanded.

## Prove it: the packaged contract suite

```python
# tests/test_my_adapter.py  (in YOUR repo)
from tee.kernel.contract import AdapterContract
from my_adapter import MyAdapter


class TestMyAdapterContract(AdapterContract):
    def make_adapter(self):
        return MyAdapter()   # a FRESH, empty-state adapter per test
```

`pytest tests/test_my_adapter.py` runs eleven tests: identity shape,
probe, the create/set/delete round-trip, diff-not-dump, both rule-6
failure shapes, caller-batch immutability, id stability, concise-row
compactness, snapshot/restore, and the capture budget. Green = the
kernel's real expectations hold; TEE's own adapters run the same class
in-tree, so the suite cannot drift from the kernel.

## Wire it in

```python
from tee.app import TeeApp

app = TeeApp({"mytool": MyAdapter()}, project_root=".")
```

That alone gives every kernel tool on your adapter: `tee_batch`
(auto-checkpointed), `tee_scene_summary` (cached, paged, columnar),
`tee_diff`, `tee_checkpoint`/`tee_rollback`, `tee_capture`, `tee_job`.
Long-tail capability beyond the typed ops registers as virtual tools —
`VirtualTool` in `tee.kernel.registry`, reachable through
`tee_search_tools` at zero always-loaded cost (see any
`register_*_tools` module in-tree for the pattern; keep descriptions to
one summary line, they are priced per search hit).

To serve it: add a builder in `tee/cli.py` next to
`_build_blender_app` — or embed `TeeApp` in your own process and call
`tee.server.build_server(app)`.

## Session etiquette your adapter inherits

- Adapters **fail fast**; long operations go through `app.jobs.submit`
  and answer a job token (the `tee_job` pattern) instead of blocking.
- Version drift is the #1 friction: verify API calls against the live
  tool (a probe, a smoke test), never from memory; answer drifted
  calls with a rule-6 error naming what changed.
- The rehearsal law: this kit's acceptance is that a real adapter gets
  built from THIS page alone. Every stumble you hit is a kit bug —
  file it against `docs/adapter-kit.md`.
