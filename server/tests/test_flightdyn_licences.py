"""A75 P1: the licence gate, load-bearing like windtunnel's and partkiln's.

JSBSim is LGPL-2.0-or-later and this lane uses it as a library, in-process,
unmodified and dynamically linked (docs/DECISIONS.md, 2026-09-07). The gate
that matters most is the EIGHTH test below, which has no precedent in this
repo: PyPI declares `LGPLv2+` for the whole jsbsim distribution while the wheel
ships one **GPL-3.0-or-later** file - `jsbsim/script.py`, installed as the
`jsbsim` console script. A gate that reads `importlib.metadata` passes that
package. So this one reads the grant in each installed file's own header, and
fails if `script.py`'s licence moves or if a GPL file appears where an LGPL one
was. A declaration is a claim; a measurement is evidence.

Nothing upstream is vendored: the wheel ships 60 aircraft and a directory of
engines, and this lane writes its own.
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
LANE = SERVER / "src" / "tee" / "flightdyn"
DATA = SERVER / "tests" / "data" / "flightdyn"
EVIDENCE = SERVER.parent / "docs" / "research" / "76-evidence"

# In-process is the ruled route. Every OTHER way to reach JSBSim is banned by
# name, and so is anything that would drag a viewer or a second FDM in.
BANNED = (
    "flightgear",
    "fgfs",
    "yasim",
    "aerosandbox",
    "openvsp",
    "vsp",
    "matplotlib",
    "pandas",
    "scipy",
)
#: Importable only from the worker child, and only there.
EXTRA_ONLY = ("jsbsim", "numpy")
ALLOWED_EXTRA_SITES = {
    ("worker.py", "_mute"),
    ("worker.py", "_open"),
    ("worker.py", "trim"),
    ("worker.py", "modes"),
    ("worker.py", "main"),
}
UPSTREAM_BANNERS = (
    "Jon S. Berndt",
    "JSBSim Flight Dynamics Model",
    "Aero-Matic",
    "jsbsim.sourceforge.net",
)
LANE_FILES = sorted(LANE.glob("*.py"))


def _import_sites() -> list[tuple[str, str, str]]:
    """(file, enclosing function, module) for every import in the lane."""

    def walk(node: ast.AST, fn: str, filename: str, out: list[tuple[str, str, str]]) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, ast.FunctionDef) else fn
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                mods = (
                    [a.name for a in child.names]
                    if isinstance(child, ast.Import)
                    else [child.module or ""]
                )
                for m in mods:
                    out.append((filename, name, m.split(".")[0]))
            walk(child, name, filename, out)

    sites: list[tuple[str, str, str]] = []
    for f in LANE_FILES:
        walk(ast.parse(f.read_text()), "<module>", f.name, sites)
    return sites


def test_the_lane_imports_stdlib_only_in_a_fresh_interpreter():
    """An AST scan cannot see a transitive pull. A subprocess can."""
    code = (
        "import sys;"
        "import tee.flightdyn, tee.flightdyn.aircraft, tee.flightdyn.probe,"
        "tee.flightdyn.store, tee.flightdyn.tools;"
        f"print('LOADED', [m for m in {list(EXTRA_ONLY)!r} if m in sys.modules])"
    )
    r = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=SERVER,
        env={"PYTHONPATH": str(SERVER / "src"), "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0, r.stderr
    assert "LOADED []" in r.stdout, f"the lane dragged an extra in at import: {r.stdout}"


def test_no_banned_module_is_imported_anywhere_in_the_lane():
    for file, fn, mod in _import_sites():
        assert mod not in BANNED, f"{file}:{fn} imports banned {mod!r}"


def test_the_extra_is_imported_in_exactly_the_declared_places():
    for file, fn, mod in _import_sites():
        if mod in EXTRA_ONLY:
            assert (file, fn) in ALLOWED_EXTRA_SITES, (
                f"{file}:{fn} imports {mod!r}; the extra may only be imported "
                f"from {sorted(ALLOWED_EXTRA_SITES)}"
            )


def test_the_scan_catches_a_deliberate_intruder(tmp_path, monkeypatch):
    intruder = tmp_path / "intruder.py"
    intruder.write_text("import flightgear\n")
    monkeypatch.setattr(sys.modules[__name__], "LANE_FILES", [intruder])
    bad = [m for _, _, m in _import_sites() if m in BANNED]
    assert bad == ["flightgear"], "the gate does not actually fire"


def test_no_upstream_file_is_vendored():
    for base in (LANE, DATA, EVIDENCE):
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file() or f.suffix in {".log", ".json"}:
                continue
            head = f.read_text(errors="ignore")[:2000]
            for banner in UPSTREAM_BANNERS:
                assert banner not in head, f"{f} carries an upstream banner: {banner!r}"


def test_every_golden_states_where_it_came_from():
    if not DATA.exists():
        pytest.skip("no goldens yet")
    for f in DATA.rglob("*"):
        if f.is_file():
            first = f.read_text(errors="ignore").splitlines()[:3]
            assert any("generated-by" in line or "transcribed" in line for line in first), (
                f"{f} does not say where it came from"
            )


def test_the_extra_has_the_shape_the_lane_declares():
    data = tomllib.loads((SERVER / "pyproject.toml").read_text())
    extras = data["project"]["optional-dependencies"]
    assert sorted(e.split(">")[0] for e in extras["flightdyn"]) == ["jsbsim", "numpy"]
    from tee.kernel import extras as ex

    assert ex.WITNESS["flightdyn"] == "jsbsim"
    markers = " ".join(data["tool"]["pytest"]["ini_options"]["markers"])
    assert "fdm:" in markers
    assert "not fdm" in data["tool"]["pytest"]["ini_options"]["addopts"]


def test_the_lane_docstring_states_the_arms_length_rule():
    doc = (LANE / "__init__.py").read_text()
    for word in ("LGPL-2.0-or-later", "GPL-3.0-or-later", "script.py", "SIGSEGV", "vendored"):
        assert word in doc, f"{word!r} missing from the lane docstring"


# --- the eighth: read the GRANT, not the metadata -------------------------

#: What each installed JSBSim file must grant, MEASURED not assumed. The first
#: draft of this test expected an LGPL header in `__init__.py` and the gate
#: caught it: that file is a 537-byte re-export and carries no header at all.
#: The licence lives in LICENSE.txt; the GPL-3 lives in script.py.
EXPECTED_GRANTS = {
    "LICENSE.txt": "LESSER",  # the distribution's shipped licence: LGPL 2.1
    "script.py": "GENERAL",  # the `jsbsim` console script: GPL-3.0-or-later
    "__init__.py": "NONE",  # a bare re-export; asserting a grant here would lie
}


def _grant(text: str) -> str:
    """LESSER or GENERAL, from the licence sentence in a file's own header."""
    head = " ".join(text[:4000].split())
    if "Lesser General Public License" in head:
        return "LESSER"
    if "General Public License" in head:
        return "GENERAL"
    return "NONE"


@pytest.mark.fdm
def test_installed_jsbsim_files_grant_what_the_lane_assumes():
    """PyPI says LGPLv2+ for the distribution; one shipped file says GPL-3.

    If this fails, the ruling in docs/DECISIONS.md has to be revisited before
    the lane ships - not after.
    """
    jsbsim = pytest.importorskip("jsbsim")
    root = Path(jsbsim.__file__).parent
    for name, expected in EXPECTED_GRANTS.items():
        f = root / name
        if not f.exists():
            pytest.skip(f"{name} not in this wheel")
        got = _grant(f.read_text(errors="ignore"))
        assert got == expected, (
            f"{name} grants {got}, expected {expected}. The licence layout of "
            f"the jsbsim wheel has changed; re-read docs/research/75 section 2.1 "
            f"and the ruling in docs/DECISIONS.md before shipping."
        )
    # and the distribution metadata is exactly the claim that misleads
    declared = " ".join(metadata.metadata("jsbsim").get_all("Classifier") or [])
    assert "Lesser General Public License" in declared


def test_the_grant_reader_distinguishes_the_two_licences():
    assert _grant("under the terms of the GNU Lesser General Public License") == "LESSER"
    assert _grant("under the terms of the GNU General Public License") == "GENERAL"
    assert _grant("MIT licence, do what you like") == "NONE"
