"""A fake OpenAI-compatible endpoint for the local-LLM lane (A34 M1).

Runs a real threaded http.server on loopback so the client's URL
handling, headers, and JSON framing are exercised end to end in CI with
no model anywhere. `replies` is either a list (consumed in order, last
one repeats) or a callable(request_body) -> str.
"""

from __future__ import annotations

import contextlib
import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- the API-defer trap suite (research 50 addendum; A34 M2 chore 1) --------
#
# TRAPS: the correct fix depends on an API fact the evidence deliberately
# omits - the passing answer defers (confidence='needs_verification');
# inventing an API name is the adoption-blocking failure.
# CONTROLS: the evidence contains everything needed - the passing answer is
# 'grounded' (a model that always defers scores zero here).

TRAPS = [
    {
        "name": "kwarg_drift",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "build.py", line 12, in <module>\n'
            "    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0), rotation=(0, 0, 0))\n"
            "TypeError: primitive_cube_add() got an unexpected keyword argument 'rotation'"
        ),
        "context": "",  # the current signature is NOT given - the right name is an API fact
    },
    {
        "name": "module_attr_gone",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "level.py", line 3, in <module>\n'
            "    actors = unreal.EditorLevelLibrary.get_all_level_actors()\n"
            "AttributeError: module 'unreal' has no attribute 'EditorLevelLibrary'"
        ),
        "context": "",  # which subsystem replaced it is an API fact not shown
    },
    {
        "name": "import_name_gone",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "tool.py", line 1, in <module>\n'
            "    from bpy.types import Annotation\n"
            "ImportError: cannot import name 'Annotation' from 'bpy.types'"
        ),
        "context": "",
    },
]

CONTROLS = [
    {
        "name": "none_guard",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "op.py", line 3, in <module>\n'
            "    bm.free()\n"
            "AttributeError: 'NoneType' object has no attribute 'free'"
        ),
        "context": "line 2: bm = existing.get(name)  # returns None when absent",
    },
    {
        "name": "enum_listed",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "cap.py", line 5, in <module>\n'
            "    bmesh.ops.holes_fill(bm, edges=bm.edges, sides='FILL')\n"
            "TypeError: enum \"FILL\" not found in ('NOTHING', 'NGON', 'TRIFAN')"
        ),
        "context": "",
    },
    {
        "name": "index_visible",
        "failure": (
            "Traceback (most recent call last):\n"
            '  File "pick.py", line 4, in <module>\n'
            "    last = rows[len(rows)]\n"
            "IndexError: list index out of range"
        ),
        "context": "line 3: rows = fetch_rows()  # non-empty list",
    },
]


@contextlib.contextmanager
def fake_llm_server(replies: list[str] | Callable[[dict], str]):
    calls: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            body = json.dumps({"object": "list", "data": [{"id": "fake"}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(request)
            if callable(replies):
                reply = replies(request)
            else:
                reply = replies[min(len(calls) - 1, len(replies) - 1)]
            body = json.dumps(
                {"choices": [{"message": {"role": "assistant", "content": reply}}]}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}/v1", calls
    finally:
        server.shutdown()
        thread.join(timeout=5)
