"""Bản chạy thử web local: UI gọi answer() trong agent.py qua HTTP.

Chạy bằng: python run.py   (macOS/Linux có thể là python3, Windows có thể là py)
Giữ `python run.py` là lệnh duy nhất để chạy bản chạy thử.
"""
import os
import json
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tracing
from agent import answer
from tools import load_product_dataset
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

for _stream in (sys.stdout, sys.stderr, sys.stdin):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
MAX_BODY_BYTES = 8 * 1024


def _catalog():
    data, products = load_product_dataset()
    listings = []
    for product in products:
        models = {}
        if product.get("phone_models"):
            models = {
                entry["phone_model"]: set(entry.get("case_variants", []))
                for entry in product["phone_models"]
            }
        else:
            for review in product.get("reviews", []):
                model = review.get("phone_model")
                variant = review.get("case_variant")
                if not isinstance(model, str) or not isinstance(variant, str):
                    continue
                models.setdefault(model, set()).add(variant)
        listings.append({
            "product_url": product["product_url"],
            "product_title": product.get("title") or product["product_url"],
            "phone_models": [
                {"phone_model": model, "case_variants": sorted(variants)}
                for model, variants in sorted(models.items())
            ],
        })
    return {
        "version": data.get("version", "unversioned"),
        "source_type": data.get("source_type", "fixture"),
        "source_label": data.get("source_label", "Dữ liệu demo giả lập"),
        "listings": listings,
    }


def _object_no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _valid_output(result):
    if not isinstance(result, dict) or set(result) != {"output"}:
        return False
    if not isinstance(result["output"], str):
        return False
    try:
        output = json.loads(result["output"])
    except (TypeError, ValueError):
        return False
    if not isinstance(output, dict) or output.get("status") not in {"ok", "needs_input", "error"}:
        return False
    if output["status"] == "ok":
        return isinstance(output.get("recommendation"), str) and isinstance(output.get("evidence"), list)
    return "recommendation" not in output


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 10

    def log_message(self, format, *args):
        pass

    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status, value):
        self._send(status, json.dumps(value, ensure_ascii=False))

    def _error(self, status, code, message):
        self._json(status, {"status": "error", "code": code, "message": message})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/analyze":
            self._method_not_allowed("POST")
            return
        if path == "/catalog":
            try:
                self._json(200, _catalog())
            except (OSError, ValueError, KeyError, TypeError):
                self._error(503, "CATALOG_UNAVAILABLE", "Chưa đọc được danh mục demo. Hãy thử lại.")
            return
        if path in {"/", "/index.html", "/styles.css", "/app.js"}:
            name = "index.html" if path in {"/", "/index.html"} else path[1:]
            try:
                with open(os.path.join(WEB_DIR, name), "rb") as source:
                    body = source.read()
            except OSError:
                self._error(404, "NOT_FOUND", "Không tìm thấy trang demo.")
                return
            content_type = "text/html; charset=utf-8" if name.endswith(".html") else (
                "text/css; charset=utf-8" if name.endswith(".css") else "text/javascript; charset=utf-8"
            )
            self._send(200, body, content_type)
            return
        self._error(404, "NOT_FOUND", "Đường dẫn không có trong bản demo.")

    def do_POST(self):
        path = urlsplit(self.path).path
        if path == "/catalog":
            self._method_not_allowed("GET")
            return
        if path != "/analyze":
            self._error(404, "NOT_FOUND", "Đường dẫn không có trong bản demo.")
            return
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            self._error(415, "INVALID_INPUT", "Gửi Content-Type: application/json.")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY_BYTES:
            if 0 < length <= MAX_BODY_BYTES + 1:
                self.rfile.read(length)
            self.close_connection = True
            self._error(413 if length > MAX_BODY_BYTES else 400, "INVALID_INPUT", "Gửi JSON gồm đúng ba trường của mẫu ốp.")
            return
        try:
            request = json.loads(self.rfile.read(length).decode("utf-8"), object_pairs_hook=_object_no_duplicates)
        except (UnicodeDecodeError, ValueError):
            self._error(400, "INVALID_INPUT", "Gửi JSON hợp lệ gồm product_url, phone_model và case_variant.")
            return
        if not isinstance(request, dict) or set(request) != {"product_url", "phone_model", "case_variant"}:
            self._error(400, "INVALID_INPUT", "Gửi JSON gồm đúng product_url, phone_model và case_variant.")
            return
        if not self.server.analysis_lock.acquire(blocking=False):
            self._error(503, "ANALYSIS_BUSY", "Đang có một lượt phân tích. Hãy thử lại sau khi lượt đó xong.")
            return
        try:
            tracing.begin("web")
            try:
                result = answer(json.dumps(request, ensure_ascii=False))
            finally:
                tracing.end()
        except Exception:
            self._error(200, "ANALYSIS_UNAVAILABLE", "Chưa xác thực được phân tích review; chưa đưa ra khuyến nghị.")
            return
        finally:
            self.server.analysis_lock.release()
        if not _valid_output(result):
            self._error(200, "ANALYSIS_UNAVAILABLE", "Phân tích chưa đủ dữ liệu để hiển thị; chưa đưa ra khuyến nghị.")
            return
        self._json(200, result)

    def _method_not_allowed(self, allow):
        self.send_response(405)
        self.send_header("Allow", allow)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_PUT(self):
        self._method_not_allowed("GET, POST")

    def do_DELETE(self):
        self._method_not_allowed("GET, POST")

    def do_PATCH(self):
        self._method_not_allowed("GET, POST")


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, _Handler)
        self.analysis_lock = threading.Lock()


def make_server(port=8765, host="127.0.0.1"):
    return _Server((host, port))


def main() -> int:
    try:
        server = make_server()
    except OSError as error:
        print("Không mở được cổng 8765: %s" % error)
        return 1
    print("BacTrung demo: http://127.0.0.1:8765/")
    print("Dữ liệu review giả lập; không truy cập Shopee. Dừng: Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng demo.")
    finally:
        server.server_close()
    return 0


run_app = main


if __name__ == "__main__":
    sys.exit(main())
