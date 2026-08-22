"""Validated Verse templates (12.2): seeded from MIT/Apache-corpus
patterns (uefncentral MIT examples, OsirionGG Apache-2.0 - patterns
re-authored, never copied verbatim; AGPL sources are reference-only and
nothing here derives from them).

Each template declares the digest symbols it depends on; `instantiate`
verifies them against the LOADED digest before emitting code, so a
template can never silently ship stale API. Compile-checking through
Epic's MCP Verse toolset is the live upgrade on editor machines.
"""

from __future__ import annotations

from typing import Any

from tee.kernel.errors import TeeError
from tee.uefn.digest import all_classes, find_member

TEMPLATES: dict[str, dict[str, Any]] = {
    "device_subscribe": {
        "gloss": "creative device reacting to a button press",
        "requires": [("button_device", "InteractedWithEvent"), ("creative_device", None)],
        "code": """
using {{ /Fortnite.com/Devices }}
using {{ /Verse.org/Simulation }}

{name} := class(creative_device):
    @editable Button : button_device = button_device{{}}

    OnBegin<override>()<suspends> : void =
        Button.InteractedWithEvent.Subscribe(OnPressed)

    OnPressed(Agent : agent) : void =
        Print("pressed")
""",
    },
    "persistence_weak_map": {
        "gloss": "per-player persistent score via weak_map",
        "requires": [("creative_device", None)],
        "code": """
using {{ /Fortnite.com/Devices }}
using {{ /Verse.org/Simulation }}

score_data := class<final><persistable>:
    Version : int = 1
    Score : int = 0

var PlayerScores : weak_map(player, score_data) = map{{}}

{name} := class(creative_device):
    AddScore(Player : player, Points : int) : void =
        var Current : score_data = score_data{{}}
        if (Existing := PlayerScores[Player]):
            set Current = Existing
        if (set PlayerScores[Player] = score_data{{
                Version := Current.Version,
                Score := Current.Score + Points}}) {{}}
""",
    },
    "scene_graph_component": {
        "gloss": "custom Scene Graph component (the UE6 object model)",
        "requires": [("component", None)],
        "code": """
using {{ /Verse.org/SceneGraph }}
using {{ /Verse.org/Simulation }}

{name} := class(component):
    OnBegin<override>()<suspends> : void =
        Print("component up")
""",
    },
    "concurrency_race": {
        "gloss": "structured concurrency: first branch wins, loser cancelled",
        "requires": [],
        "code": """
{name}(TimeoutSeconds : float)<suspends> : void =
    race:
        block:
            Sleep(TimeoutSeconds)
            Print("timeout")
        block:
            AwaitTheThing()
            Print("done first")
""",
    },
}


def list_templates() -> list[dict[str, str]]:
    return [{"name": name, "gloss": t["gloss"]} for name, t in TEMPLATES.items()]


def instantiate(
    template_name: str, digest: dict[str, Any], *, name: str = "my_device"
) -> dict[str, Any]:
    template = TEMPLATES.get(template_name)
    if template is None:
        raise TeeError(
            "unknown_template",
            f"No Verse template '{template_name}'.",
            fix=f"Templates: {', '.join(sorted(TEMPLATES))}.",
        )
    classes = all_classes(digest)
    missing = []
    for class_name, member in template["requires"]:
        if class_name not in classes:
            missing.append(class_name)
        elif member and find_member(digest, class_name, member) is None:
            missing.append(f"{class_name}.{member}")
    if missing:
        raise TeeError(
            "template_digest_mismatch",
            f"Template '{template_name}' needs symbols missing from digest "
            f"{digest.get('version')}: {', '.join(missing)}.",
            fix="Refresh the digest from the current UEFN install; the API "
            "may have drifted (check uefn_digest_diff).",
        )
    return {
        "template": template_name,
        "digest_version": digest.get("version"),
        "code": template["code"].format(name=name),
        "note": "digest-symbol-validated; compile via Epic's MCP Verse "
        "toolset when a live editor is present",
    }
