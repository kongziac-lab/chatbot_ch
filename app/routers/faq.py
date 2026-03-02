from fastapi import APIRouter, BackgroundTasks, HTTPException, Header
from loguru import logger
import threading

from app.models.schemas import (
    AnswerRequest,
    FAQSearchRequest,
    FAQSearchResponse,
    FAQItem,
)
from app.services.rag_engine import vector_store, COLLECTION_FAQ, COLLECTION_DOCUMENTS
from app.services.sheet_manager import faq_sheet_manager
from app.config import settings
from app.utils.sync_state import get_last_sync_time, update_last_sync_time
from app.utils.metrics import metrics_collector, Timer, SyncMetric
from datetime import datetime, timezone

router = APIRouter(prefix="/faq", tags=["FAQ"])
_SYNC_LOCK = threading.Lock()


@router.post("/answer")
async def answer_question(request: AnswerRequest):
    """레거시 /answer 엔드포인트는 비활성화되었습니다."""
    _ = request
    raise HTTPException(
        status_code=410,
        detail="FAQ /answer 엔드포인트는 제거되었습니다. /api/v1/chat 엔드포인트를 사용하세요.",
    )


@router.post("/generate")
async def generate_faq():
    """FAQ 자동 생성 기능은 비활성화되었습니다."""
    raise HTTPException(
        status_code=410,
        detail="FAQ 자동 생성 기능은 제거되었습니다. Lark Base에서 FAQ를 수동 관리하세요.",
    )


@router.post("/search", response_model=FAQSearchResponse)
async def search_faq(request: FAQSearchRequest):
    """벡터 유사도 검색."""
    try:
        results = vector_store.search(request.query, top_k=request.top_k)
        faqs = [
            FAQItem(
                question=r["text"][:200],
                answer=r["text"],
                language=request.language,
            )
            for r in results
        ]
        return FAQSearchResponse(results=faqs, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/generate")
async def start_pipeline():
    raise HTTPException(
        status_code=410,
        detail="FAQ 자동 생성 파이프라인은 제거되었습니다. Lark Base를 사용하세요.",
    )


@router.get("/pipeline/status/{job_id}")
async def get_pipeline_status(job_id: str):
    raise HTTPException(
        status_code=410,
        detail=f"FAQ 자동 생성 파이프라인은 제거되었습니다. job_id={job_id}",
    )


@router.get("/list", response_model=list[dict])
async def list_faqs(
    category_major: str | None = None,
    category_minor: str | None = None,
):
    """게시중 FAQ 조회 (카테고리 필터 지원)."""
    try:
        return faq_sheet_manager.get_published_faqs(
            category_major=category_major,
            category_minor=category_minor,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_faq_vector_sync(full_sync: bool = False) -> dict:
    """Lark Base의 게시중 FAQ를 ChromaDB에 벡터화하여 저장합니다.
    
    Args:
        full_sync: True이면 전체 동기화, False이면 증분 업데이트 (기본값)
    """
    # 성능 메트릭 수집
    timer = Timer()
    success = True
    error_msg = None
    sync_type = "full" if full_sync else "incremental"
    faq_count = 0
    chunk_count = 0
    deleted_count = 0
    
    if not _SYNC_LOCK.acquire(blocking=False):
        raise RuntimeError("이미 FAQ 동기화가 실행 중입니다. 잠시 후 다시 시도하세요.")

    try:
        with timer:
            # 1) 증분 업데이트: 마지막 동기화 이후 변경된 FAQ만 조회
            last_sync = get_last_sync_time() if not full_sync else None
            
            if last_sync:
                logger.info("🔄 증분 업데이트 시작 | 마지막 동기화: {}", last_sync.isoformat())
                faqs = faq_sheet_manager.get_modified_faqs(since=last_sync)
                sync_type = "incremental"
            else:
                logger.info("🔄 전체 동기화 시작")
                faqs = faq_sheet_manager.get_published_faqs()
                sync_type = "full"
            
            faq_count = len(faqs)
            
            if not faqs:
                update_last_sync_time()
                return {
                    "success": True,
                    "message": "변경된 FAQ가 없습니다." if last_sync else "게시중인 FAQ가 없습니다.",
                    "synced_count": 0,
                    "updated_count": 0,
                    "sync_type": sync_type,
                }

            # 2) 변경된 FAQ의 기존 벡터 삭제
            for faq in faqs:
                faq_id = str(faq.get("고유번호", ""))
                if faq_id:
                    deleted_count += vector_store.delete_by_faq_id(faq_id, COLLECTION_FAQ)
            
            logger.info("🗑️  기존 벡터 삭제 완료: {}건", deleted_count)

            # 3) FAQ를 청크 형식으로 변환
            chunks = []
            for faq in faqs:
                faq_id = str(faq.get("고유번호", ""))
                question_ko = str(faq.get("질문(한국어)", ""))
                answer_ko = str(faq.get("답변(한국어)", ""))
                question_zh = str(faq.get("질문(중국어)", ""))
                answer_zh = str(faq.get("답변(중국어)", ""))
                category = str(faq.get("카테고리(대분류)", ""))
                
                if not faq_id or not question_ko:
                    continue

                # 한국어 FAQ 청크
                chunks.append({
                    "text": f"질문: {question_ko}\n답변: {answer_ko}",
                    "metadata": {
                        "faq_id": faq_id,
                        "language": "ko",
                        "category": category,
                        "source_doc": f"FAQ_{faq_id}",
                        "doc_type": "FAQ",
                    }
                })

                # 중국어 FAQ 청크 (있는 경우)
                if question_zh:
                    chunks.append({
                        "text": f"问题: {question_zh}\n回答: {answer_zh}",
                        "metadata": {
                            "faq_id": faq_id,
                            "language": "zh",
                            "category": category,
                            "source_doc": f"FAQ_{faq_id}",
                            "doc_type": "FAQ",
                        }
                    })

            # 4) FAQ 전용 컬렉션에 저장
            document_id = "faq_master"
            chunk_count = vector_store.add_documents(
                chunks, 
                document_id,
                collection_name=COLLECTION_FAQ
            )
            
            # 5) 동기화 시간 업데이트
            update_last_sync_time()

            logger.info("✅ FAQ 동기화 완료 | 타입={} | FAQ={}건 | 청크={}건", 
                       sync_type, faq_count, chunk_count)

            return {
                "success": True,
                "message": f"FAQ 벡터화 완료 (컬렉션: {COLLECTION_FAQ})",
                "sync_type": sync_type,
                "updated_faqs": faq_count,
                "synced_count": chunk_count,
                "deleted_count": deleted_count,
                "collection": COLLECTION_FAQ,
            }

    except Exception as e:
        success = False
        error_msg = str(e)
        logger.error(f"FAQ 벡터화 오류: {e}")
        raise
    
    finally:
        _SYNC_LOCK.release()
        # 메트릭 기록
        try:
            metrics_collector.record_sync(SyncMetric(
                timestamp=datetime.now(timezone.utc).isoformat(),
                sync_type=sync_type,
                duration_ms=timer.get_elapsed_ms(),
                faq_count=faq_count,
                chunk_count=chunk_count,
                deleted_count=deleted_count,
                success=success,
                error=error_msg,
            ))
        except Exception as metric_error:
            logger.warning("동기화 메트릭 기록 실패: {}", metric_error)


@router.post("/sync-vector-db")
async def sync_faq_to_vector_db(full_sync: bool = False):
    try:
        return run_faq_vector_sync(full_sync=full_sync)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/auto-sync")
async def webhook_auto_sync(
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(..., alias="X-Webhook-Secret"),
):
    """외부 트리거에서 FAQ 변경 시 자동 호출되는 Webhook (증분 업데이트).
    
    보안:
        X-Webhook-Secret 헤더로 인증
    
    Returns:
        즉시 202 Accepted 응답, 실제 동기화는 백그라운드에서 실행
    """
    # 1) Webhook Secret 검증
    if x_webhook_secret != settings.webhook_secret:
        logger.warning("Webhook 인증 실패: 잘못된 secret")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid webhook secret")
    
    logger.info("📢 Webhook 수신: FAQ 증분 동기화 시작")
    
    # 2) 백그라운드에서 증분 동기화 실행 (응답은 즉시 반환)
    async def sync_task():
        try:
            # 증분 업데이트: 마지막 동기화 이후 변경된 FAQ만
            last_sync = get_last_sync_time()
            
            if last_sync:
                logger.info("🔄 증분 동기화 | 마지막 동기화: {}", last_sync.isoformat())
                faqs = faq_sheet_manager.get_modified_faqs(since=last_sync)
            else:
                logger.info("🔄 첫 동기화 - 전체 FAQ 처리")
                faqs = faq_sheet_manager.get_published_faqs()
            
            if not faqs:
                logger.info("변경된 FAQ 없음 - 동기화 스킵")
                update_last_sync_time()
                return
            
            # 변경된 FAQ의 기존 벡터 삭제
            deleted_count = 0
            for faq in faqs:
                faq_id = str(faq.get("고유번호", ""))
                if faq_id:
                    deleted_count += vector_store.delete_by_faq_id(faq_id, COLLECTION_FAQ)
            
            logger.info("🗑️  기존 벡터 삭제: {}건", deleted_count)
            
            # 청크 생성
            chunks = []
            for faq in faqs:
                faq_id = str(faq.get("고유번호", ""))
                question_ko = str(faq.get("질문(한국어)", ""))
                answer_ko = str(faq.get("답변(한국어)", ""))
                question_zh = str(faq.get("질문(중국어)", ""))
                answer_zh = str(faq.get("답변(중국어)", ""))
                category = str(faq.get("카테고리(대분류)", ""))
                
                if not faq_id or not question_ko:
                    continue
                
                chunks.append({
                    "text": f"질문: {question_ko}\n답변: {answer_ko}",
                    "metadata": {
                        "faq_id": faq_id,
                        "language": "ko",
                        "category": category,
                        "source_doc": f"FAQ_{faq_id}",
                        "doc_type": "FAQ",
                    }
                })
                
                if question_zh:
                    chunks.append({
                        "text": f"问题: {question_zh}\n回答: {answer_zh}",
                        "metadata": {
                            "faq_id": faq_id,
                            "language": "zh",
                            "category": category,
                            "source_doc": f"FAQ_{faq_id}",
                            "doc_type": "FAQ",
                        }
                    })
            
            synced_count = vector_store.add_documents(
                chunks, 
                "faq_master",
                collection_name=COLLECTION_FAQ
            )
            
            # 동기화 시간 업데이트
            update_last_sync_time()
            
            logger.info("✅ Webhook 증분 동기화 완료 | FAQ={}건 | 청크={}건", len(faqs), synced_count)
            
        except Exception as e:
            logger.error("❌ Webhook 동기화 실패: {}", e)
    
    background_tasks.add_task(sync_task)
    
    return {
        "status": "accepted",
        "message": "FAQ 증분 동기화 작업이 백그라운드에서 실행됩니다.",
    }
