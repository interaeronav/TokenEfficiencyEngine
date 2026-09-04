"""The controls: each one BUILDS a command dict, and nothing else.

A53 Law 3, carried into A66: *the GUI is a client of the core*. A control here
writes the same `{op, kind, name, props}` object a model sends through
`tee_batch` (D5), so a click and a script line are the same thing and there is
no path through the window that a batch cannot take. `shell.py` applies it;
this module never touches a kernel.

A factory reads the D7 entity ROWS - what `KernelClient.entities()` puts on the
wire - and nothing else, so the same table drives the in-process kernel and the
sidecar. It never reads geometry: hard rule 1 keeps coordinates off the wire,
and a control that needed them would be a control the sidecar could not build.

A factory that cannot build its command raises `ValueError` naming the fix
(rule 6). That is the same contract as a refused command, and the shell logs it
without touching the document.

Qt-free on purpose: PySide6 is not installed on the machine that wrote this, so
every control is exercised by `tests/test_gui.py` with Qt absent.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Row = Mapping[str, Any]
State = Sequence[Row]
Factory = Callable[[State, Path], dict[str, Any]]

# The parameter table the shell starts from. Every length downstream is one of
# these or an expression over one, so "Set W" is a part family in one press and
# the script `pk_script` hands back replays as one too.
PARAMS: dict[str, str] = {
    "W": "120mm",
    "H": "80mm",
    "T": "10mm",
    "PX": "100mm",
    "PY": "50mm",
    "R": "5mm",
    "C": "1mm",
}


# -- reading the rows ----------------------------------------------------------


def _ids(state: State, prefix: str) -> list[str]:
    """Every entity name under one id prefix, in row order (kernel order)."""
    head = f"{prefix}:"
    return [str(row["id"])[len(head) :] for row in state if str(row.get("id", "")).startswith(head)]


def _kinds(state: State, prefix: str, *kinds: str) -> list[str]:
    head = f"{prefix}:"
    return [
        str(row["id"])[len(head) :]
        for row in state
        if str(row.get("id", "")).startswith(head) and row.get("kind") in kinds
    ]


def _free_name(state: State, prefix: str, stem: str) -> str:
    """`stem1`, `stem2`, ... - the first one no entity under `prefix` holds.

    Names are ours to choose (D5: omitted -> `<kind><n>`), but a shell that
    reuses one would silently redefine a feature, so it counts instead.
    """
    taken = set(_ids(state, prefix))
    index = 1
    while f"{stem}{index}" in taken:
        index += 1
    return f"{stem}{index}"


def _params(state: State) -> dict[str, float]:
    return {str(row["name"]): float(row["value"]) for row in state if row.get("kind") == "param"}


def _need_params(state: State, *names: str) -> None:
    missing = [n for n in names if n not in _params(state)]
    if missing:
        raise ValueError(
            f"no parameter {', '.join(missing)}: press Parameters first "
            f"(it sets {', '.join(sorted(PARAMS))})."
        )


def _need_part(state: State) -> str:
    parts = _ids(state, "part")
    if not parts:
        raise ValueError("no part yet: press New part.")
    if len(parts) > 1:
        raise ValueError(
            f"{len(parts)} parts ({', '.join(parts)}): this shell drives one. "
            "Name the part in a batch, or start a new document."
        )
    return parts[0]


def _need_feature(state: State, *kinds: str) -> str:
    found = _kinds(state, "feat", *kinds)
    if not found:
        raise ValueError(f"no {' or '.join(kinds)} feature yet: press {_PRESS[kinds[0]]} first.")
    return found[-1]


def _first_feature(state: State, *kinds: str) -> str:
    found = _kinds(state, "feat", *kinds)
    if not found:
        raise ValueError(f"no {' or '.join(kinds)} feature yet: press {_PRESS[kinds[0]]} first.")
    return found[0]


# Which button makes the thing a refusal says is missing.
_PRESS = {
    "extrude": "Extrude",
    "fillet": "Fillet",
    "hole": "Hole",
    "sketch": "Sketch",
    "pattern": "Pattern",
}


# -- the controls --------------------------------------------------------------


def _c_params(state: State, workdir: Path) -> dict[str, Any]:
    return {"op": "param_set", "props": dict(PARAMS)}


def _c_part(state: State, workdir: Path) -> dict[str, Any]:
    return {
        "op": "create",
        "kind": "part",
        "name": _free_name(state, "part", "part"),
        "props": {"material": "steel_s275"},
    }


def _c_sketch(state: State, workdir: Path) -> dict[str, Any]:
    """A W x H rectangle on XY - the profile every other control builds on."""
    _need_params(state, "W", "H")
    return {
        "op": "create",
        "kind": "sketch",
        "name": _free_name(state, "sk", "sk"),
        "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
    }


def _c_extrude(state: State, workdir: Path) -> dict[str, Any]:
    _need_params(state, "T")
    _need_part(state)
    sketches = _ids(state, "sk")
    if not sketches:
        raise ValueError("no sketch yet: press Sketch first.")
    return {
        "op": "create",
        "kind": "extrude",
        "name": _free_name(state, "feat", "ex"),
        "props": {"sketch": sketches[-1], "distance": "T"},
    }


def _c_fillet(state: State, workdir: Path) -> dict[str, Any]:
    """The four vertical corners, by selector - never by edge index (D6)."""
    _need_params(state, "R")
    base = _first_feature(state, "extrude")
    return {
        "op": "create",
        "kind": "fillet",
        "name": _free_name(state, "feat", "fl"),
        "props": {"edges": f"{base}:edges(dir=Z)", "r": "R"},
    }


def _c_chamfer(state: State, workdir: Path) -> dict[str, Any]:
    """The top face's outer loop. `loop=outer` is what keeps a hole's rim out
    of it - the A66 worked example refuses when the loop filter is dropped."""
    _need_params(state, "C")
    base = _first_feature(state, "extrude")
    return {
        "op": "create",
        "kind": "chamfer",
        "name": _free_name(state, "feat", "ch"),
        "props": {"edges": f"{base}:edges(of=end, loop=outer)", "d": "C"},
    }


def _c_hole(state: State, workdir: Path) -> dict[str, Any]:
    """One ISO 273 clearance hole, placed in the face's own frame (D5).

    The frame's origin is the world origin projected onto the face, so the
    position is written from the corner and stays parametric in W, H, PX, PY.
    """
    _need_params(state, "W", "H", "PX", "PY")
    base = _first_feature(state, "extrude")
    return {
        "op": "create",
        "kind": "hole",
        "name": _free_name(state, "feat", "hl"),
        "props": {
            "on": f"{base}.end",
            "at": [["(W-PX)/2", "(H-PY)/2"]],
            "std": "M6 clearance normal",
        },
    }


def _c_pattern(state: State, workdir: Path) -> dict[str, Any]:
    """Two instances along X at the hole pitch - one n-ary cut, not two."""
    _need_params(state, "PX")
    return {
        "op": "create",
        "kind": "pattern",
        "name": _free_name(state, "feat", "pt"),
        "props": {"of": _need_feature(state, "hole"), "dx": "PX", "nx": 2},
    }


def _c_plane(state: State, workdir: Path) -> dict[str, Any]:
    """The datum the mirror needs. XZ offset by -H/2 lands at y = +H/2: the
    XZ plane's normal is -Y, and a mirror about the wrong side of the part is
    the `pk_no_effect` refusal, not a silent no-op."""
    _need_params(state, "H")
    return {
        "op": "create",
        "kind": "plane",
        "name": _free_name(state, "plane", "mid"),
        "props": {"offset": {"from": "XZ", "distance": "-H/2"}},
    }


def _c_mirror(state: State, workdir: Path) -> dict[str, Any]:
    """Mirror the HOLE, not the pattern: only features that own a tool body
    (extrude, revolve, sweep, loft, hole) can be copied, and the kernel says so
    by name when they cannot."""
    planes = _ids(state, "plane")
    if not planes:
        raise ValueError("no datum plane yet: press Midplane first.")
    return {
        "op": "create",
        "kind": "mirror",
        "name": _free_name(state, "feat", "mr"),
        "props": {"of": _need_feature(state, "hole"), "plane": f"plane:{planes[-1]}"},
    }


def _c_set(state: State, workdir: Path) -> dict[str, Any]:
    """Edit the fillet in place: `set` on the feature, which regenerates every
    feature downstream of it and reports what each one's volume did."""
    return {
        "op": "set",
        "id": f"feat:{_need_feature(state, 'fillet')}",
        "props": {"r": "R*1.6"},
    }


def _c_widen(state: State, workdir: Path) -> dict[str, Any]:
    """The one-press part family: change W, the whole model re-derives."""
    _need_params(state, "W")
    return {"op": "param_set", "props": {"W": "140mm"}}


def _c_delete(state: State, workdir: Path) -> dict[str, Any]:
    """Delete the last feature. `cascade` is declared, not assumed: without it
    the kernel refuses and names the dependents (D5)."""
    features = _ids(state, "feat")
    if not features:
        raise ValueError("no feature to delete yet.")
    return {"op": "delete", "id": f"feat:{features[-1]}", "props": {"cascade": True}}


def _c_check(state: State, workdir: Path) -> dict[str, Any]:
    """Check the built body against the DECLARED intent - the parameter table -
    not against itself. W/H/T are what the designer typed; the bounding box is
    what OCCT measured, and a param edit that failed to regenerate shows up
    here as a violation rather than as a passing tautology."""
    _need_params(state, "W", "H", "T")
    values = _params(state)
    return {
        "op": "check",
        "props": {
            "of": _need_part(state),
            "spec": {
                "bbox": [values["W"], values["H"], values["T"]],
                "valid": True,
                "watertight": True,
            },
        },
    }


def _c_drawing(state: State, workdir: Path) -> dict[str, Any]:
    """A sheet with two views, four dimensions READ BACK from the model, and a
    hole table. This is `create drawing`, so the sheet is in the script; the
    SVG/DXF/PDF files are written by the shell's `render_drawing`, which is a
    render, not a model change."""
    part = _need_part(state)
    return {
        "op": "create",
        "kind": "drawing",
        "name": _free_name(state, "dwg", "sheet"),
        "props": {
            "of": part,
            "sheet": "A3L",
            "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
            "dims": [
                {"name": "d1", "view": "top", "kind": "extent", "axis": "X"},
                {"name": "d2", "view": "top", "kind": "extent", "axis": "Y"},
                {"name": "d3", "view": "front", "kind": "extent", "axis": "Y"},
            ],
            "hole_table": True,
            "title": {"part": part.upper(), "rev": "A", "scale": "1:1"},
        },
    }


def _c_export(state: State, workdir: Path) -> dict[str, Any]:
    """STEP AP242 into the shell's working directory, round-trip verified."""
    part = _need_part(state)
    return {
        "op": "export",
        "props": {
            "format": "step",
            "of": part,
            "out": str(Path(workdir) / f"{part}.step"),
            "schema": "AP242",
            "roundtrip": True,
        },
    }


@dataclass(frozen=True)
class Control:
    """One button.

    `op` is the D5 verb or the kernel method the command carries; `kind` is the
    `create` kind when there is one, DECLARED here so the coverage list is read
    off the table instead of remembered (a test asserts the declaration matches
    what the factory actually emits). `needs_brep` is what the shell checks
    BEFORE applying, so a machine with no OCP wheel gets one honest
    `pk_kernel_absent` instead of a kernel stack.
    """

    label: str
    op: str
    build: Factory
    kind: str = ""
    needs_brep: bool = False


CONTROLS: tuple[Control, ...] = (
    Control("Parameters", "param_set", _c_params),
    Control("New part", "create", _c_part, kind="part"),
    Control("Sketch", "create", _c_sketch, kind="sketch"),
    Control("Extrude", "create", _c_extrude, kind="extrude", needs_brep=True),
    Control("Fillet", "create", _c_fillet, kind="fillet", needs_brep=True),
    Control("Chamfer", "create", _c_chamfer, kind="chamfer", needs_brep=True),
    Control("Hole", "create", _c_hole, kind="hole", needs_brep=True),
    Control("Pattern", "create", _c_pattern, kind="pattern", needs_brep=True),
    Control("Midplane", "create", _c_plane, kind="plane"),
    Control("Mirror", "create", _c_mirror, kind="mirror", needs_brep=True),
    Control("Edit fillet", "set", _c_set, needs_brep=True),
    Control("Set W", "param_set", _c_widen, needs_brep=True),
    Control("Delete last", "delete", _c_delete, needs_brep=True),
    Control("Check spec", "check", _c_check, needs_brep=True),
    Control("Draw sheet", "create", _c_drawing, kind="drawing", needs_brep=True),
    Control("Export STEP", "export", _c_export, needs_brep=True),
)

# -- what this shell does NOT do -----------------------------------------------
#
# Written down rather than implied, and asserted against the kernel's own
# tables in tests/test_gui.py so the list cannot rot: a kind added to the
# kernel and to neither list fails the test that same day.

VERBS_WITHOUT_A_CONTROL: tuple[str, ...] = ()

KINDS_WITHOUT_A_CONTROL: tuple[str, ...] = (
    "angle",
    "axis",
    "ball",
    "coil",
    "combine",
    "component",
    "cylindrical",
    "draft",
    "flush",
    "import",
    "insert",
    "joint",
    "loft",
    "mate",
    "object",
    "planar",
    "point",
    "revolute",
    "revolve",
    "rigid",
    "sheet",
    "shell",
    "slider",
    "split",
    "sweep",
    "tangent",
    "thread",
)

# Kernel methods the shell drives as plumbing rather than as a button: the
# window is built on them, so they are covered even though nothing is labelled
# with their name.
METHODS_THE_SHELL_DRIVES: tuple[str, ...] = (
    "apply",
    "detail",
    "drawing",
    "entities",
    "fingerprint",
    "info",
    "probe",
    "script",
    "shutdown",
    "warm",
)

METHODS_WITHOUT_A_CONTROL: tuple[str, ...] = (
    "bom",
    "discard",
    "flat",
    "import",
    "lint",
    "materials",
    "measure",
    "ping",
    "query",
    "restore",
    "snapshot",
    "standards",
    "verbs",
)


def covered_kinds() -> tuple[str, ...]:
    """The `create` kinds a control builds, read off the table itself."""
    return tuple(sorted({c.kind for c in CONTROLS if c.kind}))


def covered_methods() -> tuple[str, ...]:
    """Every kernel method the shell reaches: the buttons plus the plumbing."""
    from partkiln import document

    document.load_verb_modules()
    buttons = {c.op for c in CONTROLS if c.op not in set(document.VERBS)}
    return tuple(sorted(buttons | set(METHODS_THE_SHELL_DRIVES)))


def coverage() -> dict[str, tuple[int, int]]:
    """(covered, total) for verbs, `create` kinds and kernel methods.

    The number the guide prints, computed from the kernel's live tables so a
    stale figure is impossible.
    """
    from partkiln import document
    from partkiln.client import known_methods

    document.load_verb_modules()
    verbs = set(document.VERBS)
    kinds = set(document.KINDS)
    methods = set(known_methods())
    return {
        "verbs": (len(verbs - set(VERBS_WITHOUT_A_CONTROL)), len(verbs)),
        "kinds": (len(set(covered_kinds())), len(kinds)),
        "methods": (len(set(covered_methods()) & methods), len(methods)),
    }


__all__ = [
    "CONTROLS",
    "KINDS_WITHOUT_A_CONTROL",
    "METHODS_THE_SHELL_DRIVES",
    "METHODS_WITHOUT_A_CONTROL",
    "PARAMS",
    "VERBS_WITHOUT_A_CONTROL",
    "Control",
    "coverage",
    "covered_kinds",
    "covered_methods",
]
