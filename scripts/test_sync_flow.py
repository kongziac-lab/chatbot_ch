#!/usr/bin/env python3
"""FAQ 벡터 동기화 간단 테스트.

실행 예:
  python3 scripts/test_sync_flow.py --base-url http://localhost:8000 --full-sync
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--full-sync", action="store_true")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    sync_url = f"{base}/api/v1/faq/sync-vector-db"
    params = {"full_sync": "true"} if args.full_sync else {}

    try:
        with httpx.Client(timeout=60.0) as client:
            health = client.get(f"{base}/health")
            print("health:", health.status_code)
            if health.status_code != 200:
                print("서버 헬스체크 실패")
                return 2

            resp = client.post(sync_url, params=params)
            print("sync status:", resp.status_code)
            try:
                payload = resp.json()
            except Exception:
                payload = {"raw": resp.text}

            print(json.dumps(payload, ensure_ascii=False, indent=2))

            if resp.status_code >= 400:
                return 1

        return 0
    except Exception as exc:
        print(f"요청 실패: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
