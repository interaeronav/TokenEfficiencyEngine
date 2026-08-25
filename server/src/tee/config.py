"""Per-project configuration: `.tee/config.toml` (Phase 4).

Users explicitly ask for hard tool disables (they cannot stop assistants
over-invoking tools they never want). Config must never brick a session: a
malformed file degrades to defaults with a warning surfaced in tee_status.

    [tools]
    disabled = ["bl_render"]

    [server]
    allow_code_exec = true   # same effect as `tee serve --allow-code-exec`

    [blender]
    port = 9876

    [assets]
    allow_sa = false          # opt into CC-BY-SA share-alike assets (A13)
    sketchfab = false         # guarded backend opt-in
    backends = ["polyhaven"]  # optional: restrict enabled backends

    [pins]
    namespace = "tee_pin"     # actor-tag prefix the pin lane reads and writes
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProjectConfig:
    disabled_tools: set[str] = field(default_factory=set)
    allow_code_exec: bool | None = None  # None = not set
    blender_port: int | None = None
    assets: dict[str, Any] = field(default_factory=dict)
    pins: dict[str, Any] = field(default_factory=dict)
    warning: str | None = None

    @classmethod
    def load(cls, project_root: Path | str) -> ProjectConfig:
        path = Path(project_root) / ".tee" / "config.toml"
        if not path.exists():
            return cls()
        try:
            data = tomllib.loads(path.read_text())
        except (tomllib.TOMLDecodeError, OSError) as exc:
            return cls(warning=f"ignored malformed {path.name}: {exc}")
        config = cls()
        problems: list[str] = []

        tools = data.get("tools", {})
        disabled = tools.get("disabled", [])
        if isinstance(disabled, list) and all(isinstance(t, str) for t in disabled):
            config.disabled_tools = set(disabled)
        elif disabled:
            problems.append("[tools].disabled must be a list of tool names")

        server = data.get("server", {})
        allow = server.get("allow_code_exec")
        if isinstance(allow, bool):
            config.allow_code_exec = allow
        elif allow is not None:
            problems.append("[server].allow_code_exec must be a boolean")

        blender = data.get("blender", {})
        port = blender.get("port")
        if isinstance(port, int) and 1024 <= port <= 65535:
            config.blender_port = port
        elif port is not None:
            problems.append("[blender].port must be an integer in 1024-65535")

        assets = data.get("assets", {})
        if isinstance(assets, dict):
            config.assets = assets
        elif assets:
            problems.append("[assets] must be a table")

        pins = data.get("pins", {})
        if isinstance(pins, dict):
            config.pins = pins
        elif pins:
            problems.append("[pins] must be a table")

        if problems:
            config.warning = f"{path.name}: " + "; ".join(problems)
        return config
