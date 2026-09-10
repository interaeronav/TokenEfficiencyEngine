"""Release-gating lint over the MCP tool surface (decision A6).

Client failure modes this protects against are silent (whole-catalog drops,
content drops), so the assertions run against the real tools/list output as
an MCP client sees it.
"""

import json

import anyio
import pytest
from mcp.client import Client

from tee.app import TeeApp
from tee.kernel.adapter import FakeAdapter
from tee.kernel.budget import estimate_tokens
from tee.server import build_server

MAX_TOOLS = 17
MAX_DESCRIPTION_BYTES = 2_048
MAX_TOTAL_DEFINITION_TOKENS = 8_000


@pytest.fixture(scope="module")
def tools():
    app = TeeApp({"fake": FakeAdapter()}, project_root=".")
    server = build_server(app)

    async def fetch():
        async with Client(server) as client:
            listed = await client.list_tools()
            return listed.tools

    try:
        return anyio.run(fetch)
    finally:
        app.shutdown()


def test_surface_is_small(tools):
    assert 1 <= len(tools) <= MAX_TOOLS


def test_every_input_schema_is_a_plain_object(tools):
    for tool in tools:
        schema = tool.input_schema
        assert isinstance(schema, dict), tool.name
        assert schema.get("type") == "object", tool.name
        for key in ("anyOf", "oneOf", "allOf"):
            assert key not in schema, f"{tool.name}: root-level {key} breaks clients"
        for prop_name, prop in (schema.get("properties") or {}).items():
            assert isinstance(prop, dict), f"{tool.name}.{prop_name}: boolean schemas break clients"


def test_no_output_schema_emitted(tools):
    for tool in tools:
        assert tool.output_schema in (None, {}), (
            f"{tool.name}: outputSchema triggers silent tool drops in Claude "
            "Desktop and historic drop-all in Claude Code (A6)"
        )


def test_descriptions_are_present_and_bounded(tools):
    for tool in tools:
        assert tool.description and tool.description.strip(), tool.name
        assert len(tool.description.encode()) <= MAX_DESCRIPTION_BYTES, tool.name


def test_total_definition_budget(tools):
    total = estimate_tokens(json.dumps([t.model_dump(mode="json") for t in tools], default=str))
    assert total <= MAX_TOTAL_DEFINITION_TOKENS, (
        f"always-loaded tool definitions cost ~{total} tokens; "
        f"budget is {MAX_TOTAL_DEFINITION_TOKENS}"
    )


def test_tool_names_are_prefixed_and_stable(tools):
    for tool in tools:
        assert tool.name.startswith("tee_"), tool.name


EXPECTED_TOOL_COUNT = 17


def test_tool_count_matches_expectation(tools):
    # silent whole-catalog drops are the failure mode this canary catches;
    # update the constant deliberately when adding/removing a tool
    assert len(tools) == EXPECTED_TOOL_COUNT


def test_schemas_carry_no_generated_padding(tools):
    # The served schema is documentation for the model - validation runs on
    # the pydantic signature model. Pydantic titles and anyOf-null wrappers
    # measured ~19% of the wire surface before _slim_schema (SI-1).
    for tool in tools:
        schema = tool.input_schema
        assert "title" not in schema, tool.name
        for prop_name, prop in (schema.get("properties") or {}).items():
            where = f"{tool.name}.{prop_name}"
            assert "title" not in prop, where
            if "default" in prop:
                assert prop["default"] is not None, where
            for branch in prop.get("anyOf", []):
                assert branch.get("type") != "null", where


def test_adapter_params_advertise_no_default(tools):
    # SI-B6: adapter= resolves server-side to the sole configured adapter;
    # a wire-visible 'fake' default fails on every real deployment.
    for tool in tools:
        prop = (tool.input_schema.get("properties") or {}).get("adapter")
        if prop is not None:
            assert "default" not in prop, tool.name


def test_adapter_params_carry_one_short_line(tools):
    # A68: a bare {"type":"string"} told the model nothing about what to put
    # there. One line, capped, so eight copies stay cheap on the wire.
    seen = 0
    for tool in tools:
        prop = (tool.input_schema.get("properties") or {}).get("adapter")
        if prop is not None:
            seen += 1
            assert prop.get("description"), tool.name
            assert len(prop["description"].encode()) <= 64, tool.name
    assert seen == 8


def test_mcpb_manifest_tool_list_matches_surface(tools):
    """The store-facing manifest names every always-loaded tool and nothing
    else - it went stale once (16 entries while the server served 17)."""
    import json
    from pathlib import Path

    manifest = Path(__file__).resolve().parents[2] / "packaging" / "mcpb_manifest.json"
    declared = {t["name"] for t in json.loads(manifest.read_text())["tools"]}
    served = {t.name for t in tools}
    assert declared == served, (
        f"manifest drift: only-in-manifest={sorted(declared - served)}, "
        f"only-on-server={sorted(served - declared)}"
    )


# A66/A68: the surface figure is an invariant quoted in the lane guides, the
# CHANGELOG and every campaign script - and until now NOTHING measured it. It
# moved 2,033 -> 2,129 at bd70096 (A68 P2 gave the shared `adapter=` parameter
# a one-line description on eight tools, +96 tok) and four commits' worth of
# prose went on printing the old number, this file's author included. A count
# canary does not catch that: the tool count never changed.
EXPECTED_WIRE_TOKENS = 2_129


def _wire_tokens(tools) -> int:
    # by_alias + exclude_none is what the SDK actually puts on the wire; a bare
    # model_dump counts ~470 tokens of null padding no client ever sees. This
    # is the same measurement benchmarks/run_benchmarks.py prints as `surface:`.
    return estimate_tokens(
        [t.model_dump(by_alias=True, mode="json", exclude_none=True) for t in tools]
    )


def test_wire_token_cost_is_pinned(tools):
    wire = _wire_tokens(tools)
    assert wire == EXPECTED_WIRE_TOKENS, (
        f"always-loaded surface is {wire} tok on the wire, pinned at "
        f"{EXPECTED_WIRE_TOKENS} ({wire - EXPECTED_WIRE_TOKENS:+d}). Adding a tool, a "
        "description or a schema field is what moves this. If the change is deliberate, "
        "update EXPECTED_WIRE_TOKENS and the `N wire tokens` figure every docs/*-lane.md "
        "prints - test_lane_docs_quote_the_measured_surface asserts they agree."
    )


def test_lane_docs_quote_the_measured_surface(tools):
    """A lane guide states the surface cost as current fact; a stale one is a lie
    told to every reader. The figure it prints must be the figure we measure."""
    import re
    from pathlib import Path

    docs = sorted((Path(__file__).resolve().parents[2] / "docs").glob("*-lane.md"))
    assert docs, "no lane guides found; this test would pass vacuously"
    quoted = [
        (doc.name, int(m.group(1).replace(",", "")))
        for doc in docs
        for m in re.finditer(r"([\d,]+) wire tokens", doc.read_text())
    ]
    assert quoted, (
        "no lane guide states the surface cost. One of them should: it is the "
        "invariant the whole progressive-disclosure design rests on."
    )
    stale = [(name, n) for name, n in quoted if n != _wire_tokens(tools)]
    assert not stale, (
        f"lane guides print a surface cost we do not measure: {stale}; "
        f"measured {_wire_tokens(tools)} tok on the wire."
    )


def test_no_hermetic_engine_test_reads_this_machine():
    """A hermetic test that asks the MACHINE what it has is hermetic only on
    the machine you ran it on.

    Shipped once, on 2026-09-07: one assertion in `test_windtunnel_cfmesh.py`
    called the OpenFOAM finder with an EMPTY config, which searches the real
    install locations. It passed on a container with OpenFOAM v2606 and failed
    on a CI runner with none - in the file whose own docstring says "the cfMesh
    writer, with no cfMesh". The engine finders take a config for exactly this
    reason: the fixtures' fake install is a config away.

    `test_windtunnel_live.py` is excluded because reading the machine is its
    entire job; it is `cfd`-marked and deselected by default.
    """
    import re
    from pathlib import Path

    tests = Path(__file__).resolve().parent
    suspects = sorted(p for p in tests.glob("test_*.py") if p.name != "test_windtunnel_live.py")
    assert suspects, "no test files found; this test would pass vacuously"
    # `find_openfoam({})`, `find_su2({})`, `probe({})` - a call whose only
    # argument is an empty dict asks the machine what it has
    empty_cfg = re.compile(r"\b(find_\w+|probe)\(\s*\{\s*\}\s*[,)]")
    # ...which is legitimate in exactly one shape: a test that BLINDS the
    # machine first and then asserts the refusal an absent engine produces
    # (test_windtunnel_readers.py does this - it patches `shutil.which`, HOME
    # and the environment, then expects `wt_su2_missing`). What is forbidden
    # is depending on whatever this particular machine happens to have.
    blinds = ('"which"', "_foam_candidates", "_binary_candidates")
    guilty = []
    for path in suspects:
        body: list[str] = []
        start = 0
        lines = [*path.read_text().splitlines(), "def test_END():"]
        for i, line in enumerate(lines, 1):
            if line.startswith("def ") or line.startswith("class "):
                text = "\n".join(body)
                if any(
                    empty_cfg.search(ln) and not ln.lstrip().startswith("#") for ln in body
                ) and not any(b in text for b in blinds):
                    guilty.append(f"{path.name}:{start}")
                body, start = [], i
            body.append(line)
    assert not guilty, (
        "these tests read the machine's engines instead of the fixtures' fake "
        f"install: {guilty}. Pass the app's own config (`app.config.windtunnel`) "
        "- an empty dict searches the real install locations, so the result "
        "depends on who is running the suite. If the point IS the absent-engine "
        "refusal, blind the machine first the way test_windtunnel_readers.py does."
    )


def test_the_makefile_never_lets_uv_resync_the_venv():
    """`uv run` SYNCS the venv to the lock unless told not to, and this
    project's engine extras are installed ON TOP of the locked set with
    `uv pip install` - the `mcpb` target prints the restore line itself. A
    sync drops them.

    `make test` was the worst of the four bare invocations: it would remove
    the extras and then every suite that needs them would SKIP rather than
    fail, so the only trace is a skip count nobody reads. Measured 2026-09-08:
    a bare `uv run` in this tree reported "Installed 1 package" - the sync
    doing its job, on a checkout where nothing happened to need removing.
    """
    import re
    from pathlib import Path

    makefile = Path(__file__).resolve().parents[1] / "Makefile"
    assert makefile.is_file(), makefile
    bare = [
        f"{i}: {line.strip()}"
        for i, line in enumerate(makefile.read_text().splitlines(), 1)
        if re.match(r"^\t*uv run (?!--no-sync|--frozen)", line)
    ]
    assert not bare, (
        f"these Makefile recipes let uv re-sync the venv: {bare}. Add "
        "`--no-sync` (or `--frozen`): a bare `uv run` reinstalls from the lock "
        "and drops every pip-installed extra, after which the suites that need "
        "them skip instead of failing."
    )


def test_the_lockfile_records_the_version_pyproject_declares():
    """CI runs `uv sync --locked`, which refuses a lockfile that does not match
    `pyproject.toml` — so a version bump without `uv lock` fails the build
    BEFORE a single test runs:

        error: The lockfile at `uv.lock` needs to be updated, but `--locked`
        was provided.

    That has cost this branch three CI cycles (0.24.1, the 0.29.0 renumber, and
    0.30.0). The lock records `tee-engine`'s own version, so the mismatch is
    visible locally in milliseconds instead of three minutes into a runner.
    """
    import re
    import tomllib
    from pathlib import Path

    server = Path(__file__).resolve().parents[1]
    declared = tomllib.loads((server / "pyproject.toml").read_text())["project"]["version"]
    lock = (server / "uv.lock").read_text()
    m = re.search(r'name = "tee-engine"\nversion = "([^"]+)"', lock)
    assert m, "uv.lock has no tee-engine entry; has the distribution been renamed?"
    assert m.group(1) == declared, (
        f"pyproject declares {declared} and uv.lock records {m.group(1)}. "
        "Run `uv lock` (never `uv sync`, which drops the pip-installed extras) "
        "and commit the lock with the bump."
    )


def test_the_shipped_manifest_declares_the_version_pyproject_does():
    """The store-facing manifest carries its own `version`, and nothing
    compared it to pyproject - so it drifted. Measured 2026-09-10: the
    INSTALLED Desktop extension declared 0.30.1 while every tracked file
    still said 0.30.0, because the bundle had been built with the manifest
    edited out of tree. `make mcpb` from that tree could not reproduce the
    thing the owner was running, and two `tee-engine` distributions were
    visible at once - only sys.path order deciding which version the server
    reported about itself.

    Same shape as A46's defect one level out: one question, two answers.
    """
    import json
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    declared = tomllib.loads((root / "server" / "pyproject.toml").read_text())["project"]["version"]
    manifest = json.loads((root / "packaging" / "mcpb_manifest.json").read_text())["version"]
    assert manifest == declared, (
        f"pyproject declares {declared} and the mcpb manifest declares {manifest}. "
        "Bump both in the same commit, with `uv lock`, or the installed "
        "extension reports a version no tracked file can rebuild."
    )


# --- which adapters the shipped manifest serves ------------------------------
#
# The manifest's `tools` list is checked above, but nothing checked its
# `--adapter` flags, and an adapter that is never named is a lane nobody can
# reach: measured 2026-09-08, the shipped manifest served blender, partkiln,
# seamkiln and fusion, so 19 long-tail tools - 12 `ue_*` and the 7 `pin_*` that
# `_attach_pins` gates on unreal - were unreachable from Claude Desktop while
# UE 5.8.1, the ModelContextProtocol plugin and TeeToolset were all installed
# and every unreal unit test passed. Nothing was broken; the lane was simply
# not asked for.
#
# So the served set is pinned. Changing it is fine - editing this line is how
# that change becomes visible in review instead of silent in a JSON array.
SERVED_ADAPTERS = ("blender", "partkiln", "seamkiln", "fusion", "unreal")


def _manifest_args():
    import json
    from pathlib import Path

    manifest = Path(__file__).resolve().parents[2] / "packaging" / "mcpb_manifest.json"
    return json.loads(manifest.read_text())["server"]["mcp_config"]["args"]


def test_manifest_serves_the_adapters_we_think_it_does():
    args = _manifest_args()
    served = tuple(args[i + 1] for i, a in enumerate(args) if a == "--adapter")
    assert served == SERVED_ADAPTERS, (
        f"the shipped manifest serves {served}, pinned at {SERVED_ADAPTERS}. An "
        "adapter dropped from here takes its whole lane out of reach of every "
        "Desktop session, and no other test notices."
    )


def test_every_adapter_the_manifest_names_is_real():
    from tee.cli import ADAPTER_NAMES

    args = _manifest_args()
    named = [args[i + 1] for i, a in enumerate(args) if a == "--adapter"]
    unknown = [n for n in named if n not in ADAPTER_NAMES]
    assert not unknown, f"manifest names adapters that do not exist: {unknown}"
