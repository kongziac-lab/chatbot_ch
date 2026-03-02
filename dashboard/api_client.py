"""FastAPI 백엔드 HTTP 클라이언트."""
import os
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
_TIMEOUT = 60.0


def _get(path: str, **params) -> dict | list:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.get(f"{BASE_URL}{path}", params=params)
        r.raise_for_status()
        return r.json()


def _post(path: str, json: dict | None = None, **kwargs) -> dict:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.post(f"{BASE_URL}{path}", json=json, **kwargs)
        r.raise_for_status()
        return r.json()


def _delete(path: str) -> dict:
    with httpx.Client(timeout=_TIMEOUT) as c:
        r = c.delete(f"{BASE_URL}{path}")
        r.raise_for_status()
        return r.json()


# FAQ
def get_faqs(category_major=None, category_minor=None):
    params = {}
    if category_major:
        params["category_major"] = category_major
    if category_minor:
        params["category_minor"] = category_minor
    return _get("/faq/list", **params)


def start_pipeline(doc_id: str, department: str, cat_major: str, cat_minor: str) -> dict:
    return _post("/faq/pipeline/generate", json={
        "doc_id": doc_id,
        "department": department,
        "category_major": cat_major,
        "category_minor": cat_minor,
    })


def get_pipeline_status(job_id: str) -> dict:
    return _get(f"/faq/pipeline/status/{job_id}")


# Documents
def upload_document(file_bytes: bytes, filename: str, doc_type: str) -> dict:
    with httpx.Client(timeout=120.0) as c:
        r = c.post(
            f"{BASE_URL}/documents/upload",
            files={"file": (filename, file_bytes)},
            data={"doc_type": doc_type},
        )
        r.raise_for_status()
        return r.json()


def delete_document(document_id: str) -> dict:
    return _delete(f"/documents/{document_id}")


# Translate
def translate_qa(question_ko: str, answer_ko: str) -> dict:
    return _post("/translate/qa", json={
        "question_ko": question_ko,
        "answer_ko": answer_ko,
    })
