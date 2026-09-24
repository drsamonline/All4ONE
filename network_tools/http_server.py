from __future__ import annotations

import argparse
import functools
import http.server
import socketserver
from pathlib import Path


def run(args=None):
    p = argparse.ArgumentParser(description="Serve a directory over local HTTP.")
    p.add_argument("directory", nargs="?", default=".")
    p.add_argument("--port", type=int, default=8000)
    a = p.parse_args(args or [])
    root = Path(a.directory).resolve()
    if not root.is_dir():
        print("Directory not found.")
        return 1
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    with socketserver.ThreadingTCPServer(("127.0.0.1", a.port), handler) as server:
        server.daemon_threads = True
        print(f"Serving {root} at http://127.0.0.1:{a.port} (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
    return 0
