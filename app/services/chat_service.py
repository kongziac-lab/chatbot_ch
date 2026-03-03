"""RAG 기반 챗봇 서비스.

ChatService:
  - 언어 자동 감지 (한국어 / 중국어)
  - 세션별 대화 이력 관리 (인메모리)
  - 벡터 DB 검색 → OpenAI GPT 답변 생성
  - 관련 FAQ 링크 제공
"""

from __future__ import annotations

import re
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI, RateLimitError, APIStatusError
from loguru import logger

from app.config import settings
from app.utils.metrics import metrics_collector, Timer, ChatMetric

_MAX_RETRIES = 3
_RETRY_DELAY = 1.0
from app.models.schemas import Language
from app.services.rag_engine import vector_store, COLLECTION_FAQ, COLLECTION_DOCUMENTS
from app.services.sheet_manager import faq_sheet_manager

# ---------------------------------------------------------------------------
# 언어 감지
# ---------------------------------------------------------------------------

_KO_RE  = re.compile(r"[\uAC00-\uD7AF\u1100-\u11FF]")   # 한글 음절·자모
_ZH_RE  = re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF]")   # CJK 한자

def detect_language(text: str) -> Language:
    """텍스트에서 한국어/중국어를 자동 감지.

    한글 문자 수 > 한자 문자 수 → 한국어
    한자 문자 수 ≥ 한글 문자 수 → 중국어
    판단 불가 → 한국어(기본)
    """
    ko_count = len(_KO_RE.findall(text))
    zh_count = len(_ZH_RE.findall(text))
    if zh_count > 0 and zh_count >= ko_count:
        return Language.ZH
    return Language.KO


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    role: str        # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RelatedFAQ:
    faq_id: str
    question: str
    language: Language


@dataclass
class ChatResult:
    answer: str
    language: Language
    related_faqs: list[RelatedFAQ]
    session_id: str
    confidence: str   # high | medium | low


# ---------------------------------------------------------------------------
# 프롬프트
# ---------------------------------------------------------------------------

_SYSTEM_KO = textwrap.dedent("""\
    당신은 외국인 유학생을 돕는 대학 행정 FAQ 챗봇입니다.
    반드시 제공된 참고자료에 근거해서만 답변하세요.
    참고자료에 없는 내용은 "해당 정보를 찾을 수 없습니다. 담당 부서에 문의하세요."라고 안내하세요.
    답변은 친절하고 간결하게, 한국어로 작성하세요.
""")

_SYSTEM_ZH = textwrap.dedent("""\
    您是一位帮助外国留学生的大学行政FAQ聊天机器人。
    请仅根据提供的参考资料回答问题。
    如果参考资料中没有相关信息，请说明"暂无相关信息，请联系相关部门。"
    请用简体中文友好、简洁地回答。
""")

_CHAT_PROMPT = textwrap.dedent("""\
    [참고자료]
    {context}

    [이전 대화]
    {history}

    [현재 질문]
    {question}
""")

_CHAT_PROMPT_ZH = textwrap.dedent("""\
    [参考资料]
    {context}

    [对话历史]
    {history}

    [当前问题]
    {question}
""")

_MAX_HISTORY = 6        # 최근 N개 메시지만 유지 (토큰 절약)
_TOP_K_CHUNKS = 5
_TOP_K_RELATED = 3     # 관련 FAQ 최대 수
_MIN_SOURCE_SCORE = 0.35  # 출처로 노출할 최소 유사도
_KOREAN_JOSA_SUFFIXES = ("으로", "에서", "에게", "께서", "까지", "부터", "처럼", "보다", "하고", "이며", "에", "은", "는", "이", "가", "을", "를", "도", "과", "와", "로", "의")


# ---------------------------------------------------------------------------
# ChatService
# ---------------------------------------------------------------------------

class ChatService:
    """RAG 기반 챗봇 서비스."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)
        # session_id → list[ChatMessage]
        self._sessions: dict[str, list[ChatMessage]] = {}

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def chat(
        self,
        message: str,
        session_id: str | None = None,
    ) -> ChatResult:
        """사용자 메시지를 받아 RAG 답변과 관련 FAQ를 반환.

        Args:
            message:    사용자 입력 문장
            session_id: 이전 세션 재사용 (None이면 신규 생성)

        Returns:
            ChatResult (answer, language, related_faqs, session_id, confidence)
        """
        # 성능 메트릭 수집 시작
        total_timer = Timer()
        search_timer = Timer()
        llm_timer = Timer()
        
        success = True
        error_msg = None
        confidence = "low"
        chunk_count = 0
        
        try:
            with total_timer:
                # 세션 초기화
                if not session_id or session_id not in self._sessions:
                    session_id = str(uuid.uuid4())
                    self._sessions[session_id] = []

                history = self._sessions[session_id]

                # 1) 언어 감지
                language = detect_language(message)

                # 2) 벡터 DB 검색 (FAQ 우선) - 성능 측정
                with search_timer:
                    try:
                        # 2-1) FAQ 컬렉션에서 먼저 검색
                        faq_chunks = vector_store.search(
                            message, 
                            top_k=_TOP_K_CHUNKS, 
                            collection_name=COLLECTION_FAQ
                        )
                        
                        # 2-2) FAQ에서 충분하지 않으면 원본 문서에서 보충
                        if len(faq_chunks) < _TOP_K_CHUNKS:
                            doc_chunks = vector_store.search(
                                message,
                                top_k=_TOP_K_CHUNKS - len(faq_chunks),
                                collection_name=COLLECTION_DOCUMENTS
                            )
                            chunks = faq_chunks + doc_chunks
                            logger.debug("복합 검색: FAQ={}건, 문서={}건", len(faq_chunks), len(doc_chunks))
                        else:
                            chunks = faq_chunks
                            logger.debug("FAQ 검색: {}건", len(faq_chunks))
                            
                    except Exception as e:
                        logger.error("벡터 DB 검색 오류: {} | 타입: {}", str(e), type(e).__name__)
                        raise
                
                chunk_count = len(chunks)
                context = self._format_context(chunks)
                confidence = (
                    "high"   if len(chunks) >= 3 else
                    "medium" if len(chunks) >= 1 else
                    "low"
                )

                # 3) 관련 FAQ 출처 구성
                #    - 1순위: 실제 검색에 사용된 FAQ 청크 metadata(faq_id)
                #    - 2순위: 질문 키워드 기반 보조 검색
                related_faqs = self._find_related_faqs_from_chunks(chunks, language, message)
                if len(related_faqs) < _TOP_K_RELATED:
                    keyword_related = self._find_related_faqs(message, language)
                    existing_ids = {f.faq_id for f in related_faqs}
                    for item in keyword_related:
                        if item.faq_id in existing_ids:
                            continue
                        related_faqs.append(item)
                        existing_ids.add(item.faq_id)
                        if len(related_faqs) >= _TOP_K_RELATED:
                            break

                # 3-3) 출처가 비면 상위 FAQ 청크 1건은 반드시 표기
                if not related_faqs:
                    fallback = self._fallback_source_from_chunks(chunks, language)
                    if fallback:
                        related_faqs = [fallback]

                # 4) OpenAI GPT 답변 생성 - 성능 측정
                with llm_timer:
                    history_text = self._format_history(history, language)
                    if language == Language.ZH:
                        prompt  = _CHAT_PROMPT_ZH.format(
                            context=context or "暂无参考资料。",
                            history=history_text,
                            question=message,
                        )
                        system = _SYSTEM_ZH
                    else:
                        prompt = _CHAT_PROMPT.format(
                            context=context or "※ 관련 참고자료를 찾을 수 없습니다.",
                            history=history_text,
                            question=message,
                        )
                        system = _SYSTEM_KO

                    answer = self._call_openai(system, prompt)

                # 5) 대화 이력 저장 (최근 N개 유지)
                history.append(ChatMessage(role="user",      content=message))
                history.append(ChatMessage(role="assistant", content=answer))
                self._sessions[session_id] = history[-_MAX_HISTORY:]

                result = ChatResult(
                    answer       = answer,
                    language     = language,
                    related_faqs = related_faqs,
                    session_id   = session_id,
                    confidence   = confidence,
                )
        
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error("챗봇 오류: {}", e)
            raise
        
        finally:
            # 메트릭 기록
            try:
                metrics_collector.record_chat(ChatMetric(
                    timestamp=datetime.now().isoformat(),
                    message=message[:100],  # 처음 100자만 저장
                    language=language.value if 'language' in locals() else "ko",
                    duration_ms=total_timer.get_elapsed_ms(),
                    search_duration_ms=search_timer.get_elapsed_ms(),
                    llm_duration_ms=llm_timer.get_elapsed_ms(),
                    confidence=confidence,
                    chunk_count=chunk_count,
                    success=success,
                    error=error_msg,
                ))
            except Exception as metric_error:
                logger.warning("메트릭 기록 실패: {}", metric_error)
        
        return result

    def clear_session(self, session_id: str) -> None:
        """세션 대화 이력 초기화."""
        self._sessions.pop(session_id, None)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _call_openai(self, system: str, prompt: str) -> str:
        """OpenAI GPT API 호출 with 3회 재시도 및 폴백."""
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=1024,
                    temperature=0.7,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.choices[0].message.content.strip()
            except (RateLimitError, APIStatusError) as exc:
                delay = _RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning("챗봇 API 오류 (시도 {}/{}) — {}s 후 재시도: {}", attempt, _MAX_RETRIES, delay, exc)
                last_exc = exc
                time.sleep(delay)
            except Exception as exc:
                logger.error("챗봇 API 예외: {}", exc)
                return "죄송합니다. 현재 답변을 생성할 수 없습니다."
        logger.error("챗봇 API {}회 재시도 모두 실패: {}", _MAX_RETRIES, last_exc)
        return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."

    def _format_context(self, chunks: list[dict]) -> str:
        parts = []
        for i, c in enumerate(chunks, 1):
            meta = c.get("metadata", {})
            src  = meta.get("source_doc", "")
            page = meta.get("page_num", "")
            text = c.get("text", "").strip()
            parts.append(f"[{i}] {src} p.{page}\n{text}")
        return "\n\n".join(parts)

    def _format_history(self, history: list[ChatMessage], language: Language) -> str:
        if not history:
            return "(없음)" if language == Language.KO else "(无)"
        lines = []
        for m in history[-_MAX_HISTORY:]:
            role = "사용자" if m.role == "user" else "챗봇"
            if language == Language.ZH:
                role = "用户" if m.role == "user" else "机器人"
            lines.append(f"{role}: {m.content}")
        return "\n".join(lines)

    def _find_related_faqs(
        self, query: str, language: Language
    ) -> list[RelatedFAQ]:
        """Sheets 캐시에서 질문 키워드로 관련 FAQ 검색."""
        try:
            rows = faq_sheet_manager.get_published_faqs(search=query)
        except Exception:
            return []

        results: list[RelatedFAQ] = []
        q_col = "질문(중국어)" if language == Language.ZH else "질문(한국어)"

        for r in rows[:_TOP_K_RELATED]:
            faq_id   = str(r.get("고유번호", ""))
            question = str(r.get(q_col, "") or r.get("질문(한국어)", ""))
            if faq_id and question:
                results.append(RelatedFAQ(
                    faq_id   = faq_id,
                    question = question,
                    language = language,
                ))
        return results

    def _find_related_faqs_from_chunks(
        self, chunks: list[dict], language: Language, query: str
    ) -> list[RelatedFAQ]:
        """검색에 실제 사용된 FAQ 청크의 faq_id를 출처로 변환."""
        q_col = "질문(중국어)" if language == Language.ZH else "질문(한국어)"
        results: list[RelatedFAQ] = []
        seen_ids: set[str] = set()
        keywords = self._extract_query_keywords(query)

        for c in chunks:
            meta = c.get("metadata", {}) or {}
            faq_id = str(meta.get("faq_id", "")).strip()
            score = float(c.get("score") or 0.0)
            if not faq_id or faq_id in seen_ids:
                continue
            if score < _MIN_SOURCE_SCORE:
                continue

            question = ""
            try:
                row = faq_sheet_manager.get_faq_by_id(faq_id)
                if row:
                    question = str(row.get(q_col, "") or row.get("질문(한국어)", "")).strip()
            except Exception:
                question = ""

            if not question:
                question = f"FAQ-{faq_id}"
            elif keywords and not self._has_keyword_overlap(question, keywords):
                # 질문 키워드와 겹치지 않으면 출처 표기에서 제외
                continue

            results.append(
                RelatedFAQ(
                    faq_id=faq_id,
                    question=question,
                    language=language,
                )
            )
            seen_ids.add(faq_id)

            if len(results) >= _TOP_K_RELATED:
                break

        return results

    @staticmethod
    def _extract_query_keywords(query: str) -> list[str]:
        """질문 문장에서 출처 필터링용 키워드 추출."""
        stopwords = {"대해", "알려줘", "알려주세요", "문의", "질문", "어떻게", "무엇", "인가요", "해주세요"}
        tokens = [t.strip().lower() for t in re.split(r"[\s,./!?()\[\]{}]+", query) if t.strip()]
        normalized_tokens: list[str] = []
        for t in tokens:
            norm = t
            for suffix in _KOREAN_JOSA_SUFFIXES:
                if norm.endswith(suffix) and len(norm) > len(suffix) + 1:
                    norm = norm[: -len(suffix)]
                    break
            normalized_tokens.append(norm)
        # 2자 이상 토큰만 사용
        tokens = [t for t in normalized_tokens if len(t) >= 2 and t not in stopwords]
        return tokens

    @staticmethod
    def _has_keyword_overlap(text: str, keywords: list[str]) -> bool:
        low = text.lower()
        return any((k in low) or (low in k) for k in keywords)

    def _fallback_source_from_chunks(
        self, chunks: list[dict], language: Language
    ) -> RelatedFAQ | None:
        """필터링 결과가 비었을 때 상위 FAQ 청크 1건을 출처로 보장."""
        q_col = "질문(중국어)" if language == Language.ZH else "질문(한국어)"
        for c in chunks:
            meta = c.get("metadata", {}) or {}
            faq_id = str(meta.get("faq_id", "")).strip()
            if not faq_id:
                continue
            question = f"FAQ-{faq_id}"
            try:
                row = faq_sheet_manager.get_faq_by_id(faq_id)
                if row:
                    question = str(row.get(q_col, "") or row.get("질문(한국어)", "")).strip() or question
            except Exception:
                pass
            return RelatedFAQ(faq_id=faq_id, question=question, language=language)
        return None


chat_service = ChatService()
