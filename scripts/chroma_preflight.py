#!/usr/bin/env python3
"""ChromaDB 사전 점검.

실행:
  python3 scripts/chroma_preflight.py
"""

from __future__ import annotations

import json
from pathlib import Path

from app.config import settings
from app.services.rag_engine import vector_store


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    persist_dir = settings.chroma_dir
    try:
        persist_dir.mkdir(parents=True, exist_ok=True)
        checks.append(("persist_dir_exists", persist_dir.exists(), str(persist_dir)))
    except Exception as exc:
        checks.append(("persist_dir_exists", False, f"디렉터리 생성 실패: {exc}"))

    try:
        probe = persist_dir / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        checks.append(("persist_dir_writable", True, str(persist_dir)))
    except Exception as exc:
        checks.append(("persist_dir_writable", False, f"쓰기 실패: {exc}"))

    try:
        snap = vector_store.health_snapshot()
        checks.append(("vector_store_access", True, json.dumps(snap, ensure_ascii=False)))
    except Exception as exc:
        checks.append(("vector_store_access", False, f"접근 실패: {exc}"))

    failed = [c for c in checks if not c[1]]

    print("=== Chroma Preflight ===")
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")

    if failed:
        print("\n결론: FAIL")
        return 1

    print("\n결론: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
