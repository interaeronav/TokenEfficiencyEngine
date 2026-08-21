"""`tee` command line: serve the MCP server, print environment diagnostics."""

from __future__ import annotations

import argparse
import platform
import shutil
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
    return app


def cmd_serve(args: argparse.Namespace) -> int:
    from tee.server import build_server

    if args.adapter == "fake":
        app = _build_fake_app(args.project)
    elif args.adapter == "blender":
        app = _build_blender_app(
            args.project, args.blender_host, args.blender_port, args.allow_code_exec
        )
    else:
        print(
            f"adapter '{args.adapter}' is not wired yet (unreal arrives in "
            "Phase 3); available: fake, blender",
            file=sys.stderr,
        )
        return 2
    server = build_server(app)
    try:
        server.run()  # stdio transport
    finally:
        app.shutdown()
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Environment diagnostics. Phase 1 scope: interpreter + DCC discovery;
    the full doctor (ports, plugins, wheel ABI) lands in Phase 4."""
    print(f"tee {__version__}")
    print(f"python {platform.python_version()} on {platform.system().lower()}")
    blender = shutil.which("blender")
    print(f"blender on PATH: {blender or 'not found'}")
    for name in ("UnrealEditor", "UnrealEditor-Cmd"):
        found = shutil.which(name)
        if found:
            print(f"{name}: {found}")
    print("note: full diagnostics (sockets, plugins, versions) arrive in Phase 4")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tee", description="Token Efficiency Engine")
    parser.add_argument("--version", action="version", version=f"tee {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the MCP server on stdio")
    serve.add_argument("--adapter", default="fake", help="adapter to serve (fake|blender|unreal)")
    serve.add_argument("--project", default=".", help="project root for .tee/ memory")
    serve.add_argument("--blender-host", default="127.0.0.1", help="Blender bridge host")
    serve.add_argument("--blender-port", type=int, default=9876, help="Blender bridge port")
    serve.add_argument(
        "--allow-code-exec",
        action="store_true",
        help="enable the bl_execute_python escape hatch (off by default, A7)",
    )
    serve.set_defaults(fn=cmd_serve)

    doctor = sub.add_parser("doctor", help="environment diagnostics")
    doctor.set_defaults(fn=cmd_doctor)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
