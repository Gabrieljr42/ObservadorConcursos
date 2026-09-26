"""Serve the exported Expo app locally with the isolation required by SQLite WASM."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from http.client import HTTPConnection
from pathlib import Path
import re
import signal
import threading
from urllib.parse import urlsplit


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/web", **kwargs)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            return self.proxy_api()
        path = urlsplit(self.path).path
        local = Path(self.translate_path(path))
        if not local.exists() and local.with_suffix(".html").is_file():
            self.path = path + ".html"
        elif re.fullmatch(r'/concurso/[1-9]\d*/?', path):
            self.path = '/concurso/[id].html'
        super().do_GET()

    def proxy_api(self):
        if not self.path.startswith('/api/'):
            self.send_error(404)
            return
        length = int(self.headers.get('Content-Length', '0'))
        if length > 2 * 1024 * 1024:
            self.send_error(413)
            return
        body = self.rfile.read(length) if length else None
        headers = {key: self.headers[key] for key in ('Authorization', 'Content-Type', 'Accept') if key in self.headers}
        # The review UI allows 400 seconds for bounded document preparation.
        # Do not cut its connection while the API is still preserving PDFs.
        document_work = re.fullmatch(r'/api/tenderproof/continuous/document-review/[^/?]+/(?:prepare|cases/[^/?]+/select-document)', self.path)
        connection = HTTPConnection('api', 8000, timeout=420 if document_work else 120)
        try:
            connection.request(self.command, self.path[4:], body=body, headers=headers)
            response = connection.getresponse()
            content = response.read()
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/octet-stream'))
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except (OSError, TimeoutError):
            self.send_error(502, 'Backend local indisponivel')
        finally:
            connection.close()

    do_POST = proxy_api
    do_PUT = proxy_api
    do_PATCH = proxy_api
    do_DELETE = proxy_api


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 13000), Handler)
    server.daemon_threads = False
    # Python running as PID 1 needs an explicit SIGTERM handler. shutdown()
    # must run outside serve_forever's thread; server_close drains requests.
    signal.signal(signal.SIGTERM, lambda *_: threading.Thread(target=server.shutdown, daemon=True).start())
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
