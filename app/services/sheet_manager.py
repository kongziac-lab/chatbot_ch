"""Lark Base FAQ 연동 서비스.

기존 모듈명을 유지하여 기존 import (`sheet_manager`) 호환성을 보장합니다.
FAQ 자동 생성 파이프라인 없이, Lark Base 수동 운영을 전제로 합니다.
"""

from __future__ import annotations

import threading
import time
import uuid
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from loguru import logger

from app.config import settings

CACHE_TTL = settings.cache_ttl_seconds
PUBLISHED_STATUS = "게시중"
HEADER_ROW = [
    "고유번호", "카테고리(대분류)", "카테고리(중분류)",
    "질문(한국어)", "답변(한국어)", "질문(중국어)", "답변(중국어)",
    "출처", "상태", "생성부서", "적용범위", "생성일", "수정일",
    "우선순위", "조회수", "도움됨비율",
]
REQUIRED_FAQ_FIELDS = set(HEADER_ROW)


@dataclass
class _CacheEntry:
    data: Any
    expires_at: float = field(default_factory=lambda: time.monotonic() + CACHE_TTL)

    def is_valid(self) -> bool:
        return time.monotonic() < self.expires_at


class FAQSheetManager:
    """Lark Base FAQ 매니저 (Google Sheets 대체)."""

    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}
        self._view_buffer: dict[str, int] = {}
        self._view_lock = threading.Lock()
        self._http = httpx.Client(timeout=20.0)
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _invalidate_cache(self) -> None:
        self._cache.pop("published_faqs", None)

    def _require_lark_env(self) -> None:
        missing = []
        if not settings.lark_app_id:
            missing.append("LARK_APP_ID")
        if not settings.lark_app_secret:
            missing.append("LARK_APP_SECRET")
        if not settings.lark_base_app_token:
            missing.append("LARK_BASE_APP_TOKEN")
        if not settings.lark_faq_table_id:
            missing.append("LARK_FAQ_TABLE_ID")
        if missing:
            raise RuntimeError(f"Lark Base 환경변수 누락: {', '.join(missing)}")

    def _get_tenant_access_token(self) -> str:
        now = time.monotonic()
        if self._token and now < self._token_expires_at:
            return self._token

        self._require_lark_env()
        url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
        payload = self._request_json(
            "POST",
            url,
            json={"app_id": settings.lark_app_id, "app_secret": settings.lark_app_secret},
        )

        token = payload["tenant_access_token"]
        expire = int(payload.get("expire", 7200))
        self._token = token
        self._token_expires_at = now + max(expire - 60, 60)
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_tenant_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _request_json(self, method: str, url: str, **kwargs) -> dict[str, Any]:
        """Lark API 호출 공통 처리.

        실패 시 HTTP status + Lark code/msg를 포함한 상세 예외를 발생시킵니다.
        """
        resp = self._http.request(method, url, **kwargs)
        raw_text = resp.text
        try:
            payload: dict[str, Any] = resp.json()
        except Exception:
            payload = {}

        lark_code = payload.get("code")
        lark_msg = payload.get("msg")
        if resp.status_code >= 400 or (lark_code is not None and lark_code != 0):
            raise RuntimeError(
                "Lark API 호출 실패 | "
                f"status={resp.status_code} | code={lark_code} | msg={lark_msg} | "
                f"url={url} | body={raw_text[:500]}"
            )
        return payload

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        try:
            return int(str(value or default).strip())
        except Exception:
            return default

    @classmethod
    def _field_text(cls, value: Any) -> str:
        """Lark Base 필드값을 텍스트로 변환 (하이퍼링크는 Markdown 링크로 보존)."""
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float, bool)):
            return str(value).strip()
        if isinstance(value, dict):
            # 링크 메타데이터 보존
            text_part = cls._field_text(
                value.get("text")
                or value.get("name")
                or value.get("value")
                or value.get("label")
                or ""
            )
            link_data = value.get("link") or value.get("url") or value.get("href")
            link_url = ""
            if isinstance(link_data, dict):
                link_url = str(
                    link_data.get("url")
                    or link_data.get("href")
                    or link_data.get("link")
                    or ""
                ).strip()
            elif isinstance(link_data, str):
                link_url = link_data.strip()

            if link_url:
                link_label = text_part or link_url
                return f"[{link_label}]({link_url})"

            for key in ("text", "name", "value", "label"):
                if key in value and value[key] is not None:
                    return cls._field_text(value[key])
            return str(value).strip()
        if isinstance(value, list):
            parts = [cls._field_text(v) for v in value]
            parts = [p for p in parts if p]
            return " ".join(parts)
        return str(value).strip()

    @staticmethod
    def _normalize_match_text(value: Any) -> str:
        text = unicodedata.normalize("NFKC", str(value or ""))
        text = text.strip().lower()
        text = text.replace("／", "/")
        return "".join(text.split())

    @classmethod
    def _is_published_status(cls, value: Any) -> bool:
        normalized = cls._normalize_match_text(value)
        return normalized in {"게시중", "게시", "published", "공개", "active", "on"}

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _list_records(self, table_id: str) -> list[dict]:
        items: list[dict] = []
        page_token: str | None = None

        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            url = (
                f"https://open.larksuite.com/open-apis/bitable/v1/apps/"
                f"{settings.lark_base_app_token}/tables/{table_id}/records"
            )
            payload = self._request_json("GET", url, headers=self._headers(), params=params)

            data = payload.get("data", {})
            items.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")

        return items

    def _list_fields(self, table_id: str) -> list[dict]:
        items: list[dict] = []
        page_token: str | None = None

        while True:
            params = {"page_size": 500}
            if page_token:
                params["page_token"] = page_token

            url = (
                f"https://open.larksuite.com/open-apis/bitable/v1/apps/"
                f"{settings.lark_base_app_token}/tables/{table_id}/fields"
            )
            payload = self._request_json("GET", url, headers=self._headers(), params=params)

            data = payload.get("data", {})
            items.extend(data.get("items", []))
            if not data.get("has_more"):
                break
            page_token = data.get("page_token")

        return items

    def _create_record(self, table_id: str, fields: dict[str, Any]) -> str:
        url = (
            f"https://open.larksuite.com/open-apis/bitable/v1/apps/"
            f"{settings.lark_base_app_token}/tables/{table_id}/records"
        )
        payload = self._request_json("POST", url, headers=self._headers(), json={"fields": fields})
        return payload["data"]["record"]["record_id"]

    def _update_record(self, table_id: str, record_id: str, fields: dict[str, Any]) -> None:
        url = (
            f"https://open.larksuite.com/open-apis/bitable/v1/apps/"
            f"{settings.lark_base_app_token}/tables/{table_id}/records/{record_id}"
        )
        self._request_json("PUT", url, headers=self._headers(), json={"fields": fields})

    def _record_to_row(self, item: dict) -> dict[str, Any]:
        fields = item.get("fields", {})
        row = {
            "고유번호": self._field_text(fields.get("고유번호")),
            "카테고리(대분류)": self._field_text(fields.get("카테고리(대분류)")),
            "카테고리(중분류)": self._field_text(fields.get("카테고리(중분류)")),
            "질문(한국어)": self._field_text(fields.get("질문(한국어)")),
            "답변(한국어)": self._field_text(fields.get("답변(한국어)")),
            "질문(중국어)": self._field_text(fields.get("질문(중국어)")),
            "답변(중국어)": self._field_text(fields.get("답변(중국어)")),
            "출처": self._field_text(fields.get("출처")),
            "상태": self._field_text(fields.get("상태")),
            "생성부서": self._field_text(fields.get("생성부서")),
            "적용범위": self._field_text(fields.get("적용범위")),
            "생성일": self._field_text(fields.get("생성일")),
            "수정일": self._field_text(fields.get("수정일")),
            "우선순위": self._to_int(fields.get("우선순위"), 5),
            "조회수": self._to_int(fields.get("조회수"), 0),
            "도움됨비율": float(fields.get("도움됨비율") or 0),
            "_record_id": item.get("record_id", ""),
        }
        return row

    def _all_rows(self) -> list[dict[str, Any]]:
        records = self._list_records(settings.lark_faq_table_id)
        return [self._record_to_row(r) for r in records]

    def get_faq_table_field_names(self) -> set[str]:
        fields = self._list_fields(settings.lark_faq_table_id)
        names: set[str] = set()
        for f in fields:
            name = str(f.get("field_name") or "").strip()
            if name:
                names.add(name)
        return names

    def check_faq_field_compatibility(self) -> dict[str, Any]:
        names = self.get_faq_table_field_names()
        missing = sorted(list(REQUIRED_FAQ_FIELDS - names))
        return {
            "ok": len(missing) == 0,
            "required_count": len(REQUIRED_FAQ_FIELDS),
            "actual_count": len(names),
            "missing_fields": missing,
        }

    def get_published_faqs(
        self,
        category_major: str | None = None,
        category_minor: str | None = None,
        scope: str | None = None,
        search: str | None = None,
    ) -> list[dict[str, Any]]:
        cache_key = "published_faqs"
        cached = self._cache.get(cache_key)

        if cached and cached.is_valid():
            rows = list(cached.data)
        else:
            rows = [r for r in self._all_rows() if self._is_published_status(r.get("상태"))]
            self._cache[cache_key] = _CacheEntry(rows)

        if category_major:
            category_major_norm = self._normalize_match_text(category_major)
            rows = [
                r for r in rows
                if self._normalize_match_text(r.get("카테고리(대분류)")) == category_major_norm
            ]
        if category_minor:
            category_minor_norm = self._normalize_match_text(category_minor)
            rows = [
                r for r in rows
                if self._normalize_match_text(r.get("카테고리(중분류)")) == category_minor_norm
            ]
        if scope:
            scope_norm = self._normalize_match_text(scope)
            rows = [r for r in rows if self._normalize_match_text(r.get("적용범위")) == scope_norm]
        if search:
            q = search.lower()
            rows = [
                r for r in rows
                if q in str(r.get("질문(한국어)", "")).lower()
                or q in str(r.get("질문(중국어)", "")).lower()
                or q in str(r.get("답변(한국어)", "")).lower()
                or q in str(r.get("답변(중국어)", "")).lower()
            ]

        return rows

    def get_modified_faqs(self, since: datetime | None = None) -> list[dict[str, Any]]:
        rows = self.get_published_faqs()
        if since is None:
            return rows

        modified: list[dict[str, Any]] = []
        for row in rows:
            raw = str(row.get("수정일") or "").strip()
            if not raw:
                continue
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except Exception:
                continue
            if dt > since:
                modified.append(row)

        return modified

    def get_faq_by_id(self, faq_id: str) -> dict[str, Any] | None:
        faq_id = str(faq_id)
        for row in self._all_rows():
            if str(row.get("고유번호")) == faq_id:
                return row
        return None

    def add_faq(
        self,
        category_major: str,
        category_minor: str,
        question_ko: str,
        answer_ko: str,
        question_zh: str = "",
        answer_zh: str = "",
        source: str = "",
        status: str = PUBLISHED_STATUS,
        department: str = "",
        scope: str = "",
        priority: int = 5,
    ) -> str:
        faq_id = str(uuid.uuid4())
        now = self._now_iso()
        fields = {
            "고유번호": faq_id,
            "카테고리(대분류)": category_major,
            "카테고리(중분류)": category_minor,
            "질문(한국어)": question_ko,
            "답변(한국어)": answer_ko,
            "질문(중국어)": question_zh,
            "답변(중국어)": answer_zh,
            "출처": source,
            "상태": status,
            "생성부서": department,
            "적용범위": scope,
            "생성일": now,
            "수정일": now,
            "우선순위": priority,
            "조회수": 0,
            "도움됨비율": 0,
        }
        self._create_record(settings.lark_faq_table_id, fields)
        self._invalidate_cache()
        return faq_id

    def increment_view_count(self, faq_id: str) -> None:
        with self._view_lock:
            self._view_buffer[faq_id] = self._view_buffer.get(faq_id, 0) + 1

    def flush_view_counts(self) -> int:
        with self._view_lock:
            pending = dict(self._view_buffer)
            self._view_buffer.clear()

        if not pending:
            return 0

        updated = 0
        for faq_id, delta in pending.items():
            row = self.get_faq_by_id(faq_id)
            if not row:
                continue
            record_id = row.get("_record_id")
            if not record_id:
                continue

            current = self._to_int(row.get("조회수"), 0)
            self._update_record(
                settings.lark_faq_table_id,
                str(record_id),
                {
                    "조회수": current + delta,
                    "수정일": self._now_iso(),
                },
            )
            updated += 1

        if updated:
            self._invalidate_cache()
            logger.info("Lark 조회수 flush 완료: {}건", updated)

        return updated

    def save_user_feedback(
        self,
        faq_id: str,
        helpful: bool,
        comment: str = "",
        language: str = "ko",
    ) -> str:
        feedback_id = str(uuid.uuid4())

        table_id = settings.lark_feedback_table_id
        if table_id:
            self._create_record(
                table_id,
                {
                    "feedback_id": feedback_id,
                    "faq_id": faq_id,
                    "helpful": bool(helpful),
                    "comment": comment,
                    "language": language,
                    "created_at": self._now_iso(),
                },
            )

        return feedback_id

    def save_feedback(self, feedback: Any) -> str:
        feedback_id = str(uuid.uuid4())
        table_id = settings.lark_feedback_table_id
        if table_id:
            self._create_record(
                table_id,
                {
                    "feedback_id": feedback_id,
                    "faq_question": getattr(feedback, "faq_question", ""),
                    "faq_answer": getattr(feedback, "faq_answer", ""),
                    "rating": int(getattr(feedback, "rating", 0) or 0),
                    "comment": getattr(feedback, "comment", "") or "",
                    "language": str(getattr(feedback, "language", "ko")),
                    "created_at": self._now_iso(),
                },
            )
        return feedback_id

    def save_source_document(
        self,
        document_id: str,
        filename: str,
        doc_type: str,
        num_chunks: int,
        total_pages: int,
        uploader: str = "",
    ) -> str:
        record_id = str(uuid.uuid4())
        table_id = settings.lark_source_doc_table_id
        if table_id:
            self._create_record(
                table_id,
                {
                    "record_id": record_id,
                    "document_id": document_id,
                    "filename": filename,
                    "doc_type": doc_type,
                    "num_chunks": num_chunks,
                    "total_pages": total_pages,
                    "uploader": uploader,
                    "created_at": self._now_iso(),
                },
            )
        return record_id


faq_sheet_manager = FAQSheetManager()
