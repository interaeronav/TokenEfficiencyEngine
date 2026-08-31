"""A45 P2 — the shared lazy-import + honest-refusal helper for the fleet.

Every fleet group is an OPTIONAL extra. The always-loaded surface must not
grow and the .mcpb must not swell, so nothing here is imported until a tool
is actually called. When the library is absent the caller gets ONE short
structured error naming the exact command - the `web/media.py` pattern,
which exists precisely so a missing extra never arrives as an ImportError
traceback the model has to interpret.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
from typing import Any

from tee.kernel.errors import TeeError

# import name -> distribution name, where they differ
_DIST = {
    "pypfopt": "pyportfolioopt",
    "cv2": "opencv-python-headless",
    "PIL": "pillow",
}

# group -> (pip extra, the resources it brings, install line)
EXTRAS: dict[str, tuple[str, str, str]] = {
    "solve": (
        "solve",
        "HiGHS, SCIP, COIN-OR Cbc, Google OR-Tools",
        "uv pip install 'tee-engine[solve]'",
    ),
    "quant": (
        "quant",
        "PyPortfolioOpt, skfolio, pandas",
        "uv pip install 'tee-engine[quant]'",
    ),
    "cad": (
        "cad",
        "CadQuery (OpenSCAD is a separate app: brew install --cask openscad)",
        "uv pip install 'tee-engine[cad]'",
    ),
    "medimg": (
        "medimg",
        "pydicom + nibabel + numpy - no torch (Orthanc is a separate server you run)",
        "uv pip install 'tee-engine[medimg]'",
    ),
}


# Set once at startup so a refusal can tell "never installed" from "an
# upgrade removed it". None means the app never recorded a state dir, in
# which case the refusal is the plain one and nothing is claimed.
_state_dir: list[Any] = [None]


def bind_state_dir(state_dir: Any) -> None:
    """Called by TeeApp so `need()` can consult the extras record."""
    _state_dir[0] = state_dir


def need(module: str, group: str, *, what: str = "") -> Any:
    """Import `module` or refuse loudly with the exact fix."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        extra, brings, line = EXTRAS.get(group, (group, module, f"uv pip install {module}"))
        detail = f" ({what})" if what else ""
        # An extra that WAS here and is gone is an upgrade artefact, not a
        # setup the owner skipped. Saying "install this" to someone who did
        # install it sends them looking in the wrong place - measured three
        # upgrades running.
        note = None
        try:
            from tee.kernel import extras as _extras

            note = _extras.loss_note(group, _state_dir[0])
        except Exception:  # a diagnostic must never replace the real error
            note = None
        raise TeeError(
            f"{group}_unavailable",
            (f"{note} " if note else "")
            + f"This needs the [{extra}] extra{detail}: {module} is not installed.",
            fix=f"{line}  - brings {brings}.",
        ) from exc


def have(module: str) -> bool:
    """Cheap presence check; never raises, and never IMPORTS.

    A probe that answers "not installed" must not first pay 344 ms to load
    torch in order to say so. `find_spec` locates the module without
    executing it - which also means a probe cannot be poisoned by an
    optional dependency's import-time side effects."""
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError, ModuleNotFoundError):
        return False


def probe_rows(modules: dict[str, str]) -> dict[str, Any]:
    """{label: module} -> a compact installed/absent table for a *_probe tool."""
    rows = {}
    for label, mod in modules.items():
        present = have(mod)
        row: dict[str, Any] = {"installed": present}
        if present:
            # version from metadata, not from importing the package
            for dist in (_DIST.get(mod, mod), mod.replace("_", "-")):
                try:
                    row["version"] = importlib.metadata.version(dist)
                    break
                except importlib.metadata.PackageNotFoundError:
                    continue
        rows[label] = row
    return rows
