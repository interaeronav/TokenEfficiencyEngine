"""Features: the part kernel's verbs, registered into the document by import.

`import partkiln.features` registers `create part` and one `create <kind>`
per feature builder (extrude, revolve, sweep, loft, hole, fillet, chamfer,
shell, draft, pattern, mirror, combine, split) plus the datums (plane, axis,
point), and it costs no OCP: every builder imports `partkiln.brep.*` inside
its function. The document imports this package lazily the first time a
`create` names a kind it does not know (document.py), so `import partkiln`
stays OCP-free and a P1 document never pays for it.

The other half of this module is the regen plumbing the document calls
back into: which features depend on a sketch, a parameter or another part
(`dependents`), and the rebuilds an edit triggers - `set` on a feature
(from that feature), `param_set` and `set sk:` (from the first feature that
uses what changed), `delete` (from the deleted index, refusing while
dependents exist unless `cascade`). Every one answers with Law 14's blast
radius: `{changed: [{feature, delta_mm3, faces}], unchanged, failed,
volume_mm3, fingerprint}` per part.
"""

from __future__ import annotations

from typing import Any

from partkiln.document import CommandError, Document, register_kind
from partkiln.features import (  # noqa: F401 - importing registers the builders and datum kinds
    combine_split,
    edge,
    extrude,
    hole,
    pattern,
    revolve,
    shell_draft,
    sweep_loft,
    workplane,
)
from partkiln.features.base import BUILDERS, Feature, get_part, r3
from partkiln.features.part import Part

FEATURE_KINDS = tuple(sorted(BUILDERS))


# --------------------------------------------------------------------------- create part


@register_kind("part")
def _k_part(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
    name = doc.new_name(args, "part", doc.parts)
    material = None
    if args.get("material") is not None:
        from partkiln.materials import resolve

        material = resolve(str(args["material"]))
    else:
        assumed["material"] = None
    part = Part(name, material)
    cached = doc._cache.get(name) if doc._cache else None
    if cached is not None:
        from partkiln.naming import NameTable

        part.shape = cached.get("shape")
        part.names = NameTable.from_dict(cached.get("names") or {})
        part.cached = part.shape is not None
    doc.parts[name] = part
    out: dict[str, Any] = {"id": f"part:{name}", "material": material, "features": 0}
    if part.cached:
        out["cached"] = True
    return out


# --------------------------------------------------------------------------- create <feature>


def _make_handler(kind: str) -> Any:
    def handler(doc: Document, args: dict[str, Any], assumed: dict[str, Any]) -> dict[str, Any]:
        props = {k: v for k, v in args.items() if k not in ("kind", "name", "id", "part")}
        if (
            kind == "combine"
            and "part" not in args
            and isinstance(args.get("bodies"), list | tuple)
            and args["bodies"]
        ):
            args = {**args, "part": args["bodies"][0]}
        if kind == "split" and "part" not in args and args.get("body") is not None:
            args = {**args, "part": args["body"]}
        part = get_part(doc, args, assumed)
        if part.consumed_by:
            raise CommandError(
                f"part {part.name} was consumed by combine in part {part.consumed_by}; edit that "
                "part, or recreate the combine with keep_tool: true.",
                code="pk_needs",
            )
        taken = {f.id: f for f in part.features}
        fid = doc.new_name(args, kind, taken)
        feature = Feature(fid, kind, props)
        if part.cached and part.shape is not None and not doc._cache_building:
            # Restored from a .brep (D3): the record is kept, the geometry is
            # the cached body; the first edit rebuilds from 0.
            feature.status = "cached"
            part.features.append(feature)
            return {"id": f"feat:{fid}", "kind": kind, "status": "cached"}
        details = part.add_feature(doc, feature, assumed)
        details["part"] = f"part:{part.name}"
        return details

    handler.__name__ = f"_k_{kind}"
    return handler


for _kind in FEATURE_KINDS:
    register_kind(_kind)(_make_handler(_kind))


# --------------------------------------------------------------------------- dependents


def _mentions(feature: Feature, fid: str) -> bool:
    if f"feat:{fid}" in feature.depends:
        return True
    for ref in feature.refs:
        if (
            ref == fid
            or ref.startswith(fid + ".")
            or ref.startswith(fid + ":")
            or ref == f"feat:{fid}"
        ):
            return True
        if "|" in ref and any(
            side.split("[", 1)[0].split(".", 1)[0] == fid for side in ref.split("|")
        ):
            return True
    for value in feature.args.values():
        if isinstance(value, str) and (
            value == fid or value.startswith(fid + ".") or value.startswith(fid + ":")
        ):
            return True
    return False


def dependents(doc: Document, entity_id: str) -> list[str]:
    """Ids that break if `entity_id` goes: features using a sketch, a feature's
    names, a part (combine), or a datum."""
    found: list[str] = []
    fid = entity_id[5:] if entity_id.startswith("feat:") else None
    for part in doc.parts.values():
        for i, feature in enumerate(part.features):
            if (
                entity_id in feature.depends
                or entity_id in feature.refs
                or (
                    fid is not None
                    and part.has_feature(fid)
                    and i > part.index_of(fid)
                    and _mentions(feature, fid)
                )
            ):
                found.append(f"feat:{feature.id}")
    if entity_id.startswith("part:"):
        name = entity_id[5:]
        for sk in doc.sketches.values():
            if sk.plane.startswith("on:") and len(doc.parts) == 1 and name in doc.parts:
                found.append(f"sk:{sk.name}")
    return sorted(set(found))


# --------------------------------------------------------------------------- regen hooks


def _regen_where(doc: Document, predicate: Any, assumed: dict[str, Any]) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    touched: list[str] = []
    for name in sorted(doc.parts):
        part = doc.parts[name]
        start = next((i for i, f in enumerate(part.features) if predicate(f)), None)
        if start is None:
            continue
        reports[f"part:{name}"] = part.regen(doc, start)
        touched.append(name)
    for name in touched:  # a combine in another part that used a regenerated part
        for other in sorted(doc.parts):
            if other in touched or f"part:{other}" in reports:
                continue
            part = doc.parts[other]
            start = next(
                (i for i, f in enumerate(part.features) if f"part:{name}" in f.depends), None
            )
            if start is not None:
                reports[f"part:{other}"] = part.regen(doc, start)
    return reports


def after_sketch_change(doc: Document, names: list[str], assumed: dict[str, Any]) -> dict[str, Any]:
    wanted = {f"sk:{n}" for n in names}
    return _regen_where(doc, lambda f: bool(f.depends & wanted), assumed)


def after_param_change(
    doc: Document, params: set[str], sketches: list[str], assumed: dict[str, Any]
) -> dict[str, Any]:
    wanted = {f"sk:{n}" for n in sketches}
    return _regen_where(
        doc, lambda f: bool(f.param_deps & params) or bool(f.depends & wanted), assumed
    )


# --------------------------------------------------------------------------- set / delete


def _locate(doc: Document, target: str) -> tuple[Part, Feature | None]:
    text = str(target)
    if text.startswith("part:"):
        part = doc.parts.get(text[5:])
        if part is None:
            raise CommandError(
                f"no part {text!r}. Parts: "
                f"{', '.join(f'part:{n}' for n in sorted(doc.parts)) or '(none)'}.",
                code="pk_ref_unknown",
            )
        return part, None
    fid = text[5:] if text.startswith("feat:") else text
    if not text.startswith("feat:") and fid in doc.parts:
        return doc.parts[fid], None
    owners = [p for p in doc.parts.values() if p.has_feature(fid)]
    if len(owners) > 1:
        raise CommandError(
            f"feature {fid!r} exists in parts {', '.join(sorted(p.name for p in owners))}; say "
            "which with part:<name>/feat:<id>.",
            code="pk_part_ambiguous",
        )
    if not owners:
        known = [f"part:{n}" for n in sorted(doc.parts)] + [
            f"feat:{f.id}" for p in doc.parts.values() for f in p.features
        ]
        raise CommandError(
            f"nothing to set on {target!r}. Settable ids: doc, sk:<sketch>, "
            f"{', '.join(known[:12]) or 'part:<name>'}.",
            code="pk_ref_unknown",
        )
    return owners[0], owners[0].feature(fid)


def set_target(
    doc: Document, target: str, props: dict[str, Any], assumed: dict[str, Any]
) -> dict[str, Any]:
    part, feature = _locate(doc, target)
    if not props:
        raise CommandError(
            f"set {target} needs props: any creation prop, suppressed, name"
            + (", material" if feature is None else "")
            + ".",
            code="pk_needs",
        )
    if feature is None:
        return _set_part(doc, part, props, assumed)
    changed: list[dict[str, Any]] = []
    for key, value in props.items():
        if key == "suppressed":
            if not isinstance(value, bool):
                raise CommandError("suppressed is true or false.", code="pk_needs")
            changed.append({"key": key, "old": feature.suppressed, "new": value})
            feature.suppressed = value
        elif key == "name":
            new = doc.new_name({"name": value}, feature.kind, {f.id: f for f in part.features})
            changed.append({"key": key, "old": feature.id, "new": new})
            for users in doc.params.users.values():
                if f"feat:{feature.id}" in users:
                    users.discard(f"feat:{feature.id}")
                    users.add(f"feat:{new}")
            part.retire(part.names.drop_feature(feature.id))
            feature.id = new
        else:
            old = feature.args.get(key)
            changed.append({"key": key, "old": old, "new": value})
            feature.args[key] = value
    index = part.index_of(feature.id)
    report = part.regen(doc, index)
    own = next((f for f in report["failed"] if f["feature"] == feature.id), None)
    if own is not None:
        raise CommandError(
            f"set {target}: with these props {feature.kind} {feature.id} fails: {own['error']}",
            code=own.get("code", "pk_op_failed"),
        )
    return {"id": f"feat:{feature.id}", "part": f"part:{part.name}", "props": changed, **report}


def _set_part(
    doc: Document, part: Part, props: dict[str, Any], assumed: dict[str, Any]
) -> dict[str, Any]:
    changed: list[dict[str, Any]] = []
    for key, value in props.items():
        if key == "material":
            from partkiln.materials import resolve

            new = None if value in (None, "", "none") else resolve(str(value))
            changed.append({"key": key, "old": part.material, "new": new})
            part.material = new
        elif key == "name":
            new = doc.new_name({"name": value}, "part", doc.parts)
            changed.append({"key": key, "old": part.name, "new": new})
            del doc.parts[part.name]
            part.name = new
            doc.parts[new] = part
            part.invalidate()
        else:
            raise CommandError(
                f"part has no setting {key!r}. Settings: material, name.", code="pk_ref_unknown"
            )
    out: dict[str, Any] = {
        "id": f"part:{part.name}",
        "props": changed,
        "volume_mm3": r3(part.volume()),
    }
    mass = part.mass_g()
    if mass is not None:
        out["mass_g"] = mass
    out["fingerprint"] = part.fingerprint()
    return out


def delete_target(
    doc: Document, target: str, cascade: bool, assumed: dict[str, Any]
) -> dict[str, Any]:
    part, feature = _locate(doc, target)
    if feature is None:
        entity = f"part:{part.name}"
        blocked = dependents(doc, entity)
        if blocked and not cascade:
            raise CommandError(
                f"{entity} is used by {', '.join(blocked)}. Delete those first, or pass "
                "cascade: true.",
                code="pk_delete_blocked",
            )
        removed = [entity]
        for dep in blocked:
            if dep.startswith("feat:"):
                removed.extend(delete_target(doc, dep, True, assumed)["deleted"])
            elif dep.startswith("sk:"):
                doc.sketches.pop(dep[3:], None)
                removed.append(dep)
        for users in doc.params.users.values():
            for f in part.features:
                users.discard(f"feat:{f.id}")
        del doc.parts[part.name]
        return {"deleted": removed, "parts": len(doc.parts)}
    entity = f"feat:{feature.id}"
    blocked = dependents(doc, entity)
    if blocked and not cascade:
        raise CommandError(
            f"{entity} is used by {', '.join(blocked)}. Delete those first, or pass cascade: true.",
            code="pk_delete_blocked",
        )
    removed = []
    for dep in blocked:
        if dep.startswith("feat:") and any(p.has_feature(dep[5:]) for p in doc.parts.values()):
            removed.extend(delete_target(doc, dep, True, assumed)["deleted"])
    index = part.index_of(feature.id)
    part.features.pop(index)
    part.retire(part.names.drop_feature(feature.id))
    for users in doc.params.users.values():
        users.discard(entity)
    removed.insert(0, entity)
    report = part.regen(doc, index)
    return {"deleted": removed, "part": f"part:{part.name}", **report}


# --------------------------------------------------------------------------- fingerprint / summary


def fingerprint_payload(doc: Document) -> list[list[Any]]:
    """Per part: name, B-rep fingerprint, material (a stand-in without them hashes as such)."""
    rows: list[list[Any]] = []
    for name in sorted(doc.parts):
        part = doc.parts[name]
        fp = part.fingerprint() if callable(getattr(part, "fingerprint", None)) else "?"
        rows.append([name, fp, getattr(part, "material", None)])
    return rows


__all__ = [
    "FEATURE_KINDS",
    "Feature",
    "Part",
    "after_param_change",
    "after_sketch_change",
    "delete_target",
    "dependents",
    "fingerprint_payload",
    "set_target",
]
