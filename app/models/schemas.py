from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class Language(str, Enum):
    KO = "ko"
    EN = "en"
    JA = "ja"
    ZH = "zh"


class FAQItem(BaseModel):
    question: str
    answer: str
    category: Optional[str] = None
    language: Language = Language.KO


class FAQGenerateRequest(BaseModel):
    topic: str = Field(..., description="FAQ를 생성할 주제 또는 질문")
    num_faqs: int = Field(default=5, ge=1, le=20, description="생성할 FAQ 개수")
    language: Language = Field(default=Language.KO, description="생성 언어")
    category: Optional[str] = Field(default=None, description="FAQ 대분류 카테고리")
    category_minor: Optional[str] = Field(default="", description="FAQ 중분류 카테고리")


class FAQGenerateResponse(BaseModel):
    faqs: list[FAQItem]
    source_document: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class FAQSearchRequest(BaseModel):
    query: str = Field(..., description="검색 쿼리")
    language: Language = Field(default=Language.KO)
    top_k: int = Field(default=5, ge=1, le=20)


class FAQSearchResponse(BaseModel):
    results: list[FAQItem]
    query: str


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    doc_type: str
    total_pages: int
    num_chunks: int
    message: str


class FeedbackRequest(BaseModel):
    faq_question: str
    faq_answer: str
    rating: int = Field(..., ge=1, le=5, description="평점 1-5")
    comment: Optional[str] = None
    language: Language = Language.KO


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None


class AnswerRequest(BaseModel):
    question: str = Field(..., description="유학생 질문")
    language: Language = Field(default=Language.KO, description="답변 언어")
    doc_type: Optional[str] = Field(default=None, description="문서 유형 필터 (규정/공지/안내)")


class SourceRef(BaseModel):
    source_doc: str
    page_num: int
    doc_type: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    language: Language
    sources: list[SourceRef]
    retrieved_count: int
    confidence: str   # high / medium / low


class TranslateRequest(BaseModel):
    text: str
    source_language: Language = Language.KO
    target_language: Language = Language.ZH


class TranslateResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: Language
    target_language: Language


class TranslateQARequest(BaseModel):
    question_ko: str = Field(..., description="한국어 질문")
    answer_ko: str = Field(..., description="한국어 답변")


class TranslateQAResponse(BaseModel):
    question_ko: str
    answer_ko: str
    question_zh: str
    answer_zh: str


class TranslateBatchRequest(BaseModel):
    pairs: list[TranslateQARequest] = Field(
        ..., min_length=1, max_length=20, description="번역할 Q&A 쌍 목록 (최대 20개)"
    )


class TranslateBatchResponse(BaseModel):
    results: list[TranslateQAResponse]
    total: int


# ---------------------------------------------------------------------------
# Chat API
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message:    str            = Field(..., min_length=1, max_length=500, description="사용자 질문")
    session_id: Optional[str]  = Field(default=None, description="이전 세션 ID (재사용 시 전달)")


class RelatedFAQItem(BaseModel):
    faq_id:   str
    question: str
    language: Language


class ChatResponse(BaseModel):
    answer:       str
    language:     Language
    related_faqs: list[RelatedFAQItem]
    session_id:   str
    confidence:   str    # high | medium | low


class ChatFeedbackRequest(BaseModel):
    session_id: str
    helpful:    bool
    comment:    Optional[str] = Field(default=None, max_length=300)


class ChatFeedbackResponse(BaseModel):
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Public FAQ 조회 API
# ---------------------------------------------------------------------------

class FAQPublicItem(BaseModel):
    faq_id: str
    category_major: str
    category_minor: str
    question: str             # lang 파라미터에 따라 한국어 또는 중국어
    answer: str
    source: str
    scope: str
    priority: int
    view_count: int
    helpful_pct: Optional[float] = None
    language: Language


class FAQListResponse(BaseModel):
    items: list[FAQPublicItem]
    total: int
    language: Language


class FAQDetailResponse(FAQPublicItem):
    question_ko: str
    answer_ko: str
    question_zh: str
    answer_zh: str
    created_at: str
    updated_at: str


class UserFeedbackRequest(BaseModel):
    helpful: bool = Field(..., description="도움이 되었나요?")
    comment: Optional[str] = Field(default=None, max_length=500, description="추가 의견")
    language: Language = Field(default=Language.KO, description="사용 언어")


class UserFeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class PipelineRequest(BaseModel):
    doc_id: str = Field(..., description="벡터 DB에 저장된 문서 ID")
    department: str = Field(default="", description="생성 부서")
    category_major: str = Field(default="", description="카테고리 대분류")
    category_minor: str = Field(default="", description="카테고리 중분류")


class PipelineStartResponse(BaseModel):
    job_id: str
    status: str
    message: str


class PipelineStatusResponse(BaseModel):
    job_id: str
    doc_id: str
    status: str                    # pending | running | completed | failed
    department: str
    total_chunks: int
    raw_questions: int
    unique_questions: int
    saved_faqs: int
    error: str
    started_at: str
    completed_at: str
