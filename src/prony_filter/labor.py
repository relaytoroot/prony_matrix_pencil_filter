"""Lokale Browseroberfläche für das Matrix-Pencil-Labor."""

from __future__ import annotations

import argparse
import errno
import json
import logging
import socket
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from .labor_analysis import analyze
from .labor_catalog import catalog, public_catalog


_UI = Path(__file__).with_name("labor_ui")
_ASSETS = {
    "/": ("index.html", "text/html"),
    "/index.html": ("index.html", "text/html"),
    "/style.css": ("style.css", "text/css"),
    "/app.js": ("app.js", "text/javascript"),
}
_ANALYSIS_LOCK = threading.Lock()


class LaborServer(ThreadingHTTPServer):
    def server_bind(self) -> None:
        # Windows kann sonst zwei HTTP-Server auf denselben Port binden.
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.allow_reuse_address = False
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class LaborHandler(BaseHTTPRequestHandler):
    """Liefert die Bedienoberfläche und berechnet die angeforderte Analyse."""

    def _reply(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Prony-Labor", "1")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # Das Browserfenster wurde während der Berechnung geschlossen.

    def _error(self, code: int, message: str) -> None:
        self._reply(code, "application/json", json.dumps({"error": message}).encode())

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/catalog":
            body = json.dumps(public_catalog(), ensure_ascii=False).encode("utf-8")
            self._reply(HTTPStatus.OK, "application/json", body)
            return
        if path.startswith("/api/data/") and path.endswith(".csv"):
            entry = catalog().get(path[len("/api/data/"):-4], {})
            if "csvPath" in entry:
                self._reply(HTTPStatus.OK, "text/csv", entry["csvPath"].read_bytes())
                return
        asset = _ASSETS.get(path)
        if asset is None:
            self._error(HTTPStatus.NOT_FOUND, "Diese Adresse gibt es im Labor nicht.")
            return
        filename, content_type = asset
        self._reply(HTTPStatus.OK, content_type, (_UI / filename).read_bytes())

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/analyze":
            self._error(HTTPStatus.NOT_FOUND, "Unbekannte Laborfunktion.")
            return
        port = self.server.server_address[1]
        host = self.headers.get("Host")
        origin = self.headers.get("Origin")
        if host not in {f"127.0.0.1:{port}", f"localhost:{port}"} or (
            origin is not None and origin != f"http://{host}"
        ):
            self._error(HTTPStatus.FORBIDDEN, "Öffne die Analyse im lokalen Labor.")
            return
        if self.headers.get_content_type() != "application/json":
            self._error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Parameter als JSON senden.")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = 0
        if not 0 < size <= 8192:
            self._error(HTTPStatus.BAD_REQUEST, "Ungültige Größe der Parameterliste.")
            return
        try:
            settings = json.loads(self.rfile.read(size))
        except (ValueError, RecursionError):
            self._error(HTTPStatus.BAD_REQUEST, "Die Parameter sind kein gültiges JSON.")
            return
        if not isinstance(settings, dict):
            self._error(HTTPStatus.BAD_REQUEST, "Die Analyse erwartet benannte Parameter.")
            return
        try:
            with _ANALYSIS_LOCK:
                result = analyze(settings)
            body = json.dumps(result, allow_nan=False, separators=(",", ":")).encode()
        except ValueError as exc:
            self._error(HTTPStatus.UNPROCESSABLE_ENTITY, str(exc))
            return
        except FileNotFoundError:
            self._error(HTTPStatus.NOT_FOUND, "Die Messdatei fehlt im Datenordner des Projekts.")
            return
        except Exception:
            logging.exception("Analyse fehlgeschlagen")
            self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "Die Analyse ist fehlgeschlagen. Details stehen im Terminal.")
            return
        self._reply(HTTPStatus.OK, "application/json", body)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8791, help="Lokaler Port (Standard 8791, 0 für freie Wahl)")
    parser.add_argument("--no-browser", action="store_true", help="Browser nicht automatisch öffnen")
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error("Der Port muss zwischen 0 und 65535 liegen.")
    try:
        server = LaborServer(("127.0.0.1", args.port), LaborHandler)
    except OSError as exc:
        if exc.errno in (errno.EADDRINUSE, errno.EACCES, 10048, 10013) and not args.no_browser:
            url = f"http://127.0.0.1:{args.port}/"
            try:
                with urlopen(url, timeout=1) as response:
                    if response.headers.get("X-Prony-Labor") == "1":
                        print(f"Das Labor läuft bereits unter {url}", flush=True)
                        webbrowser.open(url)
                        return
            except OSError:
                pass
        parser.exit(1, f"Das Labor kann Port {args.port} nicht öffnen ({exc}). Mit --port 0 einen freien Port wählen.\n")
    with server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Matrix-Pencil-Labor unter {url}  ·  Beenden mit Strg+C", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
