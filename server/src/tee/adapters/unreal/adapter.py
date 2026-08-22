"""Unreal adapter: TEE's kernel contract over Epic's in-editor MCP server.

This is a PROXY, not a bridge (decision A4). Epic ships 830 tools across the
toolset registry; TEE does not re-port them. What it adds is the part Epic
does not: compact entity ids and diffs instead of refPath soup, one
round-trip per batch, checkpoints, and a summarizing front for the schema
dumps.

Checkpointing is TEE's own (A24): UE 5.8.1 disabled transaction bundling
during tool scripts, so the editor's undo stack cannot be relied on to
unwind a batch. `snapshot` records the actor set with transforms and
`restore` re-applies it - see `restore` for exactly what that does and does
not cover.
"""

from __future__ import annotations

import json
from typing import Any

from tee.kernel.adapter import AdapterInfo, Diff, Entity
from tee.kernel.errors import TeeError

from . import blueprint as bp_verify
from . import codegen
from .catalog import ToolsetCatalog
from .wire import UnrealWire

_SCRIPT_TIMEOUT = 300.0


class UnrealAdapter:
    kind = "unreal"

    def __init__(self, wire: UnrealWire | None = None):
        self.wire = wire or UnrealWire()
        self.catalog = ToolsetCatalog(self.wire)
        self._refs: dict[str, str] = {}  # TEE entity id -> actor refPath
        self._ids: dict[str, str] = {}  # actor refPath -> TEE entity id
        self._labels: dict[str, str] = {}  # refPath -> label TEE gave it
        self._moved: set[str] = set()  # refPaths TEE itself transformed
        self._next = 0

    # -- identity ----------------------------------------------------------

    def info(self) -> AdapterInfo:
        connected = self.wire.probe()
        toolsets = len(self.catalog.load_toolsets()) if connected else 0
        return AdapterInfo(
            id="unreal",
            product="Unreal Engine",
            version="5.8+",
            connected=connected,
            extra={"endpoint": self.wire.url, "toolsets": toolsets},
        )

    def probe(self) -> bool:
        return self.wire.probe()

    # -- entity ids --------------------------------------------------------

    def _id_for(self, ref: str) -> str:
        if ref not in self._ids:
            self._next += 1
            eid = f"u{self._next}"
            self._ids[ref] = eid
            self._refs[eid] = ref
        return self._ids[ref]

    def _ref_for(self, eid: str) -> str:
        try:
            return self._refs[eid]
        except KeyError:
            raise TeeError(
                "unknown_entity",
                f"No Unreal entity {eid!r} in this session.",
                fix="Refresh with tee_scene_summary(adapter='unreal', refresh=true).",
            ) from None

    def _entity(self, record: dict[str, Any]) -> Entity:
        """A listing record carries only `ref`; a detail record adds label and
        location. Names fall back to the object name in the refPath, which is
        free - resolving the editor label costs a game-thread dispatch."""
        ref = record["ref"]
        summary: dict[str, Any] = {"ref": ref}
        if "location" in record:
            summary["location"] = record["location"]
        return Entity(
            id=self._id_for(ref),
            name=record.get("label") or self._labels.get(ref) or ref.rsplit(".", 1)[-1],
            kind="actor",
            summary=summary,
        )

    # -- reads -------------------------------------------------------------

    def _run_script(self, script: str, timeout: float = _SCRIPT_TIMEOUT) -> dict[str, Any]:
        raw = self.catalog.call(
            "ProgrammaticToolset", "execute_tool_script", {"script": script}, timeout=timeout
        )
        try:
            outer = json.loads(raw)
        except json.JSONDecodeError:
            # The sandbox reports script failures as bare text, not JSON.
            raise TeeError(
                "ue_script_failed",
                _first_line(raw),
                fix="The script ran inside the editor; the message above is "
                "the sandbox's own error.",
            ) from None
        inner = outer.get("returnValue")
        if isinstance(inner, str):
            try:
                return json.loads(inner)
            except json.JSONDecodeError:
                raise TeeError("ue_script_failed", _first_line(inner)) from None
        return inner if isinstance(inner, dict) else {}

    def list_entities(self) -> list[Entity]:
        """One game-thread dispatch regardless of scene size."""
        data = self._run_script(codegen.LIST_ACTORS)
        return [self._entity(a) for a in data.get("actors", [])]

    def entity_details(self, ids: list[str]) -> list[Entity]:
        """Label + transform for a bounded set (2 dispatches each, so this is
        opt-in and never fans out over the whole level)."""
        refs = [self._ref_for(eid) for eid in ids]
        data = self._run_script(codegen.details_program(refs))
        return [self._entity(a) for a in data.get("actors", [])]

    # -- mutation ----------------------------------------------------------

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        """Whole batch, one round-trip (P3)."""
        try:
            refs = {op["id"]: self._ref_for(op["id"]) for op in batch if op.get("id")}
            script = codegen.program_batch(batch, refs)
        except ValueError as exc:
            raise TeeError(
                "bad_batch_op", str(exc), fix="Fix the op and resend the batch."
            ) from exc
        data = self._run_script(script)

        for record in (data.get("details") or {}).values():
            if record.get("label"):
                self._labels[record["ref"]] = record["label"]
        self._moved.update(data.get("created") or [])
        self._moved.update(data.get("modified") or [])

        details = {}
        upserts = []
        for record in (data.get("details") or {}).values():
            ent = self._entity(record)
            details[ent.id] = ent.detailed()
            upserts.append(ent)
        deleted = []
        for ref in data.get("deleted") or []:
            eid = self._ids.pop(ref, None)
            if eid:
                self._refs.pop(eid, None)
                deleted.append(eid)
        return Diff(
            created=[self._id_for(r) for r in data.get("created") or []],
            modified=[self._id_for(r) for r in data.get("modified") or []],
            deleted=deleted,
            details=details,
            upserts=upserts,
        )

    # -- checkpoints -------------------------------------------------------

    def snapshot(self, label: str) -> dict[str, Any]:
        """One dispatch for the actor set, plus transforms only for actors TEE
        has already moved - the only ones restore can meaningfully put back."""
        data = self._run_script(codegen.LIST_ACTORS)
        actors = [{"ref": a["ref"], "location": None} for a in data.get("actors", [])]
        touched = [a for a in actors if a["ref"] in self._moved]
        if touched:
            detailed = self._run_script(codegen.details_program([a["ref"] for a in touched]))
            positions = {d["ref"]: d["location"] for d in detailed.get("actors", [])}
            for entry in actors:
                if entry["ref"] in positions:
                    entry["location"] = positions[entry["ref"]]
        return {"label": label, "actors": actors}

    def restore(self, payload: dict[str, Any]) -> None:
        """Re-apply a snapshot: delete actors added since, and put the
        surviving ones back where they were.

        Honest bounds - this is NOT a general undo. It restores actor
        existence and transforms. It does not resurrect actors deleted since
        the snapshot, and it does not revert property edits made through
        other toolsets. UE 5.8.1 disabled transaction bundling during tool
        scripts (A24), so the editor's own undo stack is not a substitute.
        """
        self._run_script(codegen.restore_program(payload.get("actors", [])))

    def discard_snapshot(self, payload: dict[str, Any]) -> None:
        return None

    # -- blueprint authoring ----------------------------------------------

    def blueprint_function(
        self,
        *,
        folder: str,
        asset_name: str,
        function_name: str,
        dsl: str,
        params: list[dict[str, Any]] | None = None,
        parent_class: str = "/Script/Engine.Actor",
        warnings_as_errors: bool = True,
    ) -> dict[str, Any]:
        """Author a Blueprint function from graph DSL and VERIFY it landed.

        Epic's write_graph_dsl drops statements it cannot resolve without
        error, and the Blueprint then compiles clean, so a hallucinated node
        type looks like success from every signal the engine exposes. TEE
        reads the graph back and compares structure before reporting success.
        """
        try:
            bp_verify.parse_sexpr(dsl)  # fail on our side, before the editor
        except bp_verify.DslSyntaxError as exc:
            raise TeeError(
                "ue_dsl_syntax",
                f"Graph DSL does not parse: {exc}",
                fix="Check bracket balance; ue_call BlueprintTools "
                "get_graph_dsl_docs returns the full grammar.",
            ) from exc

        data = self._run_script(
            codegen.blueprint_function_program(
                folder,
                asset_name,
                function_name,
                dsl,
                list(params or []),
                parent_class,
                warnings_as_errors,
            )
        )
        # Compile as a SEPARATE call: a tool failure inside the script is not
        # catchable there (the sandbox aborts the whole run), so the only way
        # to get compile diagnostics instead of a dead script is to ask for
        # the compile on its own and let the error come back normally.
        compile_status, compile_error = "clean", None
        try:
            self.catalog.call(
                "BlueprintTools",
                "compile_blueprint",
                {
                    "blueprint": {"refPath": data.get("blueprint")},
                    "warnings_as_errors": warnings_as_errors,
                },
                timeout=300,
            )
        except TeeError as exc:
            compile_status, compile_error = "failed", exc.message[:800]

        report = bp_verify.verify_written(dsl, data.get("readback", ""))
        result = {
            "blueprint": data.get("blueprint"),
            "function": function_name,
            "compile": compile_status,
            "reused": data.get("reused"),
            "verified": report["ok"],
            "forms_requested": report["forms_requested"],
            "forms_written": report["forms_written"],
        }
        if compile_error:
            result["compile_error"] = compile_error
        if not report["ok"]:
            raise TeeError(
                "ue_graph_incomplete",
                f"The editor kept only {report['forms_written']} of "
                f"{report['forms_requested']} DSL forms in {function_name} - "
                f"unresolved: {', '.join(report.get('likely_unresolved') or []) or 'unknown'}. "
                "write_graph_dsl drops what it cannot resolve and still "
                "compiles clean, so this would otherwise look like success.",
                fix="Check the node type ids with BlueprintTools "
                "find_node_types; the graph now holds: " + report["readback"][:200],
            )
        return result

    def capture(self, view: str, max_bytes: int) -> bytes:
        raise TeeError(
            "capture_unsupported",
            "Viewport capture is not wired for Unreal yet.",
            fix="Use tee_scene_summary / ue_call with EditorAppToolset "
            "screenshot tools; text state is the default evidence (P4).",
        )

    def close(self) -> None:
        self.wire.close()


def _first_line(text: str) -> str:
    line = (text or "").strip().splitlines()
    return line[0][:300] if line else "the editor script failed with no message"
