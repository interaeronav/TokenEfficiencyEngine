# SPDX-License-Identifier: GPL-3.0-or-later
"""Run the TEE bridge in headless Blender:

    blender --background [file.blend] --python boot_background.py -- --port 9876

Serves until the process is terminated. Deferred responses are not supported
in background mode; every request completes synchronously.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bridge_server  # noqa: E402


def main() -> None:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(prog="tee_bridge")
    parser.add_argument("--host", default=bridge_server.DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=bridge_server.DEFAULT_PORT)
    args = parser.parse_args(argv)
    bridge_server.run_blocking(args.host, args.port)


if __name__ == "__main__":
    main()
