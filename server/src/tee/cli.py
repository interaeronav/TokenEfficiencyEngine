"""`tee` command line: serve the MCP server, print environment diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from tee import __version__

if TYPE_CHECKING:
    from tee.app import TeeApp
    from tee.kernel.adapter import Adapter


class Lane(NamedTuple):
    """What one `--adapter NAME` contributes to the served app.

    Building the adapter and registering its tools are two phases because
    the app in between is SHARED: `tee serve --adapter blender --adapter
    partkiln --adapter seamkiln` (the Desktop manifest since 2026-09-04)
    holds every adapter named in ONE TeeApp, so a lane cannot construct the
    app itself. It yields its adapter; `attach` runs once the app exists -
    partkiln's warm-up job must land in the shared app's job manager, and
    Blender's bl_*/hb_* tools register on the shared registry."""

    name: str
    adapter: Adapter
    attach: Callable[[TeeApp], None] | None = None


def _fake_lane() -> Lane:
    from tee.kernel.adapter import FakeAdapter

    return Lane("fake", FakeAdapter())


def _blender_lane(host: str, port: int) -> Lane:
    from tee.adapters.blender.adapter import BlenderAdapter
    from tee.adapters.blender.tools import register_blender_tools
    from tee.adapters.blender.wire import BlenderWire

    adapter = BlenderAdapter(BlenderWire(host=host, port=port))

    def attach(app: TeeApp) -> None:
        register_blender_tools(app, adapter)
        from tee.adapters.blender.homebuilder import register_hb_tools

        register_hb_tools(app, adapter)  # the joinery lane (A37); refuses w/ fix if HB absent

    return Lane("blender", adapter, attach)


def _unreal_lane(host: str, port: int) -> Lane:
    from tee.adapters.unreal.adapter import UnrealAdapter
    from tee.adapters.unreal.tools import register_unreal_tools
    from tee.adapters.unreal.wire import UnrealWire

    adapter = UnrealAdapter(UnrealWire(host=host, port=port))
    return Lane("unreal", adapter, lambda app: register_unreal_tools(app, adapter))


def _seamkiln_lane(project: str) -> Lane:
    """seamkiln needs no bridge and no running application - the garment
    kernel is a library, so the adapter is live the moment it is built."""
    from tee.adapters.seamkiln import SeamkilnAdapter

    return Lane("seamkiln", SeamkilnAdapter(project))


def _partkiln_lane(project: str) -> Lane:
    """A66: partkiln headless. Like seamkiln the kernel is a library, so the
    adapter is live the moment it is built - but unlike seamkiln it may live
    in a sidecar interpreter and it pays a 26 s cold `import OCP` (P0a). Law
    17 says no call ever waits on that, so the import is submitted as an
    interactive job - on the SHARED app's job manager, hence in `attach` -
    and `probe`, `tee_scene_summary` and `tee_checkpoint` answer from the
    in-process mirror until it lands."""
    from tee.adapters.partkiln import PartkilnAdapter
    from tee.config import ProjectConfig

    config = ProjectConfig.load(project)
    adapter = PartkilnAdapter(project, config=config.partkiln)
    # jobs.submit("partkiln_warm", ..., qos="interactive")
    return Lane("partkiln", adapter, lambda app: adapter.submit_warm(app.jobs))


def _godot_lane(project: str, port: int) -> Lane:
    """A49: Godot headless. The adapter imports the project first if it has
    never been imported - a project without a .godot directory hangs
    `--headless -s` silently, which is a duty rather than a caveat."""
    from tee.adapters.godot import GodotAdapter, GodotWire

    adapter = GodotAdapter(wire=GodotWire(port=port), project=Path(project))
    adapter.ensure_bridge(repo_root=Path(__file__).resolve().parents[3])
    return Lane("godot", adapter)


def build_app(
    lanes: list[Lane],
    project: str,
    *,
    allow_code_exec: bool,
    default_adapter: str | None = None,
) -> TeeApp:
    """ONE TeeApp for every lane, in the order given, and NO lane the hub.

    A68 (owner: "decentralize the use of Blender or Unreal Engine"): the
    order of `--adapter` no longer implies a default. An omitted adapter=
    resolves by what the batch contains - entity id, create kind, op verb -
    and only a batch several lanes accept needs a tie-breaker, which an
    operator declares with `--default-adapter NAME` (Law 19: default and
    declare; tee_status reports it). A library caller who builds several
    adapters with no default keeps SI-B6's loud `adapter_required` for the
    ambiguous case. Lanes attach only after the app exists, because what
    they attach (tools, the partkiln warm-up job) belongs to the shared app,
    not to a private one per adapter."""
    from tee.app import TeeApp

    adapters: dict[str, Adapter] = {}
    for lane in lanes:
        if lane.name in adapters:
            raise ValueError(f"adapter '{lane.name}' is listed twice; name each adapter once")
        adapters[lane.name] = lane.adapter
    app = TeeApp(
        adapters,
        project_root=Path(project),
        allow_code_exec=allow_code_exec,
        default_adapter=default_adapter,
    )
    for lane in lanes:
        if lane.attach is not None:
            lane.attach(app)
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


def _attach_pipeline(app, project: str) -> None:
    """The pipeline lane (A43): declared steps for this project, if any.
    Registration is unconditional - the tool itself reports an absent
    declaration with the fix, which is friendlier than a missing tool."""
    from tee.pipeline.tools import (
        register_adhoc_tools,
        register_pipeline_tools,
        register_run_tools,
    )

    register_pipeline_tools(app, Path(project))
    register_adhoc_tools(app, Path(project))
    register_run_tools(app, Path(project))


def _attach_capture(app, project: str, extract_store) -> None:
    """Register the reality-capture lane (A42 T2): ingest rides the extract
    store; reconstruct gates loudly on disk, engine presence and set size."""
    from tee.capture.tools import register_capture_tools

    register_capture_tools(app, Path(project), extract_store=extract_store)


def _attach_pointcloud(app, project: str) -> None:
    """Register the point-cloud scan-prep lane (A67). Needs the `pointcloud`
    extra for LAS/LAZ; skips silently otherwise, as the kernel works without
    it. This lane does NOT register clouds - capture_register already does."""
    try:
        from tee.pointcloud.tools import register_pointcloud_tools
    except ImportError:
        return
    register_pointcloud_tools(app, Path(project))


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


def _attach_purge(app, project: str) -> None:
    """Register tee_purge (A52). Pure stdlib; always on."""
    from tee.purge import register_purge_tools

    register_purge_tools(app, Path(project))


def _attach_pdf(app, project: str) -> None:
    """Register pdf_* (A48). fpdf2/pypdf live in the [pdf] extra and refuse
    with their install line at call time, so registration is
    unconditional - a tool that vanishes when its extra is missing is
    indistinguishable from one that never existed."""
    from tee.pdf import register_pdf_tools

    register_pdf_tools(app, Path(project))


def _attach_senses(app, project: str) -> None:
    """Register sense_* (A47). Vision needs the local shim and audio needs
    the extract extra; both refuse with their exact fix at call time, so
    registration is unconditional - a tool that vanishes when its provider
    is down is indistinguishable from one that never existed, which is the
    confusion this lane was built to end."""
    from tee.senses import register_sense_tools

    register_sense_tools(app, Path(project))


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


def _freecad_lane() -> Lane:
    """The fabrication lane (A37): FreeCADAdapter over the neka-nat bridge
    (the P0-decided one bridge) + fc_drawing / fc_export."""
    from tee.adapters.freecad.adapter import FreeCADAdapter
    from tee.adapters.freecad.tools import register_freecad_tools

    adapter = FreeCADAdapter()
    return Lane("freecad", adapter, lambda app: register_freecad_tools(app, adapter))


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


ADAPTER_NAMES = ("fake", "blender", "unreal", "freecad", "godot", "seamkiln", "partkiln")


def _lane(name: str, args: argparse.Namespace, blender_port: int) -> Lane:
    if name == "fake":
        return _fake_lane()
    if name == "blender":
        return _blender_lane(args.blender_host, blender_port)
    if name == "unreal":
        return _unreal_lane(args.unreal_host, args.unreal_port)
    if name == "freecad":
        return _freecad_lane()
    if name == "seamkiln":
        return _seamkiln_lane(args.project)
    if name == "godot":
        return _godot_lane(args.project, args.godot_port)
    if name == "partkiln":
        return _partkiln_lane(args.project)
    raise ValueError(name)  # unreachable: cmd_serve checks every name first


def cmd_serve(args: argparse.Namespace) -> int:
    from tee.config import ProjectConfig
    from tee.server import build_server

    # `--adapter` repeats; omitted still means fake. Every name is checked
    # before any adapter is built, so a typo in the third cannot leave the
    # first two connected to their bridges for nothing.
    names: list[str] = list(args.adapter or ["fake"])
    for name in names:
        if name not in ADAPTER_NAMES:
            print(
                f"adapter '{name}' is not recognised; available: {', '.join(ADAPTER_NAMES)}",
                file=sys.stderr,
            )
            return 2
        if names.count(name) > 1:
            print(
                f"adapter '{name}' is listed more than once; name each adapter once",
                file=sys.stderr,
            )
            return 2
    default = getattr(args, "default_adapter", None)
    if default is not None and default not in names:
        print(
            f"--default-adapter '{default}' is not among the served adapters "
            f"({', '.join(names)}); list it with --adapter or drop the flag",
            file=sys.stderr,
        )
        return 2

    config = ProjectConfig.load(args.project)
    blender_port = args.blender_port
    if blender_port == 9876 and config.blender_port:
        blender_port = config.blender_port

    lanes = [_lane(name, args, blender_port) for name in names]
    app = build_app(
        lanes, args.project, allow_code_exec=args.allow_code_exec, default_adapter=default
    )
    extract_store = _attach_extract(app, args.project, with_handoff="blender" in app.adapters)
    _attach_assets(app, args.project, extract_store)
    _attach_capture(app, args.project, extract_store)
    _attach_pointcloud(app, args.project)
    _attach_pipeline(app, args.project)
    _attach_pins(app, args.project)
    _attach_design(app, args.project)
    _attach_senses(app, args.project)
    _attach_pdf(app, args.project)
    _attach_purge(app, args.project)
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
    # No `default=`: argparse APPENDS to a list default, so default=["fake"]
    # would turn `--adapter blender` into fake + blender. cmd_serve resolves
    # an omitted flag to ["fake"].
    serve.add_argument(
        "--adapter",
        action="append",
        metavar="NAME",
        help=(
            "adapter to serve (fake|blender|unreal|freecad|godot|seamkiln|partkiln); "
            "repeatable - all named adapters share one server and none is the hub: an "
            "omitted adapter= routes by the batch's content (default: fake)"
        ),
    )
    serve.add_argument(
        "--default-adapter",
        metavar="NAME",
        help=(
            "the served adapter a batch goes to when SEVERAL lanes accept it and no "
            "adapter= was given; undeclared, such a batch is refused naming the lanes. "
            "tee_status reports a declared default"
        ),
    )
    serve.add_argument(
        "--godot-port", type=int, default=9879, help="Godot bridge port (9876/9877 are Blender's)"
    )
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
