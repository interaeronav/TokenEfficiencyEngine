"""FusionAdapter: Autodesk Fusion as a live TEE lane (A69), the seven kit
methods plus vocab() over the bridge add-in.

The kit's discipline (docs/adapter-kit.md) over the FreeCAD precedent: typed
ops in, one script per batch through one round trip, one JSON-shaped result
back; stable ids (short prefixed ids the bridge mints over entityToken);
rule-6 failures with Fusion's own message; checkpoints that are the
timeline marker plus every parameter expression and SAY what they restore;
budgeted JPEG capture of the live viewport. Everything the codegen emits is
a reference-verified row in docs/research/71-fusion-lane.md section 3.

What this lane will not do (doc 71 Law 5): create, save, close or upload
the owner's document. It works in the active design and writes exports and
captures where the caller says.
"""

from __future__ import annotations

import contextlib
import io
import os
import tempfile
from typing import Any

from tee.adapters.fusion import codegen
from tee.adapters.fusion.wire import FusionWire
from tee.kernel.adapter import AdapterInfo, Diff, Entity, LaneVocab
from tee.kernel.errors import TeeError

PURPOSE = "Autodesk Fusion, live: parametric CAD in the open design; renders pixels"
_BATCH_TIMEOUT_S = 120.0
_CAPTURE_TIMEOUT_S = 60.0
# The Blender rungs: full, then the floor; at most two renders per capture.
_CAPTURE_FULL = (1024, 576, 80)
_CAPTURE_SMALL = (640, 360, 70)
_CAPTURE_FLOOR = (320, 180, 55)
_ROW_KEYS = ("name", "kind", "parent")
_FIXES = {
    "fusion_no_design": "Open or create a design in Fusion (File > New Design); tee_status "
    "shows the active document.",
    "fusion_unknown_entity": "tee_scene_summary(adapter=fusion, refresh=true) lists the ids "
    "this bridge session knows.",
    "fusion_direct_design": "Switch the design to parametric (Design Settings > Capture "
    "Design History), or work without rollback: tee_batch still applies.",
    "fusion_capture_failed": "Fusion's viewport declined to write an image; check that a "
    "document is open and visible.",
    "fusion_export_failed": "Check the path is writable and the format matches the geometry.",
}


class FusionAdapter:
    def __init__(self, wire: FusionWire | None = None, *, workdir: str | None = None):
        self.wire = wire or FusionWire()
        self.workdir = workdir or tempfile.mkdtemp(prefix="tee-fusion-")
        self._version: str | None = None

    # -- identity ----------------------------------------------------------

    def info(self) -> AdapterInfo:
        try:
            ping = self.wire.ping()
        except TeeError:
            return AdapterInfo(
                id="fusion",
                product="Autodesk Fusion",
                version=self._version or "unknown",
                connected=False,
            )
        self._version = str(ping.get("version") or self._version or "unknown")
        return AdapterInfo(
            id="fusion",
            product="Autodesk Fusion",
            version=self._version,
            connected=True,
            extra={
                "document": ping.get("document"),
                "design": ping.get("design"),
                "ids": ping.get("ids", 0),
            },
        )

    def probe(self) -> bool:
        return self.wire.probe()

    def vocab(self) -> LaneVocab:
        """What this lane CLAIMS for routing (A68): the kinds the codegen
        dispatches. The generic fallback - any other word lands as a named
        empty component, the kit contract - is reachable with adapter=fusion."""
        return LaneVocab(
            ops=codegen.OPS,
            kinds=codegen.KINDS,
            kind_optional=False,
            imports=codegen.IMPORT_SUFFIXES,
            renders=True,
            purpose=PURPOSE,
        )

    # -- the wire, with Fusion's refusals -------------------------------------

    def run(self, program: str, *, timeout: float | None = None) -> dict[str, Any]:
        """One program on the primary thread; a script-level error becomes
        the one rule-6 refusal it names."""
        result = self.wire.execute(program, timeout=timeout or _BATCH_TIMEOUT_S)
        error = result.get("error")
        if error:
            code = str(error.get("code") or "fusion_op_failed")
            index = error.get("op_index", -1)
            where = f"Batch op {index} failed: " if isinstance(index, int) and index >= 0 else ""
            raise TeeError(
                code,
                f"{where}{str(error.get('message'))[:300]}",
                fix=_FIXES.get(
                    code,
                    "Fusion's message above names the problem; nothing after it ran.",
                ),
            )
        return result

    # -- listing -----------------------------------------------------------

    def list_entities(self) -> list[Entity]:
        rows = self.run(codegen.LIST_PROGRAM).get("rows") or []
        out: list[Entity] = []
        for row, summary in rows:
            out.append(
                Entity(
                    id=str(row["id"]),
                    name=str(row.get("name") or row["id"]),
                    kind=str(row.get("kind") or "object"),
                    parent=row.get("parent"),
                    summary=dict(summary or {}),
                )
            )
        return out

    # -- execute -----------------------------------------------------------

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        ops = [dict(op) for op in batch]
        codegen.check_batch(ops)  # bad_op / bad_kind before the wire, with the fix
        result = self.run(codegen.compile_batch(ops), timeout=_BATCH_TIMEOUT_S)
        details = {str(k): dict(v) for k, v in (result.get("details") or {}).items()}
        diff = Diff(
            created=[str(n) for n in result.get("created", [])],
            modified=[str(n) for n in result.get("modified", [])],
            deleted=[str(n) for n in result.get("deleted", [])],
            # a diff row says what the id IS (name, kind) plus the compact facts
            details={sid: dict(row) for sid, row in details.items()},
        )
        for sid, row in details.items():
            if sid in diff.created or sid in diff.modified:
                diff.upserts.append(
                    Entity(
                        id=sid,
                        name=str(row.get("name") or sid),
                        kind=str(row.get("kind") or "object"),
                        parent=row.get("parent"),
                        summary={k: v for k, v in row.items() if k not in _ROW_KEYS},
                    )
                )
        return diff

    # -- checkpoints ---------------------------------------------------------

    def snapshot(self, label: str) -> dict[str, Any]:
        state = self.run(codegen.SNAPSHOT_PROGRAM)
        return {
            "label": label,
            "marker": int(state["marker"]),
            "count": int(state["count"]),
            "params": dict(state.get("params") or {}),
            "restores": "timeline+parameters: what was created after this point is deleted and "
            "every parameter expression is put back; entities deleted since, sketch geometry "
            "edited in place, and user parameters added since are not restored",
        }

    def restore(self, payload: dict[str, Any]) -> None:
        self.run(codegen.restore_program(int(payload["marker"]), dict(payload.get("params") or {})))

    # -- capture -------------------------------------------------------------

    def capture(self, view: str, max_bytes: int) -> bytes:
        """At most two renders of the live viewport (fit, then save): one at
        a rung picked from the budget, one retry at the floor. Fusion writes
        the format its build supports (jpg first, png as the fallback - doc
        71 open question 1); a PNG is re-encoded here."""
        first = _CAPTURE_FULL if max_bytes >= 24 * 1024 else _CAPTURE_SMALL
        last_size = 0
        for width, height, quality in (first, _CAPTURE_FLOOR):
            jpg = os.path.join(self.workdir, f"capture-{width}.jpg")
            png = os.path.join(self.workdir, f"capture-{width}.png")
            for stale in (jpg, png):
                with contextlib.suppress(OSError):
                    os.unlink(stale)
            saved = self.run(
                codegen.capture_program(jpg, png, width, height), timeout=_CAPTURE_TIMEOUT_S
            )
            path = png if saved.get("ext") == "png" else jpg
            with open(path, "rb") as fh:
                data = fh.read()
            if saved.get("ext") == "png":
                data = _png_to_jpeg(data, quality)
            last_size = len(data)
            if last_size <= max_bytes:
                return data
        raise TeeError(
            "capture_over_budget",
            f"Smallest render is {last_size} bytes; budget is {max_bytes}.",
            fix="Raise max_kb, or read entity summaries instead of pixels.",
        )

    def close(self) -> None:  # nothing owned: the add-in belongs to Fusion
        return


def _png_to_jpeg(data: bytes, quality: int) -> bytes:
    try:
        from PIL import Image
    except ImportError as exc:
        raise TeeError(
            "capture_needs_pillow",
            "Fusion wrote a PNG and Pillow is not installed to re-encode it as JPEG.",
            fix="uv pip install pillow (the extract extra carries it), or accept text evidence.",
        ) from exc
    with Image.open(io.BytesIO(data)) as image:
        out = io.BytesIO()
        image.convert("RGB").save(out, format="JPEG", quality=quality, optimize=True)
        return out.getvalue()
