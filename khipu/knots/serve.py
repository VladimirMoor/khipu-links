"""Serve the knot-shape page (khipu/knots/index.html) on http://127.0.0.1:8767/ ; its "save" button PUTs the shapes,
which are written to site/knots.json."""
import http.server
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[1] / "site/knots.json"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(HERE), **k)

    def do_PUT(self):
        if self.path != "/knots.json":
            self.send_response(404); self.end_headers(); return
        OUT.write_bytes(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok")
        print(f"wrote {OUT}")


if __name__ == "__main__":
    print("http://127.0.0.1:8767/")
    http.server.ThreadingHTTPServer(("127.0.0.1", 8767), Handler).serve_forever()
