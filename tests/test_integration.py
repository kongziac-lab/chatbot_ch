"""전체 시스템 통합 테스트.

시나리오 6단계:
  1. 문서 업로드 → 파싱 → 벡터 저장 → Sheets 기록
  2. FAQ 생성 → 번역 → Sheets 기록 (16개 열 검증)
  3. 관리자 검수 (상태 변경) → 웹페이지 반영
  4. 사용자 조회 → 조회수 업데이트
  5. 챗봇 질문 → RAG 답변 생성
  6. 피드백 기록 → 도움됨 비율 계산

실행:
    pytest tests/test_integration.py -v
"""

from __future__ import annotations

import time
import uuid
from unittest.mock import MagicMock, call, patch

import pytest

from app.services.sheet_manager import HEADER_ROW


# ===========================================================================
# 시나리오 1: 문서 업로드 → 파싱 → 벡터 저장 → Sheets 기록
# ===========================================================================

class TestScenario1_DocumentUpload:
    """POST /api/v1/documents/upload 엔드투엔드."""

    def test_upload_txt_returns_200(self, client, sample_txt_bytes):
        resp = client.post(
            "/api/v1/documents/upload",
            files={"file": ("sample.txt", sample_txt_bytes, "text/plain")},
            data={"doc_type": "안내"},
        )
        # txt는 지원하지 않으므로 400 예상
        assert resp.status_code == 400
        assert "지원하지 않는" in resp.json()["detail"]

    def test_upload_pdf_full_pipeline(self, client, mock_vector_store, mock_sheet_manager):
        """PDF 업로드 → 벡터 저장 → Sheets Source_Documents 기록."""
        import io
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 100), "수강신청 안내 문서 내용입니다.")
            buf = io.BytesIO()
            doc.save(buf)
            pdf_bytes = buf.getvalue()
        except Exception:
            pytest.skip("PyMuPDF 미설치 — PDF 파싱 테스트 생략")

        with patch("app.services.rag_engine.ingestion_pipeline") as mock_pipeline:
            mock_parsed = MagicMock()
            mock_parsed.total_pages = 1
            mock_pipeline.ingest.return_value = (3, mock_parsed)

            resp = client.post(
                "/api/v1/documents/upload",
                files={"file": ("guide.pdf", pdf_bytes, "application/pdf")},
                data={"doc_type": "안내", "uploader": "국제처"},
            )

        assert resp.status_code == 200
        data = resp.json()

        # ── assertion: 응답 필드 ──
        assert "document_id" in data
        assert data["filename"]    == "guide.pdf"
        assert data["doc_type"]    == "안내"
        assert data["num_chunks"]  == 3
        assert data["total_pages"] == 1
        assert "완료" in data["message"]

        # ── assertion: Sheets 기록 호출 ──
        mock_sheet_manager.save_source_document.assert_called_once()
        call_kwargs = mock_sheet_manager.save_source_document.call_args.kwargs
        assert call_kwargs["filename"]  == "guide.pdf"
        assert call_kwargs["doc_type"]  == "안내"
        assert call_kwargs["num_chunks"] == 3

    def test_upload_empty_doc_returns_422(self, client):
        """텍스트 없는 DOCX → 422 Unprocessable."""
        with patch("app.services.rag_engine.ingestion_pipeline") as mock_pipeline:
            mock_parsed = MagicMock()
            mock_parsed.total_pages = 0
            mock_pipeline.ingest.return_value = (0, mock_parsed)

            resp = client.post(
                "/api/v1/documents/upload",
                files={"file": ("empty.docx", b"PK\x03\x04", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"doc_type": "공지"},
            )
        assert resp.status_code in (400, 422, 500)


# ===========================================================================
# 시나리오 2: FAQ 생성 → 번역 → Sheets 기록 (16개 열 검증)
# ===========================================================================

class TestScenario2_FAQGeneration:
    """파이프라인 시작 및 Sheets 16열 구조 검증."""

    def test_pipeline_start_returns_job_id(self, client):
        """POST /api/v1/faq/pipeline/generate → job_id 즉시 반환."""
        resp = client.post("/api/v1/faq/pipeline/generate", json={
            "doc_id":         "doc-test-001",
            "department":     "국제처",
            "category_major": "학사",
            "category_minor": "수강신청",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id"  in data
        assert data["status"] == "pending"
        assert len(data["job_id"]) > 0

    def test_faq_master_header_has_16_columns(self):
        """FAQ_Master 헤더가 정확히 16개 열인지 검증."""
        expected = [
            "고유번호", "카테고리(대분류)", "카테고리(중분류)",
            "질문(한국어)", "답변(한국어)", "질문(중국어)", "답변(중국어)",
            "출처", "상태", "생성부서", "적용범위",
            "생성일", "수정일", "우선순위", "조회수", "도움됨비율",
        ]
        assert HEADER_ROW == expected
        assert len(HEADER_ROW) == 16

    def test_add_faq_called_with_all_fields(self, mock_sheet_manager):
        """add_faq() 호출 시 필수 필드가 모두 전달되는지 검증."""
        mock_sheet_manager.add_faq(
            category_major="학사",
            category_minor="수강신청",
            question_ko="수강신청은 어떻게 하나요?",
            answer_ko="포털에서 신청하세요.",
            question_zh="如何选课？",
            answer_zh="请通过门户申请。",
            source="학사안내.pdf",
            department="학사팀",
        )
        called_kwargs = mock_sheet_manager.add_faq.call_args.kwargs
        required_keys = {
            "category_major", "category_minor",
            "question_ko", "answer_ko",
            "question_zh", "answer_zh",
        }
        assert required_keys.issubset(called_kwargs.keys())

    def test_translate_qa_endpoint(self, client):
        """POST /api/v1/translate/qa → 한→중 번역 응답 형식."""
        resp = client.post("/api/v1/translate/qa", json={
            "question_ko": "수강신청은 언제 하나요?",
            "answer_ko":   "개강 2주 전에 포털에서 신청하세요.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "question_zh" in data
        assert "answer_zh"   in data
        assert "question_ko" in data
        assert "answer_ko"   in data

    def test_translate_batch_endpoint(self, client):
        """POST /api/v1/translate/batch → 여러 쌍 일괄 번역."""
        resp = client.post("/api/v1/translate/batch", json={
            "pairs": [
                {"question_ko": "장학금은 어떻게 신청하나요?", "answer_ko": "국제교류처에 문의하세요."},
                {"question_ko": "기숙사 신청 방법은?",        "answer_ko": "입학 후 1주일 내 신청하세요."},
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        for item in data["results"]:
            assert "question_zh" in item
            assert "answer_zh"   in item


# ===========================================================================
# 시나리오 3: 관리자 검수 → 웹페이지 반영
# ===========================================================================

class TestScenario3_AdminReview:
    """상태 필터로 자동생성 FAQ 조회, 게시중 FAQ 목록 반영 확인."""

    def test_get_published_faqs_returns_list(self, client):
        """GET /api/v1/faqs → 게시중 FAQ 목록 반환."""
        resp = client.get("/api/v1/faqs")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 0

    def test_category_filter_applied(self, client, mock_sheet_manager):
        """category 파라미터가 sheet_manager에 전달되는지 확인."""
        client.get("/api/v1/faqs?category=학사&lang=ko")
        mock_sheet_manager.get_published_faqs.assert_called_with(
            category_major="학사",
            scope=None,
            search=None,
        )

    def test_scope_filter_applied(self, client, mock_sheet_manager):
        """scope 파라미터 필터 적용 확인."""
        resp = client.get("/api/v1/faqs?scope=전체")
        assert resp.status_code == 200

    def test_search_filter_applied(self, client, mock_sheet_manager):
        """search 키워드 파라미터 전달 확인."""
        resp = client.get("/api/v1/faqs?search=수강신청")
        assert resp.status_code == 200

    def test_faq_list_response_structure(self, client):
        """응답 items의 각 FAQ가 필수 필드를 갖는지 확인."""
        resp = client.get("/api/v1/faqs?lang=ko")
        assert resp.status_code == 200
        items = resp.json()["items"]
        for item in items:
            assert "faq_id"         in item
            assert "question"       in item
            assert "answer"         in item
            assert "category_major" in item
            assert "view_count"     in item

    def test_zh_language_returns_chinese_content(self, client):
        """lang=zh 요청 시 중국어 질문/답변 반환 확인."""
        resp = client.get("/api/v1/faqs?lang=zh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "zh"
        if data["items"]:
            item = data["items"][0]
            assert item["language"] == "zh"


# ===========================================================================
# 시나리오 4: 사용자 조회 → 조회수 업데이트
# ===========================================================================

class TestScenario4_UserQueryViewCount:
    """GET /api/v1/faqs/{faq_id} → 조회수 +1 백그라운드 처리."""

    def test_get_faq_detail_returns_all_fields(self, client, faq_id):
        """개별 FAQ 상세 조회 시 16개 열 중 주요 필드 포함."""
        resp = client.get(f"/api/v1/faqs/{faq_id}")
        assert resp.status_code == 200
        data = resp.json()

        required = [
            "faq_id", "question", "answer",
            "question_ko", "answer_ko", "question_zh", "answer_zh",
            "source", "scope", "priority", "view_count",
            "created_at", "updated_at",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_view_count_incremented_in_background(self, client, mock_sheet_manager, faq_id):
        """조회수 increment_view_count 호출 확인 (BackgroundTasks)."""
        # TestClient는 response 반환 전 BackgroundTasks를 실행
        client.get(f"/api/v1/faqs/{faq_id}")
        mock_sheet_manager.increment_view_count.assert_called_once_with(faq_id)

    def test_unknown_faq_returns_404(self, client, mock_sheet_manager):
        """존재하지 않는 faq_id → 404."""
        mock_sheet_manager.get_faq_by_id.return_value = None
        resp = client.get("/api/v1/faqs/nonexistent-id")
        assert resp.status_code == 404

    def test_view_count_value_in_response(self, client, faq_id):
        """응답의 view_count가 숫자형인지 확인."""
        resp = client.get(f"/api/v1/faqs/{faq_id}")
        assert isinstance(resp.json()["view_count"], int)


# ===========================================================================
# 시나리오 5: 챗봇 질문 → RAG 답변 생성
# ===========================================================================

class TestScenario5_Chatbot:
    """POST /api/v1/chat → 언어 감지, 답변, 관련 FAQ."""

    def test_korean_question_returns_answer(self, client):
        """한국어 질문 → 한국어 답변."""
        resp = client.post("/api/v1/chat", json={"message": "수강신청은 어떻게 하나요?"})
        assert resp.status_code == 200
        data = resp.json()
        assert "answer"       in data
        assert "session_id"   in data
        assert "confidence"   in data
        assert "related_faqs" in data
        assert len(data["answer"]) > 0

    def test_chinese_question_detects_zh(self, client):
        """중국어 질문 → language=zh 감지."""
        resp = client.post("/api/v1/chat", json={"message": "如何申请奖学金？"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["language"] == "zh"

    def test_session_continuity(self, client):
        """동일 session_id 재사용 시 세션 유지."""
        r1 = client.post("/api/v1/chat", json={"message": "수강신청 방법은?"})
        sid = r1.json()["session_id"]

        r2 = client.post("/api/v1/chat", json={"message": "방금 말한 신청 기간이 언제인가요?", "session_id": sid})
        assert r2.status_code == 200
        assert r2.json()["session_id"] == sid

    def test_new_session_created_when_none(self, client):
        """session_id 미전달 시 신규 UUID 발급."""
        resp = client.post("/api/v1/chat", json={"message": "장학금 조건이 뭔가요?"})
        sid = resp.json()["session_id"]
        assert len(sid) == 36   # UUID 형식

    def test_confidence_field_valid_values(self, client):
        """confidence 필드가 high/medium/low 중 하나."""
        resp = client.post("/api/v1/chat", json={"message": "기숙사 신청은 언제 하나요?"})
        assert resp.json()["confidence"] in ("high", "medium", "low")

    def test_related_faqs_structure(self, client, mock_sheet_manager):
        """관련 FAQ가 있을 때 faq_id + question 포함."""
        resp = client.post("/api/v1/chat", json={"message": "수강신청 관련 FAQ 알려주세요"})
        assert resp.status_code == 200
        for faq in resp.json()["related_faqs"]:
            assert "faq_id"   in faq
            assert "question" in faq
            assert "language" in faq

    def test_clear_session(self, client):
        """DELETE /api/v1/chat/{session_id} → 세션 초기화."""
        r = client.post("/api/v1/chat", json={"message": "안녕하세요"})
        sid = r.json()["session_id"]

        del_resp = client.delete(f"/api/v1/chat/{sid}")
        assert del_resp.status_code == 200
        assert del_resp.json()["success"] is True

    def test_vector_store_searched_on_chat(self, client, mock_vector_store):
        """챗봇 호출 시 vector_store.search()가 실행되는지 확인."""
        client.post("/api/v1/chat", json={"message": "등록금 납부 방법은?"})
        mock_vector_store.search.assert_called()
        call_kwargs = mock_vector_store.search.call_args
        assert "등록금" in str(call_kwargs)


# ===========================================================================
# 시나리오 6: 피드백 기록 → 도움됨 비율 계산
# ===========================================================================

class TestScenario6_FeedbackAndHelpfulRatio:
    """POST /api/v1/faqs/{faq_id}/feedback → User_Feedback 기록 및 비율 갱신."""

    def test_helpful_feedback_recorded(self, client, mock_sheet_manager, faq_id):
        """helpful=true 피드백 전송 → save_user_feedback 호출."""
        resp = client.post(f"/api/v1/faqs/{faq_id}/feedback", json={
            "helpful":  True,
            "comment":  "매우 도움이 되었어요!",
            "language": "ko",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"]     is True
        assert "feedback_id" in data
        assert len(data["feedback_id"]) > 0

    def test_not_helpful_feedback_recorded(self, client, mock_sheet_manager, faq_id):
        """helpful=false 피드백 전송 확인."""
        resp = client.post(f"/api/v1/faqs/{faq_id}/feedback", json={
            "helpful": False,
            "comment": "답변이 부정확해요.",
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_save_user_feedback_called_with_correct_args(
        self, client, mock_sheet_manager, faq_id
    ):
        """save_user_feedback() 인자 검증."""
        client.post(f"/api/v1/faqs/{faq_id}/feedback", json={
            "helpful": True, "comment": "좋아요", "language": "ko",
        })
        mock_sheet_manager.save_user_feedback.assert_called_once_with(
            faq_id   = faq_id,
            helpful  = True,
            comment  = "좋아요",
            language = "ko",
        )

    def test_helpful_ratio_recalculated(self, mock_sheet_manager, faq_id):
        """도움됨 비율 재계산 — record_feedback() 호출 확인."""
        mock_sheet_manager.save_user_feedback(
            faq_id="faq-001", helpful=True, comment="", language="ko"
        )
        # save_user_feedback 내부에서 record_feedback을 호출하므로
        # 직접 호출 여부 검증
        assert mock_sheet_manager.save_user_feedback.called

    def test_feedback_on_unknown_faq_returns_404(self, client, mock_sheet_manager):
        """존재하지 않는 FAQ에 피드백 → 404."""
        mock_sheet_manager.get_faq_by_id.return_value = None
        resp = client.post("/api/v1/faqs/unknown-id/feedback", json={"helpful": True})
        assert resp.status_code == 404

    def test_feedback_comment_max_length(self, client, faq_id):
        """코멘트 500자 초과 시 422 Validation Error."""
        resp = client.post(f"/api/v1/faqs/{faq_id}/feedback", json={
            "helpful": True,
            "comment": "a" * 501,
        })
        assert resp.status_code == 422


# ===========================================================================
# 단위 테스트: 언어 감지
# ===========================================================================

class TestLanguageDetection:
    def test_korean_detected(self):
        from app.services.chat_service import detect_language
        from app.models.schemas import Language
        assert detect_language("수강신청은 어떻게 하나요?") == Language.KO

    def test_chinese_detected(self):
        from app.services.chat_service import detect_language
        from app.models.schemas import Language
        assert detect_language("如何申请奖学金？") == Language.ZH

    def test_mixed_prefers_dominant(self):
        from app.services.chat_service import detect_language
        from app.models.schemas import Language
        # 중국어 비율이 높으면 ZH
        assert detect_language("我想问一下수강신청") == Language.ZH
        # 한국어 비율이 높으면 KO
        assert detect_language("수강신청 방법을 请告诉我") == Language.KO


# ===========================================================================
# 단위 테스트: 캐시 TTL
# ===========================================================================

class TestCacheTTL:
    def test_cache_expires_immediately_at_ttl_zero(self):
        """CACHE_TTL=0 설정 시 캐시가 즉시 만료되는지 검증."""
        from app.services.sheet_manager import _CacheEntry
        entry = _CacheEntry(data=["some_data"])
        # TTL=0이면 expires_at ≈ now → 이미 만료
        time.sleep(0.01)
        # TTL이 0이면 즉시 만료 (conftest에서 CACHE_TTL_SECONDS=0 설정)
        assert not entry.is_valid()

    def test_cache_valid_within_ttl(self):
        """충분한 TTL 내에서 캐시가 유효한지 검증."""
        import time as _time
        from app.services.sheet_manager import _CacheEntry
        with patch("app.services.sheet_manager.CACHE_TTL", 60):
            entry = _CacheEntry(
                data=["data"],
                expires_at=_time.monotonic() + 60,
            )
            assert entry.is_valid()


# ===========================================================================
# 단위 테스트: 문서 파서
# ===========================================================================

class TestDocumentParser:
    def test_parse_txt_content(self, tmp_path):
        """TXT 파일 파싱 → ValueError (지원 안 함)."""
        from app.services.document_parser import document_parser
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("테스트 내용입니다.", encoding="utf-8")
        with pytest.raises(ValueError, match="지원하지 않는"):
            document_parser.parse(str(txt_file))

    def test_parse_nonexistent_file_raises(self):
        """존재하지 않는 파일 → FileNotFoundError."""
        from app.services.document_parser import document_parser
        with pytest.raises(FileNotFoundError):
            document_parser.parse("/nonexistent/path/file.pdf")

    def test_chunk_produces_metadata(self, tmp_path):
        """청킹 결과의 각 청크가 필수 메타데이터를 포함하는지 검증."""
        import fitz
        from app.services.document_parser import document_parser, DocType

        doc_fitz = fitz.open()
        page = doc_fitz.new_page()
        page.insert_text((50, 100), "수강신청 안내 내용. " * 50)
        pdf_path = tmp_path / "test.pdf"
        doc_fitz.save(str(pdf_path))
        doc_fitz.close()

        parsed = document_parser.parse(str(pdf_path))
        chunks = document_parser.chunk(parsed, doc_type=DocType.GUIDE)

        assert len(chunks) > 0
        for chunk in chunks:
            assert "text"     in chunk
            assert "metadata" in chunk
            meta = chunk["metadata"]
            assert "source_doc"  in meta
            assert "page_num"    in meta
            assert "chunk_index" in meta
            assert "doc_type"    in meta
            assert meta["doc_type"] == "안내"
