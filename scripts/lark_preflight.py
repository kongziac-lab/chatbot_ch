#!/usr/bin/env python3
"""Lark Base 연동 사전 점검.

실행:
  python3 scripts/lark_preflight.py
"""

from __future__ import annotations

import json
import sys

from app.config import settings
from app.services.sheet_manager import faq_sheet_manager


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    required = {
        "LARK_APP_ID": settings.lark_app_id,
        "LARK_APP_SECRET": settings.lark_app_secret,
        "LARK_BASE_APP_TOKEN": settings.lark_base_app_token,
        "LARK_FAQ_TABLE_ID": settings.lark_faq_table_id,
    }

    for key, value in required.items():
        checks.append((key, bool((value or "").strip()), "필수 환경변수"))

    missing_env = [k for k, ok, _ in checks if not ok]
    if missing_env:
        print("[FAIL] 필수 환경변수 누락:", ", ".join(missing_env))
        return 2

    try:
        token = faq_sheet_manager._get_tenant_access_token()  # noqa: SLF001
        checks.append(("tenant_access_token", bool(token), "토큰 발급"))
    except Exception as exc:
        checks.append(("tenant_access_token", False, f"토큰 발급 실패: {exc}"))

    field_result = {"ok": False, "missing_fields": ["(field check failed)"]}
    try:
        field_result = faq_sheet_manager.check_faq_field_compatibility()
        checks.append(("faq_table_fields", field_result["ok"], json.dumps(field_result, ensure_ascii=False)))
    except Exception as exc:
        checks.append(("faq_table_fields", False, f"필드 조회 실패: {exc}"))

    row_count_ok = False
    row_count_msg = ""
    try:
        rows = faq_sheet_manager.get_published_faqs()
        row_count_ok = True
        row_count_msg = f"게시중 FAQ {len(rows)}건"
    except Exception as exc:
        row_count_msg = f"FAQ 조회 실패: {exc}"
    checks.append(("faq_read", row_count_ok, row_count_msg))

    failed = [c for c in checks if not c[1]]

    print("=== Lark Preflight ===")
    for name, ok, detail in checks:
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}: {detail}")

    if failed:
        print("\n결론: FAIL")
        return 1

    print("\n결론: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
