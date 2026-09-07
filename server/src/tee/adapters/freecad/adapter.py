"""FreeCADAdapter: the seven kit methods over the one bridge (A37 P4).

Follows docs/adapter-kit.md: typed ops in, diffs out, stable ids
(FreeCAD object Names are stable per document session), rule-6 failures,
snapshot/restore via document save-copies, budgeted JPEG capture.

Sketch ops are solved SERVER-SIDE first (tee.physical.sketch/py-slvs,
mm as numbers - the solver is unit-agnostic) so FreeCAD receives final
geometry; closure is by construction, never by hoping a DCC solver
converges from guesses.
"""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path
from typing import Any

from tee.adapters.freecad import codegen
from tee.adapters.freecad.wire import FreeCADWire
from tee.kernel.adapter import AdapterInfo, Diff, Entity, LaneVocab
from tee.kernel.errors import TeeError

DEFAULT_DOC = "TEE"


class FreeCADAdapter:
    def __init__(self, wire: FreeCADWire | None = None, *, doc: str = DEFAULT_DOC):
        self.wire = wire or FreeCADWire()
        self.doc = doc
        self._doc_ready = False
        self._version: list[str] | None = None
        self._spill_dir: Path | None = None

    # -- identity ----------------------------------------------------------

    def info(self) -> AdapterInfo:
        connected = self.wire.ping()
        if connected and self._version is None:
            try:
                self._version = [
                    str(v)
                    for v in self.wire.py_json(
                        "import FreeCAD, json; print(json.dumps(FreeCAD.Version()[:3]))"
                    )
                ]
            except TeeError:
                self._version = None
        version = ".".join(self._version) if self._version else "unknown"
        return AdapterInfo(
            id="freecad",
            product="FreeCAD",
            version=version,
            connected=connected,
            extra={"doc": self.doc},
        )

    def probe(self) -> bool:
        return self.wire.ping()

    def vocab(self) -> LaneVocab:
        """What this lane accepts (A68): three typed ops; any named create
        kind (primitives, sketch/pad/pocket, or a generic FeaturePython) but
        never a kind-less create."""
        return LaneVocab(
            ops=("create", "set", "delete"),
            kinds=None,
            kind_optional=False,
            imports=(),
            renders=True,
            purpose="FreeCAD fabrication: sketch/pad/pocket, TechDraw sheets",
        )

    # -- document ----------------------------------------------------------

    def _ensure_doc(self) -> None:
        if self._doc_ready:
            return
        if self.doc not in self.wire.list_documents():
            actual = self.wire.create_document(self.doc)
            self.doc = actual  # FreeCAD sanitises/deduplicates names
        self._doc_ready = True

    # -- listing -----------------------------------------------------------

    def list_entities(self) -> list[Entity]:
        self._ensure_doc()
        rows = self.wire.py_json(codegen.LIST_CODE.format(doc=self.doc))
        out: list[Entity] = []
        for row, summary in rows:
            out.append(
                Entity(
                    id=str(row["id"]),
                    name=str(row.get("name") or row["id"]),
                    kind=str(row.get("kind") or "object"),
                    summary=dict(summary or {}),
                )
            )
        return out

    # -- execute -----------------------------------------------------------

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        self._ensure_doc()
        ops = [self._prepare(dict(op)) for op in batch]
        script = codegen.compile_batch(self.doc, ops)
        result = self.wire.py_json(script)
        if "error" in result:
            err = result["error"]
            raise TeeError(
                "freecad_op_failed",
                f"Batch op {err.get('op_index')} failed: {str(err.get('message'))[:250]}",
                fix="FreeCAD's message above names the problem; nothing after it ran.",
            )
        diff = Diff(
            created=[str(n) for n in result.get("created", [])],
            modified=[str(n) for n in result.get("modified", [])],
            deleted=[str(n) for n in result.get("deleted", [])],
            details={str(k): dict(v) for k, v in (result.get("details") or {}).items()},
        )
        for entity in self.list_entities():
            if entity.id in diff.created or entity.id in diff.modified:
                diff.upserts.append(entity)
        return diff

    def _prepare(self, op: dict[str, Any]) -> dict[str, Any]:
        """Solve sketches before they reach FreeCAD (the sketch_solve wiring)."""
        if op.get("op") == "create" and op.get("kind") == "sketch":
            from tee.physical.sketch import solve_sketch

            props = dict(op.get("props") or {})
            solved = solve_sketch(
                {
                    "points": props.get("points") or [],
                    "lines": props.get("lines") or [],
                    "constraints": props.get("constraints") or [],
                }
            )
            # solve_sketch answers {"points": {id: [x, y]}, "dof": n, ...}
            props["_solved_points"] = {
                str(pid): [float(xy[0]), float(xy[1])]
                for pid, xy in dict(solved.get("points") or {}).items()
            }
            op["props"] = props
        return op

    # -- checkpoints ---------------------------------------------------------

    def _spill(self) -> Path:
        if self._spill_dir is None:
            self._spill_dir = Path(tempfile.mkdtemp(prefix="tee-freecad-cp-"))
        return self._spill_dir

    def snapshot(self, label: str) -> dict[str, Any]:
        self._ensure_doc()
        safe = "".join(c if c.isalnum() else "_" for c in label)[:40] or "cp"
        path = self._spill() / f"{safe}.FCStd"
        self.wire.py(f"import FreeCAD; FreeCAD.getDocument({self.doc!r}).saveCopy({str(path)!r})")
        return {"label": label, "doc": self.doc, "path": str(path)}

    def restore(self, payload: dict[str, Any]) -> None:
        path = str(payload["path"])
        if not Path(path).is_file():
            raise TeeError(
                "freecad_checkpoint_gone",
                f"Checkpoint file missing: {path}",
                fix="The spill dir is per-session; roll back within the session.",
            )
        self.wire.py(
            "import FreeCAD\n"
            f"try: FreeCAD.closeDocument({self.doc!r})\n"
            "except Exception: pass\n"
            f"doc = FreeCAD.openDocument({path!r})\n"
            "doc.recompute()"
        )
        self._doc_ready = True

    # -- capture -------------------------------------------------------------

    def capture(self, view: str, max_bytes: int) -> bytes:
        self._ensure_doc()
        for width, height in ((800, 600), (400, 300)):
            payload = self.wire.py_json(
                "import FreeCADGui, json, base64, tempfile, os\n"
                f"FreeCADGui.getDocument({self.doc!r})\n"
                "v = FreeCADGui.activeDocument().activeView()\n"
                f"v.viewIsometric() if {view!r} in ('', 'viewport', 'iso') else None\n"
                "fd, p = tempfile.mkstemp(suffix='.jpg'); os.close(fd)\n"
                f"v.saveImage(p, {width}, {height}, 'White')\n"
                "data = open(p, 'rb').read(); os.unlink(p)\n"
                "print(json.dumps({'b64': base64.b64encode(data).decode()}))"
            )
            data = base64.b64decode(payload["b64"])
            if len(data) <= max_bytes:
                return data
        raise TeeError(
            "capture_over_budget",
            f"The smallest render is {len(data)} bytes (> {max_bytes}).",
            fix="Raise max_kb, or read entity summaries instead of pixels.",
        )

    def close(self) -> None:  # nothing owned: the bridge belongs to FreeCAD
        return
