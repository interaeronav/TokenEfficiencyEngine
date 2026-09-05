"""`tee serve --adapter A --adapter B`: one app, every adapter, and no lane
the hub.

Why (measured by the lead, 2026-09-04): Claude Desktop's manifest served
`--adapter blender` alone and `--adapter` was a single string, so the pk_*
and sk_* lanes shipped in 0.20.0/0.21.0 refused `pk_not_served` /
`seamkiln_not_served` from the very product that installs them - unreachable
BY CONSTRUCTION. The kernel already held several adapters (`TeeApp(adapters)`);
only the CLI built exactly one. The first ruling made the first `--adapter`
the declared default for an omitted adapter=. A68 (2026-09-05, owner:
"decentralize the use of Blender or Unreal Engine") revised it: the order
implies nothing, an omitted adapter= routes by the batch's CONTENT, and a
tie-breaker exists only when an operator declares one with
`--default-adapter NAME` (Law 19: default and declare; tee_status reports
it). SI-B6 stands for the undeclared ambiguous case: several lanes accept
the batch and none was declared - fail loud, naming them.

No test here touches a bridge: fake, seamkiln and partkiln all construct
without a kernel or a running application, Blender's adapter only connects
on first use, and partkiln's warm-up job is recorded instead of run so no
test pays the cold `import OCP`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import anyio
import pytest
from mcp.client import Client
from mcp.types import TextContent

from tee import cli
from tee.app import Route, TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.errors import AdapterUnavailable, TeeError
from tee.server import build_server

MANIFEST = Path(__file__).resolve().parents[2] / "packaging" / "mcpb_manifest.json"
DEFAULT_UNAVAILABLE_FIX = "Start the DCC and its bridge, then retry; check with tee_status."


def _payload(result):
    block = result.content[0]
    assert isinstance(block, TextContent)
    return json.loads(block.text)


class _Serve:
    """The REAL `cmd_serve` with only the stdio transport stubbed: every lane
    is built, every `_attach_*` runs, and the app is captured where
    `server.run()` would have blocked. partkiln's `submit_warm` is recorded,
    not run, so the test can assert it received the SHARED app's job manager
    without paying the cold OCP import."""

    def __init__(self, monkeypatch, project: Path):
        import tee.server
        from tee.adapters.partkiln.adapter import PartkilnAdapter

        self.project = project
        self.app: TeeApp | None = None
        self.status: dict | None = None
        self.warm_jobs = None
        self.want_status = False
        box = self

        class _Transport:
            def __init__(self, app):
                box.app = app

            def run(self):
                if box.want_status:  # at serve time: lanes attached, nothing shut down
                    box.status = box.app.status()

        def submit_warm(adapter, jobs):
            box.warm_jobs = jobs
            return "partkiln_warm:stub"

        monkeypatch.setattr(tee.server, "build_server", _Transport)
        monkeypatch.setattr(PartkilnAdapter, "submit_warm", submit_warm)

    def __call__(self, *argv: str, status: bool = False) -> int:
        self.app = self.status = self.warm_jobs = None
        self.want_status = status
        return cli.main(["serve", *argv, "--project", str(self.project)])


@pytest.fixture
def serve(monkeypatch, tmp_path) -> _Serve:
    return _Serve(monkeypatch, tmp_path)


def test_adapter_repeats_in_order_and_no_lane_is_the_hub(serve):
    assert serve("--adapter", "fake", "--adapter", "seamkiln", status=True) == 0
    app = serve.app
    assert list(app.adapters) == ["fake", "seamkiln"]
    assert app.default_adapter is None, "order implies no default (A68)"
    with pytest.raises(TeeError) as err:
        app.resolve_adapter(None)
    assert err.value.code == "adapter_required" and "fake, seamkiln" in err.value.fix
    assert app.resolve_adapter("seamkiln") == "seamkiln"
    assert "default_adapter" not in serve.status
    assert set(serve.status["adapters"]) == {"fake", "seamkiln"}
    assert "bl_build_from_plan" not in app.registry.names(), "handoff needs a served Blender"
    # content still routes: a verb only seamkiln speaks goes there, a bare
    # create to the lane that takes one - no default needed for either. A
    # kind the reference fake ALSO claims (it takes any kind) is honestly
    # ambiguous, and the refusal names both.
    assert app.route_batch([{"op": "drape", "props": {}}], None).adapter == "seamkiln"
    assert app.route_batch([{"op": "create", "name": "x"}], None).adapter == "fake"
    with pytest.raises(TeeError) as err:
        app.route_batch([{"op": "create", "kind": "panel"}], None)
    assert err.value.code == "adapter_required" and "fake, seamkiln" in err.value.message

    # the same order, reversed, still declares nothing
    assert serve("--adapter", "seamkiln", "--adapter", "fake") == 0
    assert list(serve.app.adapters) == ["seamkiln", "fake"]
    assert serve.app.default_adapter is None


def test_a_default_is_declared_only_by_the_flag(serve):
    assert (
        serve(
            "--adapter",
            "fake",
            "--adapter",
            "seamkiln",
            "--default-adapter",
            "seamkiln",
            status=True,
        )
        == 0
    )
    app = serve.app
    assert app.default_adapter == "seamkiln"
    assert app.resolve_adapter(None) == "seamkiln"
    assert serve.status["default_adapter"] == "seamkiln"
    # a declared default breaks TIES only; content still wins
    assert app.route_batch([{"op": "create", "name": "x"}], None).adapter == "fake"


def test_omitted_flag_still_means_fake_alone(serve):
    assert serve(status=True) == 0
    assert list(serve.app.adapters) == ["fake"]
    assert serve.app.default_adapter is None
    assert serve.app.resolve_adapter(None) == "fake", "the sole lane needs no declaration"
    assert "default_adapter" not in serve.status


def test_partkiln_warm_up_lands_in_the_shared_app(serve):
    """Law 17's background import is submitted AFTER the one app exists, to
    ITS job manager - not to a private app the lane built for itself."""
    assert serve("--adapter", "fake", "--adapter", "partkiln") == 0
    assert list(serve.app.adapters) == ["fake", "partkiln"]
    assert serve.warm_jobs is serve.app.jobs


def test_the_desktop_manifest_serves_three_lanes_and_declares_no_hub(serve):
    """The manifest serves blender, partkiln and seamkiln and declares NO
    default (A68): an existing Desktop batch of Blender kinds still lands on
    Blender - by content, not by position - and a partkiln batch lands on
    partkiln without naming it."""
    args = json.loads(MANIFEST.read_text())["server"]["mcp_config"]["args"]
    names = [args[i + 1] for i, flag in enumerate(args) if flag == "--adapter"]
    assert names == ["blender", "partkiln", "seamkiln"]
    assert "--default-adapter" not in args

    assert serve(*[word for name in names for word in ("--adapter", name)]) == 0
    app = serve.app
    assert list(app.adapters) == names
    assert app.default_adapter is None
    cube = [{"op": "create", "kind": "cube", "name": "Cube"}]
    part = [{"op": "create", "kind": "part", "name": "bracket"}]
    assert app.route_batch(cube, None) == Route("blender", "kind")
    assert app.route_batch(part, None) == Route("partkiln", "kind")
    assert app.route_batch([{"op": "drape", "props": {}}], None).adapter == "seamkiln"
    registered = set(app.registry.names())
    assert any(n.startswith("bl_") for n in registered), "Blender's lane attached"
    assert any(n.startswith("hb_") for n in registered), "and its joinery lane"
    assert {"pk_probe", "sk_avatar"} <= registered
    try:
        import tee.extract.tools  # noqa: F401
    except ImportError:
        pass
    else:
        assert "bl_build_from_plan" in registered, "handoff rides with a served Blender"
    # The defect itself: from a Desktop-shaped server these two refused
    # `*_not_served`. Any other answer (a health dict, or a kernel-absent
    # refusal naming its install) means the lane is served.
    for name, not_served in (("pk_probe", "pk_not_served"), ("sk_avatar", "seamkiln_not_served")):
        try:
            out = app.registry.call(name, {})
        except TeeError as exc:
            assert exc.code != not_served, f"{name} still refuses {exc.code}"
        else:
            assert isinstance(out, dict)
    assert serve.warm_jobs is app.jobs


def test_unknown_or_repeated_names_refuse_before_any_adapter_is_built(serve, capsys):
    assert serve("--adapter", "blender", "--adapter", "nope") == 2
    err = capsys.readouterr().err
    assert "adapter 'nope' is not recognised" in err
    assert "available: fake, blender, unreal, freecad, godot, seamkiln, partkiln" in err
    assert serve.app is None, "nothing was built"

    assert serve("--adapter", "fake", "--adapter", "fake") == 2
    assert "listed more than once" in capsys.readouterr().err
    assert serve.app is None

    assert serve("--adapter", "fake", "--adapter", "seamkiln", "--default-adapter", "blender") == 2
    err = capsys.readouterr().err
    assert "--default-adapter 'blender' is not among the served adapters (fake, seamkiln)" in err
    assert serve.app is None


def test_build_app_refuses_a_lane_listed_twice(tmp_path):
    """The library-level guard: a dict would keep the last one silently."""
    lanes = [cli._fake_lane(), cli._fake_lane()]
    with pytest.raises(ValueError, match="listed twice"):
        cli.build_app(lanes, str(tmp_path), allow_code_exec=False)


def test_several_adapters_without_a_default_keep_si_b6_loud(tmp_path):
    app = TeeApp({"fake": FakeAdapter(), "fake2": FakeAdapter()}, project_root=tmp_path)
    try:
        with pytest.raises(TeeError) as err:
            app.resolve_adapter(None)
        assert err.value.code == "adapter_required"
        assert "fake, fake2" in err.value.fix
        assert "default_adapter" not in app.status()
    finally:
        app.shutdown()


def test_a_default_that_names_no_adapter_is_a_startup_error(tmp_path):
    with pytest.raises(ValueError) as err:
        TeeApp({"fake": FakeAdapter()}, project_root=tmp_path, default_adapter="blender")
    assert "'blender'" in str(err.value) and "fake" in str(err.value)


def test_a_declared_default_wins_and_is_reported(tmp_path):
    app = TeeApp(
        {"fake": FakeAdapter(), "fake2": FakeAdapter()},
        project_root=tmp_path,
        default_adapter="fake2",
    )
    try:
        assert app.resolve_adapter(None) == "fake2"
        assert app.resolve_adapter("fake") == "fake"
        assert app.status()["default_adapter"] == "fake2"
    finally:
        app.shutdown()


def test_a_down_default_names_the_other_served_adapters(tmp_path):
    """New failure mode of a declared default: Blender down, and the caller
    wanted partkiln. The refusal names the way there. A single-adapter
    server keeps the old text byte for byte."""
    down = FakeAdapter()
    down._connected = False
    app = TeeApp(
        {"fake": down, "fake2": FakeAdapter()}, project_root=tmp_path, default_adapter="fake"
    )
    try:
        with pytest.raises(AdapterUnavailable) as err:
            app.adapter(app.resolve_adapter(None))
        assert err.value.fix.startswith(DEFAULT_UNAVAILABLE_FIX)
        assert "adapter=" in err.value.fix and "fake2" in err.value.fix
    finally:
        app.shutdown()

    solo = TeeApp({"fake": down}, project_root=tmp_path)
    try:
        with pytest.raises(AdapterUnavailable) as err:
            solo.adapter("fake")
        assert err.value.fix == DEFAULT_UNAVAILABLE_FIX
    finally:
        solo.shutdown()


def test_an_ambiguous_batch_with_no_declared_default_refuses_on_the_wire(tmp_path):
    """Two lanes that both take everything, nothing declared: SI-B6 loud."""
    app = TeeApp({"fake": FakeAdapter(), "fake2": FakeAdapter()}, project_root=tmp_path)
    server = build_server(app)

    async def main():
        async with Client(server) as client:
            out = _payload(
                await client.call_tool("tee_batch", {"ops": [{"op": "create", "name": "x"}]})
            )
            assert out["ok"] is False
            assert out["error"]["code"] == "adapter_required"
            assert "fake, fake2" in out["error"]["message"]

    try:
        anyio.run(main)
    finally:
        app.shutdown()


def test_omitted_adapter_routes_to_the_declared_default_on_the_wire(tmp_path):
    app = TeeApp(
        {"fake": FakeAdapter(), "fake2": FakeAdapter()},
        project_root=tmp_path,
        default_adapter="fake",
    )
    server = build_server(app)

    async def main():
        async with Client(server) as client:
            status = _payload(await client.call_tool("tee_status", {}))
            assert status["default_adapter"] == "fake"
            routed = _payload(
                await client.call_tool(
                    "tee_batch", {"ops": [{"op": "create", "kind": "mesh", "name": "Routed"}]}
                )
            )
            assert routed["ok"] is True and routed["created"] == ["e1"]
            assert routed["adapter"] == "fake" and routed["routed"] == "declared default"
            named = _payload(
                await client.call_tool(
                    "tee_batch",
                    {
                        "adapter": "fake2",
                        "ops": [{"op": "create", "kind": "mesh", "name": "Named"}],
                    },
                )
            )
            assert named["ok"] is True and named["adapter"] == "fake2"
            assert "routed" not in named, "an explicit adapter= is not a routing decision"
            assert _payload(await client.call_tool("tee_scene_summary", {}))["ok"] is True

    try:
        anyio.run(main)
        assert [e.name for e in app.caches["fake"].entities.values()] == ["Routed"]
        assert [e.name for e in app.caches["fake2"].entities.values()] == ["Named"]
    finally:
        app.shutdown()


def test_seamkiln_install_hint_names_the_restart(monkeypatch):
    """An editable install is a .pth hook that site.py reads once at
    interpreter start - measured: written after startup it stays invisible,
    invalidate_caches() included - so a running server keeps refusing after
    the named fix. The hint has to say so, in both of its copies."""
    from tee.adapters.seamkiln import adapter as sk_adapter
    from tee.adapters.seamkiln import tools as sk_tools

    assert sk_adapter.INSTALL_HINT == sk_tools.INSTALL_HINT
    assert sk_adapter.INSTALL_HINT.endswith("then restart the server")
    monkeypatch.setitem(sys.modules, "seamkiln", None)  # makes `import seamkiln` raise
    with pytest.raises(TeeError) as err:
        sk_tools._need()
    assert err.value.code == "seamkiln_unavailable"
    assert "restart the server" in err.value.fix
