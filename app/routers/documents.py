"""문서 업로드 API.

POST /api/v1/documents/upload
  파일 업로드 → 파싱 → 의미 단위 청킹 → 벡터 저장 → Sheets 기록
DELETE /api/v1/documents/{document_id}
  벡터 DB에서 문서 삭제
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile, File

from app.models.schemas import DocumentUploadResponse
from app.services.document_parser import DocType
from app.services.rag_engine import ingestion_pipeline, vector_store
from app.services.sheet_manager import faq_sheet_manager

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="업로드할 PDF 또는 DOCX 파일"),
    doc_type: DocType = Form(
        default=DocType.GUIDE,
        description="문서 유형: 규정 | 공지 | 안내",
    ),
    uploader: str = Form(default="", description="업로더 이름/부서 (선택)"),
):
    """문서를 업로드하고 벡터 DB에 인덱싱합니다.

    - **file**: PDF 또는 DOCX 파일
    - **doc_type**: 문서 유형 (규정 / 공지 / 안내)
    - **uploader**: 업로더 정보 (선택)
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"지원하지 않는 파일 형식: '{suffix}'. "
                f"허용 형식: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    document_id = str(uuid.uuid4())
    save_path = UPLOAD_DIR / f"{document_id}{suffix}"

    try:
        # 1) 임시 저장
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2) 파싱 → 청킹 → 벡터 저장
        num_chunks, parsed = ingestion_pipeline.ingest(
            file_path=str(save_path),
            document_id=document_id,
            doc_type=doc_type,
        )

        if num_chunks == 0:
            raise HTTPException(
                status_code=422,
                detail="문서에서 텍스트를 추출할 수 없습니다. 파일 내용을 확인하세요.",
            )

        # 3) Source_Documents 시트 기록
        faq_sheet_manager.save_source_document(
            document_id=document_id,
            filename=file.filename,
            doc_type=doc_type.value,
            num_chunks=num_chunks,
            total_pages=parsed.total_pages,
            uploader=uploader,
        )

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            doc_type=doc_type.value,
            total_pages=parsed.total_pages,
            num_chunks=num_chunks,
            message=f"'{file.filename}' 업로드 및 인덱싱 완료 ({num_chunks}개 청크).",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if save_path.exists():
            save_path.unlink()


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """벡터 DB에서 문서를 삭제합니다."""
    deleted = vector_store.delete_collection(document_id)
    if deleted == 0:
        raise HTTPException(
            status_code=404,
            detail=f"문서를 찾을 수 없습니다: {document_id}",
        )
    return {"document_id": document_id, "deleted_chunks": deleted, "message": "삭제 완료"}
