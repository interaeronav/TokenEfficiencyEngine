"""Progressively disclosed lane contracts and offline batch checks (A78).

The adapter owns its API facts. This module neither imports a DCC nor warms
one. A syntax verdict is deliberately weaker than a live geometry verdict.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.kernel.registry import VirtualTool


def declared_adapter(app: Any, name: str) -> Any:
    """Look up a declaration without TeeApp.adapter's connection probe."""
    if name not in app.adapters:
        raise TeeError(
            "unknown_adapter",
            f"No adapter '{name}'.",
            fix=f"Configured adapters: {', '.join(sorted(app.adapters)) or '(none)'}.",
        )
    return app.adapters[name]


def validate_shape(ops: Any) -> None:
    if not isinstance(ops, list) or not ops:
        raise TeeError(
            "bad_batch",
            "ops must be a nonempty list of operation objects.",
            fix='Use ops=[{"op":"create","kind":...,"props":{...}}].',
        )
    for index, op in enumerate(ops):
        if not isinstance(op, dict):
            raise TeeError(
                "bad_batch",
                f"batch[{index}] must be an object.",
                fix="Pass JSON objects in ops, not serialized JSON strings.",
            )
        if not isinstance(op.get("op"), str) or not op["op"]:
            raise TeeError(
                "bad_batch",
                f"batch[{index}].op must name an operation.",
                fix="Use lane_guide for this adapter's operations and examples.",
            )
        if "props" in op and not isinstance(op["props"], dict):
            raise TeeError(
                "bad_batch",
                f"batch[{index}].props must be an object.",
                fix="Put property names and values in a JSON object, or omit props.",
            )


def preflight(app: Any, name: str, ops: Any) -> bool:
    """True means adapter-specific syntax was checked; no live state is read."""
    adapter = declared_adapter(app, name)
    validate_shape(ops)
    check = getattr(adapter, "preflight", None)
    if not callable(check):
        return False
    check(ops)
    return True


def register_guidance_tools(app: Any) -> None:
    def lane_guide(args: dict[str, Any]) -> dict[str, Any]:
        name = args["adapter"]
        adapter = declared_adapter(app, name)
        guide = getattr(adapter, "guide", None)
        if callable(guide):
            return {"adapter": name, "offline": True, **guide(args.get("topic"))}
        vocab = app.vocab(name)
        return {
            "adapter": name,
            "offline": True,
            "detailed_contract": False,
            "purpose": vocab.purpose,
            "ops": vocab.ops,
            "kinds": vocab.kinds,
            "next": "Search tools by capability, then describe the selected tool. "
            "This adapter has no detailed batch guide yet.",
        }

    def lane_preflight(args: dict[str, Any]) -> dict[str, Any]:
        checked = preflight(app, args["adapter"], args["ops"])
        return {
            "ok": True,
            "adapter": args["adapter"],
            "operations": len(args["ops"]),
            "checked": "adapter syntax" if checked else "outer shape only",
            "live_state_checked": False,
            "next": "tee_batch with the same adapter and ops; then read back dimensions "
            "and required properties. Geometry, entity existence, permissions and "
            "output quality are not established by preflight.",
        }

    for tool in (
        VirtualTool(
            "lane_guide",
            "Learn a lane's typed operations: units, properties, dependency examples "
            "and verification steps. Omit topic for a compact index. Works offline.",
            {
                "type": "object",
                "properties": {"adapter": {"type": "string"}, "topic": {"type": "string"}},
                "required": ["adapter"],
            },
            lane_guide,
            tags=["guide", "learn", "beginner", "workflow", "batch", "contract", "units"],
            examples=[{"adapter": "blender", "topic": "camera"}],
        ),
        VirtualTool(
            "lane_preflight",
            "Validate proposed typed operations before connection or checkpoint. "
            "Returns exact syntax fixes; never executes or approves geometry.",
            {
                "type": "object",
                "properties": {
                    "adapter": {"type": "string"},
                    "ops": {"type": "array", "items": {"type": "object"}},
                },
                "required": ["adapter", "ops"],
            },
            lane_preflight,
            tags=["preflight", "validate", "batch", "syntax", "draft", "repair"],
        ),
    ):
        app.registry.register(tool)
