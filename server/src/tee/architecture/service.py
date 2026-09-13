"""Project-owned persistence and shared operations for TEE and the optional GUI."""

from __future__ import annotations

import json
import os
import re
import threading
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .model import ArchitectureError, Document

MAX_STATE_BYTES = 32 * 1024 * 1024
_MODEL_ID = re.compile(r"building_[a-f0-9]{16}\Z")
_IMPORT_ID = re.compile(r"import_[a-f0-9]{16}\Z")


def _fail(code: str, message: str) -> None:
    raise ArchitectureError(code, message)


def _check_cancel(cancelled: Callable[[], bool] | None) -> None:
    if cancelled is not None and cancelled():
        _fail("architecture_cancelled", "Operation cancelled before publishing its result.")


def _plain_path(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink():
            _fail("architecture_path", "Symbolic links are not supported for model state.")
    if path.exists() and path.is_file() and path.stat().st_nlink != 1:
        _fail("architecture_path", "Hard-linked state or input files are not supported.")


def _read(path: Path, limit: int = MAX_STATE_BYTES) -> dict[str, Any]:
    _plain_path(path)
    try:
        if not path.is_file() or path.stat().st_size > limit:
            _fail("architecture_file", "File is missing or exceeds the operation's size limit.")
        with path.open("rb") as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            _fail("architecture_file", "File exceeds the operation's size limit.")
        value = json.loads(raw)
    except (OSError, ValueError) as exc:
        if isinstance(exc, ArchitectureError):
            raise
        _fail("architecture_file", f"Cannot read architectural JSON: {type(exc).__name__}.")
    if not isinstance(value, dict):
        _fail("architecture_file", "Expected a JSON object.")
    return value


def _write(path: Path, value: dict[str, Any]) -> None:
    _plain_path(path)
    data = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
    if len(data) > MAX_STATE_BYTES:
        _fail("architecture_limit", "Document exceeds the 32 MiB persisted-state limit.")
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def compact_house() -> list[dict[str, Any]]:
    """Explicit example dimensions, never a pre-approved building or hardware design."""
    entities: list[dict[str, Any]] = [
        {"id": "ground", "kind": "storey", "name": "Ground floor", "elevation": 0, "height": 2800},
    ]
    for name, start, end in (
        ("south", [0, 0], [10000, 0]),
        ("east", [10000, 0], [10000, 8000]),
        ("north", [10000, 8000], [0, 8000]),
        ("west", [0, 8000], [0, 0]),
        ("partition", [6000, 0], [6000, 8000]),
    ):
        entities.append(
            {
                "id": name,
                "kind": "wall",
                "name": name.title(),
                "storey": "ground",
                "start": start,
                "end": end,
                "thickness": 200,
                "height": 2800,
            }
        )
    entities += [
        {
            "id": "entrance",
            "kind": "opening",
            "name": "Entrance",
            "wall": "south",
            "offset": 1200,
            "width": 1000,
            "height": 2200,
            "sill": 0,
            "fill": "door",
        },
        {
            "id": "internal_door",
            "kind": "opening",
            "name": "Internal door",
            "wall": "partition",
            "offset": 3200,
            "width": 900,
            "height": 2100,
            "sill": 0,
            "fill": "door",
        },
        {
            "id": "east_window",
            "kind": "opening",
            "name": "East window",
            "wall": "east",
            "offset": 2400,
            "width": 1800,
            "height": 1200,
            "sill": 900,
            "fill": "window",
        },
        {
            "id": "west_window",
            "kind": "opening",
            "name": "West window",
            "wall": "west",
            "offset": 2800,
            "width": 1800,
            "height": 1200,
            "sill": 900,
            "fill": "window",
        },
        {
            "id": "living",
            "kind": "space",
            "name": "Living room",
            "storey": "ground",
            "polygon": [[100, 100], [5900, 100], [5900, 7900], [100, 7900]],
            "height": 2800,
        },
        {
            "id": "room",
            "kind": "space",
            "name": "Room",
            "storey": "ground",
            "polygon": [[6100, 100], [9900, 100], [9900, 7900], [6100, 7900]],
            "height": 2800,
        },
        {
            "id": "floor",
            "kind": "slab",
            "name": "Ground slab",
            "storey": "ground",
            "polygon": [[-100, -100], [10100, -100], [10100, 8100], [-100, 8100]],
            "thickness": 150,
        },
        {
            "id": "roof",
            "kind": "roof",
            "name": "Flat roof",
            "storey": "ground",
            "base_height": 2800,
            "polygon": [[-300, -300], [10300, -300], [10300, 8300], [-300, 8300]],
            "thickness": 200,
        },
        {
            "id": "cabinet",
            "kind": "cabinet",
            "name": "Base cabinet",
            "storey": "ground",
            "origin": [500, 500, 0],
            "width": 900,
            "depth": 600,
            "height": 900,
            "panel_thickness": 18,
            "back_thickness": 6,
            "shelves": 1,
            "doors": 2,
            "plinth_height": 100,
            "grain": "height",
            "edge_band_mm": 0,
            "material": "Generic sheet; specify grade before manufacture",
            "properties": {"door_gap_mm": 2},
        },
    ]
    return [{"op": "create", "entity": entity} for entity in entities]


class ArchitectureService:
    def __init__(self, project: Path | str) -> None:
        self.project = Path(project).resolve()
        self.root = self.project / ".tee/architecture"
        self._mutex = threading.RLock()

    def _folder(self, model_id: str) -> Path:
        if not isinstance(model_id, str) or not _MODEL_ID.fullmatch(model_id):
            _fail("architecture_id", "Use a model_id returned by ak_create or ak_status.")
        folder = self.root / model_id
        _plain_path(folder)
        if not folder.is_dir():
            _fail("architecture_missing", "The architectural model does not exist in this project.")
        return folder

    @contextmanager
    def _locked(self) -> Iterator[None]:
        with self._mutex:
            _plain_path(self.root)
            self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
            lock = self.root / ".lock"
            _plain_path(lock)
            fd = os.open(lock, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
            try:
                if os.name == "nt":
                    import msvcrt

                    if os.fstat(fd).st_size == 0:
                        os.write(fd, b"\0")
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
                    try:
                        yield
                    finally:
                        os.lseek(fd, 0, os.SEEK_SET)
                        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def status(self) -> dict[str, Any]:
        _plain_path(self.root)
        models = []
        if self.root.is_dir():
            for folder in sorted(self.root.glob("building_*"))[:100]:
                try:
                    doc = Document.from_dict(_read(self._folder(folder.name) / "document.json"))
                    models.append({"model_id": folder.name, **doc.summary()})
                except ArchitectureError:
                    models.append(
                        {
                            "model_id": folder.name,
                            "error": "Unreadable model; inspect its saved document.",
                        }
                    )
        return {
            "ok": True,
            "product": "archkiln",
            "version": "0.1.0",
            "models": models,
            "units": "mm",
            "gui": "optional; ak_open",
            "jurisdiction_coverage": "explicit rule packs; unverified until assessed",
        }

    def create(self, name: str, preset: str = "empty") -> dict[str, Any]:
        if not isinstance(preset, str) or preset not in {
            "empty",
            "compact-house",
            "compact-dwelling",
        }:
            _fail("architecture_preset", "Choose empty, compact-house or compact-dwelling.")
        doc = Document.create(name)
        if preset == "compact-house":
            doc.apply(
                [
                    {
                        "op": "project",
                        "changes": {"facts": {"wall_join_policy": "orthogonal_butt_v1"}},
                    },
                    *compact_house(),
                ]
            )
        if preset == "compact-dwelling":
            from .templates import compact_dwelling

            doc.apply(compact_dwelling())
        with self._locked():
            model_id = "building_" + uuid.uuid4().hex[:16]
            folder = self.root / model_id
            folder.mkdir(mode=0o700)
            _write(folder / "document.json", doc.to_dict())
        return {
            "ok": True,
            "model_id": model_id,
            **doc.summary(),
            "preset": preset,
            "note": "Example geometry has no regulatory or fabrication approval.",
        }

    def state(self, model_id: str) -> dict[str, Any]:
        # Atomic replacement gives readers one complete revision without writing
        # a lock file or creating state through a read-tier tool.
        doc = Document.from_dict(_read(self._folder(model_id) / "document.json"))
        result = doc.to_dict()
        result.pop("history", None)
        return result

    def query(
        self,
        model_id: str,
        entity_id: str | None = None,
        detail: str = "entity",
        stock: dict[str, Any] | None = None,
        offset: int = 0,
        limit: int | None = None,
        kind: str | None = None,
        collection: str | None = None,
    ) -> dict[str, Any]:
        if (
            not isinstance(detail, str)
            or detail
            not in {
                "entity",
                "cabinet",
                "bim",
                "quality",
                "schedules",
                "performance",
                "distribution",
                "thermal",
            }
            or (stock is not None and detail != "cabinet")
        ):
            _fail(
                "architecture_query",
                "Choose entity, cabinet, bim, quality, schedules, performance, distribution "
                "or thermal. "
                "Stock needs cabinet detail.",
            )
        if detail == "cabinet" and entity_id is None:
            _fail("architecture_query", "Cabinet detail requires an entity_id.")
        reports = {
            "schedules": (
                "openings",
                "rooms",
                "walls",
                "cabinets",
                "roofs",
                "stairs",
                "slabs",
                "slab_openings",
                "virtual_boundaries",
                "members",
            ),
            "bim": (
                "types",
                "materials",
                "instances",
                "unconstructed_fillings",
                "information_gaps",
            ),
            "quality": ("issues", "portals", "room_access"),
            "performance": ("spaces", "routes"),
            "distribution": ("systems", "ports", "connections"),
            "thermal": ("surfaces", "assemblies", "zones", "spaces"),
        }
        if limit is None:
            limit = 5 if detail in reports else 100
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 100:
            _fail("architecture_query", "Use offset >= 0 and limit from 1 to 100.")
        if kind is not None and (not isinstance(kind, str) or not kind):
            _fail("architecture_query", "kind must be a nonempty entity kind.")
        if detail in reports and entity_id is not None:
            _fail("architecture_query", "Model reports apply to the whole model.")
        if kind is not None and (detail != "entity" or entity_id is not None):
            _fail("architecture_query", "kind applies to the entity index only.")
        if detail in reports:
            if collection is None:
                collection = reports[detail][0]
            if not isinstance(collection, str) or collection not in reports[detail]:
                _fail(
                    "architecture_query",
                    f"For {detail}, choose collection from {', '.join(reports[detail])}.",
                )
        elif collection is not None:
            _fail(
                "architecture_query",
                "collection applies to a model report detail.",
            )
        elif (offset or limit != 100) and entity_id is not None:
            _fail("architecture_query", "Pagination applies to an index or model report.")
        state = self.state(model_id)
        if detail in reports:
            from .bim import bim_report
            from .quality import review, schedules

            if detail in {"schedules", "performance", "distribution", "thermal"}:
                from .distribution import report as distribution_report
                from .performance import evaluate
                from .thermal import report as thermal_report

                report = (
                    schedules(state)
                    if detail == "schedules"
                    else evaluate(state)
                    if detail == "performance"
                    else distribution_report(state)
                    if detail == "distribution"
                    else thermal_report(state)
                )
                collections = {name: report.pop(name) for name in reports[detail]}
                counts = {name: len(rows) for name, rows in collections.items()}
                rows = collections[collection][offset : offset + limit]
            elif detail == "bim":
                report = bim_report(state)
                library = state["project"]["facts"].get("bim", {})
                collections = {
                    name: [
                        {"id": key, **value} for key, value in sorted(library.get(name, {}).items())
                    ]
                    for name in ("types", "materials")
                }
                collections["instances"] = sorted(
                    report.pop("instances"), key=lambda row: row["id"]
                )
                collections["unconstructed_fillings"] = [
                    {"id": value} for value in sorted(report.pop("unconstructed_fillings"))
                ]
                collections["information_gaps"] = report.pop("information_gaps")
                for name in ("types", "materials", "typed_instances"):
                    report.pop(name)
                counts = {name: len(rows) for name, rows in collections.items()}
                rows = collections[collection][offset : offset + limit]
            else:
                # The critic retains complete counts but slices issues at their
                # source; a model can produce more than its former 500-row cap.
                report = review(
                    state,
                    max_issues=limit if collection == "issues" else 1,
                    issue_offset=offset if collection == "issues" else 0,
                )
                access = report.pop("room_access")
                collections = {
                    "portals": sorted(access["portals"], key=lambda row: row["door"]),
                    "room_access": sorted(
                        [
                            {"id": identifier, "status": status}
                            for status in ("reachable", "unverified")
                            for identifier in access[status]
                        ],
                        key=lambda row: row["id"],
                    ),
                }
                counts = {name: len(values) for name, values in collections.items()}
                counts["issues"] = report.pop("issue_count")
                issues = report.pop("issues")
                rows = (
                    issues
                    if collection == "issues"
                    else collections[collection][offset : offset + limit]
                )
                report["severity_counts"] = report.pop("counts")
                report["room_access_counts"] = {
                    name: len(access[name]) for name in ("reachable", "unverified")
                }
                for name in ("truncated", "issue_offset", "next_issue_offset"):
                    report.pop(name)
            total = counts[collection]
            report.update(
                collection=collection,
                counts=counts,
                rows=rows,
                page={
                    "offset": offset,
                    "limit": limit,
                    "returned": len(rows),
                    "total": total,
                    "next_offset": offset + len(rows) if offset + len(rows) < total else None,
                },
            )
            return {
                "ok": True,
                "model_id": model_id,
                "revision": state["revision"],
                detail: report,
            }
        if entity_id is None:
            doc = Document.from_dict(state)
            rows = [
                row for row in state["entities"].values() if kind is None or row["kind"] == kind
            ]
            return {
                "ok": True,
                "model_id": model_id,
                **doc.summary(),
                "entities": [
                    {"id": row["id"], "kind": row["kind"], "name": row.get("name", "")}
                    for row in rows[offset : offset + limit]
                ],
                "truncated": offset + limit < len(rows),
                "total": len(rows),
                "offset": offset,
                "next_offset": offset + limit if offset + limit < len(rows) else None,
            }
        if entity_id not in state["entities"]:
            _fail("architecture_entity", "Entity not found; query the model's entity index.")
        result = {
            "ok": True,
            "model_id": model_id,
            "revision": state["revision"],
            "entity": state["entities"][entity_id],
        }
        if detail == "cabinet":
            from .cabinets import nest, panels, schedule

            result["schedule"] = schedule(result["entity"])
            if stock is not None:
                if (
                    not isinstance(stock, dict)
                    or set(stock)
                    - {
                        "sheet_width",
                        "sheet_height",
                        "kerf",
                        "allow_rotate",
                        "algorithm",
                        "trim_mm",
                    }
                    or not {"sheet_width", "sheet_height", "kerf"} <= set(stock)
                ):
                    _fail("architecture_stock", "Supply sheet_width, sheet_height and kerf in mm.")
                result["nesting"] = nest(panels(result["entity"]), **stock)
        return result

    def edit(
        self, model_id: str, operations: list[dict[str, Any]], expected_revision: int | None = None
    ) -> dict[str, Any]:
        with self._locked():
            path = self._folder(model_id) / "document.json"
            doc = Document.from_dict(_read(path))
            diff = doc.apply(operations, expected_revision=expected_revision)
            _write(path, doc.to_dict())
        return {"ok": True, "model_id": model_id, **diff}

    def undo(self, model_id: str, expected_revision: int | None = None) -> dict[str, Any]:
        with self._locked():
            path = self._folder(model_id) / "document.json"
            doc = Document.from_dict(_read(path))
            diff = doc.undo(expected_revision=expected_revision)
            _write(path, doc.to_dict())
        return {"ok": True, "model_id": model_id, **diff}

    def input_path(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative or len(relative) > 1024:
            _fail("architecture_path", "Provide a project-relative file path.")
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or "\\" in relative or "\x00" in relative:
            _fail("architecture_path", "Use a contained project-relative path without traversal.")
        target = self.project / path
        _plain_path(target)
        if not target.is_file() or not target.resolve().is_relative_to(self.project):
            _fail("architecture_path", "The selected input is not a regular file in this project.")
        return target

    def import_source(
        self,
        model_id: str,
        path: str,
        units: str,
        tolerance_mm: float,
        transform: list[list[float]] | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        from .imports import inspect_source, propose

        self._folder(model_id)
        source = inspect_source(self.input_path(path), units=units, transform=transform)
        proposal = propose(source, tolerance_mm=tolerance_mm)
        _check_cancel(cancelled)
        import_id = "import_" + uuid.uuid4().hex[:16]
        bundle = {"import_id": import_id, "source": source, "proposal": proposal}
        with self._locked():
            _check_cancel(cancelled)
            folder = self._folder(model_id) / "imports"
            _plain_path(folder)
            folder.mkdir(exist_ok=True, mode=0o700)
            _write(folder / (import_id + ".json"), bundle)
        return {
            "ok": True,
            "model_id": model_id,
            "import_id": import_id,
            "candidates": len(proposal.get("candidates", [])),
            "applied": False,
            "next": "ak_candidates then ak_promote with explicit construction dimensions",
        }

    def candidates(self, model_id: str, import_id: str) -> dict[str, Any]:
        if not isinstance(import_id, str) or not _IMPORT_ID.fullmatch(import_id):
            _fail("architecture_import", "Use an import_id returned by ak_import.")
        return _read(self._folder(model_id) / "imports" / (import_id + ".json"), 4 * 1024 * 1024)

    def promote(
        self,
        model_id: str,
        import_id: str,
        candidate_id: str,
        storey: str,
        overrides: dict[str, Any],
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        from .imports import promotion

        bundle = self.candidates(model_id, import_id)
        candidates = bundle["proposal"].get("candidates", [])
        selected = next((c for c in candidates if c.get("id") == candidate_id), None)
        if selected is None:
            _fail("architecture_candidate", "Candidate not found in this import.")
        source_path = selected.get("provenance", {}).get("source_path")
        if not isinstance(source_path, str):
            _fail("architecture_source", "Candidate has no retained source path; import it again.")
        try:
            relative = Path(source_path).relative_to(self.project)
        except ValueError:
            _fail("architecture_path", "Candidate source is outside the connected project.")
        self.input_path(str(relative))
        operation = promotion(selected, storey, overrides)
        return self.edit(model_id, [operation], expected_revision)

    def check(
        self, model_id: str, pack_paths: list[str] | None = None, assessment_date: str | None = None
    ) -> dict[str, Any]:
        from .bim import bim_report
        from .exchange import validate_geometry_policy
        from .quality import review
        from .rules import assess

        paths = pack_paths or []
        if len(paths) > 32:
            _fail("architecture_rules", "Assess at most 32 explicit rule packs at a time.")
        packs = [_read(self.input_path(path), 1024 * 1024) for path in paths]
        state = self.state(model_id)
        validation = Document.from_dict(state).validate()
        return {
            "model_id": model_id,
            "revision": state["revision"],
            "model_validation": validation,
            "geometry": validate_geometry_policy(state),
            "bim": bim_report(state),
            "design_review": review(state, max_issues=20),
            "regulatory": assess(state, packs, assessment_date),
        }

    def export(
        self,
        model_id: str,
        format: str = "all",
        cancelled: Callable[[], bool] | None = None,
        cabinet_id: str | None = None,
        cnc_setup: dict[str, Any] | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        if not isinstance(format, str) or format not in {
            "all",
            "ifc",
            "drawings",
            "glb",
            "json",
            "cabinet_cnc",
        }:
            _fail("architecture_export", "Choose all, ifc, drawings, glb, json or cabinet_cnc.")
        if format != "cabinet_cnc" and (cabinet_id is not None or cnc_setup is not None):
            _fail("architecture_export", "cabinet_id and cnc_setup only apply to cabinet_cnc.")
        state = self.state(model_id)
        Document.from_dict(state)._revision_check(expected_revision)
        if format == "cabinet_cnc" and type(expected_revision) is not int:
            _fail("architecture_cnc", "Virtual CNC export requires the reviewed expected_revision.")
        virtual_job = None
        if format == "cabinet_cnc":
            from .cabinet_cnc import plan_job

            if (
                not isinstance(cabinet_id, str)
                or state["entities"].get(cabinet_id, {}).get("kind") != "cabinet"
            ):
                _fail(
                    "architecture_cnc",
                    "Select an existing cabinet_id and provide explicit cnc_setup.",
                )
            virtual_job = plan_job(state["entities"][cabinet_id], cnc_setup)
        _check_cancel(cancelled)
        export_root = self.project / "output/archkiln" / model_id
        _plain_path(export_root)
        export_root.mkdir(parents=True, exist_ok=True)
        folder = export_root / (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        )
        folder.mkdir()
        report: dict[str, Any] = {
            "ok": True,
            "model_id": model_id,
            "revision": state["revision"],
            "directory": str(folder),
            "regulatory_status": "not_verified",
        }
        _write(folder / "document.json", state)
        if "thermal" in state["project"]["facts"]:
            from .thermal import report as thermal_report

            _write(folder / "thermal-scenario.json", thermal_report(state))
            report["thermal_report"] = str(folder / "thermal-scenario.json")
        if virtual_job is not None:
            _write(folder / "virtual-cnc-job.json", virtual_job)
            (folder / "program.virtual.nc.txt").write_text(virtual_job["program"], encoding="utf-8")
            report["cabinet_cnc"] = {
                "cabinet_id": cabinet_id,
                "job_path": str(folder / "virtual-cnc-job.json"),
                "program_path": str(folder / "program.virtual.nc.txt"),
                **{
                    key: virtual_job[key]
                    for key in ("input_sha256", "program_sha256", "simulation", "readiness")
                },
            }
        if format in {"all", "drawings"}:
            from .quality import review, schedules

            _write(folder / "schedules.json", schedules(state))
            design_review = review(state)
            _write(folder / "design-review.json", design_review)
            report["design_review"] = {
                "issue_count": design_review["issue_count"],
                "counts": design_review["counts"],
                "path": str(folder / "design-review.json"),
            }
            report["schedules"] = str(folder / "schedules.json")
            if "distribution" in state["project"]["facts"]:
                from .distribution import report as distribution_report

                _write(folder / "distribution.json", distribution_report(state))
                report["distribution_report"] = str(folder / "distribution.json")
            if "performance" in state["project"]["facts"]:
                from .performance import evaluate

                _write(folder / "design-performance.json", evaluate(state))
                report["performance"] = str(folder / "design-performance.json")
        if format in {"all", "ifc"}:
            from .exchange import export_ifc, validate_ifc

            report["ifc"] = export_ifc(state, folder / "building.ifc")
            report["ifc_validation"] = validate_ifc(folder / "building.ifc")
            _check_cancel(cancelled)
        if format in {"all", "drawings"}:
            from .drawings import export_drawings

            report["drawings"] = export_drawings(state, folder)
            _check_cancel(cancelled)
        if format in {"all", "glb"}:
            from .exchange import export_glb

            report["glb"] = export_glb(state, folder / "building.glb")
        _check_cancel(cancelled)
        _write(folder / "manifest.json", report)
        return report

    def preview(self, model_id: str) -> dict[str, Any]:
        from .drawings import drawing_index
        from .exchange import preview

        state = self.state(model_id)
        return {**preview(state), "available_drawings": drawing_index(state)}

    def drawing(self, model_id: str, view_name: str) -> dict[str, Any]:
        """One read-only coordinated drawing, shared with IFC/shop export views."""
        from .drawings import drawing_view

        state = self.state(model_id)
        return {
            "model_id": model_id,
            "revision": state["revision"],
            "view": drawing_view(state, view_name),
        }

    def _ifc_reference(self, model_id: str, reference_id: str) -> dict[str, Any]:
        import hashlib

        if not isinstance(reference_id, str) or not re.fullmatch(r"ifc_[a-f0-9]{16}", reference_id):
            _fail("architecture_ifc", "Use a reference_id returned by ak_ifc_reference.")
        folder = self._folder(model_id) / "references" / reference_id
        manifest = _read(folder / "reference.json", 1024 * 1024)
        source = folder / "source.ifc"
        _plain_path(source)
        if (
            manifest.get("reference_id") != reference_id
            or not isinstance(manifest.get("source"), dict)
            or manifest["source"].get("path") != str(source)
            or not source.is_file()
        ):
            _fail("architecture_ifc", "Stored IFC reference identity/path is inconsistent.")
        if source.stat().st_size > 64 * 1024 * 1024:
            _fail("architecture_ifc", "Retained IFC exceeds the supported 64 MiB limit.")
        with source.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != manifest["source"].get("sha256") or reference_id != "ifc_" + digest[:16]:
            _fail(
                "architecture_ifc",
                "Retained IFC source has changed; create a new reviewed reference.",
            )
        return manifest

    def _attached_ifc_reference(
        self, model_id: str, reference_id: str, metadata: Any
    ) -> dict[str, Any]:
        reference = self._ifc_reference(model_id, reference_id)
        if not isinstance(metadata, dict) or any(
            metadata.get(key) != reference["source"].get(key) for key in ("sha256", "schema")
        ):
            _fail(
                "architecture_ifc",
                "Attached IFC reference metadata differs from its retained source identity; "
                "reattach the reviewed reference.",
            )
        return reference

    def ifc_reference(
        self,
        model_id: str,
        path: str,
        expected_revision: int | None = None,
        expected_sha256: str | None = None,
        cancelled: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        from .ifc_interop import inspect_ifc, prepare_ifc_reference

        source = self.input_path(path)
        inspected = inspect_ifc(source, limit=1)
        digest = inspected["source"]["sha256"]
        if expected_sha256 is not None and digest != expected_sha256:
            _fail("architecture_ifc", "IFC checksum differs from the reviewed source.")
        reference_id = "ifc_" + digest[:16]
        with self._locked():
            folder = self._folder(model_id)
            document = Document.from_dict(_read(folder / "document.json"))
            document._revision_check(expected_revision)
            _check_cancel(cancelled)
            destination = folder / "references" / reference_id
            _plain_path(destination)
            if destination.exists():
                retained = self._ifc_reference(model_id, reference_id)
            else:
                retained = prepare_ifc_reference(source, destination, digest)
            if retained["source"]["sha256"] != digest:
                _fail(
                    "architecture_ifc", "Reference identifier collision; source checksums differ."
                )
            facts = document.to_dict()["project"]["facts"]
            references = facts.setdefault("ifc_references", {})
            if not isinstance(references, dict):
                _fail("architecture_ifc", "project.facts.ifc_references must be a mapping.")
            references[reference_id] = {
                "sha256": digest,
                "schema": retained["source"]["schema"],
                "editing": "immutable_reference",
                "original_project_path": path,
            }
            _check_cancel(cancelled)
            diff = document.apply(
                [{"op": "project", "changes": {"facts": facts}}], expected_revision
            )
            _write(folder / "document.json", document.to_dict())
        return {
            "ok": True,
            "model_id": model_id,
            "reference_id": reference_id,
            **diff,
            "source": {key: value for key, value in retained["source"].items() if key != "path"},
            "native_entities_created": 0,
            "next": "Inspect reference; review supported candidates before native edits.",
        }

    def ifc_query(
        self,
        model_id: str,
        reference_id: str,
        detail: str = "index",
        offset: int = 0,
        limit: int = 50,
        guids: list[str] | None = None,
    ) -> dict[str, Any]:
        from .ifc_interop import inspect_ifc, native_candidates

        if not isinstance(detail, str) or detail not in {"index", "full", "native"}:
            _fail("architecture_ifc", "Choose index, full or native IFC detail.")
        state = self.state(model_id)
        references = state["project"]["facts"].get("ifc_references", {})
        if not isinstance(references, dict) or reference_id not in references:
            _fail("architecture_ifc", "Reference is not attached to the current model revision.")
        manifest = self._attached_ifc_reference(model_id, reference_id, references[reference_id])
        source = Path(manifest["source"]["path"])
        result = (
            native_candidates(source, guids=guids)
            if detail == "native"
            else inspect_ifc(
                source,
                offset=offset,
                limit=limit,
                include_details=detail == "full",
                geometry_guids=guids,
            )
        )
        return {
            "ok": True,
            "model_id": model_id,
            "reference_id": reference_id,
            "revision": state["revision"],
            "detail": detail,
            "result": result,
        }

    def ifc_ids(
        self,
        model_id: str,
        reference_id: str,
        ids_path: str,
        cancelled: Callable[[], bool] | None = None,
    ) -> dict[str, Any]:
        from .ifc_interop import assess_ids

        state = self.state(model_id)
        references = state["project"]["facts"].get("ifc_references", {})
        if not isinstance(references, dict) or reference_id not in references:
            _fail("architecture_ifc", "Reference is not attached to the current model revision.")
        reference = self._attached_ifc_reference(model_id, reference_id, references[reference_id])
        _check_cancel(cancelled)
        result = assess_ids(Path(reference["source"]["path"]), self.input_path(ids_path))
        _check_cancel(cancelled)
        return {
            "ok": True,
            "model_id": model_id,
            "revision": state["revision"],
            "reference_id": reference_id,
            "assessment": result,
        }

    def ifc_federate(
        self,
        model_id: str,
        reference_ids: list[str],
        transforms_mm: dict[str, Any],
        cancelled: Callable[[], bool] | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, Any]:
        from .ifc_interop import federation_manifest

        if (
            not isinstance(reference_ids, list)
            or not 1 <= len(reference_ids) <= 16
            or any(not isinstance(value, str) for value in reference_ids)
        ):
            _fail("architecture_ifc", "Specify one to sixteen reference IDs.")
        state = self.state(model_id)
        Document.from_dict(state)._revision_check(expected_revision)
        attached = state["project"]["facts"].get("ifc_references", {})
        if not isinstance(attached, dict) or any(value not in attached for value in reference_ids):
            _fail("architecture_ifc", "Federate only references attached to this model revision.")
        references = [
            self._attached_ifc_reference(model_id, value, attached[value])
            for value in reference_ids
        ]
        _check_cancel(cancelled)
        federation = federation_manifest(references, transforms_mm=transforms_mm)
        _check_cancel(cancelled)
        folder = (
            self.project / "output/archkiln" / model_id / ("federation-" + uuid.uuid4().hex[:16])
        )
        _plain_path(folder)
        folder.mkdir(parents=True)
        _write(folder / "federation.json", federation)
        return {
            "ok": True,
            "model_id": model_id,
            "revision": state["revision"],
            "references": reference_ids,
            "manifest_path": str(folder / "federation.json"),
            "native_authoring": "reference_only",
            "regulatory": "not_verified",
        }
