#!/usr/bin/env python3
"""Print `name==version` for packages named in a uv lock file.

WHY this exists: CI installs the CPU build of torch from download.pytorch.org
instead of the CUDA build the lock resolves from PyPI (2,189 MB of nvidia-*
wheels a GPU-less runner can never execute). That install happens OUTSIDE
`uv sync`, so its version would drift the moment the lock moved. Reading the
version back out of the lock keeps the one pin honest without a second place
to remember. Stdlib only - it runs before any environment exists.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: lock_version.py <uv.lock> <package> [package ...]", file=sys.stderr)
        return 2
    lock_path = Path(argv[1])
    try:
        lock = tomllib.loads(lock_path.read_text())
    except FileNotFoundError:
        print(f"lock_missing: {lock_path} does not exist", file=sys.stderr)
        return 2
    versions: dict[str, set[str]] = {}
    for pkg in lock.get("package", []):
        if "version" in pkg:
            versions.setdefault(pkg["name"], set()).add(pkg["version"])

    out: list[str] = []
    for raw in argv[2:]:
        name = re.sub(r"[-_.]+", "-", raw).lower()
        found = versions.get(name)
        if not found:
            print(
                f"lock_no_such_package: '{raw}' is not in {lock_path}. "
                f"Fix: name a package the lock resolves, or re-run `uv lock`.",
                file=sys.stderr,
            )
            return 1
        if len(found) > 1:
            print(
                f"lock_forked_version: '{raw}' resolves to {sorted(found)} in {lock_path}. "
                f"Fix: pin it in the workflow instead of reading it from the lock.",
                file=sys.stderr,
            )
            return 1
        out.append(f"{name}=={found.pop()}")
    print(" ".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
