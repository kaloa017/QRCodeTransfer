"""QR Stream LAN server.

Serves qrstream.html over HTTPS on your local network so a phone can open it
and use the camera (browsers only allow camera access on HTTPS or localhost).

note: this is mainly a testing environment. It's not recommended to use this 
Python file unless you are developing on it. You may also encounter missing
browser certificates.

Run:  pip install -r requirements.txt && python app.py
"""
import os
import socket
import urllib.request

from flask import Flask, Response, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.join(HERE, "lib")
PORT = 8443

# Scripts the page needs. Downloaded once, then served locally so the
# phone doesn't need internet access (works on an offline hotspot/router).
LIBS = {
    "qrcode.js": "https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js",
    "jsQR.js": "https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js",
    "lame.min.js": "https://cdn.jsdelivr.net/npm/lamejs@1.2.1/lame.min.js",
}

app = Flask(__name__)


def fetch_libs():
    os.makedirs(LIB_DIR, exist_ok=True)
    for name, url in LIBS.items():
        path = os.path.join(LIB_DIR, name)
        if not os.path.exists(path):
            try:
                print(f"Downloading {name} ...")
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                print(f"  could not download {name} ({e}); page will fall back to the CDN")


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))  # no packets are actually sent
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def find_page():
    """Use qrstream.html, or any similarly named .html file next to app.py
    (browsers sometimes rename downloads, e.g. 'qrstream (1).html' or 'qrstream')."""
    exact = os.path.join(HERE, "qrstream.html")
    if os.path.exists(exact):
        return exact
    names = sorted(os.listdir(HERE))
    for n in names:
        if n.lower().startswith("qrstream") and os.path.isfile(os.path.join(HERE, n)):
            return os.path.join(HERE, n)
    for n in names:
        if n.lower().endswith((".html", ".htm")):
            return os.path.join(HERE, n)
    return None


@app.route("/")
def index():
    page = find_page()
    if not page:
        return Response(
            f"qrstream.html was not found in {HERE}\n"
            "Download it again and put it in the same folder as app.py.",
            status=404, mimetype="text/plain")
    with open(page, encoding="utf-8") as f:
        html = f.read()
    for name, url in LIBS.items():
        if os.path.exists(os.path.join(LIB_DIR, name)):
            html = html.replace(url, f"/lib/{name}")
    return Response(html, mimetype="text/html")


@app.route("/lib/<path:name>")
def lib(name):
    return send_from_directory(LIB_DIR, name)


if __name__ == "__main__":
    fetch_libs()
    ip = lan_ip()
    page = find_page()
    print(f"Serving page: {page}" if page else f"WARNING: no qrstream.html found in {HERE}")
    print("\nQR Stream is running.")
    print(f"  On this computer:  https://localhost:{PORT}")
    print(f"  On your phone:     https://{ip}:{PORT}   (same Wi-Fi)")
    print("  Your browser will warn about the certificate: choose Advanced > Proceed.\n")
    app.run(host="0.0.0.0", port=PORT, ssl_context="adhoc")