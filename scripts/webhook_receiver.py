"""
Webhook receiver de teste - printa payloads recebidos.
Uso: python webhook_receiver.py [porta]
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
        os.write(1, line.encode("utf-8", errors="replace"))
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
                # Arquivo: UTF-8 real. Terminal: ensure_ascii evita garble no PowerShell
                with open(LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n")
                try:
                    os.write(1, (json.dumps(parsed, indent=2, ensure_ascii=True) + "\n").encode("utf-8"))
                except Exception:
                    pass
            except Exception:
                out(body.decode("utf-8", errors="replace"))

            out(sep)

        except Exception as e:
            out(f"[ERRO] {e}")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    open(LOG_FILE, "w").close()
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    out(f"[Webhook Receiver] http://localhost:{PORT}")
    out(f"Log em: {LOG_FILE}")
    out("Aguardando payloads...")
    server.serve_forever()
