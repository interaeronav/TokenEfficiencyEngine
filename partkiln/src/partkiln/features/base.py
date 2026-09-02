"""The feature record and the one `apply` pattern every feature shares.

resolve refs -> build with brep -> record history -> name -> measure -> details.

A `Feature` is what the document keeps per verb: its args (the script), the
shape AFTER it, the hand-built history map from its input to that shape (how
names survive a regen, D6), the role names it materialised, its tool bodies
(what a pattern or a mirror copies), and the scalars the diff reports (D7:
volume, delta, unique counts - Law 20 - assumed, resolved, names). Nothing
here holds a coordinate list; `details()` is what goes on the wire.

Law 11 lives in `boolean()`: a cut, join, intersect or hole whose result has
the base's unique face AND edge counts AND its volume (1e-9 relative) is a
failed boolean and refuses `pk_no_effect` unless `allow_no_effect`. Measured
(A66 P0a): glue mode returned the UNCUT plate with `IsDone() == True`, which
is exactly the silent failure this refusal exists for.

Rounding: volumes to 3 dp (the fixture table pins 59 214.602, so the 2 dp of
D7's prose would lose the pin; recorded as a deviation), lengths 3 dp.
Statuses: ok | failed | suppressed | cached (restored from a .brep, not
rebuilt in this process). OCP is imported inside functions only.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from partkiln._errors import KernelError
from partkiln.document import CommandError
from partkiln.naming import NameEntry, Resolved, materialise, resolve

Vec3 = tuple[float, float, float]

_MODES = ("new", "join", "cut", "intersect")


def r3(x: float) -> float:
    return round(float(x), 3) + 0.0


def bbox_fields(bb: Sequence[float]) -> dict[str, Any]:
    """`bbox_mm` is the EXTENTS [dx, dy, dz] (D7, W1: `bbox_mm:[120,80,10]`), the
    same key and meaning `checks.mass.mass_properties` reports, with the corners
    under `bbox_min` / `bbox_max` for the caller that needs a position."""
    if len(bb) != 6:
        return {"bbox_mm": []}
    x0, y0, z0, x1, y1, z1 = bb
    return {
        "bbox_mm": [r3(x1 - x0), r3(y1 - y0), r3(z1 - z0)],
        "bbox_min": [r3(x0), r3(y0), r3(z0)],
        "bbox_max": [r3(x1), r3(y1), r3(z1)],
    }


@dataclass
class Outcome:
    """What a kind's builder hands back to `build()`.

    `names` are (name, role, sub-shape IN `shape`); `tools` are the bodies
    the feature added or removed BEFORE the boolean (a pattern copies them)
    with `tool_roles` = (role, sub-shape on the tool) so the copies can be
    named the same way; `extra` joins the details verbatim (scalars only).
    """

    shape: Any
    history: Any = None
    names: list[tuple[str, str, Any]] = field(default_factory=list)
    tools: list[Any] = field(default_factory=list)
    tool_roles: list[tuple[str, Any]] = field(default_factory=list)
    mode: str = ""
    resolved: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    failed_edges: list[str] = field(default_factory=list)
    frame: Any = None
    cosmetic: dict[str, Any] = field(default_factory=dict)
    no_effect: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Feature:
    id: str
    kind: str
    args: dict[str, Any]
    status: str = "ok"
    error: str = ""
    shape: Any = field(default=None, repr=False, compare=False)
    history: Any = field(default=None, repr=False, compare=False)
    tools: list[Any] = field(default_factory=list, repr=False, compare=False)
    tool_roles: list[tuple[str, Any]] = field(default_factory=list, repr=False, compare=False)
    mode: str = ""
    frame: Any = None
    names: list[str] = field(default_factory=list)
    volume: float = 0.0
    delta_mm3: float = 0.0
    faces: int = 0
    edges: int = 0
    solids: int = 0
    bbox: tuple[float, ...] = ()
    assumed: dict[str, Any] = field(default_factory=dict)
    resolved: dict[str, Any] = field(default_factory=dict)
    selected: dict[str, list[str]] = field(default_factory=dict)
    seam_excluded: int = 0
    notes: list[str] = field(default_factory=list)
    failed_edges: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    depends: set[str] = field(default_factory=set)
    param_deps: set[str] = field(default_factory=set)
    cosmetic: dict[str, Any] = field(default_factory=dict)
    suppressed: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def __deepcopy__(self, memo: dict[int, Any]) -> Feature:
        # OCCT handles are immutable values here (no feature mutates a shape in
        # place), so the snapshot Law 16 takes per command shares them and
        # copies only the Python side - deepcopy of a pybind object would fail.
        twin = Feature(self.id, self.kind, copy.deepcopy(self.args, memo))
        for key, value in self.__dict__.items():
            if key in ("id", "kind", "args"):
                continue
            if key in ("shape", "history", "tools", "tool_roles", "frame"):
                setattr(twin, key, list(value) if isinstance(value, list) else value)
            else:
                setattr(twin, key, copy.deepcopy(value, memo))
        return twin

    @property
    def active(self) -> bool:
        return self.status == "ok" and not self.suppressed

    def signature(self) -> tuple[Any, ...]:
        """What 'unchanged' compares after a regen (Law 14): the feature's OWN
        contribution - its delta, the faces it named, its resolved counts and
        its status - not the whole body, which every upstream edit changes."""
        return (
            self.status,
            r3(self.delta_mm3),
            len(self.names),
            tuple(sorted((k, v) for k, v in self.resolved.items() if isinstance(v, int))),
            tuple(self.failed_edges),
        )

    def details(self) -> dict[str, Any]:
        """The D7 per-op details: scalars only, names <= 8 then a count."""
        out: dict[str, Any] = {
            "id": f"feat:{self.id}",
            "kind": self.kind,
            "status": "suppressed" if self.suppressed else self.status,
        }
        if self.status == "failed":
            out["error"] = self.error
            return out
        out.update(
            {
                "volume_mm3": r3(self.volume),
                "delta_mm3": r3(self.delta_mm3),
                **bbox_fields(self.bbox),
                "faces": self.faces,
                "edges": self.edges,
                "solids": self.solids,
            }
        )
        if self.mode:
            out["mode"] = self.mode
        if self.assumed:
            out["assumed"] = dict(self.assumed)
        if self.resolved:
            out["resolved"] = dict(self.resolved)
        if self.selected:
            out["selected"] = dict(self.selected)
        if self.seam_excluded:
            out["seam_excluded"] = self.seam_excluded
        if self.names:
            out["names"] = materialise(self.names)
        if self.failed_edges:
            out["failed"] = list(self.failed_edges)
        if self.frame is not None:
            out["frame"] = self.frame.as_dict()
        if self.cosmetic:
            out["cosmetic"] = dict(self.cosmetic)
        if self.notes:
            out["notes"] = list(self.notes)
        out.update(self.extra)
        return out

    def row(self) -> dict[str, Any]:
        """The concise tree row (~20 tokens)."""
        row: dict[str, Any] = {
            "id": f"feat:{self.id}",
            "kind": self.kind,
            "status": "suppressed" if self.suppressed else self.status,
        }
        if self.status == "ok" and not self.suppressed:
            row["volume_mm3"] = r3(self.volume)
            row["delta_mm3"] = r3(self.delta_mm3)
            row["faces"] = self.faces
        if self.refs:
            row["refs"] = list(self.refs)[:4]
        return row


Builder = Callable[[Any, Any, Feature, dict[str, Any]], Outcome]
BUILDERS: dict[str, Builder] = {}


def builder(kind: str) -> Callable[[Builder], Builder]:
    def wrap(fn: Builder) -> Builder:
        BUILDERS[kind] = fn
        return fn

    return wrap


# --------------------------------------------------------------------------- helpers


def get_part(doc: Any, args: dict[str, Any], assumed: dict[str, Any]) -> Any:
    """The part an op works on: `part`, else the only part, else a refusal."""
    raw = args.get("part")
    if raw is not None:
        name = str(raw)[5:] if str(raw).startswith("part:") else str(raw)
        part = doc.parts.get(name)
        if part is None:
            known = ", ".join(f"part:{n}" for n in sorted(doc.parts)) or "(none)"
            raise CommandError(f"no part {raw!r}. Parts: {known}.", code="pk_ref_unknown")
        return part
    if not doc.parts:
        raise CommandError(
            "no part yet. Create one first: {op: create, kind: part, name: <n>}.",
            code="pk_ref_unknown",
        )
    if len(doc.parts) > 1:
        raise CommandError(
            f"the document has {len(doc.parts)} parts ({', '.join(sorted(doc.parts))}); "
            "say which with part: <name>.",
            code="pk_part_ambiguous",
        )
    return next(iter(doc.parts.values()))


def parse_mode(args: dict[str, Any], part: Any, assumed: dict[str, Any]) -> str:
    raw = args.get("mode")
    if raw is None:
        mode = "new" if part.shape is None else "join"
        assumed["mode"] = mode
        return mode
    mode = str(raw).lower()
    if mode not in _MODES:
        raise CommandError(f"mode {raw!r} is not one of {', '.join(_MODES)}.", code="pk_needs")
    if mode == "new" and part.shape is not None:
        raise CommandError(
            f"part {part.name} already has a body; mode new would make a second one. "
            "Use join, cut or intersect, or create another part.",
            code="pk_needs",
        )
    if mode != "new" and part.shape is None:
        raise CommandError(
            f"part {part.name} is empty; mode {mode} needs a body to act on. Use mode new "
            "(or leave mode out).",
            code="pk_needs",
        )
    return mode


def refs_of(feature: Feature, *values: Any) -> None:
    """Record the reference strings a feature used (for dependents and rows)."""
    for v in values:
        if isinstance(v, list | tuple):
            refs_of(feature, *v)
        elif isinstance(v, str) and v and v not in feature.refs:
            feature.refs.append(v)


def one(part: Any, feature: Feature, ref: Any, kind: str, what: str) -> Resolved:
    if ref is None or ref == "":
        raise CommandError(
            f"{feature.kind} {feature.id} needs {what}: a {kind} name (e.g. plate.end) or a "
            f"selector ({part.name}:{kind}s(...)).",
            code="pk_needs",
        )
    res = resolve(part, ref, kind, "one")
    _note(feature, res)
    refs_of(feature, ref)
    return res


def many(part: Any, feature: Feature, ref: Any, kind: str, what: str) -> Resolved:
    if ref is None or ref == "" or ref == []:
        raise CommandError(
            f"{feature.kind} {feature.id} needs {what}: {kind} names or a selector "
            f"({part.name}:{kind}s(...)).",
            code="pk_needs",
        )
    res = resolve(part, ref, kind, "many")
    _note(feature, res)
    refs_of(feature, ref)
    return res


def _note(feature: Feature, res: Resolved) -> None:
    feature.resolved.update(res.echo())
    feature.selected.update(res.selected())
    feature.seam_excluded += res.seam_excluded
    if res.how == "fingerprint":
        feature.notes.append(
            f"{res.ref} no longer exists by that name; resolved by fingerprint to "
            f"{', '.join(res.names[:4])}"
        )


def boolean(
    base: Any,
    tools: Sequence[Any],
    mode: str,
    feature: Feature,
    allow_no_effect: bool = False,
    touching: bool = False,
) -> tuple[Any, Any]:
    """ONE boolean (`join` fuse / `cut` / `intersect` common) then unify, with
    the two histories merged into one map. Refuses `pk_no_effect` (Law 11)."""
    from partkiln.brep import history, shapes

    if mode == "join":
        res = shapes.fuse([base, *tools], touching=touching)
    elif mode == "cut":
        res = shapes.cut(base, list(tools))
    elif mode == "intersect":
        if len(tools) != 1:
            raise CommandError(
                f"{feature.kind} {feature.id}: intersect takes exactly one tool.", code="pk_needs"
            )
        res = shapes.common(base, tools[0])
    else:
        raise CommandError(f"mode {mode!r} is not a boolean.", code="pk_needs")
    if not res.is_done:
        raise CommandError(
            f"{feature.kind} {feature.id}: the {mode} did not complete in OCCT. Check that the "
            "profile lies on the body and is not tangent to a face.",
            code="pk_op_failed",
        )
    if res.empty:
        raise CommandError(
            f"{feature.kind} {feature.id}: the {mode} left NO solid (the tool consumed or "
            "missed the whole body). Check the direction and the distance.",
            code="pk_no_effect",
        )
    if res.no_effect:
        if not allow_no_effect:
            raise CommandError(
                f"{feature.kind} {feature.id}: the {mode} changed nothing - the body still has "
                f"{res.counts_after['faces']} faces, {res.counts_after['edges']} edges and "
                f"{r3(res.volume_after)} mm3. The tool misses the body (Law 11). Check the "
                "position, direction and distance, or pass allow_no_effect: true.",
                code="pk_no_effect",
            )
        feature.notes.append(f"{mode} changed nothing (allow_no_effect)")
    merged = history.from_algo(res.history)
    unified, uh = shapes.unify(res.shape)
    merged.merge(uh)
    return unified, merged


def follow(
    history_map: Any, shape: Any, subshape: Any, present: list[Any] | None = None
) -> list[Any]:
    """Successors of a tool/input sub-shape that are IN `shape` (unique faces).

    `present` is the shape's unique sub-shapes of that kind, passed in by
    callers that follow many sub-shapes into one shape (a 99-copy pattern)."""
    from partkiln.brep import shapes

    succ = [subshape] if history_map is None else history_map.successors(subshape)
    if present is None:
        present = shapes.unique_subshapes(shape, subshape.ShapeType())
    hits: list[Any] = []
    for s in succ:
        for p in present:
            if p.IsSame(s) and not any(p.IsSame(h) for h in hits):
                hits.append(p)
    return hits


def name_from_tool(
    history_map: Any, shape: Any, prefix: str, tool_roles: Sequence[tuple[str, Any]]
) -> list[tuple[str, str, Any]]:
    """Materialise `<prefix>.<role>` for every tool sub-shape that survived the
    boolean; a role that fanned out into k faces becomes `<prefix>.<role>[k]`."""
    from OCP.TopAbs import TopAbs_FACE

    from partkiln.brep import query, shapes

    present = shapes.unique_subshapes(shape, TopAbs_FACE)
    out: list[tuple[str, str, Any]] = []
    for role, sub in tool_roles:
        hits = follow(history_map, shape, sub, present)
        if len(hits) == 1:
            out.append((f"{prefix}.{role}", role, hits[0]))
        elif hits:
            ranked = sorted(
                hits,
                key=lambda h: tuple(round(c, 3) for c in query.faces(h)[0].centroid),
            )
            for k, h in enumerate(ranked):
                out.append((f"{prefix}.{role}[{k}]", role, h))
    return out


def measure(feature: Feature, before: Any, after: Any) -> None:
    from partkiln.brep import shapes

    feature.volume = shapes.volume(after) if after is not None else 0.0
    v0 = shapes.volume(before) if before is not None else 0.0
    feature.delta_mm3 = feature.volume - v0
    counts = shapes.counts(after) if after is not None else {"faces": 0, "edges": 0, "solids": 0}
    feature.faces, feature.edges, feature.solids = (
        counts["faces"],
        counts["edges"],
        counts["solids"],
    )
    feature.bbox = tuple(shapes.bbox(after)) if after is not None else ()


def build(doc: Any, part: Any, feature: Feature, index: int, assumed: dict[str, Any]) -> None:
    """Run the kind's builder at `index` in `part`, then record, name and measure.

    Raises the builder's refusal (a `CommandError`); the caller decides whether
    that is a refused command (creation) or a `failed` feature (regen, Law 14).
    """
    from partkiln.brep import fingerprint

    fn = BUILDERS.get(feature.kind)
    if fn is None:
        raise CommandError(
            f"no builder for feature kind {feature.kind!r}. Kinds: {', '.join(sorted(BUILDERS))}.",
            code="pk_bad_op",
        )
    before = part.shape
    feature.resolved, feature.notes, feature.names = {}, [], []
    feature.selected, feature.seam_excluded = {}, 0
    feature.failed_edges, feature.refs, feature.depends = [], [], set()
    feature.param_deps, feature.extra = set(), {}
    feature.error = ""
    if feature.suppressed:
        feature.status = "ok"
        feature.shape, feature.history, feature.tools, feature.tool_roles = before, None, [], []
        measure(feature, before, before)
        return
    try:
        outcome = fn(doc, part, feature, assumed)
    except KernelError as exc:
        raise CommandError(
            f"{feature.kind} {feature.id}: {exc.message}" + (f" Fix: {exc.fix}" if exc.fix else ""),
            code=exc.code if exc.code != "pk_op_failed" else "pk_op_failed",
        ) from exc
    feature.shape = outcome.shape
    feature.history = outcome.history
    feature.tools = list(outcome.tools)
    feature.tool_roles = list(outcome.tool_roles)
    feature.mode = outcome.mode
    feature.frame = outcome.frame
    feature.resolved.update(outcome.resolved)
    feature.notes.extend(outcome.notes)
    feature.failed_edges = list(outcome.failed_edges)
    feature.cosmetic = dict(outcome.cosmetic)
    feature.extra = dict(outcome.extra)
    feature.assumed = {k: v for k, v in assumed.items() if k not in ("units", "angle_unit")}
    feature.status = "ok"
    part.retire(part.names.drop_feature(feature.id))
    for name, role, sub in outcome.names:
        key = fingerprint.subshape_fingerprint(sub)
        part.names.add(NameEntry(name, "face", feature.id, role, index, key, sub))
        part.stale.remove(name)
        feature.names.append(name)
    measure(feature, before, outcome.shape)
    part.shape = outcome.shape
    part.invalidate()


__all__ = [
    "BUILDERS",
    "Feature",
    "Outcome",
    "Vec3",
    "bbox_fields",
    "boolean",
    "build",
    "builder",
    "follow",
    "get_part",
    "many",
    "measure",
    "name_from_tool",
    "one",
    "parse_mode",
    "r3",
    "refs_of",
]
