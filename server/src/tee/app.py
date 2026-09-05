"""TeeApp: composition root wiring adapters to the kernel.

One TeeApp per server process. Holds the per-adapter scene caches and the
shared managers; the MCP tool surface in `server.py` is a thin layer over
this object, so the whole app is testable without any MCP transport.

Concurrency: the mcp SDK dispatches every tool call on its own worker
thread. Kernel state (caches, checkpoints, response log) is not internally
locked, and the DCC bridges are serial by nature, so `app.lock` serializes
all tool bodies - the same discipline Epic's official MCP server enforces
(its tools run serially on the game thread; parallel dispatch deadlocks).
Jobs run outside the lock; their DCC calls queue on the bridge socket.
"""

from __future__ import annotations

import contextlib
import math
import threading
from pathlib import Path
from typing import Any, NamedTuple

from tee.config import ProjectConfig
from tee.kernel.adapter import Adapter, LaneVocab
from tee.kernel.budget import ResponseLog
from tee.kernel.checkpoints import CheckpointManager
from tee.kernel.errors import AdapterUnavailable, TeeError
from tee.kernel.jobs import JobManager
from tee.kernel.memory import ProjectMemory
from tee.kernel.registry import ToolRegistry
from tee.kernel.scene_cache import SceneCache


class Route(NamedTuple):
    """Where a batch goes and why (A68). `how` is None for an explicit
    adapter=, else "sole" | "id" | "kind" | "op" | "default"."""

    adapter: str
    how: str | None


# Refusal codes that mean "this lane does not speak that op": the ones the
# kernel may answer with the lanes that do. Runtime failures stay silent.
_VOCAB_REFUSALS = frozenset(
    {"bad_op", "bad_kind", "bad_batch_op", "pk_bad_op", "seamkiln_bad_op", "seamkiln_bad_kind"}
)


def _values_match(requested: Any, actual: Any) -> bool:
    """Echo test with float tolerance: a DCC rounding a requested 1.0 to
    1.0000000149 is still an echo, not drift worth reporting."""
    if isinstance(requested, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(float(requested), float(actual), rel_tol=1e-5, abs_tol=1e-5)
    if isinstance(requested, list) and isinstance(actual, list):
        return len(requested) == len(actual) and all(
            _values_match(r, a) for r, a in zip(requested, actual, strict=True)
        )
    return bool(requested == actual)


def _trim_batch_echoes(
    ops: list[dict[str, Any]],
    payload: dict[str, Any],
    prior: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Batch reports carry drift, not echoes (hard rule 2).

    A detail field that exactly matches what the op requested says nothing -
    drop it. For modified entities, a field whose value is unchanged from the
    pre-batch cache state is a re-report, not news - drop it too. Everything
    else (measured dims, adapter renames, computed side effects) stays.
    Created ids remain addressable via a compact names map. `created` is
    op-ordered: all three adapters build it by sequential append, and batches
    are atomic, so create op N maps to created[N]. The full post-op state
    still reaches the scene cache - this trims only the client payload."""
    details = payload.get("details")
    if not isinstance(details, dict):
        return
    requested: dict[str, dict[str, Any]] = {}
    created_list = payload.get("created") or []
    creator_ops = [op for op in ops if op.get("op") not in ("set", "delete")]
    if len(creator_ops) == len(created_list):
        # every creator op (create, import_file, ...) yielded exactly one
        # entity, in op order - map request to id; otherwise skip the
        # request mapping and rely on the prior-state rule alone
        for op, eid in zip(creator_ops, created_list, strict=False):
            req = dict(op.get("props") or {})
            for key in ("name", "kind"):
                if key in op:
                    req[key] = op[key]
            requested[eid] = req
    for op in ops:
        if op.get("op") == "set" and op.get("id") is not None:
            requested.setdefault(str(op["id"]), {}).update(op.get("props") or {})
    names: dict[str, str] = {}
    for eid in payload.get("created") or []:
        det = details.get(eid)
        if isinstance(det, dict) and isinstance(det.get("name"), str):
            names[eid] = det["name"]
    for eid, det in list(details.items()):
        if not isinstance(det, dict):
            continue
        req = requested.get(eid, {})
        was = (prior or {}).get(eid, {})
        for field in list(det):
            if (
                field == "id"
                or (field == "name" and eid in names)
                or (field in req and _values_match(req[field], det[field]))
                or (field in was and _values_match(was[field], det[field]))
            ):
                del det[field]
        if not det:
            del details[eid]
    if not details:
        payload.pop("details", None)
    if names:
        payload["names"] = names


def _vocab_line(vocab: LaneVocab, limit: int = 8) -> str:
    """One lane's vocabulary in a refusal, capped: the menu is paid only on
    error, and even then it must stay a sentence."""

    def clip(items: tuple[str, ...]) -> str:
        shown = ", ".join(items[:limit])
        return shown + (f" +{len(items) - limit} more" if len(items) > limit else "")

    ops = "any op" if vocab.ops is None else clip(vocab.ops)
    if vocab.kinds is None:
        kinds = "any kind" if vocab.accepts_op("create") else ""
    else:
        kinds = "kinds " + clip(vocab.kinds)
    return f"{ops}" + (f" ({kinds})" if kinds else "")


class TeeApp:
    def __init__(
        self,
        adapters: dict[str, Adapter],
        project_root: Path | str = ".",
        *,
        allow_code_exec: bool = False,
        default_adapter: str | None = None,
    ):
        from tee.kernel.machine import MachineLedger

        self.adapters = adapters
        # The DECLARED default: the lane a batch goes to when SEVERAL lanes
        # accept it and none was named (Law 19: default and declare). A68:
        # only `tee serve --default-adapter NAME` sets it - the order of
        # --adapter implies nothing, so a Desktop server holding blender +
        # partkiln + seamkiln has no hub; content routes, and a genuinely
        # ambiguous batch refuses naming the lanes. Checked before any side
        # effect: a default naming no served adapter is a startup error, not
        # a refusal the model meets on its first call.
        if default_adapter is not None and default_adapter not in adapters:
            known = ", ".join(adapters) or "(none)"
            raise ValueError(
                f"default_adapter '{default_adapter}' is not a configured adapter "
                f"(configured: {known}); list it among the adapters or drop the default."
            )
        self.default_adapter = default_adapter
        self.caches: dict[str, SceneCache] = {name: SceneCache() for name in adapters}
        self.checkpoints = CheckpointManager()
        self.jobs = JobManager()
        self.machine = MachineLedger()  # the ONE machine-load ledger (A42 R1)
        self.project_root = Path(project_root)
        # Remember which optional extras are installed, so a later refusal
        # can say "an upgrade removed this" instead of "you never installed
        # it". Installing a bundle rebuilds the venv from its lock and drops
        # everything added on top; measured three upgrades running.
        try:
            from datetime import date

            from tee.fleet import probe as _probe
            from tee.kernel import extras as _extras

            _state = self.project_root / ".tee"
            _extras.remember(_state, today=date.today().isoformat())
            _probe.bind_state_dir(_state)
        except Exception:  # bookkeeping must never stop the server booting
            pass
        self.memory = ProjectMemory(Path(project_root))
        self.registry = ToolRegistry()
        # A68: search prefers a tool whose lane is served over one whose lane
        # is not (it would only refuse); the registry asks the app which are.
        self.registry.served = lambda: set(self.adapters)
        self.response_log = ResponseLog()
        self.config = ProjectConfig.load(project_root)
        self.registry.disabled = set(self.config.disabled_tools)
        # A43 L1: what this project may do, and WHICH FILE said so. Naming
        # the loaded path in every refusal is what closes SI-B17, where an
        # edit that went nowhere was indistinguishable from a bug.
        from tee.kernel import trust

        config_path = Path(project_root) / ".tee" / "config.toml"
        self.registry.audit_log = self.response_log
        source = str(config_path) if config_path.is_file() else f"{config_path} (absent)"
        self.registry.grants = trust.Grants.from_config(self.config, source=source)

        # A45 P0a: keep reading it. The owner edits .tee/config.toml and the
        # next call sees it - no Desktop restart, which is the friction that
        # made a correct grant look like a broken one (SI-B17's second half).
        def _reload() -> trust.Grants:
            fresh = ProjectConfig.load(project_root)
            live = str(config_path) if config_path.is_file() else f"{config_path} (absent)"
            return trust.Grants.from_config(fresh, source=live)

        self.registry.grants_watcher = trust.GrantsWatcher(config_path, _reload)
        # K0 shadow recorder: on by default, zero behavior change; the
        # degrade-to-static law - [scheduler] shadow = false turns it off.
        from tee.kernel import shadow

        scheduler_cfg = dict(self.config.scheduler or {})
        if scheduler_cfg.get("shadow", True):
            shadow.RECORDER.enable(
                Path(project_root) / ".tee" / "shadow",
                cap_mb=float(scheduler_cfg.get("cap_mb", shadow.DEFAULT_CAP_MB)),
            )
        # K1: QoS as law (admission + rank + aging) - [scheduler] qos = false
        # restores plain FIFO, the degrade-to-static promise.
        self.jobs.configure(
            machine=self.machine,
            qos=bool(scheduler_cfg.get("qos", True)),
            aging_s=scheduler_cfg.get("aging_s"),
        )
        self.machine.set_queue_probe(self.jobs.queue_ages)
        # an explicit CLI flag enables; otherwise the project config decides
        self.allow_code_exec = allow_code_exec or bool(self.config.allow_code_exec)
        self.lock = threading.RLock()
        # installed by the extract module: (source, region, timestamp, budget)
        # -> (jpeg bytes, info) for the kernel tee_media tool
        self.media_view = None
        # installed by the extract module: () -> compact store recap dict
        self.extract_recap = None
        self._web = None  # lazy WebLookupService (A34)
        self.gateway = None  # GatewayService when [gateway] backends exist (A37)
        from tee.boards import register_board_tools
        from tee.kernel.meter import register_session_tools
        from tee.kernel.trust_tools import register_trust_tools

        register_session_tools(self)  # report_savings + handoff (A37 P6)
        register_trust_tools(self)  # tee_trust: the kernel's visibility (A43)

        # A45 P2: the headless fleet. Registration is metadata only - no
        # solver, CAD kernel or imaging library is imported until a tool is
        # actually called, so an uninstalled extra costs nothing at startup.
        from tee.fleet.tools import register_fleet_tools

        register_fleet_tools(self)
        register_board_tools(self)  # board_compose (A37 P7)

        # A53 P4: seamkiln's garment lane. Registration is metadata only -
        # seamkiln itself is never imported until a tool is called, so an
        # environment without it costs nothing at startup and every entry
        # point refuses with the install command rather than an ImportError
        # halfway through a batch.
        from tee.adapters.seamkiln.tools import register_seamkiln_tools

        register_seamkiln_tools(self)

        # A66 P4: partkiln's mechanical CAD lane. Metadata only, for the same
        # reason and one more: `import OCP` costs 26 s in a cold venv (P0a),
        # so paying it at boot would break Law 17 before the first call. The
        # kernel is reached through the adapter (in-process or the sidecar
        # venv that survives the extension wipe) and never imported here.
        from tee.adapters.partkiln.tools import register_partkiln_tools

        register_partkiln_tools(self)

    @property
    def llm_cfg(self) -> dict:
        """[llm] config enriched with the state dir the switch profiles
        persist into (A37 P0-S) - the one dict every chore consumer gets."""
        cfg = dict(self.config.llm or {})
        cfg["_state_dir"] = str(self.project_root / ".tee")
        cfg["_grants"] = self.registry.grants  # A43: the paid-engine gate
        return cfg

    @property
    def web(self):
        """The web-lookup service, built on first use from [web] config."""
        if self._web is None:
            from tee.web.tools import WebLookupService

            self._web = WebLookupService(
                self.project_root,
                config=self.config.web,
                llm=self.llm_cfg,
                registry=self.registry,
            )
        return self._web

    # -- helpers -----------------------------------------------------------

    def resolve_adapter(self, name: str | None) -> str:
        """Resolve an omitted adapter= to the declared default, else the sole
        configured adapter.

        Omitting the argument must just work on a real server (SI-B6: a
        wire-visible default of 'fake' failed on every non-test server and
        taxed each call with an explicit adapter=). Since 2026-09-04 the
        Desktop manifest serves blender + partkiln + seamkiln in ONE app, and
        an operator who wrote `--adapter blender --adapter partkiln` has
        DECLARED a default - the first listed - which tee_status reports
        (Law 19: default and declare). SI-B6's loud failure guards against an
        UNDECLARED default, so an app built with several adapters and no
        default still fails loud, naming the choices."""
        if name is not None:
            return name
        if self.default_adapter is not None:
            return self.default_adapter
        if len(self.adapters) == 1:
            return next(iter(self.adapters))
        known = ", ".join(sorted(self.adapters)) or "(none)"
        raise TeeError(
            "adapter_required",
            "Several adapters are configured; pass adapter=.",
            fix=f"Configured adapters: {known}.",
        )

    def adapter(self, name: str) -> Adapter:
        adapter = self.adapters.get(name)
        if adapter is None:
            known = ", ".join(sorted(self.adapters)) or "(none)"
            raise TeeError(
                "unknown_adapter",
                f"No adapter '{name}'.",
                fix=f"Configured adapters: {known}.",
            )
        if not adapter.probe():
            unavailable = AdapterUnavailable(name, hint=self._busy_hint())
            if len(self.adapters) > 1:
                # A multi-adapter server routes an omitted adapter= to its
                # declared default; when that DCC is down the caller who
                # wanted another lane needs the way there, not just "start
                # Blender". Single-adapter servers keep the old text.
                others = ", ".join(n for n in self.adapters if n != name)
                unavailable.fix = (
                    f"{unavailable.fix} Or pass adapter= to use another served adapter: {others}."
                )
            raise unavailable
        return adapter

    def vocab(self, name: str) -> LaneVocab:
        """What a served lane declares it accepts; a lane that declares
        nothing (no `vocab()`, or one that fails) claims everything."""
        fn = getattr(self.adapters[name], "vocab", None)
        if not callable(fn):
            return LaneVocab()
        try:
            return fn()
        except Exception:
            return LaneVocab()

    def route_batch(self, ops: list[dict[str, Any]], adapter: str | None) -> Route:
        """Which lane a batch goes to, and why (A68: no lane is the hub).

        An explicit adapter= is honoured as given. On a single-lane server
        the sole lane takes everything, so its payloads never change. On a
        multi-lane server an omitted adapter= resolves by CONTENT: an op that
        names an entity goes where that entity lives; a create goes where its
        kind is made; any other verb goes where it is accepted. One lane that
        takes every op wins and the reply says so. Several: the declared
        default breaks the tie if one was declared (Law 19), else the refusal
        names them (SI-B6). None: the refusal names, per op, the lanes that
        would take it."""
        if adapter is not None:
            return Route(adapter, None)
        served = list(self.adapters)
        if len(served) <= 1:
            return Route(self.resolve_adapter(None), "sole")
        vocabs = {name: self.vocab(name) for name in served}
        per_op: list[tuple[str, set[str]]] = []
        warmed = False
        for index, op in enumerate(ops):
            verb = op.get("op")
            eid = op.get("id")
            if eid is not None:
                if not warmed:  # a cold cache holds nothing; warm() is a no-op afterwards
                    for name in served:
                        with contextlib.suppress(Exception):
                            self.warm(name)
                    warmed = True
                holders = {n for n in served if self.caches[n].get(str(eid)) is not None}
                if not holders:
                    raise TeeError(
                        "unknown_entity",
                        f"batch[{index}]: no entity '{eid}' in any served lane "
                        f"({', '.join(served)}).",
                        fix="tee_scene_summary(adapter=<lane>) lists ids; refresh=true if the "
                        "lane changed outside TEE. Or pass adapter= to pin the lane.",
                    )
                per_op.append(("id", holders))
                continue
            takers = {n for n, v in vocabs.items() if v.accepts(op)}
            if not takers:
                raise self._no_lane_for(index, op, vocabs)
            per_op.append(("kind" if verb == "create" else "op", takers))
        candidates = set(served)
        for _, takers in per_op:
            candidates &= takers
        if len(candidates) == 1:
            lane = next(iter(candidates))
            how = next(k for k in ("id", "kind", "op") if any(kk == k for kk, _ in per_op))
            return Route(lane, how)
        if candidates:
            if self.default_adapter in candidates:
                return Route(self.default_adapter, "default")
            names = ", ".join(sorted(candidates))
            raise TeeError(
                "adapter_required",
                f"{len(candidates)} lanes accept this batch: {names}.",
                fix="Pass adapter=<lane>; tee_status lists each lane's ops and kinds. An "
                "operator can declare a tie-breaker with `tee serve --default-adapter NAME`.",
            )
        where = "; ".join(
            f"op {i} ({ops[i].get('op')}) fits {', '.join(sorted(takers))}"
            for i, (_, takers) in enumerate(per_op)
        )
        raise TeeError(
            "batch_spans_lanes",
            f"No single lane accepts every op: {where}.",
            fix="A batch is one lane's checkpoint - send one batch per lane (tee_script can "
            "chain them), or pass adapter= to pin one.",
        )

    def _no_lane_for(
        self, index: int, op: dict[str, Any], vocabs: dict[str, LaneVocab]
    ) -> TeeError:
        verb = op.get("op")
        what = f"create kind {op.get('kind')!r}" if verb == "create" else f"op {verb!r}"
        menu = "; ".join(f"{name}: {_vocab_line(v)}" for name, v in vocabs.items())
        return TeeError(
            "op_not_in_lane",
            f"batch[{index}]: no served lane accepts {what}.",
            fix=f"Served lanes and what they take - {menu}. Pass adapter= to pin a lane; "
            "tee_status lists them.",
        )

    def lane_accepts(self, name: str, ops: list[dict[str, Any]]) -> bool:
        vocab = self.vocab(name)
        return all(vocab.accepts(op) for op in ops)

    def _other_lanes_hint(self, lane: str, ops: list[dict[str, Any]], exc: BaseException) -> str:
        """After a lane refused an op it does not speak: the lanes that would
        take the whole batch, so the kernel - not the adapter - names them."""
        if getattr(exc, "code", None) not in _VOCAB_REFUSALS or len(self.adapters) < 2:
            return ""
        others = [n for n in self.adapters if n != lane and self.lane_accepts(n, ops)]
        if not others:
            return ""
        return f" Lanes that accept this batch: {', '.join(others)} (pass adapter={others[0]})."

    def cache(self, name: str) -> SceneCache:
        return self.caches[name]

    # -- decentralised reads (A68) ----------------------------------------
    #
    # On a multi-lane server with no declared default, a read that names no
    # lane is answered ACROSS lanes rather than defaulted to one: the summary
    # is an overview, an entity is found where it lives, a checkpoint covers
    # every lane with state, a rollback finds the lane that owns the ref, and
    # a capture goes to the one lane that can render. None of them snapshots.

    def unbound(self) -> bool:
        """Several lanes and no declared default: reads decentralise."""
        return len(self.adapters) > 1 and self.default_adapter is None

    # -- lanes by capability (A68 P1e) --------------------------------------
    #
    # Nine kernel-lane sites used to pick Blender by position (the first
    # adapter listed), by alphabet, or by name. A headless lane never touches
    # a DCC; a tool that genuinely needs one finds it by what it can do and
    # refuses by name when it is not served.

    def run_routed(
        self, ops: list[dict[str, Any]], adapter: str | None, label: str | None = None
    ) -> dict[str, Any]:
        """A batch from a virtual tool: route by content when no lane was
        named, then run and declare - what tee_batch does."""
        route = self.route_batch(ops, adapter)
        return self.run_batch(route.adapter, ops, label, routed=route.how)

    def blender_lane(self, adapter: str | None = None) -> str:
        """The served lane that runs Blender-side patterns (it executes
        Python), for the tier-2 modeling ops, the sims, the UEFN export and
        the extract-to-scene bridge. Named: checked. Unnamed: the one served
        Blender, found by capability - never by position."""
        able = [n for n, a in self.adapters.items() if hasattr(a, "execute_python")]
        if adapter is not None:
            if adapter not in self.adapters:
                self.adapter(adapter)  # raises unknown_adapter with the served names
            if adapter not in able:
                raise TeeError(
                    "unsupported_adapter",
                    f"This tool compiles to Blender-side patterns; lane '{adapter}' cannot run it.",
                    fix=f"Use the served Blender lane: {', '.join(able) or 'none is served'}.",
                )
            return adapter
        if len(able) == 1:
            return able[0]
        if not able:
            raise TeeError(
                "blender_not_served",
                f"This tool needs a Blender lane and none is served (served: "
                f"{', '.join(self.adapters) or 'none'}).",
                fix="tee serve --adapter blender ... ; on Desktop start Blender with the "
                "bridge add-on and check tee_status.",
            )
        raise TeeError(
            "adapter_required",
            f"{len(able)} served lanes run Blender-side patterns: {', '.join(able)}.",
            fix="Pass adapter=<lane>.",
        )

    def importer_lane(self, suffix: str, adapter: str | None = None) -> str:
        """The served lane that lands a file of this suffix as an import_file
        op (what its vocab declares under `imports`). Named: as given. On a
        single-lane or declared-default server: that lane, as before. Else
        the one lane that takes the suffix, or a refusal naming the lanes."""
        if adapter is not None:
            return adapter
        if not self.unbound():
            return self.resolve_adapter(None)
        ext = suffix.lower().lstrip(".")
        takers = [n for n in self.adapters if ext in self.vocab(n).imports]
        if len(takers) == 1:
            return takers[0]
        if not takers:
            raise TeeError(
                "handoff_no_importer",
                f"No served lane imports '.{ext}' files (served: {', '.join(self.adapters)}).",
                fix="Serve a lane that imports it (Blender takes glb/gltf/obj/fbx, Unreal "
                "glb/gltf/fbx/obj), or export a format one of them takes.",
            )
        raise TeeError(
            "handoff_importer_ambiguous",
            f"{len(takers)} served lanes import '.{ext}': {', '.join(takers)}.",
            fix="Pass adapter=<lane>.",
        )

    def _connected(self, name: str) -> bool:
        try:
            return bool(self.adapters[name].probe())
        except Exception:
            return False

    def overview(self) -> dict[str, Any]:
        """Every lane's stamp and kind counts - no rows. Connected lanes are
        warmed first so the counts are the lane's, not an empty cache's."""
        lanes: dict[str, Any] = {}
        for name in self.adapters:
            connected = self._connected(name)
            if connected:
                with contextlib.suppress(Exception):
                    self.warm(name)
            cache = self.caches[name]
            kinds: dict[str, int] = {}
            for entity in cache.entities.values():
                kinds[entity.kind] = kinds.get(entity.kind, 0) + 1
            row: dict[str, Any] = {
                "connected": connected,
                "entities": len(cache.entities),
                **cache.stamp(),
            }
            if kinds:
                row["kinds"] = kinds
            lanes[name] = row
        return {"lanes": lanes, "note": "pass adapter=<lane> for entity rows"}

    def locate(self, entity_id: str) -> str:
        """The one served lane whose cache holds the id."""
        for name in self.adapters:
            with contextlib.suppress(Exception):
                self.warm(name)
        holders = [n for n in self.adapters if self.caches[n].get(entity_id) is not None]
        if len(holders) == 1:
            return holders[0]
        if not holders:
            raise TeeError(
                "unknown_entity",
                f"No entity '{entity_id}' in any served lane ({', '.join(self.adapters)}).",
                fix="tee_scene_summary(adapter=<lane>) lists ids; refresh=true if the lane "
                "changed outside TEE.",
            )
        raise TeeError(
            "entity_ambiguous",
            f"Entity '{entity_id}' exists in {len(holders)} lanes: {', '.join(holders)}.",
            fix="Pass adapter=<lane>.",
        )

    def checkpoint_all(self, label: str) -> dict[str, Any]:
        """One label, every connected lane that holds state; lanes TEE has
        never touched have nothing a checkpoint could restore and are listed
        as skipped rather than snapshotted for nothing."""
        taken: dict[str, str] = {}
        skipped: list[str] = []
        for name, adapter in self.adapters.items():
            if not self._connected(name):
                skipped.append(name)
                continue
            with contextlib.suppress(Exception):
                self.warm(name)
            cache = self.caches[name]
            if not cache.has_state():
                skipped.append(name)
                continue
            cp = self.checkpoints.create(adapter, label, cache.revision, lane=name)
            taken[name] = cp.id
        if not taken:
            raise TeeError(
                "nothing_to_checkpoint",
                "No connected lane holds state to snapshot.",
                fix="Pass adapter=<lane> to checkpoint one lane regardless.",
            )
        out: dict[str, Any] = {"checkpoints": taken}
        if skipped:
            out["skipped"] = skipped
        return out

    def renderers(self) -> list[str]:
        """Connected lanes that can answer pixels right now."""
        out: list[str] = []
        for name, adapter in self.adapters.items():
            if not self.vocab(name).renders or not self._connected(name):
                continue
            can = getattr(adapter, "can_render", None)
            try:
                if callable(can) and not can():
                    continue
            except Exception:
                continue
            out.append(name)
        return out

    def capture_lane(self, adapter: str | None) -> str:
        """The lane a capture goes to: the one named, the sole or declared
        lane, else the one connected lane that renders."""
        if adapter is not None or not self.unbound():
            return self.resolve_adapter(adapter)
        lanes = self.renderers()
        if len(lanes) == 1:
            return lanes[0]
        if not lanes:
            raise TeeError(
                "capture_no_renderer",
                "No served lane can render pixels right now.",
                fix=f"Served: {', '.join(self.adapters)}. Start a lane that renders (Blender, "
                "Unreal) or arrange a garment in seamkiln, then pass adapter=<lane>. Text-first "
                "lanes answer tee_scene_summary and their own measure tools instead.",
            )
        raise TeeError(
            "capture_ambiguous",
            f"{len(lanes)} lanes can render: {', '.join(lanes)}.",
            fix="Pass adapter=<lane>.",
        )

    def rollback_ref(self, ref: str) -> dict[str, Any]:
        """Roll back by ref alone: the checkpoint knows its lane."""
        lane, cp = self.checkpoints.find(ref)
        return self.rollback(lane, cp.id)

    def warm(self, name: str) -> None:
        """Establish a cache baseline from the DCC on first contact, so diff
        stamps handed to the model are never computed against a cold cache
        (a cold (0,0) stamp would otherwise yield silently-wrong deltas)."""
        cache = self.caches.get(name)
        adapter = self.adapters.get(name)
        if cache is None or adapter is None:
            return
        if cache.revision == 0 and not cache.entities and adapter.probe():
            cache.resync(adapter)

    # -- operations shared by tools ---------------------------------------

    def run_batch(
        self,
        adapter_name: str,
        ops: list[dict[str, Any]],
        label: str | None = None,
        *,
        checkpoint: bool = True,
        routed: str | None = None,
    ) -> dict[str, Any]:
        """checkpoint=False is for callers that already hold an enclosing
        checkpoint and roll back on any raise (the script lane): the inner
        checkpoint+restore is then redundant work - on UE it doubled the
        cost of every scripted batch (A35 P2, two extra game-thread
        dispatches per batch).

        `routed` is the Route.how the caller resolved; on a multi-lane server
        the reply always carries `adapter` (Law 5: the reply says where the
        state is) and, when the kernel decided by content, `routed`."""
        adapter = self.adapter(adapter_name)
        self.warm(adapter_name)
        cache = self.cache(adapter_name)
        cp_label = label or f"auto:batch-r{cache.revision + 1}"
        cp = (
            self.checkpoints.create(adapter, cp_label, cache.revision, lane=adapter_name)
            if checkpoint
            else None
        )
        try:
            diff = adapter.execute(ops)
        except Exception as exc:
            # Make the failure atomic: a batch that failed mid-way must not
            # leave the DCC and the cache silently divergent.
            if cp is None:
                outcome = "is restored by the enclosing script checkpoint"
            else:
                try:
                    adapter.restore(cp.payload)
                    outcome = f"rolled back to checkpoint {cp.id}; no ops were kept"
                except Exception:
                    self.cache(adapter_name).invalidate()
                    outcome = (
                        "rollback also failed - state may be partially applied; "
                        "run tee_scene_summary(refresh=true)"
                    )
            if isinstance(exc, TeeError):
                hint = self._other_lanes_hint(adapter_name, ops, exc)
                fix = f"{exc.fix}{hint} Batch {outcome}." if exc.fix else f"{hint} Batch {outcome}."
                raise TeeError(exc.code, exc.message, fix=fix.strip()) from exc
            raise TeeError(
                "batch_failed",
                f"Batch failed: {type(exc).__name__}: {exc}",
                fix=f"Batch {outcome}.",
            ) from exc
        prior: dict[str, dict[str, Any]] = {}
        for eid in diff.modified:
            ent = cache.get(eid)
            if ent is not None:
                prior[eid] = ent.detailed()
        cache.apply_diff(diff, diff.upserts)
        payload: dict[str, Any] = {"ok": True, **cache.stamp()}
        if cp is not None:
            payload["checkpoint"] = cp.id
        payload["applied"] = len(ops)
        if len(self.adapters) > 1:
            payload["adapter"] = adapter_name
        if routed in ("id", "kind", "op"):
            payload["routed"] = f"by {routed}; pass adapter= to pin"
        elif routed == "default":
            payload["routed"] = "declared default"
        payload.update(diff.to_payload())
        _trim_batch_echoes(ops, payload, prior)
        return payload

    def rollback(self, adapter_name: str, ref: str) -> dict[str, Any]:
        adapter = self.adapter(adapter_name)
        cache = self.cache(adapter_name)
        cp = self.checkpoints.rollback(adapter, ref, lane=adapter_name)
        cache.resync(adapter)  # continuity break + rebuild from restored state
        out: dict[str, Any] = {"ok": True, "restored": cp.to_payload(), **cache.stamp()}
        if len(self.adapters) > 1:
            out["adapter"] = adapter_name
        return out

    def _rootedness(self) -> dict[str, Any]:
        """The project root, where grants would come from, and the tier
        split that follows. Compact by design: three lines that turn a
        confusing denial into a one-line fix."""
        from tee.kernel import trust as _t

        cfg_file = self.project_root / ".tee" / "config.toml"
        granted = sorted(self.registry.grants.granted)
        # Derive the tiers from what actually gates REGISTERED tools, never
        # from a hardcoded list. The first version of this hardcoded one,
        # and reported `mutate-scene` denied - which sounds alarming and
        # gates zero tools, while the capability that really governs scene
        # edits (`write-scene`, 33 tools) was granted all along. A denial
        # report that names capabilities nothing uses invents outages.
        # Every tool this session could actually be asked for: the virtual
        # registry PLUS the always-loaded surface, which is where the
        # mutation tools (tee_batch, tee_script) live. Counting only the
        # registry missed them and reported a grantless root as unrestricted.
        caps: dict[str, int] = {}
        for tool in self.registry._tools.values():
            cap = getattr(tool, "capability", None)
            if cap:
                caps[cap] = caps.get(cap, 0) + 1
        for name, cap in _t._EXPLICIT.items():
            if name.startswith("tee_"):
                caps[cap] = caps.get(cap, 0) + 1
        blocked = {
            cap: n
            for cap, n in caps.items()
            if not _t.check(
                cap, caller="live-turn", grants=self.registry.grants, consent=True
            ).allowed
        }
        denied = sorted(blocked)
        out: dict[str, Any] = {
            "project_root": str(self.project_root),
            "grants_file": str(cfg_file) if cfg_file.is_file() else "none found",
            "granted": granted or [],
        }
        if denied:
            out["denied_tiers"] = {c: f"{blocked[c]} tool(s)" for c in denied}
            out["why"] = (
                "reads and project memory work; these tiers need a grant "
                "in the project this session is rooted at"
            )
            out["fix"] = (
                f"launch with --project <the granted project>, or add a "
                f"[trust] grants line to {cfg_file}"
            )
        return out

    def status(self) -> dict[str, Any]:
        from tee.kernel import trust as _trust

        adapters = {}
        for name, adapter in self.adapters.items():
            try:
                self.warm(name)
                info = adapter.info().to_payload()
            except Exception as exc:
                info = {"id": name, "connected": False, "error": str(exc)[:120]}
            if not info.get("connected"):
                busy = self._busy_hint()
                if busy:
                    info["note"] = busy
            info["scene"] = self.caches[name].stamp()
            adapters[name] = info
        jobs = [j for j in self.jobs.list() if j["state"] in ("queued", "running")]
        from tee.llm import profiles

        payload: dict[str, Any] = {
            "adapters": adapters,
            "active_jobs": jobs,
            "checkpoints": self.checkpoints.list()[-5:],
            "virtual_tools": len(self.registry),
            # A46 P2a: report the CAPABILITY, not the pre-A43 flag. These
            # disagreed in the same payload the owner was reading:
            # tee_status said code_exec_enabled false while tee_trust said
            # exec-code was granted and tee_script actually ran. The legacy
            # `allow_code_exec` flag is one of two inputs the kernel ORs
            # together, so reporting it alone was reporting a premise as
            # though it were the conclusion.
            "code_exec_enabled": _trust.check(
                "exec-code",
                caller="live-turn",
                grants=self.registry.grants,
                consent=True,
            ).allowed
            or bool(self.allow_code_exec),
            "llm_profile": profiles.status_line(self.llm_cfg),
            # A47 P0.5: where this session is ROOTED, and what that costs.
            #
            # `tee serve --project` defaults to the launching client's cwd.
            # A terminal host (opencode) that does not pass --project boots
            # from a root with no grants file, keeps the read tiers, and
            # silently loses every mutation tier - while the owner's grants
            # sit in another directory. The owner read that as "TEE denies
            # access to all the tools", and TEE never said which root it had
            # loaded or where a grant would come from. It does now.
            #
            # This REPORTS; it never grants. TEE granting itself is exactly
            # what A45 forbids.
            "rooted_at": self._rootedness(),
        }
        if self.default_adapter is not None:
            # Declared, so an omitted adapter= is never a guess (Law 19).
            payload["default_adapter"] = self.default_adapter
        if len(self.adapters) > 1:
            # A68: what each lane is FOR and what it takes - the one place a
            # model can learn it at runtime. One capped line per lane.
            payload["lanes"] = {name: self._lane_line(name) for name in self.adapters}
        if self.registry.disabled:
            payload["disabled_tools"] = sorted(self.registry.disabled)
        if self.gateway is not None:
            payload["gateway"] = self.gateway.status()
        if self.config.warning:
            payload["config_warning"] = self.config.warning
        alerts = {
            tool: entry["alert"]
            for tool, entry in self.response_log.report().items()
            if "alert" in entry
        }
        if alerts:
            payload["response_size_alerts"] = alerts
        return payload

    def _lane_line(self, name: str) -> str:
        """purpose · ops · kinds · tool families, capped (~45 tokens)."""
        from tee.kernel import lanes as _lanes

        vocab = self.vocab(name)
        parts = [vocab.purpose or "(no purpose declared)"]
        if vocab.ops is not None:
            shown = ", ".join(vocab.ops[:6]) + (
                f" +{len(vocab.ops) - 6}" if len(vocab.ops) > 6 else ""
            )
            parts.append(f"ops {shown}")
        if vocab.kinds is not None:
            shown = ", ".join(vocab.kinds[:6]) + (
                f" +{len(vocab.kinds) - 6}" if len(vocab.kinds) > 6 else ""
            )
            parts.append(f"kinds {shown}")
        families = [f for f in _lanes.families_for(name) if f.endswith("_")]
        if families:
            parts.append("tools " + "/".join(families))
        if not vocab.renders:
            parts.append("no pixels")
        return " · ".join(parts)

    def recap(self) -> dict[str, Any]:
        """Eviction-safe resume (Phase 8, A12): a compact project recap
        rebuilt entirely from server-side state - scene stamps and kind
        counts, recent checkpoints, extract store shape, memory - so a host
        that evicted old tool results catches up with one call."""
        adapters: dict[str, Any] = {}
        for name, cache in self.caches.items():
            kinds: dict[str, int] = {}
            for entity in cache.entities.values():
                kinds[entity.kind] = kinds.get(entity.kind, 0) + 1
            adapters[name] = {**cache.stamp(), "entities": len(cache.entities)}
            if kinds:
                adapters[name]["kinds"] = kinds
        out: dict[str, Any] = {"adapters": adapters}
        checkpoints = self.checkpoints.list()[-3:]
        if checkpoints:
            out["checkpoints"] = checkpoints
        memory = self.memory.preamble()
        if memory.get("facts") or memory.get("notes"):
            out["memory"] = memory
        if self.extract_recap is not None:
            with contextlib.suppress(Exception):
                out["extract"] = self.extract_recap()
        active = [j for j in self.jobs.list() if j["state"] in ("queued", "running")]
        if active:
            out["active_jobs"] = active
        from tee.kernel.meter import savings_block

        block = savings_block(self.response_log.ledger())
        if block:
            out["savings"] = block
        meter = self.machine.meter_block()
        if meter["routed_tasks"] or meter["jobs"]["active"]:
            swaps = meter["swaps"]["implicit"] + meter["swaps"]["explicit"]
            line = (
                f"{meter['routed_tasks']} routed / {meter['escalations']} escalated, "
                f"{swaps} swaps ({meter['swaps']['refused']} refused)"
            )
            with contextlib.suppress(Exception):
                from tee.llm import profiles

                if profiles.load_state(self.llm_cfg).get("pinned"):
                    line += ", pinned"
            out["router"] = line
        return out

    def _busy_hint(self) -> str | None:
        """The serial bridge looks 'down' while a long job holds it."""
        active = [j for j in self.jobs.list() if j["state"] == "running"]
        if active:
            names = ", ".join(f"{j['job']} ({j['label']})" for j in active[:3])
            return f"the bridge may be busy with a running job: {names}"
        return None

    def shutdown(self) -> None:
        from tee.kernel import shadow

        shadow.RECORDER.disable()
        self.jobs.shutdown()
        if self.gateway is not None:
            with contextlib.suppress(Exception):
                self.gateway.shutdown()
        for name, adapter in self.adapters.items():
            with contextlib.suppress(Exception):
                self.checkpoints.discard_all(adapter, lane=name)
            close = getattr(adapter, "close", None)
            if close is not None:
                with contextlib.suppress(Exception):
                    close()
