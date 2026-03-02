"""한국어 → 중국어(简体中文) 번역 서비스.

Translator 클래스:
  - translate_qa()    : 질문/답변 쌍 단건 번역
  - translate_batch() : 여러 쌍 배치 번역 (단일 API 호출)
  - translate()       : 범용 텍스트 번역 (하위 호환)
"""

from __future__ import annotations

import json
import re
import textwrap
import time
from dataclasses import dataclass

from openai import OpenAI, RateLimitError, APIStatusError
from loguru import logger

from app.config import settings
from app.models.schemas import Language

_MAX_RETRIES = 3
_RETRY_DELAY = 1.0


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class QAPair:
    question_ko: str
    answer_ko: str


@dataclass
class QAPairZH:
    question_ko: str
    answer_ko: str
    question_zh: str
    answer_zh: str


# ---------------------------------------------------------------------------
# 프롬프트
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""\
    당신은 한국 대학교 행정 문서 번역 전문가입니다.
    한국어 FAQ를 중국어(简体中文)로 번역합니다.
    반드시 지시된 규칙을 따르고 지정된 JSON 형식으로만 출력하세요.
""")

# 단건 번역 프롬프트
_SINGLE_PROMPT = textwrap.dedent("""\
    한국 대학교 행정 문서의 FAQ를 중국어(简体中文)로 번역하세요.

    [규칙]
    1. 대학 행정 용어는 중국 대학 기준으로 번역
       예) 수강신청 → 选课, 학점 → 学分, 장학금 → 奖学金
    2. 고유명사(계명대학교, 장춘대학 등)는 원문 유지
    3. 한국 특유의 제도는 괄호 안에 설명 추가
       예) 수능(韩国大学修学能力试验) → 수능(韩国大学入学考试)
    4. 자연스러운 중국어 표현 사용
    5. 존댓말·경어체는 정중한 중국어 표현으로 전환

    [원문]
    질문: {question_ko}
    답변: {answer_ko}

    반드시 아래 JSON 형식으로만 출력하세요. 다른 텍스트는 절대 포함하지 마세요.
    {{
      "question_zh": "번역된 질문",
      "answer_zh": "번역된 답변"
    }}
""")

# 배치 번역 프롬프트
_BATCH_PROMPT_HEADER = textwrap.dedent("""\
    한국 대학교 행정 문서의 FAQ 목록을 중국어(简体中文)로 번역하세요.

    [규칙]
    1. 대학 행정 용어는 중국 대학 기준으로 번역
       예) 수강신청 → 选课, 학점 → 学分, 장학금 → 奖学金
    2. 고유명사(계명대학교, 장춘대학 등)는 원문 유지
    3. 한국 특유의 제도는 괄호 안에 설명 추가
       예) 수능 → 수능(韩国大学入学考试)
    4. 자연스러운 중국어 표현 사용
    5. 존댓말·경어체는 정중한 중국어 표현으로 전환

    [원문 목록]
    {items}

    반드시 아래 JSON 배열 형식으로만 출력하세요. 항목 순서는 원문과 동일해야 합니다.
    [
      {{"index": 0, "question_zh": "...", "answer_zh": "..."}},
      {{"index": 1, "question_zh": "...", "answer_zh": "..."}}
    ]
""")

# 범용 번역 프롬프트 (translate() 메서드용)
_GENERIC_PROMPT = textwrap.dedent("""\
    한국 대학교 행정 문서를 중국어(简体中文)로 번역하세요.
    번역문만 출력하고 다른 설명은 포함하지 마세요.

    [원문]
    {text}
""")


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------

class Translator:
    """한국 대학 행정 FAQ 전문 번역기."""

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.openai_api_key)

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def translate_qa(
        self,
        question_ko: str,
        answer_ko: str,
    ) -> tuple[str, str]:
        """질문/답변 쌍 단건 번역.

        Args:
            question_ko: 한국어 질문
            answer_ko:   한국어 답변

        Returns:
            (question_zh, answer_zh)
        """
        prompt = _SINGLE_PROMPT.format(
            question_ko=question_ko.strip(),
            answer_ko=answer_ko.strip(),
        )
        raw = self._call_api(prompt, max_tokens=2048)
        data = self._parse_json_object(raw)
        return (
            data.get("question_zh", ""),
            data.get("answer_zh", ""),
        )

    def translate_batch(
        self,
        qa_pairs: list[QAPair],
    ) -> list[QAPairZH]:
        """여러 질문/답변 쌍을 단일 API 호출로 배치 번역.

        Args:
            qa_pairs: QAPair 목록

        Returns:
            QAPairZH 목록 (원문 + 번역문 포함, 입력 순서 보존)
        """
        if not qa_pairs:
            return []

        # 번역 요청 JSON 직렬화
        items_json = json.dumps(
            [
                {"index": i, "question_ko": p.question_ko, "answer_ko": p.answer_ko}
                for i, p in enumerate(qa_pairs)
            ],
            ensure_ascii=False,
            indent=2,
        )

        prompt = _BATCH_PROMPT_HEADER.format(items=items_json)
        # 배치 크기에 비례해 토큰 여유 확보 (쌍당 최대 600토큰 추정)
        max_tokens = min(4096, 600 * len(qa_pairs) + 512)
        raw = self._call_api(prompt, max_tokens=max_tokens)

        translated = self._parse_json_array(raw)
        # index 기준 정렬 후 원본과 병합
        translated.sort(key=lambda x: x.get("index", 0))

        results: list[QAPairZH] = []
        for i, pair in enumerate(qa_pairs):
            t = translated[i] if i < len(translated) else {}
            results.append(QAPairZH(
                question_ko=pair.question_ko,
                answer_ko=pair.answer_ko,
                question_zh=t.get("question_zh", ""),
                answer_zh=t.get("answer_zh", ""),
            ))
        return results

    def translate(
        self,
        text: str,
        source_language: Language = Language.KO,
        target_language: Language = Language.ZH,
    ) -> str:
        """범용 텍스트 번역 (하위 호환 메서드).

        한→중 이외의 방향은 간단한 프롬프트로 처리합니다.
        """
        if source_language == target_language:
            return text

        if source_language == Language.KO and target_language == Language.ZH:
            prompt = _GENERIC_PROMPT.format(text=text.strip())
        else:
            src = source_language.value
            tgt = target_language.value
            prompt = (
                f"{src}에서 {tgt}로 다음 텍스트를 번역하세요.\n"
                f"번역문만 출력하세요.\n\n원문:\n{text}"
            )

        return self._call_api(prompt, max_tokens=2048)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """OpenAI GPT API 호출 with 3회 재시도."""
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = self._client.chat.completions.create(
                    model="gpt-4o-mini",
                    max_tokens=max_tokens,
                    temperature=0.3,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                )
                return response.choices[0].message.content.strip()
            except (RateLimitError, APIStatusError) as exc:
                delay = _RETRY_DELAY * (2 ** (attempt - 1))
                logger.warning("번역 API 오류 (시도 {}/{}) — {}s 후 재시도: {}", attempt, _MAX_RETRIES, delay, exc)
                last_exc = exc
                time.sleep(delay)
            except Exception as exc:
                logger.error("번역 API 예외: {}", exc)
                return ""
        logger.error("번역 API {}회 재시도 모두 실패: {}", _MAX_RETRIES, last_exc)
        return ""

    def _parse_json_object(self, text: str) -> dict:
        """응답에서 JSON 오브젝트 {} 를 추출·파싱."""
        # 코드 블록 제거
        text = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        # 첫 번째 { ... } 구간 추출
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {}
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return {}

    def _parse_json_array(self, text: str) -> list[dict]:
        """응답에서 JSON 배열 [] 를 추출·파싱."""
        text = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        match = re.search(r"\[[\s\S]*\]", text)
        if not match:
            return []
        try:
            data = json.loads(match.group())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


# ---------------------------------------------------------------------------
# 싱글턴
# ---------------------------------------------------------------------------

translator = Translator()
