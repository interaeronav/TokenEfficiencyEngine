"""The `sk_*` long tail: garment capability that is NOT a scene mutation.

The batch verbs (create / set / delete / arrange / drape / export) drive the
garment through the existing surface. These six are the things a batch is the
wrong shape for - catalogues, reports and file I/O - and they live behind
progressive disclosure like every other long-tail tool, so the always-loaded
surface stays at 17.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

# measured: a .pth written after startup stays invisible (invalidate_caches() too) until restart
INSTALL_HINT = (
    "seamkiln is not installed. From the repo root: "
    "uv pip install --python <this interpreter> -e seamkiln, then restart the server"
)


def _adapter(app):
    from tee.adapters.seamkiln.adapter import SeamkilnAdapter

    for adapter in getattr(app, "adapters", {}).values():
        if isinstance(adapter, SeamkilnAdapter):
            return adapter
    raise TeeError(
        "seamkiln_not_served",
        "no seamkiln adapter is attached to this server.",
        fix="Start with `tee serve --adapter seamkiln`.",
    )


def _need():
    try:
        import seamkiln  # noqa: F401
    except ImportError as exc:
        raise TeeError("seamkiln_unavailable", INSTALL_HINT, fix=INSTALL_HINT) from exc


def register_seamkiln_tools(app) -> None:
    """Register sk_* (the surface stays 17)."""

    def room(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.drape.environment import GRAVITY_PRESETS, Environment

        if not args:
            return {
                "standard": Environment().describe(),
                "gravity_presets": {k: round(v, 3) for k, v in GRAVITY_PRESETS.items()},
                "note": "pass gravity/wind/temperature_c/humidity/pressure_kpa to see "
                "the room it makes; a drape takes it via settings.environment",
            }
        gravity = args.get("gravity")
        if isinstance(gravity, str):
            built = Environment.preset(gravity)
        elif gravity is not None:
            built = Environment(gravity=float(gravity))
        else:
            built = Environment()
        for key in ("temperature_c", "humidity", "pressure_kpa", "wind_gust"):
            if key in args:
                setattr(built, key, float(args[key]))
        if "wind" in args:
            built.wind = tuple(float(v) for v in args["wind"])
        return {
            **built.describe(),
            "conditioning": built.conditioning(str(args.get("fibre", "cotton"))),
        }

    def materials(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln import materials as library

        action = str(args.get("action", "list"))
        if action == "list":
            return {
                "materials": library.library(args.get("category"), tier=args.get("tier")),
                "categories": sorted(library.CATEGORIES),
            }
        if action == "compare":
            return library.compare([str(n) for n in args.get("names", [])])
        if action == "derive":
            # `texture` is the one string on the card (a render property); every
            # other change is a number.
            card = library.derive(
                str(args["base"]),
                str(args["name"]),
                **{
                    k: (str(v) if k == "texture" else float(v))
                    for k, v in (args.get("changes") or {}).items()
                },
            )
            library.add(card, category=str(args.get("category", "custom")), overwrite=True)
            return card.describe()
        if action == "export":
            return library.to_file(args.get("names"), str(args["path"]))
        if action == "import":
            return {"loaded": library.from_file(str(args["path"]), overwrite=True)}
        raise TeeError(
            "seamkiln_bad_material_action",
            f"no material action {action!r}.",
            fix="Actions: list, compare, derive, export, import.",
        )

    def blocks(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.pattern.fixtures import tee_block
        from seamkiln.session import VERBS

        pattern = tee_block()
        return {
            "blocks": [
                {
                    "name": "tee",
                    "panels": [p.id for p in pattern.panels],
                    "seams": len(pattern.seams),
                    "parameters": ["half_chest", "length", "shoulder", "neck"],
                    "units": "mm",
                }
            ],
            # The verbs are driven through tee_batch, not as tools of their
            # own - which is right, but it means a search for "rip a seam"
            # finds nothing unless the vocabulary is written down somewhere a
            # searcher lands. This is that somewhere.
            "batch_verbs": {
                "block": "start from a built-in block",
                "panel / seam / delete": "build a pattern by hand",
                "allowance": "record a seam allowance (the outline stays the sew line)",
                "grade": "scale to measurements, or to_body",
                "cut": "op = cut | dart | spread | pleat",
                "body": "kind = anny | mannequin",
                "arrange": "place the panels on the body",
                "drape": "solve; fabric, frames, and the environment",
                "rip": "tear a seam, or auto=true to let the load choose",
                "pinch": "grabs, mirrored by default",
                "lace": "eyelets, style and tension between two panels",
                "finish": "kind = wash | fur",
                "animate": "blend-shape keyframes",
                "fit / techpack / export": "what comes out",
            },
            "verbs": list(VERBS),
            "note": "create one with {'op':'create','kind':'block','props':{'block':'tee'}}",
        }

    def fabrics(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.pattern.fabric import catalogue, fabric

        name = args.get("name")
        if name:
            return fabric(str(name)).describe()
        return {
            "fabrics": catalogue(),
            "tier_note": "every bundled row is `plausible`: weight and thickness are "
            "published facts, the stiffnesses are solver constants. Measured KES-F "
            "data would be tier `measured` with its test report cited.",
        }

    def fit(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        adapter = _adapter(app)
        if adapter._drape is None or adapter._garment is None or adapter._body is None:
            raise TeeError(
                "seamkiln_not_draped",
                "there is no drape to report on.",
                fix="Run the 'arrange' and 'drape' ops first.",
            )
        from seamkiln.drape.measure import fit_report

        report = fit_report(adapter._garment, adapter._drape.points, adapter._body)
        return {**report, "drape": adapter._drape.report()}

    def plot(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        adapter = _adapter(app)
        if adapter._pattern is None:
            raise TeeError(
                "seamkiln_no_pattern",
                "there is no pattern to plot.",
                fix="Create panels or a block first.",
            )
        from seamkiln.pattern import plot as plotting

        out = str(args["out"])
        if str(args.get("format", "pdf")).lower() == "svg":
            return plotting.to_svg(adapter._pattern, out)
        return plotting.to_pdf(adapter._pattern, out, page=str(args.get("page", "A4")))

    def interchange(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        adapter = _adapter(app)
        from seamkiln.pattern.dxf import DIALECTS, write_dxf

        action = str(args.get("action", "write")).lower()
        flavour = str(args.get("dialect", "astm"))
        if action == "dialects":
            return {
                "dialects": {
                    name: {
                        "verified": d.verified,
                        "source": d.source,
                        "layers": d.layers,
                        "notes": d.notes,
                    }
                    for name, d in DIALECTS.items()
                }
            }
        if action == "read":
            # the session's own `load` verb, so the read enters the script
            # and replays like every other command
            from seamkiln.session import Command, CommandError

            load_args = {k: args[k] for k in ("path", "dialect", "strict", "units_mm") if k in args}
            try:
                result = adapter.session.apply(Command("load", load_args))
            except CommandError as exc:
                raise TeeError("seamkiln_load_refused", str(exc), fix=str(exc)) from exc
            return {
                "pieces": len(result["panels"]),
                **{k: v for k, v in result.items() if k != "panels"},
                "summary": adapter.session.pattern.summary(),
            }
        if adapter._pattern is None:
            raise TeeError(
                "seamkiln_no_pattern",
                "there is no pattern to write.",
                fix="Create a pattern, or use action='read'.",
            )
        return write_dxf(adapter._pattern, str(args["path"]), flavour=flavour)

    def body(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.drape.body import mannequin
        from seamkiln.drape.measure import body_measurements

        kind = str(args.get("kind", "mannequin")).lower()
        stature = float(args.get("stature_m", 1.75))
        if kind == "anny":
            from seamkiln.drape.anny_body import anny_body, describe

            mesh = anny_body(
                stature_m=stature,
                **{
                    k: float(v)
                    for k, v in args.items()
                    if k in ("gender", "age", "muscle", "weight", "height", "proportions")
                },
            )
            shape = describe(mesh)
        else:
            mesh = mannequin(height=stature, chest=float(args.get("chest_m", 1.0)))
            shape = {"vertices": len(mesh.vertices), "faces": len(mesh.faces)}
        return {"kind": kind, "mesh": shape, "measurements": body_measurements(mesh)}

    def techpack(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        adapter = _adapter(app)
        from seamkiln.session import Command, CommandError

        try:
            return adapter.session.apply(Command("techpack", dict(args)))
        except CommandError as exc:
            raise TeeError("seamkiln_techpack_refused", str(exc), fix=str(exc)) from exc

    def look(args: dict[str, Any]) -> dict[str, Any]:
        """Render the drape and ask the local vision model what it sees.

        A51's law, restated where it matters: the model's verdict is ADVICE,
        not measurement. It may say a garment reads as a shirt; it may not
        decide that a seam closed or that cloth stayed out of the body -
        `sk_fit` and the drape report decide those, from geometry. This tool
        is labelled accordingly and is never allowed to fail a build.
        """
        _need()
        adapter = _adapter(app)
        if adapter.session.garment is None:
            raise TeeError(
                "seamkiln_nothing_to_look_at",
                "no garment has been arranged yet.",
                fix="Run the 'arrange' and 'drape' ops first.",
            )
        from seamkiln.drape import preview

        ok, why = preview.available()
        if not ok:
            return {
                "kind": "advice",
                "available": False,
                "reason": why,
                "note": "the geometry is unaffected: read sk_fit and the drape report.",
            }
        session = adapter.session
        points = session.drape.points if session.drape else session.garment.points
        adapter.workdir.mkdir(parents=True, exist_ok=True)
        prefix = adapter.workdir / "look"
        preview.render(
            prefix,
            garment=preview.garment_mesh(points, session.garment.triangles),
            body=session.body,
            views={"front": (0.0, 5.0)},
            width=512,
            height=680,
        )
        image = f"{prefix}_front.png"
        question = str(
            args.get("question")
            or "Describe this draped garment: what kind of garment is it, how does it "
            "hang, and does anything look wrong? Three sentences."
        )
        try:
            from tee import senses

            answer = senses.describe({"path": image, "question": question, "max_tokens": 220})
        except Exception as exc:  # advice must never fail a build
            return {
                "kind": "advice",
                "available": False,
                "reason": f"{type(exc).__name__}: {exc}"[:200],
                "image": image,
                "note": "the geometry is unaffected: read sk_fit and the drape report.",
            }
        return {
            "kind": "advice",
            "available": True,
            "image": image,
            "question": question,
            "reading": answer.get("answer"),
            "provided_by": answer.get("provided_by"),
            "caveat": "A model's eye is ADVICE, not measurement. Seam closure, "
            "penetration and ease are decided by geometry - see sk_fit.",
        }

    app.registry.register(
        VirtualTool(
            name="sk_blocks",
            description=(
                "seamkiln's built-in pattern blocks AND the batch verb vocabulary - "
                "grade, cut, dart, pleat, rip a seam, pinch, lace, wash, fur, animate. "
                "Those are driven through tee_batch rather than as tools of their own, "
                "so this is where to look them up."
            ),
            schema={"type": "object", "properties": {}},
            handler=blocks,
            tags=[
                "seamkiln",
                "pattern",
                "garment",
                "sewing",
                "block",
                "draft",
                "tshirt",
                "t-shirt",
                "shirt",
                "clothing",
                "apparel",
                "make",
            ],
            examples=[{}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_fabrics",
            description=(
                "The fabric catalogue with weight, thickness and an honest tier flag, "
                "or one fabric's full card including the solver compliances it maps to. "
                "Every bundled row is tier `plausible`: the weights are published facts, "
                "the stiffnesses are solver constants, and nothing here is a KES-F "
                "measurement pretending to be one."
            ),
            schema={
                "type": "object",
                "properties": {"name": {"type": "string", "description": "One fabric to detail."}},
            },
            handler=fabrics,
            tags=["seamkiln", "fabric", "cloth", "material", "textile", "drape"],
            examples=[{}, {"name": "denim_12oz"}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_fit",
            description=(
                "The fitting report for the current drape: body measurements, per-landmark "
                "ease in millimetres with a verdict, and a per-panel strain map. Numbers, "
                "not a picture - `tee_capture` renders the garment when a picture is what "
                "you need."
            ),
            schema={"type": "object", "properties": {}},
            handler=fit,
            tags=["seamkiln", "fit", "ease", "measure", "garment", "strain", "fitting"],
            examples=[{}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_plot",
            description=(
                "Write the pattern as sheets: a true 1:1 tiled PDF for printing (every "
                "tile carries a 100 mm ruler) or a single SVG. Returns the sheet size and "
                "page count, never the file."
            ),
            schema={
                "type": "object",
                "properties": {
                    "out": {"type": "string", "description": "Destination path."},
                    "format": {"type": "string", "description": "pdf (default) or svg."},
                    "page": {
                        "type": "string",
                        "description": "A4 | A3 | A0 | LETTER | PLOTTER_1370. Default A4.",
                    },
                },
                "required": ["out"],
            },
            handler=plot,
            tags=["seamkiln", "plot", "print", "pattern", "sheet", "pdf", "plotter"],
            examples=[{"out": "/tmp/tee.pdf", "page": "A4"}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_interchange",
            description=(
                "Read or write a pattern as industry DXF - the AAMA and ASTM dialects, "
                "with the 23-layer map. `action='read'` is the session's `load` op (also "
                "a tee_batch op): it replaces the pattern, enters the script and reports "
                "which unit won. `action='dialects'` returns the layer tables and which "
                "of them this repo has verified; ASTM is verified, AAMA's layer map is "
                "second-hand and says so."
            ),
            schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "write (default) | read | dialects",
                    },
                    "path": {"type": "string"},
                    "dialect": {"type": "string", "description": "astm (default) | aama"},
                    "strict": {
                        "type": "boolean",
                        "description": "Reading: refuse unknown layers. Default true.",
                    },
                    "units_mm": {
                        "type": "number",
                        "description": (
                            "Reading: millimetres per drawing unit, overriding $INSUNITS "
                            "and the header's UNITS text (METRIC = cm). Read the result's "
                            "units_source before trusting a size."
                        ),
                    },
                },
            },
            handler=interchange,
            tags=["seamkiln", "dxf", "aama", "astm", "pattern", "interchange", "cad", "import"],
            examples=[{"action": "dialects"}, {"action": "write", "path": "/tmp/p.dxf"}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_body",
            description=(
                "Build a parametric body and measure it: stature, chest girth and the "
                "tape-measure landmarks. `kind='anny'` is the real model (Apache-2.0, "
                "six phenotype axes from infant to elder); `kind='mannequin'` is a "
                "stand-in that needs no download."
            ),
            schema={
                "type": "object",
                "properties": {
                    "kind": {"type": "string", "description": "anny | mannequin (default)."},
                    "stature_m": {"type": "number"},
                    "chest_m": {"type": "number", "description": "mannequin only."},
                    "gender": {"type": "number"},
                    "age": {"type": "number"},
                    "muscle": {"type": "number"},
                    "weight": {"type": "number"},
                    "proportions": {"type": "number"},
                },
            },
            handler=body,
            tags=["seamkiln", "body", "avatar", "mannequin", "measure", "size", "fit"],
            examples=[{"kind": "anny", "stature_m": 1.72}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_techpack",
            description=(
                "Write the tech pack: piece list, fabric card WITH ITS TIER FLAG, seam "
                "schedule with ease and mismatch, and - when the garment has been draped "
                "- the fit and strain tables. The document a factory is actually sent."
            ),
            schema={
                "type": "object",
                "properties": {
                    "out": {"type": "string", "description": "Destination PDF path."},
                    "style": {"type": "string", "description": "Style name/number."},
                    "author": {"type": "string"},
                },
                "required": ["out"],
            },
            handler=techpack,
            tags=["seamkiln", "techpack", "spec", "factory", "document", "pdf", "garment"],
            examples=[{"out": "/tmp/tee.pdf", "style": "TEE-001"}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_look",
            description=(
                "Render the drape and ask the local vision model what it sees - a second "
                "opinion on whether the garment READS right. Advice, never measurement: "
                "seam closure, body penetration and ease are decided by geometry in "
                "sk_fit, and this tool is not allowed to fail a build."
            ),
            schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "What to ask about it."}
                },
            },
            handler=look,
            tags=["seamkiln", "look", "vision", "render", "check", "garment", "advice"],
            examples=[{}, {"question": "Does the sleeve sit correctly on the shoulder?"}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_room",
            description=(
                "The environment a garment is tested in: gravity (any strength, any "
                "direction), wind with a deterministic gust, and temperature / humidity / "
                "pressure, which reach the cloth through moisture regain. Called bare it "
                "returns the ISO 139 standard atmosphere and the gravity presets."
            ),
            schema={
                "type": "object",
                "properties": {
                    "gravity": {
                        "description": "a preset (earth|moon|mars|jupiter|zero|half|"
                        "double) or a number in m/s^2"
                    },
                    "wind": {"type": "array", "description": "[x, y, z] in m/s"},
                    "wind_gust": {"type": "number", "description": "0..1 of `wind`"},
                    "temperature_c": {"type": "number"},
                    "humidity": {"type": "number", "description": "relative, 0..1"},
                    "pressure_kpa": {"type": "number"},
                    "fibre": {"type": "string", "description": "which sorption curve"},
                },
            },
            handler=room,
            tags=[
                "seamkiln",
                "environment",
                "gravity",
                "wind",
                "temperature",
                "humidity",
                "pressure",
                "room",
                "climate",
                "test",
            ],
            examples=[{}, {"gravity": "moon", "wind": [4, 0, 0], "humidity": 0.9}],
        )
    )
    app.registry.register(
        VirtualTool(
            name="sk_materials",
            description=(
                "The material library: list by what a cloth is for, compare cards side by "
                "side, derive a variant, or move a library in and out of a file. Deriving "
                "DROPS the tier to `plausible`, because a measured cloth's test report "
                "does not describe one you made heavier."
            ),
            schema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "list (default) | compare | derive | export | import",
                    },
                    "category": {"type": "string"},
                    "tier": {"type": "string"},
                    "names": {"type": "array"},
                    "base": {"type": "string"},
                    "name": {"type": "string"},
                    "changes": {"type": "object"},
                    "path": {"type": "string"},
                },
            },
            handler=materials,
            tags=[
                "seamkiln",
                "material",
                "fabric",
                "library",
                "cloth",
                "catalogue",
                "denim",
                "fur",
                "wash",
                "compare",
            ],
            examples=[{}, {"action": "compare", "names": ["denim_12oz", "chiffon"]}],
        )
    )

    # ------------------------------------------------------------------ A65
    # The A54-A64 capabilities were reachable through `tee_batch` and findable
    # by nothing: "zipper", "button" and "walk cycle" returned an EMPTY search.
    # P4's acceptance says the long tail must land top-3 for its queries, and
    # a capability a model cannot find is a capability it does not have.

    def hardware(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.hardware.buttons import TYPES as BUTTON_TYPES
        from seamkiln.hardware.trim import BUTTON_TRIM, ZIPPER_TRIM
        from seamkiln.hardware.zipper import LAYOUTS, SIZES

        adapter = _adapter(app)
        session = adapter.session
        fitted = {k: z.summary() for k, z in getattr(session, "zippers", {}).items()}
        fastened = [f.summary() for f in getattr(session, "buttons", [])]
        return {
            "zippers": {
                "materials": {
                    k: {"chain_g_per_m_at_5": t.chain_g_per_m, "self_healing": t.self_healing}
                    for k, t in ZIPPER_TRIM.items()
                },
                "sizes": list(SIZES),
                "layouts": list(LAYOUTS),
                "fitted": fitted,
                "verbs": {
                    "zip": {
                        "opening": "centre-front",
                        "material": "metal",
                        "size": 5,
                        "layout": "one-way",
                    },
                    "unzip": {"opening": "centre-front", "to": 0.3, "slider": 0},
                },
            },
            "buttons": {
                "types": list(BUTTON_TYPES),
                "materials": list(BUTTON_TRIM),
                "fastened": fastened,
                "verbs": {
                    "button": {
                        "panel": "FRONT_R",
                        "x": 14,
                        "y": 240,
                        "hole_panel": "FRONT_L",
                        "hole_x": -14,
                        "hole_y": 240,
                        "type": "4-hole",
                        "ligne": 24,
                    },
                    "unfasten": {"id": "button@..."},
                },
                "custom": "register an OBJ with hardware.buttons.register_obj (it is WEIGHED "
                "from its volume) or a black-on-transparent PNG buttonhole with register_mask",
            },
            "openings": "declare a seam kind='zipper' or 'placket' on the pattern; it is "
            "paired but not sewn. The bundled 'jacket-zip' and 'jacket-placket' blocks have one.",
        }

    app.registry.register(
        VirtualTool(
            name="sk_hardware",
            description=(
                "Zippers and buttons: what can be fitted (materials, sizes, one-way and "
                "two-way layouts; button types and materials), what IS fitted on the "
                "current garment, and the exact batch ops to fit, drag a slider, fasten "
                "or undo. Hardware is trim, not cloth - it carries its own weight and "
                "stiffness into the drape."
            ),
            schema={"type": "object", "properties": {}},
            handler=hardware,
            tags=[
                "seamkiln",
                "zipper",
                "zip",
                "slider",
                "button",
                "buttonhole",
                "snap",
                "rivet",
                "toggle",
                "fasten",
                "hardware",
                "trim",
                "placket",
                "garment",
            ],
            examples=[{}],
        )
    )

    def avatar(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.avatar import GAITS, JOINTS
        from seamkiln.figure import PARTS

        adapter = _adapter(app)
        session = adapter.session
        body = dict(getattr(session, "body_spec", {}) or {})
        return {
            "bodies": {
                "mannequin": "capsule stand-in, no download; the cylinder arrangement is "
                "tuned on it",
                "anny": "parametric, Apache-2.0; phenotypes gender/age/muscle/weight/"
                "height/proportions",
                "posed": "the mannequin at joint angles",
                "figure": "a clothable figure with joints (arms/legs/trunk) that the dressing "
                "lane asks directly; walks with articulated limbs",
                "custom": "your own mesh from 'path'; units and up-axis inferred and "
                "REPORTED. A glTF carrying a SKIN keeps its skeleton and walks with "
                "articulated limbs; any other file walks as one piece and the answer "
                "says which, in 'articulated'",
            },
            "joints": list(JOINTS),
            "figure_parts": list(PARTS),
            "gaits": {
                k: {"speed_ms": g.speed_ms, "cycle_s": g.cycle_s, "source": g.source}
                for k, g in GAITS.items()
            },
            "current_body": body,
            "verbs": {
                "body": {"kind": "figure", "stature_m": 1.8, "pose": {"hip_r": 20}},
                "arrange": {"arrangement": "auto|cylinder|wrap", "dress": True},
                "walk": {
                    "gait": "walk",
                    "cycles": 1.0,
                    "fps": 12,
                    "travel": True,
                    "heading": [0, 0, 1],
                },
                "animate": "blend-shape keyframes on an anny body (see the session verb)",
            },
            "laws": [
                "cloth time per animation frame is DERIVED from fps; a mismatch is refused",
                "travel uses the gait's own speed, or the feet skate",
                "'auto' arrangement = cylinder on the mannequin, wrap on anything else",
            ],
        }

    app.registry.register(
        VirtualTool(
            name="sk_avatar",
            description=(
                "Bodies, poses and gait: which avatars exist (mannequin, Anny, posed, a "
                "clothable figure with joints, your own mesh), the walk/run gait "
                "kinematics, how a garment is dressed onto a body, and the batch ops for "
                "posing, walking and animating a draped garment on it."
            ),
            schema={"type": "object", "properties": {}},
            handler=avatar,
            tags=[
                "seamkiln",
                "avatar",
                "body",
                "figure",
                "rig",
                "pose",
                "walk",
                "run",
                "gait",
                "animation",
                "cycle",
                "dress",
                "custom",
                "import",
            ],
            examples=[{}],
        )
    )

    def touch(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        return {
            "what": "live interaction with a draped garment, at an interactive rate",
            "measured": "43 fps on a 4,549-particle tee (23 ms a step) once the constraint "
            "graph is prepared once and reused; a rebuilt graph ran at 18 fps",
            "verbs": {
                "pull": {
                    "x": 0.17,
                    "y": 0.92,
                    "z": 0.01,
                    "to_x": 0.22,
                    "to_y": 0.95,
                    "to_z": -0.06,
                    "radius_mm": 40,
                    "steps": 12,
                    "settle": 40,
                },
                "fold": {
                    "x": 0.0,
                    "y": 1.1,
                    "z": 0.2,
                    "depth_mm": 40,
                    "direction": [0, 0, -1],
                    "radius_mm": 50,
                },
                "ease": {"seam": "side-right", "mm": 6.0},
                "pinch": "symmetric pinching - see the session verb",
            },
            "notes": [
                "a pull records the NET gesture; `steps` is how finely it is interpolated",
                "ease rebuilds the graph (~30 ms) - it is a discrete edit, not a drag",
                "fold retention is measured along the push axis; it does not order by "
                "stiffness, because weight pulls a fold out while stiffness holds it",
            ],
        }

    app.registry.register(
        VirtualTool(
            name="sk_touch",
            description=(
                "Pull, fold and adjust a draped garment live: grab cloth and drag it at "
                "an interactive rate, push a fold in by hand, or let a seam out or take "
                "it in by millimetres. Returns the batch ops and the measured rate."
            ),
            schema={"type": "object", "properties": {}},
            handler=touch,
            tags=[
                "seamkiln",
                "pull",
                "drag",
                "grab",
                "fold",
                "pinch",
                "ease",
                "stitch",
                "seam",
                "interactive",
                "live",
                "adjust",
                "tweak",
                "garment",
            ],
            examples=[{}],
        )
    )

    def handoff_info(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.handoff import SOURCE, TARGETS

        return {
            "source": {"up": SOURCE.up, "handed": SOURCE.handed, "unit_m": SOURCE.unit_m},
            "targets": {
                k: {
                    "up": t.up,
                    "handed": t.handed,
                    "unit_m": t.unit_m,
                    "prefers": t.prefers,
                    "driven_by_tee": t.driven_by_tee,
                    "note": t.note,
                }
                for k, t in TARGETS.items()
            },
            "verb": {"handoff": {"out": "/path/dir", "target": "blender", "hardware": True}},
            "law": "a self-describing format (glTF/USD) is left alone; OBJ carries the "
            "transform baked into its vertices. Verified in a headless Blender 5.2.",
        }

    def handoff(args: dict[str, Any]) -> dict[str, Any]:
        """No `out`: the targets and their conventions, the listing this tool
        has always been. With `out`: the bundle, written through the
        session's own handoff verb. With `into` as well: the bundle landed in
        a served scene lane as one checkpointed batch with a read-back verdict
        (A68 P3, `kernel/handoff_import.land`) - the ops the verb used to hand
        back are run, not returned."""
        if not args.get("out"):
            return handoff_info(args)
        _need()
        adapter = _adapter(app)
        from seamkiln.session import Command, CommandError

        into = args.get("into")
        into = str(into).strip() if into is not None else None
        verb_args = {k: args[k] for k in ("out", "target", "format", "hardware") if k in args}
        if into and into.lower() != "auto" and "target" not in verb_args:
            from seamkiln.handoff import TARGETS

            if into in TARGETS:  # a lane named for its application writes ITS convention
                verb_args["target"] = into
        try:
            result = adapter.session.apply(Command("handoff", verb_args))
        except CommandError as exc:
            raise TeeError("seamkiln_handoff_refused", str(exc), fix=str(exc)) from exc
        out = dict(result)
        if into:
            from pathlib import Path

            from tee.kernel.handoff_import import land

            name = Path(result["files"]["garment"]).stem
            files = {name: result["files"]["garment"]}
            if "hardware" in result["files"]:
                files[f"{name}-hardware"] = result["files"]["hardware"]
            out.pop("ops", None)
            out.pop("why_no_ops", None)
            out["landed"] = land(
                app, files=files, into=into, units=result.get("units"), caller="sk_handoff"
            )
        return out

    app.registry.register(
        VirtualTool(
            name="sk_handoff",
            description=(
                "Hand a draped garment to another application - Blender, Unreal, Maya, "
                "ZBrush, Houdini, Marvelous, Godot - in ITS units and up-axis, with the "
                "flat-pattern UVs and the hardware. No args lists every target's "
                "conventions; out= writes the bundle (plus the ops that load it where TEE "
                "drives the target); into=<lane|auto> also lands it in a served scene lane "
                "as one checkpointed batch with a read-back verdict."
            ),
            schema={
                "type": "object",
                "properties": {
                    "out": {
                        "type": "string",
                        "description": "directory to write the bundle into; omit to list targets",
                    },
                    "target": {
                        "type": "string",
                        "description": "blender|unreal|maya|zbrush|houdini|marvelous|godot",
                    },
                    "format": {
                        "type": "string",
                        "description": "glb|obj (default: the target's preference)",
                    },
                    "hardware": {
                        "type": "boolean",
                        "description": "include zips and buttons (default true)",
                    },
                    "into": {
                        "type": "string",
                        "description": "land the bundle in this served lane (or auto)",
                    },
                },
            },
            handler=handoff,
            tags=[
                "seamkiln",
                "handoff",
                "export",
                "land",
                "blender",
                "unreal",
                "maya",
                "zbrush",
                "houdini",
                "godot",
                "pipeline",
                "glb",
                "obj",
                "units",
                "axis",
            ],
            examples=[{}, {"out": "shot/", "target": "blender", "into": "auto"}],
        )
    )
