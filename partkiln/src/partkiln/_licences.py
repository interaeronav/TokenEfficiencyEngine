"""Licence metadata plumbing for the gate in `tests/test_licences.py`.

Installed metadata is inconsistent on purpose-free grounds: on 2026-09-02 in
`server/.venv`, numpy carries a `License-Expression`, scipy carries only a
Trove classifier plus the first line of its LICENSE.txt, trimesh pastes the
whole MIT text into `License`, vtk says `BSD`, and python-dateutil says "Dual
License" with two classifiers. A gate that read one field would pass nothing
or everything. So the resolution order is fixed here, in one place:

    1. `License-Expression` (PEP 639), verbatim;
    2. else the Trove `License ::` classifiers, mapped to SPDX (several ->
       joined with OR, because a dual licence is the user's choice);
    3. else the free-text `License` field through an alias table;
    4. else None - and the gate FAILS on None. Silence is not permission.

Every function here is pure and takes its metadata through `metadata_of` /
`requires_of`, which the deliberate-failure tests monkeypatch instead of
installing anything. Nothing here imports OCP, tee, or packaging eagerly:
`packaging.licenses` is loaded lazily so `import partkiln` stays cheap and
dependency-free, and the tests skip the canonicalisation sub-check when it
is absent.
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Iterable, Mapping
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Any

from partkiln.document import CommandError

ROOT = Path(__file__).resolve().parents[2]  # partkiln/

# Trove classifier -> SPDX. Only classifiers a wheel on this lane can plausibly
# carry; an unlisted `License ::` classifier maps to nothing and falls through.
CLASSIFIER_SPDX: dict[str, str] = {
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: MIT No Attribution License (MIT-0)": "MIT-0",
    "License :: OSI Approved :: BSD License": "BSD-3-Clause",
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: zlib/libpng License": "Zlib",
    "License :: OSI Approved :: Boost Software License 1.0 (BSL-1.0)": "BSL-1.0",
    "License :: OSI Approved :: The Unlicense (Unlicense)": "Unlicense",
    "License :: OSI Approved :: Historical Permission Notice and Disclaimer (HPND)": "HPND",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "License :: OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)": "EPL-2.0",
    "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)": "LGPL-2.0-only",
    "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)": (
        "LGPL-2.0-or-later"
    ),
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)": "LGPL-3.0-only",
    "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)": (
        "LGPL-3.0-or-later"
    ),
    "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)": (
        "LGPL-2.1-or-later"
    ),
    "License :: OSI Approved :: GNU General Public License v2 (GPLv2)": "GPL-2.0-only",
    "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)": (
        "GPL-2.0-or-later"
    ),
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)": "GPL-3.0-only",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)": (
        "GPL-3.0-or-later"
    ),
    "License :: OSI Approved :: GNU General Public License (GPL)": "GPL-2.0-or-later",
    "License :: OSI Approved :: GNU Affero General Public License v3": "AGPL-3.0-only",
    "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)": (
        "AGPL-3.0-or-later"
    ),
    "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication": "CC0-1.0",
    "License :: Public Domain": "LicenseRef-Public-Domain",
    "License :: Other/Proprietary License": "LicenseRef-Proprietary",
    "License :: Free for non-commercial use": "LicenseRef-Non-Commercial",
    "License :: Free For Educational Use": "LicenseRef-Educational-Only",
    "License :: Free For Home Use": "LicenseRef-Home-Use-Only",
}

# Free-text `License` field (first non-empty line, lower-cased, whitespace
# collapsed) -> SPDX. The scipy line is its LICENSE.txt header, which is the
# BSD-3-Clause text (scipy/LICENSE.txt); it earns a name of its own because
# the classifier is the only other evidence scipy ships.
FREE_TEXT_SPDX: dict[str, str] = {
    "mit": "MIT",
    "mit license": "MIT",
    "mit license (mit)": "MIT",
    "the mit license": "MIT",
    "the mit license (mit)": "MIT",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "3-clause bsd": "BSD-3-Clause",
    "3-clause bsd license": "BSD-3-Clause",
    "new bsd": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "modified bsd": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "bsd 2-clause license": "BSD-2-Clause",
    "simplified bsd": "BSD-2-Clause",
    "simplified bsd license": "BSD-2-Clause",
    "apache": "Apache-2.0",
    "apache 2": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache-2": "Apache-2.0",
    "apache license": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache license version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache software license 2.0": "Apache-2.0",
    "apache public license 2.0": "Apache-2.0",
    "asl 2.0": "Apache-2.0",
    "psf": "PSF-2.0",
    "psfl": "PSF-2.0",
    "psf-2.0": "PSF-2.0",
    "psf license": "PSF-2.0",
    "python software foundation license": "PSF-2.0",
    "isc": "ISC",
    "isc license": "ISC",
    "isc license (iscl)": "ISC",
    "zlib": "Zlib",
    "zlib/libpng": "Zlib",
    "zlib/libpng license": "Zlib",
    "0bsd": "0BSD",
    "cc0": "CC0-1.0",
    "cc0-1.0": "CC0-1.0",
    "cc0 1.0": "CC0-1.0",
    "cc0 1.0 universal": "CC0-1.0",
    "mpl-2.0": "MPL-2.0",
    "mpl 2.0": "MPL-2.0",
    "mozilla public license 2.0": "MPL-2.0",
    "mozilla public license 2.0 (mpl 2.0)": "MPL-2.0",
    "lgpl": "LGPL-2.1-or-later",
    "lgpl-2.1": "LGPL-2.1-only",
    "lgplv2.1": "LGPL-2.1-only",
    "lgpl-3.0": "LGPL-3.0-only",
    "lgplv3": "LGPL-3.0-only",
    "lgplv3+": "LGPL-3.0-or-later",
    "gpl": "GPL-2.0-or-later",
    "gpl-2.0": "GPL-2.0-only",
    "gplv2": "GPL-2.0-only",
    "gplv2+": "GPL-2.0-or-later",
    "gpl-3.0": "GPL-3.0-only",
    "gplv3": "GPL-3.0-only",
    "gplv3+": "GPL-3.0-or-later",
    "agpl-3.0": "AGPL-3.0-only",
    "agplv3": "AGPL-3.0-only",
    "copyright (c) 2001-2002 enthought, inc. 2003, scipy developers.": "BSD-3-Clause",
    "copyright (c) 2001-2002 enthought, inc. 2003-2024, scipy developers.": "BSD-3-Clause",
}

# The GNU family spelt out in words ("GNU Lesser General Public License v3").
# Ordered: the more specific pattern first, and Lesser/Affero before plain GPL.
_GNU_FREE_TEXT: tuple[tuple[str, str], ...] = (
    (r"lesser general public license.*\b(v\.?\s?|version\s)?2\.1", "LGPL-2.1-only"),
    (r"lesser general public license.*\b(v\.?\s?|version\s)?3", "LGPL-3.0-only"),
    (r"lesser general public license.*\b(v\.?\s?|version\s)?2\b", "LGPL-2.0-only"),
    (r"lesser general public license", "LGPL-2.1-or-later"),
    (r"affero general public license", "AGPL-3.0-only"),
    (r"general public license.*\b(v\.?\s?|version\s)?3", "GPL-3.0-only"),
    (r"general public license.*\b(v\.?\s?|version\s)?2", "GPL-2.0-only"),
    (r"general public license", "GPL-2.0-or-later"),
)

_NAME_SEPARATORS = ("[", ">", "<", "=", "!", "~", " ", "(", ";", "@")
_TOKEN = re.compile(r"\(|\)|[A-Za-z0-9.+\-]+")


def normalise(name: str) -> str:
    """The distribution name as `importlib.metadata` keys it: lower, hyphens."""
    for sep in _NAME_SEPARATORS:
        name = name.split(sep)[0]
    return name.strip().lower().replace("_", "-")


# --- the two monkeypatchable sources ------------------------------------------


def metadata_of(dist_name: str) -> Mapping[str, Any] | None:
    """The installed distribution's metadata, or None when it is not installed.

    Returns the `email.message.Message`-like object `importlib.metadata`
    hands back (`.get`, `.get_all`). The deliberate-failure tests replace
    this function with a fake that answers for a distribution that does not
    exist - which is how the gate is proven to fire without installing
    anything that would then have to be uninstalled.
    """
    try:
        return distribution(dist_name).metadata
    except PackageNotFoundError:
        return None


def requires_of(dist_name: str) -> list[str] | None:
    """The distribution's `Requires-Dist` lines, or None when not installed."""
    try:
        return list(distribution(dist_name).requires or [])
    except PackageNotFoundError:
        return None


# --- resolution ---------------------------------------------------------------


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = " ".join(line.split()).strip()
        if line:
            return line
    return ""


def canonicalize(expression: str) -> str | None:
    """`packaging.licenses.canonicalize_license_expression`, or None if
    packaging is absent or the expression is not valid SPDX. Lazy on purpose:
    packaging is a dev dependency, never a partkiln one."""
    try:
        from packaging.licenses import InvalidLicenseExpression, canonicalize_license_expression
    except ImportError:
        return None
    try:
        return canonicalize_license_expression(expression)
    except InvalidLicenseExpression:
        return None


def spdx_from_free_text(text: str) -> str | None:
    """Step 3: the `License` field. The first line carries the name when the
    field holds a whole licence text (trimesh, contourpy); the alias table
    handles the historical spellings; the GNU family is matched in words."""
    line = _first_line(text)
    if not line:
        return None
    key = line.lower().rstrip(",;")
    if key in FREE_TEXT_SPDX:
        return FREE_TEXT_SPDX[key]
    if key.rstrip(".") in FREE_TEXT_SPDX:
        return FREE_TEXT_SPDX[key.rstrip(".")]
    for pattern, spdx in _GNU_FREE_TEXT:
        if re.search(pattern, key):
            return spdx
    # A field that already IS an SPDX expression ("MIT-CMU", "MIT OR Apache-2.0").
    if len(line) <= 80 and "copyright" not in key:
        return canonicalize(line)
    return None


def spdx_from_classifiers(classifiers: Iterable[str]) -> str | None:
    """Step 2: every `License ::` classifier that maps, joined with OR."""
    found = [CLASSIFIER_SPDX[c.strip()] for c in classifiers if c.strip() in CLASSIFIER_SPDX]
    if not found:
        return None
    unique = list(dict.fromkeys(found))
    return " OR ".join(unique) if len(unique) > 1 else unique[0]


def spdx_of(dist_name: str) -> str | None:
    """The distribution's licence as an SPDX expression, or None only when the
    `License-Expression` field, the classifiers and the `License` field are
    ALL empty or unmappable (an uninstalled distribution is also None)."""
    meta = metadata_of(dist_name)
    if meta is None:
        return None
    expression = (meta.get("License-Expression") or "").strip()
    if expression:
        return expression
    from_classifiers = spdx_from_classifiers(meta.get_all("Classifier") or [])
    if from_classifiers:
        return from_classifiers
    return spdx_from_free_text(meta.get("License") or "")


def licence_text(dist_name: str) -> str:
    """Everything the metadata says about licensing, lower-cased, for the
    non-commercial marker scan. Empty when the distribution is absent."""
    meta = metadata_of(dist_name)
    if meta is None:
        return ""
    parts = [meta.get("License") or "", meta.get("License-Expression") or ""]
    parts.extend(meta.get_all("Classifier") or [])
    return " ".join(parts).lower()


# --- SPDX expressions ---------------------------------------------------------


def _parse(tokens: list[str], pos: int) -> tuple[Any, int]:
    """SPDX precedence: WITH binds tightest, then AND, then OR."""
    node, pos = _parse_and(tokens, pos)
    while pos < len(tokens) and tokens[pos].upper() == "OR":
        rhs, pos = _parse_and(tokens, pos + 1)
        node = ("OR", node, rhs)
    return node, pos


def _parse_and(tokens: list[str], pos: int) -> tuple[Any, int]:
    node, pos = _parse_with(tokens, pos)
    while pos < len(tokens) and tokens[pos].upper() == "AND":
        rhs, pos = _parse_with(tokens, pos + 1)
        node = ("AND", node, rhs)
    return node, pos


def _parse_with(tokens: list[str], pos: int) -> tuple[Any, int]:
    if pos >= len(tokens):
        raise ValueError("SPDX expression ends where a licence id was expected")
    if tokens[pos] == "(":
        node, pos = _parse(tokens, pos + 1)
        if pos >= len(tokens) or tokens[pos] != ")":
            raise ValueError("SPDX expression has an unclosed '('")
        pos += 1
    else:
        node, pos = tokens[pos], pos + 1
    if pos < len(tokens) and tokens[pos].upper() == "WITH":
        if pos + 1 >= len(tokens):
            raise ValueError("SPDX 'WITH' names no exception")
        node, pos = f"{node} WITH {tokens[pos + 1]}", pos + 2
    return node, pos


def _judge(node: Any, allow: frozenset[str], exceptions: frozenset[str]) -> tuple[bool, list[str]]:
    if isinstance(node, str):
        if node in exceptions or node in allow:
            return True, []
        # "X WITH Y" is allowed when the whole phrase is a named exception, or
        # when X itself is permissive (an exception only ever loosens X).
        base = node.split(" WITH ", 1)[0]
        return (True, []) if base in allow else (False, [node])
    op, lhs, rhs = node
    ok_l, bad_l = _judge(lhs, allow, exceptions)
    ok_r, bad_r = _judge(rhs, allow, exceptions)
    if op == "AND":
        return ok_l and ok_r, bad_l + bad_r
    return ok_l or ok_r, [] if (ok_l or ok_r) else bad_l + bad_r


def expression_verdict(
    expression: str, *, allow: Iterable[str], exceptions: Iterable[str] = ()
) -> tuple[bool, list[str]]:
    """(allowed, offending operands). Every AND operand must be allowlisted;
    an OR passes when any branch does; `exceptions` are whole `X WITH Y`
    phrases accepted by name (the one OCCT exception)."""
    canonical = canonicalize(expression) or expression
    tokens = _TOKEN.findall(canonical)
    if not tokens:
        return False, [expression]
    try:
        node, pos = _parse(tokens, 0)
    except ValueError:
        return False, [expression]
    if pos != len(tokens):
        return False, [expression]
    return _judge(node, frozenset(allow), frozenset(exceptions))


# --- the declared tree --------------------------------------------------------


def _pyproject() -> dict[str, Any]:
    return tomllib.loads((ROOT / "pyproject.toml").read_text())


def declared_requirements(extra: str | None = None) -> list[str]:
    """Normalised distribution names partkiln declares: the core list when
    `extra` is None, else exactly that optional extra. An unknown extra is a
    refusal naming the ones that exist."""
    project = _pyproject()["project"]
    if extra is None:
        specs = project.get("dependencies", [])
    else:
        extras = project.get("optional-dependencies", {})
        if extra not in extras:
            raise CommandError(
                f"pyproject.toml declares no extra {extra!r}. "
                f"Fix: pass one of {', '.join(sorted(extras))}, or None for the core list.",
                code="pk_ref_unknown",
            )
        specs = extras[extra]
    names = {normalise(spec.split(";")[0]) for spec in specs}
    return sorted(n for n in names if n)


def closure(names: Iterable[str], *, depth: int = 8) -> set[str]:
    """Transitive dependency closure over what is actually installed.

    Declared names stay in the result even when uninstalled (a banned name is
    banned whether or not it is present), and `extra ==` requirements are
    skipped: a package's optional dependencies are doors nobody opened.
    Scoped to the names given, never to the whole environment, because the
    surrounding venv is TEE's and this gate is about what PARTKILN pulls in.
    """
    seen: set[str] = set()
    frontier = {normalise(n) for n in names}
    for _ in range(depth):
        nxt: set[str] = set()
        for name in sorted(frontier - seen):
            seen.add(name)
            for requirement in requires_of(name) or []:
                if "extra ==" in requirement:
                    continue
                child = normalise(requirement.split(";")[0])
                if child:
                    nxt.add(child)
        if not nxt - seen:
            break
        frontier = nxt
    return seen
