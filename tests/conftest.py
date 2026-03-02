"""pytest 공유 픽스처 및 Mock 설정.

외부 의존성 (Google Sheets, Anthropic API, ChromaDB) 을 모두 Mock으로 대체해
실제 네트워크 호출 없이 통합 테스트를 실행합니다.

실제 서비스 연동 테스트가 필요하면:
    pytest -m integration --no-header -rN
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ── 공통 경로 ──────────────────────────────────────────────────────────────
FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_TXT   = FIXTURES_DIR / "sample.txt"


# ===========================================================================
# 환경 변수 픽스처 (앱 로드 전 반드시 설정)
# ===========================================================================

@pytest.fixture(scope="session", autouse=True)
def mock_env(monkeypatch_session):
    """필수 환경 변수를 테스트용 더미 값으로 설정."""
    monkeypatch_session.setenv("ANTHROPIC_API_KEY",              "test-anthropic-key")
    monkeypatch_session.setenv("SPREADSHEET_ID",                 "test-sheet-id")
    monkeypatch_session.setenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "tests/fixtures/fake_creds.json")
    monkeypatch_session.setenv("CHROMA_PERSIST_DIR",             "/tmp/test_chroma")
    monkeypatch_session.setenv("EMBEDDING_MODEL_NAME",           "BAAI/bge-m3")
    monkeypatch_session.setenv("CACHE_TTL_SECONDS",              "0")   # 캐시 즉시 만료


@pytest.fixture(scope="session")
def monkeypatch_session(request):
    """session-scoped monkeypatch."""
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


# ===========================================================================
# Google Sheets Mock
# ===========================================================================

FAKE_FAQ_ROW = {
    "고유번호":          "faq-001",
    "카테고리(대분류)": "학사",
    "카테고리(중분류)": "수강신청",
    "질문(한국어)":     "수강신청은 어떻게 하나요?",
    "답변(한국어)":     "포털시스템에서 개강 2주 전에 신청하세요.",
    "질문(중국어)":     "如何选课？",
    "답변(중국어)":     "请在开学两周前通过门户系统申请。",
    "출처":             "학사안내.pdf",
    "상태":             "게시중",
    "생성부서":         "학사팀",
    "적용범위":         "전체",
    "생성일":           "2024-01-01 09:00:00",
    "수정일":           "2024-01-02 10:00:00",
    "우선순위":         5,
    "조회수":           10,
    "도움됨비율":       80.0,
}


@pytest.fixture
def mock_sheet_manager():
    """FAQSheetManager 전체 Mock."""
    mgr = MagicMock()
    mgr.get_published_faqs.return_value   = [FAKE_FAQ_ROW]
    mgr.get_faq_by_id.return_value        = FAKE_FAQ_ROW
    mgr.add_faq.return_value              = "faq-" + str(uuid.uuid4())[:8]
    mgr.increment_view_count.return_value = True
    mgr.flush_view_counts.return_value    = 0
    mgr.save_user_feedback.return_value   = "fb-" + str(uuid.uuid4())[:8]
    mgr.save_source_document.return_value = None
    mgr.save_generation_log.return_value  = None
    mgr.record_feedback.return_value      = True
    return mgr


# ===========================================================================
# ChromaDB / VectorStore Mock
# ===========================================================================

FAKE_CHUNK = {
    "text": "수강신청은 매 학기 개강 2주 전 포털시스템(portal.kmu.ac.kr)에서 진행한다.",
    "metadata": {
        "source_doc":  "sample.txt",
        "page_num":    1,
        "chunk_index": 0,
        "doc_type":    "안내",
        "document_id": "doc-test-001",
    },
    "score": 0.92,
}


@pytest.fixture
def mock_vector_store():
    vs = MagicMock()
    vs.add_documents.return_value         = 3
    vs.search.return_value                = [FAKE_CHUNK]
    vs.get_chunks_by_doc_id.return_value  = [FAKE_CHUNK]
    vs.delete_collection.return_value     = 3
    vs.get_context.return_value           = FAKE_CHUNK["text"]
    vs.embed_texts.return_value           = [[0.1] * 128]
    return vs


# ===========================================================================
# Anthropic API Mock
# ===========================================================================

def _make_claude_response(text: str):
    """anthropic.Message 형태의 Mock 객체 생성."""
    content = MagicMock()
    content.text = text
    msg = MagicMock()
    msg.content = [content]
    return msg


@pytest.fixture
def mock_anthropic():
    client = MagicMock()
    client.messages.create.side_effect = lambda **kw: _make_claude_response(
        _fake_claude_response(kw.get("system", ""), kw.get("messages", []))
    )
    return client


def _fake_claude_response(system: str, messages: list) -> str:
    """시스템 프롬프트에 따라 적절한 더미 응답 반환."""
    user_msg = messages[-1]["content"] if messages else ""
    if "JSON" in system or "json" in str(user_msg):
        return '[{"question":"수강신청 방법은?","answer":"포털에서 신청하세요.","category":"학사"}]'
    if "번역" in system or "翻译" in system:
        return '{"question_zh":"如何选课？","answer_zh":"请通过门户网站申请。"}'
    if "FAQ" in system and "배열" in system:
        return '[{"index":0,"question_zh":"如何选课？","answer_zh":"请申请。"}]'
    return "수강신청은 포털시스템에서 진행합니다. [출처: 학사안내.pdf, 제3조]"


# ===========================================================================
# BGE-M3 임베딩 Mock (sentence-transformers 로드 방지)
# ===========================================================================

@pytest.fixture(autouse=True)
def mock_embedding_fn(mock_vector_store):
    """BGEM3EmbeddingFunction.__call__ 을 Mock으로 대체."""
    with patch(
        "app.services.rag_engine.BGEM3EmbeddingFunction.__call__",
        return_value=[[0.1] * 768],
    ):
        yield


# ===========================================================================
# FastAPI TestClient (모든 외부 의존성 패치 후 생성)
# ===========================================================================

@pytest.fixture
def client(mock_sheet_manager, mock_vector_store, mock_anthropic):
    """모든 외부 서비스를 Mock으로 교체한 TestClient."""
    with (
        patch("app.services.sheet_manager.faq_sheet_manager", mock_sheet_manager),
        patch("app.services.rag_engine.vector_store",          mock_vector_store),
        patch("app.services.faq_generator.vector_store",       mock_vector_store),
        patch("app.services.faq_generator._anthropic_client",  mock_anthropic),
        patch("app.services.translator.Translator._call_api",
              side_effect=lambda prompt, max_tokens:
                  '{"question_zh":"如何选课？","answer_zh":"请申请。"}'
                  if "{" in prompt else
                  '[{"index":0,"question_zh":"如何选课？","answer_zh":"请申请。"}]'),
        patch("app.services.chat_service.vector_store",        mock_vector_store),
        patch("app.services.chat_service.faq_sheet_manager",   mock_sheet_manager),
        patch("app.services.chat_service.ChatService._call_claude",
              return_value="수강신청은 포털에서 진행합니다. [출처: 학사안내.pdf]"),
    ):
        from app.main import app
        yield TestClient(app, raise_server_exceptions=True)


# ===========================================================================
# 샘플 파일 픽스처
# ===========================================================================

@pytest.fixture
def sample_txt_bytes() -> bytes:
    return SAMPLE_TXT.read_bytes()


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """최소한의 유효 PDF 바이트 (실제 파싱 테스트용)."""
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), SAMPLE_TXT.read_text(encoding="utf-8"))
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception:
        return b"%PDF-1.4 minimal"


@pytest.fixture
def doc_id() -> str:
    return "doc-test-" + str(uuid.uuid4())[:8]


@pytest.fixture
def faq_id() -> str:
    return "faq-001"
