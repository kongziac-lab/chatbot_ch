"""챗봇 API 라우터.

POST /api/v1/chat           — RAG 기반 질의응답
DELETE /api/v1/chat/{sid}   — 세션 초기화
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatFeedbackRequest,
    ChatFeedbackResponse,
    ChatRequest,
    ChatResponse,
    RelatedFAQItem,
)
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """사용자 질문을 받아 RAG 기반 답변과 관련 FAQ를 반환합니다.

    - 언어(한국어/중국어) 자동 감지
    - 세션 이력을 유지해 연속 대화 지원 (`session_id` 재전달)
    """
    try:
        result = chat_service.chat(
            message    = request.message,
            session_id = request.session_id,
        )
        return ChatResponse(
            answer       = result.answer,
            language     = result.language,
            session_id   = result.session_id,
            confidence   = result.confidence,
            related_faqs = [
                RelatedFAQItem(
                    faq_id   = f.faq_id,
                    question = f.question,
                    language = f.language,
                )
                for f in result.related_faqs
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}", response_model=ChatFeedbackResponse)
async def clear_session(session_id: str):
    """대화 세션 이력을 초기화합니다."""
    chat_service.clear_session(session_id)
    return ChatFeedbackResponse(success=True, message="세션이 초기화되었습니다.")
