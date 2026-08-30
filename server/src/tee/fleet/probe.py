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
from typing import Any

from tee.kernel.errors import TeeError

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
    "medimg": (
        "medimg",
        "MONAI Core (Orthanc itself is a separate server you run)",
        "uv pip install 'tee-engine[medimg]'",
    ),
}


def need(module: str, group: str, *, what: str = "") -> Any:
    """Import `module` or refuse loudly with the exact fix."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        extra, brings, line = EXTRAS.get(group, (group, module, f"uv pip install {module}"))
        detail = f" ({what})" if what else ""
        raise TeeError(
            f"{group}_unavailable",
            f"This needs the [{extra}] extra{detail}: {module} is not installed.",
            fix=f"{line}  - brings {brings}.",
        ) from exc


def have(module: str) -> bool:
    """Cheap presence check for probe tools; never raises."""
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False


def probe_rows(modules: dict[str, str]) -> dict[str, Any]:
    """{label: module} -> a compact installed/absent table for a *_probe tool."""
    rows = {}
    for label, mod in modules.items():
        present = have(mod)
        row: dict[str, Any] = {"installed": present}
        if present:
            try:
                m = importlib.import_module(mod)
                v = getattr(m, "__version__", None)
                if v:
                    row["version"] = str(v)
            except Exception:
                pass
        rows[label] = row
    return rows
