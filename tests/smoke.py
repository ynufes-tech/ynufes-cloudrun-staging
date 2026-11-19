"""Exercise the built nginx image against real HTTP upstreams in its network namespace."""
import http.client
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time

fixture = json.loads(Path(__file__).with_name("routes.json").read_text())

class Upstream(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"port": self.server.server_port, "path": self.path}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass

servers = []
for port in set(fixture["routes"].values()):
    server = ThreadingHTTPServer(("127.0.0.1", port), Upstream)
    Thread(target=server.serve_forever, daemon=True).start()
    servers.append(server)

def request(path, host="localhost"):
    connection = http.client.HTTPConnection("127.0.0.1", 80, timeout=10)
    try:
        connection.request("GET", path, headers={"Host": host})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()

try:
    for attempt in range(50):
        try:
            request("/robots.txt")
            break
        except (OSError, http.client.HTTPException):
            if attempt == 49:
                raise
            time.sleep(0.1)
    for route, port in fixture["routes"].items():
        path = route + "/security-smoke?keep=a%20b&second=2"
        status, headers, body = request(path)
        assert status == 200, (path, status, body)
        assert json.loads(body) == {"port": port, "path": path}, (path, body)
        print("PASS proxy", route, "->", port)

    for path in ("/", "/?keep=1"):
        status, headers, body = request(path)
        expected = fixture["root"] + ("?keep=1" if "?" in path else "")
        assert status == 302 and headers["Location"] == expected, (status, headers)
        print("PASS root redirect", path)

    for host, target in fixture["redirects"].items():
        status, headers, body = request("/schedule?keep=1", host)
        assert status == 301 and headers["Location"] == target + "/schedule?keep=1", (host, status, headers)
        print("PASS host redirect", host)

    status, headers, body = request("/robots.txt")
    expected = Path(__file__).parent.parent.joinpath("www/robots.txt").read_bytes()
    assert status == 200 and body == expected, (status, body)
    assert request("/security-smoke-missing-file")[0] == 404
    print("PASS static content and missing-file response")
finally:
    for server in servers:
        server.shutdown()
