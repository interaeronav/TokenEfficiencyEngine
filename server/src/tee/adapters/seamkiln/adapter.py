"""SeamkilnAdapter: garments as a TEE scene, with zero new always-loaded tools.

The whole point of the Adapter protocol is that `tee_scene_summary`,
`tee_batch`, `tee_diff`, the checkpoint machinery and `tee_capture` already
know how to drive *a scene*. A garment is a scene: panels and seams are
entities with stable ids, an edit is a batch, and what changed is a diff. So
seamkiln joins TEE without moving the 17-tool surface at all.

Operations are DECLARATIVE and enumerable, the trade-rule lesson from A49:
`create`, `set`, `delete` plus a named, closed set of garment verbs. There is
no "run arbitrary Python" door here; the escape hatch is seamkiln's own
library, reached by a caller who already has code execution.

seamkiln is an OPTIONAL dependency. Absent, every entry point refuses with
the install command rather than failing on an import line halfway through a
batch.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from tee.kernel.adapter import AdapterInfo, Diff, Entity
from tee.kernel.errors import TeeError

INSTALL_HINT = (
    "seamkiln is not installed. From the repo root: "
    "uv pip install --python <this interpreter> -e seamkiln"
)
BUILTIN_BLOCKS = ("tee",)
DEFAULT_PARTICLE_MM = 15.0


def _need_seamkiln():
    try:
        import seamkiln  # noqa: F401
    except ImportError as exc:
        raise TeeError("seamkiln_unavailable", INSTALL_HINT, fix=INSTALL_HINT) from exc


class SeamkilnAdapter:
    """A pattern, optionally arranged on a body and draped."""

    def __init__(self, project_root: str | Path = ".", *, workdir: str | Path | None = None):
        self.project_root = Path(project_root)
        self.workdir = Path(workdir or (self.project_root / ".tee" / "seamkiln"))
        self._pattern = None  # seamkiln.pattern.model.Pattern
        self._body = None  # trimesh.Trimesh
        self._body_spec: dict[str, Any] = {}
        self._sdf = None
        self._garment = None  # GarmentMesh
        self._drape = None  # DrapeResult
        self._fabric = "cotton_jersey"
        self._epoch = 0

    # -- Adapter protocol ---------------------------------------------------

    def info(self) -> AdapterInfo:
        try:
            _need_seamkiln()
            import seamkiln

            version = getattr(seamkiln, "__version__", "0.1.0.dev0")
            connected = True
        except TeeError:
            version = "absent"
            connected = False
        extra: dict[str, Any] = {
            "pattern": getattr(self._pattern, "name", None),
            "panels": len(self._pattern.panels) if self._pattern else 0,
            "seams": len(self._pattern.seams) if self._pattern else 0,
            "draped": self._drape is not None,
            "fabric": self._fabric,
        }
        if self._body_spec:
            extra["body"] = self._body_spec
        return AdapterInfo(
            id="seamkiln", product="seamkiln", version=version, connected=connected, extra=extra
        )

    def probe(self) -> bool:
        try:
            _need_seamkiln()
        except TeeError:
            return False
        return True

    def list_entities(self) -> list[Entity]:
        """Panels, seams and the garment - compact summaries, never geometry."""
        if self._pattern is None:
            return []
        from seamkiln.pattern.model import true_up

        entities: list[Entity] = []
        for panel in self._pattern.panels:
            minx, miny, maxx, maxy = panel.bbox
            entities.append(
                Entity(
                    id=f"panel:{panel.id}",
                    name=panel.name,
                    kind="panel",
                    summary={
                        "area_mm2": round(panel.area_mm2, 1),
                        "perimeter_mm": round(panel.perimeter_mm, 1),
                        "edges": len(panel.edges()),
                        "marks": len(panel.marks),
                        "internals": len(panel.internals),
                        "bbox_mm": [round(maxx - minx, 1), round(maxy - miny, 1)],
                        "seam_allowance_mm": panel.seam_allowance_mm,
                    },
                )
            )
        checks = {c.seam_id: c for c in true_up(self._pattern, tolerance_mm=0.0)}
        for seam in self._pattern.seams:
            check = checks.get(seam.id)
            entities.append(
                Entity(
                    id=f"seam:{seam.id}",
                    name=seam.id,
                    kind="seam",
                    summary={
                        "a": str(seam.a),
                        "b": str(seam.b),
                        "gather": seam.gather,
                        "mismatch_mm": check.mismatch_mm if check else None,
                    },
                )
            )
        if self._garment is not None:
            summary = dict(self._garment.summary())
            if self._drape is not None:
                summary.update(
                    {
                        "seam_gap_mean_mm": self._drape.seam_gaps.get("mean_gap_mm"),
                        "penetration_mm": self._drape.penetration.get("deepest_penetration_mm"),
                        "worn": self._drape.contact.get("worn"),
                        "fabric": self._drape.fabric,
                    }
                )
            entities.append(Entity(id="garment", name="garment", kind="garment", summary=summary))
        return entities

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        _need_seamkiln()
        diff = Diff()
        for index, op in enumerate(batch):
            verb = op.get("op")
            handler = _OPS.get(verb)
            if handler is None:
                raise TeeError(
                    "seamkiln_bad_op",
                    f"batch[{index}]: unknown op {verb!r}.",
                    fix=f"seamkiln accepts: {', '.join(sorted(_OPS))}.",
                )
            handler(self, op, index, diff)
        self._epoch += 1
        return diff

    def snapshot(self, label: str) -> dict[str, Any]:
        """Checkpoint the pattern and the drape. Spilled to disk, not inlined."""
        if self._pattern is None:
            return {"label": label, "empty": True}
        self.workdir.mkdir(parents=True, exist_ok=True)
        stamp = f"{label}-{self._epoch}-{int(time.time() * 1000)}"
        path = self.workdir / f"{stamp}.json"
        payload = {
            "pattern": _pattern_to_dict(self._pattern),
            "fabric": self._fabric,
            "body": self._body_spec,
        }
        if self._drape is not None and self._garment is not None:
            points = self.workdir / f"{stamp}.npy"
            import numpy as np

            np.save(points, self._drape.points)
            payload["drape"] = {
                "points": str(points),
                "particle_distance_mm": self._garment.particle_distance_mm,
                "fingerprint": self._drape.fingerprint,
            }
        path.write_text(json.dumps(payload))
        return {"label": label, "path": str(path), "epoch": self._epoch}

    def restore(self, payload: dict[str, Any]) -> None:
        if payload.get("empty"):
            self._pattern = None
            self._garment = None
            self._drape = None
            return
        path = Path(payload["path"])
        if not path.is_file():
            raise TeeError(
                "seamkiln_checkpoint_missing",
                f"checkpoint {path} is gone.",
                fix="Checkpoints live under .tee/seamkiln; tee_purge may have reclaimed it.",
            )
        data = json.loads(path.read_text())
        self._pattern = _pattern_from_dict(data["pattern"])
        self._fabric = data.get("fabric", self._fabric)
        self._body_spec = data.get("body", {})
        self._garment = None  # geometry is rebuilt from the pattern, never trusted stale
        self._drape = None
        self._epoch += 1

    def capture(self, view: str, max_bytes: int) -> bytes:
        """Render the garment through Blender, or refuse with the reason.

        Never a black rectangle and never a placeholder: A49's law. A garment
        that has not been draped has nothing to photograph, and saying so is
        more useful than an image of an empty room.
        """
        _need_seamkiln()
        if self._garment is None:
            raise TeeError(
                "seamkiln_nothing_to_capture",
                "no garment has been arranged yet, so there is nothing to render.",
                fix="Run the 'arrange' op (and usually 'drape') first.",
            )
        from seamkiln.drape import preview

        ok, why = preview.available()
        if not ok:
            raise TeeError(
                "seamkiln_no_renderer",
                f"seamkiln renders through Blender and {why}.",
                fix="Install Blender, or read the drape's numbers - seam gaps, "
                "penetration, contact and the fit report say more than a picture.",
            )
        points = self._drape.points if self._drape is not None else self._garment.points
        self.workdir.mkdir(parents=True, exist_ok=True)
        prefix = self.workdir / "capture"
        views = {"front": (0.0, 5.0), "side": (90.0, 5.0), "back": (180.0, 5.0)}
        chosen = view if view in views else "front"
        mesh = preview.garment_mesh(points, self._garment.triangles)

        # The same two-rung ladder the Blender adapter uses: try a useful
        # size, fall back to a small one, then refuse WITH THE NUMBERS rather
        # than hand back something over budget or silently truncated.
        last = 0
        for width, height in ((640, 800), (320, 400)):
            preview.render(
                prefix,
                garment=mesh,
                body=self._body,
                views={chosen: views[chosen]},
                width=width,
                height=height,
            )
            data = Path(f"{prefix}_{chosen}.png").read_bytes()
            last = len(data)
            if last <= max_bytes:
                return data
        raise TeeError(
            "seamkiln_capture_too_large",
            f"the smallest render is {last} bytes; the budget is {max_bytes}.",
            fix="Raise the budget, or read the drape report instead - seam gaps, "
            "penetration, contact and ease are a few hundred bytes.",
        )


# -- ops ---------------------------------------------------------------------


def _panel_id(raw: str) -> str:
    return raw.split(":", 1)[1] if raw.startswith("panel:") else raw


def _op_create(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    from seamkiln.pattern.geometry import Vertex, VertexKind
    from seamkiln.pattern.model import Panel, Pattern, Seam

    kind = op.get("kind")
    props = dict(op.get("props") or {})
    if adapter._pattern is None:
        adapter._pattern = Pattern(name=props.get("pattern") or "untitled")

    if kind == "panel":
        outline = props.get("outline")
        if not outline or len(outline) < 3:
            raise TeeError(
                "seamkiln_bad_panel",
                f"batch[{index}]: a panel needs an outline of at least 3 points.",
                fix="props.outline = [[x_mm, y_mm], ...] or "
                "[[x, y, 'turn'|'curve'], ...] to tag corners.",
            )
        vertices = [
            Vertex(
                float(point[0]),
                float(point[1]),
                VertexKind(point[2]) if len(point) > 2 else VertexKind.TURN,
            )
            for point in outline
        ]
        panel = Panel(id=op.get("name") or f"P{len(adapter._pattern.panels) + 1}", outline=vertices)
        adapter._pattern.panels.append(panel)
        entity = _panel_entity(panel)
        diff.created.append(entity.id)
        diff.details[entity.id] = entity.detailed()
        diff.upserts.append(entity)
    elif kind == "seam":
        seam = Seam(
            a=_edge_ref(props.get("a"), index),
            b=_edge_ref(props.get("b"), index),
            gather=float(props.get("gather", 1.0)),
            id=op.get("name") or "",
        )
        adapter._pattern.seams.append(seam)
        diff.created.append(f"seam:{seam.id}")
        diff.details[f"seam:{seam.id}"] = {"a": str(seam.a), "b": str(seam.b)}
    elif kind == "block":
        name = str(props.get("block") or "tee")
        if name not in BUILTIN_BLOCKS:
            raise TeeError(
                "seamkiln_unknown_block",
                f"batch[{index}]: no built-in block {name!r}.",
                fix=f"Built-in blocks: {', '.join(BUILTIN_BLOCKS)}.",
            )
        from seamkiln.pattern.fixtures import tee_block

        adapter._pattern = tee_block(**{k: float(v) for k, v in props.items() if k != "block"})
        for panel in adapter._pattern.panels:
            entity = _panel_entity(panel)
            diff.created.append(entity.id)
            diff.upserts.append(entity)
        diff.notes.append(
            f"block '{name}': {len(adapter._pattern.panels)} panels, "
            f"{len(adapter._pattern.seams)} seams"
        )
    else:
        raise TeeError(
            "seamkiln_bad_kind",
            f"batch[{index}]: cannot create kind {kind!r}.",
            fix="Kinds: panel, seam, block.",
        )


def _edge_ref(raw: Any, index: int):
    from seamkiln.pattern.model import EdgeRef

    if isinstance(raw, dict):
        return EdgeRef(
            panel=_panel_id(str(raw["panel"])),
            edge=int(raw["edge"]),
            t0=float(raw.get("t0", 0.0)),
            t1=float(raw.get("t1", 1.0)),
        )
    text = str(raw or "")
    if "#" not in text:
        raise TeeError(
            "seamkiln_bad_edge",
            f"batch[{index}]: {text!r} is not an edge reference.",
            fix='Use \'PANEL#3\', or {"panel": "FRONT", "edge": 3, "t0": 0, "t1": 0.5}.',
        )
    panel, edge = text.split("#", 1)
    return EdgeRef(panel=_panel_id(panel), edge=int(edge))


def _op_set(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    from seamkiln.pattern.allowance import add_seam_allowance

    panel = _require_panel(adapter, op, index)
    props = dict(op.get("props") or {})
    if "seam_allowance_mm" in props:
        grown = add_seam_allowance(panel, float(props["seam_allowance_mm"]))
        adapter._pattern.panels[adapter._pattern.panels.index(panel)] = grown
        panel = grown
    if "name" in props:
        panel.name = str(props["name"])
    entity = _panel_entity(panel)
    diff.modified.append(entity.id)
    diff.details[entity.id] = entity.detailed()
    diff.upserts.append(entity)


def _op_delete(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    panel = _require_panel(adapter, op, index)
    adapter._pattern.panels.remove(panel)
    adapter._pattern.seams = [
        s for s in adapter._pattern.seams if panel.id not in (s.a.panel, s.b.panel)
    ]
    diff.deleted.append(f"panel:{panel.id}")


def _op_arrange(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    from seamkiln.drape.body import mannequin, sdf_from_mesh
    from seamkiln.drape.garment import build_garment, top_arrangement

    if adapter._pattern is None or not adapter._pattern.panels:
        raise TeeError(
            "seamkiln_no_pattern",
            f"batch[{index}]: nothing to arrange - the pattern has no panels.",
            fix="Create panels, or a built-in block, first.",
        )
    props = dict(op.get("props") or {})
    kind = str(props.get("body", "mannequin")).lower()
    stature = float(props.get("stature_m", 1.75))
    if kind == "anny":
        from seamkiln.drape.anny_body import anny_body

        adapter._body = anny_body(
            stature_m=stature,
            **{
                k: float(v)
                for k, v in props.items()
                if k in ("gender", "age", "muscle", "weight", "height", "proportions")
            },
        )
    elif kind == "mannequin":
        adapter._body = mannequin(height=stature, chest=float(props.get("chest_m", 1.0)))
    else:
        raise TeeError(
            "seamkiln_unknown_body",
            f"batch[{index}]: no body kind {kind!r}.",
            fix="Bodies: 'anny' (parametric, Apache-2.0) or 'mannequin' (stand-in).",
        )
    adapter._body_spec = {"kind": kind, "stature_m": stature}
    voxel = float(props.get("voxel_mm", 8.0))
    adapter._sdf = sdf_from_mesh(adapter._body, voxel_mm=voxel)
    particle = float(props.get("particle_distance_mm", DEFAULT_PARTICLE_MM))
    adapter._garment = build_garment(
        adapter._pattern,
        top_arrangement(adapter._pattern, adapter._body),
        particle_distance=particle,
    )
    adapter._drape = None
    summary = adapter._garment.summary()
    diff.modified.append("garment")
    diff.details["garment"] = {**summary, "body": adapter._body_spec, "voxel_mm": voxel}
    diff.notes.append(
        f"arranged {summary['points']} points on a {kind} body; "
        f"{summary['seams_flipped']} seams auto-flipped"
    )


def _op_drape(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    from seamkiln.drape.solve import DrapeSettings, drape

    if adapter._garment is None or adapter._sdf is None:
        raise TeeError(
            "seamkiln_not_arranged",
            f"batch[{index}]: the garment has not been arranged on a body.",
            fix="Run {'op': 'arrange', 'props': {'body': 'anny'}} first.",
        )
    props = dict(op.get("props") or {})
    adapter._fabric = str(props.get("fabric", adapter._fabric))
    settings = DrapeSettings(
        frames=int(props.get("frames", 250)),
        substeps=int(props.get("substeps", 8)),
        friction=float(props.get("friction", 0.35)),
        thickness_mm=float(props.get("thickness_mm", 1.0)),
    )
    adapter._drape = drape(
        adapter._garment, adapter._sdf, fabric=adapter._fabric, settings=settings
    )
    diff.modified.append("garment")
    diff.details["garment"] = adapter._drape.report()
    if not adapter._drape.contact.get("worn"):
        diff.notes.append(
            "the garment is NOT being worn - it came off the body. Check the "
            "arrangement, the particle distance, or whether the pattern fits."
        )


def _op_export(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    props = dict(op.get("props") or {})
    fmt = str(props.get("format", "dxf")).lower()
    out = props.get("out")
    if not out:
        raise TeeError(
            "seamkiln_no_out",
            f"batch[{index}]: export needs props.out (a destination path).",
            fix="Set props.out to where the file should be written.",
        )
    if adapter._pattern is None:
        raise TeeError(
            "seamkiln_no_pattern",
            f"batch[{index}]: nothing to export.",
            fix="Create a pattern first.",
        )
    if fmt in ("dxf", "aama", "astm"):
        from seamkiln.pattern.dxf import write_dxf

        flavour = "aama" if fmt == "aama" else str(props.get("dialect", "astm"))
        result = write_dxf(adapter._pattern, out, flavour=flavour)
    elif fmt == "svg":
        from seamkiln.pattern import plot

        result = plot.to_svg(adapter._pattern, out)
    elif fmt == "pdf":
        from seamkiln.pattern import plot

        result = plot.to_pdf(adapter._pattern, out, page=str(props.get("page", "A4")))
    elif fmt in ("obj", "glb", "ply", "stl"):
        if adapter._garment is None:
            raise TeeError(
                "seamkiln_not_arranged",
                f"batch[{index}]: a 3D export needs a draped garment.",
                fix="Run 'arrange' and 'drape' first, or export dxf/svg/pdf for the flat pattern.",
            )
        from seamkiln.drape.preview import garment_mesh

        points = adapter._drape.points if adapter._drape else adapter._garment.points
        mesh = garment_mesh(points, adapter._garment.triangles)
        mesh.export(out)
        result = {"path": str(out), "format": fmt, "vertices": len(mesh.vertices)}
    else:
        raise TeeError(
            "seamkiln_bad_format",
            f"batch[{index}]: cannot export {fmt!r}.",
            fix="Formats: dxf (aama|astm), svg, pdf, obj, glb, ply, stl.",
        )
    diff.notes.append(f"exported {fmt}: {result.get('path')}")
    diff.details.setdefault("export", {}).update(result)
    diff.modified.append("export")


_OPS = {
    "create": _op_create,
    "set": _op_set,
    "delete": _op_delete,
    "arrange": _op_arrange,
    "drape": _op_drape,
    "export": _op_export,
}


def _require_panel(adapter: SeamkilnAdapter, op: dict, index: int):
    if adapter._pattern is None:
        raise TeeError(
            "seamkiln_no_pattern",
            f"batch[{index}]: there is no pattern.",
            fix="Create panels or a block first.",
        )
    target = _panel_id(str(op.get("id") or ""))
    for panel in adapter._pattern.panels:
        if panel.id == target:
            return panel
    known = ", ".join(f"panel:{p.id}" for p in adapter._pattern.panels) or "(none)"
    raise TeeError(
        "seamkiln_no_such_panel",
        f"batch[{index}]: no panel {op.get('id')!r}.",
        fix=f"Panels: {known}.",
    )


def _panel_entity(panel) -> Entity:
    minx, miny, maxx, maxy = panel.bbox
    return Entity(
        id=f"panel:{panel.id}",
        name=panel.name,
        kind="panel",
        summary={
            "area_mm2": round(panel.area_mm2, 1),
            "edges": len(panel.edges()),
            "bbox_mm": [round(maxx - minx, 1), round(maxy - miny, 1)],
        },
    )


# -- checkpoint serialisation -------------------------------------------------


def _pattern_to_dict(pattern) -> dict[str, Any]:
    return {
        "name": pattern.name,
        "units": pattern.units,
        "panels": [
            {
                "id": p.id,
                "name": p.name,
                "seam_allowance_mm": p.seam_allowance_mm,
                "outline": [[v.x, v.y, str(v.kind)] for v in p.outline],
                "marks": [
                    {
                        "kind": str(m.kind),
                        "x": m.x,
                        "y": m.y,
                        "depth": m.depth,
                        "diameter": m.diameter,
                    }
                    for m in p.marks
                ],
                "internals": [
                    {
                        "kind": str(i.kind),
                        "closed": i.closed,
                        "points": [[v.x, v.y, str(v.kind)] for v in i.points],
                    }
                    for i in p.internals
                ],
            }
            for p in pattern.panels
        ],
        "seams": [
            {
                "id": s.id,
                "a": _ref_to_dict(s.a),
                "b": _ref_to_dict(s.b),
                "gather": s.gather,
                "flip": s.flip,
            }
            for s in pattern.seams
        ],
    }


def _ref_to_dict(ref) -> dict[str, Any]:
    return {"panel": ref.panel, "edge": ref.edge, "t0": ref.t0, "t1": ref.t1}


def _pattern_from_dict(data: dict[str, Any]):
    from seamkiln.pattern.geometry import Vertex, VertexKind
    from seamkiln.pattern.model import (
        EdgeRef,
        InternalLine,
        LineKind,
        Mark,
        MarkKind,
        Panel,
        Pattern,
        Seam,
    )

    panels = [
        Panel(
            id=row["id"],
            name=row.get("name", ""),
            outline=[Vertex(v[0], v[1], VertexKind(v[2])) for v in row["outline"]],
            marks=[
                Mark(MarkKind(m["kind"]), m["x"], m["y"], depth=m["depth"], diameter=m["diameter"])
                for m in row.get("marks", [])
            ],
            internals=[
                InternalLine(
                    LineKind(i["kind"]),
                    [Vertex(v[0], v[1], VertexKind(v[2])) for v in i["points"]],
                    closed=i["closed"],
                )
                for i in row.get("internals", [])
            ],
            seam_allowance_mm=row.get("seam_allowance_mm", 0.0),
        )
        for row in data["panels"]
    ]
    seams = [
        Seam(
            a=EdgeRef(**row["a"]),
            b=EdgeRef(**row["b"]),
            gather=row.get("gather", 1.0),
            flip=row.get("flip", False),
            id=row.get("id", ""),
        )
        for row in data.get("seams", [])
    ]
    return Pattern(
        name=data.get("name", "restored"), panels=panels, seams=seams, units=data.get("units", "mm")
    )
