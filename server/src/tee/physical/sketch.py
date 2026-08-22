"""sketch_solve (A21): server-side 2D constraint solving with py-slvs
(the SolveSpace wheel) - dimensioned plans close BEFORE extrusion, with
zero DCC involvement.

Input contract (all lengths meters, angles degrees):
    points: [{"id": "a", "at": [x, y], "fixed": true?}, …]   guesses
    lines:  [{"id": "ab", "from": "a", "to": "b"}, …]
    constraints: [
      {"kind": "distance", "a": "a", "b": "b", "value": 4.0},
      {"kind": "horizontal" | "vertical", "line": "ab"},
      {"kind": "angle", "l1": "ab", "l2": "bc", "value": 90},
      {"kind": "parallel" | "perpendicular" | "equal_length",
       "l1": "ab", "l2": "cd"},
      {"kind": "coincident", "a": "a", "b": "d"},
    ]

Failures are one short message with the exact fix: over-constrained
names the offending constraint(s); under-constrained reports the free
degrees of freedom (2 DOF - the rigid-body translation - is normal for
an unanchored sketch and solves fine).
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError

_RESULT = {0: "ok", 1: "inconsistent", 2: "didnt_converge", 3: "too_many_unknowns"}


def solve_sketch(sketch: dict[str, Any]) -> dict[str, Any]:
    try:
        from py_slvs import slvs
    except ImportError as exc:
        raise TeeError(
            "physical_extra_missing",
            "sketch_solve needs py-slvs (the [physical] extra).",
            fix="uv sync --extra physical",
        ) from exc

    system = slvs.System()
    param_handle = 0

    def add_param(group: int, value: float) -> int:
        nonlocal param_handle
        param_handle += 1
        return system.addParam(slvs.makeParam(param_handle, group, float(value)))

    base_group = 1
    origin = system.addPoint3d(
        add_param(base_group, 0), add_param(base_group, 0), add_param(base_group, 0),
        base_group,
    )
    normal = system.addNormal3d(
        add_param(base_group, 1), add_param(base_group, 0),
        add_param(base_group, 0), add_param(base_group, 0), base_group,
    )
    workplane = system.addWorkplane(origin, normal, base_group)
    group = 2

    points: dict[str, int] = {}
    fixed_lookup: dict[str, tuple[float, float]] = {}
    for spec in sketch.get("points", []):
        pid = str(spec["id"])
        x, y = (float(v) for v in spec.get("at", [0.0, 0.0]))
        target_group = base_group if spec.get("fixed") else group
        points[pid] = system.addPoint2d(
            workplane, add_param(target_group, x), add_param(target_group, y),
            target_group,
        )
        if spec.get("fixed"):
            fixed_lookup[pid] = (x, y)
    if not points:
        raise TeeError("empty_sketch", "sketch has no points.", fix="add points+constraints")

    lines: dict[str, int] = {}
    for spec in sketch.get("lines", []):
        lid = str(spec["id"])
        try:
            lines[lid] = system.addLineSegment(
                points[str(spec["from"])], points[str(spec["to"])], group
            )
        except KeyError as exc:
            raise TeeError(
                "unknown_point",
                f"line '{lid}' references unknown point {exc}.",
                fix=f"declared points: {', '.join(points)}",
            ) from exc

    constraint_labels: dict[int, str] = {}

    def _point(ref: Any, constraint: dict) -> int:
        key = str(ref)
        if key not in points:
            raise TeeError(
                "unknown_point",
                f"constraint {constraint.get('kind')} references unknown point '{key}'.",
                fix=f"declared points: {', '.join(points)}",
            )
        return points[key]

    def _line(ref: Any, constraint: dict) -> int:
        key = str(ref)
        if key not in lines:
            raise TeeError(
                "unknown_line",
                f"constraint {constraint.get('kind')} references unknown line '{key}'.",
                fix=f"declared lines: {', '.join(lines)}",
            )
        return lines[key]

    for index, con in enumerate(sketch.get("constraints", [])):
        kind = con.get("kind")
        label = f"[{index}] {kind}"
        if kind == "distance":
            handle = system.addPointsDistance(
                float(con["value"]), _point(con["a"], con), _point(con["b"], con),
                workplane, group,
            )
        elif kind == "horizontal":
            line = con.get("line")
            if line is not None:
                handle = system.addLineHorizontal(_line(line, con), workplane, group)
            else:
                handle = system.addPointsHorizontal(
                    _point(con["a"], con), _point(con["b"], con), workplane, group
                )
        elif kind == "vertical":
            line = con.get("line")
            if line is not None:
                handle = system.addLineVertical(_line(line, con), workplane, group)
            else:
                handle = system.addPointsVertical(
                    _point(con["a"], con), _point(con["b"], con), workplane, group
                )
        elif kind == "angle":
            handle = system.addAngle(
                float(con["value"]), False, _line(con["l1"], con),
                _line(con["l2"], con), workplane, group,
            )
        elif kind == "parallel":
            handle = system.addParallel(
                _line(con["l1"], con), _line(con["l2"], con), workplane, group
            )
        elif kind == "perpendicular":
            handle = system.addPerpendicular(
                _line(con["l1"], con), _line(con["l2"], con), workplane, group
            )
        elif kind == "equal_length":
            handle = system.addEqualLength(
                _line(con["l1"], con), _line(con["l2"], con), workplane, group
            )
        elif kind == "coincident":
            handle = system.addPointsCoincident(
                _point(con["a"], con), _point(con["b"], con), workplane, group
            )
        else:
            raise TeeError(
                "unknown_constraint",
                f"constraint [{index}] has unknown kind '{kind}'.",
                fix="kinds: distance, horizontal, vertical, angle, parallel, "
                "perpendicular, equal_length, coincident",
            )
        constraint_labels[int(handle)] = label

    result = system.solve(group, True)
    status = _RESULT.get(result, str(result))
    if result == 1 or (result != 0 and system.Failed):
        failing = [constraint_labels.get(int(f), f"handle {int(f)}") for f in system.Failed]
        raise TeeError(
            "over_constrained",
            f"sketch is over-constrained ({status}): {', '.join(failing)} "
            "cannot all hold.",
            fix="remove or correct one of the named constraints "
            "(dimensions likely disagree with the topology)",
        )
    if result != 0:
        raise TeeError(
            "solve_failed",
            f"sketch did not solve ({status}).",
            fix="check for contradictory or numerically extreme dimensions",
        )

    solved: dict[str, list[float]] = {}
    for pid, handle in points.items():
        if pid in fixed_lookup:
            solved[pid] = [fixed_lookup[pid][0], fixed_lookup[pid][1]]
            continue
        x = system.getParam(system.getEntityParam(handle, 0)).val
        y = system.getParam(system.getEntityParam(handle, 1)).val
        solved[pid] = [round(x, 6), round(y, 6)]
    dof = int(system.Dof)
    out: dict[str, Any] = {"ok": True, "points": solved, "dof": dof}
    anchored = bool(fixed_lookup)
    free_allowance = 0 if anchored else 3  # translation x2 + rotation
    if dof > free_allowance:
        out["under_constrained"] = (
            f"{dof} degrees of freedom remain"
            + ("" if anchored else " (3 = free placement, more = loose geometry)")
            + " - add dimensions if the shape wandered from intent"
        )
    return out


def polygon_from(solved: dict[str, list[float]], order: list[str]) -> list[list[float]]:
    """Ordered closed polygon from solved points - feeds wall/slab ops."""
    missing = [p for p in order if p not in solved]
    if missing:
        raise TeeError(
            "unknown_point", f"polygon order references unsolved points {missing}."
        )
    return [solved[p] for p in order]
