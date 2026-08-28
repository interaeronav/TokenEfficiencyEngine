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
