"""Start the bundled source on an interpreter that already has the deps.

This is the whole difference between the two bundle shapes. The `uv` shape
ships `pyproject.toml` + `uv.lock` and Claude Desktop provisions a venv from
them with `uv sync`, which rebuilds strictly from the lock and DELETES every
extra installed on top - and TEE's fleet extras are on top by design, because
keeping them out is what holds the base install to 586 MB instead of 2.2 GB.

This shape ships no venv at all. The manifest names an interpreter that
already carries the dependencies, and this shim puts the bundle's OWN `src`
ahead of whatever that interpreter can already import, so the code is the
bundle's and only the dependencies are borrowed.

`dont_write_bytecode` is not tidiness: A73 measured `pvpython` writing 201
`.pyc` files into ParaView's signed `.app`, breaking its notarization seal so
macOS refused to launch it. The manifest sets PYTHONDONTWRITEBYTECODE too;
this line covers a launch that bypasses the manifest's env.
"""

import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tee.cli import main  # noqa: E402  (must follow the path insert)

if __name__ == "__main__":
    main()
