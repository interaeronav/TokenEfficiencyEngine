"""The licence gate (A66 P0b).

A53's Law 2, read for parts: the licence gate is a TEST, because a human
forgets and CI does not. This lane's mines are the obvious answers - py-slvs
(SolveSpace) is the best sketch solver on PyPI and is GPL-3.0 with no linking
exception; cadquery is Apache-2.0 and imports casadi (LGPL-3.0+) eagerly;
FreeCAD's Fasteners workbench and BOLTS are the best fastener tables and are
GPL. Every one is a choice a future session would make without noticing.

What the gate proves, on the tree as installed:

  * the transitive closure of the core list (and of `[brep]` when it is
    installed) resolves to an SPDX expression whose every AND operand is on
    the ALLOWLIST - there is no MPL on it, so "permissive-only in-process"
    stays literally true;
  * the one weak-copyleft payload (OCCT, LGPL-2.1-only WITH the OCCT
    exception) is named in KNOWN_PAYLOADS for BOTH OCP wheels, and NOTICE
    carries its prominent notice whether or not OCP is installed;
  * nothing banned, and nothing non-commercial, is in that closure;
  * `import partkiln` loads none of tee, cadquery, casadi, VTK, py_slvs,
    fpdf or OCP - the modules that ARE in the dev venv must stay unreached;
  * every shipped data file has its paper trail, and no Autodesk mark is in
    any shipped NAME (docs may say "Inventor"; a verb or an id may not).

`partkiln._licences` holds the metadata plumbing (the field-resolution order
that installed metadata makes necessary); the deliberate-failure tests
monkeypatch its two sources so the gate is proven to fire without installing
anything that would then have to be uninstalled.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from importlib.metadata import packages_distributions
from pathlib import Path
from typing import Any

import pytest

import partkiln
from partkiln import _licences as L

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# name -> (why it is banned, what to use instead). Distribution names as
# importlib.metadata keys them (lower, hyphens).
BANNED: dict[str, tuple[str, str]] = {
    "py-slvs": (
        "SolveSpace's solver is GPL-3.0 with no linking exception; importing it "
        "in-process makes partkiln GPL",
        "partkiln.sketch.solver (scipy least_squares, own residual rows)",
    ),
    "python-solvespace": (
        "the same SolveSpace binding under its other name",
        "partkiln.sketch.solver",
    ),
    "cadquery": (
        "Apache-2.0 itself, but it imports casadi (LGPL-3.0+) eagerly and links nine VTK dylibs",
        "OCP direct (partkiln.brep)",
    ),
    "casadi": ("LGPL-3.0+, and the wheel is built with luksan", "partkiln.assembly.solver (scipy)"),
    "nlopt": ("LGPL-2.1+ (the wheel carries luksan)", "scipy.optimize"),
    "pythonocc-core": (
        "LGPL-3.0, and redundant with the Apache-2.0 OCP wheel",
        "cadquery-ocp-novtk",
    ),
    "bd-materials": (
        "carries NO licence at all",
        "partkiln/data/materials.json (own cards, cited)",
    ),
    "build123d": (
        "Apache-2.0, but its next release requires bd_materials, which carries no licence",
        "OCP direct (partkiln.brep)",
    ),
    "gmsh": ("GPL-2.0+; out of process only, never imported", "an external process, later"),
    "calculix": ("GPL-2.0+; out of process only, never imported", "an external process, later"),
}

# Any licence text carrying one of these is disqualifying whatever it is called.
# Whole words: scipy's metadata bundles the LGPL text, whose "allowed only
# occasionally and noncommercially" is boilerplate about conveying object
# code, not a term of use - `\bnoncommercial\b` does not match it.
NON_COMMERCIAL_MARKERS = (
    r"\bnon[- ]?commercial\b",
    r"\bcc[- ]by[- ]nc\b",
    r"\bresearch (purposes )?only\b",
    r"\bacademic use only\b",
    r"\bnvidia source code license\b",
)

# The in-process allowlist. No MPL, no LGPL: Law 2 ("permissive-only
# in-process") stays literally true. 0BSD, Zlib and CC0-1.0 are here because
# numpy's expression is `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`.
ALLOWED_SPDX = frozenset(
    {
        "MIT",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "Apache-2.0",
        "ISC",
        "PSF-2.0",
        "0BSD",
        "Zlib",
        "CC0-1.0",
    }
)

# The ONE weak-copyleft payload, accepted by name as a whole `X WITH Y` phrase.
OCCT_EXCEPTION = "LGPL-2.1-only WITH OCCT-exception-1.0"
OCCT_LICENCE_URL = "https://github.com/Open-Cascade-SAS/OCCT/blob/master/OCCT_LGPL_EXCEPTION.txt"

# Both OCP wheels ship the same OCCT payload under the same Apache-2.0 binding
# licence; either may be the live carrier (they clobber each other's `OCP/`).
KNOWN_PAYLOADS: dict[str, tuple[str, str, str]] = {
    "cadquery-ocp": (OCCT_EXCEPTION, OCCT_LICENCE_URL, "2026-09-02"),
    "cadquery-ocp-novtk": (OCCT_EXCEPTION, OCCT_LICENCE_URL, "2026-09-02"),
}
# The proxy wheel both carriers depend on: Apache-2.0, no payload of its own.
CARRIER_ALLOWED = frozenset({"cadquery-ocp-proxy"})

# Distributions allowed ONLY inside a named extra, with the licence that is
# the reason: the core must never reach them.
EXTRA_ONLY: dict[str, tuple[str, str]] = {
    "fpdf2": ("pdf", "LGPL-3.0-only"),
    # The Qt shell's dependency. Registered here for the same reason fpdf2 is:
    # FORBIDDEN_ON_IMPORT already proves the core never LOADS Qt, but nothing
    # else asserts the core never DECLARES it.
    "pyside6": ("gui", "LGPL-3.0-only"),
}

# Third-party CAD datasets whose licence forbids what a fixture would do with them.
BANNED_DATASETS = ("Fusion 360 Gallery", "Text2CAD", "CAD-Recode", "GenCAD-Code")

# Data sources that are GPL, share-alike, or terms-of-use bound; a manifest
# entry citing one is a defect however good the numbers are. Regexes over
# the ORIGINAL text: BOLTS (the GPL-3 parts library) is upper-case and a
# whole token, so "hexagon head bolts" in an ISO title is not a hit.
BANNED_DATA_SOURCES = (
    re.compile(r"fasteners workbench", re.IGNORECASE),
    re.compile(r"freecad fasteners", re.IGNORECASE),
    re.compile(r"\bBOLTS\b"),
    re.compile(r"wikipedia", re.IGNORECASE),
    re.compile(r"matweb", re.IGNORECASE),
    re.compile(r"engineeringtoolbox", re.IGNORECASE),
    re.compile(r"makeitfrom", re.IGNORECASE),
)

# Autodesk marks, matched as whole tokens over shipped NAMES only (D9 / P0b).
MARKS = (
    "autodesk",
    "inventor",
    "forge",
    "fusion",
    "vault",
    "nastran",
    "anycad",
    "ilogic",
    "ipart",
    "iassembly",
    "ifeature",
    "imate",
    "apprentice",
    "content center",
    "design accelerator",
)
_MARK = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(re.escape(m) for m in MARKS) + r")(?![a-z0-9])", re.IGNORECASE
)

# Modules `import partkiln` (and every P1 module) must never load.
FORBIDDEN_ON_IMPORT = (
    "OCP",
    "tee",
    "cadquery",
    "casadi",
    "py_slvs",
    "fpdf",
    "vtkmodules",
    "PySide6",
)

# The modules that must import with NO OCP installed: everything P0/P1 wrote,
# plus the `brep` and `exchange` packages themselves (their OCP imports are
# lazy by design, D1). OCP-backed submodules (`brep.shapes`, `brep.query`,
# P2's features) are `pytest.importorskip("OCP")` territory and stay out.
MUST_IMPORT_WITHOUT_OCP = (
    "partkiln",
    "partkiln._errors",
    "partkiln._licences",
    "partkiln.brep",
    "partkiln.data",
    "partkiln.document",
    "partkiln.exchange",
    "partkiln.materials",
    "partkiln.params",
    "partkiln.sketch",
    "partkiln.sketch.model",
    "partkiln.sketch.presets",
    "partkiln.sketch.solver",
    "partkiln.standards",
    "partkiln.units",
)
# Never imported anywhere in the package, lazily or not.
NEVER_IMPORTED = ("tee", "cadquery", "casadi", "py_slvs", "python_solvespace", "nlopt", "OCC")
_IMPORT_LINE = re.compile(r"^(?P<indent>[ \t]*)(?:from|import)\s+(?P<name>[A-Za-z_][\w.]*)", re.M)


# --- helpers ------------------------------------------------------------------


def _problems(names: set[str]) -> list[str]:
    """Every distribution in `names` whose licence is not allowlisted, as one
    line each: the name, the expression, and the offending operand."""
    problems: list[str] = []
    for name in sorted(names):
        if L.metadata_of(name) is None:
            problems.append(f"{name}: not installed, so its licence cannot be read")
            continue
        spdx = L.spdx_of(name)
        if spdx is None:
            problems.append(
                f"{name}: no licence metadata at all (no License-Expression, no License :: "
                "classifier, no License text). Silence is not permission."
            )
            continue
        ok, offending = L.expression_verdict(spdx, allow=ALLOWED_SPDX, exceptions=[OCCT_EXCEPTION])
        if not ok:
            problems.append(
                f"{name}: {spdx!r} is not permissive (offending: {', '.join(offending)}). "
                f"Allowed: {', '.join(sorted(ALLOWED_SPDX))}; the OCCT exception by name."
            )
    return problems


def _banned_hits(names: set[str]) -> list[str]:
    return [
        f"{name}: {BANNED[name][0]}. Use instead: {BANNED[name][1]}."
        for name in sorted(names & BANNED.keys())
    ]


def _non_commercial_hits(names: set[str]) -> list[str]:
    offenders = []
    for name in sorted(names):
        text = L.licence_text(name)
        for marker in NON_COMMERCIAL_MARKERS:
            found = re.search(marker, text)
            if found:
                offenders.append(f"{name}: licence metadata contains {found.group(0)!r}")
                break
    return offenders


def _live_carrier() -> str | None:
    """The distribution that provides the top-level `OCP` package, if any."""
    carriers = packages_distributions().get("OCP") or []
    if not carriers:
        return None
    return L.normalise(carriers[0])


class _FakeMeta:
    """Just enough of `email.message.Message` for `_licences` to read."""

    def __init__(self, fields: dict[str, Any]) -> None:
        self.fields = fields

    def get(self, key: str, default: Any = None) -> Any:
        value = self.fields.get(key)
        return default if value is None else value

    def get_all(self, key: str) -> list[str] | None:
        value = self.fields.get(key)
        return list(value) if value else None


def _fake_tree(monkeypatch: pytest.MonkeyPatch, tree: dict[str, dict[str, Any]]) -> None:
    """Declare `tree` (name -> metadata fields) as the whole world: the core
    list is its keys, nothing requires anything, metadata is what is given."""
    real_metadata = L.metadata_of
    monkeypatch.setattr(
        L, "declared_requirements", lambda extra=None: sorted(tree) if extra is None else []
    )
    monkeypatch.setattr(
        L,
        "metadata_of",
        lambda name: _FakeMeta(tree[name]) if name in tree else real_metadata(name),
    )
    monkeypatch.setattr(L, "requires_of", lambda name: [] if name in tree else None)


# --- the tree as installed --------------------------------------------------------


def test_core_dependencies_are_installed_and_permissive() -> None:
    """A missing CORE dependency FAILS (the venv is wrong, not the gate); every
    distribution the core reaches transitively is on the allowlist."""
    core = L.declared_requirements()
    assert core, "pyproject.toml declares no core dependencies"
    missing = [n for n in core if L.metadata_of(n) is None]
    assert not missing, f"core dependencies not installed: {', '.join(missing)}. Fix: uv sync."
    problems = _problems(L.closure(core))
    assert not problems, "\n".join(problems)


def test_brep_extra_is_permissive_or_skips_naming_the_extra() -> None:
    """`[brep]` = cadquery-ocp-novtk. The dev venv carries the VTK wheel instead
    (both ship `OCP/`, never co-install), so here the declared name is absent:
    that is a skip naming the extra, never a silent pass."""
    brep = L.declared_requirements("brep")
    assert brep == ["cadquery-ocp-novtk"], brep
    missing = [n for n in brep if L.metadata_of(n) is None]
    if missing:
        pytest.skip(f"partkiln[brep] declares {', '.join(missing)}, which is not installed here")
    problems = _problems(L.closure(brep) - CARRIER_ALLOWED)
    assert not problems, "\n".join(problems)


def test_live_ocp_carrier_is_a_known_payload() -> None:
    """Whichever wheel provides `OCP` must be one whose OCCT payload is on
    record; its own licence is Apache-2.0 and nothing it drags in is banned or
    non-commercial. (The VTK wheel's closure reaches matplotlib and pillow
    through vtk; that is why the SPDX allowlist runs over the DECLARED tree
    and this test asks the carrier's closure only the banned/non-commercial
    questions.)"""
    carrier = _live_carrier()
    if carrier is None:
        pytest.skip("no OCP wheel in this interpreter (partkiln[brep] not installed)")
    assert carrier in KNOWN_PAYLOADS, (
        f"OCP is provided by {carrier!r}, which is not in KNOWN_PAYLOADS. Record its OCCT "
        "payload licence (expression, url, date) there before accepting it."
    )
    assert L.spdx_of(carrier) == "Apache-2.0", L.spdx_of(carrier)
    expression, url, date = KNOWN_PAYLOADS[carrier]
    ok, offending = L.expression_verdict(
        expression, allow=ALLOWED_SPDX, exceptions=[OCCT_EXCEPTION]
    )
    assert ok, offending
    assert url.startswith("https://") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
    reach = L.closure({carrier})
    assert not _banned_hits(reach), "\n".join(_banned_hits(reach))
    assert not _non_commercial_hits(reach), "\n".join(_non_commercial_hits(reach))


def test_known_payloads_cover_both_ocp_wheels() -> None:
    assert set(KNOWN_PAYLOADS) == {"cadquery-ocp", "cadquery-ocp-novtk"}
    for name, (expression, url, date) in KNOWN_PAYLOADS.items():
        assert expression == OCCT_EXCEPTION, name
        assert "OCCT_LGPL_EXCEPTION" in url, name
        assert date == "2026-09-02", name
    # The exception is accepted ONLY as the whole named phrase: bare LGPL-2.1 is not.
    assert L.expression_verdict(
        "LGPL-2.1-only", allow=ALLOWED_SPDX, exceptions=[OCCT_EXCEPTION]
    ) == (
        False,
        ["LGPL-2.1-only"],
    )


def _declared_closure() -> set[str]:
    names = set(L.declared_requirements()) | set(L.declared_requirements("brep"))
    carrier = _live_carrier()
    if carrier is not None:
        names.add(carrier)
    return L.closure(names)


def test_no_banned_distribution_in_the_declared_closure() -> None:
    hits = _banned_hits(_declared_closure())
    assert not hits, "\n".join(hits)


def test_no_declared_dependency_carries_a_non_commercial_licence() -> None:
    hits = _non_commercial_hits(_declared_closure())
    assert not hits, "\n".join(hits)


def test_weak_copyleft_lives_only_in_its_named_extra() -> None:
    """fpdf2 and PySide6 are LGPL-3.0-only. Each is allowed exactly where TEE
    allows it: an optional extra the core never reaches (drawing/pdf.py imports
    fpdf2 lazily; gui/app.py is the only module that names Qt)."""
    for name, (extra, licence) in EXTRA_ONLY.items():
        assert name in L.declared_requirements(extra), f"{name} should be declared under [{extra}]"
        assert name not in L.closure(L.declared_requirements()), (
            f"{name} ({licence}) reached the core"
        )
        assert name not in L.closure(L.declared_requirements("brep")), f"{name} reached [brep]"
        spdx = L.spdx_of(name)
        if spdx is not None:
            assert spdx == licence, spdx
            ok, _ = L.expression_verdict(spdx, allow=ALLOWED_SPDX)
            assert not ok, f"{name} is {spdx}; if that became permissive, EXTRA_ONLY is stale"


def test_notice_names_occt_unconditionally() -> None:
    """The OCCT exception asks for a prominent notice in supporting
    documentation. It is owed whether or not OCP is installed here."""
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Open CASCADE" in text
    assert "LGPL" in text and "exception" in text.lower()
    assert "bd_warehouse" in text and "threadlib" in text  # the data tables' sources


def test_pyproject_writes_every_ban_down() -> None:
    """The BANNED table here and the comment block in pyproject.toml are the
    same list, so a cold session reading either sees the whole story."""
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8").lower()
    missing = [name for name in BANNED if name not in text and name.replace("-", "_") not in text]
    assert not missing, f"pyproject.toml's BANNED block does not name: {', '.join(missing)}"
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["license"] == {"text": "MIT"}
    assert "brep" in data["project"]["optional-dependencies"]
    assert "sheet" not in data["project"]["optional-dependencies"]  # the extra is [pdf], D1


# --- the gate proven to fire --------------------------------------------------


@pytest.mark.parametrize("intruder", ["py-slvs", "cadquery", "casadi"])
def test_the_ban_fires(intruder: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A gate nobody has seen fail is a gate nobody knows is wired up."""
    monkeypatch.setattr(L, "declared_requirements", lambda extra=None: ["numpy", intruder])
    monkeypatch.setattr(L, "requires_of", lambda name: [])
    with pytest.raises(AssertionError) as excinfo:
        test_no_banned_distribution_in_the_declared_closure()
    message = str(excinfo.value)
    assert intruder in message
    assert BANNED[intruder][1].split()[0] in message  # the replacement is named


def test_the_ban_fires_transitively(monkeypatch: pytest.MonkeyPatch) -> None:
    """cadquery two hops down (a helper that requires it) is still cadquery."""
    monkeypatch.setattr(L, "declared_requirements", lambda extra=None: ["helper"])
    monkeypatch.setattr(
        L, "requires_of", lambda name: ["cadquery>=2.0"] if name == "helper" else []
    )
    with pytest.raises(AssertionError, match="cadquery"):
        test_no_banned_distribution_in_the_declared_closure()


def test_a_licence_less_distribution_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_tree(monkeypatch, {"pretend": {}})
    with pytest.raises(AssertionError, match="no licence metadata"):
        test_core_dependencies_are_installed_and_permissive()


def test_an_lgpl_expression_in_core_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_tree(monkeypatch, {"pretend": {"License-Expression": "MIT AND LGPL-3.0-only"}})
    with pytest.raises(AssertionError, match=r"LGPL-3\.0-only"):
        test_core_dependencies_are_installed_and_permissive()


def test_a_classifier_only_bsd_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    """scipy's case: no License-Expression, a Trove classifier, a text header."""
    _fake_tree(
        monkeypatch,
        {
            "pretend": {
                "Classifier": ["License :: OSI Approved :: BSD License"],
                "License": "Copyright (c) 2001-2002 Enthought, Inc. 2003, SciPy Developers.",
            }
        },
    )
    test_core_dependencies_are_installed_and_permissive()


def test_free_text_lgpl_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_tree(monkeypatch, {"pretend": {"License": "GNU Lesser General Public License v3"}})
    with pytest.raises(AssertionError, match=r"LGPL-3\.0-only"):
        test_core_dependencies_are_installed_and_permissive()


def test_free_text_aliases_resolve() -> None:
    for text, spdx in (
        ("The MIT License (MIT)", "MIT"),
        ("BSD", "BSD-3-Clause"),
        ("Apache Public License 2.0", "Apache-2.0"),
        ("MIT License\n\nCopyright (c) 2019 Michael Dawson-Haggerty\n...", "MIT"),
        ("MIT-CMU", "MIT-CMU"),
    ):
        assert L.spdx_from_free_text(text) == spdx, text


def test_the_marker_scan_fires(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_tree(
        monkeypatch,
        {"pretend": {"License": "NVIDIA Source Code License (non-commercial use only)"}},
    )
    with pytest.raises(AssertionError, match="non-commercial"):
        test_no_declared_dependency_carries_a_non_commercial_licence()


def test_a_missing_core_dependency_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(L, "declared_requirements", lambda extra=None: ["numpy", "not-a-real-dist"])
    with pytest.raises(AssertionError, match="not-a-real-dist"):
        test_core_dependencies_are_installed_and_permissive()


# --- import hygiene ---------------------------------------------------------------


def test_import_hygiene() -> None:
    """`import partkiln` and every P0/P1 module load with no OCP, tee,
    cadquery, casadi, VTK, py_slvs, fpdf or Qt - in a subprocess so this
    test's own imports cannot mask a leak, and exercised (a sketch, a lookup,
    a mass) so a lazy import hiding in a call path is caught too."""
    for name in MUST_IMPORT_WITHOUT_OCP:
        parts = name.split(".")[1:]
        path = SRC.joinpath("partkiln", *parts)
        assert path.with_suffix(".py").exists() or (path / "__init__.py").exists(), name
    code = (
        "import sys\n"
        f"for m in {MUST_IMPORT_WITHOUT_OCP!r}:\n"
        "    __import__(m)\n"
        "from partkiln.document import Document\n"
        "Document().apply({'op': 'create', 'kind': 'sketch', "
        "'props': {'plane': 'XY', 'profile': {'rect': [1, 1]}}})\n"
        "from partkiln import standards, materials\n"
        "standards.clearance_hole('M6'); materials.mass_g('steel', 1000)\n"
        f"bad = [m for m in sys.modules if m.split('.')[0] in {FORBIDDEN_ON_IMPORT!r}]\n"
        "print(sorted(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={"PYTHONPATH": str(SRC), "PATH": "/usr/bin:/bin"},
        check=False,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]", out.stdout


def test_no_eager_ocp_import_outside_brep_and_nothing_banned_anywhere() -> None:
    """Static, over every .py in the package (in-flight P2 files included):
    an OCP import at column 0 outside `partkiln/brep/` would make the module
    unimportable on the extension venv (3.13.9, no OCP); a tee / cadquery /
    casadi / py_slvs import anywhere, however lazy, is the licence mine
    itself. `partkiln/brep/shapes.py` may import OCP eagerly: nothing in
    MUST_IMPORT_WITHOUT_OCP imports it."""
    hits = []
    for path in sorted((SRC / "partkiln").rglob("*.py")):
        rel = path.relative_to(SRC)
        text = path.read_text(encoding="utf-8")
        in_brep = rel.parts[:2] == ("partkiln", "brep")
        for match in _IMPORT_LINE.finditer(text):
            top = match.group("name").split(".")[0]
            line = text.count("\n", 0, match.start()) + 1
            if top in NEVER_IMPORTED:
                hits.append(f"{rel}:{line}: imports {top} (banned in-process, see BANNED)")
            elif top == "OCP" and not match.group("indent") and not in_brep:
                hits.append(f"{rel}:{line}: eager OCP import outside partkiln/brep (D1)")
    assert not hits, "\n".join(hits)


def test_package_imports_nothing_heavy() -> None:
    """In-process too: `import partkiln` is a version string and nothing else."""
    assert partkiln.__version__
    loaded = [m for m in sys.modules if m.split(".")[0] in FORBIDDEN_ON_IMPORT]
    if loaded:  # another test module may legitimately have imported these
        pytest.skip(f"already loaded by the test session: {', '.join(sorted(loaded)[:4])}")


# --- data provenance and fixtures ---------------------------------------------------


def test_data_files_carry_provenance() -> None:
    """Every shipped CSV/JSON has source, licence and retrieved in the
    manifest (the loader refuses otherwise - this pins that the manifest is
    complete TODAY), and no entry cites a GPL / share-alike / terms-bound
    table. The material cards' per-value sources are checked the same way."""
    from partkiln import data
    from partkiln.materials import cards

    files = data.shipped_files()
    assert files, "no data files shipped"
    listed = set(data.manifest()["files"])
    assert set(files) <= listed, f"shipped without a manifest entry: {sorted(set(files) - listed)}"
    assert listed <= set(files), (
        f"manifest names files that are absent: {sorted(listed - set(files))}"
    )
    for name in files:
        entry = data.provenance(name)  # refuses when a field is missing
        for key in data.REQUIRED_PROVENANCE:
            assert entry[key], f"{name}: empty {key}"
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["retrieved"]), (name, entry["retrieved"])
        cited = " ".join(str(entry.get(k, "")) for k in ("source", "authority", "notes"))
        for banned in BANNED_DATA_SOURCES:
            assert not banned.search(cited), f"{name} cites {banned.pattern!r}: {entry['source']}"
        if entry["licence"] != "own":
            ok, _ = L.expression_verdict(entry["licence"], allow=ALLOWED_SPDX)
            assert ok, f"{name}: data licence {entry['licence']!r} is not permissive"
    for card in cards():
        for prop, leaf in card["properties"].items():
            source = str(leaf["source"])
            assert source, f"{card['name']}.{prop} has no source"
            for banned in BANNED_DATA_SOURCES:
                assert not banned.search(source), f"{card['name']}.{prop} cites {banned.pattern!r}"


def test_the_provenance_gate_fires(monkeypatch: pytest.MonkeyPatch) -> None:
    from partkiln import data

    real = json.loads(json.dumps(data.manifest()))
    real["files"]["clearance_holes.csv"].pop("licence")
    monkeypatch.setattr(data, "manifest", lambda: real)
    with pytest.raises(data.DataError, match="without licence"):
        data.load_table("clearance_holes.csv")
    with pytest.raises(data.DataError, match="no entry"):
        data.provenance("dropped_in.csv")


def test_no_banned_dataset_under_fixtures() -> None:
    """Fixtures are own-built (F1-F8) until P0a row 18 records a third-party
    dataset card's licence in fixtures/third_party/ATTRIBUTION.md."""
    fixtures = ROOT / "fixtures"
    if not fixtures.exists():
        return
    hits = []
    for path in sorted(fixtures.rglob("*")):
        if not path.is_file() or path.suffix not in (".json", ".md", ".txt", ".py", ".csv"):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        hits.extend(f"{path.relative_to(ROOT)}: {name}" for name in BANNED_DATASETS if name in text)
    assert not hits, "\n".join(hits)
    third_party = fixtures / "third_party"
    if third_party.exists() and any(p.is_file() for p in third_party.rglob("*")):
        assert (third_party / "ATTRIBUTION.md").exists(), (
            "fixtures/third_party has files but no ATTRIBUTION.md naming their licences"
        )


# --- no Autodesk marks in shipped names ------------------------------------------------


def _shipped_surfaces() -> list[tuple[str, str]]:
    """(label, text) for everything a mark could be shipped IN: names, never docs.

    P4 must add its VirtualTool names, descriptions and tags here when
    `server/src/tee/adapters/partkiln/` lands (D9: `pk_*`, 14 rows).
    """
    import partkiln.document as document
    from partkiln import materials, standards
    from partkiln.sketch import CONSTRAINT_KINDS, DIM_KINDS, PRESETS

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    surfaces: list[tuple[str, str]] = [
        ("package name", partkiln.__name__),
        ("pyproject name", project["name"]),
        ("pyproject description", project["description"]),
        ("verbs", " ".join(document.VERBS)),
        ("create kinds", " ".join(document.KINDS)),
        ("constraint kinds", " ".join(CONSTRAINT_KINDS)),
        ("dimension kinds", " ".join(DIM_KINDS)),
        ("presets", " ".join(PRESETS)),
        ("standards", " ".join(standards.supported_standards())),
        ("material cards", " ".join(materials.names())),
        ("data/manifest.json", (SRC / "partkiln" / "data" / "manifest.json").read_text("utf-8")),
        (
            "module names",
            " ".join(str(p.relative_to(SRC)) for p in (SRC / "partkiln").rglob("*.py")),
        ),
        ("data file names", " ".join(p.name for p in (SRC / "partkiln" / "data").iterdir())),
    ]
    return surfaces


def test_no_autodesk_marks_in_shipped_names() -> None:
    hits = []
    for label, text in _shipped_surfaces():
        for match in _MARK.finditer(text):
            hits.append(f"{label}: {match.group(0)!r}")
    assert not hits, (
        "Autodesk marks in shipped names (docs may name the incumbent; ids may not):\n"
        + "\n".join(hits)
    )


def test_the_marks_scan_is_whole_token() -> None:
    """`inventory` is not `inventor`; `forged` is not `forge`; `Inventor` is."""
    assert not _MARK.search("inventory forged vaults refusion")
    assert _MARK.search("An Inventor-class loop")
    assert _MARK.search("ipart")
    assert _MARK.search("content center")
