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

INSTALL_HINT = (
    "seamkiln is not installed. From the repo root: "
    "uv pip install --python <this interpreter> -e seamkiln"
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

    def blocks(args: dict[str, Any]) -> dict[str, Any]:
        _need()
        from seamkiln.pattern.fixtures import tee_block

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
        from seamkiln.pattern.dxf import DIALECTS, read_dxf, write_dxf

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
            pattern, report = read_dxf(
                str(args["path"]), flavour=flavour, strict=bool(args.get("strict", True))
            )
            adapter._pattern = pattern
            adapter._garment = None
            adapter._drape = None
            return {
                "pieces": report.pieces,
                "skipped_blocks": report.skipped_blocks,
                "unknown_layers": report.unknown_layers,
                "insunits": report.insunits,
                "summary": pattern.summary(),
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
                "List seamkiln's built-in pattern blocks and the parameters each takes. "
                "A block is a starting garment - draft from it with a create/block op, "
                "then edit panels through the normal batch verbs."
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
                "with the 23-layer map. `action='dialects'` returns the layer tables and "
                "which of them this repo has verified; ASTM is verified, AAMA's layer map "
                "is second-hand and says so."
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
