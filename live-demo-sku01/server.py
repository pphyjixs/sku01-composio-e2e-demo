#!/usr/bin/env python3
"""Stdlib HTTP server for SKU 01 (QINGYOU STUDIO) live prototype."""

from __future__ import annotations

import hmac
import json
import os
import re
import threading
import uuid
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "layer0-customers.json"
ASSETS_DIR = BASE_DIR / "assets"

ALLOWED_SESSIONS = {
    "午后拉坯体验",
    "窑变器皿鉴赏",
    "私享选品",
}
PHONE_RE = re.compile(r"^1\d{10}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

STATIC_FILES: dict[str, tuple[Path, str]] = {
    "/": (BASE_DIR / "index.html", "text/html; charset=utf-8"),
    "/index.html": (BASE_DIR / "index.html", "text/html; charset=utf-8"),
    "/styles.css": (BASE_DIR / "styles.css", "text/css; charset=utf-8"),
    "/app.js": (BASE_DIR / "app.js", "application/javascript; charset=utf-8"),
}

DB_LOCK = threading.Lock()


def _ensure_db_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        DB_PATH.write_text("[]\n", encoding="utf-8")


def _load_leads_unlocked() -> list[dict[str, Any]]:
    _ensure_db_file()
    raw = DB_PATH.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    parsed = json.loads(raw)
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]


def _save_leads_unlocked(records: list[dict[str, Any]]) -> None:
    _ensure_db_file()
    tmp_path = DB_PATH.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(DB_PATH)


def _get_admin_token() -> str:
    return os.environ.get("SKU1_ADMIN_TOKEN", "qingyou-local-dev-token")


class QingyouHandler(BaseHTTPRequestHandler):
    server_version = "QingyouSKU01/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        # Keep console output clean and structured
        sys_msg = format % args
        print(f"[{self.log_date_time_string()}] {self.address_string()} {sys_msg}")

    def _send_json(self, status_code: int, payload: Any) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: Path, content_type: str) -> None:
        if not file_path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        data = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if content_type.startswith("image/"):
            self.send_header("Cache-Control", "public, max-age=3600")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _read_json_body(self) -> tuple[dict[str, Any] | None, str | None]:
        raw_len = self.headers.get("Content-Length")
        if raw_len is None:
            return None, "Missing Content-Length header"
        try:
            length = int(raw_len)
        except ValueError:
            return None, "Invalid Content-Length header"
        if length <= 0 or length > 65536:
            return None, "Request body size out of bounds"
        raw_bytes = self.rfile.read(length)
        try:
            parsed = json.loads(raw_bytes.decode("utf-8"))
        except Exception:
            return None, "Malformed JSON payload"
        if not isinstance(parsed, dict):
            return None, "JSON payload must be an object"
        return parsed, None

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)

        if path in ("/admin.html", "/admin", "/admin/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        if path == "/api/health":
            self._send_json(
                HTTPStatus.OK,
                {"ok": True, "service": "sku01-qingyou-live-demo"},
            )
            return

        if path == "/api/internal/leads":
            provided = self.headers.get("X-Admin-Token", "")
            expected = _get_admin_token()
            if not provided or not hmac.compare_digest(provided, expected):
                self._send_json(
                    HTTPStatus.UNAUTHORIZED,
                    {"ok": False, "error": "Unauthorized"},
                )
                return
            with DB_LOCK:
                leads = _load_leads_unlocked()
            self._send_json(
                HTTPStatus.OK,
                {"ok": True, "count": len(leads), "leads": leads},
            )
            return

        if path in STATIC_FILES:
            file_path, content_type = STATIC_FILES[path]
            self._send_file(file_path, content_type)
            return

        if path.startswith("/assets/"):
            rel_name = path[len("/assets/"):]
            if "/" in rel_name or "\\" in rel_name or not rel_name.lower().endswith(".jpg"):
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            candidate = (ASSETS_DIR / rel_name).resolve()
            if candidate.parent != ASSETS_DIR.resolve():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            self._send_file(candidate, "image/jpeg")
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path != "/api/leads":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        body, err = self._read_json_body()
        if err or body is None:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "invalid_request", "message": err or "Invalid body"},
            )
            return

        name = str(body.get("name", "")).strip()
        phone = str(body.get("phone", "")).strip()
        booking_date = str(body.get("date", "")).strip()
        session = str(body.get("session", "")).strip()
        notes = str(body.get("notes", "")).strip()[:240]
        utm_source = str(body.get("utm_source", "direct")).strip()[:64] or "direct"

        raw_guests = body.get("guests", 1)
        try:
            guests = int(raw_guests)
        except (TypeError, ValueError):
            guests = 1
        guests = max(1, min(4, guests))

        if not name:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": "invalid_name", "message": "请填写访客姓名。"},
            )
            return

        if not PHONE_RE.match(phone):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "invalid_phone",
                    "message": "请填写 11 位有效手机号（以 1 开头）。",
                },
            )
            return

        if not DATE_RE.match(booking_date):
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "invalid_date",
                    "message": "预约日期格式需为 YYYY-MM-DD。",
                },
            )
            return

        try:
            date.fromisoformat(booking_date)
        except ValueError:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "invalid_date",
                    "message": "请选择有效的日历日期。",
                },
            )
            return

        if not session or session not in ALLOWED_SESSIONS:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "ok": False,
                    "error": "invalid_session",
                    "message": "请选择工坊开放的预约场次。",
                },
            )
            return

        with DB_LOCK:
            records = _load_leads_unlocked()
            is_duplicate = any(
                rec.get("phone") == phone and rec.get("date") == booking_date
                for rec in records
            )
            if is_duplicate:
                self._send_json(
                    HTTPStatus.CONFLICT,
                    {
                        "ok": False,
                        "status": 409,
                        "error": "duplicate_booking",
                        "message": f"手机号 {phone} 在 {booking_date} 已存在预约记录，同一手机号同一天禁止重复预约（HTTP 409）。",
                    },
                )
                return

            lead_id = f"QY-{uuid.uuid4().hex[:8].upper()}"
            lead_record = {
                "id": lead_id,
                "name": name,
                "phone": phone,
                "date": booking_date,
                "session": session,
                "guests": guests,
                "notes": notes,
                "utm_source": utm_source,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            records.append(lead_record)
            _save_leads_unlocked(records)

        self._send_json(
            HTTPStatus.CREATED,
            {
                "ok": True,
                "status": 201,
                "id": lead_id,
                "message": "预约登记成功。",
                "lead": lead_record,
            },
        )


def run_server() -> None:
    _ensure_db_file()
    host = "127.0.0.1"
    port = int(os.environ.get("PORT", 8770))
    httpd = ThreadingHTTPServer((host, port), QingyouHandler)
    print(f"SKU 01 server listening on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
