"""
Webhook receiver for testing - prints received payloads.
Usage: python webhook_receiver.py [port]
"""
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

PORT = int(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else 9000
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webhook_received.log")


def out(text: str):
    line = text + "\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)
    try:
        print(text, flush=True)
    except Exception:
        pass


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b""

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok": true}')

            ts = datetime.now().strftime("%H:%M:%S")
            sep = "=" * 60
            out(sep)
            out(f"[{ts}] POST {self.path}")

            try:
                parsed = json.loads(body)
                pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(pretty + "\n")
                print(pretty, flush=True)
            except Exception:
                out(body.decode("utf-8", errors="replace"))

            out(sep)

        except Exception as e:
            out(f"[ERROR] {e}")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    import socket, signal, sys

    # Kill any process already holding the port
    def _kill_port(port: int) -> None:
        try:
            import subprocess
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    if pid and pid != "0":
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True)
                        print(f"Killed PID {pid} on port {port}", flush=True)
        except Exception as e:
            print(f"[warn] Could not kill port {port}: {e}", flush=True)

    _kill_port(PORT)

    # SO_REUSEADDR so TIME_WAIT sockets don't block rebind
    HTTPServer.allow_reuse_address = True

    open(LOG_FILE, "w").close()
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)

    def _shutdown(sig, frame):
        print("\n[Receiver] Shutting down.", flush=True)
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    out(f"[Webhook Receiver] http://localhost:{PORT}")
    out(f"Log at: {LOG_FILE}")
    out("Waiting for payloads...")
    server.serve_forever()
