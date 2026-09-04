"""The fourteen `pk_*` tools: mechanical CAD capability a batch is the wrong shape for.

A66 P4 / D9. Modelling IS `tee_batch` - sketch, extrude, hole, fillet, mate,
drawing and export are wire ops on the `PartkilnAdapter`, so the whole
Inventor-class loop arrives through the surface TEE already has. What is left
over is everything that is not a scene mutation: health, the vocabulary
itself, a pre-flight, selector and tree reads, measurements, spec checks, the
standards and material tables, the BOM, and the four things that write files
(drawing, export, flat pattern) or read one (import). Those are these fourteen,
and they live behind progressive disclosure like every other long-tail tool,
so the always-loaded surface stays at 17 tools / 2,033 tok.

Three rules hold this file's shape:

* **Nothing here imports partkiln at module level.** Registration is metadata
  only - `TeeApp.__init__` calls `register_partkiln_tools` on every server,
  including the ones with no kernel installed, and paying an OCP import (26 s
  cold, P0a) at boot would violate Law 17 twice over. Every handler imports
  lazily and every refusal names the install line for BOTH routes.
* **Every handler goes through the adapter**, never through `partkiln` in this
  interpreter: the production route is the sidecar venv that survives the
  extension wipe, and only the adapter knows which kernel it holds.
* **`capability` is left `None`** so `trust.capability_for` resolves it from
  the table at registration - all fourteen are tabled individually in
  `kernel/trust.py` (no `pk_` family row: three of them write files and two
  mutate the document, and a prefix default would hand a writer the open read
  tier - the A45 `cad_`/`trade_` lesson).
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

# Shipped strings, so the licence posture is answerable while the kernel is
# still cold (P0b): the audit is a test, but a caller asking `pk_probe` at
# 3 a.m. should not have to run one.
LICENCE_NOTICES = {
    "partkiln": "MIT",
    "occt": (
        "LGPL-2.1-only WITH OCCT-exception-1.0, reached through the Apache-2.0 OCP wheel, "
        "dynamically linked; NOTICE ships with the package"
    ),
    "data": (
        "clearance/tap/drill and ISO fastener tables from bd_warehouse (Apache-2.0) and "
        "threadlib (BSD-3-Clause); each file carries source, licence and retrieved date"
    ),
    "never_in_process": (
        "py-slvs and SolveSpace (GPL-3.0), cadquery (eager casadi, LGPL-3.0+), "
        "FreeCAD Fasteners (GPL-2), BOLTS (GPL-3) - the lane writes its own solvers instead"
    ),
    "optional": "fpdf2 (LGPL-3.0-only) only inside the [pdf] extra, for PDF sheets",
}


def _adapter(app: Any) -> Any:
    """The partkiln adapter attached to this server, or one refusal naming
    how to attach one. Imported lazily - the module pulls in the wire, which
    imports nothing from partkiln, but there is no reason to pay it at boot."""
    from tee.adapters.partkiln.adapter import PartkilnAdapter

    for adapter in (getattr(app, "adapters", None) or {}).values():
        if isinstance(adapter, PartkilnAdapter):
            return adapter
    raise TeeError(
        "pk_not_served",
        "no partkiln adapter is attached to this server.",
        fix="Start with `tee serve --adapter partkiln --project <dir>`; the batch verbs and "
        "every pk_* tool then answer through it.",
    )


def _need(app: Any = None) -> None:
    """Refuse only when partkiln is reachable by NEITHER route (D2).

    An adapter that already holds a live kernel IS a route - that is the case
    in tests and wherever one was injected. Otherwise: importable here (the
    dev venv) or a sidecar interpreter on disk (production). `find_spec` only,
    because importing OCP costs 26 s cold and a refusal must be cheap.
    """
    from importlib.util import find_spec

    from tee.adapters.partkiln.adapter import INSTALL_HINT, PartkilnAdapter
    from tee.adapters.partkiln.wire import SIDECAR_PY

    for adapter in (getattr(app, "adapters", None) or {}).values():
        if isinstance(adapter, PartkilnAdapter) and adapter.probe():
            return
    try:
        importable = find_spec("partkiln") is not None
    except (ImportError, ValueError):
        importable = False
    if importable or SIDECAR_PY.is_file():
        return
    raise TeeError("pk_kernel_absent", INSTALL_HINT, fix=INSTALL_HINT)


def register_partkiln_tools(app: Any) -> None:
    """Register the fourteen `pk_*` virtual tools (the surface stays 17).

    Metadata only: no partkiln import happens here, so a server with no
    kernel boots at the same speed and every tool refuses with the install
    line rather than an ImportError halfway through a call.
    """

    def _call(method: str, args: dict[str, Any] | None) -> Any:
        """`_need()` then the adapter then one kernel round trip - the same
        three steps in every handler, so a missing kernel, an unattached
        adapter and a kernel refusal are three distinct, named answers."""
        _need(app)
        return _adapter(app).call(method, dict(args or {}))

    # -- health, vocabulary, pre-flight ------------------------------------

    def probe(args: dict[str, Any]) -> dict[str, Any]:
        """Answers from the adapter by default: `pk_probe` must never be the
        call that pays the OCP import or spawns a worker. `deep` is the opt-in
        for callers who want the kernel's own answer and will wait for it."""
        _need(app)
        adapter = _adapter(app)
        out = dict(adapter.health())
        out["licence"] = dict(LICENCE_NOTICES)
        out["units"] = "mm / deg on the wire, both directions"
        if args.get("deep"):
            out["kernel"] = adapter.call("probe", {})
        return out

    def verbs(args: dict[str, Any]) -> dict[str, Any]:
        return _call("verbs", args)

    def lint(args: dict[str, Any]) -> dict[str, Any]:
        """The batch is never applied: lint reads it. That is what makes it
        cheap enough to run before every `tee_batch` (D8's needs protocol
        collects at most three questions across the whole batch)."""
        if not isinstance(args.get("batch"), list):
            raise TeeError(
                "pk_bad_request",
                "pk_lint needs batch: the list of ops you are about to send to tee_batch.",
                fix='pk_lint(batch=[{"op": "create", "kind": "extrude", "name": "plate", '
                '"props": {"sketch": "base", "distance": "10mm"}}]).',
            )
        return _call("lint", args)

    # -- reads --------------------------------------------------------------

    def query(args: dict[str, Any]) -> dict[str, Any]:
        return _call("query", args)

    def measure(args: dict[str, Any]) -> dict[str, Any]:
        return _call("measure", args)

    def check(args: dict[str, Any]) -> dict[str, Any]:
        return _call("check", args)

    def standards(args: dict[str, Any]) -> dict[str, Any]:
        return _call("standards", args)

    def materials(args: dict[str, Any]) -> dict[str, Any]:
        return _call("materials", args)

    def bom(args: dict[str, Any]) -> dict[str, Any]:
        return _call("bom", args)

    # -- writers ------------------------------------------------------------

    def drawing(args: dict[str, Any]) -> dict[str, Any]:
        return _call("drawing", args)

    def export(args: dict[str, Any]) -> dict[str, Any]:
        return _call("export", args)

    def flat(args: dict[str, Any]) -> dict[str, Any]:
        return _call("flat", args)

    def import_(args: dict[str, Any]) -> dict[str, Any]:
        return _call("import", args)

    def script(args: dict[str, Any]) -> dict[str, Any]:
        return _call("script", args)

    for tool in (
        VirtualTool(
            name="pk_probe",
            description=(
                "Kernel health: OCCT/OCP version, mode (in-process|sidecar|absent), warm "
                "state, formats, licence notices.\n\n"
                "Never waits and never imports: the answer comes from the adapter's own "
                "state, so it is the right first call on a cold server. `deep: true` asks "
                "the kernel itself, which selects (and may spawn) it."
            ),
            schema={
                "type": "object",
                "properties": {
                    "deep": {
                        "type": "boolean",
                        "description": "ask the kernel itself; may spawn the sidecar",
                    }
                },
            },
            handler=probe,
            tags=[
                "partkiln",
                "probe",
                "health",
                "kernel",
                "occt",
                "ocp",
                "version",
                "warm",
                "warming",
                "sidecar",
                "mode",
                "licence",
                "license",
                "formats",
                "mechanical",
                "cad",
            ],
            examples=[{}],
        ),
        VirtualTool(
            name="pk_verbs",
            description=(
                "The batch vocabulary for parts, assemblies, drawings, sheet metal - one "
                "example op per kind.\n\n"
                "Modelling is tee_batch, not a tool per feature: sketch, extrude, revolve, "
                "sweep, loft, hole, fillet, chamfer, shell, draft, pattern, mirror, "
                "combine, split, datums, component, mate, joint, drawing and sheet are all "
                "`{op, kind, name, props}` rows. This is where you look them up, with the "
                "required props and the defaults that are otherwise only echoed as "
                "`assumed` in the diff."
            ),
            schema={
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "description": "one kind, e.g. hole; omit for all"},
                    "examples": {"type": "boolean", "description": "include an example op"},
                },
            },
            handler=verbs,
            tags=[
                "partkiln",
                "verbs",
                "vocabulary",
                "batch",
                "ops",
                "sketch",
                "sketches",
                "extrude",
                "extrudes",
                "revolve",
                "sweep",
                "loft",
                "hole",
                "holes",
                "fillet",
                "fillets",
                "chamfer",
                "shell",
                "draft",
                "pattern",
                "patterns",
                "mirror",
                "part",
                "parts",
                "assembly",
                "assemblies",
                "mate",
                "mates",
                "joint",
                "joints",
                "component",
                "components",
                "feature",
                "features",
                "model",
                "modelling",
                "cad",
                "examples",
            ],
            examples=[{"kind": "hole", "examples": True}],
        ),
        VirtualTool(
            name="pk_lint",
            description=(
                "Pre-flight a batch without the kernel: schema, units, unresolvable refs, "
                "predicted sketch DOF, structured needs.\n\n"
                "Reads the ops, applies nothing, touches no geometry - so it costs a "
                "millisecond and answers the three questions that otherwise cost a failed "
                "batch: is every op a verb, is every length a unit this kernel accepts, "
                "and can every selector be resolved. Returns one `needs:` list (at most "
                "three questions) when the spec is genuinely under-determined."
            ),
            schema={
                "type": "object",
                "properties": {
                    "batch": {
                        "type": "array",
                        "description": "the ops you are about to send to tee_batch",
                    },
                    "strict_units": {
                        "type": "boolean",
                        "description": "treat a bare number as an error rather than mm/deg",
                    },
                },
            },
            handler=lint,
            tags=[
                "partkiln",
                "lint",
                "preflight",
                "validate",
                "validation",
                "dry",
                "batch",
                "schema",
                "units",
                "dof",
                "needs",
                "refusal",
                "errors",
                "cad",
            ],
            examples=[
                {
                    "batch": [
                        {
                            "op": "create",
                            "kind": "fillet",
                            "name": "f1",
                            "props": {"edges": "plate:edges(dir=Z)", "r": "5mm"},
                        }
                    ]
                }
            ],
        ),
        VirtualTool(
            name="pk_query",
            description=(
                "Resolve a selector to names with sub-shape facts; the feature tree as "
                "text; changes since a revision.\n\n"
                "A sub-shape is addressed by NAME, never by an explorer index (Law 13), "
                "so this is the tool that tells you what a selector like "
                "`plate:edges(dir=Z, not(of=hole))` actually caught - with each face's "
                "type, area, centroid and normal - before a fillet spends a batch on it."
            ),
            schema={
                "type": "object",
                "properties": {
                    "selector": {"type": "string", "description": "e.g. plate:faces(normal=+Z)"},
                    "of": {"type": "string", "description": "part or feature to query"},
                    "tree": {"type": "boolean", "description": "the feature tree as text"},
                    "since": {"type": "integer", "description": "revision to diff against"},
                    "limit": {"type": "integer", "description": "max rows (default 40)"},
                },
            },
            handler=query,
            tags=[
                "partkiln",
                "query",
                "queries",
                "selector",
                "selectors",
                "resolve",
                "names",
                "naming",
                "face",
                "faces",
                "edge",
                "edges",
                "tree",
                "feature",
                "features",
                "history",
                "topology",
                "changes",
                "revision",
                "cad",
            ],
            examples=[{"selector": "plate:edges(dir=Z)"}],
        ),
        VirtualTool(
            name="pk_measure",
            description=(
                "Numbers not pixels: mass, clearance, interference, min wall, section "
                "area, face inventory - live document or a STEP/BREP/STL path.\n\n"
                "The evidence a mechanical part actually needs. Every answer is a scalar "
                "with its units, computed exactly (BRepGProp, not a mesh estimate) unless "
                "the row says `estimate`. Works on a file too, so a part that never "
                "entered this document can still be weighed."
            ),
            schema={
                "type": "object",
                "properties": {
                    "what": {
                        "type": "string",
                        "description": "mass|bbox|clearance|interference|wall|section|faces|asm",
                    },
                    "of": {"type": "string", "description": "entity id or name"},
                    "path": {"type": "string", "description": "a STEP/BREP/STL file instead"},
                    "a": {"type": "string", "description": "first body for clearance/interference"},
                    "b": {"type": "string", "description": "second body"},
                    "plane": {"type": "string", "description": "section plane, e.g. x=50"},
                    "material": {"type": "string", "description": "material card for mass"},
                    "density_kg_m3": {"type": "number", "description": "override the density"},
                },
            },
            handler=measure,
            tags=[
                "partkiln",
                "measure",
                "measurement",
                "mass",
                "weight",
                "volume",
                "clearance",
                "interference",
                "collision",
                "wall",
                "thickness",
                "section",
                "area",
                "inventory",
                "distance",
                "assembly",
                "assemblies",
                "dof",
                "bbox",
                "part",
                "parts",
                "cad",
            ],
            examples=[{"what": "mass", "of": "part:bracket"}],
        ),
        VirtualTool(
            name="pk_check",
            description=(
                "Verify a spec: bbox, hole dia/count, min wall, watertight, volume/mass "
                "bands, zero interference, DOF -> verdict + violations with the fix.\n\n"
                "The closed rule set is the point: an unknown rule refuses BEFORE any "
                "geometry is measured, and every violation carries `{rule, got, limit, "
                "fix}` rather than a boolean. `strict` turns a violation into a refusal, "
                "which is what a batch wants when the next op depends on the answer."
            ),
            schema={
                "type": "object",
                "properties": {
                    "spec": {"type": "object", "description": "rule: limit pairs"},
                    "of": {"type": "string", "description": "part, assembly or export id"},
                    "strict": {"type": "boolean", "description": "refuse on any violation"},
                },
                "required": ["spec"],
            },
            handler=check,
            tags=[
                "partkiln",
                "check",
                "verify",
                "verification",
                "spec",
                "specification",
                "requirements",
                "tolerance",
                "verdict",
                "violations",
                "watertight",
                "wall",
                "interference",
                "assembly",
                "assemblies",
                "audit",
                "cad",
            ],
            examples=[
                {"spec": {"bbox_mm": [120, 80, 10], "min_wall_mm": 2.0}, "of": "part:bracket"}
            ],
        ),
        VirtualTool(
            name="pk_standards",
            description=(
                "Clearance/tap/drill for a bolt (ISO 273/262 via bd_warehouse), ISO "
                "4762/4014/4017/4032/7089 - with source and licence.\n\n"
                "Every row names the standard it came from and the permissively licensed "
                "table it was read out of, because a hole diameter with no provenance is a "
                "guess. Feed the answer straight into a hole op, or pass "
                '`std: "M6 clearance normal"` in the batch and let the kernel look it up.'
            ),
            schema={
                "type": "object",
                "properties": {
                    "size": {"type": "string", "description": "thread designation, e.g. M6"},
                    "kind": {
                        "type": "string",
                        "description": "clearance|tap|drill|screw|nut|washer",
                    },
                    "fit": {"type": "string", "description": "close|normal|loose (clearance)"},
                    "standard": {"type": "string", "description": "e.g. ISO 4762"},
                    "list": {"type": "boolean", "description": "list the tables and sizes"},
                },
            },
            handler=standards,
            tags=[
                "partkiln",
                "standards",
                "iso",
                "clearance",
                "hole",
                "holes",
                "tap",
                "tapped",
                "drill",
                "bolt",
                "bolts",
                "screw",
                "screws",
                "nut",
                "nuts",
                "washer",
                "washers",
                "fastener",
                "fasteners",
                "thread",
                "threads",
                "pitch",
                "metric",
                "cad",
            ],
            examples=[{"size": "M6", "kind": "clearance", "fit": "normal"}],
        ),
        VirtualTool(
            name="pk_materials",
            description=(
                "Material cards (density, E, yield) with an honesty tier per value. Pure "
                "lookup - assignment is `set part material=` in a batch.\n\n"
                "Each value carries `{value, unit, source, honesty}`: a density cited to "
                "EN 1993-1-1 is not the same claim as a stand-in for a bearing steel, and "
                "a mass computed from either says which it used."
            ),
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "card name, e.g. steel_s275"},
                    "category": {"type": "string", "description": "filter, e.g. steel"},
                    "list": {"type": "boolean", "description": "list every card"},
                },
            },
            handler=materials,
            tags=[
                "partkiln",
                "materials",
                "material",
                "density",
                "steel",
                "aluminium",
                "aluminum",
                "alloy",
                "yield",
                "modulus",
                "young",
                "cards",
                "properties",
                "honesty",
                "mass",
                "cad",
            ],
            examples=[{"name": "steel_s275"}],
        ),
        VirtualTool(
            name="pk_bom",
            description=(
                "Bill of materials: structured or parts-only, qty, material, mass, "
                "standard designations.\n\n"
                "Parts-only rolls every instance of the same part into one row with a "
                "quantity - the shape a purchasing list wants; structured keeps the "
                "assembly tree. Fasteners resolved from the standards tables carry their "
                "designation (ISO 4762 M6x20) rather than a made-up name."
            ),
            schema={
                "type": "object",
                "properties": {
                    "of": {"type": "string", "description": "assembly id; omit for the document"},
                    "structured": {"type": "boolean", "description": "keep the tree"},
                    "parts_only": {"type": "boolean", "description": "roll up to unique parts"},
                },
            },
            handler=bom,
            tags=[
                "partkiln",
                "bom",
                "bill",
                "materials",
                "parts",
                "list",
                "quantity",
                "qty",
                "assembly",
                "assemblies",
                "component",
                "components",
                "purchasing",
                "mass",
                "cad",
            ],
            examples=[{"parts_only": True}],
        ),
        VirtualTool(
            name="pk_drawing",
            description=(
                "Write a dimensioned sheet to SVG/DXF/PDF: views, sections, dims read back "
                "from the model, hole table, parts list, title block.\n\n"
                "Law 15: a dimension is READ from the named sub-shape it points at, never "
                "typed - so `agree` is true by construction and a drawing cannot quietly "
                "disagree with the part. First angle follows ISO, third follows ANSI, and "
                "the choice is echoed as `assumed` when you do not make it."
            ),
            schema={
                "type": "object",
                "properties": {
                    "of": {"type": "string", "description": "part, assembly or drawing id"},
                    "out": {"type": "string", "description": "output DIRECTORY (named by `name`)"},
                    "out_dir": {"type": "string", "description": "alias for out"},
                    "formats": {"type": "array", "description": "svg|dxf|pdf (default svg)"},
                    "name": {"type": "string", "description": "sheet name"},
                    "sheet": {"type": "string", "description": "A4L..A0L|ANSI_B"},
                    "standard": {"type": "string", "description": "ISO|ANSI|DIN"},
                    "angle": {"type": "string", "description": "first|third"},
                    "scale": {"type": "string", "description": "e.g. 1:2"},
                    "views": {"type": "array", "description": "[{name, dir}] front|top|right|iso"},
                    "dims": {"type": "array", "description": "[{name, view, kind, of|a, b}]"},
                    "hole_table": {"type": "boolean"},
                    "parts_list": {"type": "boolean"},
                    "title": {"type": "object", "description": "title-block fields"},
                },
                "required": ["of"],
            },
            handler=drawing,
            tags=[
                "partkiln",
                "drawing",
                "drawings",
                "sheet",
                "sheets",
                "views",
                "dimensions",
                "dimensioned",
                "section",
                "detail",
                "hlr",
                "hidden",
                "svg",
                "dxf",
                "pdf",
                "title",
                "blueprint",
                "annotation",
                "print",
                "cad",
            ],
            examples=[
                {
                    "of": "part:bracket",
                    "out": "out/bracket.svg",
                    "views": [{"name": "top", "dir": "top"}, {"name": "front", "dir": "front"}],
                }
            ],
        ),
        VirtualTool(
            name="pk_export",
            description=(
                "STEP AP242/214/203, IGES, BREP, STL, OBJ, 3MF, GLB, DXF with a handoff "
                "manifest (units, up axis) for Blender/Unreal/Godot; round-trip verified.\n\n"
                "The manifest is the point: STEP and glTF declare their units, STL and OBJ "
                "declare nothing, and the manifest says which - so the receiving "
                "application is never asked to guess a scale. GLB is written Z-up-corrected "
                "and in metres; the round trip is read back and its volume compared."
            ),
            schema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "step|iges|brep|stl|obj|3mf|glb|dxf",
                    },
                    "out": {"type": "string", "description": "output path"},
                    "of": {"type": "string", "description": "part/assembly id; omit for all"},
                    "schema": {"type": "string", "description": "AP242|AP214|AP203 (STEP)"},
                    "tol": {"type": "number", "description": "mesh deflection mm (default 0.05)"},
                    "target": {"type": "string", "description": "blender|unreal|godot"},
                    "job": {"type": "boolean", "description": "run as a background job"},
                },
                "required": ["format", "out"],
            },
            handler=export,
            tags=[
                "partkiln",
                "export",
                "exports",
                "step",
                "ap242",
                "iges",
                "brep",
                "stl",
                "obj",
                "3mf",
                "glb",
                "gltf",
                "dxf",
                "handoff",
                "blender",
                "unreal",
                "godot",
                "manifest",
                "units",
                "interchange",
                "part",
                "parts",
                "cad",
            ],
            examples=[{"format": "step", "out": "out/bracket.step", "of": "part:bracket"}],
        ),
        VirtualTool(
            name="pk_flat",
            description=(
                "Sheet-metal flat pattern: BA/BD per bend (K or bend table), flat extents, "
                "bend lines; DXF layers OUTLINE/BEND_UP/BEND_DOWN/HOLES.\n\n"
                "Bend allowance is A*pi/180*(R + K*T). K defaults to 0.44 - this kernel's "
                "declared choice inside the usual 0.3-0.5 band, not a standard - so a "
                "production part should pass its own `k` or a bend table, and the answer "
                "says which was used."
            ),
            schema={
                "type": "object",
                "properties": {
                    "of": {"type": "string", "description": "sheet id, e.g. sheet:brk"},
                    "out": {"type": "string", "description": "DXF output path"},
                    "k": {"type": "number", "description": "K-factor (default 0.44, declared)"},
                    "bend_table": {"type": "object", "description": "radius/angle -> allowance"},
                    "format": {"type": "string", "description": "dxf|svg|json (default dxf)"},
                },
            },
            handler=flat,
            tags=[
                "partkiln",
                "flat",
                "pattern",
                "sheet",
                "sheetmetal",
                "metal",
                "bend",
                "bends",
                "bending",
                "unfold",
                "unfolded",
                "blank",
                "kfactor",
                "allowance",
                "brake",
                "flange",
                "flanges",
                "dxf",
                "laser",
                "cad",
            ],
            examples=[{"of": "sheet:brk", "out": "out/brk.dxf"}],
        ),
        VirtualTool(
            name="pk_import",
            description=(
                "Import STEP/IGES/BREP as a base body with fingerprint-named faces; "
                "reports units, solids, validity.\n\n"
                "An imported body has no feature history, so its sub-shapes are named by "
                "geometric fingerprint (`import.face[k]`) - selectors still work, and the "
                "report says how many solids arrived, whether they are valid, and what "
                "unit the file declared."
            ),
            schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "the STEP/IGES/BREP file"},
                    "name": {"type": "string", "description": "part name for the base body"},
                    "units": {"type": "string", "description": "override an undeclared unit"},
                },
                "required": ["path"],
            },
            handler=import_,
            tags=[
                "partkiln",
                "import",
                "imports",
                "load",
                "read",
                "step",
                "iges",
                "brep",
                "base",
                "bodies",
                "faces",
                "translate",
                "file",
                "cad",
            ],
            examples=[{"path": "in/housing.step", "name": "housing"}],
        ),
        VirtualTool(
            name="pk_script",
            description=(
                "The document as a replayable script: dump, replay (job when long), replay "
                "with param overrides (the part family), compare fingerprints.\n\n"
                "Law 16: the script IS the state and the B-rep is a cache, so this is also "
                "how a part becomes a family - replay the same commands with "
                '`overrides: {T: "12mm"}` and you have the next size, deterministically, '
                "with a fingerprint you can compare."
            ),
            schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "dump|replay|compare (default dump)",
                    },
                    "path": {"type": "string", "description": "read/write the script here"},
                    "script": {"type": "object", "description": "an inline script to replay"},
                    "overrides": {"type": "object", "description": "param overrides for a replay"},
                    "job": {"type": "boolean", "description": "run a long replay as a job"},
                },
            },
            handler=script,
            tags=[
                "partkiln",
                "script",
                "scripts",
                "replay",
                "dump",
                "history",
                "commands",
                "overrides",
                "parametric",
                "family",
                "variants",
                "fingerprint",
                "determinism",
                "deterministic",
                "rebuild",
                "regen",
                "cad",
            ],
            examples=[{"action": "replay", "overrides": {"T": "12mm"}}],
        ),
    ):
        app.registry.register(tool)


__all__ = ["LICENCE_NOTICES", "register_partkiln_tools"]
