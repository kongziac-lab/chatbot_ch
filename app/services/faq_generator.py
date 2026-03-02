"""FAQ 생성 및 RAG 기반 답변 생성 서비스.

FAQGenerator   : 주제 → FAQ 목록 (JSON) 생성
AnswerGenerator: 질문 → 벡터 DB 검색 → OpenAI GPT 근거 기반 답변

최적화:
  - loguru 로깅
  - LLM API 3회 재시도 + 폴백 처리 (_call_llm)
  - FAQ 생성 파이프라인 에러 핸들링 강화
"""

from __future__ import annotations

import json
import re
import textwrap
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI, RateLimitError, APIStatusError
import numpy as np
from loguru import logger

from app.config import settings
from app.models.schemas import FAQItem, Language
from app.services.rag_engine import vector_store

# ---------------------------------------------------------------------------
# 공통
# ---------------------------------------------------------------------------

LANGUAGE_NAMES = {
    Language.KO: "한국어",
    Language.EN: "English",
    Language.JA: "日本語",
    Language.ZH: "中文",
}

_openai_client = OpenAI(api_key=settings.openai_api_key)

_LLM_MAX_RETRIES   = 3
_LLM_RETRY_DELAY   = 1.0    # 지수 백오프 기준 (seconds)
_LLM_TIMEOUT       = 60.0   # 단일 요청 타임아웃 (seconds; SDK 옵션)


# ---------------------------------------------------------------------------
# LLM 재시도 헬퍼
# ---------------------------------------------------------------------------

def _call_llm(
    *,
    model: str,
    system: str,
    user_prompt: str,
    max_tokens: int,
    fallback_text: str = "",
) -> str:
    """OpenAI API 호출 with 3회 재시도 및 폴백.

    Args:
        model:         OpenAI 모델 ID (gpt-4o, gpt-4o-mini 등)
        system:        시스템 프롬프트
        user_prompt:   사용자 메시지
        max_tokens:    최대 출력 토큰
        fallback_text: 3회 실패 시 반환할 폴백 문자열

    Returns:
        응답 텍스트 (실패 시 fallback_text)
    """
    last_exc: Exception | None = None
    for attempt in range(1, _LLM_MAX_RETRIES + 1):
        try:
            response = _openai_client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content
            return content.strip() if content else fallback_text
        except RateLimitError as exc:
            delay = _LLM_RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning("LLM RateLimit (시도 {}/{}) — {}s 후 재시도: {}", attempt, _LLM_MAX_RETRIES, delay, exc)
            last_exc = exc
            time.sleep(delay)
        except APIStatusError as exc:
            status_code = getattr(exc, "status_code", None)
            if status_code and status_code >= 500:
                delay = _LLM_RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning("LLM 서버 오류 {} (시도 {}/{}) — {}s 후 재시도", status_code, attempt, _LLM_MAX_RETRIES, delay)
                last_exc = exc
                time.sleep(delay)
            else:
                logger.error("LLM API 클라이언트 오류: {}", exc)
                return fallback_text
        except Exception as exc:
            delay = _LLM_RETRY_DELAY * (2 ** (attempt - 1))
            logger.warning("LLM 예외 (시도 {}/{}) — {}s 후 재시도: {}", attempt, _LLM_MAX_RETRIES, delay, exc)
            last_exc = exc
            time.sleep(delay)

    logger.error("LLM {}회 재시도 모두 실패: {}", _LLM_MAX_RETRIES, last_exc)
    return fallback_text


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class SourceRef:
    """답변에 인용된 출처 정보."""
    source_doc: str
    page_num: int
    doc_type: str


@dataclass
class AnswerResult:
    """AnswerGenerator 반환 타입."""
    question: str
    answer: str
    language: Language
    sources: list[SourceRef] = field(default_factory=list)
    retrieved_count: int = 0
    confidence: str = "medium"    # high / medium / low


# ---------------------------------------------------------------------------
# AnswerGenerator
# ---------------------------------------------------------------------------

_ANSWER_SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 외국인 유학생을 위한 학교 FAQ 답변 전문가입니다.
    반드시 제공된 참고자료에 근거해서만 답변하세요.
    참고자료에 없는 내용은 "해당 정보를 참고자료에서 찾을 수 없습니다"라고 답하세요.
""")

_ANSWER_PROMPT_TEMPLATE = textwrap.dedent("""\
    아래 참고자료를 바탕으로 외국인 유학생의 질문에 정확하게 답변하세요.

    [규칙]
    1. 참고자료에 있는 내용만 답변하세요
    2. 단계별로 명확하게 설명하세요
    3. 관련 규정/조항 번호를 출처로 표시하세요
    4. 연락처나 부서 정보가 있으면 포함하세요
    5. 답변 마지막에 [출처: 문서명, 조항] 형식으로 표시

    [참고자료]
    {retrieved_chunks}

    [질문]
    {question}
""")

_ANSWER_FALLBACK = "죄송합니다. 현재 답변을 생성할 수 없습니다. 잠시 후 다시 시도해 주세요."


class AnswerGenerator:
    """RAG 기반 질의응답 생성기."""

    def __init__(self, top_k: int = 5) -> None:
        self._top_k = top_k

    def generate(
        self,
        question: str,
        language: Language = Language.KO,
        doc_type: str | None = None,
    ) -> AnswerResult:
        """질문을 받아 벡터 DB 검색 후 Claude로 근거 기반 답변 생성."""
        # 1) 벡터 DB 검색 (MMR 리랭킹 포함)
        results = vector_store.search(
            query=question,
            top_k=self._top_k,
            doc_type=doc_type,
            use_mmr=True,
        )

        # 2) 청크 포맷팅 및 출처 수집
        formatted_chunks, sources = self._format_chunks(results)

        # 3) 프롬프트 구성
        lang_name = LANGUAGE_NAMES.get(language, "한국어")
        retrieved_section = formatted_chunks or "※ 관련 참고자료를 찾을 수 없습니다."
        prompt = _ANSWER_PROMPT_TEMPLATE.format(
            retrieved_chunks=retrieved_section,
            question=f"({lang_name}로 답변해 주세요)\n{question}",
        )

        # 4) OpenAI GPT API 호출 (재시도 + 폴백)
        answer_text = _call_llm(
            model="gpt-4o-mini",
            system=_ANSWER_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=2048,
            fallback_text=_ANSWER_FALLBACK,
        )

        # 5) 신뢰도 판정
        count = len(results)
        confidence = "high" if count >= 3 else ("medium" if count >= 1 else "low")

        logger.info(
            "답변 생성: 청크={} | 신뢰도={} | 질문={}",
            count, confidence, question[:40],
        )
        return AnswerResult(
            question=question,
            answer=answer_text,
            language=language,
            sources=sources,
            retrieved_count=count,
            confidence=confidence,
        )

    def _format_chunks(
        self, results: list[dict]
    ) -> tuple[str, list[SourceRef]]:
        parts: list[str] = []
        seen: set[tuple] = set()
        sources: list[SourceRef] = []

        for i, r in enumerate(results, start=1):
            meta       = r.get("metadata", {})
            source_doc = meta.get("source_doc", "unknown")
            page_num   = int(meta.get("page_num", 0))
            doc_type   = meta.get("doc_type", "")
            score      = r.get("score", 0.0)
            text       = r.get("text", "").strip()

            parts.append(
                f"[{i}] 문서: {source_doc} | 페이지: {page_num} "
                f"| 유형: {doc_type} | 유사도: {score:.2f}\n{text}"
            )

            key = (source_doc, page_num)
            if key not in seen:
                seen.add(key)
                sources.append(SourceRef(
                    source_doc=source_doc,
                    page_num=page_num,
                    doc_type=doc_type,
                ))

        return "\n\n".join(parts), sources


# ---------------------------------------------------------------------------
# FAQGenerator
# ---------------------------------------------------------------------------

_FAQ_SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 FAQ를 생성하는 전문가입니다.
    주어진 컨텍스트와 주제를 바탕으로 명확하고 유용한 FAQ를 생성하세요.
    반드시 JSON 배열 형식으로만 응답하세요.
""")

_FAQ_PROMPT_TEMPLATE = textwrap.dedent("""\
    다음 주제에 대해 {language}로 FAQ {num_faqs}개를 생성해주세요.

    주제: {topic}

    {context_section}

    다음 JSON 형식으로만 응답하세요:
    [
      {{
        "question": "질문 내용",
        "answer": "답변 내용",
        "category": "카테고리명"
      }}
    ]
""")


class FAQGenerator:
    """주제 기반 FAQ 목록 생성기."""

    def generate(
        self,
        topic: str,
        num_faqs: int = 5,
        language: Language = Language.KO,
        category: str | None = None,
        use_rag: bool = True,
    ) -> list[FAQItem]:
        context_section = ""
        if use_rag:
            context = vector_store.get_context(topic, top_k=3)
            if context:
                context_section = f"참고 문서:\n{context}"

        prompt = _FAQ_PROMPT_TEMPLATE.format(
            language=LANGUAGE_NAMES.get(language, "한국어"),
            num_faqs=num_faqs,
            topic=topic,
            context_section=context_section,
        )

        text = _call_llm(
            model="gpt-4o",
            system=_FAQ_SYSTEM_PROMPT,
            user_prompt=prompt,
            max_tokens=4096,
            fallback_text="[]",
        )

        faq_data = self._parse_json(text)
        logger.info("FAQ 생성: {}개 | topic={}", len(faq_data), topic[:30])
        return [
            FAQItem(
                question=item.get("question", ""),
                answer=item.get("answer", ""),
                category=item.get("category") or category,
                language=language,
            )
            for item in faq_data
        ]

    def _parse_json(self, text: str) -> list[dict]:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1)
        try:
            data = json.loads(text.strip())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


# ---------------------------------------------------------------------------
# FAQPipeline
# ---------------------------------------------------------------------------

_QUESTION_SYSTEM = textwrap.dedent("""\
    당신은 대학 행정 FAQ 전문가입니다.
    제공된 문서 청크를 읽고 외국인 유학생이 실제로 물어볼 법한 질문을 추출하세요.
    반드시 JSON 형식으로만 응답하세요.
""")

_QUESTION_BATCH_PROMPT = textwrap.dedent("""\
    아래 대학 행정 문서 청크들에서 외국인 유학생이 자주 묻는 질문을 청크당 최대 3개 생성하세요.

    [청크 목록]
    {chunks_text}

    반드시 아래 JSON 배열 형식으로만 출력하세요:
    [
      {{"chunk_index": 0, "questions": ["질문1", "질문2"]}},
      {{"chunk_index": 1, "questions": ["질문1"]}}
    ]
""")

_DEDUP_THRESHOLD = 0.85
_CHUNK_BATCH_SIZE = 4


@dataclass
class PipelineResult:
    job_id: str
    doc_id: str
    status: str                   # pending | running | completed | failed
    department: str = ""
    total_chunks: int = 0
    raw_questions: int = 0
    unique_questions: int = 0
    saved_faqs: int = 0
    error: str = ""
    started_at: str = ""
    completed_at: str = ""


class FAQPipeline:
    """문서 → 질문 추출 → 중복 제거 → 답변 생성 → 번역 → Sheets 저장 파이프라인."""

    def __init__(self) -> None:
        self._jobs: dict[str, PipelineResult] = {}

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def get_status(self, job_id: str) -> PipelineResult | None:
        return self._jobs.get(job_id)

    def generate_faqs(
        self,
        job_id: str,
        doc_id: str,
        department: str = "",
        category_major: str = "",
        category_minor: str = "",
    ) -> PipelineResult:
        """전체 FAQ 생성 파이프라인 (동기, BackgroundTasks에서 호출).

        Steps:
          1) 벡터 DB에서 문서 청크 조회
          2) 청크 배치 → 질문 생성
          3) 중복 질문 제거 (BGE-M3 코사인 유사도)
          4) 각 질문에 RAG 답변 생성
          5) 한→중 배치 번역
          6) FAQ_Master 시트 저장
          7) Generation_Log 기록
        """
        from app.services.sheet_manager import faq_sheet_manager
        from app.services.translator import QAPair, translator

        result = PipelineResult(
            job_id=job_id,
            doc_id=doc_id,
            department=department,
            status="running",
            started_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self._jobs[job_id] = result

        try:
            # ── 1) 청크 조회 ──────────────────────────────────────────────
            chunks = vector_store.get_chunks_by_doc_id(doc_id)
            result.total_chunks = len(chunks)
            logger.info("[{}] 청크 {}개 로드", job_id, len(chunks))

            if not chunks:
                raise ValueError(f"doc_id='{doc_id}'에 해당하는 청크가 없습니다.")

            # ── 2) 질문 생성 ──────────────────────────────────────────────
            all_questions = self._extract_questions(chunks)
            result.raw_questions = len(all_questions)
            logger.info("[{}] 원시 질문 {}개 생성", job_id, len(all_questions))

            if not all_questions:
                raise ValueError("청크에서 질문을 추출할 수 없습니다.")

            # ── 3) 중복 제거 ──────────────────────────────────────────────
            unique_qs = self._deduplicate(all_questions)
            result.unique_questions = len(unique_qs)
            logger.info("[{}] 중복 제거 후 {}개", job_id, len(unique_qs))

            # ── 4) RAG 답변 생성 ──────────────────────────────────────────
            source_doc = chunks[0]["metadata"].get("source_doc", doc_id)
            doc_type   = chunks[0]["metadata"].get("doc_type", "")
            qa_ko: list[tuple[str, str]] = []

            for q in unique_qs:
                try:
                    ans = answer_generator.generate(q, doc_type=doc_type)
                    if (
                        ans.answer
                        and "참고자료에서 찾을 수 없습니다" not in ans.answer
                        and ans.answer != _ANSWER_FALLBACK
                    ):
                        qa_ko.append((q, ans.answer))
                except Exception as exc:
                    logger.warning("[{}] 답변 생성 건너뜀: {} — {}", job_id, q[:30], exc)

            logger.info("[{}] 답변 생성 완료: {}건", job_id, len(qa_ko))

            # ── 5) 한→중 배치 번역 ────────────────────────────────────────
            pairs_ko = [QAPair(question_ko=q, answer_ko=a) for q, a in qa_ko]
            translated = translator.translate_batch(pairs_ko) if pairs_ko else []

            # ── 6) FAQ_Master 저장 ────────────────────────────────────────
            saved = 0
            for t in translated:
                try:
                    faq_sheet_manager.add_faq(
                        category_major=category_major,
                        category_minor=category_minor,
                        question_ko=t.question_ko,
                        answer_ko=t.answer_ko,
                        question_zh=t.question_zh,
                        answer_zh=t.answer_zh,
                        source=source_doc,
                        department=department,
                    )
                    saved += 1
                except Exception as e:
                    logger.warning("[{}] FAQ 저장 실패: {}", job_id, e)

            result.saved_faqs = saved
            result.status = "completed"
            logger.info("[{}] 완료 — FAQ {}건 저장", job_id, saved)

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.error("[{}] 파이프라인 실패: {}", job_id, e, exc_info=True)

        finally:
            result.completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._jobs[job_id] = result

            # ── 7) Generation_Log 기록 ────────────────────────────────────
            try:
                from app.services.sheet_manager import faq_sheet_manager as _sm
                _sm.save_generation_log(
                    job_id=job_id,
                    doc_id=doc_id,
                    department=department,
                    status=result.status,
                    total_chunks=result.total_chunks,
                    raw_questions=result.raw_questions,
                    unique_questions=result.unique_questions,
                    saved_faqs=result.saved_faqs,
                    started_at=result.started_at,
                    completed_at=result.completed_at,
                    error_message=result.error,
                )
            except Exception as log_err:
                logger.warning("[{}] 로그 저장 실패: {}", job_id, log_err)

        return result

    # ------------------------------------------------------------------
    # 내부: 질문 추출
    # ------------------------------------------------------------------

    def _extract_questions(self, chunks: list[dict]) -> list[str]:
        """청크 배치를 Claude에 전달해 질문 목록 추출 (재시도 포함)."""
        questions: list[str] = []

        for i in range(0, len(chunks), _CHUNK_BATCH_SIZE):
            batch = chunks[i : i + _CHUNK_BATCH_SIZE]
            chunks_text = "\n\n".join(
                f"[청크 {j}]\n{c['text'][:600]}"
                for j, c in enumerate(batch)
            )
            prompt = _QUESTION_BATCH_PROMPT.format(chunks_text=chunks_text)

            text = _call_llm(
                model="gpt-4o-mini",
                system=_QUESTION_SYSTEM,
                user_prompt=prompt,
                max_tokens=1024,
                fallback_text="[]",
            )
            batch_qs = self._parse_question_json(text)
            questions.extend(batch_qs)
            logger.debug("질문 추출 배치 {}: {}개", i // _CHUNK_BATCH_SIZE, len(batch_qs))

        return questions

    def _parse_question_json(self, text: str) -> list[str]:
        text = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return []
        try:
            data = json.loads(match.group())
            questions: list[str] = []
            for item in data:
                questions.extend(item.get("questions", []))
            return [q.strip() for q in questions if isinstance(q, str) and q.strip()]
        except json.JSONDecodeError:
            return []

    # ------------------------------------------------------------------
    # 내부: 중복 제거 (BGE-M3 코사인 유사도)
    # ------------------------------------------------------------------

    def _deduplicate(self, questions: list[str]) -> list[str]:
        """코사인 유사도 기반 그리디 중복 제거."""
        if not questions:
            return []

        vectors = np.array(vector_store.embed_texts(questions), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True).clip(min=1e-9)
        vectors = vectors / norms

        selected_idx: list[int] = [0]
        for i in range(1, len(vectors)):
            selected_vecs = vectors[selected_idx]
            sims = selected_vecs @ vectors[i]
            if float(sims.max()) < _DEDUP_THRESHOLD:
                selected_idx.append(i)

        return [questions[i] for i in selected_idx]


# ---------------------------------------------------------------------------
# 싱글턴
# ---------------------------------------------------------------------------

faq_generator    = FAQGenerator()
answer_generator = AnswerGenerator(top_k=5)
faq_pipeline     = FAQPipeline()
