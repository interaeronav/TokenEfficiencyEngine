"""The kernel methods behind the fourteen `pk_*` tools (A66 D9).

`client.py` opens ONE generic door - `call(method, params)` over
`KERNEL_METHODS` - and this module fills it: `probe verbs lint query measure
check standards materials bom export import script drawing flat`, each a
function over the live `Document` that returns plain JSON-able scalars. The
adapter's fourteen `VirtualTool`s are thin wrappers over these names, and the
worker dispatches them through the same table, so a method added here is on
the wire with no adapter and no worker change.

What every method owes the model (the metric is tokens per completed part
task, so each of these is a token rule before it is a taste):

* **Numbers, not geometry.** No coordinate list, no mesh, no B-rep ever
  crosses this boundary; a face is a name and a handful of scalars.
* **A refusal names the reason AND the fix**, with a D8 code - `pk_needs`
  when a required argument is missing, `pk_bad_op` for a closed vocabulary,
  `pk_not_served` for a phase this build does not ship.
* **`lint` never touches OCCT.** It answers schema, units, references and the
  predicted sketch DOF from the pure-Python core alone, which is what makes
  it worth calling before a batch instead of after it.
* **`import` is a command, not a side effect.** It goes through
  `create import` so the file lands in the script and a replay rebuilds it -
  the checkpoint is the script (Law 16).

Importing this module costs no OCP: the builders reach `partkiln.brep`
lazily, exactly as the features do, and `LocalKernel.call` imports it on
first use so `import partkiln` stays clean.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from partkiln import __version__, document
from partkiln._errors import KernelError
from partkiln.client import (
    KERNEL_METHODS,
    LocalKernel,
    known_methods,
    occt_version,
    register_method,
    rss_mb,
)
from partkiln.document import CommandError, Document, register_kind
from partkiln.features.base import Feature, Outcome, boolean, builder, get_part, parse_mode

# What `export` can write, and what each format says about itself on disk -
# the handoff manifest (D4/D1 `handoff.py`). `declares_units` is the honest
# half: STL and OBJ carry no unit at all, so a receiver has to be told.
FORMATS: dict[str, dict[str, Any]] = {
    "step": {"units": "mm", "declares_units": True, "up": "Z", "kind": "brep"},
    "iges": {"units": "mm", "declares_units": True, "up": "Z", "kind": "brep"},
    "brep": {"units": "mm", "declares_units": False, "up": "Z", "kind": "brep"},
    "stl": {"units": "mm", "declares_units": False, "up": "Z", "kind": "mesh"},
    "obj": {"units": "mm", "declares_units": False, "up": "Z", "kind": "mesh"},
    "3mf": {"units": "mm", "declares_units": True, "up": "Z", "kind": "mesh"},
    "glb": {"units": "m", "declares_units": True, "up": "Y", "kind": "mesh"},
    "dxf": {"units": "mm", "declares_units": True, "up": "Z", "kind": "drawing"},
    "svg": {"units": "mm", "declares_units": False, "up": "Z", "kind": "drawing"},
    "pdf": {"units": "mm", "declares_units": False, "up": "Z", "kind": "drawing"},
}
# Where a bundle lands, and what the receiver believes a unit is (A53's table).
TARGETS: dict[str, dict[str, Any]] = {
    "blender": {"units": "m", "up": "Z", "prefer": "glb", "scale_from_mm": 0.001},
    "unreal": {"units": "cm", "up": "Z", "prefer": "glb", "scale_from_mm": 0.1},
    "godot": {"units": "m", "up": "Y", "prefer": "glb", "scale_from_mm": 0.001},
}
READERS = ("step", "stp", "iges", "igs", "brep")
MEASURES = ("mass", "clearance", "interference", "wall", "section", "faces", "asm", "bbox")
_MESH_SUFFIXES = (".stl", ".obj", ".3mf")
_MAX_ROWS = 24  # sub-shape facts per answer; beyond this the count is the answer


def _r3(value: float) -> float:
    return round(float(value), 3) + 0.0


def _need(params: dict[str, Any], key: str, method: str, fix: str) -> Any:
    if params.get(key) in (None, ""):
        raise KernelError(f"{method} needs {key}.", fix=fix, code="pk_needs")
    return params[key]


def _one_of(value: Any, allowed: tuple[str, ...], what: str) -> str:
    text = str(value).strip().lower()
    if text not in allowed:
        raise KernelError(
            f"{what} {value!r} is not one of {', '.join(allowed)}.",
            fix=f"pass {what}: {allowed[0]} (or one of the others).",
            code="pk_bad_op",
        )
    return text


def _doc(kernel: LocalKernel) -> Document:
    return kernel.document


def _part(doc: Document, ref: Any, *, what: str = "this") -> Any:
    """One part by id, by name, or the only one there is."""
    if ref in (None, "", "doc"):
        with_body = [n for n in sorted(doc.parts) if doc.parts[n].shape is not None]
        if len(with_body) == 1:
            return doc.parts[with_body[0]]
        if not with_body:
            raise KernelError(
                "no part has a body yet.",
                fix="build one first (create part -> create sketch -> create extrude).",
                code="pk_ref_empty",
            )
        raise KernelError(
            f"the document has {len(with_body)} bodies ({', '.join(with_body)}).",
            fix=f"say which with of: part:<name> on {what}.",
            code="pk_part_ambiguous",
        )
    name = str(ref)
    name = name[5:] if name.startswith("part:") else name
    part = doc.parts.get(name)
    if part is None:
        known = ", ".join(f"part:{n}" for n in sorted(doc.parts)) or "(none)"
        raise KernelError(f"no part {ref!r}.", fix=f"parts: {known}.", code="pk_ref_unknown")
    return part


def _bodies(doc: Document, ref: Any) -> list[tuple[str, Any]]:
    """(name, shape) for `of`: a part, a list of parts, or every part with a body."""
    if isinstance(ref, list | tuple):
        return [(_part(doc, r).name, _part(doc, r).shape) for r in ref]
    if ref in (None, "", "all", "doc"):
        rows = [
            (n, doc.parts[n].shape) for n in sorted(doc.parts) if doc.parts[n].shape is not None
        ]
        if not rows:
            raise KernelError(
                "no part has a body yet.",
                fix="build one first, or pass path: <file> to measure a file.",
                code="pk_ref_empty",
            )
        return rows
    part = _part(doc, ref)
    if part.shape is None:
        raise KernelError(
            f"part {part.name} has no body yet.",
            fix="build it before measuring or exporting it.",
            code="pk_ref_empty",
        )
    return [(part.name, part.shape)]


def _compound(shapes: list[Any]) -> Any:
    """Several bodies as ONE shape, for a whole-document measure."""
    if len(shapes) == 1:
        return shapes[0]
    from OCP.BRep import BRep_Builder
    from OCP.TopoDS import TopoDS_Compound

    compound = TopoDS_Compound()
    builder_ = BRep_Builder()
    builder_.MakeCompound(compound)
    for shape in shapes:
        builder_.Add(compound, shape)
    return compound


def _assembly(doc: Document, params: dict[str, Any]) -> Any:
    from partkiln.assembly.verbs import assembly_of

    return assembly_of(doc, {"assembly": params.get("assembly")})


def _safe_name(text: str, fallback: str = "imported") -> str:
    name = re.sub(r"[^a-z0-9_]+", "_", str(text).lower()).strip("_")[:24]
    return name or fallback


# --------------------------------------------------------------------------- probe


def _notices() -> list[str]:
    """The licence lines from NOTICE - the prominent notice OCCT's exception asks for.

    Read from the file when the source tree is there (the sidecar installs
    partkiln editable, so it usually is) and from this constant otherwise, so
    `pk_probe` never answers "no licence information" for a shipped wheel.
    """
    lines = [
        "partkiln: MIT.",
        "Open CASCADE Technology (OCCT): LGPL-2.1-only WITH OCCT-exception-1.0, reached "
        "through the Apache-2.0 cadquery-ocp wheel, dynamically linked, never vendored.",
        "Standards data: bd_warehouse (Apache-2.0) and threadlib (BSD-3-Clause); every file "
        "carries source, licence and retrieved in data/manifest.json.",
    ]
    notice = Path(__file__).resolve().parents[2] / "NOTICE"
    if notice.is_file():
        found = [
            line.strip()
            for line in notice.read_text(encoding="utf-8").splitlines()
            if re.search(r"LGPL|Apache|BSD|MIT|exception", line)
        ]
        if found:
            return [line[:200] for line in found[:8]]
    return lines


@register_method("probe")
def m_probe(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Kernel health: OCCT/OCP, mode, warm state, formats, licence notices."""
    from partkiln.brep import INSTALL_LINE, ocp_available

    info = kernel.info()
    ocp = ocp_available()
    out: dict[str, Any] = {
        "alive": True,
        "mode": info["mode"],
        "pid": info["pid"],
        "python": info["python"],
        "partkiln": __version__,
        "ocp": ocp,
        "occt": occt_version(),
        "warm": info["warm"],
        "rss_mb": rss_mb(),
        "document": {
            "name": info["name"],
            "commands": info["commands"],
            "parts": info["parts"],
            "assemblies": info["assemblies"],
            "drawings": info["drawings"],
            "sheets": info["sheets"],
            "fingerprint": info["fingerprint"],
        },
        "formats": {
            "export": sorted(f for f in FORMATS if FORMATS[f]["kind"] != "drawing")
            + sorted(f for f in FORMATS if FORMATS[f]["kind"] == "drawing"),
            "import": sorted(set(READERS)),
            "targets": sorted(TARGETS),
        },
        "methods": list(known_methods()),
        "phases": _phases(),
        "licence": _notices(),
    }
    if not ocp:
        out["fix"] = INSTALL_LINE
        out["note"] = (
            "no OCP in this interpreter: sketches, parameters, the assembly solver and lint "
            "answer; every B-rep answer refuses until partkiln[brep] is installed."
        )
    return out


def _phases() -> dict[str, bool]:
    """Which optional phases this build actually serves (D9's honesty tier)."""
    from importlib.util import find_spec

    def has(module: str) -> bool:
        try:
            return find_spec(module) is not None
        except (ImportError, ValueError):
            return False

    return {
        "parts": True,
        "assemblies": True,
        "drawings": has("partkiln.drawing.views") or has("partkiln.drawing.verbs"),
        "sheetmetal": has("partkiln.sheetmetal.fold") or has("partkiln.sheetmetal.verbs"),
        "pdf": has("fpdf"),
    }


# --------------------------------------------------------------------------- verbs

# One example per kind: what the model copies. Generated entries (a kind with
# no row here) get the shape of the op and nothing else, and say so, because
# an invented example is worse than none.
_EXAMPLES: dict[str, dict[str, Any]] = {
    "part": {
        "op": "create",
        "kind": "part",
        "name": "bracket",
        "props": {"material": "steel_s275"},
    },
    "sketch": {
        "op": "create",
        "kind": "sketch",
        "name": "base",
        "props": {"plane": "XY", "profile": [{"rect": ["W", "H"], "tag": "outer"}]},
    },
    "extrude": {
        "op": "create",
        "kind": "extrude",
        "name": "plate",
        "props": {"sketch": "base", "distance": "T"},
    },
    "revolve": {
        "op": "create",
        "kind": "revolve",
        "name": "shaft",
        "props": {"sketch": "prof", "axis": "X", "angle": 360},
    },
    "sweep": {
        "op": "create",
        "kind": "sweep",
        "name": "tube",
        "props": {"profile": "sect", "path": "spine"},
    },
    "loft": {"op": "create", "kind": "loft", "name": "horn", "props": {"sections": ["a", "b"]}},
    "hole": {
        "op": "create",
        "kind": "hole",
        "name": "h",
        "props": {"on": "plate.end", "at": [[20, 30]], "std": "M6 clearance normal"},
    },
    "fillet": {
        "op": "create",
        "kind": "fillet",
        "name": "f1",
        "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
    },
    "chamfer": {
        "op": "create",
        "kind": "chamfer",
        "name": "c1",
        "props": {"edges": "plate:edges(of=end, loop=outer)", "d": "1mm"},
    },
    "shell": {
        "op": "create",
        "kind": "shell",
        "name": "sh",
        "props": {"faces": "box.end", "t": "2mm"},
    },
    "draft": {
        "op": "create",
        "kind": "draft",
        "name": "dr",
        "props": {"faces": "box:faces(dir=X)", "angle": 3, "neutral": "box.start"},
    },
    "pattern": {
        "op": "create",
        "kind": "pattern",
        "name": "p",
        "props": {"of": "h", "layout": "rect", "dx": 20, "nx": 10, "dy": 20, "ny": 10},
    },
    "mirror": {
        "op": "create",
        "kind": "mirror",
        "name": "m",
        "props": {"of": "upright", "plane": "YZ"},
    },
    "combine": {
        "op": "create",
        "kind": "combine",
        "name": "cb",
        "props": {"bodies": ["a", "b"], "mode": "join"},
    },
    "split": {"op": "create", "kind": "split", "name": "sp", "props": {"body": "a", "plane": "XY"}},
    "plane": {
        "op": "create",
        "kind": "plane",
        "name": "top",
        "props": {"offset": {"from": "XY", "distance": "15mm"}},
    },
    "axis": {"op": "create", "kind": "axis", "name": "spin", "props": {"of": "bore.1.wall"}},
    "point": {"op": "create", "kind": "point", "name": "p0", "props": {"at": [10, 10, 0]}},
    "component": {
        "op": "create",
        "kind": "component",
        "name": "pin",
        "props": {"part": "pin", "at": [0, 0, 0]},
    },
    "mate": {
        "op": "create",
        "kind": "mate",
        "name": "ins",
        "props": {"type": "insert", "a": "block.bore.1.wall", "b": "pin.shaft.side.c"},
    },
    "joint": {
        "op": "create",
        "kind": "joint",
        "name": "j1",
        "props": {
            "type": "revolute",
            "a": "block.bore.1.wall",
            "b": "pin.shaft.side.c",
            "limits": [0, 180],
        },
    },
    "object": {
        "op": "create",
        "kind": "object",
        "name": "brg",
        "props": {"part": "6204", "standard": "ISO 15"},
    },
    "import": {
        "op": "create",
        "kind": "import",
        "name": "base",
        "props": {"path": "in/housing.step", "part": "housing"},
    },
    "drawing": {
        "op": "create",
        "kind": "drawing",
        "name": "sheet1",
        "props": {
            "of": "bracket",
            "sheet": "A4L",
            "views": [{"name": "top", "dir": "top"}],
            "dims": [{"name": "d1", "view": "top", "kind": "extent", "axis": "X"}],
        },
    },
    "sheet": {
        "op": "create",
        "kind": "sheet",
        "name": "brk",
        "props": {"t": 2, "width": 50, "flanges": [{"len": 60}, {"len": 40, "angle": 90, "r": 2}]},
    },
}
_VERB_EXAMPLES: dict[str, dict[str, Any]] = {
    "create": _EXAMPLES["extrude"],
    "set": {"op": "set", "id": "feat:h", "props": {"dia": "12mm"}},
    "delete": {"op": "delete", "id": "feat:h", "props": {"cascade": True}},
    "param_set": {"op": "param_set", "props": {"W": "120mm", "H": "W/2 - 5mm"}},
    "export": {"op": "export", "props": {"format": "step", "out": "out/bracket.step"}},
    "check": {"op": "check", "props": {"spec": {"bbox": [120, 80, 10], "min_wall_mm": 2}}},
}
# The props a kind refuses without (D5's bold column) - `lint`'s table too.
REQUIRED: dict[str, tuple[str, ...]] = {
    "sketch": ("plane",),
    "extrude": ("sketch",),
    "revolve": ("sketch", "axis"),
    "sweep": ("profile", "path"),
    "loft": ("sections",),
    "hole": ("on", "at"),
    "fillet": ("edges",),
    "chamfer": ("edges",),
    "shell": ("faces", "t"),
    "draft": ("faces", "angle"),
    "pattern": ("of",),
    "mirror": ("of", "plane"),
    "combine": ("bodies",),
    "split": ("body",),
    "component": ("part",),
    "mate": ("a", "b"),
    "joint": ("a", "b"),
    "import": ("path",),
    "drawing": ("of",),
    "sheet": ("t", "width", "flanges"),
}
# Which props carry a length and which an angle: `lint` parses them without
# the kernel, which is how a bad unit is caught before OCCT is ever started.
LENGTHS = (
    "distance",
    "r",
    "d",
    "t",
    "dia",
    "depth",
    "dx",
    "dy",
    "offset",
    "len",
    "width",
    "height",
    "thickness",
    "pitch",
)
ANGLES = ("angle", "deg", "taper", "twist")


@register_method("verbs")
def m_verbs(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """The batch vocabulary: every verb and every create kind, with an example."""
    document.load_verb_modules()
    kinds: dict[str, Any] = {}
    for kind in document.KINDS:
        row: dict[str, Any] = {"required": list(REQUIRED.get(kind, ()))}
        example = _EXAMPLES.get(kind)
        if example is None:
            row["example"] = {"op": "create", "kind": kind, "name": f"{kind}1", "props": {}}
            row["documented"] = False
        else:
            row["example"] = example
        kinds[kind] = row
    verbs = {
        verb: {"example": _VERB_EXAMPLES.get(verb, {"op": verb, "props": {}})}
        for verb in document.VERBS
    }
    for verb in ("export", "check"):  # methods, but they ride in a batch (D5)
        verbs.setdefault(verb, {"example": _VERB_EXAMPLES[verb], "method": True})
    return {
        "verbs": verbs,
        "kinds": kinds,
        "methods": list(known_methods()),
        "units": {"length": "mm", "angle": "deg", "note": "a bare number is mm/deg (Law 12)"},
        "notes": [
            "the wire folds `kind` beside `op`, so a mate or joint kind is `type` "
            "(or its own create kind: create insert / create revolute)",
            "a param name or an expression is legal wherever a length is: 'W/2 - 5mm'",
        ],
    }


# --------------------------------------------------------------------------- lint


@register_method("lint")
def m_lint(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Pre-flight a batch WITHOUT the kernel: schema, units, refs, sketch DOF.

    Never imports OCP and never mutates the document (a spy in the test suite
    asserts it): every answer comes from the closed verb table, the unit
    parser, the name tables the document already holds, and - for a sketch -
    the P1 solver, which is scipy and pure Python. That is what makes it
    worth a call before a batch rather than a refusal after one.
    """
    document.load_verb_modules()
    doc = _doc(kernel)
    batch = params.get("commands", params.get("batch", params.get("ops")))
    if not isinstance(batch, list):
        raise KernelError(
            "lint needs commands: the batch you are about to send.",
            fix='pass {"commands": [{"op": "create", "kind": "part", ...}, ...]}.',
            code="pk_needs",
        )
    issues: list[dict[str, Any]] = []
    needs: list[str] = []
    sketches: list[dict[str, Any]] = []
    known_names = _known_names(doc)
    # A batch is usually self-contained - it defines its parameters, draws its
    # sketch and extrudes it in one go - so lint walks it IN ORDER against a
    # scratch document: what command 0 defines, command 3 may use. Anything
    # else would call every good first batch broken.
    scratch = _scratch(doc)
    for index, raw in enumerate(batch):
        _lint_one(scratch, index, raw, known_names, issues, needs, sketches)
    return {
        "ok": not issues,
        "commands": len(batch),
        "issues": issues,
        "needs": needs[:3],
        "sketches": sketches,
        "kernel_called": False,
        "names_known": len(known_names),
    }


def _scratch(doc: Document) -> Document:
    """A copy of the document's UNIT and PARAMETER state, and nothing else.

    Parameters are the only thing lint has to carry forward as it walks (an
    expression in command 5 may name what command 0 set); geometry it cannot
    build without the kernel anyway, so the names are tracked as strings.
    """
    import copy

    probe = Document(
        name=doc.name,
        units=doc.units,
        angle_unit=doc.angle_unit,
        standard=doc.standard,
        strict_units=doc.strict_units,
    )
    probe.params = copy.deepcopy(doc.params)
    return probe


def _known_names(doc: Document) -> set[str]:
    """Every name a reference could legally use TODAY, without touching OCCT."""
    names: set[str] = {f"sk:{n}" for n in doc.sketches} | set(doc.sketches)
    names |= {f"part:{n}" for n in doc.parts} | set(doc.parts)
    names |= {f"{d.kind}:{n}" for n, d in doc.datums.items()}
    names |= {"XY", "XZ", "YZ", "X", "Y", "Z"}
    for part in doc.parts.values():
        names |= {f"feat:{f.id}" for f in part.features}
        names |= {f.id for f in part.features}
        names |= set(part.names.names())
    for record in doc.assemblies.values():
        names |= set(record.asm.components)
        names |= {c.name for c in record.asm.constraints()}
    return names


def _lint_one(
    doc: Document,
    index: int,
    raw: Any,
    known: set[str],
    issues: list[dict[str, Any]],
    needs: list[str],
    sketches: list[dict[str, Any]],
) -> None:
    def flag(code: str, message: str, fix: str) -> None:
        issues.append({"index": index, "code": code, "message": message, "fix": fix})

    if not isinstance(raw, dict) or "op" not in raw:
        flag("pk_bad_op", f"batch[{index}] has no op.", "every command names a verb.")
        return
    op = str(raw["op"])
    props = dict(raw.get("props") or {})
    args = {k: v for k, v in raw.items() if k not in ("op", "props", "args")}
    args.update(props)
    if op not in document.VERBS and op not in ("export", "check"):
        flag(
            "pk_bad_op",
            f"batch[{index}]: unknown op {op!r}.",
            f"partkiln accepts: {', '.join([*document.VERBS, 'export', 'check'])}.",
        )
        return
    if op == "param_set":
        # Apply it to the scratch document so a later command may use it.
        inner = args.get("params")
        assignments = (
            dict(inner)
            if isinstance(inner, dict)
            else {k: v for k, v in args.items() if k not in ("kind", "name", "id")}
        )
        try:
            doc.params.set_many(assignments)
        except CommandError as exc:
            flag(
                getattr(exc, "code", "pk_bad_expr"),
                f"batch[{index}]: param_set would refuse: {exc}",
                "define the names it depends on first, in an earlier command.",
            )
        known |= set(assignments)
        return
    if op == "create":
        kind = str(args.get("kind") or "")
        if kind not in document.KINDS:
            flag(
                "pk_bad_op",
                f"batch[{index}]: unknown create kind {kind!r}.",
                f"kinds: {', '.join(document.KINDS)}.",
            )
            return
        # What this command will make is a name later commands may use: the
        # feature and part names, and the face names they will materialise
        # (`plate.end` resolves through its `plate` root).
        made = str(args.get("name") or f"{kind}{index}")
        known |= {made, f"{kind}:{made}", f"feat:{made}", f"part:{made}", f"sk:{made}"}
        missing = [p for p in REQUIRED.get(kind, ()) if args.get(p) in (None, "")]
        if missing:
            fix = f"{kind} needs {', '.join(missing)}; example: "
            fix += json.dumps(_EXAMPLES.get(kind, {"op": "create", "kind": kind}))
            flag("pk_needs", f"batch[{index}]: {kind} is missing {', '.join(missing)}.", fix)
            needs.append(f"{index}: {kind} needs {', '.join(missing)}")
        name = args.get("name")
        if name is not None and not re.match(r"^[a-z0-9_]{1,24}$", str(name)):
            flag(
                "pk_needs",
                f"batch[{index}]: name {name!r} is not allowed.",
                "1-24 characters from a-z 0-9 _ .",
            )
        if kind == "sketch":
            _lint_sketch(doc, index, args, flag, sketches)
    if op in ("export", "check"):
        _lint_method_op(index, op, args, flag, needs)
    _lint_units(doc, index, args, flag)
    _lint_refs(doc, index, op, args, known, flag)


def _lint_units(doc: Document, index: int, args: dict[str, Any], flag: Any) -> None:
    from partkiln import units

    for key, value in args.items():
        base = key.lower()
        kind = "length" if base in LENGTHS else ("angle" if base in ANGLES else None)
        if kind is None or not isinstance(value, str):
            continue
        if units.is_literal(value):
            try:
                if kind == "length":
                    units.parse_length(value)
                else:
                    units.parse_angle(value)
            except CommandError as exc:
                flag("pk_unit_unknown", f"batch[{index}]: {key}={value!r}. {exc}", str(exc))
            continue
        try:
            evaluated = doc.params.evaluate(value)
        except CommandError as exc:
            flag(
                "pk_bad_expr",
                f"batch[{index}]: {key}={value!r} does not evaluate. {exc}",
                f"define the parameter first (param_set) - known: "
                f"{', '.join(doc.params.names()) or '(none)'}.",
            )
            continue
        from partkiln import params as params_mod

        wrong = params_mod.ANGLE if kind == "length" else params_mod.LENGTH
        if evaluated.kind == wrong:
            flag(
                "pk_unit_kind",
                f"batch[{index}]: {key}={value!r} is an {evaluated.kind}, not a {kind}.",
                f"give {key} a {kind}.",
            )


def _lint_refs(
    doc: Document, index: int, op: str, args: dict[str, Any], known: set[str], flag: Any
) -> None:
    from partkiln.naming import is_selector

    fields = ("sketch", "of", "on", "edges", "faces", "part", "body", "a", "b", "profile", "path")
    for field in fields:
        value = args.get(field)
        refs = value if isinstance(value, list | tuple) else [value]
        for ref in refs:
            if not isinstance(ref, str) or not ref:
                continue
            if is_selector(ref):
                scope = ref.split(":", 1)[0].strip()
                if scope and scope.split(".")[0] not in known:
                    flag(
                        "pk_ref_unknown",
                        f"batch[{index}]: {field}={ref!r} selects on {scope!r}, which is not a "
                        "part or a feature here.",
                        f"known: {', '.join(sorted(known)[:12])}.",
                    )
                continue
            if ref in known:
                continue
            root = ref.split(".", 1)[0].split("[", 1)[0]
            if root in known or ref.startswith(("plane:", "axis:", "point:", "on:")):
                continue
            if op == "create" and args.get("name") == ref:
                continue
            flag(
                "pk_ref_stale" if root else "pk_ref_unknown",
                f"batch[{index}]: {field}={ref!r} resolves to nothing in this document.",
                "a reference is a name from tee_scene_summary, or a selector "
                "(<part>:faces(...)). Earlier commands in this batch are not counted.",
            )


def _lint_method_op(index: int, op: str, args: dict[str, Any], flag: Any, needs: list[str]) -> None:
    if op == "export":
        fmt = str(args.get("format") or "").lower()
        if not fmt:
            flag("pk_needs", f"batch[{index}]: export needs format.", f"one of {sorted(FORMATS)}.")
            needs.append(f"{index}: export needs format ({', '.join(sorted(FORMATS))})")
        elif fmt not in FORMATS:
            flag(
                "pk_bad_op",
                f"batch[{index}]: format {fmt!r} is not written by partkiln.",
                f"formats: {', '.join(sorted(FORMATS))}.",
            )
        if not args.get("out"):
            flag("pk_needs", f"batch[{index}]: export needs out.", "out: <path to write>.")
            needs.append(f"{index}: export needs out")
    elif not isinstance(args.get("spec"), dict):
        flag(
            "pk_needs",
            f"batch[{index}]: check needs spec.",
            'spec: {"bbox": [120, 80, 10], "min_wall_mm": 2} - '
            "rules: bbox, volume_mm3, mass_g, holes, min_wall_mm, valid, watertight, "
            "faces, edges.",
        )


def _lint_sketch(
    doc: Document, index: int, args: dict[str, Any], flag: Any, sketches: list[dict[str, Any]]
) -> None:
    """Predicted DOF from the P1 solver - the sketch is built, never stored."""
    from partkiln.sketch import presets
    from partkiln.sketch.model import Sketch

    name = str(args.get("name") or f"sketch{index}")
    try:
        sketch = Sketch(name, str(args.get("plane") or "XY"))
        for spec in args.get("profile") or []:
            if not isinstance(spec, dict):
                continue
            expansion = presets.expand(
                spec,
                length=lambda v: doc.length(v, {}),
                angle=lambda v: doc.angle(v, {}),
                existing=sketch.tags(),
            )
            for entity in expansion.entities:
                sketch.add(entity)
            for kind, refs, tag in expansion.constraints:
                sketch.constrain(kind, *refs, tag=tag)
            for d_kind, refs, value, tag, axis, expr in expansion.dims:
                sketch.dimension(d_kind, *refs, value=value, tag=tag, axis=axis, expr=expr)
        if not sketch.entities:
            return
        solution = sketch.solve()
    except CommandError as exc:
        flag(
            getattr(exc, "code", "pk_op_failed"),
            f"batch[{index}]: sketch {name} would refuse: {exc}",
            "fix the profile before sending the batch.",
        )
        return
    row = {
        "index": index,
        "name": name,
        "dof": solution.dof,
        "status": solution.status,
        "closed": sketch.closed(),
        "entities": len(sketch.entities),
    }
    sketches.append(row)
    if solution.status == "conflict":
        flag(
            "pk_sketch_overconstrained",
            f"batch[{index}]: sketch {name} does not solve ({'; '.join(solution.conflicts)}).",
            "drop or relax one of the named dimensions, or make one driven.",
        )


# --------------------------------------------------------------------------- query


@register_method("query")
def m_query(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Resolve a selector to names, print the feature tree, or diff a fingerprint."""
    doc = _doc(kernel)
    asked = params.get("sel") or params.get("selector") or params.get("ref")
    what = str(params.get("what") or ("names" if asked else "tree"))
    if what == "changes" or params.get("since") is not None:
        return _query_changes(doc, params)
    if what == "tree":
        return {"what": "tree", "lines": _tree_lines(doc), "fingerprint": doc.fingerprint()}
    if what not in ("names", "faces", "edges"):
        raise KernelError(
            f"what {what!r} is not one of names, tree, changes.",
            fix="what: names resolves a selector; tree prints the feature tree; changes "
            "diffs a fingerprint.",
            code="pk_bad_op",
        )
    ref = params.get("sel") or params.get("selector") or params.get("ref")
    if not ref:
        raise KernelError(
            "query needs sel: what to resolve.",
            fix='sel: a name ("plate.end") or a selector ("plate:edges(dir=Z)"); '
            "what: tree prints the feature tree instead.",
            code="pk_needs",
        )
    from partkiln import naming
    from partkiln.naming import is_selector, resolve

    part = _part(doc, params.get("of") or params.get("part"), what="query")
    kind = "edge" if (what == "edges" or ":edges(" in str(ref) or "|" in str(ref)) else "face"
    # Law 12 at the verb boundary, as `features/__init__.py` does it: a bare
    # number in a filter (`len>3`) is the DOCUMENT's unit, and `resolve` is
    # reached here with a part that does not know the document.
    with naming.document_unit(doc.units):
        resolved = resolve(part, str(ref), kind, "many")
    facts = [
        _subshape_facts(name, info, kind)
        for name, info in zip(resolved.names, resolved.infos, strict=False)
    ]
    out: dict[str, Any] = {
        "what": what,
        "ref": str(ref),
        "part": f"part:{part.name}",
        "kind": kind,
        "count": resolved.count,
        "how": resolved.how,
        "names": list(resolved.names)[:_MAX_ROWS],
        "selector": is_selector(str(ref)),
    }
    if resolved.seam_excluded:
        out["seam_excluded"] = resolved.seam_excluded
    if len(facts) <= _MAX_ROWS:
        out["facts"] = facts
    return out


def _subshape_facts(name: str, info: Any, kind: str) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name}
    if kind == "face":
        row.update(
            {
                "type": info.surface_type,
                "area_mm2": _r3(info.area),
                "centroid_mm": [_r3(c) for c in info.centroid],
            }
        )
        if info.normal is not None:
            row["normal"] = [round(c, 3) + 0.0 for c in info.normal]
    else:
        row.update(
            {
                "type": info.curve_type,
                "length_mm": _r3(info.length),
                "convexity": info.convexity,
                "seam": info.is_seam,
            }
        )
    if getattr(info, "radius", None) is not None:
        row["radius_mm"] = _r3(info.radius)
    return row


def _tree_lines(doc: Document) -> list[str]:
    """The feature tree as text - the cheapest full read of a document."""
    lines = [
        f"doc {doc.name}: {len(doc.params)} params, {len(doc.sketches)} sketches, "
        f"{len(doc.parts)} parts, {len(doc.assemblies)} assemblies, "
        f"{len(doc.history)} commands, fingerprint {doc.fingerprint()}"
    ]
    for name in sorted(doc.params.names()):
        param = doc.params.get(name)
        lines.append(f"  param:{name} = {param.value:g} ({param.expr})")
    for name in sorted(doc.sketches):
        sketch = doc.sketches[name]
        report = sketch.report()
        lines.append(
            f"  sk:{name} on {sketch.plane}: {report['entities']} entities, dof {report['dof']} "
            f"({report['status']})"
        )
    for name in sorted(doc.parts):
        part = doc.parts[name]
        summary = part.summary()
        lines.append(
            f"  part:{name} {summary['volume_mm3']} mm3, {summary.get('faces', 0)} faces, "
            f"{summary.get('edges', 0)} edges, material {part.material or 'none'}"
        )
        for feature in part.features:
            mark = "-" if feature.suppressed else ("!" if feature.status == "failed" else " ")
            lines.append(
                f"   {mark} feat:{feature.id} {feature.kind} {feature.status} "
                f"{_r3(feature.delta_mm3):+g} mm3, {feature.faces} faces"
            )
    for name in sorted(doc.assemblies):
        record = doc.assemblies[name]
        summary = record.summary()
        lines.append(
            f"  asm {name}: {summary['components']} components, {summary['constraints']} "
            f"constraints, dof {summary['dof']} ({summary['status']})"
        )
        for row in record.entity_rows()[1:]:
            lines.append(f"    {row['id']} {row.get('type', row.get('part', ''))}")
    return lines


def _query_changes(doc: Document, params: dict[str, Any]) -> dict[str, Any]:
    """What moved since a fingerprint.

    A fingerprint is an identity, not a log, so the honest answer to a bare
    string is "the same or not". Hand back the object this method returned
    last time and it can do better: the per-part fingerprints name WHICH part
    changed, which is the question behind the question.
    """
    since = params.get("since")
    now = doc.fingerprint()
    parts = {name: doc.parts[name].fingerprint() for name in sorted(doc.parts)}
    out: dict[str, Any] = {
        "what": "changes",
        "now": now,
        "parts": parts,
        "commands": len(doc.history),
    }
    if isinstance(since, dict):
        before = {str(k): str(v) for k, v in (since.get("parts") or {}).items()}
        out["since"] = since.get("now") or since.get("fingerprint")
        out["changed"] = sorted(
            f"part:{n}" for n in set(before) | set(parts) if before.get(n) != parts.get(n)
        )
        out["equal"] = out["since"] == now
    elif since is not None:
        out["since"] = str(since)
        out["equal"] = str(since) == now
        out["hint"] = (
            "pass the whole answer back as `since` next time and this names the parts that "
            "changed, not just whether anything did."
        )
    return out


# --------------------------------------------------------------------------- measure


@register_method("measure")
def m_measure(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Numbers, not pixels: mass, clearance, interference, wall, section, faces, asm."""
    doc = _doc(kernel)
    what = _one_of(params.get("what") or "mass", MEASURES, "what")
    if what == "asm":
        record = _assembly(doc, params)
        return {"what": "asm", **record.details()}
    if what == "interference":
        return _measure_interference(doc, params)
    if what == "clearance":
        return _measure_clearance(doc, params)
    path = params.get("path")
    if path:
        name, shape, source = _read_shape(str(path))
        bodies = [(name, shape)]
    else:
        source = "document"
        bodies = _bodies(doc, params.get("of") or params.get("part"))
    if what == "mass":
        return _measure_mass(doc, params, bodies, source)
    if what == "bbox":
        from partkiln.brep import shapes as shapes_mod

        shape = _compound([s for _n, s in bodies])
        box = shapes_mod.bbox(shape)
        return {
            "what": "bbox",
            "source": source,
            "of": [n for n, _s in bodies],
            "bbox_mm": [_r3(box[3] - box[0]), _r3(box[4] - box[1]), _r3(box[5] - box[2])],
            "bbox_min": [_r3(c) for c in box[:3]],
            "bbox_max": [_r3(c) for c in box[3:]],
        }
    if what == "wall":
        from partkiln.checks.wall import check_wall, min_wall

        shape = _compound([s for _n, s in bodies])
        samples = int(params.get("samples", 5))
        limit = params.get("limit_mm", params.get("limit"))
        if limit is None:
            return {"what": "wall", "source": source, **min_wall(shape, samples_per_face=samples)}
        return {
            "what": "wall",
            "source": source,
            **check_wall(shape, float(limit), samples_per_face=samples),
        }
    if what == "section":
        from partkiln.checks.section import section_area

        shape = _compound([s for _n, s in bodies])
        point, normal = _section_plane(doc, params)
        return {"what": "section", "source": source, **section_area(shape, point, normal)}
    return _measure_faces(bodies, source)


def _measure_mass(
    doc: Document, params: dict[str, Any], bodies: list[tuple[str, Any]], source: str
) -> dict[str, Any]:
    from partkiln.checks.mass import mass_properties

    material = params.get("material")
    if material is None and source == "document" and len(bodies) == 1:
        part = doc.parts.get(bodies[0][0])
        material = getattr(part, "material", None)
    density = params.get("density_kg_m3")
    shape = _compound([s for _n, s in bodies])
    out = mass_properties(shape, material, None if density is None else float(density))
    return {"what": "mass", "source": source, "of": [n for n, _s in bodies], **out}


def _measure_faces(bodies: list[tuple[str, Any]], source: str) -> dict[str, Any]:
    """The face inventory: counts by surface type and the cylinders by diameter.

    Counts are UNIQUE sub-shapes (Law 20) - the explorer double-counts every
    shared edge (F5: 624 visits, 312 edges).
    """
    from partkiln.brep import query
    from partkiln.brep import shapes as shapes_mod

    rows: list[dict[str, Any]] = []
    for name, shape in bodies:
        counts = shapes_mod.counts(shape)
        faces = query.faces(shape)
        by_type: dict[str, int] = {}
        holes: dict[float, int] = {}
        for info in faces:
            by_type[info.surface_type] = by_type.get(info.surface_type, 0) + 1
            if info.surface_type == "cylinder" and info.radius:
                key = round(info.radius * 2, 3)
                holes[key] = holes.get(key, 0) + 1
        rows.append(
            {
                "of": name,
                "faces": counts["faces"],
                "edges": counts["edges"],
                "solids": counts["solids"],
                "by_type": by_type,
                "cylinders": [{"dia_mm": d, "faces": n} for d, n in sorted(holes.items())],
                "valid": shapes_mod.is_valid(shape),
            }
        )
    return {"what": "faces", "source": source, "bodies": rows}


def _section_plane(doc: Document, params: dict[str, Any]) -> tuple[list[float], list[float]]:
    """`at: "x=50"` | `{point, normal}` | `plane: XY|plane:<datum>`."""
    at = params.get("at")
    if isinstance(at, str) and "=" in at:
        axis, _, value = at.partition("=")
        axis = axis.strip().upper()
        if axis not in ("X", "Y", "Z"):
            raise KernelError(
                f"section at {at!r} names no axis.", fix="at: 'x=50'.", code="pk_needs"
            )
        index = "XYZ".index(axis)
        point = [0.0, 0.0, 0.0]
        point[index] = doc.length(value.strip(), {})
        normal = [0.0, 0.0, 0.0]
        normal[index] = 1.0
        return point, normal
    point = params.get("point")
    normal = params.get("normal")
    if isinstance(point, list | tuple) and isinstance(normal, list | tuple):
        return [float(c) for c in point], [float(c) for c in normal]
    plane = params.get("plane")
    if plane:
        from partkiln.features.workplane import plane_of

        origin, direction = plane_of(doc, str(plane))
        return list(origin), list(direction)
    raise KernelError(
        "a section needs a plane.",
        fix="at: 'x=50', or plane: 'XY' | 'plane:<datum>', or point + normal.",
        code="pk_needs",
    )


def _measure_interference(doc: Document, params: dict[str, Any]) -> dict[str, Any]:
    from partkiln.assembly.interference import report as contact_report

    of = params.get("of")
    if of in (None, "", "asm"):
        record = _assembly(doc, params)
        bodies = [
            (c.name, c.shape_ref() if callable(c.shape_ref) else c.shape_ref, c.pose)
            for c in record.asm.components.values()
            if not c.virtual
        ]
        missing = [n for n, s, _p in bodies if s is None]
        if missing:
            raise KernelError(
                f"{', '.join(missing)} has no body yet.",
                fix="build every part before measuring interference.",
                code="pk_ref_empty",
            )
        rows = contact_report(bodies, near_mm=float(params.get("near_mm", 10.0)))
        return {"what": "interference", "source": "asm", "components": len(bodies), **rows}
    bodies2 = _bodies(doc, of)
    rows = contact_report([(n, s) for n, s in bodies2], near_mm=float(params.get("near_mm", 10.0)))
    return {"what": "interference", "source": "parts", "bodies": [n for n, _s in bodies2], **rows}


def _measure_clearance(doc: Document, params: dict[str, Any]) -> dict[str, Any]:
    from partkiln.assembly.interference import clearance

    a_ref = _need(params, "a", "measure clearance", "a: part:<name> or cmp:<name>.")
    b_ref = _need(params, "b", "measure clearance", "b: part:<name> or cmp:<name>.")
    a_name, a_shape, a_pose = _placed(doc, params, a_ref)
    b_name, b_shape, b_pose = _placed(doc, params, b_ref)
    out = clearance(a_shape, b_shape, a_pose, b_pose)
    return {"what": "clearance", "a": a_name, "b": b_name, **out}


def _placed(doc: Document, params: dict[str, Any], ref: Any) -> tuple[str, Any, Any]:
    """A body and where it stands: a component (with its pose) or a bare part."""
    text = str(ref)
    if text.startswith("cmp:") or (doc.assemblies and not text.startswith("part:")):
        for record in doc.assemblies.values():
            name = text[4:] if text.startswith("cmp:") else text
            component = record.asm.components.get(name)
            if component is not None:
                shape = (
                    component.shape_ref() if callable(component.shape_ref) else component.shape_ref
                )
                if shape is None:
                    raise KernelError(
                        f"component {name} has no body yet.",
                        fix="build its part first.",
                        code="pk_ref_empty",
                    )
                return name, shape, component.pose
    part = _part(doc, text, what="clearance")
    if part.shape is None:
        raise KernelError(
            f"part {part.name} has no body yet.", fix="build it first.", code="pk_ref_empty"
        )
    return part.name, part.shape, None


# --------------------------------------------------------------------------- check


@register_method("check")
def m_check(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Verify a spec over a part or the whole assembly: verdict + violations with the fix."""
    doc = _doc(kernel)
    spec = params.get("spec")
    if not isinstance(spec, dict):
        raise KernelError(
            "check needs spec: a dict of rules.",
            fix='spec: {"bbox": [120, 80, 10], "holes": [{"dia": 6.6, "count": 4}], '
            '"min_wall_mm": 2} - rules: bbox, volume_mm3, mass_g, holes, min_wall_mm, valid, '
            "watertight, faces, edges.",
            code="pk_needs",
        )
    from partkiln.checks.spec import check_spec

    of = params.get("of") or params.get("part")
    material = params.get("material")
    if str(of or "").startswith("asm") or of == "assembly":
        record = _assembly(doc, params)
        from partkiln.assembly.interference import placed

        shapes = [
            placed(c.shape_ref() if callable(c.shape_ref) else c.shape_ref, c.pose)
            for c in record.asm.components.values()
            if not c.virtual and (c.shape_ref is not None)
        ]
        target: Any = shapes
        subject = "asm"
    else:
        bodies = _bodies(doc, of)
        target = [s for _n, s in bodies]
        subject = ", ".join(f"part:{n}" for n, _s in bodies)
        if material is None and len(bodies) == 1:
            material = getattr(doc.parts.get(bodies[0][0]), "material", None)
    # `units=doc`: a bare length in the spec is the DOCUMENT's unit (Law 12),
    # and under `strict_units` the document refuses it - the API had this from
    # the start, the verb was reading every bare number as millimetres.
    out = check_spec(target, spec, material, units=doc)
    out["of"] = subject
    if str(of or "").startswith("asm") or of == "assembly":
        record = _assembly(doc, params)
        details = record.details()
        out["asm"] = {
            "dof": details["dof"],
            "status": details["status"],
            "interference": len(details.get("interference") or ()),
        }
        if params.get("no_interference") and details.get("interference"):
            out["verdict"] = "fail"
            out.setdefault("violations", []).append(
                {
                    "rule": "no_interference",
                    "got": len(details["interference"]),
                    "limit": 0,
                    "fix": "move or resize "
                    + ", ".join(f"{r['a']}/{r['b']}" for r in details["interference"]),
                }
            )
    if params.get("strict") and out["verdict"] == "fail":
        lines = "; ".join(
            f"{v['rule']}: got {v.get('got')} vs {v.get('limit')}" for v in out["violations"]
        )
        raise KernelError(
            f"check failed on {subject}: {lines}.",
            fix=" ".join(str(v.get("fix", "")) for v in out["violations"])[:400],
            code="pk_spec_conflict",
        )
    return out


# --------------------------------------------------------------------------- standards / materials


@register_method("standards")
def m_standards(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Clearance, tap, drill, pitch and fastener tables - each with source and licence."""
    from partkiln import standards

    what = str(params.get("what") or ("fastener" if params.get("standard") else "clearance"))
    what = _one_of(what, ("clearance", "tap", "drill", "pitch", "fastener", "list"), "what")
    if what == "list":
        return {
            "what": "list",
            "standards": standards.supported_standards(),
            "series": ["close", "normal", "loose"],
            "note": "sizes are metric designations: M6, M6x0.75.",
        }
    if what == "drill":
        name = _need(params, "name", "standards drill", "name: a drill designation, e.g. '#7'.")
        return {"what": what, **standards.drill_size(str(name))}
    size = _need(params, "size", f"standards {what}", "size: a bolt designation, e.g. 'M6'.")
    if what == "clearance":
        return {
            "what": what,
            **standards.clearance_hole(size, str(params.get("series") or "normal")),
        }
    if what == "tap":
        return {"what": what, **standards.tap_drill(size)}
    if what == "pitch":
        return {"what": what, **standards.pitch(size)}
    standard = _need(
        params,
        "standard",
        "standards fastener",
        f"standard: one of {', '.join(standards.supported_standards())}.",
    )
    return {"what": what, **standards.fastener(str(standard), size)}


@register_method("materials")
def m_materials(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Material cards with an honesty tier per value. A pure lookup - assignment
    is `set part:<n> material=` in a batch, which is why nothing here mutates."""
    from partkiln import materials

    name = params.get("name") or params.get("material")
    if name:
        return {"what": "card", **materials.describe(str(name))}
    cards = materials.cards()
    return {
        "what": "list",
        "count": len(cards),
        "materials": [
            {
                "name": card["name"],
                "designation": card.get("designation", ""),
                "family": card.get("family", ""),
                "density_kg_m3": card["properties"]["density"]["value"],
                "honesty": card["properties"]["density"]["honesty"],
            }
            for card in cards
        ],
        "note": "pass name: <key> for the full card with sources.",
    }


# --------------------------------------------------------------------------- bom


@register_method("bom")
def m_bom(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Bill of materials: qty, material, mass and standard designation per row."""
    doc = _doc(kernel)
    from partkiln.assembly.bom import bom
    from partkiln.assembly.verbs import part_cards

    record = _assembly(doc, params)
    view = _one_of(params.get("view") or "parts", ("parts", "structured"), "view")
    cards = part_cards(doc, record)
    for name, card in cards.items():
        extra = (params.get("cards") or {}).get(name)
        if isinstance(extra, dict):
            card.update(extra)
    out = bom(record.asm, cards, view)
    out["assembly"] = record.name
    out["note"] = (
        "masses are rounded per row before they are multiplied, so the rows add up to the "
        "total exactly."
    )
    return out


# --------------------------------------------------------------------------- export


@register_method("export")
def m_export(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Write a file and say what it declares about itself (the handoff manifest)."""
    doc = _doc(kernel)
    fmt = str(
        _need(params, "format", "export", f"format: one of {', '.join(sorted(FORMATS))}.")
    ).lower()
    if fmt in ("stp", "iges_", "gltf"):
        fmt = {"stp": "step", "gltf": "glb"}.get(fmt, fmt)
    if fmt not in FORMATS:
        raise KernelError(
            f"partkiln does not write {fmt!r}.",
            fix=f"formats: {', '.join(sorted(FORMATS))}. DWG, USDz, Parasolid, SAT, JT and "
            "the native Inventor formats are out of scope (doc 68).",
            code="pk_bad_op",
        )
    out_path = Path(
        str(_need(params, "out", "export", "out: the path to write, e.g. out/bracket.step."))
    )
    target = params.get("target")
    if target is not None:
        target = _one_of(target, tuple(TARGETS), "target")
    if FORMATS[fmt]["kind"] == "drawing":
        return _export_drawing(kernel, fmt, out_path, params)
    bodies = _bodies(doc, params.get("of") or params.get("part"))
    result = _write_bodies(fmt, bodies, out_path, params)
    result.update(
        {
            "id": f"export:{out_path.name}",
            "format": fmt,
            "of": [n for n, _s in bodies],
            "manifest": _manifest(fmt, target),
        }
    )
    if fmt == "step" and params.get("roundtrip", True):
        from partkiln.exchange.step import roundtrip

        checked = roundtrip(
            _compound([s for _n, s in bodies]), schema=str(params.get("schema") or "AP242")
        )
        result["roundtrip"] = {
            "volume_ok": checked["volume_ok"],
            "faces_ok": checked["faces_ok"],
            "volume_rel": checked["volume_rel"],
            "file_schema": checked["file_schema"],
        }
    return result


def _write_bodies(
    fmt: str, bodies: list[tuple[str, Any]], out: Path, params: dict[str, Any]
) -> dict[str, Any]:
    tol = float(params.get("tol", params.get("deflection_mm", 0.05)))
    if fmt == "step":
        from partkiln.exchange.step import write_step

        return write_step(bodies, out, schema=str(params.get("schema") or "AP242"))
    if fmt == "iges":
        from partkiln.exchange.iges import write_iges

        return write_iges(bodies, out)
    if fmt == "brep":
        from partkiln.exchange.brep_io import write_brep

        return write_brep(_compound([s for _n, s in bodies]), out)
    if fmt == "stl":
        from partkiln.exchange.stl import write_stl

        return write_stl(_compound([s for _n, s in bodies]), out, deflection_mm=tol)
    if fmt == "obj":
        from partkiln.exchange.obj import write_obj

        return write_obj(_compound([s for _n, s in bodies]), out, deflection_mm=tol)
    if fmt == "3mf":
        from partkiln.exchange.threemf import write_3mf

        return write_3mf(bodies, out, deflection_mm=tol)
    from partkiln.exchange.gltf import write_glb

    return write_glb(bodies, out, deflection_mm=tol)


def _manifest(fmt: str, target: str | None) -> dict[str, Any]:
    """What the receiver has to be told, per format (D4) - and per target (A53's table).

    `partkiln.handoff` owns this table when the sheet-metal phase ships it;
    until then these are the same numbers, kept here so an export never
    answers "units: unknown".
    """
    row = dict(FORMATS[fmt])
    row.pop("kind", None)
    manifest: dict[str, Any] = {"format": fmt, "source_units": "mm", "source_up": "Z", **row}
    if target:
        spec = TARGETS[target]
        manifest["target"] = target
        manifest["target_units"] = spec["units"]
        manifest["target_up"] = spec["up"]
        manifest["scale_from_mm"] = spec["scale_from_mm"]
        manifest["transform_needed"] = not (
            fmt == "glb" and spec["units"] == row["units"] and spec["up"] == row["up"]
        )
        if fmt == "glb" and target == "blender":
            manifest["note"] = (
                "GLB needs no transform BECAUSE the writer sets the 0.001 m length unit and "
                "the Z-up input coordinate system."
            )
    try:
        # Optional, and owned by the sheet-metal phase: its table wins when it ships.
        from partkiln import handoff
    except ImportError:
        return manifest
    own = getattr(handoff, "manifest", None)
    if callable(own):
        try:
            extra = own(fmt, target)
        except Exception:  # a phase's own table must never break an export
            return manifest
        if isinstance(extra, dict):
            manifest.update(extra)
    return manifest


def _export_drawing(
    kernel: LocalKernel, fmt: str, out: Path, params: dict[str, Any]
) -> dict[str, Any]:
    """DXF/SVG/PDF come from a drawing or a flat pattern, never from a body.

    Routed through the kernel's own table so the phase that owns the format
    answers when it ships and the `pk_not_served` refusal names it when it
    does not - `export format=dxf` and `pk_drawing` are then one code path.
    """
    of = params.get("of")
    method = "flat" if of and str(of).split(":", 1)[-1] in kernel.document.sheets else "drawing"
    return dict(kernel.call(method, {**params, "of": of, "format": fmt, "out": str(out)}))


# --------------------------------------------------------------------------- import


@builder("import")
def _b_import(doc: Document, part: Any, feature: Feature, assumed: dict[str, Any]) -> Outcome:
    """Read a STEP/IGES/BREP file as this feature's body, faces named by fingerprint.

    An import is a FEATURE, not a side effect: it sits in the part's tree with
    the path it read, so a regen re-reads the file and a replay of the script
    rebuilds the same body (Law 16). D6: an imported face has no history to
    inherit, so its name is `<feature>.face[k]` over the deterministic
    `brep.query` order and its identity is the fingerprint.
    """
    from partkiln.brep import query

    args = feature.args
    path = Path(str(args.get("path") or args.get("file") or ""))
    if not str(path):
        raise CommandError(
            "import needs path: the STEP, IGES or BREP file to read.", code="pk_needs"
        )
    name, shape, _source = _read_shape(str(path), product=args.get("product"))
    mode = parse_mode(args, part, assumed)
    if mode == "new":
        body, history = shape, None
    else:
        body, history = boolean(part.shape, [shape], mode, feature)
    faces = query.faces(body)
    names = [(f"{feature.id}.face[{k}]", f"face[{k}]", info.shape) for k, info in enumerate(faces)]
    from partkiln.brep import shapes as shapes_mod

    counts = shapes_mod.counts(body)
    return Outcome(
        body,
        history,
        names,
        mode=mode,
        extra={
            "path": str(path),
            "source": name,
            "solids": counts["solids"],
            "valid": shapes_mod.is_valid(body),
        },
        notes=[f"imported {path.name}: names are fingerprints, there is no feature history"],
    )


@register_kind("import")
def _k_import(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    """`create import` - the same shape as every other feature kind."""
    from partkiln import naming

    part = get_part(doc, args, assumed)
    props = {k: v for k, v in args.items() if k not in ("kind", "name", "id", "part")}
    fid = doc.new_name(args, "import", {f.id: f for f in part.features})
    feature = Feature(fid, "import", props)
    # The same unit binding every other `create <kind>` gets from
    # `features/__init__.py`: this kind is registered here, so it binds it here.
    with naming.document_unit(doc.units):
        details = part.add_feature(doc, feature, assumed)
    details["part"] = f"part:{part.name}"
    return details


def _read_shape(path: str, product: Any = None) -> tuple[str, Any, str]:
    """(name, shape, source) from a STEP, IGES or BREP file; refuses anything else."""
    src = Path(path)
    if not src.is_file():
        raise KernelError(
            f"no file at {src}.", fix="check the path (it is read, never written).", code="pk_needs"
        )
    suffix = src.suffix.lower().lstrip(".")
    if suffix in ("step", "stp"):
        from partkiln.exchange.step import read_step

        data = read_step(src)
        products = data["products"]
        if not products:
            raise KernelError(
                f"{src.name} holds no product geometry.",
                fix="open it in another reader; partkiln reads free shapes only.",
                code="pk_op_failed",
            )
        chosen = _pick_product(products, product, src.name)
        # The header's FILE_SCHEMA is a paragraph; the answer wants the token.
        schema = next((tag for tag in ("AP242", "AP214", "AP203") if tag in data["schema"]), "step")
        return str(chosen["name"] or src.stem), chosen["shape"], f"step:{schema}"
    if suffix in ("iges", "igs"):
        from partkiln.exchange.iges import read_iges

        data = read_iges(src)
        return src.stem, data["shape"], "iges"
    if suffix == "brep":
        from partkiln.exchange.brep_io import read_brep

        return src.stem, read_brep(src), "brep"
    raise KernelError(
        f"partkiln reads STEP, IGES and BREP; {src.suffix or 'that file'} is none of them.",
        fix="convert it first, or measure a mesh (STL/OBJ/3MF) with pk_measure path=.",
        code="pk_bad_op",
    )


def _pick_product(products: list[dict[str, Any]], wanted: Any, filename: str) -> dict[str, Any]:
    if wanted is None:
        return max(products, key=lambda p: p["volume_mm3"]) if len(products) > 1 else products[0]
    if isinstance(wanted, int) and not isinstance(wanted, bool):
        if 0 <= wanted < len(products):
            return products[wanted]
        raise KernelError(
            f"{filename} has {len(products)} products; there is no index {wanted}.",
            fix=f"product: 0..{len(products) - 1}, or the product name.",
            code="pk_ref_unknown",
        )
    for candidate in products:
        if str(candidate["name"]) == str(wanted):
            return candidate
    raise KernelError(
        f"{filename} has no product {wanted!r}.",
        fix=f"products: {', '.join(str(p['name']) for p in products[:12])}.",
        code="pk_ref_unknown",
    )


@register_method("import")
def m_import(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """Import a file as a part, reporting units, solids and validity.

    Goes through `create part` + `create import` in ONE atomic apply, so the
    import is in the script and a replay rebuilds it from the same file.
    """
    doc = _doc(kernel)
    path = Path(str(_need(params, "path", "import", "path: a STEP, IGES or BREP file to read.")))
    part_name = _safe_name(str(params.get("part") or params.get("name") or path.stem))
    commands: list[dict[str, Any]] = []
    if part_name not in doc.parts:
        props = {"material": params.get("material")} if params.get("material") else {}
        commands.append({"op": "create", "kind": "part", "name": part_name, "props": props})
    feature_props: dict[str, Any] = {"path": str(path), "part": part_name}
    for key in ("product", "mode", "allow_no_effect"):
        if params.get(key) is not None:
            feature_props[key] = params[key]
    commands.append(
        {
            "op": "create",
            "kind": "import",
            "name": _safe_name(str(params.get("feature") or "import"), "import"),
            "props": feature_props,
        }
    )
    outcome = kernel.apply(commands)
    details = outcome["results"][-1]
    part = doc.parts[part_name]
    summary = part.summary()
    unit = "mm"
    unit_source = "kernel"
    if path.suffix.lower() in (".step", ".stp"):
        from partkiln.exchange.step import declared_unit

        unit, unit_source = declared_unit(path)
    return {
        "id": f"part:{part_name}",
        "path": str(path),
        "part": f"part:{part_name}",
        "feature": details.get("id"),
        "units": unit,
        "units_source": unit_source,
        "volume_mm3": summary["volume_mm3"],
        "bbox_mm": summary.get("bbox_mm"),
        "solids": summary.get("solids"),
        "faces": summary.get("faces"),
        "edges": summary.get("edges"),
        "valid": summary.get("valid"),
        "names": summary.get("names"),
        "fingerprint": outcome["fingerprint"],
        "notes": [
            "imported faces are named by fingerprint (import.face[k]); there is no feature "
            "history behind them, so an edit upstream cannot move them."
        ],
    }


# --------------------------------------------------------------------------- script


@register_method("script")
def m_script(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
    """The document as a replayable script: dump, replay (with overrides), compare.

    `replay` builds a SECOND document and reports what it becomes; nothing
    the live document holds changes unless `commit: true` says so, which is
    how a part family is explored without losing the original.
    """
    doc = _doc(kernel)
    what = _one_of(params.get("what") or "dump", ("dump", "replay", "compare"), "what")
    if what == "dump":
        script = doc.script()
        if params.get("out"):
            path = Path(str(params["out"]))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(script, indent=2), encoding="utf-8")
            return {
                "what": "dump",
                "path": str(path),
                "bytes": path.stat().st_size,
                "count": len(script["commands"]),
                "fingerprint": doc.fingerprint(),
            }
        # The dump IS the script (`KernelClient.script()` calls this method with
        # no params through the sidecar), so the script's own keys stay at the
        # top level and the extras go beside them - never over them.
        return {
            **script,
            "what": "dump",
            "count": len(script["commands"]),
            "fingerprint": doc.fingerprint(),
        }
    script = params.get("script") or doc.script()
    if isinstance(script, str):
        script = json.loads(Path(script).read_text(encoding="utf-8"))
    overrides = params.get("overrides")
    if overrides is not None and not isinstance(overrides, dict):
        raise KernelError(
            "overrides is {parameter: value}.",
            fix='overrides: {"t": "8mm"} - every param_set that sets t is rewritten.',
            code="pk_needs",
        )
    before = doc.fingerprint()
    fresh = Document.replay(script, overrides=overrides or None)
    after = fresh.fingerprint()
    parts = {
        name: {
            "volume_mm3": fresh.parts[name].summary()["volume_mm3"],
            "fingerprint": fresh.parts[name].fingerprint(),
        }
        for name in sorted(fresh.parts)
    }
    result: dict[str, Any] = {
        "what": what,
        "commands": len(fresh.history),
        "fingerprint": after,
        "compared_to": before,
        "equal": after == before,
        "parts": parts,
        "overrides": overrides or {},
    }
    if what == "compare":
        result["changed"] = sorted(
            f"part:{name}"
            for name in set(parts) & set(doc.parts)
            if parts[name]["fingerprint"] != doc.parts[name].fingerprint()
        )
        result["added"] = sorted(f"part:{n}" for n in set(parts) - set(doc.parts))
        result["removed"] = sorted(f"part:{n}" for n in set(doc.parts) - set(parts))
        return result
    if params.get("commit"):
        kernel._adopt(fresh)  # the same door `restore()` uses (D3)
        result["committed"] = True
        result["fingerprint"] = kernel.fingerprint()
    else:
        result["committed"] = False
        result["note"] = "the live document is untouched; pass commit: true to adopt this replay."
    return result


# --------------------------------------------------------------------------- drawing / flat


def _phase_method(method: str, module: str, phase: str) -> Any:
    """A stub that hands `method` to its phase module, or refuses naming the phase.

    The drawing and sheet-metal phases register their own kernel method on
    import, which REPLACES this stub in the table; the stub therefore imports
    the module, looks the name up again, and calls whatever answered - so a
    build that ships the phase serves it and a build that does not says which
    phase owns it, rather than raising an ImportError three frames down.
    """

    def handler(kernel: LocalKernel, params: dict[str, Any]) -> dict[str, Any]:
        import importlib

        from partkiln.client import KERNEL_METHODS

        try:
            loaded = importlib.import_module(f"{module}.verbs")
        except ImportError:
            loaded = None
        if loaded is not None:
            current = KERNEL_METHODS.get(method)
            if current is not None and current is not handler:
                return dict(current(kernel, params))
            entry = getattr(loaded, f"{method}_method", None)
            if callable(entry):
                return dict(entry(kernel, params))
        raise KernelError(
            f"partkiln does not serve {method!r} in this build.",
            fix=f"{phase} owns it ({module}); until it ships, pk_measure answers with numbers "
            "and pk_export writes models rather than sheets.",
            code="pk_not_served",
        )

    handler.__name__ = f"m_{method}"
    return handler


# Registered ONLY when the phase has not already registered its own: a stub
# that clobbered the real handler would turn a shipped phase into a refusal,
# and import order (who calls `register_method` last) must not decide that.
for _method, _module, _phase in (
    ("drawing", "partkiln.drawing", "P5a (drawings)"),
    ("flat", "partkiln.sheetmetal", "P5b (sheet metal)"),
):
    if _method not in KERNEL_METHODS:
        register_method(_method)(_phase_method(_method, _module, _phase))


__all__ = [
    "FORMATS",
    "MEASURES",
    "READERS",
    "REQUIRED",
    "TARGETS",
    "m_bom",
    "m_check",
    "m_export",
    "m_import",
    "m_lint",
    "m_materials",
    "m_measure",
    "m_probe",
    "m_query",
    "m_script",
    "m_standards",
    "m_verbs",
]
