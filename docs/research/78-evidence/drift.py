"""78-evidence: the benchmark measures a server that does not exist.

TEE's core metric is tokens per completed task and CLAUDE.md says every design
decision is judged by it first. That metric lives in `benchmarks/RESULTS.md`,
which nothing re-runs and nothing asserts. This measures the gap between the
server `cmd_serve` builds and the one the benchmark harness builds.

    uv run --no-sync python docs/research/78-evidence/drift.py
"""

from __future__ import annotations

import re
import sys
import tempfile
from importlib import import_module
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "server" / "tests"))
sys.path.insert(0, str(REPO / "benchmarks"))

from tee import cli  # noqa: E402
from tee.adapters.partkiln import PartkilnAdapter  # noqa: E402
from tee.server import _DESC  # noqa: E402


def _served_app():
    """Every lane cmd_serve attaches - the server that actually ships."""
    fake = import_module("fixtures_partkiln").FakeKernel
    root = tempfile.mkdtemp()
    lanes = [
        cli._blender_lane("127.0.0.1", 1),
        cli.Lane("partkiln", PartkilnAdapter(root, kernel=fake())),
        cli._seamkiln_lane(root),
    ]
    app = cli.build_app(lanes, root, allow_code_exec=False)
    store = cli._attach_extract(app, root, with_handoff=True)
    cli._attach_assets(app, root, store)
    cli._attach_capture(app, root, store)
    for name in _serve_attachments():
        if name in {"extract", "assets", "capture"}:
            continue
        getattr(cli, f"_attach_{name}")(app, root)
    return app


def _serve_attachments() -> list[str]:
    """The lanes cmd_serve names, read from the source rather than listed."""
    src = (REPO / "server" / "src" / "tee" / "cli.py").read_text()
    body = src[src.index("def cmd_serve") :]
    return sorted({m for m in re.findall(r"_attach_([a-z]+)\(app, args\.project\)", body)})


def _benchmark_attachments() -> list[str]:
    src = (REPO / "benchmarks" / "run_benchmarks.py").read_text()
    return sorted(set(re.findall(r"_attach_([a-z]+)\(", src)))


def main() -> None:
    serve = _serve_attachments()
    bench = _benchmark_attachments()
    missing = [n for n in serve if n not in bench]

    print("A77 P0 - what the benchmark cannot see\n")
    print(f"  lanes cmd_serve attaches   : {len(serve)}")
    print(f"  lanes the harness attaches : {len(bench)}")
    print(f"  MISSING from the benchmark : {', '.join(missing) or 'none'}")

    app = _served_app()
    served_total = len(app.registry.names())
    print(f"\n  a real server serves       : {served_total} tools "
          f"({len(_DESC)} always-loaded + {served_total - len(_DESC)} virtual)")

    from run_benchmarks import run_surface_scenario

    out = run_surface_scenario()
    print(f"  the benchmark measures     : {out['n_virtual_tools']} virtual tools")
    gap = (served_total - len(_DESC)) - out["n_virtual_tools"]
    print(f"  invisible to the benchmark : {gap} tools "
          f"({100 * gap / (served_total - len(_DESC)):.0f}% of the long tail)")
    print(f"  its headline saving        : {out['saving']:.1f}% "
          f"- computed over the corpus it can see, not the one that ships")

    results = (REPO / "benchmarks" / "RESULTS.md").read_text()
    numbers = re.findall(r"\|\s*[\d,]+\s*\|", results)
    sections = re.findall(r"^## ", results, re.M)
    print(f"\n  RESULTS.md                 : {len(sections)} sections, "
          f"{len(numbers)} tabled numbers")
    print("  asserted by any test       : none found "
          "(grep for RESULTS.md in server/tests returns nothing)")
    print("\n  A measurement nothing re-runs is a declaration with a date on it.")


if __name__ == "__main__":
    main()
