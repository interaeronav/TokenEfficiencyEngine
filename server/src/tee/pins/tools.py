"""TEE Pins virtual tools (pin_*).

A pin is a marker actor that stands where something should eventually go, with
its whole record - id, name, category, notes, wishlist, and what finally
filled it - stored in the actor's own tags. `pin_fill` closes the loop:
wishlist terms -> asset search -> the owner's pick -> import at the pin, with
the chosen key written back onto the pin.

`pin_export` / `pin_import` exist because pins are AUTHORED state living in a
GENERATED artifact: a level rebuilt from a project's data files would drop
them. The file is a seed and a backup, not a second source of truth - the tags
in the level stay authoritative, and an export is a snapshot of them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tee.assets.envelopes import envelope_for, load_envelopes
from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.pins import model, program

DEFAULT_NAMESPACE = "tee_pin"


#: Bumped only when the on-disk shape changes incompatibly.
EXPORT_VERSION = 1

#: Fields carried through an export, in file order.
EXPORT_FIELDS = (
    "id",
    "name",
    "category",
    "notes",
    "wishlist",
    "asset_class",
    "target_dims",
    "asset",
)


def _fill_label(pin_id: str) -> str:
    return program.FILL_LABEL_PREFIX + pin_id


def register_pin_tools(app, project_root: Path | str) -> None:
    config = getattr(app.config, "pins", {}) or {}
    namespace = str(config.get("namespace") or DEFAULT_NAMESPACE)
    # A68: pins are Unreal actor tags, so the lane is Unreal - never "whichever
    # adapter came first". _adapter_name refuses anything else by name.
    default_adapter = "unreal"

    def _adapter_name(args: dict[str, Any]) -> str:
        name = str(args.get("adapter") or default_adapter)
        if name != "unreal":
            raise TeeError(
                "pins_unsupported_adapter",
                f"Pins are an Unreal lane; adapter {name!r} has no actor tags.",
                fix="Call with adapter='unreal' against a running editor.",
            )
        return name

    def _dcc(args: dict[str, Any]):
        return app.adapter(_adapter_name(args))

    # -- reads -------------------------------------------------------------

    def _read(args: dict[str, Any]) -> list[dict[str, Any]]:
        """Every pin in the level, decoded, in one editor dispatch."""
        data = _dcc(args).editor_python(program.read_program(namespace), "TEE: read pins")
        pins = []
        for row in data.get("pins", []):
            decoded = model.decode_tags(namespace, row.get("tags", []))
            if decoded is None:
                continue
            decoded["position_m"] = row["location_m"]
            decoded["yaw"] = row["yaw"]
            decoded["actor_label"] = row["label"]
            decoded["fill_present"] = bool(row.get("fill_present"))
            pins.append(decoded)
        pins.sort(key=lambda p: p.get("id", ""))
        return pins

    def _one(args: dict[str, Any], pin_id: str) -> dict[str, Any]:
        pin_id = model.validate_id(pin_id)
        pins = _read(args)
        for pin in pins:
            if pin.get("id") == pin_id:
                return pin
        known = ", ".join(p.get("id", "?") for p in pins[:10]) or "none yet"
        raise TeeError(
            "unknown_pin",
            f"No pin {pin_id!r} in the level.",
            fix=f"Pins present: {known}. Create it with pin_set.",
        )

    def _row(pin: dict[str, Any]) -> dict[str, Any]:
        """Compact list row: what a pin IS, plus whether it is filled."""
        out = {
            "id": pin.get("id"),
            "name": pin.get("name"),
            "cat": pin.get("category"),
            "pos_m": pin.get("position_m"),
            "filled": pin.get("asset") or None,
        }
        if not out["filled"]:
            out["wishlist"] = pin.get("wishlist", [])
        elif not pin.get("fill_present"):
            # The tags claim an asset, but nothing is standing there - a level
            # rebuilt from its data files loses the props, not the record.
            out["missing"] = True
        return {k: v for k, v in out.items() if v not in (None, [], False)}

    def pin_list(args):
        pins = _read(args)
        category = args.get("category")
        if category:
            pins = [p for p in pins if p.get("category") == str(category)]
        if args.get("empty_only"):
            pins = [p for p in pins if not p.get("asset")]
        return {
            "namespace": namespace,
            "count": len(pins),
            "pins": [_row(p) for p in pins],
        }

    def pin_show(args):
        pin = _one(args, str(args["id"]))
        return {"pin": pin}

    # -- writes ------------------------------------------------------------

    def pin_set(args):
        pin_id = model.validate_id(str(args["id"]))
        adapter = _adapter_name(args)
        existing = None
        for pin in _read(args):
            if pin.get("id") == pin_id:
                existing = pin
                break
        location = args.get("location")
        if existing is None and location is None:
            raise TeeError(
                "pin_needs_location",
                f"Pin {pin_id!r} does not exist yet, so it needs a location.",
                fix="Pass location=[x, y, z] in METRES (world space).",
            )
        updates = {
            "id": pin_id,
            "name": args.get("name"),
            "category": args.get("category"),
            "notes": args.get("notes"),
            "wishlist": args.get("wishlist"),
            "asset_class": args.get("asset_class"),
            "target_dims": args.get("target_dims"),
        }
        merged = model.merge(existing, updates)
        merged.setdefault("name", pin_id)
        tags = model.encode_tags(namespace, merged)
        location_cm = [float(v) * 100.0 for v in location] if location else None
        yaw = args.get("yaw")
        dcc = app.adapter(adapter)
        checkpoint = app.checkpoints.create(
            dcc, f"auto:pin:{pin_id}", app.cache(adapter).revision, lane=adapter
        )
        data = dcc.editor_python(
            program.upsert_program(
                namespace,
                pin_id,
                f"Pin_{pin_id}",
                tags,
                location_cm,
                float(yaw) if yaw is not None else None,
            ),
            f"TEE: pin {pin_id}",
        )
        if data.get("error") == "no_location":
            raise TeeError(
                "pin_needs_location",
                f"Pin {pin_id!r} does not exist yet, so it needs a location.",
                fix="Pass location=[x, y, z] in METRES (world space).",
            )
        if data.get("created"):
            # A marker that collides or ships is worse than no marker: it
            # blocks the player or turns up inside the delivered build.
            if "NO_COLLISION" not in str(data.get("collision", "")):
                raise TeeError(
                    "pin_marker_collides",
                    f"Pin {pin_id!r} spawned with collision "
                    f"{data.get('collision')!r}, not NO_COLLISION.",
                    fix="The marker mesh's collision profile refused to take; "
                    "report this with the value above before using the pin.",
                )
            if not data.get("editor_only"):
                raise TeeError(
                    "pin_marker_would_ship",
                    f"Pin {pin_id!r} is not marked editor-only.",
                    fix="is_editor_only_actor did not take on this engine "
                    "build; report it before relying on pins.",
                )
        if location is not None:
            want = float(location[2])
            got = float(data.get("marker_base_z_m", want))
            if abs(got - want) > 0.01:
                raise TeeError(
                    "pin_misplaced",
                    f"Pin {pin_id!r} marker base landed at z={got} m, not {want} m.",
                    fix="The marker mesh bounds are not what TEE assumed; "
                    "report this with the numbers above.",
                )
        app.cache(adapter).resync(dcc)
        return {
            "pin": pin_id,
            "created": bool(data.get("created")),
            "checkpoint": checkpoint.id,
            "position_m": data.get("location_m"),
            "tags": len(tags),
            **app.cache(adapter).stamp(),
        }

    def pin_remove(args):
        pin = _one(args, str(args["id"]))
        adapter = _adapter_name(args)
        dcc = app.adapter(adapter)
        drop_fill = bool(args.get("remove_asset"))
        data = dcc.editor_python(
            program.remove_program(namespace, pin["id"], _fill_label(pin["id"]), drop_fill),
            f"TEE: remove pin {pin['id']}",
        )
        app.cache(adapter).resync(dcc)
        return {
            "pin": pin["id"],
            "removed": bool(data.get("removed")),
            "removed_asset": data.get("removed_fill"),
            **app.cache(adapter).stamp(),
        }

    # -- durability: a snapshot the level cannot lose ----------------------

    def _pin_file(args: dict[str, Any]) -> Path:
        raw = str(args.get("path") or config.get("file") or "pins.json")
        path = Path(raw).expanduser()
        return path if path.is_absolute() else Path(project_root) / path

    def pin_export(args):
        pins = _read(args)
        path = _pin_file(args)
        rows = []
        for pin in pins:
            row = {
                field: pin[field] for field in EXPORT_FIELDS if pin.get(field) not in (None, "", [])
            }
            row["position_m"] = pin["position_m"]
            if pin.get("yaw"):
                row["yaw"] = pin["yaw"]
            rows.append(row)
        document = {
            "version": EXPORT_VERSION,
            "namespace": namespace,
            "pins": sorted(rows, key=lambda r: r.get("id", "")),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        # Stable ordering, trailing newline: this file is meant to live in a
        # repo, and a snapshot that churns its own diff is useless there.
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n")
        return {"path": str(path), "pins": len(rows), "namespace": namespace}

    def pin_import(args):
        path = _pin_file(args)
        if not path.exists():
            raise TeeError(
                "pin_file_missing",
                f"No pin file at {path}.",
                fix="Write one with pin_export, or pass path= to point at it.",
            )
        try:
            document = json.loads(path.read_text())
        except (OSError, ValueError) as exc:
            raise TeeError(
                "pin_file_unreadable", f"{path}: {exc}", fix="Fix or regenerate the file."
            ) from exc
        version = document.get("version")
        if version != EXPORT_VERSION:
            raise TeeError(
                "pin_file_version",
                f"{path} is version {version!r}; this TEE writes {EXPORT_VERSION}.",
                fix="Re-export from a level that already has the pins, or "
                "hand-edit the version if you know the shapes match.",
            )
        file_ns = document.get("namespace")
        if file_ns and file_ns != namespace:
            raise TeeError(
                "pin_namespace_mismatch",
                f"{path} holds {file_ns!r} pins but this project uses {namespace!r}.",
                fix="Set [pins] namespace in .tee/config.toml to match the "
                "file, or export afresh under this project's namespace.",
            )
        wanted = document.get("pins") or []
        present = {pin["id"]: pin for pin in _read(args)}
        restored, updated, filled, unchanged = [], [], [], []
        for row in wanted:
            pin_id = model.validate_id(str(row["id"]))
            (updated if pin_id in present else restored).append(pin_id)
            pin_set(
                {
                    **{f: row[f] for f in EXPORT_FIELDS if f in row and f != "asset"},
                    "location": row.get("position_m"),
                    "yaw": row.get("yaw"),
                    "adapter": args.get("adapter"),
                }
            )
        if args.get("fill", True):
            # Only what is genuinely missing: re-importing a prop that is
            # already standing costs a download-and-place for no change.
            for pin in _read(args):
                row = next((r for r in wanted if r.get("id") == pin["id"]), None)
                if not row or not row.get("asset"):
                    continue
                if pin.get("fill_present"):
                    unchanged.append(pin["id"])
                    continue
                pin_fill({"id": pin["id"], "pick": row["asset"], "adapter": args.get("adapter")})
                filled.append(pin["id"])
        extra = sorted(set(present) - {str(r.get("id")) for r in wanted})
        out = {
            "path": str(path),
            "restored": sorted(restored),
            "updated": sorted(updated),
            "filled": sorted(filled),
        }
        if unchanged:
            out["already_standing"] = sorted(unchanged)
        if extra:
            out["in_level_not_in_file"] = extra
        return out

    # -- the loop: wishlist -> shortlist -> import -> record ---------------

    def _scale_hint(pin: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
        """Where the import gets its sense of scale from, in precedence order.

        as_search labels every hit 'model', and 'model' has no dimension
        envelope, so an import with no semantic class and no target dims has
        nothing to judge scale against and is rejected. A pin therefore
        carries that judgement itself."""
        dims = args.get("target_dims") or pin.get("target_dims")
        if dims:
            return {"target_dims": [float(v) for v in dims], "asset_class": None}
        for candidate in (args.get("asset_class"), pin.get("asset_class"), pin.get("category")):
            if candidate and envelope_for(str(candidate)):
                return {"target_dims": None, "asset_class": str(candidate)}
        classes = ", ".join(sorted(load_envelopes()))
        raise TeeError(
            "pin_no_scale_reference",
            f"Pin {pin['id']!r} has nothing to judge the import's scale "
            f"against (category {pin.get('category')!r} is not a known class).",
            fix=f"Give the pin an asset_class from: {classes}. Or pass "
            "target_dims=[x, y, z] in metres, on the pin or on this call.",
        )

    def pin_fill(args):
        pin = _one(args, str(args["id"]))
        adapter = _adapter_name(args)
        terms = args.get("wishlist") or pin.get("wishlist") or []
        pick = args.get("pick")

        if not pick:
            if not terms:
                raise TeeError(
                    "pin_no_wishlist",
                    f"Pin {pin['id']!r} has no wishlist to search for.",
                    fix="pin_set(id=..., wishlist=['woven basket', 'clay pot']) "
                    "first, or call pin_fill with wishlist=[...] for a one-off.",
                )
            limit = int(args.get("limit") or 4)
            shortlist: list[dict[str, Any]] = []
            seen: set[str] = set()
            for term in terms:
                found = app.registry.call(
                    "as_search",
                    {"query": str(term), "asset_class": "model", "limit": limit},
                )
                for row in (found.get("results") or {}).get("model", []):
                    if row["id"] in seen:
                        continue
                    seen.add(row["id"])
                    entry = {
                        "asset": row["id"],
                        "name": row.get("name"),
                        "for_term": term,
                        "license": row.get("license"),
                    }
                    if row.get("dims_m"):
                        entry["dims_m"] = row["dims_m"]
                    if row.get("tris"):
                        entry["tris"] = row["tris"]
                    shortlist.append(entry)
            return {
                "pin": pin["id"],
                "at_m": pin["position_m"],
                "searched": terms,
                "shortlist": shortlist,
                "next": f"pin_fill(id='{pin['id']}', pick='<asset>') places it at the pin.",
            }

        scale = _scale_hint(pin, args)
        label = _fill_label(pin["id"])
        # Clear by the LABEL CONVENTION, not by the pin's own record: a pin
        # whose marker was recreated has no memory of what it holds, and the
        # spot would end up with two props stacked on it.
        dropped = app.adapter(adapter).editor_python(
            program.clear_fill_program(label),
            f"TEE: clear pin {pin['id']}",
        )
        replaced = pin.get("asset") if dropped.get("removed") else None
        imported = app.registry.call(
            "as_import",
            {
                "asset": str(pick),
                "adapter": adapter,
                "location": pin["position_m"],
                "name": label,
                **({"asset_class": scale["asset_class"]} if scale["asset_class"] else {}),
                **({"target_dims": scale["target_dims"]} if scale["target_dims"] else {}),
            },
        )
        created = (imported.get("created") or [None])[0]
        if created and pin.get("yaw"):
            # TEE's rotation triple is [pitch, yaw, roll], matching Epic's
            # converter - a pin's facing is the MIDDLE component.
            app.run_batch(
                adapter,
                [
                    {
                        "op": "set",
                        "id": created,
                        "props": {
                            # batch transforms are raw UE units (cm); the
                            # importer's own `location` is metres
                            "location": [v * 100.0 for v in pin["position_m"]],
                            "rotation": [0.0, pin["yaw"], 0.0],
                        },
                    }
                ],
                label=f"pin {pin['id']} facing",
            )
        merged = model.merge(pin, {"asset": str(pick), "filled_by": label})
        app.adapter(adapter).editor_python(
            program.upsert_program(
                namespace,
                pin["id"],
                f"Pin_{pin['id']}",
                model.encode_tags(namespace, merged),
                None,
                None,
            ),
            f"TEE: record fill on pin {pin['id']}",
        )
        app.cache(adapter).resync(app.adapter(adapter))
        return {
            "pin": pin["id"],
            "filled_with": str(pick),
            "replaced": replaced,
            "entity": created,
            "actor_label": label,
            "at_m": pin["position_m"],
            "scale_band": imported.get("scale_band"),
            "dims_m": (imported.get("verify") or {}).get("read_back"),
            "license": imported.get("license"),
            "checkpoint": imported.get("checkpoint"),
        }

    # -- registration ------------------------------------------------------

    adapter_prop = {"type": "string"}
    tools = [
        VirtualTool(
            "pin_set",
            "Create or update a pin: a small editor-only marker actor whose "
            "TAGS carry its record (id, name, category, notes, wishlist). "
            "Upsert - omitted fields keep their value; location is METRES "
            "at the thing's base. Stripped from cooked builds; never "
            "collides.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "notes": {"type": "string"},
                    "wishlist": {"type": "array"},
                    "asset_class": {"type": "string"},
                    "target_dims": {"type": "array"},
                    "location": {"type": "array"},
                    "yaw": {"type": "number"},
                    "adapter": adapter_prop,
                },
                "required": ["id"],
            },
            pin_set,
            tags=["pins", "marker", "annotate", "wishlist", "unreal"],
            examples=[
                {
                    "id": "market-03",
                    "name": "Market stall 3",
                    "category": "table",
                    "wishlist": ["market stall table", "wooden trestle"],
                    "location": [10.7, 15.1, 0.0],
                }
            ],
        ),
        VirtualTool(
            "pin_list",
            "List the pins in the level as compact rows (id, name, category, "
            "position, and what fills it or its wishlist). Filter with "
            "category= or empty_only=true.",
            {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "empty_only": {"type": "boolean"},
                    "adapter": adapter_prop,
                },
            },
            pin_list,
            tags=["pins", "list", "markers", "unreal"],
        ),
        VirtualTool(
            "pin_show",
            "One pin's full record read back from its actor tags, with its "
            "world position and what currently fills it.",
            {
                "type": "object",
                "properties": {"id": {"type": "string"}, "adapter": adapter_prop},
                "required": ["id"],
            },
            pin_show,
            tags=["pins", "detail", "unreal"],
        ),
        VirtualTool(
            "pin_fill",
            "Populate a pin from its wishlist. Without pick=: searches the "
            "asset backends and answers a shortlist. With pick='source:id': "
            "imports that asset AT the pin, facing its yaw, replacing what "
            "it held, recording the choice on the pin's tags.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "pick": {"type": "string"},
                    "wishlist": {"type": "array"},
                    "asset_class": {"type": "string"},
                    "target_dims": {"type": "array"},
                    "limit": {"type": "integer"},
                    "adapter": adapter_prop,
                },
                "required": ["id"],
            },
            pin_fill,
            tags=["pins", "populate", "import", "polyhaven", "unreal"],
        ),
        VirtualTool(
            "pin_export",
            "Write every pin in the level to a JSON file (default "
            "<project>/pins.json, or [pins].file) - id, record, position and "
            "yaw, sorted so the diff is stable. Pins are authored state in a "
            "generated level; this is the copy a rebuild cannot lose.",
            {
                "type": "object",
                "properties": {"path": {"type": "string"}, "adapter": adapter_prop},
            },
            pin_export,
            tags=["pins", "export", "backup", "unreal"],
        ),
        VirtualTool(
            "pin_import",
            "Replay a pin file into the level: every pin is upserted (marker, "
            "position, tags) and, unless fill=false, any recorded asset that "
            "is not actually standing there is imported again. Reports what "
            "was restored, what was already there, and any pin in the level "
            "that the file does not mention.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "fill": {"type": "boolean"},
                    "adapter": adapter_prop,
                },
            },
            pin_import,
            tags=["pins", "import", "restore", "unreal"],
        ),
        VirtualTool(
            "pin_remove",
            "Delete a pin marker. remove_asset=true also deletes whatever the "
            "pin placed; by default the placed asset stays.",
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "remove_asset": {"type": "boolean"},
                    "adapter": adapter_prop,
                },
                "required": ["id"],
            },
            pin_remove,
            tags=["pins", "delete", "unreal"],
        ),
    ]
    for tool in tools:
        app.registry.register(tool)
