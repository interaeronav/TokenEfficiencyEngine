"""Offline cabinet drill jobs with a deliberately limited virtual post.

This module writes no files, contacts no controller and executes no programs.
Its parser verifies the emitted text against a fresh source-derived drill job.
A virtual-post pass is not commissioning of any physical machine or tooling.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from typing import Any

from tee.architecture.cabinet_production import (
    _enum,
    _identifier,
    _object,
    _rows,
    _source,
    _text,
    build,
)
from tee.architecture.model import ArchitectureError, number, positive

SCHEMA = "tee-cabinet-cnc-job/1"
SETUP_SCHEMA = "tee-cabinet-cnc-setup/1"
POST = "tee-virtual-router/1"
MAX_LINES = 10000
_TOL = 1e-5  # program coordinates are written to six decimal places
_NUM = r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?"
_MOVE = re.compile(rf"(G0|G1) X({_NUM}) Y({_NUM}) Z({_NUM})(?: F({_NUM}))?\Z")
_SPINDLE = re.compile(rf"M3 S({_NUM})\Z")


def _vector(value: Any, name: str, size: int) -> list[float]:
    if not isinstance(value, list) or len(value) != size:
        raise ArchitectureError(f"{name} needs exactly {size} coordinates in mm.")
    return [number(v, name) for v in value]


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _prepare(entity: dict[str, Any], setup: dict[str, Any]) -> dict[str, Any]:
    """Validate supplied stock/tool/setup facts without assuming machine defaults."""
    _object(
        setup,
        "cnc setup",
        {
            "schema",
            "post",
            "part_id",
            "face",
            "source",
            "machine",
            "frame",
            "safe_z_mm",
            "initial_position_mm",
            "through_overtravel_mm",
            "tool",
            "fixture_exclusions",
        },
    )
    if setup.get("schema") != SETUP_SCHEMA or setup.get("post") != POST:
        raise ArchitectureError(
            f"Only setup.schema={SETUP_SCHEMA} and post={POST} are supported; "
            "no physical-machine post is commissioned."
        )
    source = _source(setup.get("source"), "cnc setup.source")
    report = build(entity)
    pid = _text(setup.get("part_id"), "cnc setup.part_id")
    by_id = {row["id"]: row for row in report["panels"]}
    if pid not in by_id:
        raise ArchitectureError("CNC setup names an unknown cabinet panel.")
    part = by_id[pid]
    face = _enum(setup.get("face"), "cnc setup.face", {"front", "back"})
    operations = [op for op in report["machining"] if op["part_id"] == pid and op["face"] == face]
    if not operations:
        raise ArchitectureError("CNC setup has no explicit operations on this panel/face.")
    if len(operations) > 200:
        raise ArchitectureError("A virtual drill setup supports at most 200 holes.")
    if any(op["type"] != "drill" for op in operations):
        raise ArchitectureError(
            "This virtual post supports drills only; pockets are not silently omitted."
        )
    machine = _object(
        setup.get("machine"),
        "machine",
        {
            "id",
            "revision",
            "travel_mm",
            "max_feed_mm_min",
            "max_spindle_rpm",
        },
    )
    _identifier(machine.get("id"), "machine.id")
    _text(machine.get("revision"), "machine.revision")
    travel = _vector(machine.get("travel_mm"), "machine.travel_mm", 3)
    if min(travel) <= 0:
        raise ArchitectureError("machine.travel_mm must be positive on all axes.")
    max_feed = positive(machine.get("max_feed_mm_min"), "machine.max_feed_mm_min")
    max_spindle = positive(machine.get("max_spindle_rpm"), "machine.max_spindle_rpm")
    tool = _object(
        setup.get("tool"),
        "tool",
        {
            "id",
            "diameter_mm",
            "cutting_length_mm",
            "feed_mm_min",
            "spindle_rpm",
            "peck_mm",
        },
    )
    _identifier(tool.get("id"), "tool.id")
    diameter, cutting_length, feed, spindle, peck = (
        positive(tool.get(k), f"tool.{k}")
        for k in (
            "diameter_mm",
            "cutting_length_mm",
            "feed_mm_min",
            "spindle_rpm",
            "peck_mm",
        )
    )
    if min(diameter, cutting_length, feed, spindle, peck) < 0.001:
        raise ArchitectureError(
            "Tool dimensions/feed/spindle/peck must be at least 0.001 "
            "for this virtual post's resolution."
        )
    if feed > max_feed or spindle > max_spindle:
        raise ArchitectureError("Supplied tool feed/spindle exceeds the declared machine limits.")
    if any(
        not math.isclose(op["diameter_mm"], diameter, rel_tol=0, abs_tol=1e-7) for op in operations
    ):
        raise ArchitectureError(
            "All holes in this setup must match the selected drill diameter; "
            "multiple tools are unsupported."
        )
    frame = _object(setup.get("frame"), "frame", {"origin_xy_mm", "axis_map", "top_z_mm"})
    xy = _vector(frame.get("origin_xy_mm"), "frame.origin_xy_mm", 2)
    axis_map = frame.get("axis_map")
    if (
        not isinstance(axis_map, list)
        or len(axis_map) != 2
        or any(not isinstance(row, list) or len(row) != 2 for row in axis_map)
        or any(type(v) is not int or v not in {-1, 0, 1} for row in axis_map for v in row)
        or any(sum(abs(v) for v in row) != 1 for row in axis_map)
        or any(sum(abs(axis_map[i][j]) for i in range(2)) != 1 for j in range(2))
    ):
        raise ArchitectureError("frame.axis_map must be an explicit signed 2x2 axis permutation.")
    top = number(frame.get("top_z_mm"), "frame.top_z_mm", minimum=0)
    safe = positive(setup.get("safe_z_mm"), "safe_z_mm")
    initial = _vector(setup.get("initial_position_mm"), "initial_position_mm", 3)
    overtravel = number(setup.get("through_overtravel_mm"), "through_overtravel_mm", minimum=0)
    if safe <= top or safe > travel[2] or initial[2] < safe:
        raise ArchitectureError(
            "safe_z_mm must be above the stock, within travel; initial Z must be at or above it."
        )
    if top < part["thickness"]:
        raise ArchitectureError("Stock bottom falls below the virtual machine's Z travel.")
    if any(v < 0 or v > travel[i] for i, v in enumerate(initial)):
        raise ArchitectureError("initial_position_mm is outside declared machine travel.")

    def transform(u: float, v: float) -> list[float]:
        return [xy[i] + axis_map[i][0] * u + axis_map[i][1] * v for i in range(2)]

    corners = [
        transform(u, v) for u in (0, part["finished_width"]) for v in (0, part["finished_height"])
    ]
    if any(coord < 0 or coord > travel[i] for corner in corners for i, coord in enumerate(corner)):
        raise ArchitectureError("The transformed full panel exceeds declared machine XY travel.")
    stock_bounds = [
        [min(c[i] for c in corners) for i in range(2)] + [top - part["thickness"]],
        [max(c[i] for c in corners) for i in range(2)] + [top],
    ]
    fixtures = []
    fixture_ids = set()
    for box in _rows(setup.get("fixture_exclusions"), "fixture_exclusions", 100):
        _object(box, "fixture exclusion", {"id", "min_mm", "max_mm"})
        fid = _identifier(box.get("id"), "fixture.id")
        if fid in fixture_ids:
            raise ArchitectureError("fixture.id must be unique.")
        fixture_ids.add(fid)
        low = _vector(box.get("min_mm"), "fixture.min_mm", 3)
        high = _vector(box.get("max_mm"), "fixture.max_mm", 3)
        if any(low[i] >= high[i] or low[i] < 0 or high[i] > travel[i] for i in range(3)):
            raise ArchitectureError("Fixture bounds must be ordered, nonempty and within travel.")
        fixtures.append({"id": fid, "min_mm": low, "max_mm": high})
    holes = []
    for op in sorted(operations, key=lambda row: row["id"]):
        depth = op["depth_mm"] + (overtravel if op["through"] else 0)
        if depth > cutting_length or depth > top:
            raise ArchitectureError(
                f"Hole {op['id']} exceeds cutting length or Z travel including through overtravel."
            )
        steps = math.ceil(depth / peck)
        if steps > 200:
            raise ArchitectureError(
                "peck_mm requires more than 200 pecks per hole; revise the explicit tool setup."
            )
        px, py = transform(op["u_mm"], op["v_mm"])
        holes.append(
            {
                "id": op["id"],
                "xy_mm": [px, py],
                "depth_mm": depth,
                "end_z_mm": top - depth,
                "diameter_mm": diameter,
                "pecks": steps,
            }
        )
    if sum(hole["pecks"] * 2 + 1 for hole in holes) + 12 > MAX_LINES:
        raise ArchitectureError("Virtual program exceeds the bounded line budget; split the setup.")
    return {
        "part": part,
        "source": source,
        "report": report,
        "machine": machine,
        "travel": travel,
        "tool": tool,
        "safe": safe,
        "top": top,
        "initial": initial,
        "fixtures": fixtures,
        "holes": holes,
        "stock_bounds_mm": stock_bounds,
        "unplanned_operations": [op["id"] for op in report["machining"] if op not in operations],
    }


def plan_job(entity: dict[str, Any], setup: dict[str, Any]) -> dict[str, Any]:
    """Return a source-bound virtual program and a parsed independent simulation."""
    context = _prepare(entity, setup)
    safe, top, tool = context["safe"], context["top"], context["tool"]
    lines = [
        "(TEE VIRTUAL ROUTER - UNCOMMISSIONED - DO NOT RUN ON A MACHINE)",
        "G21",
        "G90",
        "G17",
        "G94",
        "G40",
        "G49",
        "G80",
        f"M3 S{tool['spindle_rpm']:.6f}",
    ]

    def move(mode: str, x: float, y: float, z: float) -> None:
        suffix = f" F{tool['feed_mm_min']:.6f}" if mode == "G1" else ""
        lines.append(f"{mode} X{x:.6f} Y{y:.6f} Z{z:.6f}{suffix}")

    ix, iy, _ = context["initial"]
    move("G0", ix, iy, safe)
    for hole in context["holes"]:
        x, y = hole["xy_mm"]
        move("G0", x, y, safe)
        for i in range(1, hole["pecks"] + 1):
            depth = min(i * tool["peck_mm"], hole["depth_mm"])
            move("G1", x, y, top - depth)
            move("G0", x, y, safe)
    lines.extend(["M5", "M2"])
    program = "\n".join(lines) + "\n"
    simulation = simulate_program(program, entity, setup)
    return {
        "schema": SCHEMA,
        "post": POST,
        "part_id": setup["part_id"],
        "face": setup["face"],
        "source": copy.deepcopy(context["source"]),
        "recipe_sha256": context["report"]["assembly"]["recipe_sha256"],
        "setup_sha256": _digest(setup),
        "input_sha256": _digest({"entity": entity, "setup": setup}),
        "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "operation_ids": [hole["id"] for hole in context["holes"]],
        "unplanned_operation_ids": context["unplanned_operations"],
        "setup": copy.deepcopy(setup),
        "stock_bounds_mm": context["stock_bounds_mm"],
        "program": program,
        "simulation": simulation,
        "readiness": "virtual_post_only_not_commissioned",
        "not_verified": [
            "physical machine/controller",
            "work offsets and homing",
            "tool loading",
            "tool shank and holder collisions",
            "drill tip geometry",
            "hardware specification",
            "hold-down forces",
            "feeds/speeds suitability",
            "machine commissioning",
        ],
        "unsupported": [
            "pocket CAM",
            "multiple tools",
            "tool changes",
            "sheet nesting CAM",
            "physical machine execution",
        ],
    }


def _intersects(start: list[float], end: list[float], low: list[float], high: list[float]) -> bool:
    """Slab intersection of an axis-aligned box and a segment, including contact."""
    enter, leave = 0.0, 1.0
    for axis in range(3):
        delta = end[axis] - start[axis]
        if abs(delta) < 1e-12:
            if start[axis] < low[axis] or start[axis] > high[axis]:
                return False
        else:
            a, b = (low[axis] - start[axis]) / delta, (high[axis] - start[axis]) / delta
            enter, leave = max(enter, min(a, b)), min(leave, max(a, b))
            if enter > leave:
                return False
    return True


def simulate_program(program: str, entity: dict[str, Any], setup: dict[str, Any]) -> dict[str, Any]:
    """Parse supported G-code text; reject changes that violate the source job.

    No executable parser, macros, interpolation, controller or network is involved.
    The accepted language deliberately excludes even valid unsupported G-code.
    """
    context = _prepare(entity, setup)
    if not isinstance(program, str) or len(program) > 1_000_000:
        raise ArchitectureError("Virtual program must be text of at most 1 MB.")
    raw = program.splitlines()
    if len(raw) > MAX_LINES:
        raise ArchitectureError("Virtual program exceeds the supported line budget.")
    commands = []
    for line in raw:
        clean = line.strip()
        if not clean:
            continue
        if (
            clean.startswith("(")
            and clean.endswith(")")
            and "(" not in clean[1:]
            and ")" not in clean[:-1]
        ):
            continue
        commands.append(clean)
    header = ["G21", "G90", "G17", "G94", "G40", "G49", "G80"]
    if commands[: len(header)] != header:
        raise ArchitectureError(
            "Virtual program must explicitly establish mm/absolute/plane/feed/cancel modes."
        )
    pos = list(context["initial"])
    spindle = False
    ended = False
    seen_shutdown = False
    move_count = 0
    completed: dict[str, float] = {hole["id"]: 0 for hole in context["holes"]}
    radius = context["tool"]["diameter_mm"] / 2
    cut_length = context["tool"]["cutting_length_mm"]
    plunge_count = 0
    for command in commands[len(header) :]:
        if ended:
            raise ArchitectureError("Virtual program contains commands after M2.")
        spin = _SPINDLE.fullmatch(command)
        if spin:
            if spindle or seen_shutdown or move_count:
                raise ArchitectureError("Virtual spindle must start once, before motion.")
            rpm = float(spin[1])
            if abs(rpm - context["tool"]["spindle_rpm"]) > _TOL:
                raise ArchitectureError(
                    "Program spindle speed differs from the explicit tool setup."
                )
            spindle = True
            continue
        if command == "M5":
            if not spindle or pos[2] < context["safe"] - _TOL:
                raise ArchitectureError(
                    "Spindle stop requires spindle running and retraction to safe Z."
                )
            spindle, seen_shutdown = False, True
            continue
        if command == "M2":
            if spindle or not seen_shutdown:
                raise ArchitectureError("Program must stop spindle before M2.")
            ended = True
            continue
        match = _MOVE.fullmatch(command)
        if not match or not spindle or seen_shutdown:
            raise ArchitectureError(
                "Unsupported command or motion without the declared spindle state."
            )
        mode = match[1]
        target = [float(match[i]) for i in (2, 3, 4)]
        if any(
            not math.isfinite(v) or v < 0 or v > context["travel"][i] + _TOL
            for i, v in enumerate(target)
        ):
            raise ArchitectureError("Program move exceeds declared machine travel.")
        lateral = abs(pos[0] - target[0]) > _TOL or abs(pos[1] - target[1]) > _TOL
        if mode == "G0":
            if match[5] is not None:
                raise ArchitectureError("Virtual rapid move must not carry a feed override.")
            if lateral and min(pos[2], target[2]) < context["safe"] - _TOL:
                raise ArchitectureError("Rapid lateral motion crosses stock below safe Z.")
            if target[2] < pos[2] - _TOL and target[2] < context["top"] - _TOL:
                raise ArchitectureError("Rapid plunge enters stock; drilling must use G1.")
            if pos[2] < context["top"] - _TOL:
                cleared = any(
                    abs(pos[0] - hole["xy_mm"][0]) <= _TOL
                    and abs(pos[1] - hole["xy_mm"][1]) <= _TOL
                    and completed[hole["id"]] >= context["top"] - pos[2] - _TOL
                    for hole in context["holes"]
                )
                if lateral or target[2] < pos[2] - _TOL or not cleared:
                    raise ArchitectureError(
                        "Rapid inside stock is allowed only up a previously drilled column."
                    )
        else:
            if match[5] is None or abs(float(match[5]) - context["tool"]["feed_mm_min"]) > _TOL:
                raise ArchitectureError("Program feed differs from the explicit tool setup.")
            if lateral or target[2] >= context["top"] - _TOL or target[2] >= pos[2]:
                raise ArchitectureError("This virtual post permits vertical drilling plunges only.")
            if pos[2] < context["safe"] - _TOL:
                raise ArchitectureError("Each modeled peck begins from the declared safe Z.")
            hole = next(
                (
                    h
                    for h in context["holes"]
                    if abs(target[0] - h["xy_mm"][0]) <= _TOL
                    and abs(target[1] - h["xy_mm"][1]) <= _TOL
                ),
                None,
            )
            if hole is None:
                raise ArchitectureError(
                    "Program drills a location absent from the source operations."
                )
            depth = context["top"] - target[2]
            previous = completed[hole["id"]]
            expected = min(previous + context["tool"]["peck_mm"], hole["depth_mm"])
            if depth <= previous + _TOL or abs(depth - expected) > _TOL:
                raise ArchitectureError(
                    "Program hole depth/peck differs from the source operation and tool setup."
                )
            completed[hole["id"]] = depth
            plunge_count += 1
        for fixture in context["fixtures"]:
            low = [
                fixture["min_mm"][0] - radius,
                fixture["min_mm"][1] - radius,
                fixture["min_mm"][2] - cut_length,
            ]
            high = [
                fixture["max_mm"][0] + radius,
                fixture["max_mm"][1] + radius,
                fixture["max_mm"][2],
            ]
            if _intersects(pos, target, low, high):
                raise ArchitectureError(
                    f"Program cutter envelope intersects fixture {fixture['id']}."
                )
        pos = target
        move_count += 1
    if not ended or spindle or pos[2] < context["safe"] - _TOL:
        raise ArchitectureError("Virtual program lacks completed spindle stop/end/safe retraction.")
    if any(abs(completed[h["id"]] - h["depth_mm"]) > _TOL for h in context["holes"]):
        raise ArchitectureError("Virtual program omits or incompletely drills a source operation.")
    return {
        "status": "passed_virtual_post",
        "moves": move_count,
        "plunges": plunge_count,
        "completed_holes": len(completed),
        "final_position_mm": pos,
        "checks": [
            "source hole positions and peck depths",
            "machine travel",
            "explicit feed/spindle",
            "rapid stock crossing",
            "bounded cutter envelope against declared fixture boxes",
            "safe retraction and spindle stop",
        ],
        "scope": "ideal cylindrical drill; virtual coordinate system; "
        "supplied facts not independently verified",
        "machine_commissioning": "not_verified",
    }
