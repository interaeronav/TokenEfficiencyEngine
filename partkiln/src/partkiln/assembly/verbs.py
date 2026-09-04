"""The assembly verbs: `create component | mate | joint | object`, and their edits.

P3's library (poses, mates, joints, the scipy solver, interference, the BOM)
knows nothing about documents; this module is the wire above it. A component
is an instance of a PART at a pose, a mate or a joint holds two frames, and
those frames are read off NAMED sub-shapes (Law 13: `block.hole1.1.wall`, not
face 4) through `naming.resolve` on the component's own part - so a regen that
renumbers faces moves the mate with them or refuses with candidates, and the
solver never sees a name at all.

Three rules this file exists to keep:

* **An over-constrained assembly is reported, not refused** (D7). A
  contradictory offset comes back `status: conflict` with `over_constrained`
  naming the later constraint and the residual in millimetres, because the
  model can only fix what it can see. The ONE refusal is a frame-kind
  mismatch (`insert` on two planes), which is a mistake in the command rather
  than a state of the model, and `model.FRAME_RULES` names the fix.
* **One `details.asm` per batch** (D7). Every verb here answers under
  `result["regen"]["asm"]` - the same channel `Part.regen` uses for Law 14 -
  so the adapter lifts exactly one `details.asm` into the diff: the batch's
  final state, computed once per command and cached until the next mutation.
  Interference is skipped (with a note) above `MAX_PAIRS` pairs, which is the
  `job: true` threshold of D2, and whenever a body is missing.
* **Poses join the fingerprint** (D3). `fingerprint_payload` rounds them to
  1e-6 and the document hashes them beside the parts.

Nothing here imports OCP. The frames come from `features.workplane`, the
interference from `assembly.interference`, and both reach the kernel lazily.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from partkiln.assembly.interference import NEAR_MM
from partkiln.assembly.model import (
    JOINT_KINDS,
    MATE_KINDS,
    Assembly,
    Component,
    Constraint,
    FrameRef,
    Joint,
    Mate,
    Pose,
    Ref,
)
from partkiln.assembly.solver import SolveReport, apply_poses, solve
from partkiln.document import CommandError, Document, register_kind

# Above this many body pairs the interference pass is left to `pk_measure`
# (D2: interference over 20 pairs takes `job: true`); 20 components is 190
# pairs at ~1.3 ms each, which is a third of the 60 s batch deadline spent on
# a number nobody asked for.
MAX_PAIRS = 20
# Above this many live constraints the ROWS drop `dof_removed`: it costs one
# leave-one-out solve each, and a listing is not the place to spend them.
MAX_ROW_SOLVES = 12
DEFAULT_ASSEMBLY = "main"


def _r6(value: float) -> float:
    return round(float(value), 6) + 0.0


def _r3(value: float) -> float:
    return round(float(value), 3) + 0.0


# --------------------------------------------------------------------------- the container


class DocAssembly:
    """One assembly inside a document: the P3 `Assembly` plus what the wire needs.

    `suppressed` holds constraint names the model switched off; the solve runs
    on a twin assembly built from the SAME component objects (so the solved
    poses land on the real ones) with those constraints left out. `_report`
    and `_details` are caches invalidated by every mutation, which is what
    makes "computed once" true within a command and across the two readers
    (`entity_rows` and the verb result) that both want the number.
    """

    def __init__(self, name: str = DEFAULT_ASSEMBLY) -> None:
        self.name = name
        self.asm = Assembly()
        self.suppressed: set[str] = set()
        self.parts: dict[str, str] = {}  # component name -> part name (for the BOM)
        self._report: SolveReport | None = None
        self._details: dict[str, Any] | None = None
        self._removed: dict[str, int] | None = None
        # (state key, report) for the interference pass: the one part of the
        # asm report that costs OCCT booleans, so it is not recomputed for an
        # edit that moved nothing (a rename, a limit).
        self._contact: tuple[Any, dict[str, Any]] | None = None

    # -- state -----------------------------------------------------------

    def invalidate(self) -> None:
        self._report = None
        self._details = None
        self._removed = None

    def active(self) -> Assembly:
        """The assembly the solver sees: the same components, the live constraints."""
        if not self.suppressed:
            return self.asm
        twin = Assembly(list(self.asm.components.values()))
        for constraint in self.asm.constraints():
            if constraint.name in self.suppressed:
                continue
            if isinstance(constraint, Mate):
                twin.add_mate(constraint)
            else:
                twin.add_joint(constraint)
        return twin

    def solved(self) -> SolveReport:
        """Solve once and COMMIT the poses (the document is the state)."""
        if self._report is None:
            report = solve(self.active())
            apply_poses(self.asm, report.poses)
            self._report = report
        return self._report

    def rebuild(self, components: list[Component], constraints: list[Constraint]) -> None:
        """Replace the assembly with the same objects in a new order/set.

        `Assembly` has no remove-component and no in-place edit of a frozen
        Mate, so a delete or a `set` rebuilds it from the surviving pieces IN
        ORDER - order is load-bearing, because a conflict is charged to the
        LATER constraint.
        """
        fresh = Assembly(components)
        for constraint in constraints:
            if isinstance(constraint, Mate):
                fresh.add_mate(constraint)
            else:
                fresh.add_joint(constraint)
        self.asm = fresh
        self.suppressed &= {c.name for c in constraints}
        self.parts = {c.name: c.part_name for c in components}
        self.invalidate()

    def constraint(self, name: str) -> Constraint:
        return self.asm.constraint(name)

    def removed_map(self) -> dict[str, int]:
        """`{constraint: dof it actually removes}`, by leave-one-out solve."""
        if self._removed is not None:
            return self._removed
        live = [c for c in self.asm.constraints() if c.name not in self.suppressed]
        if len(live) > MAX_ROW_SOLVES:
            self._removed = {}
            return self._removed
        dof = self.solved().dof
        out: dict[str, int] = {}
        for constraint in live:
            without = Assembly(list(self.asm.components.values()))
            for other in live:
                if other.name == constraint.name:
                    continue
                if isinstance(other, Mate):
                    without.add_mate(other)
                else:
                    without.add_joint(other)
            out[constraint.name] = max(0, solve(without).dof - dof)
        self._removed = out
        return out

    def dependents_of_component(self, component: str) -> list[str]:
        return [
            f"{_prefix(c)}:{c.name}"
            for c in self.asm.constraints()
            if component in (c.a.component, c.b.component)
        ]

    # -- reports ---------------------------------------------------------

    def details(self, *, interference: bool = True) -> dict[str, Any]:
        """The D7 `details.asm`: the numbers, never the geometry."""
        if self._details is not None:
            return dict(self._details)
        report = self.solved()
        out: dict[str, Any] = {
            "id": "asm",
            "name": self.name,
            "components": len(self.asm.components),
            "dof": report.dof,
            "status": report.status,
            "grounded": self.asm.grounded,
            "residual": _r6(report.residual_mm),
            "constraints": len(self.asm.constraints()),
        }
        if report.dof:
            out["dof_by_component"] = {k: v for k, v in report.dof_by_component.items() if v}
        if report.over_constrained:
            out["over_constrained"] = list(report.over_constrained)
            out["conflicts"] = [dict(c) for c in report.conflicts]
        if report.redundant:
            out["redundant"] = list(report.redundant)
        if report.joint_values:
            out["joint_values"] = {k: dict(v) for k, v in report.joint_values.items()}
        if self.suppressed:
            out["suppressed"] = sorted(self.suppressed)
        notes: list[str] = list(report.warnings)
        if interference:
            out.update(self._interference(notes))
        if notes:
            out["notes"] = notes
        self._details = dict(out)
        return dict(out)

    def _interference(self, notes: list[str]) -> dict[str, Any]:
        """Interference, contacts and clearances - or an honest reason there are none."""
        from partkiln.brep import ocp_available

        bodies: list[tuple[str, Any, Pose]] = []
        missing: list[str] = []
        for component in self.asm.components.values():
            if component.virtual:
                continue
            shape = component.shape_ref() if callable(component.shape_ref) else component.shape_ref
            if shape is None:
                missing.append(component.name)
            else:
                bodies.append((component.name, shape, component.pose))
        # What the answer depends on: which bodies, and exactly where they are.
        # An edit that renames a mate or changes a limit leaves this key alone
        # and the booleans are not run again.
        key = (
            tuple(
                (name, id(shape), *pose.rounded(9).translation, *pose.rounded(9).rotation)
                for name, shape, pose in bodies
            ),
            tuple(sorted(missing)),
        )
        if self._contact is not None and self._contact[0] == key:
            return dict(self._contact[1])
        if len(bodies) < 2:
            if missing:
                notes.append(
                    f"interference not measured: {', '.join(missing)} has no body yet "
                    "(the part is empty)"
                )
            out = {"interference": [], "contacts": [], "clearance_mm": {}}
        elif not ocp_available():
            notes.append("interference not measured: partkiln[brep] is not installed here")
            return {}
        elif len(bodies) * (len(bodies) - 1) // 2 > MAX_PAIRS:
            notes.append(
                f"interference not measured: {len(bodies) * (len(bodies) - 1) // 2} body pairs "
                f"is over the {MAX_PAIRS}-pair batch budget. Ask "
                "pk_measure(what=interference), which takes job: true."
            )
            return {}
        else:
            if missing:
                notes.append(f"interference skipped for {', '.join(missing)} (no body yet)")
            # `partkiln.assembly` re-exports the FUNCTION `interference`, so the
            # module is imported by its full path or the name resolves to it.
            from partkiln.assembly.interference import report as contact_report

            report = contact_report(bodies, near_mm=NEAR_MM)
            out = {
                "interference": report["interference"],
                "contacts": report["contacts"],
                "clearance_mm": report["clearance_mm"],
            }
        self._contact = (key, dict(out))
        return dict(out)

    def summary(self) -> dict[str, Any]:
        """The compact row, cheap: the solve, never the booleans."""
        report = self.solved()
        out: dict[str, Any] = {
            "id": "asm",
            "kind": "assembly",
            "name": self.name,
            "components": len(self.asm.components),
            "constraints": len(self.asm.constraints()),
            "dof": report.dof,
            "status": report.status,
            "grounded": len(self.asm.grounded),
            "residual": _r6(report.residual_mm),
        }
        if self._details is not None:
            out["interference"] = len(self._details.get("interference") or ())
            out["contacts"] = len(self._details.get("contacts") or ())
        if report.over_constrained:
            out["over_constrained"] = list(report.over_constrained)
        return out

    def entity_rows(self) -> list[dict[str, Any]]:
        """D7: the assembly, every component, every mate and every joint."""
        rows: list[dict[str, Any]] = [self.summary()]
        report = self._report
        for component in self.asm.components.values():
            row: dict[str, Any] = {
                "id": f"cmp:{component.name}",
                "kind": "component",
                "name": component.name,
                "parent": "asm",
                "part": f"part:{component.part_name}",
                "grounded": component.grounded,
                "pose": _pose_row(component.pose),
            }
            if component.virtual:
                row["virtual"] = True
            if report is not None and component.name in report.dof_by_component:
                row["dof"] = report.dof_by_component[component.name]
            rows.append(row)
        for constraint in self.asm.constraints():
            rows.append(self._constraint_row(constraint, report))
        return rows

    def _constraint_row(self, constraint: Constraint, report: SolveReport | None) -> dict[str, Any]:
        prefix = _prefix(constraint)
        row: dict[str, Any] = {
            "id": f"{prefix}:{constraint.name}",
            "kind": "mate" if prefix == "mate" else "joint",
            "name": constraint.name,
            "parent": "asm",
            "type": constraint.kind,
            "a": constraint.a.label(),
            "b": constraint.b.label(),
            "suppressed": constraint.name in self.suppressed,
        }
        if constraint.offset_mm is not None:
            row["offset_mm"] = _r3(constraint.offset_mm)
        if constraint.angle_deg:
            row["angle_deg"] = _r3(constraint.angle_deg)
        if isinstance(constraint, Joint) and constraint.limits is not None:
            row["limits"] = [_r3(constraint.limits[0]), _r3(constraint.limits[1])]
        if isinstance(constraint, Mate) and constraint.flip:
            row["flip"] = True
        removed = _dof_removed(self, constraint)
        if removed is not None:
            row["dof_removed"] = removed
        if report is not None and constraint.name in report.over_constrained:
            row["status"] = "conflict"
        return row

    def detail(self, entity_id: str) -> dict[str, Any] | None:
        """One assembly entity, or None so the document can keep looking."""
        eid = str(entity_id)
        if eid in ("asm", f"asm:{self.name}"):
            return self.details(interference=self._details is not None)
        prefix, _, name = eid.partition(":")
        if prefix == "cmp" and name in self.asm.components:
            row = next(r for r in self.entity_rows() if r["id"] == eid)
            return {**row, "used_by": self.dependents_of_component(name)}
        if prefix in ("mate", "jt"):
            for constraint in self.asm.constraints():
                if constraint.name == name and _prefix(constraint) == prefix:
                    row = self._constraint_row(constraint, self._report)
                    row["a_frame"] = _frame_row(constraint.a.frame)
                    row["b_frame"] = _frame_row(constraint.b.frame)
                    return row
        return None


def _prefix(constraint: Constraint) -> str:
    return "mate" if isinstance(constraint, Mate) else "jt"


def _pose_row(pose: Pose) -> dict[str, list[float]]:
    return pose.as_dict(6)


def _frame_row(frame: FrameRef) -> dict[str, Any]:
    out: dict[str, Any] = {
        "kind": frame.kind,
        "origin": [_r3(c) for c in frame.origin],
        "axis": [_r6(c) for c in frame.axis],
    }
    if frame.radius is not None:
        out["radius_mm"] = _r3(frame.radius)
    return out


def _dof_removed(record: DocAssembly, constraint: Constraint) -> int | None:
    """How much rank this constraint actually adds (never its nominal count).

    Measured, not tabled: a cylindrical joint removes 4 on a free component
    and 0 on a component another mate already fixed, and only the measured
    number tells the model which of the two it has. It costs one leave-one-out
    solve per constraint, so above `MAX_ROW_SOLVES` the rows leave it out
    rather than spend a second on a listing (the create result always carries
    it, and `tee_entity_detail` re-measures on request).
    """
    if constraint.name in record.suppressed:
        return 0
    cached = record.removed_map()
    return cached.get(constraint.name)


# --------------------------------------------------------------------------- lookups


def assembly_of(doc: Document, args: dict[str, Any], *, create: bool = False) -> DocAssembly:
    """The assembly an op works on: `assembly:`, else the only one, else the default."""
    raw = args.get("assembly")
    if raw is not None:
        name = str(raw).split(":", 1)[-1] if str(raw).startswith("asm") else str(raw)
        record = doc.assemblies.get(name)
        if record is None:
            known = ", ".join(sorted(doc.assemblies)) or "(none)"
            raise CommandError(f"no assembly {raw!r}. Assemblies: {known}.", code="pk_ref_unknown")
        return record
    if not doc.assemblies:
        if not create:
            raise CommandError(
                "no assembly yet. Create a component first: "
                "{op: create, kind: component, props: {part: <name>}}.",
                code="pk_ref_unknown",
            )
        record = DocAssembly()
        doc.assemblies[record.name] = record
        _register_dependencies(doc)
        return record
    if len(doc.assemblies) > 1:
        raise CommandError(
            f"the document has {len(doc.assemblies)} assemblies "
            f"({', '.join(sorted(doc.assemblies))}); say which with assembly: <name>.",
            code="pk_part_ambiguous",
        )
    return next(iter(doc.assemblies.values()))


def _register_dependencies(doc: Document) -> None:
    """Teach `dependents_of` about components, once per document."""
    if not any(getattr(source, "_partkiln_assembly", False) for source in doc.dependency_sources):
        dependents._partkiln_assembly = True  # type: ignore[attr-defined]
        doc.dependency_sources.append(dependents)


def dependents(doc: Document, entity_id: str) -> list[str]:
    """Components that would break if `entity_id` (a part) went."""
    found: list[str] = []
    if entity_id.startswith("part:"):
        part = entity_id[5:]
        for record in doc.assemblies.values():
            found.extend(
                f"cmp:{c.name}"
                for c in record.asm.components.values()
                if c.part_name == part and not c.virtual
            )
    return sorted(set(found))


def _shape_getter(doc: Document, part_name: str) -> Any:
    """A component's body, fetched from the document when it is asked for.

    A plain closure on purpose: `copy.deepcopy` treats a function as atomic,
    so the per-command snapshot Law 16 takes never tries to copy an OCCT
    handle, and a regen that rebuilds the part is seen by every component
    that instances it.
    """

    def shape() -> Any:
        part = doc.parts.get(part_name)
        return None if part is None else part.shape

    return shape


def _part_of(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> str:
    raw = args.get("part")
    if raw is None:
        known = ", ".join(f"part:{n}" for n in sorted(doc.parts)) or "(none)"
        raise CommandError(f"create component needs part: <name>. Parts: {known}.", code="pk_needs")
    name = str(raw)[5:] if str(raw).startswith("part:") else str(raw)
    if name not in doc.parts:
        known = ", ".join(f"part:{n}" for n in sorted(doc.parts)) or "(none)"
        raise CommandError(f"no part {raw!r}. Parts: {known}.", code="pk_ref_unknown")
    return name


def _auto_name(base: str, taken: dict[str, Any]) -> str:
    if base not in taken:
        return base
    n = 2
    while f"{base}{n}" in taken:
        n += 1
    return f"{base}{n}"


def _pose_of(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> Pose:
    """`at` (mm) and `rot` - [rx, ry, rz] degrees about the WORLD X, then Y, then
    Z, or {axis: [x, y, z], deg: a}. The order is declared because two orders
    give two different poses and only one of them is what was meant."""
    at = args.get("at") or (0.0, 0.0, 0.0)
    if not isinstance(at, list | tuple) or len(at) != 3:
        raise CommandError(f"at {at!r} is [x, y, z] in mm.", code="pk_needs")
    translation = tuple(doc.length(c, assumed) for c in at)
    rot = args.get("rot")
    if rot is None:
        return Pose(translation)
    if isinstance(rot, dict):
        axis = rot.get("axis")
        deg = rot.get("deg", rot.get("angle"))
        if not isinstance(axis, list | tuple) or len(axis) != 3 or deg is None:
            raise CommandError(
                "rot is [rx, ry, rz] in degrees or {axis: [x, y, z], deg: a}.", code="pk_needs"
            )
        return Pose.from_axis_angle(axis, doc.angle(deg, assumed), translation)
    if not isinstance(rot, list | tuple) or len(rot) != 3:
        raise CommandError(
            "rot is [rx, ry, rz] in degrees (about world X, then Y, then Z) or "
            "{axis: [x, y, z], deg: a}.",
            code="pk_needs",
        )
    rx, ry, rz = (doc.angle(c, assumed) for c in rot)
    if any(abs(a) > 1e-12 for a in (rx, ry, rz)):
        assumed["rot"] = "degrees about world X, then Y, then Z"
    turn = (
        Pose.from_axis_angle((0.0, 0.0, 1.0), rz)
        .compose(Pose.from_axis_angle((0.0, 1.0, 0.0), ry))
        .compose(Pose.from_axis_angle((1.0, 0.0, 0.0), rx))
    )
    return Pose(translation, turn.rotation)


# --------------------------------------------------------------------------- frames


def frame_ref(doc: Document, record: DocAssembly, raw: Any, side: str, what: str) -> Ref:
    """`"<component>.<feature>.<role>"` -> a frame in that component's LOCAL space.

    A plane face becomes a `plane` frame (origin at its centroid, axis its
    outward normal); a cylinder or cone face becomes an `axis` frame carrying
    its radius, which is what `insert` and `tangent` need. The dict forms
    `{component, point: [x, y, z]}` and `{component, axis: [[p], [d]], radius}`
    exist for the geometry no face names (a bearing centre line).
    """
    if isinstance(raw, dict):
        return _frame_from_dict(record, raw, side, what)
    text = str(raw or "").strip()
    if not text:
        raise CommandError(
            f"{what} needs {side}: '<component>.<face name>' (e.g. block.hole1.1.wall).",
            code="pk_needs",
        )
    component_name, _, ref = text.partition(".")
    component = _component(record, component_name, side, what)
    if not ref:
        return Ref(component.name, FrameRef("point", (0.0, 0.0, 0.0)), "origin")
    if component.virtual:
        raise CommandError(
            f"component {component.name!r} is virtual (no geometry), so {text!r} names nothing. "
            "Fix: mate a component that instances a part, or give the frame explicitly "
            "({component, point: [x, y, z]}).",
            code="pk_ref_empty",
        )
    part = doc.parts.get(component.part_name)
    if part is None or part.shape is None:
        raise CommandError(
            f"part {component.part_name!r} has no body yet, so {text!r} names nothing. "
            "Fix: build the part before you mate it.",
            code="pk_ref_empty",
        )
    return Ref(component.name, _frame_of_face(doc, part, ref, text), ref)


def _component(record: DocAssembly, name: str, side: str, what: str) -> Component:
    component = record.asm.components.get(name)
    if component is None:
        known = ", ".join(sorted(record.asm.components)) or "(none)"
        raise CommandError(
            f"{what} {side}: no component {name!r}. Components: {known}. A reference is "
            "'<component>.<face name>'.",
            code="pk_ref_unknown",
        )
    return component


def _frame_from_dict(record: DocAssembly, raw: dict[str, Any], side: str, what: str) -> Ref:
    name = str(raw.get("component") or raw.get("cmp") or "")
    component = _component(record, name, side, what)
    if "point" in raw:
        return Ref(component.name, FrameRef("point", raw["point"]), "point")
    if "axis" in raw:
        axis = raw["axis"]
        if not isinstance(axis, list | tuple) or len(axis) != 2:
            raise CommandError(
                "an explicit axis frame is {component, axis: [[px, py, pz], [dx, dy, dz]], "
                "radius}.",
                code="pk_needs",
            )
        return Ref(
            component.name,
            FrameRef("axis", axis[0], axis[1], radius=raw.get("radius")),
            "axis",
        )
    if "plane" in raw:
        plane = raw["plane"]
        if not isinstance(plane, list | tuple) or len(plane) != 2:
            raise CommandError(
                "an explicit plane frame is {component, plane: [[px, py, pz], [nx, ny, nz]]}.",
                code="pk_needs",
            )
        return Ref(component.name, FrameRef("plane", plane[0], plane[1]), "plane")
    raise CommandError(
        f"{what} {side}: a frame object is {{component, point | axis | plane}}; "
        f"got keys {sorted(raw)}.",
        code="pk_needs",
    )


def _frame_of_face(doc: Document, part: Any, ref: str, label: str) -> FrameRef:
    from partkiln.features.workplane import axis_of
    from partkiln.naming import resolve

    resolved = resolve(part, ref, "face", "one")
    info = resolved.infos[0]
    if info.surface_type == "plane":
        if info.normal is None:
            raise CommandError(
                f"{label} is a plane with no normal (a degenerate face).", code="pk_op_failed"
            )
        return FrameRef("plane", info.centroid, info.normal)
    if info.surface_type in ("cylinder", "cone"):
        point, direction = axis_of(doc, ref, part)
        return FrameRef("axis", point, direction, radius=info.radius)
    raise CommandError(
        f"{label} is a {info.surface_type} face; an assembly frame is a plane (mate, flush) "
        "or a cylinder/cone (insert, tangent, revolute). Fix: name a planar or cylindrical "
        "face, or give the frame explicitly ({component, point | axis | plane}).",
        code="pk_plane_mismatch",
    )


# --------------------------------------------------------------------------- the verbs


def _result(
    record: DocAssembly, body: dict[str, Any], *, pose_of: str | None = None
) -> dict[str, Any]:
    """Every assembly verb answers with ONE asm report, on the `regen` channel.

    `details()` is what SOLVES, so a `pose` in the answer is read after it -
    a component that was asked to move somewhere its mates do not allow must
    report where it actually ended up, not where it was sent.
    """
    body["regen"] = {"asm": record.details()}
    if pose_of is not None:
        body["pose"] = _pose_row(record.asm.component(pose_of).pose)
    return body


@register_kind("component")
def _k_component(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    record = assembly_of(doc, args, create=True)
    part_name = _part_of(doc, args, assumed)
    if args.get("name"):
        name = doc.new_name(args, "cmp", record.asm.components)
    else:
        name = _auto_name(part_name, record.asm.components)
    pose = _pose_of(doc, args, assumed)
    grounded = args.get("grounded")
    if grounded is None:
        grounded = not record.asm.components
        doc.assume_once(assumed, "grounded", "the first component is grounded")
    elif not isinstance(grounded, bool):
        raise CommandError("grounded is true or false.", code="pk_needs")
    component = Component(
        name, part_name, _shape_getter(doc, part_name), pose, grounded=bool(grounded)
    )
    record.asm.add_component(component)
    record.parts[name] = part_name
    record.invalidate()
    return _result(
        record,
        {
            "id": f"cmp:{name}",
            "kind": "component",
            "part": f"part:{part_name}",
            "grounded": bool(grounded),
            "components": len(record.asm.components),
        },
        pose_of=name,
    )


@register_kind("object")
def _k_object(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    """The contract's generic kind: a virtual component - counted in the BOM,
    never solved, never measured (D5). A purchased bearing before anyone
    models it is exactly this."""
    record = assembly_of(doc, args, create=True)
    name = doc.new_name(args, "obj", record.asm.components)
    part_name = str(args.get("part") or name)
    component = Component(name, part_name, None, _pose_of(doc, args, assumed), virtual=True)
    record.asm.add_component(component)
    record.parts[name] = part_name
    record.invalidate()
    return _result(
        record,
        {
            "id": f"cmp:{name}",
            "kind": "object",
            "part": part_name,
            "virtual": True,
            "components": len(record.asm.components),
        },
    )


def _constraint_kind(args: dict[str, Any], kinds: tuple[str, ...], what: str) -> str:
    """Which mate or joint this is - and why it is not spelled `kind`.

    The wire folds `kind` beside `op` and then merges `props` over it
    (`Command.from_dict`), so `create mate {kind: insert}` arrives as
    `kind: insert` and would never reach this handler - the same collision the
    pattern layout hit in P2c. Both spellings therefore work: `type: insert`
    reaches `create mate`, and `insert` is registered as a create kind of its
    own, which is how `kind: insert` still lands here with the right kind.
    """
    raw = args.get("type", args.get(f"{what}_kind"))
    if raw is None and str(args.get("kind", "")) in kinds:
        raw = args["kind"]
    kind = str(raw or "").strip().lower()
    if kind not in kinds:
        raise CommandError(
            f"create {what} needs type: one of {', '.join(kinds)}"
            + (f" (got {raw!r})" if raw else "")
            + f". Write {{op: create, kind: {what}, props: {{type: {kinds[0]}, a: ..., b: ...}}}} "
            f"or {{op: create, kind: {kinds[0]}, props: {{a: ..., b: ...}}}}.",
            code="pk_bad_op",
        )
    return kind


def _constraint_common(
    doc: Document,
    args: dict[str, Any],
    assumed: dict[str, Any],
    kinds: tuple[str, ...],
    what: str,
) -> tuple[DocAssembly, str, str, Ref, Ref]:
    record = assembly_of(doc, args)
    kind = _constraint_kind(args, kinds, what)
    taken = {c.name: c for c in record.asm.constraints()}
    name = doc.new_name(args, what, taken)
    a = frame_ref(doc, record, args.get("a"), "a", f"{what} {name}")
    b = frame_ref(doc, record, args.get("b"), "b", f"{what} {name}")
    return record, name, kind, a, b


def _offset(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> float | None:
    raw = args.get("offset", args.get("offset_mm"))
    return None if raw is None else doc.length(raw, assumed)


def _angle(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> float:
    raw = args.get("angle", args.get("angle_deg"))
    return 0.0 if raw is None else doc.angle(raw, assumed)


@register_kind("mate")
def _k_mate(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    record, name, kind, a, b = _constraint_common(doc, args, assumed, MATE_KINDS, "mate")
    before = record.solved().dof
    mate = Mate(
        name,
        kind,
        a,
        b,
        offset_mm=_offset(doc, args, assumed),
        angle_deg=_angle(doc, args, assumed),
        flip=bool(args.get("flip", False)),
    )
    record.asm.add_mate(mate)
    record.invalidate()
    return _result(record, _constraint_result(record, mate, "mate", before))


@register_kind("joint")
def _k_joint(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    record, name, kind, a, b = _constraint_common(doc, args, assumed, JOINT_KINDS, "joint")
    before = record.solved().dof
    limits = args.get("limits")
    if limits is not None:
        if not isinstance(limits, list | tuple) or len(limits) != 2:
            raise CommandError("limits are [low, high] in mm or degrees.", code="pk_needs")
        limits = (float(limits[0]), float(limits[1]))
    joint = Joint(
        name,
        kind,
        a,
        b,
        offset_mm=_offset(doc, args, assumed),
        angle_deg=_angle(doc, args, assumed),
        limits=limits,
    )
    record.asm.add_joint(joint)
    record.invalidate()
    return _result(record, _constraint_result(record, joint, "joint", before))


def _constraint_result(
    record: DocAssembly, constraint: Constraint, what: str, dof_before: int
) -> dict[str, Any]:
    report = record.solved()
    moved = [
        name
        for name, component in record.asm.components.items()
        if not component.grounded and name in report.poses
    ]
    primary = constraint.b.component if constraint.b.component in moved else constraint.a.component
    out: dict[str, Any] = {
        "id": f"{_prefix(constraint)}:{constraint.name}",
        "kind": what,
        "type": constraint.kind,
        "a": constraint.a.label(),
        "b": constraint.b.label(),
        "dof_removed": max(0, dof_before - report.dof),
        "dof": report.dof,
        "status": report.status,
        "residual": _r6(report.residual_mm),
    }
    if primary in record.asm.components:
        out["pose"] = {
            "component": primary,
            **_pose_row(record.asm.component(primary).pose),
        }
    if constraint.name in report.over_constrained:
        out["over_constrained"] = list(report.over_constrained)
    return out


# Every mate and joint kind is ALSO a create kind, so the D5 spelling
# `create mate {kind: insert}` works: the wire's props overwrite `kind`, so
# that command arrives as `create insert` and has to be served here.
for _kind in MATE_KINDS:
    if _kind != "mate":
        register_kind(_kind)(_k_mate)
for _kind in JOINT_KINDS:
    register_kind(_kind)(_k_joint)


# --------------------------------------------------------------------------- set / delete


_COMPONENT_PROPS = ("at", "rot", "grounded", "name", "suppressed", "part")
_CONSTRAINT_PROPS = ("offset", "angle", "flip", "limits", "type", "name", "suppressed")


def set_target(
    doc: Document, target: str, props: dict[str, Any], assumed: dict[str, Any]
) -> dict[str, Any]:
    """`set cmp:|mate:|jt:|asm` - every edit re-solves and answers the new state."""
    eid = str(target)
    record = _record_for(doc, eid)
    if not props:
        raise CommandError(
            f"set {eid} needs props: "
            + (
                ", ".join(_COMPONENT_PROPS)
                if eid.startswith("cmp:")
                else ", ".join(_CONSTRAINT_PROPS)
            )
            + ".",
            code="pk_needs",
        )
    prefix, _, name = eid.partition(":")
    if eid.startswith("asm"):
        raise CommandError(
            "the assembly itself has no settings; set a component (cmp:<name>: at, rot, "
            "grounded, suppressed) or a constraint (mate:/jt:<name>: offset, angle, flip, "
            "limits, suppressed).",
            code="pk_ref_unknown",
        )
    if prefix == "cmp":
        return _set_component(doc, record, name, props, assumed)
    return _set_constraint(doc, record, prefix, name, props, assumed)


def _record_for(doc: Document, eid: str) -> DocAssembly:
    if not doc.assemblies:
        raise CommandError(
            f"nothing to set on {eid!r}: this document has no assembly. Create a component first.",
            code="pk_ref_unknown",
        )
    prefix, _, name = eid.partition(":")
    for record in doc.assemblies.values():
        if prefix == "cmp" and name in record.asm.components:
            return record
        if prefix in ("mate", "jt") and any(
            c.name == name and _prefix(c) == prefix for c in record.asm.constraints()
        ):
            return record
        if eid.startswith("asm"):
            return record
    record = next(iter(doc.assemblies.values()))
    known = ", ".join(r["id"] for r in record.entity_rows())
    raise CommandError(f"no assembly entity {eid!r}. Entities: {known}.", code="pk_ref_unknown")


def _set_component(
    doc: Document,
    record: DocAssembly,
    name: str,
    props: dict[str, Any],
    assumed: dict[str, Any],
) -> dict[str, Any]:
    component = record.asm.component(name)
    changed: list[dict[str, Any]] = []
    for key, value in props.items():
        if key in ("at", "rot"):
            old = _pose_row(component.pose)
            merged = {"at": props.get("at"), "rot": props.get("rot")}
            if merged["at"] is None:
                merged["at"] = list(component.pose.translation)
            component.pose = _pose_of(doc, merged, assumed)
            if not any(c["key"] == "pose" for c in changed):
                changed.append({"key": "pose", "old": old, "new": _pose_row(component.pose)})
        elif key == "grounded":
            if not isinstance(value, bool):
                raise CommandError("grounded is true or false.", code="pk_needs")
            changed.append({"key": key, "old": component.grounded, "new": value})
            component.grounded = value
        elif key == "suppressed":
            raise CommandError(
                "a component is not suppressed; delete it (cascade: true removes the mates "
                "that hold it) or suppress the mate that places it.",
                code="pk_needs",
            )
        elif key == "part":
            part_name = _part_of(doc, {"part": value}, assumed)
            changed.append({"key": key, "old": component.part_name, "new": part_name})
            component.part_name = part_name
            component.shape_ref = _shape_getter(doc, part_name)
            record.parts[name] = part_name
        elif key == "name":
            new = doc.new_name({"name": value}, "cmp", record.asm.components)
            changed.append({"key": key, "old": name, "new": new})
            record.rebuild(
                [
                    replace(c, name=new) if c.name == name else c
                    for c in record.asm.components.values()
                ],
                [_rename_in(c, name, new) for c in record.asm.constraints()],
            )
            component = record.asm.component(new)
            name = new
        else:
            raise CommandError(
                f"a component has no setting {key!r}. Settings: {', '.join(_COMPONENT_PROPS)}.",
                code="pk_ref_unknown",
            )
    record.invalidate()
    return _result(
        record,
        {"id": f"cmp:{name}", "kind": "component", "props": changed},
        pose_of=name,
    )


def _rename_in(constraint: Constraint, old: str, new: str) -> Constraint:
    a = replace(constraint.a, component=new) if constraint.a.component == old else constraint.a
    b = replace(constraint.b, component=new) if constraint.b.component == old else constraint.b
    return replace(constraint, a=a, b=b)


def _set_constraint(
    doc: Document,
    record: DocAssembly,
    prefix: str,
    name: str,
    props: dict[str, Any],
    assumed: dict[str, Any],
) -> dict[str, Any]:
    constraint = record.constraint(name)
    before = record.solved().dof
    changed: list[dict[str, Any]] = []
    updates: dict[str, Any] = {}
    for key, value in props.items():
        if key in ("offset", "offset_mm"):
            new = None if value is None else doc.length(value, assumed)
            changed.append({"key": "offset_mm", "old": constraint.offset_mm, "new": new})
            updates["offset_mm"] = new
        elif key in ("angle", "angle_deg"):
            new = doc.angle(value, assumed)
            changed.append({"key": "angle_deg", "old": constraint.angle_deg, "new": new})
            updates["angle_deg"] = new
        elif key == "flip":
            if not isinstance(constraint, Mate):
                raise CommandError("flip belongs to a mate, not a joint.", code="pk_ref_unknown")
            changed.append({"key": key, "old": constraint.flip, "new": bool(value)})
            updates["flip"] = bool(value)
        elif key == "limits":
            if not isinstance(constraint, Joint):
                raise CommandError("limits belong to a joint, not a mate.", code="pk_ref_unknown")
            new = None if value is None else (float(value[0]), float(value[1]))
            changed.append({"key": key, "old": constraint.limits, "new": new})
            updates["limits"] = new
        elif key in ("type", "kind"):
            kinds = MATE_KINDS if isinstance(constraint, Mate) else JOINT_KINDS
            if str(value) not in kinds:
                raise CommandError(f"{value!r} is not one of {', '.join(kinds)}.", code="pk_bad_op")
            changed.append({"key": "type", "old": constraint.kind, "new": str(value)})
            updates["kind"] = str(value)
        elif key == "suppressed":
            if not isinstance(value, bool):
                raise CommandError("suppressed is true or false.", code="pk_needs")
            was = constraint.name in record.suppressed
            changed.append({"key": key, "old": was, "new": value})
            if value:
                record.suppressed.add(constraint.name)
            else:
                record.suppressed.discard(constraint.name)
        elif key == "name":
            new_name = doc.new_name(
                {"name": value}, prefix, {c.name: c for c in record.asm.constraints()}
            )
            changed.append({"key": key, "old": name, "new": new_name})
            updates["name"] = new_name
        else:
            raise CommandError(
                f"a {('mate' if prefix == 'mate' else 'joint')} has no setting {key!r}. "
                f"Settings: {', '.join(_CONSTRAINT_PROPS)}.",
                code="pk_ref_unknown",
            )
    if updates:
        fresh = replace(constraint, **updates)
        record.rebuild(
            list(record.asm.components.values()),
            [fresh if c.name == name else c for c in record.asm.constraints()],
        )
        if "name" in updates:
            if name in record.suppressed:
                record.suppressed.discard(name)
                record.suppressed.add(str(updates["name"]))
            name = str(updates["name"])
        constraint = record.constraint(name)
    record.invalidate()
    body = _constraint_result(record, constraint, "mate" if prefix == "mate" else "joint", before)
    body["props"] = changed
    return _result(record, body)


def delete_target(
    doc: Document, target: str, cascade: bool, assumed: dict[str, Any]
) -> dict[str, Any]:
    """Delete a component, a constraint or the whole assembly; a component that
    two mates hold refuses by name unless `cascade`."""
    eid = str(target)
    record = _record_for(doc, eid)
    prefix, _, name = eid.partition(":")
    if eid.startswith("asm"):
        held = [f"cmp:{n}" for n in sorted(record.asm.components)]
        if held and not cascade:
            raise CommandError(
                f"{eid} holds {', '.join(held)}. Delete those first, or pass cascade: true "
                "to remove the assembly with them.",
                code="pk_delete_blocked",
            )
        doc.assemblies.pop(record.name, None)
        return {"deleted": [eid, *held], "assemblies": len(doc.assemblies)}
    if prefix == "cmp":
        record.asm.component(name)
        blocked = record.dependents_of_component(name)
        if blocked and not cascade:
            raise CommandError(
                f"cmp:{name} is held by {', '.join(blocked)}. Delete those first, or pass "
                "cascade: true to remove them with it.",
                code="pk_delete_blocked",
            )
        record.rebuild(
            [c for c in record.asm.components.values() if c.name != name],
            [c for c in record.asm.constraints() if name not in (c.a.component, c.b.component)],
        )
        removed = [eid, *blocked]
    else:
        record.constraint(name)
        record.rebuild(
            list(record.asm.components.values()),
            [c for c in record.asm.constraints() if c.name != name],
        )
        removed = [eid]
    body: dict[str, Any] = {"deleted": removed, "components": len(record.asm.components)}
    if record.asm.components:
        return _result(record, body)
    doc.assemblies.pop(record.name, None)
    return body


# --------------------------------------------------------------------------- fingerprint


def fingerprint_payload(doc: Document) -> list[list[Any]]:
    """Poses and constraints, rounded to 1e-6 before hashing (D3, rule 7)."""
    rows: list[list[Any]] = []
    for name in sorted(doc.assemblies):
        record = doc.assemblies[name]
        components = [
            [
                c.name,
                c.part_name,
                c.grounded,
                c.virtual,
                [_r6(v) for v in c.pose.translation],
                [_r6(v) for v in c.pose.rotation],
            ]
            for c in sorted(record.asm.components.values(), key=lambda c: c.name)
        ]
        constraints = [
            [
                c.name,
                _prefix(c),
                c.kind,
                c.a.label(),
                c.b.label(),
                None if c.offset_mm is None else _r6(c.offset_mm),
                _r6(c.angle_deg),
                c.name in record.suppressed,
            ]
            for c in record.asm.constraints()
        ]
        rows.append([name, components, constraints])
    return rows


def part_cards(doc: Document, record: DocAssembly) -> dict[str, dict[str, Any]]:
    """The `parts=` argument `assembly.bom` wants: material and mass per part."""
    cards: dict[str, dict[str, Any]] = {}
    for part_name in sorted({c.part_name for c in record.asm.components.values()}):
        part = doc.parts.get(part_name)
        if part is None:
            continue
        card: dict[str, Any] = {"material": part.material}
        mass = part.mass_g()
        if mass is not None:
            card["mass_g"] = mass
        elif part.shape is not None:
            card["volume_mm3"] = part.volume()
        cards[part_name] = card
    return cards


__all__ = [
    "DEFAULT_ASSEMBLY",
    "MAX_PAIRS",
    "DocAssembly",
    "assembly_of",
    "delete_target",
    "dependents",
    "fingerprint_payload",
    "frame_ref",
    "part_cards",
    "set_target",
]
