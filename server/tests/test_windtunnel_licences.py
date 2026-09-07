"""A72 P0c: the licence gate, load-bearing like seamkiln's and partkiln's.

Every wind-tunnel engine is copyleft or NOSA and stays a separate process:
OpenFOAM GPL-3, SU2 LGPL-2.1, OpenVSP NOSA-1.3, gmsh GPL-2+. The Python
wrappers that would put them in-process are banned by name (foamlib is
GPL-3.0-only on PyPI today, PyFoam and fluidfoam GPL, the OpenVSP bundle is
NOSA and pinned to one Python minor, vtk/pyvista are 600 MB of weight the
kernel does not need). The lane is stdlib at import time; numpy and meshio
live in the optional `[windtunnel]` extra and may be imported in exactly one
place. No tutorial case is ever vendored: the goldens under
tests/data/windtunnel carry a `transcribed` line and no upstream banner.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from importlib import metadata
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[1]
LANE = SERVER / "src" / "tee" / "windtunnel"
DATA = SERVER / "tests" / "data" / "windtunnel"
# Every research-evidence directory, not the one this test was born with: A74
# added `74-evidence` and the scan would have skipped it in silence, which is
# the "a check that samples is not a check" lesson in its cheapest form.
EVIDENCE_DIRS = sorted((SERVER.parent / "docs" / "research").glob("*-evidence"))

BANNED = (
    "foamlib",
    "PyFoam",
    "fluidfoam",
    "ofpp",
    "Ofpp",
    "vtk",
    "vtkmodules",
    "pyvista",
    "openvsp",
    "vsp",
    "pysu2",
    "SU2",
    "gmsh",
    "classy_blocks",
    "paraview",  # the ParaView package; TEE's own tee.windtunnel.paraview is a script writer
)
EXTRA_ONLY = ("numpy", "meshio")
ALLOWED_EXTRA_SITES = {("report.py", "_export_vtu")}

# The header lines a vendored upstream FILE carries (a licence NAME in our
# own prose is not a banner: the package docstring names NOSA on purpose).
UPSTREAM_BANNERS = (
    "The Open Source CFD Toolbox",
    "OpenFOAM Foundation",
    "OpenCFD Ltd",
    "www.openfoam.com",
    "www.openfoam.org",
    "SU2 Foundation",
    "su2foundation",
    "Copyright 2012-20",  # SU2's file banners
    "Christophe Geuzaine",  # gmsh
)

MODULES = sorted(p.stem for p in LANE.glob("*.py") if p.stem != "__init__")


def _import_sites(source: str) -> list[tuple[str, str | None, int]]:
    """(top-level module, enclosing function or None, line) for every import."""
    tree = ast.parse(source)
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    out = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module]
        for name in names:
            top = name.split(".")[0]
            fn = None
            cur: ast.AST | None = node
            while cur is not None:
                if isinstance(cur, ast.FunctionDef):
                    fn = cur.name
                    break
                cur = parents.get(cur)
            out.append((top, fn, node.lineno))
    return out


def test_every_lane_module_imports_nothing_banned_in_a_fresh_interpreter():
    probe = (
        "import sys\n"
        + "\n".join(f"import tee.windtunnel.{m}" for m in MODULES)
        + f"\nbanned = {BANNED!r}\nextra = {EXTRA_ONLY!r}\n"
        + "loaded = sorted(m for m in sys.modules if m.split('.')[0] in banned + extra)\n"
        "print('LOADED', loaded)\n"
    )
    res = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stderr[-800:]
    assert "LOADED []" in res.stdout, res.stdout


def test_ast_scan_finds_no_banned_import_and_confines_the_extra_to_one_function():
    for path in LANE.glob("*.py"):
        for top, fn, line in _import_sites(path.read_text()):
            assert top not in BANNED, f"{path.name}:{line} imports {top}"
            if top in EXTRA_ONLY:
                assert (path.name, fn) in ALLOWED_EXTRA_SITES, (
                    f"{path.name}:{line} imports {top} in {fn}"
                )


def test_the_scan_catches_a_deliberate_intruder():
    sites = _import_sites("import os\ndef f():\n    import foamlib\n    from vtkmodules import x\n")
    assert ("foamlib", "f", 3) in sites and ("vtkmodules", "f", 4) in sites
    assert any(top in BANNED for top, _, _ in sites)


def test_goldens_carry_their_provenance_and_no_upstream_banner():
    files = [p for p in DATA.rglob("*") if p.is_file() and p.name != "README.md"]
    assert files, "no goldens?"
    readme = (DATA / "README.md").read_text()
    for path in files:
        text = path.read_text(errors="replace")
        for banner in UPSTREAM_BANNERS:
            assert banner not in text, f"{path.name} carries an upstream banner: {banner!r}"
        first = text.splitlines()[0] if text else ""
        if (
            path.suffix == ".csv"
        ):  # a CSV's first line is its header: provenance lives in the README
            assert path.name in readme, f"{path.name} is not listed in the README"
        else:
            assert "transcribed" in first or "generated-by" in first, f"{path.name}: {first[:60]!r}"
    for path in LANE.glob("*.py"):
        text = path.read_text()
        for banner in UPSTREAM_BANNERS:
            assert banner not in text, f"{path.name} carries an upstream banner: {banner!r}"
    assert EVIDENCE_DIRS, "no research evidence directories?"
    for evidence in EVIDENCE_DIRS:
        for path in evidence.rglob("*"):
            if path.is_file() and path.suffix in (".dat", ".csv", ".polar", ".log", ".txt"):
                text = path.read_text(errors="replace")
                for banner in UPSTREAM_BANNERS:
                    assert banner not in text, f"{path} carries an upstream banner: {banner!r}"


def test_the_extra_is_pinned_to_meshio_and_numpy_and_witnessed_by_meshio():
    from tee.kernel import extras

    project = tomllib.loads((SERVER / "pyproject.toml").read_text())["project"]
    extra = project["optional-dependencies"]["windtunnel"]
    names = sorted(spec.split(">")[0].split("=")[0].split("[")[0].strip() for spec in extra)
    assert names == ["meshio", "numpy"], extra
    assert extras.WITNESS["windtunnel"] == "meshio"
    assert (
        "cfd"
        in tomllib.loads((SERVER / "pyproject.toml").read_text())["tool"]["pytest"]["ini_options"][
            "addopts"
        ]
    )
    markers = tomllib.loads((SERVER / "pyproject.toml").read_text())["tool"]["pytest"][
        "ini_options"
    ]["markers"]
    assert any(m.startswith("cfd") for m in markers)


@pytest.mark.parametrize(("dist", "word"), [("meshio", "MIT"), ("numpy", "BSD")])
def test_the_extra_dependencies_keep_their_permissive_licences(dist, word):
    try:
        meta = metadata.metadata(dist)
    except metadata.PackageNotFoundError:
        pytest.skip(f"{dist} is not installed in this venv")
    text = " ".join(
        [str(meta.get("License") or ""), str(meta.get("License-Expression") or "")]
        + [c for c in meta.get_all("Classifier") or [] if "License" in c]
    )
    assert word in text, text


def test_the_lane_docstring_states_the_arms_length_rule():
    text = (LANE / "__init__.py").read_text()
    for name in ("GPL-3", "LGPL-2.1", "NASA Open Source Agreement", "pvpython", "meshio"):
        assert name in text, name
