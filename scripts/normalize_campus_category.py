#!/usr/bin/env python3
"""Lark Base 카테고리 정규화 도구.

중분류가 '캠퍼스'인데 대분류가 '생활/숙박'이 아닌 FAQ를 찾아 정규화합니다.

실행 예:
  python3 scripts/normalize_campus_category.py
  python3 scripts/normalize_campus_category.py --apply
"""

from __future__ import annotations

import argparse
import json

from app.services.sheet_manager import faq_sheet_manager


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="실제 업데이트 수행 (기본은 dry-run)",
    )
    args = parser.parse_args()

    try:
        result = faq_sheet_manager.normalize_campus_categories(apply=args.apply)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
