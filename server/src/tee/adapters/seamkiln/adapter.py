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

# measured: a .pth written after startup stays invisible (invalidate_caches() too) until restart
INSTALL_HINT = (
    "seamkiln is not installed. From the repo root: "
    "uv pip install --python <this interpreter> -e seamkiln, then restart the server"
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
        self._session = None  # built lazily: seamkiln may not be installed
        self._epoch = 0

    @property
    def session(self):
        """The document. One per adapter, shared with every other client."""
        if self._session is None:
            _need_seamkiln()
            from seamkiln.session import Session

            self._session = Session()
        return self._session

    # Loose attributes the rest of TEE (and the benchmark) reads. They are
    # views on the session, never a second copy - a second copy is how a GUI
    # and a script drift apart, which is the failure this whole design avoids.
    @property
    def _pattern(self):
        return None if self._session is None else self._session.pattern

    @property
    def _body(self):
        return None if self._session is None else self._session.body

    @property
    def _sdf(self):
        return None if self._session is None else self._session.sdf

    @property
    def _garment(self):
        return None if self._session is None else self._session.garment

    @property
    def _drape(self):
        return None if self._session is None else self._session.drape

    @property
    def _fabric(self):
        return "cotton_jersey" if self._session is None else self._session.fabric

    @property
    def _body_spec(self):
        return {} if self._session is None else self._session.body_spec

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
        # A55-A58 state was invisible here: a zipped, buttoned, locked garment on
        # a walking figure listed exactly what a bare tee on a mannequin did.
        # Everything a batch can change is an entity, or a diff cannot name it.
        session = self.session
        for opening, fitted in getattr(session, "zippers", {}).items():
            entities.append(
                Entity(id=f"zip:{opening}", name=opening, kind="zipper", summary=fitted.summary())
            )
        for fastening in getattr(session, "buttons", []):
            entities.append(
                Entity(
                    id=f"button:{fastening.id}",
                    name=fastening.id,
                    kind="button",
                    summary=fastening.summary(),
                )
            )
        locks = getattr(session, "locks", None)
        if locks is not None and locks.held:
            entities.append(Entity(id="locks", name="locks", kind="locks", summary=locks.as_dict()))
        if session.body is not None:
            spec = dict(getattr(session, "body_spec", {}) or {})
            body = {k: v for k, v in spec.items() if k != "pose"}
            if getattr(session, "arrangement", ""):
                body["arrangement"] = session.arrangement
            if getattr(session, "avatar", None):
                body["avatar"] = {
                    k: v for k, v in session.avatar.items() if k in ("kind", "height_m", "units_in")
                }
            entities.append(Entity(id="body", name="body", kind="body", summary=body))
        return entities

    def execute(self, batch: list[dict[str, Any]]) -> Diff:
        _need_seamkiln()
        diff = Diff()
        for index, op in enumerate(batch):
            _apply_translated(self, op, index, diff)
        self._epoch += 1
        return diff

    def snapshot(self, label: str) -> dict[str, Any]:
        """Checkpoint the pattern and the drape. Spilled to disk, not inlined."""
        if self._pattern is None:
            return {"label": label, "empty": True}
        self.workdir.mkdir(parents=True, exist_ok=True)
        stamp = f"{label}-{self._epoch}-{int(time.time() * 1000)}"
        path = self.workdir / f"{stamp}.json"
        # The checkpoint IS the script. Nothing else can drift from it, and
        # it doubles as the export a caller can replay anywhere.
        payload = {"script": self.session.script()}
        payload["fingerprint"] = self.session.fingerprint()
        path.write_text(json.dumps(payload))
        return {
            "label": label,
            "path": str(path),
            "epoch": self._epoch,
            "commands": len(self.session.history),
        }

    def restore(self, payload: dict[str, Any]) -> None:
        if payload.get("empty"):
            self._session = None
            return
        path = Path(payload["path"])
        if not path.is_file():
            raise TeeError(
                "seamkiln_checkpoint_missing",
                f"checkpoint {path} is gone.",
                fix="Checkpoints live under .tee/seamkiln; tee_purge may have reclaimed it.",
            )
        from seamkiln.session import Session

        data = json.loads(path.read_text())
        # Replay, do not deserialise. A checkpoint that rebuilds by running
        # the same commands cannot restore a state the commands could not
        # produce, which is a stronger guarantee than any schema.
        self._session = Session.replay(data["script"])
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


# -- ops: a translation layer, not a second implementation --------------------
#
# Every verb here becomes a seamkiln Command and goes through Session.apply.
# That is the point: the Qt shell, a plain script and this adapter all drive
# the SAME code, so a garment built through TEE exports as a script that
# reproduces it, and there is no path through one client that another cannot
# take. The adapter's remaining job is translation - wire shapes in, Diffs out.


def _panel_id(raw: str) -> str:
    return raw.split(":", 1)[1] if raw.startswith("panel:") else raw


def _translate(op: dict[str, Any], index: int) -> list[dict[str, Any]]:
    """One wire op -> the seamkiln commands that carry it out."""
    verb = op.get("op")
    props = dict(op.get("props") or {})

    if verb == "create":
        kind = op.get("kind")
        if kind == "block":
            return [{"op": "block", "args": props}]
        if kind == "panel":
            return [{"op": "panel", "args": {**props, "id": op.get("name")}}]
        if kind == "seam":
            return [{"op": "seam", "args": {**props, "id": op.get("name")}}]
        raise TeeError(
            "seamkiln_bad_kind",
            f"batch[{index}]: cannot create kind {kind!r}.",
            fix="Kinds: panel, seam, block.",
        )
    if verb == "set":
        if "seam_allowance_mm" not in props:
            raise TeeError(
                "seamkiln_bad_set",
                f"batch[{index}]: nothing settable in {sorted(props)}.",
                fix="Settable: seam_allowance_mm.",
            )
        return [
            {
                "op": "allowance",
                "args": {
                    "mm": props["seam_allowance_mm"],
                    "panels": [_panel_id(str(op.get("id") or ""))],
                },
            }
        ]
    if verb == "delete":
        return [{"op": "delete", "args": {"id": _panel_id(str(op.get("id") or ""))}}]
    if verb == "arrange":
        body_keys = (
            "body",
            "stature_m",
            "chest_m",
            "voxel_mm",
            "gender",
            "age",
            "muscle",
            "weight",
            "height",
            "proportions",
        )
        body_args = {k: v for k, v in props.items() if k in body_keys}
        body_args["kind"] = body_args.pop("body", "mannequin")
        arrange_args: dict[str, Any] = {
            "particle_distance_mm": props.get("particle_distance_mm", DEFAULT_PARTICLE_MM)
        }
        # a pattern from CAD is named by its maker: the roles say which piece
        # is the front, the back and each sleeve (see `piece_roles`)
        for key in ("roles", "arrangement", "dress", "baste_sleeves", "baste_head_mm"):
            if key in props:
                arrange_args[key] = props[key]
        return [
            {"op": "body", "args": body_args},
            {"op": "arrange", "args": arrange_args},
        ]
    # A54 verbs pass straight through: they are already seamkiln Commands and
    # the adapter has nothing to translate. One tuple means a verb added to
    # the session reaches TEE by being named once.
    if verb in _PASSTHROUGH:
        return [{"op": verb, "args": props}]
    raise TeeError(
        "seamkiln_bad_op",
        f"batch[{index}]: unknown op {verb!r}.",
        fix=f"seamkiln accepts: {', '.join(sorted(_WIRE_OPS))}.",
    )


_PASSTHROUGH = (
    "load",
    "sew",
    "drape",
    "export",
    "grade",
    "cut",
    "rip",
    "pinch",
    "lace",
    "finish",
    "animate",
    "techpack",
    "fit",
    # A55/A56: locks and hardware. Same rule - a verb added to the Session
    # reaches TEE by being named once, here.
    "lock",
    "unlock",
    "zip",
    "unzip",
    "button",
    "unfasten",
    "handoff",
    "walk",
    "pull",
    "fold",
    "ease",
)
_WIRE_OPS = ("create", "set", "delete", "arrange", *_PASSTHROUGH)


def _apply_translated(adapter: SeamkilnAdapter, op: dict, index: int, diff: Diff) -> None:
    from seamkiln.session import Command, CommandError

    for raw in _translate(op, index):
        try:
            result = adapter.session.apply(Command.from_dict(raw))
        except CommandError as exc:
            raise TeeError(
                f"seamkiln_{raw['op']}_refused",
                f"batch[{index}]: {exc}",
                fix=str(exc),
            ) from exc
        _record(adapter, raw["op"], result, diff)


def _record(adapter: SeamkilnAdapter, verb: str, result: dict, diff: Diff) -> None:
    """Turn one command's result into diff entries the kernel understands."""
    if verb == "block":
        for panel in adapter.session.pattern.panels:
            entity = _panel_entity(panel)
            diff.created.append(entity.id)
            diff.upserts.append(entity)
        diff.notes.append(f"block: {len(result['panels'])} panels, {result['seams']} seams")
    elif verb == "load":
        for panel in adapter.session.pattern.panels:
            entity = _panel_entity(panel)
            diff.created.append(entity.id)
            diff.upserts.append(entity)
        diff.notes.append(
            f"load: {len(result['panels'])} pieces from {Path(result['path']).name}, "
            f"unit from {result['units_source']}"
            + (f"; {'; '.join(result['notes'])}" if result.get("notes") else "")
        )
    elif verb == "panel":
        entity = _panel_entity(adapter.session.pattern.panel(result["id"]))
        diff.created.append(entity.id)
        diff.details[entity.id] = entity.detailed()
        diff.upserts.append(entity)
    elif verb == "seam":
        diff.created.append(f"seam:{result['id']}")
    elif verb == "allowance":
        for panel_id in result["panels"]:
            entity = _panel_entity(adapter.session.pattern.panel(panel_id))
            diff.modified.append(entity.id)
            diff.details[entity.id] = entity.detailed()
            diff.upserts.append(entity)
    elif verb == "delete":
        diff.deleted.append(f"panel:{result['deleted']}")
    elif verb == "body":
        diff.notes.append(
            f"body: {result['kind']}, chest {result['measurements']['chest_girth_mm']:.0f} mm"
        )
    elif verb == "arrange":
        diff.modified.append("garment")
        diff.details["garment"] = result
        diff.notes.append(
            f"arranged {result['points']} points; {result['seams_flipped']} seams auto-flipped"
        )
    elif verb == "drape":
        diff.modified.append("garment")
        diff.details["garment"] = result
        if not result.get("contact", {}).get("worn"):
            diff.notes.append(
                "the garment is NOT being worn - it came off the body. Check the "
                "arrangement, the particle distance, or whether the pattern fits."
            )
    elif verb == "export":
        diff.modified.append("export")
        diff.details.setdefault("export", {}).update(result)
        diff.notes.append(f"exported: {result.get('path')}")
    elif verb in ("grade", "cut"):
        for panel in adapter.session.pattern.panels:
            entity = _panel_entity(panel)
            diff.modified.append(entity.id)
            diff.upserts.append(entity)
        diff.details[verb] = result
    elif verb in ("rip", "pinch", "lace", "finish", "animate"):
        diff.modified.append("garment")
        diff.details[verb] = result
        if verb == "rip" and result.get("tears"):
            diff.notes.append(
                f"{len(result['tears'])} seam(s) gave way; "
                f"{result['fray']['threads']} frayed threads"
            )
    elif verb in ("fit", "techpack") or verb in ("lock", "unlock"):
        diff.details[verb] = result
    elif verb in ("zip", "unzip"):
        diff.modified.append("garment")
        diff.details[verb] = result
        # A zipper's whole point is that it is sometimes open. Say which, in
        # one line, rather than making the model read six numbers to find out.
        opened = result.get("open_percent", 0.0)
        diff.notes.append(
            f"{result['id']}: {result['material']} {result['size']} "
            + ("closed" if opened <= 0.0 else f"{opened:.0f}% open")
            + (
                f", closed part at {result['closed_gap_mm']} mm"
                if result.get("closed_gap_mm")
                else ""
            )
        )
    elif verb in ("pull", "fold", "ease"):
        diff.modified.append("garment")
        diff.details[verb] = result
        rate = result.get("rate") or {}
        if rate.get("ms_per_step"):
            diff.notes.append(
                f"{verb}: {rate['steps']} step(s) at {rate['ms_per_step']} ms "
                f"({rate['fps']} fps on {rate['particles']} particles)"
            )
    elif verb == "walk":
        diff.modified.append("garment")
        diff.details["walk"] = result
        diff.notes.append(
            f"{result['gait']}: {result['frames']} frames over {result['duration_s']}s, "
            f"hem swing {result['hem_swing_mm']} mm, worn throughout: {result['worn_throughout']}"
        )
    elif verb == "handoff":
        diff.details["handoff"] = result
        diff.notes.append(
            f"handoff to {result['target']}: {', '.join(sorted(result['files']))} "
            f"({result['units']}, {result['up']}-up)"
        )
    elif verb in ("button", "unfasten"):
        diff.modified.append("garment")
        diff.details[verb] = result
        if result.get("unresolved_rim"):
            diff.notes.append(f"button rim not resolved: {result['unresolved_rim']}")


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
