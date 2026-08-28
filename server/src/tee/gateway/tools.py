"""Gateway registration (A37 P1): the service, its two control tools, and
the background handshakes. Everything is long-tail - the always-loaded
surface does not grow."""

from __future__ import annotations

from pathlib import Path

from tee.gateway.service import GatewayService
from tee.kernel.registry import VirtualTool


def register_gateway(app, project_root: Path | str) -> GatewayService | None:
    """Attach when [gateway] names backends; silent no-op otherwise."""
    service = GatewayService(app, Path(project_root))
    if not service.backends:
        return None
    app.gateway = service

    def gw_status(args):
        return {"backends": service.status()}

    def gw_accept(args):
        return service.accept(str(args.get("backend", "")))

    for tool in [
        VirtualTool(
            "gw_status",
            "Gateway backend states: connected (tool count + pinned "
            "fingerprint), drift (with the re-pin fix), dead, or disabled. "
            "Fronted tools appear as '<backend>.<tool>' via tee_search_tools.",
            {"type": "object", "properties": {}},
            gw_status,
            tags=["gateway", "backends", "status", "mcp", "front"],
        ),
        VirtualTool(
            "gw_accept",
            "Accept a gateway backend's fingerprint drift: reconnects, "
            "re-pins (server name/version + tool-list hash) and re-registers "
            "its tools FRESH - nothing stale survives an accepted change.",
            {
                "type": "object",
                "properties": {"backend": {"type": "string"}},
                "required": ["backend"],
            },
            gw_accept,
            tags=["gateway", "drift", "fingerprint", "accept", "re-pin"],
            examples=[{"backend": "fs"}],
        ),
    ]:
        app.registry.register(tool)
    service.connect_all_background()
    return service
