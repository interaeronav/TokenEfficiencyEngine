"""License lint (script 13.1.2 acceptance): prove the runtime tree keeps
NVIDIA-non-commercial, GPL, and LGPL imports out of the import path.

Rules:
- BANNED modules may never be imported, guarded or not.
- OPTIONAL_ACCELERATORS (cumesh, flex_gemm - CUDA-only, MIT with a
  non-commercial cubvh inside cumesh) may appear ONLY inside try/except
  ImportError guards, so a machine without them never touches them and a
  distribution never requires them.
"""

from __future__ import annotations

import ast
from pathlib import Path

BANNED = {
    "nvdiffrast": "NVIDIA Source Code License (non-commercial)",
    "nvdiffrec_render": "NVIDIA Source Code License (non-commercial)",
    "plyfile": "GPLv3+",
    "easydict": "LGPL-3.0",
    "pymeshlab": "GPL-3.0 (eval-venv only, never product)",
    "pymeshfix": "GPL-3.0 (subprocess only, never imported)",
    "bpy": "GPL (Blender stays out-of-process)",
}

OPTIONAL_ACCELERATORS = {"cumesh", "flex_gemm"}

# Banned MODEL WEIGHTS, referenced by repo id rather than by import - so the
# import lint above could never see them. The upstream pipeline config names
# briaai/RMBG-2.0 (CC-BY-NC) as its matting model; voxkiln substitutes MIT
# BiRefNet at load time, and this rule exists so a NEW reference cannot creep
# in unnoticed the way a string in a config would.
BANNED_WEIGHTS = {
    "briaai/RMBG-2.0": "CC-BY-NC 4.0 (non-commercial)",
    "briaai/RMBG-1.4": "CC-BY-NC 4.0 (non-commercial)",
}

# Files that legitimately MENTION a banned repo id in order to REJECT or
# replace it: this module (the rule table) and BiRefNet.py (the substitution
# site, which matches on the name to swap in the MIT weights).
WEIGHT_MENTION_ALLOWLIST = {"license_lint.py", "engine.py", "BiRefNet.py"}

# Backend modules loaded ONLY by name through the conv dispatch
# (importlib in sparse/conv/conv.py) - never imported unless that backend
# is explicitly selected, so their unguarded imports are already lazy.
LAZY_DISPATCH_FILES = {"conv_flex_gemm.py", "conv_spconv.py", "conv_torchsparse.py"}


def _module_root(node: ast.AST) -> list[str]:
    names = []
    if isinstance(node, ast.Import):
        names = [alias.name.split(".")[0] for alias in node.names]
    elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
        names = [node.module.split(".")[0]]
    return names


def _guarded_nodes(tree: ast.AST) -> set[int]:
    """ids of import nodes inside try/except blocks."""
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            for child in ast.walk(node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    guarded.add(id(child))
    return guarded


def lint_tree(*roots: str | Path) -> list[dict[str, str]]:
    """Return violations; empty list = clean."""
    violations: list[dict[str, str]] = []
    for root in roots:
        for path in sorted(Path(root).rglob("*.py")):
            if path.name in LAZY_DISPATCH_FILES:
                continue
            tree = ast.parse(path.read_text(), filename=str(path))
            guarded = _guarded_nodes(tree)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for mod in _module_root(node):
                    if mod in BANNED:
                        violations.append(
                            {
                                "file": str(path),
                                "line": str(node.lineno),
                                "module": mod,
                                "why": BANNED[mod],
                            }
                        )
                    elif mod in OPTIONAL_ACCELERATORS and id(node) not in guarded:
                        violations.append(
                            {
                                "file": str(path),
                                "line": str(node.lineno),
                                "module": mod,
                                "why": "optional CUDA accelerator must be try/except-guarded",
                            }
                        )
    violations.extend(lint_weights(*roots))
    return violations


def lint_weights(*roots: str | Path) -> list[dict[str, str]]:
    """Catch banned model repo ids anywhere in the tree, including configs.

    Weights are named as STRINGS in json/py, so the AST import lint cannot see
    them - a non-commercial matting model can ride along in a vendored config
    with every import perfectly clean.
    """
    violations: list[dict[str, str]] = []
    for root in roots:
        for path in sorted(Path(root).rglob("*")):
            if not path.is_file() or path.suffix not in (".py", ".json"):
                continue
            if path.name in WEIGHT_MENTION_ALLOWLIST:
                continue
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            for repo, why in BANNED_WEIGHTS.items():
                if repo in text:
                    violations.append(
                        {"file": str(path), "line": "-", "module": repo, "why": why}
                    )
    return violations


def main() -> int:  # pragma: no cover - thin CLI shell
    import json

    here = Path(__file__).resolve().parent
    roots = [here]
    vendor = here.parent.parent / "vendor"
    if vendor.exists():
        roots.append(vendor)
    bad = lint_tree(*roots)
    print(json.dumps({"clean": not bad, "violations": bad}, indent=1))
    return 1 if bad else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
