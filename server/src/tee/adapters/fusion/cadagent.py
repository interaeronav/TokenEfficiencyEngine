"""Typed shell and feature-pattern emitters adapted from CADAgent (A79).

The API sequences derive from ``feature_tools.py`` in er-fo/CADAgent at
42e5348eea5ea0d4c8383608bfa7974e6bff1abc (the owner's 1.1.2 download):
``create_shell``, ``_create_rectangular_pattern`` and
``_create_circular_pattern``. Copyright (c) 2026 Erik Fornlund, MIT;
the complete upstream notice is in ``CADAgent-LICENSE.txt`` beside this file.
Reference grounding lives in research 71 section 3 and research 80.

Only these modelling sequences are adapted. The downloaded add-in, controller,
backend and dependencies are never imported. TEE supplies document-scoped IDs,
mm/degree expressions, preflight, checkpoints and compact diffs. This first
version accepts native root-component targets; circular axes pass through that
component's origin. Unsupported context or input is refused explicitly.
"""

from __future__ import annotations

from typing import Any

PROPS: dict[str, set[str]] = {
    "shell": {"body", "remove_faces", "inside", "outside", "tangent", "shell_type"},
    "rectangular_pattern": {
        "features",
        "axis",
        "count",
        "spacing",
        "axis2",
        "count2",
        "spacing2",
    },
    "circular_pattern": {"features", "axis", "count", "angle"},
}


def check(index: int, kind: str, props: dict[str, Any]) -> None:
    """Check shape and bounded work before the Fusion bridge is contacted."""
    from . import codegen as c

    if kind not in PROPS:
        raise c._bad(index, f"Unknown CADAgent modelling kind {kind!r}", ", ".join(PROPS))
    c._unknown_props(index, props, PROPS[kind], kind)
    if kind == "shell":
        c._check_ref(index, props.get("body"), "body")
        faces = props.get("remove_faces", [])
        if (
            not isinstance(faces, list)
            or len(faces) > len(c.FACES)
            or any(not isinstance(face, str) or face not in c.FACES for face in faces)
            or len(set(faces)) != len(faces)
        ):
            raise c._bad(
                index,
                "remove_faces must be a list of distinct planar-face directions",
                "Use ['+z'] for an open shell, or [] for a closed shell; "
                f"directions: {', '.join(c.FACES)}.",
            )
        for key in ("inside", "outside"):
            value = props.get(key, 0)
            if not c._number(value) or value < 0:
                raise c._bad(index, f"{key} thickness must be finite and >= 0", "Thickness is mm.")
        if props.get("inside", 0) == 0 and props.get("outside", 0) == 0:
            raise c._bad(
                index,
                "shell needs positive inside or outside thickness",
                "Use inside:2 for a 2 mm inward wall, or outside:2 for an outward wall.",
            )
        if not isinstance(props.get("tangent", True), bool):
            raise c._bad(index, "tangent must be true or false", "Use tangent:true or omit it.")
        if props.get("shell_type", "sharp") not in ("sharp", "rounded"):
            raise c._bad(index, "shell_type must be sharp or rounded", "Use shell_type:'sharp'.")
        return

    refs = props.get("features")
    if not isinstance(refs, list) or not 1 <= len(refs) <= 32:
        raise c._bad(
            index,
            "features needs between 1 and 32 feature references",
            "Use features:['@bore.feature'] or a returned feature id such as f2.",
        )
    for ref in refs:
        c._check_ref(index, ref, "features")
    if len(set(refs)) != len(refs):
        raise c._bad(index, "features must not repeat a reference", "List each seed feature once.")

    def axis(key: str) -> None:
        value = props.get(key)
        if not isinstance(value, str) or value not in c.AXES:
            raise c._bad(
                index,
                f"{key} must be x, y or z",
                "Axes pass through the root-component origin; rectangular spacing may be negative.",
            )

    def count(key: str) -> int:
        value = props.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or not 2 <= value <= 1000:
            raise c._bad(
                index,
                f"{key} must be an integer from 2 to 1000",
                "Counts include the original instance; total pattern instances are capped at 1000.",
            )
        return value

    def spacing(key: str) -> None:
        value = props.get(key)
        if not c._number(value) or value == 0:
            raise c._bad(
                index,
                f"{key} must be a finite nonzero length",
                "Use signed mm: spacing:20 or spacing:-20.",
            )

    axis("axis")
    primary_count = count("count")
    if kind == "circular_pattern":
        angle = props.get("angle", 360)
        if not c._number(angle) or not 0 < angle <= 360:
            raise c._bad(
                index,
                "angle must be finite and in (0, 360] degrees",
                "Use angle:360 for a complete circular pattern.",
            )
        return

    spacing("spacing")
    second = {"axis2", "count2", "spacing2"} & props.keys()
    if second and len(second) != 3:
        raise c._bad(
            index,
            "the second pattern direction needs axis2, count2 and spacing2 together",
            "Supply all three or omit them for a one-direction pattern.",
        )
    if second:
        axis("axis2")
        if props["axis2"] == props["axis"]:
            raise c._bad(index, "pattern axes must be distinct", "Use axis:'x', axis2:'y'.")
        secondary_count = count("count2")
        spacing("spacing2")
        if primary_count * secondary_count > 1000:
            raise c._bad(
                index,
                "count times count2 must not exceed 1000",
                "Reduce the number of pattern instances.",
            )


def emit(index: int, kind: str, name: str, props: dict[str, Any]) -> list[str]:
    """Emit one checked operation inside codegen's document-guarded prelude."""
    from . import codegen as c

    check(index, kind, props)
    if kind == "shell":
        lines = [
            f"    _b = _find({c._lit(props['body'])}, {index})",
            f"    if _kind_of(_b) != 'body': raise _OpError({index}, 'shell requires a body id')",
            "    if (getattr(_b, 'assemblyContext', None) is not None or "
            "getattr(_b, 'nativeObject', None) is not None or "
            "getattr(_b, 'parentComponent', None) != _root):",
            f"        raise _OpError({index}, 'shell currently accepts native root-component "
            "bodies only; occurrence proxies and component bodies are unsupported')",
            f"    if not _b.isSolid: raise _OpError({index}, 'shell requires a solid body')",
            "    _shell_entities = adsk.core.ObjectCollection.create()",
        ]
        removed = props.get("remove_faces", [])
        if removed:
            for face in removed:
                lines.append(f"    _shell_entities.add(_face(_b, {c._lit(face)}, None, {index}))")
            lines += [
                "    if _shell_entities.count >= _b.faces.count:",
                f"        raise _OpError({index}, 'shell must leave at least one face "
                "on the body')",
            ]
        else:
            lines.append("    _shell_entities.add(_b)")
        lines += [
            "    _shells = _root.features.shellFeatures",
            "    _inp = _shells.createInput(_shell_entities, "
            f"{c._lit(props.get('tangent', True))})",
            f"    if _inp is None: raise _OpError({index}, 'shell input failed: "
            "Fusion returned null')",
        ]
        for key in ("inside", "outside"):
            if props.get(key, 0) > 0:
                value = c._lit(f"{float(props[key])!r} mm")
                lines.append(
                    f"    _inp.{key}Thickness = adsk.core.ValueInput.createByString({value})"
                )
        shell_type = (
            "RoundedOffsetShellType"
            if props.get("shell_type", "sharp") == "rounded"
            else "SharpOffsetShellType"
        )
        lines += [
            f"    _inp.shellType = adsk.fusion.ShellTypes.{shell_type}",
            "    _f = _shells.add(_inp)",
            f"    if _f is None: raise _OpError({index}, 'shell failed: Fusion returned null')",
        ]
    else:
        lines = ["    _pattern_entities = adsk.core.ObjectCollection.create()"]
        for ref in props["features"]:
            lines += [
                f"    _seed = _find({c._lit(ref)}, {index})",
                "    if _kind_of(_seed) != 'feature':",
                f"        raise _OpError({index}, 'patterns require feature ids; use the "
                "returned feature id or @alias.feature')",
                "    if (getattr(_seed, 'assemblyContext', None) is not None or "
                "getattr(_seed, 'nativeObject', None) is not None or "
                "getattr(_seed, 'parentComponent', None) != _root):",
                f"        raise _OpError({index}, 'patterns currently accept native root-component "
                "features only; occurrence proxies and component features are unsupported')",
                "    _pattern_entities.add(_seed)",
            ]
        axis = f"_root.{c.AXES[props['axis']]}"
        quantity = f"adsk.core.ValueInput.createByString({c._lit(str(props['count']))})"
        if kind == "rectangular_pattern":
            spacing_value = c._lit(f"{float(props['spacing'])!r} mm")
            distance = f"adsk.core.ValueInput.createByString({spacing_value})"
            lines += [
                "    _patterns = _root.features.rectangularPatternFeatures",
                f"    _inp = _patterns.createInput(_pattern_entities, {axis}, {quantity}, "
                f"{distance}, adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)",
                f"    if _inp is None: raise _OpError({index}, 'pattern input failed: "
                "Fusion returned null')",
                "    _inp.isSymmetricInDirectionOne = False",
                "    _inp.isSymmetricInDirectionTwo = False",
            ]
            # Live Fusion produced nine bodies for count=3 when direction two
            # was omitted. Explicitly disable that dimension (research 71 row
            # 58), including its symmetry, instead of relying on GUI defaults.
            second_axis = props.get("axis2", "y" if props["axis"] == "x" else "x")
            axis2 = f"_root.{c.AXES[second_axis]}"
            qty2 = f"adsk.core.ValueInput.createByString({c._lit(str(props.get('count2', 1)))})"
            spacing2_value = c._lit(f"{float(props.get('spacing2', 0))!r} mm")
            step2 = f"adsk.core.ValueInput.createByString({spacing2_value})"
            lines += [
                f"    if not _inp.setDirectionTwo({axis2}, {qty2}, {step2}):",
                f"        raise _OpError({index}, 'Fusion refused the second pattern direction')",
            ]
        else:
            # Six-significant-digit formatting turns 359.9999 into 360,
            # changing Fusion's full-circle instance placement semantics.
            angle = c._lit(f"{float(props.get('angle', 360))!r} deg")
            lines += [
                "    _patterns = _root.features.circularPatternFeatures",
                f"    _inp = _patterns.createInput(_pattern_entities, {axis})",
                f"    if _inp is None: raise _OpError({index}, 'pattern input failed: "
                "Fusion returned null')",
                f"    _inp.quantity = {quantity}",
                f"    _inp.totalAngle = adsk.core.ValueInput.createByString({angle})",
                "    _inp.isSymmetric = False",
            ]
        lines += [
            "    _f = _patterns.add(_inp)",
            f"    if _f is None: raise _OpError({index}, 'pattern failed: Fusion returned null')",
        ]

    lines += [
        f"    _f.name = {c._lit(name)}",
        '    _fid = _mint("f", _f.entityToken); _mark(_fid, True); _note(_fid, "feature", _f)',
    ]
    if kind == "shell":
        lines.append(
            '    _bid = _mint("b", _b.entityToken); _mark(_bid, False); _note(_bid, "body", _b)'
        )
    lines.append("    _mark_bodies(_f)")
    return lines
