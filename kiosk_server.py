import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
KIOSK_FILE = BASE_DIR / "kiosk_demo.html"
CLONE_FILE = BASE_DIR / "project_clone.html"
GROUP_CLONE_FILE = BASE_DIR / "project_clone_group.html"
START_PORT = 8765
PORT_ATTEMPTS = 10
DEFAULT_OPEN_PATH = "/group-clone"
SERVER_STARTED_AT = time.time()
MODES = {
    "media": "MEDIA MODE",
    "navigation": "NAVIGATION MODE",
    "nav": "NAVIGATION MODE",
    "touch": "TOUCH MODE",
}
CURRENT_MODE = "SYSTEM LOCKED | TOUCH MODE selected"


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def local_url(port, path=DEFAULT_OPEN_PATH):
    return f"http://127.0.0.1:{port}{path}"


def should_auto_open_browser():
    return os.environ.get("JARVIS_OPEN_BROWSER", "1").lower() not in ("0", "false", "no")


def open_browser_later(port):
    if not should_auto_open_browser():
        return

    threading.Timer(0.8, lambda: webbrowser.open(local_url(port))).start()


def send_bytes(handler, body, content_type, status=200):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def presentation_status():
    return {
        "app": "JARVIS AI Vision Controller",
        "status": "PRESENTATION SERVER",
        "mode": CURRENT_MODE,
        "locked": True,
        "fps": "--",
        "last_action": "Standalone clone server ready",
        "hand_detected": False,
        "dashboard": "standalone",
        "uptime_seconds": int(time.time() - SERVER_STARTED_AT),
        "current_gesture": "Presentation demo",
        "air_click": "Demo ready",
        "virtual_touch": "Demo ready",
        "control_quality": "Presentation mode",
        "action_count": 0,
        "last_capture": "None",
        "face_auth": "Demo mode",
        "hand_auth": "Demo mode",
        "auth_stage": "Full AI controller available from app.py",
        "auth_engine": "Standalone server",
        "eye_auth": "Demo mode",
        "voice_assistant": "Open app.py for live voice sync",
        "last_voice_command": "None",
        "voice_apps": 0,
        "voice_mic": "Standalone demo",
        "voice_feedback": "Presentation ready",
        "guardian_status": "Standby",
        "guardian_event": "None",
        "guardian_time": "None",
        "adaptive_pinch": "--",
        "hand_scale": "--",
    }


def dashboard_page():
    data = presentation_status()
    rows = "".join(
        f"<div class=\"item\"><span>{key}</span><strong>{value}</strong></div>"
        for key, value in (
            ("Status", data["status"]),
            ("Mode", data["mode"]),
            ("Voice", data["voice_assistant"]),
            ("Auth", data["auth_stage"]),
            ("Gesture", data["current_gesture"]),
            ("Uptime", f"{data['uptime_seconds']}s"),
        )
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JARVIS Presentation Dashboard</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }}
    body {{ margin: 0; min-height: 100vh; background: #101317; color: #f8fafc; display: grid; place-items: center; }}
    main {{ width: min(980px, calc(100vw - 32px)); padding: 36px 0; }}
    h1 {{ margin: 0; font-size: clamp(38px, 7vw, 82px); line-height: 1; }}
    p {{ color: #a8b4c2; line-height: 1.55; max-width: 760px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 22px; }}
    .item {{ border: 1px solid #34414f; border-radius: 8px; padding: 16px; background: #171d24; }}
    .item span {{ color: #9fb0c0; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .item strong {{ display: block; margin-top: 10px; font-size: 20px; overflow-wrap: anywhere; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 24px; }}
    a {{ border: 1px solid #34414f; border-radius: 8px; padding: 10px 12px; color: #e7eef5; text-decoration: none; background: #161d24; font-weight: 800; }}
    a:hover, a:focus-visible {{ outline: none; border-color: #79d5f2; background: #1e2a34; }}
    @media (max-width: 760px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>Presentation Dashboard</h1>
    <p>This lightweight dashboard is served by <code>kiosk_server.py</code>. Run <code>python app.py</code> when you need live camera, gesture, voice, and Guardian telemetry.</p>
    <section class="grid">{rows}</section>
    <div class="actions">
      <a href="/group-clone">Group Clone</a>
      <a href="/clone">Project Clone</a>
      <a href="/kiosk">Kiosk Demo</a>
      <a href="/guardian">Guardian SOS</a>
    </div>
  </main>
</body>
</html>"""


def guardian_page():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Guardian SOS</title>
  <style>
    :root { color-scheme: dark; font-family: Inter, Segoe UI, Arial, sans-serif; }
    body { margin: 0; min-height: 100vh; background: #101317; color: #f8fafc; display: grid; place-items: center; }
    main { width: min(940px, calc(100vw - 32px)); padding: 36px 0; }
    h1 { margin: 0 0 12px; font-size: clamp(40px, 8vw, 92px); color: #73d99f; line-height: 1; }
    .status { border: 2px solid #73d99f; border-radius: 8px; padding: 22px; background: #171c22; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-top: 18px; }
    .item { border: 1px solid #2d3743; border-radius: 8px; padding: 16px; background: #121820; }
    .label { color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: .08em; }
    .value { margin-top: 8px; font-size: 22px; overflow-wrap: anywhere; }
    a { color: #79d5f2; }
    @media (max-width: 760px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <h1>Guardian Standby</h1>
    <div class="status">
      <div class="label">Standalone Presentation Mode</div>
      <div class="value">Run <code>python app.py</code> for live SOS activation, screenshots, voice events, and full telemetry.</div>
    </div>
    <section class="grid">
      <div class="item"><div class="label">Status</div><div class="value">Standby</div></div>
      <div class="item"><div class="label">Voice Trigger</div><div class="value">Demo page ready</div></div>
      <div class="item"><div class="label">Capture</div><div class="value">Full app required</div></div>
      <div class="item"><div class="label">Back</div><div class="value"><a href="/group-clone">Group Clone</a></div></div>
    </section>
  </main>
</body>
</html>"""


class KioskHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global CURRENT_MODE
        request_path = urlparse(self.path).path

        if request_path == "/dashboard":
            body = dashboard_page().encode("utf-8")
            send_bytes(self, body, "text/html; charset=utf-8")
            return

        if request_path in ("/", "/clone", "/project_clone.html"):
            if not CLONE_FILE.exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"project_clone.html not found")
                return

            send_bytes(self, CLONE_FILE.read_bytes(), "text/html; charset=utf-8")
            return

        if request_path in ("/group-clone", "/project_clone_group.html"):
            if not GROUP_CLONE_FILE.exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"project_clone_group.html not found")
                return

            send_bytes(self, GROUP_CLONE_FILE.read_bytes(), "text/html; charset=utf-8")
            return

        if request_path in ("/guardian", "/guardian.html"):
            body = guardian_page().encode("utf-8")
            send_bytes(self, body, "text/html; charset=utf-8")
            return

        if request_path == "/api/status":
            body = json.dumps(presentation_status()).encode("utf-8")
            send_bytes(self, body, "application/json")
            return

        if request_path == "/api/mode":
            mode_text = parse_qs(urlparse(self.path).query).get("mode", [""])[0].lower()
            selected_mode = MODES.get(mode_text)
            if selected_mode is None:
                payload = {"ok": False, "message": "Mode not found"}
                status = 400
            else:
                CURRENT_MODE = f"SYSTEM LOCKED | {selected_mode} selected"
                payload = {"ok": True, "message": f"Standalone demo mode set to {selected_mode}", "mode": CURRENT_MODE}
                status = 200
            body = json.dumps(payload).encode("utf-8")
            send_bytes(self, body, "application/json", status=status)
            return

        if request_path in ("/kiosk", "/kiosk_demo.html"):
            if not KIOSK_FILE.exists():
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"kiosk_demo.html not found")
                return

            send_bytes(self, KIOSK_FILE.read_bytes(), "text/html; charset=utf-8")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def run_server():
    port = START_PORT
    for _ in range(PORT_ATTEMPTS):
        try:
            server = ReusableThreadingHTTPServer(("127.0.0.1", port), KioskHandler)
            print("\nJARVIS project presentation server is running.")
            print(f"Project clone link: {local_url(port, '/clone')}")
            print(f"Group project clone link: {local_url(port, '/group-clone')}")
            print(f"Presentation dashboard: {local_url(port, '/dashboard')}")
            print(f"Touchless kiosk demo: {local_url(port, '/kiosk')}")
            open_browser_later(port)
            print("Press Ctrl+C in this terminal to stop.\n")
            server.serve_forever()
            return
        except OSError:
            port += 1

    print("Could not start kiosk server. Ports 8765-8774 may be busy.")


if __name__ == "__main__":
    run_server()
