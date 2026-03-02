"""번역 API 라우터.

POST /api/v1/translate/qa       — 단건 Q&A 번역 (한→중)
POST /api/v1/translate/batch    — 배치 Q&A 번역 (한→중, 최대 20쌍)
POST /api/v1/translate/text     — 범용 텍스트 번역
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    TranslateBatchRequest,
    TranslateBatchResponse,
    TranslateQARequest,
    TranslateQAResponse,
    TranslateRequest,
    TranslateResponse,
)
from app.services.translator import QAPair, translator

router = APIRouter(prefix="/translate", tags=["Translate"])


@router.post("/qa", response_model=TranslateQAResponse)
async def translate_qa(request: TranslateQARequest):
    """질문/답변 쌍을 한국어 → 중국어(简体中文)로 번역합니다."""
    try:
        q_zh, a_zh = translator.translate_qa(
            question_ko=request.question_ko,
            answer_ko=request.answer_ko,
        )
        return TranslateQAResponse(
            question_ko=request.question_ko,
            answer_ko=request.answer_ko,
            question_zh=q_zh,
            answer_zh=a_zh,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=TranslateBatchResponse)
async def translate_batch(request: TranslateBatchRequest):
    """여러 Q&A 쌍을 단일 API 호출로 일괄 번역합니다 (최대 20쌍)."""
    try:
        pairs = [
            QAPair(question_ko=p.question_ko, answer_ko=p.answer_ko)
            for p in request.pairs
        ]
        translated = translator.translate_batch(pairs)
        results = [
            TranslateQAResponse(
                question_ko=t.question_ko,
                answer_ko=t.answer_ko,
                question_zh=t.question_zh,
                answer_zh=t.answer_zh,
            )
            for t in translated
        ]
        return TranslateBatchResponse(results=results, total=len(results))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """범용 텍스트 번역 (기본: 한국어 → 중국어)."""
    try:
        translated = translator.translate(
            text=request.text,
            source_language=request.source_language,
            target_language=request.target_language,
        )
        return TranslateResponse(
            original_text=request.text,
            translated_text=translated,
            source_language=request.source_language,
            target_language=request.target_language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
