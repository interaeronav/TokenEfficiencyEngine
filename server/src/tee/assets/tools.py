"""TEE Assets virtual tools (as_*), registered into the progressive-
disclosure registry. Thin handlers over the assets modules; every scene
mutation goes through app.run_batch (checkpointed, diff-reported)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.assets import context as context_mod
from tee.assets import importer as importer_mod
from tee.assets import materials as materials_mod
from tee.assets.generation import GenerationLane, build_drivers, probe_local_gpu
from tee.assets.ingest import ingest_directory
from tee.assets.search import AssetSearch
from tee.assets.sources import build_backends
from tee.assets.store import AssetStore
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool


def register_asset_tools(
    app, project_root: Path | str, *, extract_store=None
) -> AssetStore:
    config = app.config.assets if hasattr(app.config, "assets") else {}
    store = AssetStore(project_root, allow_sa=bool(config.get("allow_sa")))
    backends = build_backends(store, config)
    search = AssetSearch(store, backends)
    lane = GenerationLane(build_drivers(config))
    reg = app.registry
    default_adapter = next(iter(app.adapters), "fake")

    def _adapter(args: dict[str, Any]) -> str:
        return str(args.get("adapter") or default_adapter)

    # -- sources / search --------------------------------------------------

    def as_sources(args):
        rows = []
        for name, backend in backends.items():
            rows.append(
                {
                    "id": name,
                    "assets": backend.asset_license_regime,
                    "site_tos": backend.site_tos,
                    **({"credit": backend.credit_note} if backend.credit_note else {}),
                }
            )
        return {
            "backends": rows,
            "cached_assets": len(store.index()),
            "allow_sa": store.allow_sa,
        }

    def as_search(args):
        style_palette = None
        if args.get("match_style"):
            brief = context_mod.style_brief(store, extract_store)
            style_palette = [c["lab"] for c in brief.get("palette", [])] or None
        return search.search(
            str(args["query"]),
            asset_class=args.get("asset_class"),
            license_filter=args.get("license"),
            max_tris=args.get("max_tris"),
            dims_range=args.get("dims_range"),
            style_palette=style_palette,
            limit=int(args.get("limit", 5)),
            backends=args.get("backends"),
        )

    def as_ingest(args):
        directory = Path(str(args["directory"])).expanduser()
        if not directory.is_dir():
            raise TeeError(
                "no_such_directory",
                f"Not a directory: {directory}",
                fix="Pass a folder containing models/texture sets.",
            )
        return ingest_directory(store, directory)

    # -- import / credits --------------------------------------------------

    def as_import(args):
        return importer_mod.import_asset(
            app,
            store,
            backends,
            str(args["asset"]),
            adapter=_adapter(args),
            asset_class=args.get("asset_class"),
            target_dims=args.get("target_dims"),
            location=args.get("location"),
            rotation=args.get("rotation"),
            name=args.get("name"),
        )

    def as_credits(args):
        out_path = (
            Path(str(args["path"])) if args.get("path") else None
        )
        path = store.write_credits(out_path)
        required = sum(
            1
            for key in store.index()
            if _manifest_requires(store, key)
        )
        return {"path": str(path), "assets": len(store.index()), "required_credits": required}

    # -- creation lanes ----------------------------------------------------

    def as_materials(args):
        return {"materials": materials_mod.list_materials(args.get("category"))}

    def as_material(args):
        ops, provenance = materials_mod.assign_ops(str(args["id"]), str(args["query"]))
        batch = app.run_batch(_adapter(args), ops, label=f"material:{provenance['name']}")
        return {
            "provenance": provenance,
            **{k: batch[k] for k in ("checkpoint", "modified", "epoch", "revision") if k in batch},
        }

    def as_generate(args):
        gpu = probe_local_gpu()
        if not lane.drivers:
            raise TeeError(
                "no_generators",
                "No generation drivers are configured.",
                fix="Hosted: set TEE_TRIPO_KEY / TEE_MESHY_KEY. Local GPU: "
                + gpu.get("fix", "available"),
            )
        return lane.generate(
            str(args.get("driver") or next(iter(lane.drivers))),
            str(args.get("kind", "text_to_model")),
            str(args["prompt"]),
            options=args.get("options"),
            confirm_cost=bool(args.get("confirm_cost")),
        )

    def as_generate_status(args):
        return lane.status(str(args["driver"]), str(args["task"]))

    def as_photo_material(args):
        from tee.assets import photo_pbr

        photo = Path(str(args["photo"]))
        out_dir = store.root / "derived" / photo.stem
        source = photo
        if args.get("corners"):
            rect = photo_pbr.rectify(
                photo,
                args["corners"],
                out_dir / f"{photo.stem}_rect.png",
                width_m=float(args.get("width_m", 1.0)),
                height_m=float(args.get("height_m", 1.0)),
            )
            source = Path(rect["path"])
        maps = photo_pbr.derive_maps(
            source, out_dir, surface=str(args.get("surface", "generic"))
        )
        if args.get("tileable"):
            maps["tiled"] = photo_pbr.make_tileable(
                source, out_dir / f"{photo.stem}_tile.png"
            )["path"]
        return maps

    # -- context -----------------------------------------------------------

    def as_style_brief(args):
        return context_mod.style_brief(store, extract_store)

    def as_sun(args):
        position = context_mod.sun_position(
            float(args["lat"]),
            float(args["lon"]),
            str(args["when"]),
            tz=args.get("tz"),
        )
        out: dict[str, Any] = dict(position)
        out["hdri"] = context_mod.hdri_query(
            position["elevation_deg"], str(args.get("weather", "clear"))
        )
        if args.get("apply"):
            adapter = _adapter(args)
            ops = context_mod.sun_ops(adapter, position)
            batch = app.run_batch(adapter, ops, label="sun")
            out.update(
                {k: batch[k] for k in ("checkpoint", "created", "epoch", "revision") if k in batch}
            )
        return out

    def as_place(args):
        from tee.assets import placement as placement_mod

        room = args["room"]
        placements = placement_mod.solve_plan(args["plan"], room)
        report = placement_mod.validate_placement(
            placements, room, region=str(args.get("region", "US"))
        )
        out: dict[str, Any] = {"placements": placements, **report}
        code_violations = [
            v for v in report["violations"] if v["severity"] == "code"
        ]
        if args.get("apply"):
            if report["violations"]:
                out["applied"] = False
                out["note"] = (
                    "not applied: fix the violations (code rows are never "
                    "relaxable; guideline rows relax via plan item relax=[...])"
                    if code_violations
                    else "not applied: guideline violations present - relax "
                    "them explicitly in the plan or adjust it"
                )
                return out
            ops = []
            for item, place in zip(args["plan"], placements, strict=True):
                x, y = place["location"]
                props = {
                    "location": [x, y, 0.0],
                    "rotation_euler": [0.0, 0.0, _radians(place["rotation_deg"])],
                }
                if item.get("id"):
                    ops.append({"op": "set", "id": item["id"], "props": props})
            if ops:
                batch = app.run_batch(_adapter(args), ops, label="place")
                out["applied"] = True
                out.update(
                    {
                        k: batch[k]
                        for k in ("checkpoint", "modified", "epoch", "revision")
                        if k in batch
                    }
                )
            else:
                out["applied"] = False
                out["note"] = "no plan item carried an entity id to move"
        return out

    def as_sheet(args):
        from tee.assets.http import fetch_bytes

        keys = [str(k) for k in args["assets"]]
        entries = []
        missing = []
        thumbs_dir = store.root / "thumbs"
        for key in keys:
            source_name, _, source_id = key.partition(":")
            path = None
            entry = store.index().get(key)
            if entry and (entry.get("maps") or {}).get("base_color"):
                path = Path(entry["maps"]["base_color"])
            else:
                cached = thumbs_dir / f"{source_id}.png"
                if cached.exists():
                    path = cached
                else:
                    backend = backends.get(source_name)
                    url = backend.thumbnail_url(source_id) if backend else None
                    if url:
                        try:
                            cached.parent.mkdir(parents=True, exist_ok=True)
                            cached.write_bytes(fetch_bytes(url, timeout_s=30))
                            path = cached
                        except TeeError:
                            path = None
            if path is not None and path.exists():
                entries.append({"path": path, "label": key.split(":", 1)[-1][:24]})
            else:
                missing.append(key)
        if not entries:
            raise TeeError(
                "no_thumbnails",
                "None of the requested assets has a thumbnail available.",
                fix="Sheet works for Poly Haven hits and local material sets; "
                "judge others by their dims/tags rows.",
            )
        from tee.extract.images import contact_sheet

        sheets_dir = store.root / "sheets"
        sheets_dir.mkdir(parents=True, exist_ok=True)
        out_path = sheets_dir / f"sheet_{abs(hash(tuple(keys))) % 10**8}.jpg"
        sheet = contact_sheet(entries, out_path, cell=int(args.get("cell", 256)))
        if extract_store is not None:
            meta = extract_store.register_source(out_path)
            sheet["media_ref"] = meta["hash"][:8]
            sheet["view_with"] = f"tee_media(source='{meta['hash'][:8]}')"
        if missing:
            sheet["no_thumbnail"] = missing
        return sheet

    def as_verify(args):
        from tee.assets.verify import verify_scene

        style_palette = None
        if args.get("match_style"):
            brief = context_mod.style_brief(store, extract_store)
            style_palette = [c["lab"] for c in brief.get("palette", [])] or None
        return verify_scene(
            app,
            _adapter(args),
            room=args.get("room"),
            region=str(args.get("region", "US")),
            style_palette=style_palette,
        )

    # -- registration ------------------------------------------------------

    tools = [
        VirtualTool(
            "as_verify",
            "Render-free verification battery over the current scene: scale "
            "sanity vs class envelopes, AABB collisions (<=5 mm contact ok), "
            "floating objects, room clearances (pass room=), palette-vs-brief "
            "(match_style=true). One compact violations+fixes report; says "
            "whether a single budgeted render is even warranted.",
            {
                "type": "object",
                "properties": {
                    "adapter": {"type": "string"},
                    "room": {"type": "object"},
                    "region": {"type": "string"},
                    "match_style": {"type": "boolean"},
                },
            },
            as_verify,
            tags=["assets", "verify", "collision", "support", "check"],
        ),
        VirtualTool(
            "as_sources",
            "List enabled asset backends with their license regime and site-ToS "
            "constraints, plus cache stats.",
            {"type": "object", "properties": {}},
            as_sources,
            tags=["assets", "sources", "license"],
        ),
        VirtualTool(
            "as_search",
            "Faceted asset search across free backends + the local library.\n"
            "State WHAT you need; ranking (keywords, style palette) is server-"
            "side. Returns <=5 compact rows per class - detail/preview on "
            "demand.",
            {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "asset_class": {"type": "string"},
                    "license": {"type": "string"},
                    "max_tris": {"type": "integer"},
                    "dims_range": {"type": "array"},
                    "match_style": {"type": "boolean"},
                    "limit": {"type": "integer"},
                    "backends": {"type": "array"},
                },
                "required": ["query"],
            },
            as_search,
            tags=["assets", "search", "find", "model", "material", "hdri"],
            examples=[{"query": "wooden chair", "asset_class": "model", "max_tris": 20000}],
        ),
        VirtualTool(
            "as_sheet",
            "One labeled contact sheet for a shortlist (Poly Haven hits + "
            "local material sets) as the selection tie-breaker; view it via "
            "tee_media. Never the default - rows usually decide.",
            {
                "type": "object",
                "properties": {
                    "assets": {"type": "array"},
                    "cell": {"type": "integer"},
                },
                "required": ["assets"],
            },
            as_sheet,
            tags=["assets", "sheet", "preview", "thumbnails"],
        ),
        VirtualTool(
            "as_ingest",
            "Index a local asset folder (models + texture sets) into the "
            "searchable library; files stay in place.",
            {
                "type": "object",
                "properties": {"directory": {"type": "string"}},
                "required": ["directory"],
            },
            as_ingest,
            tags=["assets", "ingest", "library", "local"],
        ),
        VirtualTool(
            "as_import",
            "Download (license-gated, cached) and place one asset by "
            "'source:id'.\nApplies the four-band scale policy (accept / unit-"
            "fix / snap / reject); target_dims fits e.g. a door into its plan "
            "opening. Mutation runs as a checkpointed batch with read-back "
            "verification.",
            {
                "type": "object",
                "properties": {
                    "asset": {"type": "string"},
                    "adapter": {"type": "string"},
                    "asset_class": {"type": "string"},
                    "target_dims": {"type": "array"},
                    "location": {"type": "array"},
                    "rotation": {"type": "array"},
                    "name": {"type": "string"},
                },
                "required": ["asset"],
            },
            as_import,
            tags=["assets", "import", "place", "download"],
        ),
        VirtualTool(
            "as_credits",
            "Render CREDITS.md from the per-asset attribution manifests.",
            {"type": "object", "properties": {"path": {"type": "string"}}},
            as_credits,
            tags=["assets", "credits", "attribution", "license"],
        ),
        VirtualTool(
            "as_materials",
            "List the measured CC0 material dataset (physicallybased.info): "
            "compact name/category/scalar rows.",
            {"type": "object", "properties": {"category": {"type": "string"}}},
            as_materials,
            tags=["assets", "materials", "pbr", "list"],
        ),
        VirtualTool(
            "as_material",
            "Assign a measured PBR material (lane 0, zero-GPU) to an entity "
            "by id; values carry provenance (dataset, license, honesty label).",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "query": {"type": "string"},
                    "adapter": {"type": "string"},
                },
                "required": ["id", "query"],
            },
            as_material,
            tags=["assets", "material", "assign", "pbr", "procedural"],
        ),
        VirtualTool(
            "as_generate",
            "Generate an asset via a configured driver (hosted Tripo/Meshy or "
            "local GPU).\nPAID drivers require confirm_cost=true after the "
            "estimate. Polling is server-side: one call, one result. Set "
            "dressing quality - hero assets are curated, not generated.",
            {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "driver": {"type": "string"},
                    "kind": {"type": "string"},
                    "options": {"type": "object"},
                    "confirm_cost": {"type": "boolean"},
                },
                "required": ["prompt"],
            },
            as_generate,
            tags=["assets", "generate", "ai", "text-to-3d"],
        ),
        VirtualTool(
            "as_generate_status",
            "Status of a generation task that outlived the wait-poll window.",
            {
                "type": "object",
                "properties": {
                    "driver": {"type": "string"},
                    "task": {"type": "string"},
                },
                "required": ["driver", "task"],
            },
            as_generate_status,
            tags=["assets", "generate", "status", "job"],
        ),
        VirtualTool(
            "as_photo_material",
            "Photo-derived PBR (lane 2): optional homography rectify (4 "
            "corners) then estimated normal/roughness maps; metallic clamped "
            "on masonry/paint. Classical path; GPU machines refine it.",
            {
                "type": "object",
                "properties": {
                    "photo": {"type": "string"},
                    "corners": {"type": "array"},
                    "width_m": {"type": "number"},
                    "height_m": {"type": "number"},
                    "surface": {"type": "string"},
                    "tileable": {"type": "boolean"},
                },
                "required": ["photo"],
            },
            as_photo_material,
            tags=["assets", "material", "photo", "pbr", "okongo"],
        ),
        VirtualTool(
            "as_style_brief",
            "Auto-derived style brief from ingested site media: named CIELAB "
            "palette, style terms from captions, avoid-list from the audio "
            "brief.",
            {"type": "object", "properties": {}},
            as_style_brief,
            tags=["assets", "style", "brief", "palette", "context"],
        ),
        VirtualTool(
            "as_sun",
            "Sun azimuth/elevation for a GPS datum + ISO datetime (astral; "
            "NREL-verified within 1 deg) with an HDRI band suggestion; "
            "apply=true creates the sun light via a checkpointed batch.",
            {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "when": {"type": "string"},
                    "tz": {"type": "string"},
                    "weather": {"type": "string"},
                    "apply": {"type": "boolean"},
                    "adapter": {"type": "string"},
                },
                "required": ["lat", "lon", "when"],
            },
            as_sun,
            tags=["assets", "sun", "lighting", "hdri", "context"],
        ),
        VirtualTool(
            "as_place",
            "Solve a relational placement plan (anchor wall + offset, ~10 "
            "tokens/object) and validate it against the clearance/circulation "
            "rule table (code vs guideline severity; region-parameterized). "
            "apply=true moves entities (plan items carrying id) only when no "
            "violations remain.",
            {
                "type": "object",
                "properties": {
                    "plan": {"type": "array"},
                    "room": {"type": "object"},
                    "region": {"type": "string"},
                    "apply": {"type": "boolean"},
                    "adapter": {"type": "string"},
                },
                "required": ["plan", "room"],
            },
            as_place,
            tags=["assets", "place", "layout", "validate", "clearance"],
        ),
    ]
    for tool in tools:
        reg.register(tool)
    return store


def _manifest_requires(store: AssetStore, key: str) -> bool:
    try:
        return bool(store.manifest(key).get("attribution_required"))
    except Exception:
        return False


def _radians(deg: float) -> float:
    import math

    return round(math.radians(deg), 5)
