"""The document: one command model, shared by every client.

This is the architecture that makes seamkiln different from the incumbents,
so it is worth stating plainly. Marvelous Designer has a Python API, but it
runs inside the application and ships only on an enterprise tier - the GUI is
the product and the script is a bolt-on. Here it is the other way round:

    a Session holds the garment, every mutation is a Command, and every
    Command is recorded.

The Qt shell builds Commands from clicks. The TEE adapter builds the same
Commands from a batch. `Session.script()` hands back the list, and
`Session.replay(script)` rebuilds the garment from it - so an afternoon of
GUI work exports as a script that reproduces it exactly, and there is no path
through the interface that a script cannot take.

Nothing here imports Qt, and nothing here imports TEE.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Any

SCRIPT_VERSION = 1


class CommandError(ValueError):
    """A command that cannot be carried out. Always names the fix."""


@dataclass(frozen=True, slots=True)
class Command:
    op: str
    args: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"op": self.op, "args": dict(self.args)}

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> Command:
        if "op" not in raw:
            raise CommandError(f"{raw!r} has no 'op'. Every command names a verb.")
        # tolerate the adapter's wire shape, which spells args as `props`
        args = raw.get("args")
        if args is None:
            args = {k: v for k, v in raw.items() if k not in ("op", "props")}
            args.update(raw.get("props") or {})
        return Command(op=str(raw["op"]), args=dict(args))


@dataclass
class Session:
    """A garment document, and the script that produced it."""

    name: str = "untitled"
    pattern: Any = None  # seamkiln.pattern.model.Pattern
    body: Any = None  # trimesh.Trimesh
    sdf: Any = None
    garment: Any = None
    drape: Any = None
    fabric: str = "cotton_jersey"
    body_spec: dict[str, Any] = field(default_factory=dict)
    history: list[Command] = field(default_factory=list)

    # -- the script ---------------------------------------------------------

    def script(self) -> dict[str, Any]:
        """Everything needed to rebuild this session, and nothing else."""
        return {
            "seamkiln_script": SCRIPT_VERSION,
            "name": self.name,
            "commands": [c.as_dict() for c in self.history],
        }

    def save_script(self, path: str | Path) -> Path:
        destination = Path(path)
        destination.write_text(json.dumps(self.script(), indent=2), encoding="utf-8")
        return destination

    @classmethod
    def replay(cls, script: dict[str, Any] | str | Path) -> Session:
        """Rebuild a session from a script. The replay law: same script in,
        same garment out - checked by fingerprint, not by eye."""
        if isinstance(script, str | Path):
            script = json.loads(Path(script).read_text(encoding="utf-8"))
        version = script.get("seamkiln_script")
        if version != SCRIPT_VERSION:
            raise CommandError(
                f"script version {version!r} is not {SCRIPT_VERSION}. "
                "Re-export it from the version of seamkiln that wrote it."
            )
        session = cls(name=script.get("name", "replayed"))
        for raw in script.get("commands", []):
            session.apply(Command.from_dict(raw))
        return session

    def fingerprint(self) -> str:
        """A stable hash of the garment - the replay law's measuring stick."""
        import numpy as np

        parts: list[bytes] = [self.name.encode()]
        if self.pattern is not None:
            for panel in self.pattern.panels:
                parts.append(panel.id.encode())
                parts.append(
                    np.round(
                        np.asarray([(v.x, v.y) for v in panel.outline], dtype=np.float64), 6
                    ).tobytes()
                )
        if self.drape is not None:
            parts.append(np.round(self.drape.points, 6).tobytes())
        return sha256(b"|".join(parts)).hexdigest()[:16]

    # -- applying commands --------------------------------------------------

    def apply(self, command: Command | dict[str, Any]) -> dict[str, Any]:
        """Carry out one command and record it. The ONLY way state changes."""
        if isinstance(command, dict):
            command = Command.from_dict(command)
        handler = _VERBS.get(command.op)
        if handler is None:
            raise CommandError(
                f"unknown command {command.op!r}. seamkiln accepts: {', '.join(sorted(_VERBS))}."
            )
        result = handler(self, command.args)
        self.history.append(command)
        return result

    def summary(self) -> dict[str, Any]:
        """Compact state. Never geometry - hard rule 1, in the core itself."""
        out: dict[str, Any] = {
            "name": self.name,
            "commands": len(self.history),
            "fabric": self.fabric,
        }
        if self.pattern is not None:
            out["pattern"] = self.pattern.summary()
        if self.body_spec:
            out["body"] = self.body_spec
        if self.garment is not None:
            out["garment"] = self.garment.summary()
        if self.drape is not None:
            out["drape"] = self.drape.report()
        return out


# -- verbs -------------------------------------------------------------------


def _require_pattern(session: Session):
    if session.pattern is None or not session.pattern.panels:
        raise CommandError("there is no pattern yet. Use 'block' or 'panel' first.")
    return session.pattern


def _v_block(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.fixtures import tee_block

    name = str(args.get("block", "tee"))
    if name != "tee":
        raise CommandError(f"no built-in block {name!r}. Built-in blocks: tee.")
    numeric = {k: float(v) for k, v in args.items() if k != "block"}
    session.pattern = tee_block(**numeric)
    session.name = session.pattern.name
    session.garment = session.drape = None
    return {"panels": [p.id for p in session.pattern.panels], "seams": len(session.pattern.seams)}


def _v_panel(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.geometry import Vertex, VertexKind
    from seamkiln.pattern.model import Panel, Pattern

    outline = args.get("outline")
    if not outline or len(outline) < 3:
        raise CommandError(
            "a panel needs an outline of at least 3 points: "
            "[[x_mm, y_mm], ...] or [[x, y, 'turn'|'curve'], ...]."
        )
    if session.pattern is None:
        session.pattern = Pattern(name=session.name)
    vertices = [
        Vertex(float(p[0]), float(p[1]), VertexKind(p[2]) if len(p) > 2 else VertexKind.TURN)
        for p in outline
    ]
    panel = Panel(id=str(args.get("id") or f"P{len(session.pattern.panels) + 1}"), outline=vertices)
    session.pattern.panels.append(panel)
    session.garment = session.drape = None
    return {"id": panel.id, "area_mm2": round(panel.area_mm2, 1), "edges": len(panel.edges())}


def _v_seam(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.model import EdgeRef, Seam

    pattern = _require_pattern(session)

    def ref(raw: Any) -> EdgeRef:
        if isinstance(raw, dict):
            return EdgeRef(
                str(raw["panel"]),
                int(raw["edge"]),
                float(raw.get("t0", 0.0)),
                float(raw.get("t1", 1.0)),
            )
        text = str(raw or "")
        if "#" not in text:
            raise CommandError(
                f"{text!r} is not an edge reference. Use 'FRONT#3', or "
                '{"panel": "FRONT", "edge": 3, "t0": 0, "t1": 0.5}.'
            )
        panel, edge = text.split("#", 1)
        return EdgeRef(panel, int(edge))

    seam = Seam(
        a=ref(args.get("a")),
        b=ref(args.get("b")),
        gather=float(args.get("gather", 1.0)),
        id=str(args.get("id") or ""),
    )
    pattern.seams.append(seam)
    session.garment = session.drape = None
    return {"id": seam.id}


def _v_allowance(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.allowance import add_seam_allowance

    pattern = _require_pattern(session)
    millimetres = float(args.get("mm", 10.0))
    targets = args.get("panels") or [p.id for p in pattern.panels]
    for index, panel in enumerate(list(pattern.panels)):
        if panel.id in targets:
            pattern.panels[index] = add_seam_allowance(panel, millimetres)
    return {"panels": list(targets), "mm": millimetres}


def _v_body(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.body import mannequin, sdf_from_mesh
    from seamkiln.drape.measure import body_measurements

    kind = str(args.get("kind", "mannequin")).lower()
    stature = float(args.get("stature_m", 1.75))
    if kind == "anny":
        from seamkiln.drape.anny_body import anny_body

        phenotypes = {
            k: float(v)
            for k, v in args.items()
            if k in ("gender", "age", "muscle", "weight", "height", "proportions")
        }
        session.body = anny_body(stature_m=stature, **phenotypes)
    elif kind == "mannequin":
        session.body = mannequin(height=stature, chest=float(args.get("chest_m", 1.0)))
    else:
        raise CommandError(
            f"no body kind {kind!r}. Bodies: 'anny' (parametric, Apache-2.0) "
            "or 'mannequin' (stand-in, no download)."
        )
    session.body_spec = {"kind": kind, "stature_m": stature}
    session.sdf = sdf_from_mesh(session.body, voxel_mm=float(args.get("voxel_mm", 8.0)))
    session.garment = session.drape = None
    return {"kind": kind, "measurements": body_measurements(session.body)}


def _v_arrange(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.garment import build_garment, top_arrangement

    pattern = _require_pattern(session)
    if session.body is None:
        _v_body(session, {})  # a default body beats a refusal nobody can act on
    session.garment = build_garment(
        pattern,
        top_arrangement(pattern, session.body),
        particle_distance=float(args.get("particle_distance_mm", 15.0)),
    )
    session.drape = None
    return session.garment.summary()


def _v_drape(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.solve import DrapeSettings, drape

    if session.garment is None:
        _v_arrange(session, {})
    session.fabric = str(args.get("fabric", session.fabric))
    settings = DrapeSettings(
        frames=int(args.get("frames", 250)),
        substeps=int(args.get("substeps", 8)),
        friction=float(args.get("friction", 0.35)),
        thickness_mm=float(args.get("thickness_mm", 1.0)),
    )
    session.drape = drape(session.garment, session.sdf, fabric=session.fabric, settings=settings)
    return session.drape.report()


def _v_delete(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    pattern = _require_pattern(session)
    target = str(args.get("id") or args.get("panel") or "")
    for panel in list(pattern.panels):
        if panel.id == target:
            pattern.panels.remove(panel)
            # a seam whose panel is gone is not a seam; dropping it here beats
            # a dangling reference that fails later, further from the cause
            pattern.seams = [s for s in pattern.seams if target not in (s.a.panel, s.b.panel)]
            session.garment = session.drape = None
            return {"deleted": target, "panels": len(pattern.panels)}
    known = ", ".join(p.id for p in pattern.panels) or "(none)"
    raise CommandError(f"no panel {target!r}. Panels: {known}.")


def _v_export(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    pattern = _require_pattern(session)
    fmt = str(args.get("format", "dxf")).lower()
    out = args.get("out")
    if not out:
        raise CommandError("export needs 'out' - where the file should be written.")
    if fmt in ("dxf", "aama", "astm"):
        from seamkiln.pattern.dxf import write_dxf

        flavour = "aama" if fmt == "aama" else str(args.get("dialect", "astm"))
        return write_dxf(pattern, out, flavour=flavour)
    if fmt == "svg":
        from seamkiln.pattern import plot

        return plot.to_svg(pattern, out)
    if fmt == "pdf":
        from seamkiln.pattern import plot

        return plot.to_pdf(pattern, out, page=str(args.get("page", "A4")))
    if fmt in ("obj", "glb", "ply", "stl"):
        if session.garment is None:
            raise CommandError(
                "a 3D export needs a garment. Run 'arrange' (and usually 'drape') "
                "first, or export dxf/svg/pdf for the flat pattern."
            )
        from seamkiln.drape.preview import garment_mesh, pattern_uv

        points = session.drape.points if session.drape else session.garment.points
        # The flat pattern IS the UV map - free and exact, where every other
        # 3D pipeline pays an unwrap step and guesses where the seams go.
        uv = pattern_uv(session.garment.rest_points_mm)
        mesh = garment_mesh(points, session.garment.triangles, uv=uv)
        mesh.export(out)
        return {
            "path": str(out),
            "format": fmt,
            "vertices": len(mesh.vertices),
            "faces": len(mesh.faces),
            "uv": "from the flat pattern - exact, not unwrapped",
        }
    if fmt in ("usd", "usda", "usdc", "usdz"):
        raise CommandError(
            "trimesh cannot write USD - MEASURED, not assumed: trimesh 5.0's exporters "
            "are 3mf, dae, glb, gltf, obj, off, ply, stl, xyz. Export glb and convert "
            "with usdcat, or add `usd-core` (Apache-2.0) and write the stage directly."
        )
    raise CommandError(
        f"cannot export {fmt!r}. Formats: dxf (aama|astm), svg, pdf, obj, glb, ply, stl."
    )


def _v_techpack(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln import techpack

    out = args.get("out")
    if not out:
        raise CommandError("techpack needs 'out' - where the document should be written.")
    try:
        return techpack.write(
            session,
            out,
            style=str(args.get("style", "")),
            author=str(args.get("author", "")),
            stamp=args.get("stamp"),
        )
    except ValueError as exc:
        raise CommandError(str(exc)) from exc


def _v_fit(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.measure import fit_report

    if session.drape is None or session.garment is None or session.body is None:
        raise CommandError("there is no drape to report on. Run 'drape' first.")
    return fit_report(session.garment, session.drape.points, session.body)


_VERBS = {
    "block": _v_block,
    "panel": _v_panel,
    "seam": _v_seam,
    "allowance": _v_allowance,
    "body": _v_body,
    "arrange": _v_arrange,
    "drape": _v_drape,
    "delete": _v_delete,
    "export": _v_export,
    "fit": _v_fit,
    "techpack": _v_techpack,
}

VERBS = tuple(sorted(_VERBS))
