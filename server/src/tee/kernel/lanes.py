"""The lane table (A68): which served lane a virtual tool touches.

One table, like the trust table, so the answer to "does this tool need
Blender?" is a lookup and not a habit. A tool's lane is one of:

- a served adapter's name (`"blender"`, `"partkiln"`, ...): the tool is
  bound to that lane and refuses when it is not served;
- ADAPTER_ARG: the tool routes by its own `adapter=` argument (an asset
  import lands wherever the caller says, or where the file's suffix can go);
- a label that is not an adapter (`"uefn"`): the tool writes through its own
  proxy, and the label says which scene without a lane being served;
- None: adapter-agnostic - it never touches a scene.

The kernel uses the lane in three places: `tee_script` checkpoints ONLY the
lane a tool touches (a script calling pdf_compose takes no Blender snapshot);
search indexes the lane name and prefers served lanes at equal score; and
`tee_status` reports which tool families each lane owns. And one law is
structural: a `write-scene` or `exec-code` tool with no lane fails at
registration - like an untabled capability, a new scene-writing tool cannot
slip in without saying which scene.
"""

from __future__ import annotations

from typing import Any

ADAPTER_ARG = "adapter="

# Families first: a prefix names the lane its tools are registered against.
_FAMILY: tuple[tuple[str, str], ...] = (
    ("bl_", "blender"),
    ("hb_", "blender"),
    ("sim_", "blender"),
    ("ue_", "unreal"),
    ("pin_", "unreal"),
    ("fc_", "freecad"),
    ("pk_", "partkiln"),
    ("sk_", "seamkiln"),
)

# Explicit rows win over families: tools whose name says nothing about
# their lane, and tools that route by their own argument.
_EXPLICIT: dict[str, str] = {
    # the tier-2 modeling ops compile to bpy patterns (physical/tools.py)
    "wall_with_openings": "blender",
    "slab": "blender",
    "roof": "blender",
    "stairs": "blender",
    "opening_cut": "blender",
    "array_along": "blender",
    "profile_extrude": "blender",
    "param_set": "blender",
    "sense_camera": "blender",  # aims Blender's camera
    "export_for_uefn": "blender",  # exports FROM the served Blender
    # route by their own adapter= (else by content: an importer lane, the
    # entity they name, or the sole / declared lane)
    "as_import": ADAPTER_ARG,
    "as_place": ADAPTER_ARG,
    "as_material": ADAPTER_ARG,
    "as_photo_material": ADAPTER_ARG,
    "as_sun": ADAPTER_ARG,
    "mat_assign": ADAPTER_ARG,
    "capture_apply": ADAPTER_ARG,
    "sense_viewport": ADAPTER_ARG,
    "sense_frame": ADAPTER_ARG,
    # written through UEFN's own proxy; a label, not a served adapter
    "uefn_place_device": "uefn",
    "uefn_entity_batch": "uefn",
}

# What the model is told, once, in the instructions (P2).
LEGEND = (
    "bl_/hb_ Blender, pk_ partkiln, sk_ seamkiln, ue_/pin_ Unreal, fc_ FreeCAD; "
    "pc_/pdf_/ex_/sense_/kb_/solve_/quant_/med_ and the rest are headless and need no lane"
)

# Capabilities that touch a scene: a tool carrying one must name its lane.
_SCENE_WRITING = frozenset({"write-scene", "exec-code"})


def lane_for(name: str) -> str | None:
    """The lane a tool name resolves to: explicit row, then family, else None."""
    if name in _EXPLICIT:
        return _EXPLICIT[name]
    for prefix, lane in _FAMILY:
        if name.startswith(prefix):
            return lane
    return None


def check(tool: Any) -> None:
    """Registration-time law: a scene-writing tool says which scene."""
    if tool.capability in _SCENE_WRITING and tool.lane is None:
        raise ValueError(
            f"{tool.name}: a {tool.capability} tool must name its lane - add it to "
            "kernel/lanes.py (a family prefix or an explicit row), or pass lane= at "
            "registration (ADAPTER_ARG for a tool that routes by its adapter= argument)."
        )


def families_for(lane: str) -> tuple[str, ...]:
    """The prefixes (and lone names) a lane owns, for tee_status."""
    prefixes = [prefix for prefix, owner in _FAMILY if owner == lane]
    named = [name for name, owner in _EXPLICIT.items() if owner == lane]
    return tuple(prefixes + named)


def is_adapter_label(lane: str | None, served: set[str] | frozenset[str]) -> bool:
    """A lane that is a served adapter's name - what search prefers and the
    script lane checkpoints. ADAPTER_ARG, None and proxy labels are not."""
    return lane is not None and lane in served


INSTRUCTIONS_CAP_BYTES = 2_048  # research 08: Claude Code truncates past 2 KB


def instructions(app: Any) -> str:
    """The MCP instructions, built from what THIS server serves (A68).

    A deferring host indexes exactly tool names plus these instructions
    (research 08), so this is the one sentence a model reads before it
    searches. It says what is served and what each lane is for, that no lane
    is the default unless one was declared, how an omitted adapter= routes,
    which lanes never need a DCC, and when to search the long tail. Always
    under 2 KB: with many lanes the per-lane purposes are the first thing
    trimmed, never the routing rule."""
    served = list(app.adapters)
    default = getattr(app, "default_adapter", None)

    def lane_lines(with_purpose: bool) -> str:
        rows = []
        for name in served:
            purpose = app.vocab(name).purpose if with_purpose else ""
            rows.append(f"{name} ({purpose})" if purpose else name)
        return ", ".join(rows) or "none"

    def build(with_purpose: bool) -> str:
        parts = [
            "Token Efficiency Engine: one server, several lanes, none of them the hub. "
            "Reads return compact summaries and diffs, never full dumps; mutations run as "
            "checkpointed batches.",
            f"Lanes served: {lane_lines(with_purpose)}.",
            (
                f"Declared default lane: {default} (only for a batch several lanes accept)."
                if default
                else "No lane is the default."
            ),
            "adapter= names a lane. Omit it and a batch goes where its content says - an "
            "entity id to the lane that holds it, a create kind to the lane that makes it, a "
            "verb to the lane that speaks it - and the reply carries adapter (and routed). A "
            "batch two lanes take is refused naming them; an op no lane takes is refused "
            "naming the lanes that would. tee_scene_summary with no lane is every lane at a "
            "glance; tee_status lists each lane's purpose, ops and kinds.",
            "Headless lanes (partkiln, seamkiln, pc_, pdf_, ex_, sense_, kb_, the fleet) never "
            "need Blender or Unreal; use a scene lane only for scene work, and ask for pixels "
            "(tee_capture) only from a lane that renders - text and measurements first.",
            f"Tool prefixes: {LEGEND}.",
            "Long tail: tee_search_tools by capability words (extrude a sketch, drape a "
            "garment, level a scan, bake physics), tee_describe_tool for the schema and the "
            "tool's lane, tee_call to invoke. Track (epoch, revision) from replies and use "
            "tee_diff instead of re-reading a scene.",
        ]
        return " ".join(parts)

    text = build(True)
    if len(text.encode()) > INSTRUCTIONS_CAP_BYTES:
        text = build(False)
    if len(text.encode()) > INSTRUCTIONS_CAP_BYTES:  # a pathological lane list
        text = text.encode()[: INSTRUCTIONS_CAP_BYTES - 3].decode(errors="ignore") + "..."
    return text
