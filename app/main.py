"""FastAPI 애플리케이션 진입점.

최적화:
  - lifespan 이벤트로 조회수 버퍼를 120초 간격으로 자동 flush
  - loguru 로깅 설정
"""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime, date
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.config import settings
from app.routers import faq, faqs, chat, feedback, translate, metrics

# ---------------------------------------------------------------------------
# 조회수 자동 flush 백그라운드 태스크
# ---------------------------------------------------------------------------

_FLUSH_INTERVAL = 120   # seconds


async def _view_count_flush_loop() -> None:
    """120초 간격으로 조회수 버퍼를 Lark Base에 일괄 반영."""
    from app.services.sheet_manager import faq_sheet_manager
    while True:
        await asyncio.sleep(_FLUSH_INTERVAL)
        try:
            updated = faq_sheet_manager.flush_view_counts()
            if updated:
                logger.info("조회수 자동 flush: {}건 반영", updated)
        except Exception as exc:
            logger.warning("조회수 flush 실패 (다음 주기에 재시도): {}", exc)


async def _faq_auto_sync_loop() -> None:
    """10분 증분 + 하루 1회 전체 FAQ 벡터 자동 동기화."""
    from app.routers import faq as faq_router

    incremental_sec = settings.auto_sync_incremental_minutes * 60
    last_incremental_at = 0.0
    last_full_sync_date: date | None = None

    await asyncio.sleep(15)

    while True:
        now = datetime.now()
        try:
            # 하루 1회 전체 동기화
            if now.hour == settings.auto_sync_full_hour and last_full_sync_date != now.date():
                result = faq_router.run_faq_vector_sync(full_sync=True)
                last_full_sync_date = now.date()
                last_incremental_at = time.monotonic()
                logger.info(
                    "자동 전체 동기화 완료: updated_faqs={} synced_count={}",
                    result.get("updated_faqs", 0),
                    result.get("synced_count", 0),
                )
            # 10분 주기 증분 동기화
            elif time.monotonic() - last_incremental_at >= incremental_sec:
                result = faq_router.run_faq_vector_sync(full_sync=False)
                last_incremental_at = time.monotonic()
                logger.info(
                    "자동 증분 동기화 완료: updated_faqs={} synced_count={}",
                    result.get("updated_faqs", 0),
                    result.get("synced_count", 0),
                )
        except Exception as exc:
            logger.warning("자동 FAQ 동기화 실패 (다음 주기에 재시도): {}", exc)

        await asyncio.sleep(30)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("{} v{} 시작", settings.app_name, settings.app_version)
    flush_task = asyncio.create_task(_view_count_flush_loop())
    auto_sync_task = None
    if settings.auto_sync_enabled:
        auto_sync_task = asyncio.create_task(_faq_auto_sync_loop())
        logger.info(
            "자동 FAQ 동기화 활성화: {}분 주기 증분, 매일 {:02d}:00 전체",
            settings.auto_sync_incremental_minutes,
            settings.auto_sync_full_hour,
        )
    yield
    flush_task.cancel()
    if auto_sync_task:
        auto_sync_task.cancel()
    # 종료 시 남은 조회수 한 번 flush
    try:
        from app.services.sheet_manager import faq_sheet_manager
        faq_sheet_manager.flush_view_counts()
    except Exception:
        pass
    logger.info("{} 종료", settings.app_name)


# ---------------------------------------------------------------------------
# FastAPI 앱
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(faq.router,       prefix="/api/v1")   # 내부 관리 API
app.include_router(faqs.router,      prefix="/api/v1")   # 공개 조회 API
app.include_router(chat.router,      prefix="/api/v1")   # 챗봇 API
app.include_router(feedback.router,  prefix="/api/v1")
app.include_router(translate.router, prefix="/api/v1")
app.include_router(metrics.router,   prefix="/api/v1")   # 성능 메트릭 API


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.app_version}


@app.post("/admin/flush-view-counts", tags=["Admin"])
async def flush_view_counts():
    """조회수 버퍼를 즉시 Lark Base에 반영합니다 (관리자용)."""
    from app.services.sheet_manager import faq_sheet_manager
    updated = faq_sheet_manager.flush_view_counts()
    return {"flushed": updated}


@app.get("/admin/vector-health", tags=["Admin"])
async def vector_health():
    """ChromaDB 컬렉션 상태를 반환합니다."""
    from app.services.rag_engine import vector_store
    return vector_store.health_snapshot()


@app.get("/admin/preflight", tags=["Admin"])
async def preflight():
    """Lark Base + ChromaDB 기본 상태를 한번에 점검합니다."""
    from app.services.rag_engine import vector_store
    from app.services.sheet_manager import faq_sheet_manager

    result: dict[str, object] = {"ok": True}

    try:
        token = faq_sheet_manager._get_tenant_access_token()  # noqa: SLF001
        result["lark_token_ok"] = bool(token)
    except Exception as exc:
        result["ok"] = False
        result["lark_token_ok"] = False
        result["lark_token_error"] = str(exc)

    try:
        compat = faq_sheet_manager.check_faq_field_compatibility()
        result["faq_field_compatibility"] = compat
        if not compat.get("ok", False):
            result["ok"] = False
    except Exception as exc:
        result["ok"] = False
        result["faq_field_compatibility"] = {"ok": False, "error": str(exc)}

    try:
        result["vector_store"] = vector_store.health_snapshot()
    except Exception as exc:
        result["ok"] = False
        result["vector_store"] = {"ok": False, "error": str(exc)}

    return result


@app.get("/admin/lark-field-compat", tags=["Admin"])
async def lark_field_compat():
    """Lark FAQ 테이블 필드 호환성만 반환합니다."""
    from app.services.sheet_manager import faq_sheet_manager
    try:
        return faq_sheet_manager.check_faq_field_compatibility()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# 정적 파일 제공 (Vite 빌드 결과)
# ---------------------------------------------------------------------------

# public/dist 폴더가 존재하면 정적 파일 제공
_PUBLIC_DIST = Path(__file__).parent.parent / "public" / "dist"
if _PUBLIC_DIST.exists() and _PUBLIC_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_PUBLIC_DIST), html=True), name="frontend")
    logger.info("프론트엔드 정적 파일 제공: {}", _PUBLIC_DIST)
