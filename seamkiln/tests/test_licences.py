"""The licence gate (A53 P0c).

Research doc 67 §2 found that this domain is unusually mined: the best
documented open garment pipeline (GarmentCodeData) drapes through a fork of
NVIDIA Warp under a NON-COMMERCIAL licence even though its pattern half is
MIT; SMPL and SMPL-X are non-commercial; and Shewchuk's Triangle - the
default answer for constrained Delaunay, and what `meshpy` and the
`triangle` wheel wrap - "may not be sold or included in commercial products
without a licence".

Every one of those is an easy, natural, well-documented choice that a
future session would make without noticing. So this is a test, not a note:
a human forgets, CI does not. The failure message carries the reason and
the permissive replacement, so the lesson arrives with the error.
"""

from __future__ import annotations

import tomllib
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# name -> (why it is banned, what to use instead)
BANNED: dict[str, tuple[str, str]] = {
    "triangle": (
        "Shewchuk's Triangle may not be sold or included in commercial "
        "products without a direct arrangement with the author",
        "CDT (artem-ogre, MPL-2.0), or seamkiln's own constrained Delaunay",
    ),
    "meshpy": ("wraps Shewchuk's Triangle and inherits its terms", "CDT (MPL-2.0)"),
    "smplx": (
        "SMPL/SMPL-X are licensed for non-commercial research only (MPI); "
        "commercial use is sold separately through Meshcapade",
        "anny (Apache-2.0, over CC0 MakeHuman assets)",
    ),
    "smplx-toolbox": ("a SMPL-X wrapper, same terms", "anny (Apache-2.0)"),
    "arcsim": (
        "ArcSim's measured cloth parameters are non-profit-only (research doc 34)",
        "publishable GSM/thickness ranges as cited facts, solver constants flagged `plausible`",
    ),
}

# Any licence text carrying one of these is disqualifying whatever it is called.
NON_COMMERCIAL_MARKERS = (
    "non-commercial",
    "noncommercial",
    "non commercial",
    "cc-by-nc",
    "cc by-nc",
    "research purposes only",
    "research only",
    "academic use only",
    "nvidia source code license",
)


def _declared_requirements() -> set[str]:
    """Every distribution seamkiln asks for, core and extras."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text())
    project = data["project"]
    specs = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        specs.extend(group)
    names = set()
    for spec in specs:
        name = spec.split(";")[0]
        for sep in ("[", ">", "<", "=", "!", "~", " "):
            name = name.split(sep)[0]
        if name:
            names.add(name.strip().lower().replace("_", "-"))
    return names


def _closure(names: set[str], *, depth: int = 6) -> set[str]:
    """Transitive dependency closure over what is actually installed.

    Scoped to seamkiln's own requirements on purpose: the surrounding
    environment is TEE's, and this gate is about what SEAMKILN pulls in.
    """
    seen: set[str] = set()
    frontier = set(names)
    for _ in range(depth):
        nxt: set[str] = set()
        for name in frontier - seen:
            seen.add(name)
            try:
                dist = distribution(name)
            except PackageNotFoundError:
                continue
            for requirement in dist.requires or []:
                if "extra ==" in requirement:  # optional deps are opt-in, not implied
                    continue
                child = requirement.split(";")[0]
                for sep in ("[", ">", "<", "=", "!", "~", " ", "("):
                    child = child.split(sep)[0]
                child = child.strip().lower().replace("_", "-")
                if child:
                    nxt.add(child)
        if not nxt - seen:
            break
        frontier = nxt
    return seen


def _licence_text(name: str) -> str:
    try:
        meta = distribution(name).metadata
    except PackageNotFoundError:
        return ""
    parts = [meta.get("License") or ""]
    parts.extend(meta.get_all("Classifier") or [])
    parts.append(meta.get("License-Expression") or "")
    return " ".join(parts).lower()


def test_no_banned_distribution_in_the_declared_closure() -> None:
    closure = _closure(_declared_requirements())
    hits = sorted(closure & BANNED.keys())
    assert not hits, "\n".join(
        f"{name}: {BANNED[name][0]}. Use instead: {BANNED[name][1]}." for name in hits
    )


def test_no_declared_dependency_carries_a_non_commercial_licence() -> None:
    offenders = []
    for name in sorted(_closure(_declared_requirements())):
        text = _licence_text(name)
        for marker in NON_COMMERCIAL_MARKERS:
            if marker in text:
                offenders.append(f"{name}: licence metadata contains {marker!r}")
                break
    assert not offenders, "\n".join(offenders)


def test_banned_modules_are_not_importable_via_seamkiln() -> None:
    """Belt and braces: catches a vendored copy that declares nothing."""
    import importlib.util

    found = [
        name
        for name in BANNED
        if name != "arcsim" and importlib.util.find_spec(name.replace("-", "_")) is not None
    ]
    assert not found, "\n".join(
        f"{name} is importable: {BANNED[name][0]}. Use instead: {BANNED[name][1]}."
        for name in found
    )


@pytest.mark.parametrize("intruder", ["triangle", "smplx"])
def test_the_gate_actually_fires(intruder: str, monkeypatch) -> None:
    """A gate nobody has seen fail is a gate nobody knows is wired up."""
    monkeypatch.setattr(
        "test_licences._declared_requirements", lambda: {"numpy", intruder}, raising=True
    )
    with pytest.raises(AssertionError) as excinfo:
        test_no_banned_distribution_in_the_declared_closure()
    message = str(excinfo.value)
    assert intruder in message
    assert BANNED[intruder][1].split()[0] in message  # the replacement is named


def test_licence_marker_scan_catches_a_non_commercial_string(monkeypatch) -> None:
    monkeypatch.setattr("test_licences._declared_requirements", lambda: {"pretend"}, raising=True)
    monkeypatch.setattr("test_licences._closure", lambda names, depth=6: {"pretend"}, raising=True)
    monkeypatch.setattr(
        "test_licences._licence_text",
        lambda name: "nvidia source code license (non-commercial use only)",
        raising=True,
    )
    with pytest.raises(AssertionError, match="non-commercial"):
        test_no_declared_dependency_carries_a_non_commercial_licence()
