"""공개 FAQ 조회 API.

GET  /api/v1/faqs              — 게시중 FAQ 목록 (필터·검색·언어 선택)
GET  /api/v1/faqs/{faq_id}     — 개별 FAQ 상세 조회 + 조회수 +1
POST /api/v1/faqs/{faq_id}/feedback — 도움됨 피드백 기록
"""

import traceback

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from loguru import logger

from app.models.schemas import (
    FAQDetailResponse,
    FAQListResponse,
    FAQPublicItem,
    Language,
    UserFeedbackRequest,
    UserFeedbackResponse,
)
from app.services.sheet_manager import faq_sheet_manager
from app.services.translator import translator

router = APIRouter(prefix="/faqs", tags=["Public FAQ"])

# AI 번역 캐시 (메모리): {faq_id: (question_zh, answer_zh)}
_translation_cache: dict[str, tuple[str, str]] = {}


# ---------------------------------------------------------------------------
# 내부 헬퍼
# ---------------------------------------------------------------------------

def _row_to_public(row: dict, language: Language) -> FAQPublicItem:
    """Sheets 행 딕셔너리 → FAQPublicItem 변환 (언어 선택 포함).
    
    중국어가 요청되었으나 시트에 중국어가 없으면 AI로 자동 번역합니다.
    """
    faq_id = str(row.get("고유번호", ""))
    
    if language == Language.ZH:
        question_zh = str(row.get("질문(중국어)", "")).strip()
        answer_zh = str(row.get("답변(중국어)", "")).strip()
        question_ko = str(row.get("질문(한국어)", "")).strip()
        answer_ko = str(row.get("답변(한국어)", "")).strip()
        
        # 중국어가 비어있으면 AI 자동 번역
        if not question_zh or not answer_zh:
            # 캐시 확인
            if faq_id in _translation_cache:
                question_zh, answer_zh = _translation_cache[faq_id]
                logger.debug("번역 캐시 히트: {}", faq_id)
            else:
                # AI 번역 실행
                try:
                    logger.info("AI 번역 시작: {} ({})", faq_id, question_ko[:30])
                    question_zh, answer_zh = translator.translate_qa(
                        question_ko=question_ko,
                        answer_ko=answer_ko
                    )
                    # 캐시 저장
                    _translation_cache[faq_id] = (question_zh, answer_zh)
                    logger.info("AI 번역 완료: {} → 질문({}) 답변({})", 
                               faq_id, len(question_zh), len(answer_zh))
                except Exception as e:
                    logger.error("AI 번역 실패 ({}): {} — 한국어로 fallback", faq_id, e)
                    question_zh = question_ko
                    answer_zh = answer_ko
        
        question = question_zh or question_ko
        answer = answer_zh or answer_ko
    else:
        question = str(row.get("질문(한국어)", ""))
        answer = str(row.get("답변(한국어)", ""))

    try:
        helpful_pct = float(row.get("도움됨비율") or 0)
    except (ValueError, TypeError):
        helpful_pct = None

    return FAQPublicItem(
        faq_id        = faq_id,
        category_major= str(row.get("카테고리(대분류)", "")),
        category_minor= str(row.get("카테고리(중분류)", "")),
        question      = question,
        answer        = answer,
        source        = str(row.get("출처", "")),
        scope         = str(row.get("적용범위", "")),
        priority      = int(row.get("우선순위") or 5),
        view_count    = int(row.get("조회수") or 0),
        helpful_pct   = helpful_pct,
        language      = language,
    )


def _row_to_detail(row: dict, language: Language) -> FAQDetailResponse:
    """Sheets 행 딕셔너리 → FAQDetailResponse 변환.
    
    상세 조회는 한국어와 중국어를 모두 반환합니다.
    중국어가 시트에 없으면 AI로 자동 번역합니다.
    """
    base = _row_to_public(row, language)
    
    faq_id = str(row.get("고유번호", ""))
    question_ko = str(row.get("질문(한국어)", "")).strip()
    answer_ko = str(row.get("답변(한국어)", "")).strip()
    question_zh = str(row.get("질문(중국어)", "")).strip()
    answer_zh = str(row.get("답변(중국어)", "")).strip()
    
    # 중국어가 비어있으면 AI 자동 번역
    if not question_zh or not answer_zh:
        if faq_id in _translation_cache:
            question_zh, answer_zh = _translation_cache[faq_id]
        else:
            try:
                logger.info("상세조회 AI 번역: {}", faq_id)
                question_zh, answer_zh = translator.translate_qa(
                    question_ko=question_ko,
                    answer_ko=answer_ko
                )
                _translation_cache[faq_id] = (question_zh, answer_zh)
            except Exception as e:
                logger.error("상세조회 번역 실패 ({}): {}", faq_id, e)
                question_zh = question_ko
                answer_zh = answer_ko
    
    return FAQDetailResponse(
        **base.model_dump(),
        question_ko = question_ko,
        answer_ko   = answer_ko,
        question_zh = question_zh or question_ko,
        answer_zh   = answer_zh or answer_ko,
        created_at  = str(row.get("생성일", "")),
        updated_at  = str(row.get("수정일", "")),
    )


# ---------------------------------------------------------------------------
# GET /faqs — 목록 조회
# ---------------------------------------------------------------------------

@router.get("", response_model=FAQListResponse)
async def list_public_faqs(
    category_major: str | None = Query(default=None, description="카테고리(대분류) 필터"),
    category_minor: str | None = Query(default=None, description="카테고리(중분류) 필터"),
    scope:    str | None = Query(default=None, description="적용범위 필터"),
    lang:     Language   = Query(default=Language.KO, description="응답 언어 (ko / zh)"),
    search:   str | None = Query(default=None, min_length=1, max_length=100,
                                 description="질문 키워드 검색"),
):
    """게시중 FAQ를 필터·검색 조건으로 조회합니다.

    - **category_major**: 대분류 정확 매칭
    - **category_minor**: 중분류 정확 매칭
    - **scope**: 적용범위 정확 매칭
    - **lang**: `ko`(기본) 또는 `zh` — 반환 질문/답변 언어
    - **search**: 질문(한·중) 키워드 포함 검색 (대소문자 무시)
    """
    try:
        rows = faq_sheet_manager.get_published_faqs(
            category_major=category_major,
            category_minor=category_minor,
            scope=search and None or scope,   # scope는 search와 별개 적용
            search=search,
        )
        # scope 필터 별도 적용 (search와 독립)
        if scope:
            rows = [r for r in rows if r.get("적용범위") == scope]

        # 우선순위 오름차순 정렬
        rows.sort(key=lambda r: int(r.get("우선순위") or 99))

        items = [_row_to_public(r, lang) for r in rows]
        return FAQListResponse(items=items, total=len(items), language=lang)
    except Exception as e:
        logger.error("FAQ 목록 조회 실패:\n{}", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /faqs/{faq_id} — 상세 조회
# ---------------------------------------------------------------------------

@router.get("/{faq_id}", response_model=FAQDetailResponse)
async def get_faq_detail(
    faq_id: str,
    lang:   Language        = Query(default=Language.KO, description="응답 언어"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """개별 FAQ를 조회하고 조회수를 1 증가시킵니다."""
    try:
        row = faq_sheet_manager.get_faq_by_id(faq_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ를 찾을 수 없습니다: {faq_id}")

    # 조회수 업데이트 — 응답을 블로킹하지 않도록 백그라운드 처리
    background_tasks.add_task(faq_sheet_manager.increment_view_count, faq_id)

    return _row_to_detail(row, lang)


# ---------------------------------------------------------------------------
# POST /faqs/{faq_id}/feedback — 피드백 기록
# ---------------------------------------------------------------------------

@router.post("/{faq_id}/feedback", response_model=UserFeedbackResponse)
async def submit_feedback(faq_id: str, body: UserFeedbackRequest):
    """도움됨 여부와 선택적 코멘트를 User_Feedback 시트에 기록하고
    FAQ_Master의 도움됨비율을 재계산합니다.
    """
    # FAQ 존재 여부 확인
    try:
        row = faq_sheet_manager.get_faq_by_id(faq_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if row is None:
        raise HTTPException(status_code=404, detail=f"FAQ를 찾을 수 없습니다: {faq_id}")

    try:
        feedback_id = faq_sheet_manager.save_user_feedback(
            faq_id   = faq_id,
            helpful  = body.helpful,
            comment  = body.comment or "",
            language = body.language.value,
        )
        return UserFeedbackResponse(
            success     = True,
            message     = "피드백이 기록되었습니다. 감사합니다!",
            feedback_id = feedback_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
