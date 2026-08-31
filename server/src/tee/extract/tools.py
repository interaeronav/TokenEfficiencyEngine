"""TEE Extract virtual tools (ex_*) and ingest routing (7.1/7.5/7.6).

Registered into the progressive-disclosure registry; long operations run as
async jobs; media serving is token-budget-first via the kernel `tee_media`
tool, whose backend this module installs on the app.
"""

from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

from tee.extract import audio as audio_lane
from tee.extract import documents, images, video, vlm
from tee.extract.frames import FrameRegistry, fit_similarity, scale_conflict
from tee.extract.plan import SCHEMA_ID, plan_summary, validate_plan
from tee.extract.store import ExtractStore
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool

INGESTIBLE = ("cad", "bim", "document", "image", "video", "audio", "telemetry")


def register_extract_tools(app, project_root: Path | str) -> tuple[ExtractStore, FrameRegistry]:
    store = ExtractStore(project_root)
    registry = FrameRegistry(store.root)
    app.media_view = _media_view_backend(store)

    def _extract_recap() -> dict[str, Any]:
        kinds: dict[str, int] = {}
        count = 0
        for src in store.sources():
            count += 1
            for fact in store.facts(src["hash"]):
                kinds[fact["kind"]] = kinds.get(fact["kind"], 0) + 1
        out: dict[str, Any] = {"sources": count}
        if kinds:
            out["fact_kinds"] = dict(sorted(kinds.items()))
        return out

    app.extract_recap = _extract_recap
    reg = app.registry

    # -- ingest ------------------------------------------------------------

    def _extract_one(meta: dict[str, Any]) -> dict[str, Any]:
        media_hash = meta["hash"]
        path = Path(meta["paths"][0])
        media_type = meta["media_type"]
        if media_type == "cad":
            extractor = documents.DXF_EXTRACTOR
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            frame = f"dwg:{media_hash[:8]}:model"
            registry.add_frame(frame, "drawing_model", units="m", axes="x-right y-up")
            facts = documents.extract_dxf(path, frame)
        elif media_type == "document":
            extractor = documents.PDF_EXTRACTOR
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            prefix = f"dwg:{media_hash[:8]}"
            facts = documents.extract_pdf(path, prefix)
            for fact in facts:
                if fact["kind"] == "page":
                    registry.add_frame(fact["frame"], "drawing_page", units="m")
        elif media_type == "image":
            extractor = images.IMAGE_EXTRACTOR
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            facts = images.extract_image(path)
        elif media_type == "video":
            extractor = video.VIDEO_EXTRACTOR
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            facts = video.extract_video(path, store.derived_dir(media_hash, "video"))
            sidecar = path.with_suffix(".SRT")
            if not sidecar.exists():
                sidecar = path.with_suffix(".srt")
            if sidecar.exists():
                facts.extend(video.parse_dji_srt(sidecar.read_text(errors="ignore")))
            if path.suffix.lower() in (".mp4", ".mov", ".mkv"):
                # no audio track is a normal video, not an error
                with contextlib.suppress(TeeError):
                    facts.extend(
                        audio_lane.extract_audio(path, store.derived_dir(media_hash, "audio"))
                    )
        elif media_type == "audio":
            extractor = audio_lane.AUDIO_EXTRACTOR
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            facts = audio_lane.extract_audio(path, store.derived_dir(media_hash, "audio"))
        elif media_type == "telemetry":
            extractor = ("telemetry", "1")
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            facts = video.parse_dji_srt(path.read_text(errors="ignore"))
        elif media_type == "bim":
            extractor = ("bim", "1")
            if store.has_facts(media_hash, *extractor):
                return {"skipped": "cached"}
            facts = _extract_ifc(path, f"bim:{media_hash[:8]}")
        else:
            return {"skipped": f"unsupported media type '{media_type}'"}
        count = store.store_facts(media_hash, *extractor, facts, provenance={"path": str(path)})
        return {"facts": count}

    def _ingest_job(paths: list[Path]) -> dict[str, Any]:
        report: dict[str, Any] = {"ingested": 0, "cached": 0, "skipped": [], "errors": []}
        photo_entries = []
        for path in paths:
            try:
                meta = store.register_source(path)
                outcome = _extract_one(meta)
            except TeeError as exc:
                report["errors"].append(f"{path.name}: {exc.message}")
                continue
            except ModuleNotFoundError as exc:
                if (exc.name or "").startswith("tee"):
                    raise  # a broken tee module is a bug, not a missing extra
                report["skipped"].append(
                    f"{path.name}: needs the '{exc.name}' package "
                    f"(tee-engine[extract] extra) - install it in the serving "
                    f"environment to enable this lane"
                )
                continue
            if "facts" in outcome:
                report["ingested"] += 1
            elif outcome.get("skipped") == "cached":
                report["cached"] += 1
            else:
                report["skipped"].append(f"{path.name}: {outcome.get('skipped')}")
            if meta["media_type"] == "image":
                photos = store.facts(meta["hash"], kind="photo")
                if photos:
                    photo_entries.append(
                        {
                            "hash": meta["hash"],
                            "phash": photos[-1]["phash"],
                            "path": str(path),
                        }
                    )
        if len(photo_entries) > 1:
            groups = images.dedupe_photos(photo_entries)
            representatives = [
                {
                    "path": next(
                        p["path"]
                        for p in photo_entries
                        if p["hash"].startswith(g["representative"])
                    ),
                    "label": g["representative"],
                }
                for g in groups
            ]
            sheet_dir = store.root / "sheets"
            sheet_dir.mkdir(parents=True, exist_ok=True)
            sheet = images.contact_sheet(representatives, sheet_dir / "photos.jpg")
            batch_facts = [*groups, sheet]
            store.store_facts(photo_entries[0]["hash"], "photo-batch", "1", batch_facts)
            report["photo_groups"] = len(groups)
            report["contact_sheet"] = sheet["path"]
        return report

    def ex_ingest(args: dict[str, Any]) -> dict[str, Any]:
        target = Path(args["path"])
        if target.is_dir():
            paths = sorted(p for p in target.rglob("*") if p.is_file() and _ingestible(p))
        elif target.is_file():
            paths = [target]
        else:
            raise TeeError("no_such_file", f"Not found: {target}")
        if not paths:
            raise TeeError(
                "nothing_to_ingest",
                f"No ingestible media under {target}.",
                fix=f"Supported types: {', '.join(INGESTIBLE)}.",
            )
        job = app.jobs.submit(f"ex_ingest {target.name}", lambda: _ingest_job(paths))
        return {"job": job, "files": len(paths), "note": "poll tee_job for the report"}

    def _ingestible(path: Path) -> bool:
        from tee.extract.store import media_type_of

        return media_type_of(path) in INGESTIBLE

    def ex_estimate(args: dict[str, Any]) -> dict[str, Any]:
        from tee.extract import estimate

        return estimate.estimate_length(args)

    reg.register(
        VirtualTool(
            name="ex_estimate",
            description=(
                "Estimate a length in millimetres from a photo, using "
                "something of KNOWN size in the same plane. Returns "
                "estimated_mm with an error band - never a measurement. "
                "Refuses without a reference: TEE does not supply the "
                "reference's size itself. Where a drawing or survey exists, "
                "that governs and this must not be used."
            ),
            schema={
                "type": "object",
                "properties": {
                    "reference_mm": {
                        "type": "number",
                        "description": "What the reference really measures.",
                    },
                    "reference_tolerance_mm": {
                        "type": "number",
                        "description": "How sure you are of it. Unstated assumes 2%.",
                    },
                    "reference_iso216": {
                        "type": "string",
                        "description": "Instead of reference_mm: 'a4' etc, exact by standard.",
                    },
                    "reference_edge": {
                        "type": "string",
                        "enum": ["short", "long"],
                        "description": "Which edge of the ISO sheet was measured.",
                    },
                    "reference_px": {"type": "number"},
                    "target_px": {"type": "number"},
                    "coplanar": {
                        "type": "boolean",
                        "description": "Affirm the reference and target share one plane.",
                    },
                    "label": {"type": "string"},
                },
                "required": ["reference_px", "target_px", "coplanar"],
            },
            handler=ex_estimate,
            tags=["extract", "estimate", "dimension", "photo", "scale", "measure"],
            examples=[
                {
                    "reference_iso216": "a4",
                    "reference_edge": "long",
                    "reference_px": 240,
                    "target_px": 1310,
                    "coplanar": True,
                    "label": "window opening width",
                }
            ],
        )
    )

    reg.register(
        VirtualTool(
            name="ex_ingest",
            description=(
                "Ingest source materials (drawings, CAD, PDFs, photos, "
                "satellite tiles, video, audio, DJI SRT) into the extraction "
                "store: content-addressed, deduped, extracted ONCE into "
                "compact facts. Async - poll tee_job. Re-ingesting known "
                "media is a no-op."
            ),
            schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
            handler=ex_ingest,
            tags=["extract", "ingest", "media", "drawings", "photos", "video", "audio"],
            examples=[{"path": "./site-materials"}],
        )
    )

    # -- reads -------------------------------------------------------------

    def ex_sources(args: dict[str, Any]) -> dict[str, Any]:
        sources = store.sources()
        offset = int(args.get("offset") or 0)
        limit = int(args.get("limit") or 20)
        page = sources[offset : offset + limit]
        return {
            "total": len(sources),
            "sources": [
                {
                    "source": s["hash"][:8],
                    "name": s["name"],
                    "type": s["media_type"],
                    "facts": len(store.facts(s["hash"])),
                }
                for s in page
            ],
        }

    reg.register(
        VirtualTool(
            name="ex_sources",
            description="List ingested sources: id, name, media type, fact count.",
            schema={
                "type": "object",
                "properties": {"limit": {"type": "integer"}, "offset": {"type": "integer"}},
            },
            handler=ex_sources,
            tags=["extract", "sources", "list"],
        )
    )

    def ex_search(args: dict[str, Any]) -> dict[str, Any]:
        return {"items": store.search(args["query"], int(args.get("limit") or 10))}

    reg.register(
        VirtualTool(
            name="ex_search",
            description=(
                "Search every extracted fact by keywords (dimensions, room "
                "names, transcript text, requirements...). The cheap way to "
                "answer questions about source materials - never re-read the "
                "media."
            ),
            schema={
                "type": "object",
                "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                "required": ["query"],
            },
            handler=ex_search,
            tags=["extract", "search", "facts", "query"],
            examples=[{"query": "bedroom dimension"}],
        )
    )

    def ex_facts(args: dict[str, Any]) -> dict[str, Any]:
        source = store.resolve(args["source"])
        facts = store.facts(source["hash"], kind=args.get("kind"))
        offset = int(args.get("offset") or 0)
        limit = int(args.get("limit") or 30)
        page = facts[offset : offset + limit]
        compact = [
            {**f, "plan": plan_summary(f["plan"])} if f.get("kind") == "plan" else f for f in page
        ]
        out: dict[str, Any] = {"source": source["hash"][:8], "total": len(facts), "facts": compact}
        if offset + len(page) < len(facts):
            out["truncated"] = f"{len(facts) - offset - len(page)} more; use offset="
        return out

    reg.register(
        VirtualTool(
            name="ex_facts",
            description=(
                "Facts for one source (by hash prefix or filename), "
                "filterable by kind (dimension, plan, keyframe, "
                "transcript_segment, requirement, conflict...). Plan facts "
                "come back summarized; drill in with kind='plan' + the "
                "handoff tools."
            ),
            schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "kind": {"type": "string"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                },
                "required": ["source"],
            },
            handler=ex_facts,
            tags=["extract", "facts", "read"],
        )
    )

    # -- in-band writeback (7.5) -------------------------------------------

    def ex_store_facts(args: dict[str, Any]) -> dict[str, Any]:
        source = store.resolve(args["source"])
        facts = args["facts"]
        if not isinstance(facts, list) or not facts:
            raise TeeError("bad_facts", "facts must be a non-empty array of fact objects.")
        for fact in facts:
            if isinstance(fact, dict) and fact.get("kind") == "plan":
                validate_plan(fact.get("plan"))
        count = store.store_facts(
            source["hash"],
            str(args["extractor"]),
            vlm.IN_BAND_EXTRACTOR_VERSION,
            facts,
            provenance={"channel": "in-band"},
            merge=bool(args.get("merge")),
        )
        return {"stored": count, "source": source["hash"][:8]}

    reg.register(
        VirtualTool(
            name="ex_store_facts",
            description=(
                "Write back structured facts you extracted from a source "
                "(the in-band VLM channel). Facts are schema-validated; "
                "plan facts must match " + SCHEMA_ID + ". Get the packet of "
                "instructions from ex_prepare first. Default replaces this "
                "extractor's prior facts; merge=true appends instead - use "
                "it for incremental passes like captioning."
            ),
            schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "extractor": {"type": "string"},
                    "facts": {"type": "array"},
                    "merge": {"type": "boolean"},
                },
                "required": ["source", "extractor", "facts"],
            },
            handler=ex_store_facts,
            tags=["extract", "store", "writeback", "vlm"],
        )
    )

    def ex_prepare(args: dict[str, Any]) -> dict[str, Any]:
        source = store.resolve(args["source"])
        driver = str(args.get("driver") or "in_band").lower()
        if driver not in ("in_band", "local"):
            raise TeeError(
                "extract_bad_driver",
                f"'{driver}' is not a driver.",
                fix='Use "in_band" (you read the media) or "local" (TEE reads it here).',
            )
        if driver == "local":
            if not vlm.LocalVlmDriver.available():
                raise TeeError(
                    "extract_local_unavailable",
                    "The local vision driver needs this machine's model shim, "
                    "which is not answering.",
                    fix="Start it (litellm --config ~/.claude/qwen-local/litellm.yaml), "
                    'or use driver "in_band" and read the files yourself.',
                )
            job = app.jobs.submit(
                f"extract {source['hash'][:8]} @local-vlm",
                lambda: _extract_locally(source),
                qos="batch",
                engine="qvl",
            )
            return {
                "job": job,
                "driver": "local",
                "note": "TEE is reading this media on the local vision model. "
                "Poll tee_job. The first call may pay a ~10s model swap.",
            }
        captions = {
            fact.get("ref")
            for fact in store.facts(source["hash"], kind="caption")
            if fact.get("ref")
        }
        packet = vlm.prepare_instructions(
            source, store.source_dir(source["hash"]), captioned=captions
        )
        if source["media_type"] == "audio":
            packet["guidance"] = audio_lane.REQUIREMENTS_PROMPT
        # A47 P3: each driver line now says HOW to invoke it. This block
        # used to advertise `local_vlm_driver: "available (free,
        # on-machine)"` while NO code path could invoke it - a sign on a
        # door with no door behind it, and the reason a blind host
        # reasonably concluded TEE offered no vision.
        packet["drivers"] = {
            "in_band": {
                "how": "read the paths above yourself, write back via ex_store_facts",
                "available": True,
                "note": "the default and the cheapest - if you CAN read media, do this",
            },
            "local": {
                "how": 'call ex_prepare again with {"driver": "local"}',
                "available": vlm.LocalVlmDriver.available(),
                "note": "TEE reads the media on this machine's vision model and "
                "stores the facts itself. For hosts that cannot read images.",
            },
            "api": {
                "how": "set ANTHROPIC_API_KEY; extraction runs off-session",
                "available": vlm.ApiDriver.available(),
                "note": "off-machine and metered",
            },
        }
        return packet

    def _extract_locally(source: dict[str, Any]) -> dict[str, Any]:
        """Run the local vision driver over a source AS THE JOB.

        The in-band channel asks the host to read the media. A host that
        cannot read media has no move: `ApiDriver` needs a cloud key, which
        defeats running locally. This is the third door - TEE looks, TEE
        stores, the host gets facts.
        """
        driver = vlm.LocalVlmDriver()
        paths = [Path(p) for p in source["paths"]]
        media_type = source["media_type"]
        facts: list[dict[str, Any]] = []
        for path in paths:
            if not path.is_file():
                continue
            if media_type == "document":
                try:
                    payload = driver.extract_document_page(path, vlm._PLAN_SCHEMA_HINT)
                    facts.append({"kind": "plan", "ref": path.name, **payload})
                    continue
                except Exception:
                    pass  # fall through to a caption rather than losing the page
            facts.append({"kind": "caption", "ref": path.name, "text": driver.caption_image(path)})
        if not facts:
            raise TeeError(
                "extract_local_empty",
                "The local driver read nothing from this source.",
                fix="Check the source has readable image files.",
            )
        stored = store.store_facts(
            source["hash"],
            f"vlm-{media_type}",
            "1",
            facts,
            provenance={
                "driver": "local",
                "model": driver.model,
                "off_machine_calls": 0,
                "note": "TEE read this media on the local vision model; the host "
                "never opened the files. Descriptions, not the pixels.",
            },
        )
        return {
            "ok": True,
            "driver": "local",
            "source": source["hash"][:8],
            "facts_stored": stored,
            "kinds": sorted({f["kind"] for f in facts}),
            "provided_by": f"{driver.model} (local)",
            "off_machine_calls": 0,
            "note": "Facts extracted by TEE, not by you. Query them with "
            "ex_facts / ex_search as usual.",
        }

    reg.register(
        VirtualTool(
            name="ex_prepare",
            description=(
                "Extraction packet for one source: file paths to read "
                "yourself, guidance on what to transcribe (never measure "
                "pixels), the plan schema, and how to write back via "
                "ex_store_facts. CANNOT read media yourself? Pass driver: "
                '"local" and TEE reads it here on this machine\'s vision '
                "model and stores the facts for you (async - poll tee_job)."
            ),
            schema={
                "type": "object",
                "properties": {
                    "source": {"type": "string"},
                    "driver": {
                        "type": "string",
                        "enum": ["in_band", "local"],
                        "description": "in_band (default, you read the files) or "
                        '"local" (TEE reads them on this machine).',
                    },
                },
                "required": ["source"],
            },
            handler=ex_prepare,
            tags=["extract", "prepare", "vlm", "instructions"],
        )
    )

    # -- registration (7.6) ------------------------------------------------

    def ex_register(args: dict[str, Any]) -> dict[str, Any]:
        op = args["op"]
        if op == "datum":
            registry.set_site_datum(
                float(args["lat"]), float(args["lon"]), float(args.get("h") or 0)
            )
            return {"datum": {"lat": args["lat"], "lon": args["lon"]}}
        if op == "frame":
            registry.add_frame(args["frame_id"], args.get("kind") or "custom")
            return {"frames": sorted(registry.frames())}
        if op == "transform":
            record = registry.add_transform(
                args["from_frame"],
                args["to_frame"],
                args["params"],
                method=args.get("method") or "manual",
                accuracy_m=float(args.get("accuracy_m") or 0.0),
                tier=args.get("tier") or "derived",
            )
            return {"transform": {k: record[k] for k in ("id", "from", "to", "accuracy_m")}}
        if op == "fit":
            fit = fit_similarity(
                [tuple(p) for p in args["src_points"]],
                [tuple(p) for p in args["dst_points"]],
                fix_scale=args.get("fix_scale"),
            )
            conflict = None
            if args.get("fix_scale") and scale_conflict(fit["free_scale"], args["fix_scale"]):
                conflict = {
                    "kind": "conflict",
                    "fact_a": "declared units",
                    "fact_b": "footprint fit",
                    "delta_m": None,
                    "free_scale": fit["free_scale"],
                    "pinned_scale": args["fix_scale"],
                    "winner": "unresolved",
                    "disposition": "free-fit scale deviates >2% from declared "
                    "units - check drawing units or footprint identity",
                }
            record = registry.add_transform(
                args["from_frame"],
                args["to_frame"],
                fit["params"],
                method="similarity_fit",
                accuracy_m=fit["rmse_m"],
                tier=args.get("tier") or "satellite",
                residual={"rmse_m": fit["rmse_m"], "max_m": fit["max_m"], "n": fit["n"]},
            )
            out = {"transform": record["id"], "fit": fit}
            if conflict:
                out["units_conflict"] = conflict
            return out
        raise TeeError(
            "bad_op",
            f"Unknown op '{op}'.",
            fix="Use op = datum | frame | transform | fit.",
        )

    reg.register(
        VirtualTool(
            name="ex_register",
            description=(
                "Frame registry operations: set the site datum (lat/lon), "
                "add a frame, register a transform, or fit one from matched "
                "point pairs (constrained similarity; a free-scale deviation "
                ">2% from declared units raises a units conflict instead of "
                "silently recalibrating)."
            ),
            schema={
                "type": "object",
                "properties": {
                    "op": {"type": "string"},
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                    "h": {"type": "number"},
                    "frame_id": {"type": "string"},
                    "kind": {"type": "string"},
                    "from_frame": {"type": "string"},
                    "to_frame": {"type": "string"},
                    "params": {"type": "array"},
                    "method": {"type": "string"},
                    "accuracy_m": {"type": "number"},
                    "tier": {"type": "string"},
                    "src_points": {"type": "array"},
                    "dst_points": {"type": "array"},
                    "fix_scale": {"type": "number"},
                },
                "required": ["op"],
            },
            handler=ex_register,
            tags=["extract", "frames", "registration", "transform", "datum", "fit"],
        )
    )

    return store, registry


def _extract_ifc(path: Path, frame: str) -> list[dict[str, Any]]:
    import ifcopenshell

    model = ifcopenshell.open(str(path))
    facts: list[dict[str, Any]] = [{"kind": "bim", "frame": frame, "schema": model.schema}]
    for cls in ("IfcWall", "IfcDoor", "IfcWindow", "IfcSpace", "IfcBuildingStorey"):
        entities = model.by_type(cls)
        if entities:
            facts.append(
                {
                    "kind": "bim_summary",
                    "frame": frame,
                    "tier": "dimension_text",
                    "class": cls,
                    "count": len(entities),
                    "names": [e.Name for e in entities[:20] if e.Name],
                }
            )
    return facts


def _media_view_backend(store: ExtractStore):
    """Backend for the kernel tee_media tool: budgeted pixels on demand."""

    def view(source_ref: str, region, timestamp, token_budget: int):
        source = store.resolve(source_ref)
        media_type = source["media_type"]
        if media_type == "image":
            return images.budgeted_jpeg(Path(source["paths"][0]), token_budget, region)
        if media_type == "video":
            if timestamp is None:
                raise TeeError(
                    "need_timestamp",
                    "Video views need a timestamp.",
                    fix="Pick a pts_time from the keyframe facts (ex_facts).",
                )
            out = store.derived_dir(source["hash"], "video") / "fetch.jpg"
            video.fetch_frame(Path(source["paths"][0]), float(timestamp), out)
            return images.budgeted_jpeg(out, token_budget, region)
        if media_type == "document":
            import pypdfium2 as pdfium

            pdf = pdfium.PdfDocument(source["paths"][0])
            page_index = int(timestamp or 0)
            page = pdf[min(page_index, len(pdf) - 1)]
            bitmap = page.render(scale=2.0)
            out = store.derived_dir(source["hash"], "pages") / f"page{page_index}.jpg"
            bitmap.to_pil().convert("RGB").save(out, "JPEG", quality=85)
            return images.budgeted_jpeg(out, token_budget, region)
        raise TeeError(
            "no_view",
            f"'{media_type}' sources have no pixel view.",
            fix="Audio/CAD content is served as facts (ex_facts / ex_search).",
        )

    return view
