#!/usr/bin/env python3
"""Deterministic Stage A04 gates for SKU 01 live-demo-sku01 (static + HTTP contract)."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
REPORT_PATH = ROOT_DIR / "gates" / "gate_report.json"

AD_LAW_FORBIDDEN = [
    "国家级第一",
    "绝对第一",
    "100%包过",
    "包过验收",
    "全网最低",
    "国家级",
]


def http_call(
    url: str,
    *,
    method: str = "GET",
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    req_headers = dict(headers or {})
    data = None
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def run_static_gates() -> dict[str, Any]:
    html = (ROOT_DIR / "index.html").read_text(encoding="utf-8")
    css = (ROOT_DIR / "styles.css").read_text(encoding="utf-8")
    app_js = (ROOT_DIR / "app.js").read_text(encoding="utf-8")

    css_no_root = re.sub(r":root\s*\{[\s\S]*?\}", "", css, count=1)
    css_naked_hex = re.findall(r"#[0-9a-fA-F]{3,8}\b", css_no_root)
    html_inline_hex = re.findall(r'style\s*=\s*"[^"]*#[0-9a-fA-F]{3,8}', html)

    exposed_admin = re.findall(r"/admin\.html\b", html + "\n" + app_js, re.IGNORECASE)
    forbidden_hits = [w for w in AD_LAW_FORBIDDEN if w in html]
    section_ids = re.findall(r'data-section-id\s*=\s*"([^"]+)"', html)
    has_safe_area = bool(re.search(r"padding-right\s*:\s*96px", css))
    has_inline_favicon = "image/svg+xml" in html

    hero_img = ROOT_DIR / "assets" / "hero-vessel.jpg"
    craft_img = ROOT_DIR / "assets" / "craft-detail.jpg"
    hero_ok = hero_img.exists() and hero_img.stat().st_size > 10_000 and "hero-vessel.jpg" in html
    craft_ok = craft_img.exists() and craft_img.stat().st_size > 10_000 and "craft-detail.jpg" in html

    defects: list[dict[str, str]] = []
    if css_naked_hex or html_inline_hex:
        defects.append(
            {
                "gate": "naked_hex",
                "target": "styles.css / index.html",
                "issue": f"Non-:root naked HEX found: css={css_naked_hex}, html={html_inline_hex}",
                "fix_hint": "Replace all non-:root #HEX colors with var(--token) or rgba(...).",
            }
        )
    if exposed_admin:
        defects.append(
            {
                "gate": "exposed_admin",
                "target": "index.html / app.js",
                "issue": f"Public bundle references /admin.html: {exposed_admin}",
                "fix_hint": "Remove all /admin.html links from public HTML/JS.",
            }
        )
    if forbidden_hits:
        defects.append(
            {
                "gate": "ad_law_forbidden",
                "target": "index.html",
                "issue": f"Ad-law forbidden words found: {forbidden_hits}",
                "fix_hint": "Remove superlative/absolute marketing wording.",
            }
        )
    if len(section_ids) < 5:
        defects.append(
            {
                "gate": "section_locks",
                "target": "index.html",
                "issue": f"Expected >=5 data-section-id markers, got {len(section_ids)}: {section_ids}",
                "fix_hint": "Add data-section-id to header, hero, story, sessions, booking-form, faq, footer.",
            }
        )
    if not has_safe_area:
        defects.append(
            {
                "gate": "miniprogram_safe_area",
                "target": "styles.css",
                "issue": "Missing MiniProgram capsule clearance `padding-right: 96px`",
                "fix_hint": "Set padding-right: 96px on .site-header in @media (max-width: 640px).",
            }
        )
    if not has_inline_favicon:
        defects.append(
            {
                "gate": "inline_favicon",
                "target": "index.html",
                "issue": "Missing inline data:image/svg+xml favicon link",
                "fix_hint": "Add <link rel='icon' type='image/svg+xml' href='data:image/svg+xml,...' />.",
            }
        )
    if not (hero_ok and craft_ok):
        defects.append(
            {
                "gate": "studio_assets",
                "target": "index.html / assets/",
                "issue": f"Studio photos missing or unreferenced (hero_ok={hero_ok}, craft_ok={craft_ok})",
                "fix_hint": "Render real assets/hero-vessel.jpg and assets/craft-detail.jpg in index.html.",
            }
        )

    return {
        "pass": len(defects) == 0,
        "naked_hex_count": len(css_naked_hex) + len(html_inline_hex),
        "exposed_admin_count": len(exposed_admin),
        "forbidden_words": forbidden_hits,
        "section_ids": section_ids,
        "has_safe_area": has_safe_area,
        "has_inline_favicon": has_inline_favicon,
        "hero_asset_ok": hero_ok,
        "craft_asset_ok": craft_ok,
        "defects": defects,
    }


def run_http_gates(base_url: str) -> dict[str, Any]:
    defects: list[dict[str, str]] = []
    checks: dict[str, Any] = {}

    s_home, _ = http_call(f"{base_url}/")
    s_health, b_health = http_call(f"{base_url}/api/health")
    s_hero, _ = http_call(f"{base_url}/assets/hero-vessel.jpg")
    s_admin, _ = http_call(f"{base_url}/admin.html")
    s_internal_noauth, _ = http_call(f"{base_url}/api/internal/leads")

    test_date = (date.today() + timedelta(days=2)).isoformat()
    lead_payload = {
        "name": "门禁测试访客",
        "phone": "13800138999",
        "date": test_date,
        "session": "午后拉坯体验",
        "guests": 2,
        "notes": "自动化门禁双提交防重验证",
        "utm_source": "gate_smoke",
    }
    s_post1, b_post1 = http_call(f"{base_url}/api/leads", method="POST", json_body=lead_payload)
    s_post2, b_post2 = http_call(f"{base_url}/api/leads", method="POST", json_body=lead_payload)

    # Clean up temporary gate_smoke entry if present in data/layer0-customers.json
    db_path = ROOT_DIR / "data" / "layer0-customers.json"
    db_persisted = False
    if db_path.exists():
        try:
            records = json.loads(db_path.read_text(encoding="utf-8"))
            db_persisted = any(
                r.get("phone") == "13800138999" and r.get("date") == test_date
                for r in records
                if isinstance(r, dict)
            )
            cleaned = [
                r for r in records
                if not (isinstance(r, dict) and r.get("utm_source") == "gate_smoke" and r.get("phone") == "13800138999")
            ]
            db_path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    checks.update(
        {
            "home_status": s_home,
            "health_status": s_health,
            "health_body": b_health[:200],
            "hero_asset_status": s_hero,
            "admin_html_status": s_admin,
            "internal_noauth_status": s_internal_noauth,
            "post_1_status": s_post1,
            "post_1_body": b_post1[:200],
            "post_2_status": s_post2,
            "post_2_body": b_post2[:200],
            "db_persisted": db_persisted,
        }
    )

    if s_home != 200 or s_health != 200 or s_hero != 200:
        defects.append(
            {
                "gate": "http_serving",
                "target": "server.py",
                "issue": f"Unexpected static/health status: home={s_home}, health={s_health}, hero={s_hero}",
                "fix_hint": "Ensure server.py serves /, /api/health, and /assets/hero-vessel.jpg with HTTP 200.",
            }
        )
    if s_admin != 404:
        defects.append(
            {
                "gate": "admin_isolation",
                "target": "server.py",
                "issue": f"GET /admin.html returned {s_admin}, expected 404",
                "fix_hint": "Return HTTP 404 explicitly for /admin.html.",
            }
        )
    if s_internal_noauth != 401:
        defects.append(
            {
                "gate": "internal_auth",
                "target": "server.py",
                "issue": f"GET /api/internal/leads without token returned {s_internal_noauth}, expected 401",
                "fix_hint": "Require X-Admin-Token header and return HTTP 401 when missing/invalid.",
            }
        )
    if not (s_post1 == 201 and s_post2 == 409 and db_persisted):
        defects.append(
            {
                "gate": "lead_dedup_409",
                "target": "server.py",
                "issue": f"Dedup contract failed: 1st={s_post1}, 2nd={s_post2}, db_persisted={db_persisted}",
                "fix_hint": "Persist new (phone, date) to data/layer0-customers.json with 201 and reject duplicate with 409.",
            }
        )

    return {"pass": len(defects) == 0, "checks": checks, "defects": defects}


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8770"
    skip_http = "--static-only" in sys.argv

    static_res = run_static_gates()
    http_res = {"pass": True, "skipped": True, "defects": []} if skip_http else run_http_gates(base_url)

    overall_pass = bool(static_res["pass"] and http_res["pass"])
    report = {
        "pass": overall_pass,
        "base_url": base_url,
        "static": static_res,
        "http": http_res,
        "defects": static_res["defects"] + http_res["defects"],
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if overall_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
