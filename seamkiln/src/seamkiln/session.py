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

import numpy as np

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
    # A54 side products: what the last finishing, tearing, lacing or animation
    # produced. Held on the session so an export or a render can reach them
    # without the caller keeping a second copy that can drift.
    colours: Any = None
    fur: Any = None
    frayed: Any = None
    lace: Any = None
    animation: Any = None
    locks: Any = None  # seamkiln.locking.Locks, built on first use
    # A56 hardware. Zippers are keyed by the opening they fill; buttons are a
    # list because a placket has many and they are fastened in order.
    zippers: dict[str, Any] = field(default_factory=dict)
    buttons: list[Any] = field(default_factory=list)
    handoffs: list[Any] = field(default_factory=list)
    # A65 P5b. A rigged import keeps its skeleton HERE and its rest mesh in
    # `body`, because everything downstream - the SDF, the measurements, the
    # arrangements - wants a plain trimesh and always has. `walk` is the one
    # verb that asks for the rig, and it is the only reason to keep it.
    rig: Any = None  # seamkiln.rig.skin.RiggedAvatar, when the file had a skin
    arrangement: str = ""  # which arrangement built the garment: cylinder | wrap
    frame: Any = None  # seamkiln.drape.dressing.BodyFrame, when wrap was used
    avatar: dict[str, Any] = field(default_factory=dict)
    gait: Any = None
    live: Any = None  # seamkiln.interact.LiveSession, built on first pull

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

    @property
    def lock_state(self):
        from seamkiln.locking import Locks

        if self.locks is None:
            self.locks = Locks()
        return self.locks

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


def _guard(session: Session, scope: str, doing: str) -> None:
    """Refuse a change to a locked scope. Locks are set by a command, so they
    survive a replay and a locked script produces the same garment twice."""
    from seamkiln.locking import LockedError

    if session.locks is None:
        return
    try:
        session.locks.check(scope, doing)
    except LockedError as exc:
        raise CommandError(str(exc)) from exc


def _require_pattern(session: Session):
    if session.pattern is None or not session.pattern.panels:
        raise CommandError("there is no pattern yet. Use 'block' or 'panel' first.")
    return session.pattern


def _v_block(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.fixtures import jacket_block, tee_block

    if session.pattern is not None and session.pattern.panels:
        # A block replaces EVERY panel, so it has to ask about every panel -
        # not about the collective "panels" scope, which a lock on one piece
        # does not hold. Guarding only the collective let a single locked
        # panel be thrown away by loading a fresh block over it.
        _guard(session, "panels", "replacing the pattern with a block")
        for existing in session.pattern.panels:
            _guard(session, f"panel:{existing.id}", "replacing the pattern with a block")
    name = str(args.get("block", "tee"))
    if name not in ("tee", "jacket-zip", "jacket-placket"):
        raise CommandError(
            f"no built-in block {name!r}. Built-in blocks: tee, jacket-zip, jacket-placket."
        )
    numeric = {k: float(v) for k, v in args.items() if k != "block"}
    if name == "tee":
        session.pattern = tee_block(**numeric)
    else:
        session.pattern = jacket_block(
            opening="zipper" if name == "jacket-zip" else "placket", **numeric
        )
    session.name = session.pattern.name
    session.garment = session.drape = session.live = None
    return {"panels": [p.id for p in session.pattern.panels], "seams": len(session.pattern.seams)}


def _v_load(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Load a pattern from a file - DXF in the AAMA/ASTM dialects - in place of
    the current one, the way `block` replaces it.

    The script records the PATH, not the file: a replay re-reads it, and the
    replay law's fingerprint (built from the outlines) is what catches a file
    that changed in between. The result carries the file's sha256 so a caller
    can pin what was read. The reader's own report rides along - which unit
    won, the validation-curve deviation, the notes - because a DXF read in
    the wrong unit is a doll's garment that drapes perfectly.
    """
    path = args.get("path")
    if not path:
        raise CommandError("load needs 'path' - the file to read. Formats: dxf (AAMA/ASTM).")
    source = Path(str(path))
    fmt = str(args.get("format") or source.suffix.lstrip(".") or "dxf").lower()
    if fmt not in ("dxf", "aama", "astm"):
        raise CommandError(
            f"load reads dxf (AAMA/ASTM), not {fmt!r}. Export the pattern from your CAD "
            "as DXF-AAMA or DXF-ASTM, one block per piece."
        )
    if not source.is_file():
        raise CommandError(f"load: {source} is not a file.")
    if session.pattern is not None:
        for existing in session.pattern.panels:
            _guard(session, f"panel:{existing.id}", "replacing the pattern with a loaded file")

    from ezdxf import DXFError

    from seamkiln.pattern.dxf import DxfDialectError, read_dxf

    flavour = "aama" if fmt == "aama" else str(args.get("dialect", "astm"))
    units_mm = args.get("units_mm")
    try:
        pattern, report = read_dxf(
            source,
            flavour=flavour,
            strict=bool(args.get("strict", True)),
            units_mm=float(units_mm) if units_mm is not None else None,
        )
    except (DxfDialectError, DXFError, ValueError, OSError) as exc:
        raise CommandError(f"load: {exc}") from exc
    if not pattern.panels:
        raise CommandError(
            f"load: {source.name} has no piece - no block with a closed boundary on layer 1 "
            f"(skipped {', '.join(report.skipped_blocks) or 'nothing'}). Is it a pattern DXF "
            "in the AAMA/ASTM layout, one block per piece?"
        )

    session.pattern = pattern
    session.name = pattern.name
    session.garment = session.drape = session.live = None
    return {
        "path": str(source),
        "sha256": sha256(source.read_bytes()).hexdigest()[:16],
        "style": report.header.get("STYLE NAME", ""),
        "panels": [p.id for p in pattern.panels],
        "names": {p.id: p.name for p in pattern.panels if p.name != p.id},
        "seams": len(pattern.seams),
        "insunits": report.insunits,
        "units_source": report.units_source,
        "scale_mm_per_unit": report.scale_mm,
        "validation_curves": report.validation_curves,
        "qv_deviation_mm": round(report.qv_deviation_mm, 3),
        "skipped_blocks": report.skipped_blocks,
        "unknown_layers": report.unknown_layers,
        "notes": report.notes,
    }


def _v_panel(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.geometry import Vertex, VertexKind
    from seamkiln.pattern.model import Panel, Pattern

    if args.get("id"):
        _guard(session, f"panel:{args['id']}", f"redrawing {args['id']}")

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
    session.garment = session.drape = session.live = None
    return {"id": panel.id, "area_mm2": round(panel.area_mm2, 1), "edges": len(panel.edges())}


def _v_seam(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.model import EdgeRef, Seam

    pattern = _require_pattern(session)
    for side in ("a", "b"):
        named = args.get(side)
        if isinstance(named, dict | list | tuple):
            panel = named["panel"] if isinstance(named, dict) else named[0]
            _guard(session, f"panel:{panel}", f"sewing {panel}")

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
    session.garment = session.drape = session.live = None
    return {"id": seam.id}


def _v_allowance(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern.allowance import add_seam_allowance

    pattern = _require_pattern(session)
    _guard(session, "panels", "setting a seam allowance")
    millimetres = float(args.get("mm", 10.0))
    targets = args.get("panels") or [p.id for p in pattern.panels]
    for panel_id in targets:
        _guard(session, f"panel:{panel_id}", "setting a seam allowance")
    for index, panel in enumerate(list(pattern.panels)):
        if panel.id in targets:
            pattern.panels[index] = add_seam_allowance(panel, millimetres)
    return {"panels": list(targets), "mm": millimetres}


def _v_body(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    _guard(session, "body", "changing the body")
    from seamkiln.drape.body import mannequin, sdf_from_mesh
    from seamkiln.drape.measure import body_measurements

    kind = str(args.get("kind", "mannequin")).lower()
    stature = float(args.get("stature_m", 1.75))
    session.rig = None  # a new body never inherits the last one's skeleton
    rig_note: str | None = None
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
    elif kind == "figure":
        # A figure with joints the dressing lane can ask, rather than a body
        # it has to measure. Faces +Z unless turned.
        from seamkiln.avatar import Pose
        from seamkiln.figure import figure, standing_offset

        pose = Pose.from_values({k: float(v) for k, v in (args.get("pose") or {}).items()})
        from seamkiln.figure import build as figure_build

        try:
            chosen = figure_build(str(args.get("build", "male")))
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        chest = args.get("chest_m")
        try:
            session.body = figure(
                pose,
                height=stature,
                facing_deg=float(args.get("facing_deg", 0.0)),
                build=chosen,
                chest_m=float(chest) if chest is not None else None,
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        lift = standing_offset(session.body)
        session.body.apply_translation(lift)
        # the joints ride in the metadata and stand on the ground with the mesh
        session.body.metadata["joints"] = {
            k: ((np.asarray(v, dtype=np.float64) + lift).tolist() if isinstance(v, list) else v)
            for k, v in session.body.metadata["joints"].items()
        }
        session.avatar = {
            "kind": "figure",
            "build": chosen.name,
            "chest_m": float(chest) if chest is not None else None,
            "pose": pose.as_values(),
            "facing_deg": float(args.get("facing_deg", 0.0)),
        }
    elif kind in ("posed", "custom"):
        from seamkiln.avatar import (
            Pose,
            adjust,
            custom_avatar,
            describe,
            posed_mannequin,
            rigged_avatar,
        )

        if kind == "posed":
            session.body = posed_mannequin(
                Pose.from_values({k: float(v) for k, v in (args.get("pose") or {}).items()}),
                height=stature,
                chest=float(args.get("chest_m", 1.0)),
            )
        else:
            path = args.get("path")
            if not path:
                raise CommandError("a custom avatar needs 'path' - the mesh file to load.")
            # A65 P5b: a glTF may carry a SKIN, and trimesh cannot see it, so
            # the rigged reader is tried first for those. A file that simply
            # has no skin falls back to the mesh loader and SAYS SO - that is
            # an honest property of the file. Bones that cannot be MAPPED do
            # not fall back: the fix is real (rename, or pass 'joints'), and
            # quietly walking such a body as a statue would hide it.
            if str(path).lower().endswith((".glb", ".gltf")):
                from seamkiln.rig.gltf_read import RigReadError

                try:
                    session.rig = rigged_avatar(
                        path,
                        units=str(args.get("units", "auto")),
                        overrides=args.get("joints"),
                    )
                    session.body = session.rig.mesh()
                except RigReadError as exc:
                    rig_note = f"{exc} It will walk as one piece."
                except (OSError, ValueError) as exc:
                    raise CommandError(str(exc)) from exc
            if session.rig is None:
                try:
                    session.body = custom_avatar(
                        path,
                        units=str(args.get("units", "auto")),
                        up=str(args.get("up", "auto")),
                        forward_z=bool(args.get("forward_z", True)),
                    )
                except (OSError, ValueError) as exc:
                    raise CommandError(str(exc)) from exc
            if "height_m" in args or "girth_scale" in args:
                session.body = adjust(
                    session.body,
                    height_m=float(args["height_m"]) if "height_m" in args else None,
                    girth_scale=float(args.get("girth_scale", 1.0)),
                )
                if session.rig is not None:
                    # `adjust` reshapes the MESH; the skeleton it was bound to
                    # no longer matches it, and skinning against a stale bind
                    # pose tears a limb. Drop the rig rather than bend a body
                    # through bones that are in the wrong place now.
                    session.rig = None
                    rig_note = (
                        "height_m/girth_scale reshaped the mesh, so its skeleton no longer "
                        "fits it and was dropped: this body walks as one piece. Scale the "
                        "avatar in its own file if you need it rigged at another size."
                    )
            session.avatar = describe(session.body)
            if session.rig is not None:
                session.avatar["rig"] = {
                    "joints": len(session.rig.body.joints),
                    "mapped": sorted(session.rig.slots),
                    "notes": list(session.rig.notes),
                }
    else:
        raise CommandError(
            f"no body kind {kind!r}. Bodies: 'anny' (parametric, Apache-2.0), "
            "'mannequin' (stand-in, no download), 'posed' (the mannequin at "
            "joint angles), 'figure' (a clothable figure with joints, at a "
            "'pose') or 'custom' (your own mesh, from 'path')."
        )
    session.body_spec = {"kind": kind, "stature_m": stature}
    if kind == "figure":
        session.body_spec["pose"] = dict(session.avatar.get("pose", {}))
        session.body_spec["facing_deg"] = session.avatar.get("facing_deg", 0.0)
        session.body_spec["build"] = session.avatar.get("build", "male")
        session.body_spec["chest_m"] = session.avatar.get("chest_m")
    session.sdf = sdf_from_mesh(session.body, voxel_mm=float(args.get("voxel_mm", 8.0)))
    session.garment = session.drape = session.live = None
    out = {"kind": kind, "measurements": body_measurements(session.body)}
    if session.avatar:
        out["avatar"] = session.avatar
    out["articulated"] = session.rig is not None
    if rig_note:
        out["note"] = rig_note
    return out


def _arrangement_choice(session: Session, requested: str) -> str:
    """'auto' picks by body kind, and the pick is RECORDED so a replay makes it.

    The cylinder arrangement measures the body by cross-section and is tuned
    on the capsule mannequin - every number in this project's physics tests
    was produced on it, so the mannequin keeps it. Any other body gets the
    wrap arrangement, which takes its radius from the pattern and only a
    shoulder height and two arm axes from the body: on the figure, the
    cross-section measurer hung a jacket's top edge at 2.02 m for shoulders
    at 1.40 m, and the coat collapsed into a muff round the ears.
    """
    if requested not in ("auto", "cylinder", "wrap"):
        raise CommandError(f"arrangement must be 'auto', 'cylinder' or 'wrap', not {requested!r}.")
    if requested != "auto":
        return requested
    return "cylinder" if session.body_spec.get("kind", "mannequin") == "mannequin" else "wrap"


def _v_arrange(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.garment import build_garment, top_arrangement

    pattern = _require_pattern(session)
    if session.body is None:
        _v_body(session, {})  # a default body beats a refusal nobody can act on
    choice = _arrangement_choice(session, str(args.get("arrangement", "auto")))
    height = float(session.body_spec.get("stature_m", 1.75))
    roles = args.get("roles")
    if roles is not None and not isinstance(roles, dict):
        raise CommandError(
            "roles must map panel ids to front | back | sleeve_l | sleeve_r, "
            'e.g. {"Frente_M": "front", "Costas_M": "back", "Manga Esquerda_M": "sleeve_l"}.'
        )
    if choice == "cylinder":
        try:
            placements = top_arrangement(pattern, session.body, roles=roles)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
    else:
        from seamkiln.drape.dressing import frame_from_figure, frame_from_mesh, wrap_arrangement

        if session.body_spec.get("kind") == "figure":
            from seamkiln.avatar import Pose

            # The frame is in the figure's JOINT coordinates, and the session's
            # figure has been stood on the ground - so the garment is built in
            # joint coordinates and lifted afterwards, once, below.
            frame = frame_from_figure(
                Pose.from_values(session.body_spec.get("pose", {})),
                height=height,
                build=session.body_spec.get("build", "male"),
                facing_deg=float(session.body_spec.get("facing_deg", 0.0)),
            )
        else:
            try:
                frame = frame_from_mesh(session.body)
            except ValueError as exc:
                raise CommandError(
                    f"could not measure this body for a wrap arrangement: {exc}. "
                    "Use body kind 'figure', or pass arrangement='cylinder'."
                ) from exc
        try:
            placements = wrap_arrangement(
                pattern,
                frame,
                height=height,
                roles=roles,
                facing_deg=float(session.body_spec.get("facing_deg", 0.0)),
            )
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        session.frame = frame
    session.garment = build_garment(
        pattern, placements, particle_distance=float(args.get("particle_distance_mm", 15.0))
    )
    if choice == "wrap" and session.body_spec.get("kind") == "figure":
        session.garment.points = session.garment.points + _figure_lift(session)
    session.arrangement = choice
    session.drape = None
    out = session.garment.summary()
    out["arrangement"] = choice
    if choice == "wrap" and bool(args.get("dress", True)):
        out.update(_dress_now(session, args))
    return out


def _dress_now(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Pin the shoulders, baste the seams, settle, release - the fitter's job."""
    from seamkiln.drape.dressing import dress, shoulder_anchors

    frame = session.frame
    anchors = shoulder_anchors(frame, _figure_lift(session))
    anchors = {k: v for k, v in anchors.items() if k in session.garment.seam_spans}
    if not anchors:
        return {"dressed": False, "why": "no shoulder seams to pin on this pattern"}
    from seamkiln.drape.garment import piece_roles

    cast = piece_roles(session.pattern, args.get("roles"))
    result = dress(
        session.garment,
        session.sdf,
        fabric=session.fabric,
        anchors=anchors,
        hold_frames=int(args.get("dress_frames", 180)),
        settle_frames=int(args.get("settle_frames", 220)),
        sleeves={pid for pid, role in cast.items() if role.startswith("sleeve")},
        baste_sleeves_to_body=bool(args.get("baste_sleeves", True)),
        head_mm=float(args.get("baste_head_mm", 60.0)),
    )
    session.drape = result
    return {
        "dressed": True,
        "worn": result.contact.get("worn"),
        "touching_fraction": result.contact.get("touching_fraction"),
        "seam_gaps": result.seam_gaps,
    }


def _figure_lift(session: Session) -> np.ndarray:
    """The figure stands on the ground; its joint frame does not. The
    difference is the translation the garment and its anchors both need."""
    if session.body_spec.get("kind") != "figure" or session.body is None:
        return np.zeros(3)
    from seamkiln.avatar import Pose
    from seamkiln.figure import figure, standing_offset

    pose = Pose.from_values(session.body_spec.get("pose", {}))
    return standing_offset(
        figure(
            pose,
            height=float(session.body_spec.get("stature_m", 1.75)),
            build=session.body_spec.get("build", "male"),
            chest_m=session.body_spec.get("chest_m"),
        )
    )


def _v_drape(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.solve import DrapeSettings, drape

    if session.garment is None:
        _v_arrange(session, {})
    session.fabric = str(args.get("fabric", session.fabric))
    # NOT a literal 8: DrapeSettings' own default is the converged tier, and
    # hardcoding a draft value here silently made every session drape soft.
    settings = DrapeSettings(
        frames=int(args.get("frames", 250)),
        substeps=int(args.get("substeps", DrapeSettings().substeps)),
        friction=float(args["friction"]) if "friction" in args else None,  # None: the card's
        thickness_mm=float(args.get("thickness_mm", 1.0)),
    )
    session.drape = drape(session.garment, session.sdf, fabric=session.fabric, settings=settings)
    return session.drape.report()


def _v_delete(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    pattern = _require_pattern(session)
    target = str(args.get("id") or args.get("panel") or "")
    # Deleting a locked panel is the LOUDEST version of the change a lock
    # exists to prevent, and it was the one verb that did not ask. Found by
    # driving the locks through TEE's batch path rather than by reading the
    # code: the guard covered allowance, body, grade and cut, and a locked
    # panel could still be deleted outright.
    _guard(session, "panels", f"deleting {target}")
    _guard(session, f"panel:{target}", f"deleting {target}")
    for panel in list(pattern.panels):
        if panel.id == target:
            pattern.panels.remove(panel)
            # a seam whose panel is gone is not a seam; dropping it here beats
            # a dangling reference that fails later, further from the cause
            pattern.seams = [s for s in pattern.seams if target not in (s.a.panel, s.b.panel)]
            session.garment = session.drape = session.live = None
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
    if session.drape is not None:
        verdict = session.drape.report()
        if not verdict.get("converged", True) and not args.get("allow_unconverged"):
            raise CommandError(
                "the drape behind this tech pack has not converged: "
                + "; ".join(verdict.get("not_converged", []))
                + ". A factory does not need a fit table computed from a preview. "
                "Re-drape finer, or pass allow_unconverged=true to document it anyway."
            )
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
    verdict = session.drape.report()
    if not verdict.get("converged", True) and not args.get("allow_unconverged"):
        reasons = "; ".join(verdict.get("not_converged", []))
        raise CommandError(
            "this drape has not converged, so its measurements are not worth "
            f"quoting: {reasons}. Re-run at a finer particle distance or a higher "
            "quality tier - or pass allow_unconverged=true if you know you are "
            "iterating and will not report these numbers."
        )
    report = fit_report(session.garment, session.drape.points, session.body)
    return {k: v for k, v in verdict.items() if k in ("converged", "not_converged")} | report


# -- A54 verbs: everything the garment can have done to it --------------------


def _scopes(args: dict[str, Any], verb: str) -> list[str]:
    """The scopes a lock/unlock names - and a refusal when it names none.

    `lock` used to loop over an empty list and return success. A command that
    locks nothing while reporting `{"locked": []}` is the exact silent failure
    hard rule 6 exists to stop: this was found by passing `{"panel": "FRONT"}`
    instead of `{"scope": "panel:FRONT"}` through TEE's batch path, getting an
    ok back, and then watching the "locked" panel be deleted.
    """
    from seamkiln.locking import SCOPES

    named = args.get("scopes") or ([args["scope"]] if "scope" in args else [])
    if not named and not args.get("all"):
        stray = ", ".join(sorted(k for k in args if k not in ("reason", "why", "all"))) or "nothing"
        raise CommandError(
            f"{verb} names no scope (got: {stray}), so it would {verb} nothing and "
            f"report success. Pass 'scope' (or 'scopes'): {', '.join(SCOPES)}, or "
            "'panel:<id>'." + ("" if verb == "lock" else " Pass 'all': true to clear every lock.")
        )
    return [str(scope) for scope in named]


def _v_lock(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.locking import Locks

    locks = session.lock_state
    for scope in _scopes(args, "lock"):
        try:
            locks.add(scope, str(args.get("reason") or args.get("why") or ""))
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
    if not isinstance(locks, Locks):  # pragma: no cover - defensive
        raise CommandError("lock state is corrupt")
    return locks.as_dict()


def _v_unlock(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    locks = session.lock_state
    wanted = _scopes(args, "unlock")
    if args.get("all"):
        locks.clear()
    for scope in wanted:
        locks.remove(scope)
    return locks.as_dict()


def _v_grade(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    # A collective operation is guarded PANEL BY PANEL, not against a
    # collective scope: locking one piece has to stop a grade that would move
    # it, and checking only "panels" let exactly that through.
    _guard(session, "panels", "grading")
    if session.pattern is not None:
        for panel in session.pattern.panels:
            _guard(session, f"panel:{panel.id}", "grading")
    from seamkiln.pattern.grading import (
        GradingError,
        Measurements,
        grade_to_measurements,
    )

    pattern = _require_pattern(session)
    base = Measurements(**{k: float(v) for k, v in (args.get("base") or {}).items()})
    if args.get("to_body"):
        if session.body is None:
            raise CommandError("grade to_body needs a body. Run 'body' first.")
        target = Measurements.from_body(session.body)
    else:
        target = Measurements(**{k: float(v) for k, v in (args.get("target") or {}).items()})
    try:
        graded, report = grade_to_measurements(
            pattern, base, target, strict=bool(args.get("strict", True))
        )
    except GradingError as exc:
        raise CommandError(str(exc)) from exc
    session.pattern = graded
    session.garment = session.drape = session.live = None
    return {"target": target.as_dict(), **report.as_dict()}


def _v_cut(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.pattern import cutting

    pattern = _require_pattern(session)
    panel = pattern.panel(str(args.get("panel", "")))
    _guard(session, f"panel:{panel.id}", f"a {args.get('op', 'cut')} on {panel.id}")
    operation = str(args.get("op", "cut"))
    index = pattern.panels.index(panel)
    try:
        if operation == "cut":
            result = cutting.cut(panel, tuple(args["from"]), tuple(args["to"]))
            pattern.panels[index : index + 1] = result.pieces
            out = result.as_dict()
        elif operation == "dart":
            pattern.panels[index] = cutting.dart(
                panel, tuple(args["apex"]), tuple(args["base"]), float(args["width_mm"])
            )
            out = {"dart": args["width_mm"], "area_mm2": round(pattern.panels[index].area_mm2, 1)}
        elif operation == "spread":
            pattern.panels[index] = cutting.slash_spread(
                panel, tuple(args["hinge"]), tuple(args["through"]), float(args["degrees"])
            )
            out = {
                "spread_deg": args["degrees"],
                "area_mm2": round(pattern.panels[index].area_mm2, 1),
            }
        elif operation == "pleat":
            pattern.panels[index] = cutting.pleat(
                panel,
                float(args["at_x"]),
                float(args["depth_mm"]),
                kind=str(args.get("kind", "knife")),
            )
            out = {"pleat": args["depth_mm"], "kind": args.get("kind", "knife")}
        else:
            raise CommandError(f"no cutting op {operation!r}. Ops: cut, dart, spread, pleat.")
    except cutting.CuttingError as exc:
        raise CommandError(str(exc)) from exc
    except KeyError as exc:
        raise CommandError(f"cutting op {operation!r} needs {exc}") from exc
    session.garment = session.drape = session.live = None
    return {**out, **_resew(session)}


def _resew(session: Session) -> dict[str, Any]:
    """Drop the seams a cut invalidated, and name them.

    Edges are derived from corners, so a cut, a dart or a pleat that changes a
    panel's corner count moves every edge index after it - and a seam naming
    one of those now points somewhere else. Failing the whole batch on that is
    technically correct and practically useless: a pattern maker cuts first
    and re-sews after. The invalid seams are dropped HERE with their names in
    the result, which is the difference between "that broke" and "those four
    seams need re-sewing".
    """
    pattern = session.pattern
    if pattern is None:
        return {}
    kept, dropped = [], []
    for seam in pattern.seams:
        try:
            for ref in (seam.a, seam.b):
                panel = pattern.panel(ref.panel)
                if not 0 <= ref.edge < len(panel.edges()):
                    raise IndexError
        except (KeyError, IndexError):
            dropped.append(seam.id)
            continue
        kept.append(seam)
    pattern.seams = kept
    return {"seams_dropped": dropped} if dropped else {}


def _v_rip(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.tearing import auto_rip, fray, rip_seam, seam_tension

    if session.garment is None:
        raise CommandError("there is nothing to rip yet. Run 'arrange' first.")
    points = session.drape.points if session.drape else session.garment.points
    if args.get("auto"):
        session.garment, tears = auto_rip(
            session.garment, points, strength_mm=float(args.get("strength_mm", 12.0))
        )
    else:
        seam = str(args.get("seam", ""))
        try:
            session.garment, tear = rip_seam(
                session.garment,
                seam,
                fraction=float(args.get("fraction", 1.0)),
                from_end=bool(args.get("from_end", False)),
            )
        except KeyError as exc:
            raise CommandError(str(exc)) from exc
        tears = [tear]
    frayed = fray(session.garment, points, tears, length_mm=float(args.get("fray_mm", 6.0)))
    session.frayed = frayed
    return {
        "tears": [t.as_dict() for t in tears],
        "fray": frayed.summary(),
        "tension_mm": {
            k: v["max_gap_mm"] for k, v in seam_tension(session.garment, points).items()
        },
    }


def _v_pinch(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape.pinching import Pinch, pinch, pinch_report
    from seamkiln.drape.solve import DrapeSettings, drape

    if session.garment is None:
        raise CommandError("there is nothing to pinch yet. Run 'arrange' first.")
    points = (session.drape.points if session.drape else session.garment.points).copy()
    grabs = [
        Pinch(
            at=tuple(g["at"]),
            radius_mm=float(g.get("radius_mm", 25.0)),
            to=tuple(g["to"]) if g.get("to") else None,
        )
        for g in (args.get("grabs") or [])
    ]
    if not grabs:
        raise CommandError(
            'pinch needs grabs: [{"at": [x, y, z], "radius_mm": 40, "to": [x, y, z]}]'
        )
    pinches = pinch(session.garment, points, grabs, mirror=bool(args.get("mirror", True)))
    if int(pinches.mask.sum()) == 0:
        raise CommandError(
            "no cloth is within reach of those grabs. Pick a point ON the draped "
            "garment - `fit` or an export will tell you where it is."
        )
    session.garment.points = points
    result = drape(
        session.garment,
        session.sdf,
        fabric=session.fabric,
        pins=pinches.mask,
        pin_target=pinches.target,
        settings=DrapeSettings(frames=int(args.get("frames", 220))),
    )
    session.drape = result
    return pinch_report(points, result.points, pinches)


def _v_lace(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.drape import lacing
    from seamkiln.drape.solve import DrapeSettings, drape

    if session.garment is None:
        raise CommandError("there is nothing to lace yet. Run 'arrange' first.")
    points = (session.drape.points if session.drape else session.garment.points).copy()
    try:
        left = lacing.eyelets_along(
            session.garment,
            points,
            panel=str(args["left_panel"]),
            side=str(args.get("left_side", "max")),
            count=int(args.get("eyelets", 7)),
        )
        right = lacing.eyelets_along(
            session.garment,
            points,
            panel=str(args["right_panel"]),
            side=str(args.get("right_side", "max")),
            count=int(args.get("eyelets", 7)),
        )
        lace = lacing.thread(
            left,
            right,
            points,
            style=str(args.get("style", "criss-cross")),
            tension=float(args.get("tension", 0.35)),
        )
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    session.garment.points = points
    lacing.apply(session.garment, lace)
    session.lace = lace
    result = drape(
        session.garment,
        session.sdf,
        fabric=session.fabric,
        settings=DrapeSettings(frames=int(args.get("frames", 250))),
    )
    session.drape = result
    import numpy as np

    closed = (
        np.linalg.norm(
            result.points[lace.spans[:, 0]] - result.points[lace.spans[:, 1]], axis=1
        ).mean()
        * 1000.0
    )
    return {**lace.summary(), "closed_to_mm": round(float(closed), 1)}


def _v_finish(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln import finishing

    if session.garment is None or session.drape is None:
        raise CommandError("finishing reads the draped garment. Run 'drape' first.")
    kind = str(args.get("kind", "wash"))
    points, triangles = session.drape.points, session.garment.triangles
    if kind == "wash":
        result = finishing.denim_wash(points, triangles, level=str(args.get("level", "medium")))
        session.colours = result["colours"]
        return result["summary"]
    if kind == "fur":
        pelt = finishing.fur(
            points,
            triangles,
            density_per_cm2=float(args.get("density_per_cm2", 4.0)),
            length_mm=float(args.get("length_mm", 18.0)),
            curl=float(args.get("curl", 0.45)),
            clump=float(args.get("clump", 0.3)),
        )
        session.fur = pelt
        return pelt.summary()
    raise CommandError(f"no finish {kind!r}. Finishes: wash, fur.")


def _v_animate(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.animation import BlendTrack, Keyframe, animate, animation_report

    if session.garment is None:
        raise CommandError("animation drapes an arranged garment. Run 'arrange' first.")
    keys = args.get("keys") or []
    if len(keys) < 2:
        raise CommandError(
            "an animation needs at least two keyframes: "
            '[{"time_s": 0, "weight": 0.3}, {"time_s": 2, "weight": 0.8}]'
        )
    track = BlendTrack(
        [
            Keyframe(
                float(k["time_s"]),
                {kk: float(vv) for kk, vv in k.items() if kk not in ("time_s", "label")},
                str(k.get("label", "")),
            )
            for k in keys
        ]
    )
    kind = session.body_spec.get("kind", "mannequin")
    if kind == "mannequin":
        from seamkiln.drape.body import mannequin

        def factory(values):
            return mannequin(
                height=values.get("stature_m", session.body_spec.get("stature_m", 1.75)),
                chest=0.90 + 0.30 * values.get("weight", 0.5),
            )
    else:
        factory = None
    frames = animate(
        session.garment,
        track,
        fabric=session.fabric,
        fps=float(args.get("fps", 6.0)),
        frames_per_step=int(args["frames_per_step"]) if "frames_per_step" in args else None,
        body_factory=factory,
    )
    session.animation = frames
    if frames:
        session.drape = None
        session.garment.points = frames[-1].points
    return {"track": track.as_dict(), **animation_report(frames)}


# -- hardware -----------------------------------------------------------------


def _need_garment(session: Session, verb: str) -> Any:
    if session.garment is None:
        raise CommandError(f"there is nothing to {verb} yet. Run 'arrange' first.")
    return session.garment


def _redrape(session: Session, args: dict[str, Any]) -> Any:
    from seamkiln.drape.solve import DrapeSettings, drape

    result = drape(
        session.garment,
        session.sdf,
        fabric=session.fabric,
        settings=DrapeSettings(frames=int(args.get("frames", 280))),
    )
    session.drape = result
    return result


def _v_zip(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Fit a zipper to an opening, and drape it."""
    from seamkiln.hardware.zipper import ZipperSpec, apply, install

    garment = _need_garment(session, "zip")
    points = session.drape.points if session.drape else garment.points
    try:
        spec = ZipperSpec(
            material=str(args.get("material", "nylon")),
            size=float(args.get("size", 5.0)),
            layout=str(args.get("layout", "one-way")),
            tape_mm=float(args.get("tape_mm", 12.0)),
            slider_scale=float(args.get("slider_scale", 1.0)),
            weight_scale=float(args.get("weight_scale", 1.0)),
            separating=bool(args.get("separating", False)),
        )
        zipper = install(
            garment,
            points,
            seam_id=str(args.get("opening", "centre-front")),
            spec=spec,
            sliders=tuple(args["sliders"]) if "sliders" in args else None,
        )
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    apply(garment, zipper)
    session.zippers[zipper.id] = zipper
    result = _redrape(session, args)
    return {**zipper.summary(), **_zip_gaps(zipper, result.points)}


def _v_unzip(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Drag a slider and re-solve. The interactive gesture, as a command."""
    from seamkiln.hardware.zipper import apply, unzip

    garment = _need_garment(session, "unzip")
    which = str(args.get("opening", "centre-front"))
    if which not in session.zippers:
        known = ", ".join(sorted(session.zippers)) or "none"
        raise CommandError(f"no zipper fitted to {which!r} (fitted: {known}). Run 'zip' first.")
    zipper = session.zippers[which]
    try:
        unzip(zipper, to=float(args.get("to", 0.0)), slider=int(args.get("slider", 0)))
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
    apply(garment, zipper)
    result = _redrape(session, args)
    return {**zipper.summary(), **_zip_gaps(zipper, result.points)}


def _zip_gaps(zipper: Any, points: Any) -> dict[str, Any]:
    import numpy as np

    d = np.linalg.norm(points[zipper.pairs[:, 0]] - points[zipper.pairs[:, 1]], axis=1) * 1000.0
    mask = zipper.engaged()
    return {
        "closed_gap_mm": round(float(d[mask].mean()), 2) if mask.any() else None,
        "open_gap_mm": round(float(d[~mask].mean()), 2) if (~mask).all() or (~mask).any() else None,
    }


def _v_button(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Place a button and a buttonhole, fasten them, and re-solve.

    This is the Fasten Button tool: one command because it is one gesture -
    you click the button, you click the hole, and the simulation closes it.
    """
    from seamkiln.hardware.buttons import ButtonSpec, apply, check_pops, fasten, hole, place

    garment = _need_garment(session, "button")
    try:
        spec = ButtonSpec(
            kind=str(args.get("type", "4-hole")),
            ligne=float(args.get("ligne", 24.0)),
            material=str(args.get("material", "polyester")),
            thickness_mm=float(args.get("thickness_mm", 3.0)),
            shank_mm=float(args.get("shank_mm", 0.0)),
            thread_mm=float(args.get("thread_mm", 2.5)),
            mass_g=float(args["mass_g"]) if "mass_g" in args else None,
            collision_mm=float(args["collision_mm"]) if "collision_mm" in args else None,
        )
        at = place(
            garment,
            garment.points,
            panel=str(args["panel"]),
            at=(float(args["x"]), float(args["y"])),
        )
        buttonhole = hole(
            garment,
            panel=str(args["hole_panel"]),
            at=(float(args["hole_x"]), float(args["hole_y"])),
            button=spec,
            length_mm=float(args["hole_mm"]) if "hole_mm" in args else None,
            angle_deg=float(args.get("hole_angle_deg", 0.0)),
        )
        session.buttons.append(fasten(garment, at, buttonhole, button=spec, id=str(args.get("id"))))
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    apply(garment, session.buttons)
    result = _redrape(session, args)
    check_pops(garment, result.points, session.buttons)
    return {
        "fastened": len([f for f in session.buttons if not f.popped]),
        **session.buttons[-1].summary(),
        "unresolved_rim": session.buttons[-1].meta.get("rim_unresolved"),
    }


def _live(session: Session):
    """The live session, built on first use and reused after.

    Rebuilt whenever the garment's identity changes, because a LiveSession
    caches the constraint graph and a stale graph is refused by the solver
    rather than silently used.
    """
    from seamkiln.interact import LiveSession

    garment = _need_garment(session, "pull")
    if session.live is None or session.live.garment is not garment:
        session.live = LiveSession(garment, session.sdf, fabric=session.fabric)
    return session.live


def _v_pull(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Grab the cloth, drag it, and let go. The live gesture, as one command.

    A script records the NET gesture and not every mouse sample on purpose: a
    two-second drag is a hundred frames of nothing anybody wants replayed, and
    the interesting content of a pull is where it started, where it ended and
    what the cloth did. `steps` is how finely the drag is interpolated, which
    is what changes the answer - a pull taken in one jump is a different
    physical event from the same pull taken in twenty.
    """
    live = _live(session)
    try:
        handle = live.grab(
            (float(args["x"]), float(args["y"]), float(args["z"])),
            radius_mm=float(args.get("radius_mm", 40.0)),
        )
        start = handle.at.copy()
        finish = [float(args["to_x"]), float(args["to_y"]), float(args["to_z"])]
        steps = max(int(args.get("steps", 12)), 1)
        for k in range(1, steps + 1):
            live.drag(handle, tuple(start + (finish - start) * (k / steps)))
        report = live.release(handle, frames=int(args.get("settle", 40)))
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc
    return {**handle.summary(), **report, "rate": live.rate()}


def _v_fold(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    live = _live(session)
    try:
        return {
            **live.fold(
                (float(args["x"]), float(args["y"]), float(args["z"])),
                depth_mm=float(args.get("depth_mm", 40.0)),
                direction=tuple(args.get("direction", (0.0, 0.0, -1.0))),
                radius_mm=float(args.get("radius_mm", 50.0)),
                settle=int(args.get("settle", 30)),
            ),
            "rate": live.rate(),
        }
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc


def _v_ease(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    live = _live(session)
    try:
        return live.ease(str(args["seam"]), float(args.get("mm", 0.0)))
    except (KeyError, ValueError) as exc:
        raise CommandError(str(exc)) from exc


def _v_walk(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Drape along a walk or a run, carrying the cloth forward frame to frame.

    The frame rate is the only timing knob on purpose: how much cloth time one
    animation frame gets is DERIVED from it, because it is not free. See the
    note in `animation.animate` about the 270 mm slide.
    """
    from seamkiln.animation import animation_report
    from seamkiln.avatar import gait as make_gait
    from seamkiln.avatar import walk as walk_along
    from seamkiln.drape.solve import DrapeSettings

    garment = _need_garment(session, "walk")
    height = float(session.body_spec.get("stature_m", 1.75))
    kind = session.body_spec.get("kind", "mannequin")
    note = None
    # The body that walks is the SESSION'S body. It was not: this verb built
    # a posed mannequin whatever body had been chosen, so 'walk' on a figure
    # or an imported avatar quietly animated something else.
    if kind == "figure":
        from seamkiln.avatar import figure_factory

        factory = figure_factory(
            height=height,
            facing_deg=float(session.body_spec.get("facing_deg", 0.0)),
            build=str(session.body_spec.get("build", "male")),
            chest_m=session.body_spec.get("chest_m"),
        )
    elif kind in ("mannequin", "posed"):
        factory = None  # the animator's own posed mannequin
    elif session.rig is not None:
        # A65 P5b: an imported body WITH a skeleton articulates like the
        # figure does. The gait's scripted rise is dropped on purpose - with
        # the feet put on the ground each frame the pelvis rises because the
        # stance leg straightens, which is the whole reason to bend a body
        # rather than slide it.
        from seamkiln.avatar import rigged_factory

        factory = rigged_factory(session.rig)
    else:
        from seamkiln.avatar import rigid_factory

        factory = rigid_factory(session.body)
        note = (
            f"a {kind!r} body has no joints to swing, so it travels as one piece "
            "with the gait's rise; use body kind 'figure' for articulated limbs, "
            "or import a glTF that carries a skin"
        )
    try:
        track = make_gait(
            str(args.get("gait", "walk")),
            cycles=float(args.get("cycles", 1.0)),
            samples_per_cycle=int(args.get("samples_per_cycle", 8)),
        )
        frames = walk_along(
            garment,
            track,
            fabric=session.fabric,
            fps=float(args.get("fps", 12.0)),
            voxel_mm=float(args.get("voxel_mm", 10.0)),
            height=height,
            body_factory=factory,
            settings=DrapeSettings(substeps=int(args.get("substeps", 24))),
            travel=bool(args.get("travel", False)),
            heading=tuple(args.get("heading", (0.0, 0.0, 1.0))),
        )
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
    session.gait = track
    session.animation = frames  # held like animate's, so an export can reach them
    if frames:
        session.garment.points = frames[-1].points
        session.drape = None  # the last frame is a POSE, not the rest drape
    hem = [float(f.points[:, 1].min()) for f in frames]
    return {
        **track.as_dict(),
        **animation_report(frames),
        **({"note": note} if note else {}),
        "body": kind,
        "travelled_m": round(
            float(np.linalg.norm(frames[-1].points.mean(axis=0) - frames[0].points.mean(axis=0)))
            if len(frames) > 1
            else 0.0,
            3,
        ),
        "hem_swing_mm": round((max(hem) - min(hem)) * 1000.0, 1),
        "rise_mm": round(
            (float(frames[0].points[:, 1].mean()) - float(frames[-1].points[:, 1].mean()))
            * -1000.0,
            1,
        )
        if frames
        else 0.0,
        "seam_max_mm": round(max(f.report["seam_gaps"]["max_gap_mm"] for f in frames), 1)
        if frames
        else 0.0,
    }


def _v_handoff(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    """Hand the garment to the next application, in ITS coordinates."""
    from seamkiln.handoff import bundle, ops_for

    _need_garment(session, "hand off")
    out = args.get("out")
    if not out:
        raise CommandError("handoff needs 'out' - the directory to write into.")
    try:
        made = bundle(
            session,
            out,
            target=str(args.get("target", "blender")),
            fmt=str(args["format"]) if "format" in args else None,
            hardware=bool(args.get("hardware", True)),
        )
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
    session.handoffs.append(made)
    result = made.summary()
    try:
        result["ops"] = ops_for(made)
    except ValueError as exc:
        result["ops"] = None
        result["why_no_ops"] = str(exc)
    return result


def _v_unfasten(session: Session, args: dict[str, Any]) -> dict[str, Any]:
    from seamkiln.hardware.buttons import apply, unfasten

    garment = _need_garment(session, "unfasten")
    which = str(args.get("id", ""))
    matches = [f for f in session.buttons if f.id == which]
    if not matches:
        known = ", ".join(f.id for f in session.buttons) or "none"
        raise CommandError(f"no button called {which!r} (fastened: {known}).")
    try:
        unfasten(matches[0])
    except ValueError as exc:
        raise CommandError(str(exc)) from exc
    apply(garment, session.buttons)
    _redrape(session, args)
    return {"undone": which, "still_fastened": len([f for f in session.buttons if not f.popped])}


_VERBS = {
    "block": _v_block,
    "load": _v_load,
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
    "lock": _v_lock,
    "unlock": _v_unlock,
    "grade": _v_grade,
    "cut": _v_cut,
    "rip": _v_rip,
    "pinch": _v_pinch,
    "lace": _v_lace,
    "finish": _v_finish,
    "animate": _v_animate,
    "zip": _v_zip,
    "unzip": _v_unzip,
    "button": _v_button,
    "unfasten": _v_unfasten,
    "handoff": _v_handoff,
    "walk": _v_walk,
    "pull": _v_pull,
    "fold": _v_fold,
    "ease": _v_ease,
}

VERBS = tuple(sorted(_VERBS))
