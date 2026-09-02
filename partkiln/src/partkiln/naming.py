"""Names and selectors: how a model addresses a face or an edge, and never an index.

Law 13: a sub-shape is addressed by NAME. Every feature materialises role
names for what it creates (`plate.end`, `plate.side.r.0`, `h.1.wall`,
`f1.face[0]`, `sh.inner[2]`), and an edge is named by the two faces it
joins (`plate.end|plate.side.r.0`; a seam, which has one face, is
`h.1.wall~seam`). A name is resolved against the CURRENT shape in this order
(D6): the exact name -> its history successors (the sub-shape recorded when
the feature was built, followed through every later feature's hand-built
history, fan-out kept as `name[k]`) -> a fingerprint match within 1e-3 mm
(the same rounded (type, size, centroid, normal, radius) tuple, which is what
survives a rename) -> `pk_ref_stale` naming the history event that removed
it, the nearest candidate with its distance, and a selector that would
survive the regen. An explorer index never enters.

Selectors are declarative strings evaluated at regen and MATERIALISED to
names in the diff: `<part|feature>:faces(<filters>)` / `:edges(<filters>)`.
The name before the colon is a part first, then a feature (a feature's scope
is the faces it named and their edges). Filters: `normal=+Z`, `dir=Z` (line
edges, either sign), `of=<role>` (the face `<feature>.<role>`; `loop=outer|
inner` then picks its wires), `type=plane|cyl|cone|sphere|torus|bspline|
line|circle`, `r=<mm>`, `len><mm>`, `len<<mm>`, `area><mm2>`, `convex|
concave|tangent`, `nearest=[x,y,z]`, `created_by=<feature>`, `not(<filter>)`
and `seams` (keep them). Seam edges are EXCLUDED by default and counted in
`seam_excluded`: measured (A66 P0a), F1's fifth `dir=Z` edge is the
cylinder seam, which OCCT accepts in a fillet and generates nothing for.
Cardinality is declared by the consuming field: `on` needs exactly one,
`edges`/`faces` take many; 0 -> `pk_ref_empty` naming the filter that
killed the last candidates, >1 where 1 is needed -> `pk_ref_ambiguous` with
the candidates. OCP is imported inside functions only.
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from partkiln.document import CommandError

SubshapeKey = tuple[str, float, tuple[float, ...], tuple[float, ...] | None, float | None]

_SELECTOR = re.compile(
    r"^\s*(?P<scope>[a-z0-9_.]+)\s*:\s*(?P<kind>faces|edges)\s*\((?P<filters>.*)\)\s*$"
)
_TYPE_ALIASES = {"cyl": "cylinder", "cylinder": "cylinder", "plane": "plane", "cone": "cone"}
_KEY_TOL = 1e-3


# --------------------------------------------------------------------------- the table


@dataclass
class NameEntry:
    """One role name: what created it, its fingerprint at creation, and (when
    this process built it) the sub-shape inside the creating feature's result
    so history can follow it forward."""

    name: str
    kind: str  # face | edge
    feature: str
    role: str
    index: int  # the creating feature's position in the part's list
    key: SubshapeKey
    shape: Any = field(default=None, repr=False, compare=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "feature": self.feature,
            "role": self.role,
            "index": self.index,
            "key": list(self.key),
        }

    @staticmethod
    def from_dict(name: str, raw: dict[str, Any]) -> NameEntry:
        key = raw["key"]
        return NameEntry(
            name,
            str(raw["kind"]),
            str(raw["feature"]),
            str(raw["role"]),
            int(raw["index"]),
            (
                str(key[0]),
                float(key[1]),
                tuple(key[2]),
                None if key[3] is None else tuple(key[3]),
                None if key[4] is None else float(key[4]),
            ),
        )


class NameTable:
    """name -> NameEntry for one part. Iteration is sorted; nothing here is an index."""

    def __init__(self) -> None:
        self._entries: dict[str, NameEntry] = {}

    def __contains__(self, name: object) -> bool:
        return name in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def get(self, name: str) -> NameEntry | None:
        return self._entries.get(name)

    def add(self, entry: NameEntry) -> None:
        self._entries[entry.name] = entry

    def names(self) -> list[str]:
        return sorted(self._entries)

    def entries(self) -> list[NameEntry]:
        return [self._entries[n] for n in sorted(self._entries)]

    def of_feature(self, feature: str) -> list[NameEntry]:
        return [e for e in self.entries() if e.feature == feature]

    def drop_feature(self, feature: str) -> list[NameEntry]:
        """Remove a feature's names; the dropped entries come back so the part can
        keep them as `stale` (a reference to one is answered by fingerprint or
        refused with what happened to it)."""
        dropped = [e for e in self._entries.values() if e.feature == feature]
        for e in dropped:
            del self._entries[e.name]
        return dropped

    def drop_from(self, index: int) -> list[NameEntry]:
        dropped = [e for e in self._entries.values() if e.index >= index]
        for e in dropped:
            del self._entries[e.name]
        return dropped

    def remove(self, name: str) -> None:
        self._entries.pop(name, None)

    def as_dict(self) -> dict[str, Any]:
        return {n: self._entries[n].as_dict() for n in sorted(self._entries)}

    @staticmethod
    def from_dict(raw: dict[str, Any]) -> NameTable:
        table = NameTable()
        for name, entry in raw.items():
            table.add(NameEntry.from_dict(name, entry))
        return table

    def copy(self) -> NameTable:
        table = NameTable()
        table._entries = dict(self._entries)
        return table


# --------------------------------------------------------------------------- keys


def key_of(info: Any) -> SubshapeKey:
    """The rounded fingerprint of a `query.FaceInfo` / `EdgeInfo` (1e-3 mm)."""
    from partkiln.brep import query

    if isinstance(info, query.FaceInfo):
        return (
            info.surface_type,
            round(info.area, 3) + 0.0,
            tuple(round(c, 3) + 0.0 for c in info.centroid),
            None if info.normal is None else tuple(round(c, 3) + 0.0 for c in info.normal),
            None if info.radius is None else round(info.radius, 3) + 0.0,
        )
    return (
        info.curve_type,
        round(info.length, 3) + 0.0,
        tuple(round(c, 3) + 0.0 for c in info.midpoint),
        None if info.direction is None else tuple(round(c, 3) + 0.0 for c in info.direction),
        None if info.radius is None else round(info.radius, 3) + 0.0,
    )


def keys_match(a: SubshapeKey, b: SubshapeKey, tol: float = _KEY_TOL) -> bool:
    if a[0] != b[0]:
        return False
    if abs(a[1] - b[1]) > max(tol, 1e-6 * abs(a[1])):
        return False
    if any(abs(x - y) > tol for x, y in zip(a[2], b[2], strict=False)):
        return False
    if (a[3] is None) != (b[3] is None):
        return False
    if (
        a[3] is not None
        and b[3] is not None
        and any(abs(x - y) > tol for x, y in zip(a[3], b[3], strict=False))
    ):
        return False
    if (a[4] is None) != (b[4] is None):
        return False
    return not (a[4] is not None and b[4] is not None and abs(a[4] - b[4]) > tol)


def _centre(info: Any) -> tuple[float, ...]:
    return info.centroid if hasattr(info, "centroid") else info.midpoint


# --------------------------------------------------------------------------- inventory


@dataclass
class Inventory:
    """The current shape's faces and edges (brep.query order) with every face's
    materialised name and every edge's derived name. Built once per shape by
    `Part.inventory()`; nothing in it leaves the kernel unnamed."""

    faces: list[Any]
    edges: list[Any]
    face_names: list[str]
    edge_names: list[str]
    aliases: dict[str, int]  # every name (aliases included) -> face index
    stale: dict[str, str]  # name -> the event that removed it ("removed by hole h")

    def face_index(self, name: str) -> int | None:
        return self.aliases.get(name)

    def face_named(self, name: str) -> Any | None:
        i = self.aliases.get(name)
        return None if i is None else self.faces[i]

    def name_of_face(self, index: int) -> str:
        return self.face_names[index]

    def name_of_edge(self, index: int) -> str:
        return self.edge_names[index]

    def edges_of_face(self, index: int) -> list[Any]:
        return [e for e in self.edges if index in e.adjacent_face_indices]


def _find_face(faces: Sequence[Any], shape: Any) -> int | None:
    for i, f in enumerate(faces):
        if f.shape.IsSame(shape):
            return i
    return None


def build_inventory(part: Any) -> Inventory:
    """Name every face of `part.shape` from its NameTable (history first, then
    fingerprint), give the rest `<part>.face[k]`, and derive the edge names."""
    from partkiln.brep import query

    shape = part.shape
    if shape is None:
        return Inventory([], [], [], [], {}, {})
    faces = query.faces(shape)
    edges = query.edges(shape, faces)
    maps_by_index = part.history_maps()  # {feature index: HistoryMap}
    claims: dict[int, list[tuple[int, str]]] = {}  # face index -> [(creation index, name)]
    aliases: dict[str, int] = {}
    stale: dict[str, str] = {}
    for entry in part.names.entries():
        if entry.kind != "face":
            continue
        hits: list[int] = []
        removed_by = ""
        if entry.shape is not None:
            current = [entry.shape]
            for idx in sorted(i for i in maps_by_index if i > entry.index):
                nxt: list[Any] = []
                for s in current:
                    for t in maps_by_index[idx].successors(s):
                        if not any(t.IsSame(u) for u in nxt):
                            nxt.append(t)
                if not nxt and current:
                    removed_by = f"removed by {part.features[idx].kind} {part.features[idx].id}"
                current = nxt
                if not current:
                    break
            for s in current:
                i = _find_face(faces, s)
                if i is not None and i not in hits:
                    hits.append(i)
        if not hits:
            hits = [i for i, f in enumerate(faces) if keys_match(entry.key, key_of(f))]
        if not hits:
            stale[entry.name] = removed_by or "not in the current body"
            continue
        if len(hits) == 1:
            claims.setdefault(hits[0], []).append((entry.index, entry.name))
            aliases[entry.name] = hits[0]
        else:
            ordered = sorted(hits, key=lambda i: tuple(round(c, 3) for c in faces[i].centroid))
            for k, i in enumerate(ordered):
                name = f"{entry.name}[{k}]"
                claims.setdefault(i, []).append((entry.index, name))
                aliases[name] = i
    face_names: list[str] = []
    for i in range(len(faces)):
        owners = sorted(claims.get(i, []))
        if owners:
            face_names.append(owners[0][1])
        else:
            name = f"{part.name}.face[{i}]"
            face_names.append(name)
            aliases[name] = i
    edge_names = [edge_name(e, face_names) for e in edges]
    return Inventory(faces, edges, face_names, edge_names, aliases, stale)


def edge_name(edge: Any, face_names: Sequence[str]) -> str:
    adjacent = sorted(face_names[i] for i in edge.adjacent_face_indices if 0 <= i < len(face_names))
    if edge.is_seam or len(adjacent) == 1:
        return f"{adjacent[0]}~seam" if adjacent else "~seam"
    if not adjacent:
        return "~free"
    return "|".join(adjacent[:2])


# --------------------------------------------------------------------------- resolution


@dataclass
class Resolved:
    """What a reference became: the current infos, their names, and how."""

    ref: str
    kind: str  # face | edge
    infos: list[Any]
    names: list[str]
    seam_excluded: int = 0
    how: str = "name"

    @property
    def count(self) -> int:
        return len(self.infos)

    def echo(self) -> dict[str, Any]:
        """The `resolved` line for the diff: `{ref: count}`."""
        return {self.ref: self.count}

    def selected(self) -> dict[str, list[str]]:
        """`{ref: names}` when there are 6 or fewer (else the count alone says it)."""
        return {self.ref: list(self.names)} if self.names and len(self.names) <= 6 else {}


def is_selector(ref: str) -> bool:
    return _SELECTOR.match(str(ref)) is not None


def _split_filters(text: str) -> list[str]:
    out: list[str] = []
    depth = 0
    current = ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            if current.strip():
                out.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        out.append(current.strip())
    return out


def _axis(text: str) -> tuple[float, float, float]:
    sign = -1.0 if text.startswith("-") else 1.0
    letter = text.lstrip("+-").upper()
    if letter not in ("X", "Y", "Z"):
        raise CommandError(
            f"{text!r} is not an axis: use +X, -X, +Y, -Y, +Z or -Z.", code="pk_ref_unknown"
        )
    return {"X": (sign, 0.0, 0.0), "Y": (0.0, sign, 0.0), "Z": (0.0, 0.0, sign)}[letter]


def _dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


def _parse_point(text: str) -> tuple[float, float, float]:
    inner = text.strip().strip("[]()")
    parts = [p for p in inner.split(",") if p.strip()]
    if len(parts) != 3:
        raise CommandError(f"nearest needs [x, y, z] in mm, got {text!r}.", code="pk_needs")
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError as exc:
        raise CommandError(f"nearest needs three numbers, got {text!r}.", code="pk_needs") from exc


class Selector:
    """A parsed `<scope>:faces(...)` / `<scope>:edges(...)` string."""

    def __init__(self, text: str) -> None:
        m = _SELECTOR.match(str(text))
        if m is None:
            raise CommandError(
                f"{text!r} is not a selector. Form: <part|feature>:faces(<filters>) or "
                ":edges(<filters>), e.g. plate:edges(dir=Z).",
                code="pk_ref_unknown",
            )
        self.text = str(text).strip()
        self.scope = m.group("scope")
        self.kind = "face" if m.group("kind") == "faces" else "edge"
        self.filters = _split_filters(m.group("filters"))

    def evaluate(self, part: Any, inv: Inventory) -> Resolved:
        scope_faces, scope_feature = _scope(part, inv, self.scope)
        if self.kind == "face":
            candidates = [inv.faces[i] for i in scope_faces]
        else:
            seen: set[int] = set()
            candidates = []
            for e in inv.edges:
                if e.index in seen:
                    continue
                if any(i in scope_faces for i in e.adjacent_face_indices):
                    seen.add(e.index)
                    candidates.append(e)
        keep_seams = False
        ctx: dict[str, Any] = {"of": None}
        trail: list[tuple[str, int]] = [("scope", len(candidates))]
        for flt in self.filters:
            if flt == "seams":
                keep_seams = True
                continue
            before = len(candidates)
            candidates = _apply(flt, candidates, part, inv, scope_feature, ctx)
            trail.append((flt, len(candidates)))
            if not candidates:
                last = next((f for f, n in reversed(trail[:-1]) if n > 0), "scope")
                hint = _empty_hint(flt, self.kind, inv, scope_faces)
                raise CommandError(
                    f"{self.text} matched nothing: {before} candidate(s) after {last}, none after "
                    f"{flt}.{hint}",
                    code="pk_ref_empty",
                )
        seam_excluded = 0
        if self.kind == "edge" and not keep_seams:
            seams = [e for e in candidates if e.is_seam]
            seam_excluded = len(seams)
            candidates = [e for e in candidates if not e.is_seam]
            if not candidates:
                raise CommandError(
                    f"{self.text} matched only seam edges ({seam_excluded}), which are excluded by "
                    "default because OCCT generates nothing for them; add the filter 'seams' to "
                    "keep them, or select the real edges.",
                    code="pk_ref_empty",
                )
        if self.kind == "face":
            names = [inv.name_of_face(f.index) for f in candidates]
        else:
            names = [inv.name_of_edge(e.index) for e in candidates]
        return Resolved(self.text, self.kind, candidates, names, seam_excluded, "selector")


def _scope(part: Any, inv: Inventory, scope: str) -> tuple[set[int], str | None]:
    if scope == part.name:
        return set(range(len(inv.faces))), None
    if part.has_feature(scope):
        faces = {i for name, i in inv.aliases.items() if _owner(name) == scope}
        return faces, scope
    known = ", ".join([part.name, *sorted(f.id for f in part.features)])
    raise CommandError(
        f"selector scope {scope!r} is neither the part nor one of its features. Known: {known}.",
        code="pk_ref_unknown",
    )


def _owner(name: str) -> str:
    return name.split(".", 1)[0].split("[", 1)[0]


def _face_role(name: str, role: str, scope_feature: str | None) -> bool:
    base = name.split("[", 1)[0]
    if "." in role:
        return base == role
    return scope_feature is not None and base == f"{scope_feature}.{role}"


def _apply(
    flt: str,
    candidates: list[Any],
    part: Any,
    inv: Inventory,
    scope_feature: str | None,
    ctx: dict[str, Any],
) -> list[Any]:
    from partkiln.brep import query

    if flt.startswith("not(") and flt.endswith(")"):
        inner = flt[4:-1].strip()
        kept = _apply(inner, list(candidates), part, inv, scope_feature, dict(ctx))
        kept_ids = {id(c) for c in kept}
        return [c for c in candidates if id(c) not in kept_ids]
    if flt in ("convex", "concave", "tangent"):
        return [c for c in candidates if getattr(c, "convexity", None) == flt]
    for op in (">=", "<=", "=", ">", "<"):
        if op in flt:
            key, _, raw = flt.partition(op)
            key, raw = key.strip(), raw.strip()
            break
    else:
        raise CommandError(
            f"filter {flt!r} is not one of normal=, dir=, of=, loop=, type=, r=, len>, len<, "
            "area>, "
            "area<, nearest=, created_by=, convex, concave, tangent, seams, not(...).",
            code="pk_ref_unknown",
        )
    if key == "normal":
        axis = _axis(raw)
        return [
            c
            for c in candidates
            if getattr(c, "normal", None) is not None and _dot(c.normal, axis) >= 0.999
        ]
    if key == "dir":
        axis = _axis(raw)
        return [
            c
            for c in candidates
            if getattr(c, "direction", None) is not None and abs(_dot(c.direction, axis)) >= 0.999
        ]
    if key == "type":
        wanted = _TYPE_ALIASES.get(raw, raw)
        return [
            c
            for c in candidates
            if getattr(c, "surface_type", getattr(c, "curve_type", "")) == wanted
        ]
    if key == "of":
        faces = [i for name, i in inv.aliases.items() if _face_role(name, raw, scope_feature)]
        if not faces:
            raise CommandError(
                f"of={raw}: no face is named {raw!r}"
                + (f" or {scope_feature}.{raw!r}" if scope_feature else "")
                + f". Face names: {', '.join(sorted(set(inv.face_names))[:12])}.",
                code="pk_ref_unknown",
            )
        ctx["of"] = faces
        if candidates and isinstance(candidates[0], query.FaceInfo):
            return [c for c in candidates if c.index in faces]
        return [c for c in candidates if any(i in faces for i in c.adjacent_face_indices)]
    if key == "loop":
        if raw not in ("outer", "inner"):
            raise CommandError("loop is outer or inner.", code="pk_ref_unknown")
        if ctx.get("of") is None:
            raise CommandError(
                "loop=outer|inner needs of=<face role> before it, so the wire has a face.",
                code="pk_ref_unknown",
            )
        wanted: set[int] = set()
        for fi in ctx["of"]:
            wires = query.loops(inv.faces[fi].shape, inv.edges)
            for ring in wires[raw]:
                wanted.update(ring)
        return [c for c in candidates if c.index in wanted]
    if key == "r":
        r = float(raw)
        return [c for c in candidates if c.radius is not None and abs(c.radius - r) <= _KEY_TOL]
    if key in ("len", "area"):
        value = float(raw)
        attr = "length" if key == "len" else "area"
        rows = [c for c in candidates if hasattr(c, attr)]
        if op in (">", ">="):
            return [c for c in rows if getattr(c, attr) > value - 1e-9]
        if op in ("<", "<="):
            return [c for c in rows if getattr(c, attr) < value + 1e-9]
        return [c for c in rows if abs(getattr(c, attr) - value) <= _KEY_TOL]
    if key == "nearest":
        point = _parse_point(raw)
        best = query.nearest(candidates, point)
        return [best] if best is not None else []
    if key == "created_by":
        if not part.has_feature(raw):
            raise CommandError(
                f"created_by={raw}: no feature {raw!r} in part {part.name}.", code="pk_ref_unknown"
            )
        faces = {i for name, i in inv.aliases.items() if _owner(name) == raw}
        if candidates and isinstance(candidates[0], query.FaceInfo):
            return [c for c in candidates if c.index in faces]
        return [c for c in candidates if any(i in faces for i in c.adjacent_face_indices)]
    raise CommandError(f"unknown filter {key!r} in {flt!r}.", code="pk_ref_unknown")


def _empty_hint(flt: str, kind: str, inv: Inventory, scope_faces: set[int]) -> str:
    key = flt.split("=")[0].split(">")[0].split("<")[0].strip()
    pool = [inv.faces[i] for i in scope_faces] if kind == "face" else inv.edges
    if key == "len" and pool:
        lengths = sorted(e.length for e in pool)
        return f" Edge lengths in scope run {lengths[0]:.3f}-{lengths[-1]:.3f} mm."
    if key == "area" and pool:
        areas = sorted(f.area for f in pool)
        return f" Face areas in scope run {areas[0]:.3f}-{areas[-1]:.3f} mm2."
    if key == "r" and pool:
        radii = sorted({round(c.radius, 3) for c in pool if c.radius is not None})
        return f" Radii in scope: {', '.join(f'{r:g}' for r in radii) or '(none)'}."
    if key == "normal" and kind == "face":
        return (
            " Face normals: "
            + ", ".join(sorted({_axis_name(f.normal) for f in pool if f.normal is not None}))
            + "."
        )
    if key == "dir":
        return (
            " Line directions: "
            + ", ".join(sorted({_axis_name(e.direction) for e in pool if e.direction is not None}))
            + "."
        )
    return " Drop or relax that filter."


def _axis_name(v: Sequence[float]) -> str:
    for letter, i in (("X", 0), ("Y", 1), ("Z", 2)):
        if abs(v[i]) >= 0.999:
            return ("+" if v[i] > 0 else "-") + letter
    return "oblique"


def resolve(part: Any, ref: Any, kind: str, cardinality: str = "many") -> Resolved:
    """Resolve one reference (a name, a `name[k]`, an edge name or a selector).

    `kind` is 'face' or 'edge' (what the consuming field takes); `cardinality`
    'one' refuses more than one hit with the candidates.
    """
    if isinstance(ref, list | tuple):
        merged: list[Resolved] = [resolve(part, r, kind, "many") for r in ref]
        infos = [i for r in merged for i in r.infos]
        names = [n for r in merged for n in r.names]
        out = Resolved(
            ", ".join(str(r) for r in ref),
            kind,
            infos,
            names,
            sum(r.seam_excluded for r in merged),
            "list",
        )
        return _check_cardinality(out, cardinality)
    text = str(ref).strip()
    if not text:
        raise CommandError("an empty reference names nothing.", code="pk_ref_unknown")
    inv = part.inventory()
    if is_selector(text):
        sel = Selector(text)
        if sel.kind != kind:
            raise CommandError(
                f"{text} selects {sel.kind}s but this field takes {kind}s.", code="pk_ref_unknown"
            )
        return _check_cardinality(sel.evaluate(part, inv), cardinality)
    if kind == "face":
        return _check_cardinality(_resolve_face_name(part, inv, text), cardinality)
    return _check_cardinality(_resolve_edge_name(part, inv, text), cardinality)


def _check_cardinality(res: Resolved, cardinality: str) -> Resolved:
    if cardinality == "one" and res.count != 1:
        listed = "; ".join(
            f"{n} at {_fmt(_centre(i))}" for n, i in zip(res.names, res.infos, strict=False)
        )[:400]
        raise CommandError(
            f"{res.ref} must name exactly one {res.kind}, it matched {res.count}: {listed}. "
            "Add nearest=[x,y,z] or name one of them.",
            code="pk_ref_ambiguous",
        )
    return res


def _fmt(p: Sequence[float]) -> str:
    return "(" + ", ".join(f"{c:.3f}" for c in p) + ")"


def _resolve_face_name(part: Any, inv: Inventory, text: str) -> Resolved:
    i = inv.face_index(text)
    if i is not None:
        return Resolved(text, "face", [inv.faces[i]], [inv.name_of_face(i)], 0, "name")
    # a fan-out base name: `plate.end` when only `plate.end[0..k]` exist
    fan = sorted((n, j) for n, j in inv.aliases.items() if n.startswith(text + "["))
    if fan:
        return Resolved(
            text, "face", [inv.faces[j] for _, j in fan], [n for n, _ in fan], 0, "history"
        )
    entry = part.names.get(text) or part.stale.get(text)
    if entry is not None and entry.kind == "face":
        hits = [j for j, f in enumerate(inv.faces) if keys_match(entry.key, key_of(f))]
        if len(hits) == 1:
            j = hits[0]
            return Resolved(text, "face", [inv.faces[j]], [inv.name_of_face(j)], 0, "fingerprint")
        raise _stale(part, inv, entry, "face")
    raise _unknown(part, inv, text, "face")


def _resolve_edge_name(part: Any, inv: Inventory, text: str) -> Resolved:
    hits = [e for e, n in zip(inv.edges, inv.edge_names, strict=True) if n == text]
    if hits:
        return Resolved(text, "edge", hits, [text] * len(hits), 0, "name")
    if "|" in text:
        a, b = text.split("|", 1)
        sides = [_resolve_face_name(part, inv, side) for side in (a, b)]  # may refuse pk_ref_stale
        fa, fb = sides[0].infos[0].index, sides[1].infos[0].index
        shared = [
            e for e in inv.edges if fa in e.adjacent_face_indices and fb in e.adjacent_face_indices
        ]
        if shared:
            how = "fingerprint" if any(s.how == "fingerprint" for s in sides) else "history"
            return Resolved(
                text, "edge", shared, [inv.name_of_edge(e.index) for e in shared], 0, how
            )
        raise CommandError(
            f"{text}: {sides[0].names[0]} and {sides[1].names[0]} exist but share no edge now. "
            f"Select it by geometry: {part.name}:edges(of={sides[0].names[0]}, nearest=[x,y,z]).",
            code="pk_ref_stale",
        )
    raise _unknown(part, inv, text, "edge")


def _unknown(part: Any, inv: Inventory, text: str, kind: str) -> CommandError:
    pool = sorted(set(inv.face_names)) if kind == "face" else sorted(set(inv.edge_names))
    shown = ", ".join(pool[:8]) + (f" ... ({len(pool)} total)" if len(pool) > 8 else "")
    return CommandError(
        f"no {kind} named {text!r} in part {part.name}. {kind.capitalize()} names: "
        f"{shown or '(none)'}. "
        f"Or select by geometry: {part.name}:{kind}s(<filters>).",
        code="pk_ref_unknown",
    )


def _stale(
    part: Any, inv: Inventory, entry: NameEntry, kind: str, wanted: str | None = None
) -> CommandError:
    """`pk_ref_stale`: the event, the 3 nearest candidates with their distance, and a
    selector that would survive."""
    event = inv.stale.get(entry.name) or part.event_for(entry.feature)
    pool: list[Any] = inv.faces if entry.kind == "face" else inv.edges
    names = inv.face_names if entry.kind == "face" else inv.edge_names
    centre = entry.key[2]
    ranked = sorted(pool, key=lambda i: math.dist(_centre(i), centre))[:3]
    candidates = "; ".join(
        f"{names[i.index]} ({key_of(i)[0]}, {math.dist(_centre(i), centre):.3f} mm away)"
        for i in ranked
    )
    selector = survivor_selector(part.name, entry)
    what = wanted or entry.name
    return CommandError(
        f"{what} is stale: {entry.name} ({entry.kind} made by {entry.feature}) was {event}. "
        f"Nearest now: {candidates or '(nothing)'}. A selector that survives regen: {selector}.",
        code="pk_ref_stale",
    )


def survivor_selector(part_name: str, entry: NameEntry) -> str:
    kind, _size, centre, direction, radius = entry.key
    filters = [f"type={kind}"]
    if entry.kind == "face" and direction is not None:
        filters.append(f"normal={_axis_name(direction)}")
    elif entry.kind == "edge" and direction is not None and kind == "line":
        filters.append(f"dir={_axis_name(direction).lstrip('+-')}")
    if radius is not None:
        filters.append(f"r={radius:g}")
    filters.append("nearest=[" + ",".join(f"{c:g}" for c in centre) + "]")
    plural = "faces" if entry.kind == "face" else "edges"
    return f"{part_name}:{plural}({', '.join(filters)})"


def materialise(names: Sequence[str], limit: int = 8) -> list[str] | dict[str, Any]:
    """The `names` field of a diff: the names when few, else a count with the first ones."""
    listed = list(names)
    if len(listed) <= limit:
        return listed
    return {"count": len(listed), "first": listed[:limit]}


__all__ = [
    "Inventory",
    "NameEntry",
    "NameTable",
    "Resolved",
    "Selector",
    "SubshapeKey",
    "build_inventory",
    "edge_name",
    "is_selector",
    "key_of",
    "keys_match",
    "materialise",
    "resolve",
    "survivor_selector",
]
