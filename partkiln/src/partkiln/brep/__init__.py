"""The B-rep kernel: the ONLY place partkiln imports OCP, and only lazily.

`import partkiln` must succeed with no OCP installed (D1), so this package's
`__init__` imports none of its siblings and no OCP. Every sibling module
(`shapes`, `query`, `history`, `fingerprint`, `mesh`, `fixtures`) calls
`require_ocp()` at its top BEFORE its OCP imports, so importing any of them
without the wheel is one clear `KernelError` naming the install line - never
an `ImportError` three frames deep inside OCP's own package.

Measured (A66 P0a, 2026-09-02): `import OCP` costs 26 s COLD in a fresh venv
and 0.3 s warm; that is why the sidecar venv is separate and why Law 17
(cold import never blocks a call) exists. `cadquery-ocp` and
`cadquery-ocp-novtk` both ship the top-level `OCP/` package and clobber each
other, so an already-present OCP is accepted and never co-installed.
"""

from __future__ import annotations

from importlib.util import find_spec

from partkiln._errors import KernelError

INSTALL_LINE = (
    "uv venv --python 3.11 ~/TEE/.tee/sidecars/partkiln && "
    "uv pip install --python ~/TEE/.tee/sidecars/partkiln/bin/python -e <repo>/partkiln[brep]"
)

_ocp_present: bool | None = None


def ocp_available() -> bool:
    """True when the OCP wheel is importable (checked once, without importing it)."""
    global _ocp_present
    if _ocp_present is None:
        _ocp_present = find_spec("OCP") is not None
    return _ocp_present


def require_ocp() -> None:
    """Refuse with the install line when OCP is absent.

    Raises `KernelError`, never `ImportError`, so the wire error is
    `pk_no_brep` with the fix inline (Law: a refusal names the fix).
    """
    if not ocp_available():
        raise KernelError(
            "partkiln[brep] is not installed in this interpreter (no OCP module).",
            fix=INSTALL_LINE,
        )


__all__ = ["INSTALL_LINE", "ocp_available", "require_ocp"]
