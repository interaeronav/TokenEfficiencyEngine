"""`tee` command line: serve the MCP server, print environment diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tee import __version__


def _build_fake_app(project: str):
    from tee.app import TeeApp
    from tee.kernel.adapter import FakeAdapter

    return TeeApp({"fake": FakeAdapter()}, project_root=Path(project))


def _build_blender_app(project: str, host: str, port: int, allow_code_exec: bool):
    from tee.adapters.blender.adapter import BlenderAdapter
    from tee.adapters.blender.tools import register_blender_tools
    from tee.adapters.blender.wire import BlenderWire
    from tee.app import TeeApp

    adapter = BlenderAdapter(BlenderWire(host=host, port=port))
    app = TeeApp({"blender": adapter}, project_root=Path(project), allow_code_exec=allow_code_exec)
    register_blender_tools(app, adapter)
    from tee.adapters.blender.homebuilder import register_hb_tools

    register_hb_tools(app, adapter)  # the joinery lane (A37); refuses w/ fix if HB absent
    return app


def _build_unreal_app(project: str, host: str, port: int, allow_code_exec: bool):
    from tee.adapters.unreal.adapter import UnrealAdapter
    from tee.adapters.unreal.tools import register_unreal_tools
    from tee.adapters.unreal.wire import UnrealWire
    from tee.app import TeeApp

    adapter = UnrealAdapter(UnrealWire(host=host, port=port))
    app = TeeApp({"unreal": adapter}, project_root=Path(project), allow_code_exec=allow_code_exec)
    register_unreal_tools(app, adapter)
    return app


def _attach_extract(app, project: str, *, with_handoff: bool):
    """Register TEE Extract tools when the extract extra is installed;
    silently skip otherwise (the kernel works without it)."""
    try:
        from tee.extract.tools import register_extract_tools
    except ImportError:
        return None
    store, registry = register_extract_tools(app, Path(project))
    if with_handoff:
        from tee.extract.handoff import register_handoff_tools

        register_handoff_tools(app, store, registry)
    return store


def _attach_assets(app, project: str, extract_store) -> None:
    """Register TEE Assets tools (stdlib core; astral/shapely lanes degrade
    with actionable errors when their extra is missing)."""
    from tee.assets.tools import register_asset_tools

    register_asset_tools(app, Path(project), extract_store=extract_store)


def _attach_pins(app, project: str) -> None:
    """Register the pin lane (pin_*). Actor tags are the storage, so this is
    an Unreal-only lane and is not offered to a session that cannot use it."""
    if "unreal" not in app.adapters:
        return
    from tee.pins.tools import register_pin_tools

    register_pin_tools(app, Path(project))


def _attach_design(app, project: str) -> None:
    """Register TEE Design tools (pure stdlib - always on)."""
    from tee.design.tools import register_design_tools

    register_design_tools(app, Path(project))


def _attach_physical(app, project: str) -> None:
    """Register TEE Physical tools (sketch_solve degrades with an
    actionable error when the [physical] extra is missing)."""
    from tee.physical.tools import register_physical_tools

    register_physical_tools(app, Path(project))


def _attach_uefn(app, project: str) -> None:
    """Register TEE UEFN tools (offline lanes always work; the live proxy
    activates on machines with UEFN + Beta Access)."""
    from tee.uefn.tools import register_uefn_tools

    register_uefn_tools(app, Path(project))


def _build_freecad_app(project: str, allow_code_exec: bool):
    """The fabrication lane (A37): FreeCADAdapter over the neka-nat bridge
    (the P0-decided one bridge) + fc_drawing / fc_export."""
    from tee.adapters.freecad.adapter import FreeCADAdapter
    from tee.adapters.freecad.tools import register_freecad_tools
    from tee.app import TeeApp

    adapter = FreeCADAdapter()
    app = TeeApp({"freecad": adapter}, project_root=Path(project), allow_code_exec=allow_code_exec)
    register_freecad_tools(app, adapter)
    return app


def _attach_kb(app, project: str) -> None:
    """Register the kb_* lane when an Expert Knowledge Base corpus resolves
    ([kb] root, or a discoverable knowledge-base/ mirror); inactive otherwise."""
    from tee.kb.tools import register_kb_tools

    register_kb_tools(app, Path(project))


def _attach_llm(app, project: str) -> None:
    """Register the llm_* chore tools (A34): triage and lint explanation
    from the local code model, structured-unavailable when none runs."""
    from tee.llm.tools import register_llm_tools

    register_llm_tools(app, Path(project))


def _attach_web(app, project: str) -> None:
    """Register the web long tail (web_search); tee_web_lookup itself is
    always-loaded in the kernel surface."""
    from tee.web.tools import register_web_tools

    register_web_tools(app, Path(project))


def _attach_gateway(app, project: str) -> None:
    """Front the [gateway] backends (A37): their tools land as prefixed
    virtual tools; no [gateway] config, no-op."""
    from tee.gateway.tools import register_gateway

    register_gateway(app, Path(project))


def cmd_serve(args: argparse.Namespace) -> int:
    from tee.config import ProjectConfig
    from tee.server import build_server

    config = ProjectConfig.load(args.project)
    blender_port = args.blender_port
    if blender_port == 9876 and config.blender_port:
        blender_port = config.blender_port

    if args.adapter == "fake":
        app = _build_fake_app(args.project)
    elif args.adapter == "blender":
        app = _build_blender_app(
            args.project, args.blender_host, blender_port, args.allow_code_exec
        )
    elif args.adapter == "unreal":
        app = _build_unreal_app(
            args.project, args.unreal_host, args.unreal_port, args.allow_code_exec
        )
    elif args.adapter == "freecad":
        app = _build_freecad_app(args.project, args.allow_code_exec)
    else:
        print(
            f"adapter '{args.adapter}' is not recognised; available: fake, blender, "
            "unreal, freecad",
            file=sys.stderr,
        )
        return 2
    extract_store = _attach_extract(app, args.project, with_handoff=args.adapter == "blender")
    _attach_assets(app, args.project, extract_store)
    _attach_pins(app, args.project)
    _attach_design(app, args.project)
    _attach_physical(app, args.project)
    _attach_uefn(app, args.project)
    _attach_kb(app, args.project)
    _attach_llm(app, args.project)
    _attach_web(app, args.project)
    _attach_gateway(app, args.project)
    pid_file = _pid_notice(args.project)
    server = build_server(app)
    try:
        server.run()  # stdio transport
    finally:
        app.shutdown()
        if pid_file is not None:
            pid_file.unlink(missing_ok=True)
    return 0


def _pid_notice(project: str) -> Path | None:
    """Advisory single-instance notice: two servers on one project are legal
    (two MCP clients) but worth a warning - they share .tee/ state."""
    import os

    pid_file = Path(project) / ".tee" / "server.pid"
    try:
        if pid_file.exists():
            old = int(pid_file.read_text().strip())
            try:
                os.kill(old, 0)
            except (OSError, ProcessLookupError):
                pass  # stale
            else:
                print(
                    f"note: another tee server (pid {old}) already serves this "
                    "project; both will share .tee/ memory and checkpoints",
                    file=sys.stderr,
                )
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()))
        return pid_file
    except (OSError, ValueError):
        return None


def cmd_doctor(args: argparse.Namespace) -> int:
    from tee import doctor

    if args.emit:
        try:
            print(doctor.emit_config(args.emit, port=args.blender_port))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0
    checks = doctor.run_checks(bridge_port=args.blender_port)
    if args.json:
        print(json.dumps([c.to_payload() for c in checks], indent=1))
        return 1 if any(c.status == "fail" and c.required for c in checks) else 0
    text, code = doctor.render(checks)
    print(text)
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tee", description="Token Efficiency Engine")
    parser.add_argument("--version", action="version", version=f"tee {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the MCP server on stdio")
    serve.add_argument("--adapter", default="fake", help="adapter to serve (fake|blender|unreal)")
    serve.add_argument("--project", default=".", help="project root for .tee/ memory")
    serve.add_argument("--blender-host", default="127.0.0.1", help="Blender bridge host")
    serve.add_argument("--blender-port", type=int, default=9876, help="Blender bridge port")
    serve.add_argument("--unreal-host", default="127.0.0.1", help="Unreal MCP server host")
    serve.add_argument("--unreal-port", type=int, default=8000, help="Unreal MCP server port")
    serve.add_argument(
        "--allow-code-exec",
        action="store_true",
        help="enable the bl_execute_python escape hatch (off by default, A7)",
    )
    serve.set_defaults(fn=cmd_serve)

    doctor = sub.add_parser("doctor", help="environment diagnostics with fixes")
    doctor.add_argument("--json", action="store_true", help="machine-readable output")
    doctor.add_argument(
        "--emit",
        metavar="CLIENT",
        help="print MCP client config (claude-code|claude-desktop|cursor|qwen-code) and exit",
    )
    doctor.add_argument("--blender-port", type=int, default=9876, help="Blender bridge port")
    doctor.set_defaults(fn=cmd_doctor)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
