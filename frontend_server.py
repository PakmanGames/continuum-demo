"""
Serves the static frontend and proxies /api/* to the backend service.

The page used to call http://localhost:5000 directly, which only works when the
backend happens to be published on that exact port on the viewer's machine —
not under a compose file that maps it to 5001, and not on a Mac where AirPlay
sits on 5000. Proxying through this server means the page works on any
published port, with no CORS and no host baked into the JavaScript.
"""
import os
import urllib.error
import urllib.request

from flask import Flask, Response, request, send_from_directory

app = Flask(__name__)

# The backend's address *inside* the compose network.
BACKEND_URL = os.getenv("BACKEND_URL", "http://demo-backend:5000").rstrip("/")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/<path:path>", methods=["GET", "POST"])
def proxy(path):
    url = f"{BACKEND_URL}/{path}"
    if request.query_string:
        url += "?" + request.query_string.decode()
    req = urllib.request.Request(
        url,
        data=request.get_data() if request.method == "POST" else None,
        method=request.method,
        headers={"Content-Type": request.headers.get("Content-Type", "application/json")},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as upstream:
            return Response(upstream.read(), status=upstream.status,
                            content_type=upstream.headers.get("Content-Type", "application/json"))
    except urllib.error.HTTPError as e:
        return Response(e.read(), status=e.code,
                        content_type=e.headers.get("Content-Type", "application/json"))
    except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
        # The backend is down — after /crash, that is the expected answer.
        return Response(f'{{"error": "backend unreachable: {e}"}}', status=502,
                        content_type="application/json")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
