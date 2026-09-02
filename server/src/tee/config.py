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

    [kb]
    root = "../TokenEfficiencyEngine/knowledge-base"  # Expert KB corpus; defaults
    max_tokens = 800          # to the in-repo mirror when one is discoverable

    [web]
    allow_local = false       # opt-in: web_lookup may reach private addresses
    ports = [80, 443]         # opt-in extra ports for web_lookup
    search = "searxng"        # web_search backend (searxng|brave|wikipedia)
    searxng_url = "http://127.0.0.1:8888"  # your SearXNG instance

    [llm]
    url = "http://127.0.0.1:8080/v1"  # any OpenAI-compatible local endpoint
    model = "tee-coder"               # served model name (research 50 M0)
    adapters = "…/tee-triage-a2"      # optional LoRA dir, sent per-request
    managed = false                   # opt-in: llm_switch stops/starts servers
                                      # the profiles below declare they own

    [llm.profiles.q27b]               # switch profiles (llm_switch; the chat
    url = "http://127.0.0.1:8081/v1"  # phrases TEE/Q14B / TEE/Q27B); builtins
    start = "mlx_lm.server --model mlx-community/Qwen3.8-27B-bf16 --port 8081"  # managed only
    port = 8081                       # managed only, never a chat-stack port
    process = "mlx_lm.server"         # managed only: owned-process pattern

    [gateway.backends.fs]             # front another MCP server (A37): its
    command = "npx -y @modelcontextprotocol/server-filesystem /data"  # tools
    enable = true                     # appear as fs.* via tee_search_tools;
    max_tokens = 800                  # results budgeted; stdio only for now
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
    kb: dict[str, Any] = field(default_factory=dict)
    web: dict[str, Any] = field(default_factory=dict)
    llm: dict[str, Any] = field(default_factory=dict)
    gateway: dict[str, Any] = field(default_factory=dict)
    capture: dict[str, Any] = field(default_factory=dict)
    scheduler: dict[str, Any] = field(default_factory=dict)
    trust: dict[str, Any] = field(default_factory=dict)
    senses: dict[str, Any] = field(default_factory=dict)
    pipeline: dict[str, Any] = field(default_factory=dict)
    # A66: the partkiln lane - `python` (the sidecar interpreter) and
    # `batch_timeout_s`; ProjectConfig drops unknown tables silently, so the
    # lane needs its own field to be configurable at all.
    partkiln: dict[str, Any] = field(default_factory=dict)
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

        kb = data.get("kb", {})
        if isinstance(kb, dict):
            config.kb = kb
        elif kb:
            problems.append("[kb] must be a table")

        web = data.get("web", {})
        if isinstance(web, dict):
            config.web = web
        elif web:
            problems.append("[web] must be a table")

        llm = data.get("llm", {})
        if isinstance(llm, dict):
            config.llm = llm
        elif llm:
            problems.append("[llm] must be a table")

        senses = data.get("senses", {})
        if isinstance(senses, dict):
            config.senses = senses
        elif senses:
            problems.append("[senses] must be a table")

        gateway = data.get("gateway", {})
        if isinstance(gateway, dict):
            config.gateway = gateway
        elif gateway:
            problems.append("[gateway] must be a table")

        capture = data.get("capture", {})
        if isinstance(capture, dict):
            config.capture = capture
        elif capture:
            problems.append("[capture] must be a table")

        scheduler = data.get("scheduler", {})
        if isinstance(scheduler, dict):
            config.scheduler = scheduler
        elif scheduler:
            problems.append("[scheduler] must be a table")

        pipeline_section = data.get("pipeline", {})
        if isinstance(pipeline_section, dict):
            config.pipeline = pipeline_section
        elif pipeline_section:
            problems.append("[pipeline] must be a table")

        partkiln_section = data.get("partkiln", {})
        if isinstance(partkiln_section, dict):
            config.partkiln = partkiln_section
        elif partkiln_section:
            problems.append("[partkiln] must be a table")

        trust_section = data.get("trust", {})
        if isinstance(trust_section, dict):
            config.trust = trust_section
        elif trust_section:
            problems.append("[trust] must be a table")

        if problems:
            config.warning = f"{path.name}: " + "; ".join(problems)
        return config
