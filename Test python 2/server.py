"""Serve the local PDF workspace without exposing other files in the project."""

from __future__ import annotations

import argparse
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent
PUBLIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "text/javascript; charset=utf-8"),
}


class LocalWorkspaceHandler(BaseHTTPRequestHandler):
    """Expose only the static files needed by the browser app."""

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        entry = PUBLIC_FILES.get(path)
        if entry is None:
            self.send_error(404, "Not found")
            return

        filename, content_type = entry
        try:
            body = (ROOT / filename).read_bytes()
        except OSError:
            self.send_error(500, "Workspace file could not be read")
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(filename)[0])
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        # Avoid logging request data that could contain local filenames.
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Document Desk local PDF workspace.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: loopback only)")
    parser.add_argument("--port", type=int, default=8000, help="Local port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open a browser window")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("For privacy, the workspace server only supports loopback addresses.")
    server = ThreadingHTTPServer((args.host, args.port), LocalWorkspaceHandler)
    url_host = "[::1]" if args.host == "::1" else "127.0.0.1"
    url = f"http://{url_host}:{server.server_address[1]}/"
    print(f"Document Desk is available at {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Document Desk.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
