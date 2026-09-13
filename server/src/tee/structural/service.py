"""Revisioned project studies and immutable per-run evidence."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from . import mechanics, runner
from .model import fail, fingerprint, validate


def plain(path: Path) -> None:
    for p in (path, *path.parents):
        if p.is_symlink():
            fail("Structural state cannot traverse symbolic links.")


def read(path: Path) -> dict:
    plain(path)
    if not path.is_file() or path.stat().st_size > 4 * 1024 * 1024:
        fail("Missing or oversized structural state file.")
    return json.loads(path.read_text())


def write(path: Path, value: dict) -> None:
    plain(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x") as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


class StructuralService:
    def __init__(self, project: Path, config: dict | None = None) -> None:
        self.project = Path(project).resolve()
        self.root = self.project / ".tee/structural"
        self.config = dict(config or {})
        self._mutex = threading.RLock()
        # Separate from the project lock: cancellation must reach a solver even
        # when another study is preparing inputs or waiting for that lock.
        self._lifecycle = threading.Condition()
        self._closed = False
        self._active: dict[object, threading.Event] = {}

    def close(self, timeout_s: float = 5.0) -> None:
        """Cancel owned solves and wait for orderly process cleanup.

        A bounded failure is reported rather than claiming cleanup completed.
        This hook requires orderly application shutdown; abrupt interpreter
        termination or machine failure cannot execute cooperative cleanup.
        """
        if not 0 <= timeout_s <= 30:
            fail("Structural shutdown timeout must be between 0 and 30 seconds.")
        deadline = time.monotonic() + timeout_s
        with self._lifecycle:
            self._closed = True
            for stop in self._active.values():
                stop.set()
            while self._active:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    fail(
                        f"Structural shutdown cleanup timed out with {len(self._active)} "
                        "solve(s) still active."
                    )
                self._lifecycle.wait(timeout=remaining)

    @contextmanager
    def locked(self) -> Iterator[None]:
        import fcntl

        with self._mutex:
            plain(self.root)
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            path = self.root / ".lock"
            plain(path)
            with path.open("a") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(stream, fcntl.LOCK_UN)

    def folder(self, ident: str) -> Path:
        if not isinstance(ident, str) or not re.fullmatch(r"structure_[a-f0-9]{16}", ident):
            fail("Use a structural model_id from st_model.")
        p = self.root / ident
        plain(p)
        if not p.is_dir():
            fail("Structural study is missing in this project.")
        return p

    def state(self, ident: str) -> dict:
        rec = read(self.folder(ident) / "model.json")
        if fingerprint(rec["model"]) != rec["model_sha256"]:
            fail("Structural model checksum mismatch.")
        validate(rec["model"])
        return rec

    def save(
        self, model: dict, ident: str | None = None, expected_revision: int | None = None
    ) -> dict:
        m = validate(model)
        # Expensive numeric stability gate belongs to solve, so an incomplete
        # support strategy can be saved and inspected before analysis.
        with self.locked():
            if ident is None:
                if expected_revision is not None:
                    fail("New study must omit expected_revision.")
                ident = "structure_" + uuid.uuid4().hex[:16]
                folder = self.root / ident
                folder.mkdir(mode=0o700)
                revision = 1
            else:
                folder = self.folder(ident)
                old = self.state(ident)
                if type(expected_revision) is not int or old["revision"] != expected_revision:
                    fail(
                        "Stale structural revision; query then apply the edit against its "
                        "current revision."
                    )
                revision = expected_revision + 1
            rec = {
                "model_id": ident,
                "revision": revision,
                "model_sha256": fingerprint(m),
                "model": m,
            }
            write(folder / "model.json", rec)
        return self.summary(rec)

    def summary(self, rec: dict) -> dict:
        m = rec["model"]
        return {k: rec[k] for k in ("model_id", "revision", "model_sha256")} | {
            "name": m["name"],
            "counts": {
                k: len(m[k])
                for k in (
                    "nodes",
                    "elements",
                    "materials",
                    "sections",
                    "supports",
                    "cases",
                    "combinations",
                )
            },
            "design_code_status": "not_assessed",
        }

    def query(
        self, ident: str, collection: str = "summary", offset: int = 0, limit: int = 20
    ) -> dict:
        page([], offset, limit)
        rec = self.state(ident)
        out = self.summary(rec)
        if collection == "summary":
            return out
        if collection not in (
            "nodes",
            "elements",
            "materials",
            "sections",
            "supports",
            "cases",
            "combinations",
        ):
            fail("Choose a declared structural model collection or summary.")
        return out | page(rec["model"][collection], offset, limit) | {"collection": collection}

    def solve(
        self, ident: str, revision: int, case: str, engine: str, cancelled: threading.Event
    ) -> dict:
        token = object()
        with self._lifecycle:
            if self._closed:
                fail("Structural service is shutting down; new solves are refused.")
            if cancelled.is_set():
                fail("Structural job cancelled before preparation.")
            self._active[token] = cancelled
        try:
            return self._solve(ident, revision, case, engine, cancelled)
        finally:
            with self._lifecycle:
                del self._active[token]
                self._lifecycle.notify_all()

    def _solve(
        self, ident: str, revision: int, case: str, engine: str, cancelled: threading.Event
    ) -> dict:
        with self.locked():
            if cancelled.is_set():
                fail("Structural job cancelled before preparation.")
            rec = self.state(ident)
            if type(revision) is not int or rec["revision"] != revision:
                fail("Stale structural revision before solve.")
            self.check_bim(rec["model"])
            # Validate stability and availability before creating a run directory.
            sys = mechanics.system(rec["model"])
            loads = mechanics.loading(rec["model"], sys, case)
            if runner.executable(engine, self.config)[0] is None:
                fail(f"{engine} missing; configure its executable in [structural].")
            run_id = "run_" + uuid.uuid4().hex[:16]
            path = self.folder(ident) / run_id
            path.mkdir(mode=0o700)
            write(path / "input.json", rec | {"case": case, "engine": engine})
        try:
            output = runner.solve(path, rec["model"], loads, engine, self.config, cancelled)
            checked = mechanics.check(
                rec["model"], sys, loads, output["raw"], oofem_text=engine == "oofem"
            )
            result = {k: rec[k] for k in ("model_id", "revision", "model_sha256")} | {
                "run_id": run_id,
                "case": case,
                "factors": loads["factors"],
                "engine_identity": output["identity"],
                "units": "N-mm-MPa-rad",
                "force_convention": (
                    "local nodal resisting forces [Ni,Vi,Mi,Nj,Vj,Mj]; member equivalent "
                    "loads removed"
                ),
                "design_code_status": "not_assessed",
                "capacity_status": "not_assessed",
                "result": checked,
                "bim_source": rec["model"].get("bim_source"),
            }
            result["result_sha256"] = fingerprint(result)
            if cancelled.is_set():
                fail("Structural job cancelled before result publication.")
            write(path / "result.json", result)
            return self.result(ident, run_id)
        except Exception as exc:
            write(
                path / "failure.json",
                {
                    "error": str(exc),
                    "run_id": run_id,
                    "engine": engine,
                    "model_sha256": rec["model_sha256"],
                },
            )
            raise

    def result(
        self, ident: str, run_id: str, collection: str = "summary", offset: int = 0, limit: int = 20
    ) -> dict:
        if not isinstance(run_id, str) or not re.fullmatch(r"run_[a-f0-9]{16}", run_id):
            fail("Use a run_id from a completed structural job.")
        data = read(self.folder(ident) / run_id / "result.json")
        checksum = data.pop("result_sha256")
        if fingerprint(data) != checksum:
            fail("Structural result checksum mismatch.")
        rec = self.state(ident)
        val = data["result"]
        out = {
            k: data[k]
            for k in (
                "model_id",
                "revision",
                "model_sha256",
                "run_id",
                "case",
                "units",
                "design_code_status",
                "capacity_status",
            )
        }
        out.update(
            {
                "engine": data["engine_identity"]["engine"],
                "result_sha256": checksum,
                "stale": rec["model_sha256"] != data["model_sha256"]
                or rec["revision"] != data["revision"],
                "checks": val["checks"],
                "internal_member_extrema": val["internal_member_extrema"],
                "max_nodal_translation_mm": val["max_nodal_translation_mm"],
                "max_nodal_rotation_rad": val["max_nodal_rotation_rad"],
                "evidence_path": str(self.folder(ident) / run_id),
                "bim_source_current": self.bim_current(
                    {"bim_source": data["bim_source"]} if data.get("bim_source") else {}
                ),
            }
        )
        if collection != "summary":
            if collection not in ("displacements", "reactions", "element_forces"):
                fail("Choose summary, displacements, reactions or element_forces.")
            out.update(
                page([{"id": k, "values": v} for k, v in val[collection].items()], offset, limit)
            )
            out["collection"] = collection
        return out

    def bim_current(self, m: dict) -> bool | None:
        if "bim_source" not in m:
            return None
        try:
            self.check_bim(m)
            return True
        except (ValueError, OSError):
            return False

    def check_bim(self, m: dict) -> None:
        if "bim_source" not in m:
            return
        from tee.architecture.service import ArchitectureService

        b = m["bim_source"]
        from tee.architecture.model import ArchitectureError

        try:
            doc = ArchitectureService(self.project).state(b["model_id"])
        except ArchitectureError as exc:
            fail(f"Linked architectural source is unavailable: {exc}")
        if doc["revision"] != b["revision"] or fingerprint(doc) != b["document_sha256"]:
            fail(
                "Linked architectural document changed; review and relink the "
                "structural study before solve."
            )

    def from_bim(
        self, model_id: str, entity_ids: list[str], offset: int = 0, limit: int = 10
    ) -> dict:
        from tee.architecture.members import frame, profile_shape
        from tee.architecture.service import ArchitectureService

        if (
            not isinstance(entity_ids, list)
            or not 1 <= len(entity_ids) <= 50
            or not all(isinstance(i, str) for i in entity_ids)
            or len(set(entity_ids)) != len(entity_ids)
        ):
            fail("Select 1..50 distinct member entity IDs.")
        doc = ArchitectureService(self.project).state(model_id)
        entities = doc["entities"]
        if isinstance(entities, list):
            entities = {e["id"]: e for e in entities}
        result = []
        for ident in entity_ids:
            e = entities.get(ident, {})
            if e.get("kind") != "member" or e.get("role") not in (
                "beam",
                "column",
                "brace",
                "frame",
            ):
                fail(
                    "Select explicit beam/column/brace/frame members, not roof surfaces or meshes."
                )
            x, y, z = frame(e)
            c = profile_shape(e).centroid
            origin = list(e["origin"])
            origin[2] += entities[e["storey"]]["elevation"]
            a = [origin[j] + x[j] * c.x + y[j] * c.y for j in range(3)]
            b = [a[j] + z[j] * e["length"] for j in range(3)]
            result.append(
                {
                    "entity_id": ident,
                    "centroid_axis_start_mm": a,
                    "centroid_axis_end_mm": b,
                    "geometric_area_mm2": profile_shape(e).area,
                    "role": e["role"],
                }
            )
        selected = page(result, offset, limit)
        return {
            "bim_source": {
                "model_id": model_id,
                "revision": doc["revision"],
                "document_sha256": fingerprint(doc),
            },
            "members": selected["rows"],
            "page": selected["page"],
            "state": "geometry_candidate_only",
            "required": [
                "explicit analysis plane and node connectivity",
                "material and structural section properties",
                "supports, loads and combination factors",
            ],
            "automatically_merged_nodes": False,
        }


def page(values: list, offset: int, limit: int) -> dict:
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 50:
        fail("offset must be nonnegative; limit must be 1..50.")
    selected = values[offset : offset + limit]
    return {
        "rows": selected,
        "page": {
            "offset": offset,
            "returned": len(selected),
            "total": len(values),
            "next_offset": offset + limit if offset + limit < len(values) else None,
        },
    }
