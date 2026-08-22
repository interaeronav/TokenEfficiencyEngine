"""Version-aware API firewall (principle P5).

Screens Python destined for Blender against the catalogued bpy fault lines
(docs/research/10-blender-version-baseline.md) BEFORE execution, so a stale
idiom costs one short hint instead of a traceback plus a blind retry loop.
Patterns are matched per connected Blender version: an idiom is only flagged
where it is actually wrong.

This is a firewall, not a linter: it targets exactly the drift mistakes LLMs
make because their training data spans many Blender versions.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

Version = tuple[int, int, int]


@dataclass(frozen=True)
class FaultLine:
    code: str
    pattern: re.Pattern[str]
    applies: Callable[[Version], bool]
    hint: str


_F = [
    FaultLine(
        "use_nodes_write_banned",
        re.compile(r"\.use_nodes\s*="),
        lambda v: v >= (5, 0, 0),
        "Writing use_nodes is banned (A24): nodes are always-on since 5.0 and "
        "the property is a 6.0 hard-removal target (#140111) - just delete "
        "the assignment.",
    ),
    FaultLine(
        "use_auto_smooth_removed",
        re.compile(r"\buse_auto_smooth\b"),
        lambda v: v >= (4, 1, 0),
        "use_auto_smooth was removed in 4.1: add a 'Smooth by Angle' modifier "
        "(bpy.ops.object.modifier_add_node_group or shade_smooth_by_angle).",
    ),
    FaultLine(
        "id_prop_dict_access",
        re.compile(r"""(?:\bscene|\bcontext\.scene)\s*\[\s*['"]cycles['"]\s*\]"""),
        lambda v: v >= (5, 0, 0),
        "Dict access to bpy.props storage (scene['cycles']) was removed in 5.0: "
        "use attribute access, e.g. scene.cycles.samples.",
    ),
    FaultLine(
        "eevee_next_id_on_5x",
        re.compile(r"\bBLENDER_EEVEE_NEXT\b"),
        lambda v: v >= (5, 0, 0),
        "The EEVEE engine id on Blender 5.x is 'BLENDER_EEVEE' "
        "('BLENDER_EEVEE_NEXT' was the 4.2-4.5 name).",
    ),
    FaultLine(
        "eevee_id_on_4x",
        re.compile(r"""engine\s*=\s*['"]BLENDER_EEVEE['"]"""),
        lambda v: (4, 2, 0) <= v < (5, 0, 0),
        "On Blender 4.2-4.5 the EEVEE engine id is 'BLENDER_EEVEE_NEXT' "
        "(it becomes 'BLENDER_EEVEE' again in 5.0).",
    ),
    FaultLine(
        "scene_node_tree_removed",
        re.compile(r"\bscene\.node_tree\b|\bcontext\.scene\.node_tree\b"),
        lambda v: v >= (5, 0, 0),
        "scene.node_tree was removed in 5.0: use scene.compositing_node_group "
        "(and note scene.use_nodes is a no-op on 5.x).",
    ),
    FaultLine(
        "bgl_removed",
        re.compile(r"^\s*(?:import\s+bgl\b|from\s+bgl\s+import)", re.MULTILINE),
        lambda v: v >= (5, 0, 0),
        "The bgl module is gone in 5.0: use the gpu module "
        "(gpu.types.GPUShaderCreateInfo for shaders).",
    ),
    FaultLine(
        "legacy_action_fcurves",
        re.compile(r"\baction\.fcurves\b|\.animation_data\.action\.fcurves\b"),
        lambda v: v >= (5, 0, 0),
        "The legacy Action API (action.fcurves) was removed in 5.0: use the "
        "slot/channelbag API (see bpy_extras.anim_utils).",
    ),
    FaultLine(
        "sculpt_tool_renamed",
        re.compile(r"\.sculpt_tool\b"),
        lambda v: v >= (5, 0, 0),
        "brush.sculpt_tool became brush.sculpt_brush_type in 5.0 "
        "(all *_tool brush enums are now *_brush_type).",
    ),
    FaultLine(
        "file_output_node_api",
        re.compile(r"\.file_slots\b|\.layer_slots\b"),
        lambda v: v >= (5, 0, 0),
        "CompositorNodeOutputFile lost file_slots/layer_slots/base_path in "
        "5.0: use .directory, .file_name and .file_output_items.",
    ),
    FaultLine(
        "geonodes_socket_dict_access",
        re.compile(r"""modifiers?\s*\[[^\]]+\]\s*\[\s*['"](?:Socket_|Input_)"""),
        lambda v: v >= (5, 2, 0),
        "Geometry-nodes modifier inputs are real RNA since 5.2: use "
        "modifier.properties.inputs.<identifier>.value instead of "
        "modifier['Socket_N'].",
    ),
    FaultLine(
        "vse_strip_times_renamed",
        re.compile(r"\.frame_final_start\b|\.frame_final_end\b"),
        lambda v: v >= (5, 1, 0),
        "VSE strip time properties were renamed in 5.1 (frame_final_start -> "
        "left_handle etc.); the old names disappear in 6.0.",
    ),
]


def strip_comments(code: str) -> str:
    """Blank out comment tokens so the firewall never fires on prose. String
    literals stay - engine ids and subscript keys live inside strings. Falls
    back to the raw code when tokenization fails (syntax errors reach Blender
    and come back as compact errors anyway)."""
    import io
    import tokenize

    lines = code.splitlines(keepends=True)
    try:
        for tok in tokenize.generate_tokens(io.StringIO(code).readline):
            if tok.type == tokenize.COMMENT:
                row = tok.start[0] - 1
                line = lines[row]
                lines[row] = (
                    line[: tok.start[1]] + " " * (tok.end[1] - tok.start[1]) + line[tok.end[1] :]
                )
    except (tokenize.TokenError, IndentationError, SyntaxError, IndexError):
        return code
    return "".join(lines)


def firewall_check(code: str, version: Version) -> list[dict[str, str]]:
    """Return one {code, hint} entry per stale idiom found in `code` for the
    connected Blender `version`. Empty list = clean. Comments are ignored;
    string literals are screened (that is where engine ids live)."""
    stripped = strip_comments(code)
    hits: list[dict[str, str]] = []
    for fault in _F:
        if fault.applies(version) and fault.pattern.search(stripped):
            hits.append({"code": fault.code, "hint": fault.hint})
    return hits


def compact_traceback(message: str, limit: int = 400) -> str:
    """Reduce a bridge traceback to its final error line(s) (principle P7)."""
    lines = [ln for ln in message.strip().splitlines() if ln.strip()]
    if not lines:
        return "unknown error"
    last = lines[-1]
    # include the offending source line when the traceback carries one
    context = ""
    for ln in reversed(lines[:-1]):
        stripped = ln.strip()
        if not stripped.startswith(("File ", "Traceback")):
            context = stripped
            break
    out = f"{last} (at: {context})" if context and context != last else last
    return out[:limit]
