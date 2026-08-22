"""TEE UEFN virtual tools (uefn_* + export_for_uefn)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool
from tee.uefn import export as export_mod
from tee.uefn import templates as templates_mod
from tee.uefn.adapter import FakeUefn, UefnAdapter, luf_to_xyz, xyz_to_luf
from tee.uefn.digest import digest_diff, load_digest, parse_digest
from tee.uefn.lint import explain_error, lint


def register_uefn_tools(
    app, project_root: Path | str, *, uefn: UefnAdapter | None = None
) -> None:
    reg = app.registry
    adapter = uefn or FakeUefn(editor_present=False)  # offline until probed live
    digests: dict[str, dict[str, Any]] = {}
    state = {"current": None}

    def _digest(args: dict[str, Any]) -> dict[str, Any]:
        version = args.get("version") or state["current"]
        if version is None or version not in digests:
            raise TeeError(
                "no_digest",
                "No Verse digest loaded.",
                fix="Load one with uefn_digest_load(path=...) from the local "
                "UEFN install (digests are per-install, never bundled).",
            )
        return digests[version]

    def uefn_status(args):
        payload = adapter.probe().to_payload()
        payload["loaded_digests"] = sorted(digests)
        return payload

    def uefn_digest_load(args):
        if args.get("text"):
            digest = parse_digest(str(args["text"]), version=str(args.get("version", "inline")))
        else:
            digest = load_digest(Path(str(args["path"])), version=args.get("version"))
        digests[digest["version"]] = digest
        state["current"] = digest["version"]
        classes = sum(len(m["classes"]) for m in digest["modules"].values())
        members = sum(
            len(c["members"])
            for m in digest["modules"].values()
            for c in m["classes"].values()
        )
        return {
            "version": digest["version"],
            "modules": len(digest["modules"]),
            "classes": classes,
            "members": members,
        }

    def uefn_digest_diff(args):
        old = digests.get(str(args["from"]))
        new = digests.get(str(args["to"]))
        if old is None or new is None:
            raise TeeError(
                "no_digest",
                f"Both versions must be loaded first (have: {sorted(digests)}).",
                fix="uefn_digest_load each version, then diff.",
            )
        return digest_diff(old, new)

    def uefn_lint(args):
        return lint(str(args["code"]), _digest(args))

    def uefn_error(args):
        return explain_error(str(args["code"]))

    def uefn_template(args):
        if not args.get("template"):
            return {"templates": templates_mod.list_templates()}
        return templates_mod.instantiate(
            str(args["template"]), _digest(args), name=str(args.get("name", "my_device"))
        )

    def uefn_entities(args):
        return {"entities": adapter.entities()}

    def uefn_entity_batch(args):
        return adapter.entity_batch(args["ops"])

    def uefn_devices(args):
        return {"devices": adapter.device_catalog(str(args["query"]),
                                                  limit=int(args.get("limit", 5)))}

    def uefn_place_device(args):
        return adapter.place_device(str(args["device"]), args.get("xyz") or [0, 0, 0])

    def uefn_compile(args):
        return adapter.verse_compile()

    def export_preflight(args):
        return export_mod.validate_export(args["asset"])

    def export_for_uefn(args):
        report = export_mod.validate_export(args["asset"]) if args.get("asset") else None
        if report is not None and not report["export_ready"]:
            return {**report, "exported": False,
                    "note": "fix the violations, then re-run with entity ids"}
        if not args.get("ids"):
            return report or {"note": "pass asset (preflight) and/or ids (export)"}
        adapter_name = str(args.get("adapter") or "blender")
        blender = app.adapters.get(adapter_name)
        if blender is None or not hasattr(blender, "execute_python"):
            raise TeeError(
                "unsupported_adapter",
                f"Live export needs the Blender adapter (got '{adapter_name}').",
            )
        out_path = str(
            Path(project_root).resolve() / ".tee" / "exports" /
            f"{args.get('name', 'asset')}.fbx"
        )
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        program = export_mod.export_program(
            [str(i) for i in args["ids"]], out_path,
            autogen_lods=bool(args.get("autogen_lods", True)),
        )
        result = blender.execute_python(program, timeout=300)
        payload = result.get("result", result)
        if report is not None:
            payload["preflight"] = report
        return payload

    def uefn_pack_channels(args):
        out = Path(project_root) / ".tee" / "exports" / str(
            args.get("name", "packed_srm.png")
        )
        return export_mod.pack_channels(
            Path(args["specular"]) if args.get("specular") else None,
            Path(args["metallic"]) if args.get("metallic") else None,
            Path(args["roughness"]) if args.get("roughness") else None,
            out,
            size=int(args.get("size", 1024)),
        )

    def uefn_coords(args):
        if args.get("luf") is not None:
            return {"xyz": luf_to_xyz(args["luf"])}
        if args.get("xyz") is not None:
            return {"luf": xyz_to_luf(args["xyz"])}
        raise TeeError("bad_args", "Pass luf=[l,u,f] or xyz=[x,y,z].")

    def uefn_analytics(args):
        from tee.assets.http import CatalogCache

        code = str(args["island"])
        cache = CatalogCache(Path(project_root) / ".tee" / "uefn_cache")
        interval = str(args.get("interval", "day"))
        data, _info = cache.fetch_json(
            f"island-{code}-{interval}",
            f"https://api.fortnite.com/ecosystem/v1/islands/{code}/metrics/{interval}",
            ttl_s=6 * 3600,
        )
        out: dict[str, Any] = {"island": code, "interval": interval}
        for metric, series in data.items():
            if not isinstance(series, list):
                continue
            values = [p.get("value") for p in series if p.get("value") is not None]
            if values:
                out[metric] = {
                    "latest": values[-1],
                    "mean": round(sum(values) / len(values), 2),
                    "points": len(values),
                }
        if len(out) == 2:
            out["note"] = "no non-null datapoints in the window (small islands "
            "report sparsely)"
        return out

    tools = [
        VirtualTool(
            "uefn_status",
            "UEFN capability probe: offline (digest/lint/templates/export "
            "preflight work everywhere) vs gated (Beta Access toggles "
            "missing) vs live (Epic MCP toolsets reachable), with the exact "
            "remediation.",
            {"type": "object", "properties": {}},
            uefn_status,
            tags=["uefn", "status", "probe", "capability"],
        ),
        VirtualTool(
            "uefn_digest_load",
            "Parse a Verse API digest (*.digest.verse) from the LOCAL UEFN "
            "install into version-keyed facts. Digests are per-install and "
            "Epic-copyrighted - parsed locally, never redistributed.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}, "text": {"type": "string"},
                    "version": {"type": "string"},
                },
            },
            uefn_digest_load,
            tags=["uefn", "verse", "digest", "api"],
        ),
        VirtualTool(
            "uefn_digest_diff",
            "Drift facts between two loaded digest versions (added/removed "
            "members, changed effects) - the firewall for the 23.20/30.00/"
            "42.00 class of breaks.",
            {
                "type": "object",
                "properties": {"from": {"type": "string"}, "to": {"type": "string"}},
                "required": ["from", "to"],
            },
            uefn_digest_diff,
            tags=["uefn", "verse", "digest", "diff", "drift"],
        ),
        VirtualTool(
            "uefn_lint",
            "Digest-grounded Verse lint: every member access, effect "
            "specifier and event subscription checked against the loaded "
            "digest, with known-drift fixes (<varies>, GetPassengers). "
            "Catches the dominant hallucination class offline; NOT a "
            "compile (that needs the live editor).",
            {
                "type": "object",
                "properties": {"code": {"type": "string"}, "version": {"type": "string"}},
                "required": ["code"],
            },
            uefn_lint,
            tags=["uefn", "verse", "lint", "check", "hallucination"],
        ),
        VirtualTool(
            "uefn_error",
            "One-line fix for a Verse compiler error code (incl. the "
            "stale-validation false-positive class).",
            {"type": "object", "properties": {"code": {"type": "string"}},
             "required": ["code"]},
            uefn_error,
            tags=["uefn", "verse", "error", "fix"],
        ),
        VirtualTool(
            "uefn_template",
            "Digest-validated Verse templates (device subscribe, weak_map "
            "persistence, Scene Graph component, race concurrency) - "
            "symbols verified against the loaded digest before emission; no "
            "template call, lists them.",
            {
                "type": "object",
                "properties": {
                    "template": {"type": "string"}, "name": {"type": "string"},
                    "version": {"type": "string"},
                },
            },
            uefn_template,
            tags=["uefn", "verse", "template", "codegen"],
        ),
        VirtualTool(
            "uefn_entities",
            "Scene Graph entities (the UE6 object model) with positions "
            "normalized to UE XYZ - the LUF translation bug class is fixed "
            "at this boundary.",
            {"type": "object", "properties": {}},
            uefn_entities,
            tags=["uefn", "scene-graph", "entities", "list"],
        ),
        VirtualTool(
            "uefn_entity_batch",
            "Typed Scene Graph batch: create_entity/set_transform/"
            "add_component/delete_entity, positions in UE XYZ.",
            {"type": "object", "properties": {"ops": {"type": "array"}},
             "required": ["ops"]},
            uefn_entity_batch,
            tags=["uefn", "scene-graph", "batch", "create"],
        ),
        VirtualTool(
            "uefn_devices",
            "Device catalog search answered from the LOCAL index - never a "
            "forwarded 4,698-row dump.",
            {"type": "object", "properties": {"query": {"type": "string"},
                                              "limit": {"type": "integer"}},
             "required": ["query"]},
            uefn_devices,
            tags=["uefn", "devices", "catalog", "search"],
        ),
        VirtualTool(
            "uefn_place_device",
            "Place a Creative device (parallel, eventually-legacy family "
            "next to Scene Graph entities) at a UE XYZ position.",
            {"type": "object", "properties": {"device": {"type": "string"},
                                              "xyz": {"type": "array"}},
             "required": ["device"]},
            uefn_place_device,
            tags=["uefn", "devices", "place"],
        ),
        VirtualTool(
            "uefn_compile",
            "Compile the project's Verse via the editor toolset (live "
            "editor only); structured diagnostics come back compactly.",
            {"type": "object", "properties": {}},
            uefn_compile,
            tags=["uefn", "verse", "compile", "diagnostics"],
        ),
        VirtualTool(
            "export_preflight",
            "Pure preflight of an asset description against the encoded "
            "Fortnite-Ready budget tables (LOD0 caps by class/size, 3 LODs "
            "at -50%, power-of-two <=2K textures, UCX collision naming, "
            "applied transforms, baked materials) - every violation with "
            "the exact fix.",
            {"type": "object", "properties": {"asset": {"type": "object"}},
             "required": ["asset"]},
            export_preflight,
            tags=["uefn", "export", "preflight", "budget", "validate"],
        ),
        VirtualTool(
            "export_for_uefn",
            "The Blender->UEFN lane: preflight (asset=), then live export "
            "(ids=) with LOD1/2 autogeneration at -50% steps and the "
            "Fortnite-ready FBX configuration (cm scale, Face smoothing).",
            {
                "type": "object",
                "properties": {
                    "asset": {"type": "object"}, "ids": {"type": "array"},
                    "name": {"type": "string"}, "autogen_lods": {"type": "boolean"},
                    "adapter": {"type": "string"},
                },
            },
            export_for_uefn,
            tags=["uefn", "export", "blender", "fbx", "lod"],
        ),
        VirtualTool(
            "uefn_pack_channels",
            "Pack the UEFN utility map: Specular=R, Metallic=G, Roughness=B "
            "(power-of-two output).",
            {
                "type": "object",
                "properties": {
                    "specular": {"type": "string"}, "metallic": {"type": "string"},
                    "roughness": {"type": "string"}, "size": {"type": "integer"},
                    "name": {"type": "string"},
                },
            },
            uefn_pack_channels,
            tags=["uefn", "textures", "pack", "channels"],
        ),
        VirtualTool(
            "uefn_coords",
            "LUF <-> UE XYZ conversion at the documented boundary (the UEFN "
            "MCP transform bug class, fixed server-side).",
            {"type": "object", "properties": {"luf": {"type": "array"},
                                              "xyz": {"type": "array"}}},
            uefn_coords,
            tags=["uefn", "coordinates", "luf", "transform"],
        ),
        VirtualTool(
            "uefn_analytics",
            "Island engagement from the public Fortnite Data API "
            "(unauthenticated): minutes played / per-player, compactly "
            "aggregated, TTL-cached.",
            {"type": "object", "properties": {"island": {"type": "string"},
                                              "interval": {"type": "string"}},
             "required": ["island"]},
            uefn_analytics,
            tags=["uefn", "analytics", "island", "metrics"],
        ),
    ]
    for tool in tools:
        reg.register(tool)
