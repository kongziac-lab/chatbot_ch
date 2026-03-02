"""ChromaDB 기반 벡터 저장소.

임베딩 모델: BAAI/bge-m3 (sentence-transformers)
  - 한·중·영 다국어 지원
  - 코사인 유사도 기반 검색

최적화:
  - 임베딩 LRU 캐싱 (텍스트 해시 기반, maxsize=2048)
  - MMR(Maximum Marginal Relevance) 리랭킹으로 다양성 확보
  - loguru 로깅
"""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from typing import TYPE_CHECKING

import chromadb
import numpy as np
from chromadb import EmbeddingFunction, Documents, Embeddings
from loguru import logger

from app.config import settings
from app.services.document_parser import DocType, document_parser
from app.utils.metrics import metrics_collector, Timer, SearchMetric
from datetime import datetime

if TYPE_CHECKING:
    from app.services.document_parser import ParsedDocument

# 컬렉션 이름 상수
COLLECTION_DOCUMENTS = "faq_documents"  # 원본 문서 (PDF/DOCX)
COLLECTION_FAQ = "faq_knowledge"        # 정제된 FAQ

# ---------------------------------------------------------------------------
# 임베딩 LRU 캐시
# ---------------------------------------------------------------------------

_EMBED_CACHE_SIZE = 2048   # 최대 캐시 항목 수


class _EmbedLRUCache:
    """텍스트 → 임베딩 벡터 LRU 캐시 (thread-safe not required: GIL 범위 내)."""

    def __init__(self, maxsize: int = _EMBED_CACHE_SIZE) -> None:
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._maxsize = maxsize

    @staticmethod
    def _key(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()  # noqa: S324 (non-crypto)

    def get(self, text: str) -> list[float] | None:
        k = self._key(text)
        if k in self._cache:
            self._cache.move_to_end(k)
            return self._cache[k]
        return None

    def put(self, text: str, vector: list[float]) -> None:
        k = self._key(text)
        self._cache[k] = vector
        self._cache.move_to_end(k)
        if len(self._cache) > self._maxsize:
            evicted_key, _ = self._cache.popitem(last=False)
            logger.debug("임베딩 캐시 LRU 제거: {}", evicted_key[:8])

    def __len__(self) -> int:
        return len(self._cache)


_embed_cache = _EmbedLRUCache()


# ---------------------------------------------------------------------------
# BGE-M3 임베딩 함수 (ChromaDB EmbeddingFunction 인터페이스 구현)
# ---------------------------------------------------------------------------

class BGEM3EmbeddingFunction(EmbeddingFunction):
    """sentence-transformers BAAI/bge-m3 래퍼 (캐싱 포함)."""

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("BGE-M3 모델 로드 중: {}", self._model_name)
            self._model = SentenceTransformer(self._model_name)
            logger.info("BGE-M3 모델 로드 완료")

    def __call__(self, input: Documents) -> Embeddings:  # noqa: A002
        self._load()
        texts = list(input)
        results: list[list[float]] = [None] * len(texts)  # type: ignore[list-item]
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # 캐시 히트 분리
        for i, text in enumerate(texts):
            cached = _embed_cache.get(text)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            vectors = self._model.encode(
                uncached_texts,
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32,
            )
            for idx, vec in zip(uncached_indices, vectors.tolist()):
                results[idx] = vec
                _embed_cache.put(texts[idx], vec)
            logger.debug(
                "임베딩: 신규={}건, 캐시={}건 (캐시 총={})",
                len(uncached_texts),
                len(texts) - len(uncached_texts),
                len(_embed_cache),
            )

        return results  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# MMR 리랭킹 유틸
# ---------------------------------------------------------------------------

def _mmr_rerank(
    query_vec: list[float],
    candidates: list[dict],
    top_k: int,
    lambda_param: float = 0.5,
) -> list[dict]:
    """Maximum Marginal Relevance 리랭킹.

    관련성(쿼리 유사도)과 다양성(선택된 결과 간 비유사도)을 균형 있게 고려.

    Args:
        query_vec:    쿼리 임베딩 벡터
        candidates:   {"text", "metadata", "score", "_vec"} 목록
        top_k:        반환 개수
        lambda_param: 0=다양성 최대, 1=관련성 최대 (기본 0.5)

    Returns:
        리랭킹된 결과 (top_k 개)
    """
    if not candidates:
        return []

    q = np.array(query_vec, dtype=np.float32)
    vecs = np.array([c["_vec"] for c in candidates], dtype=np.float32)
    query_scores = vecs @ q                        # (n,) 쿼리 유사도

    selected_indices: list[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected_indices) < top_k:
        if not selected_indices:
            # 첫 번째: 쿼리 유사도 최고 항목
            best = max(remaining, key=lambda i: query_scores[i])
        else:
            selected_vecs = vecs[selected_indices]     # (k, dim)
            mmr_scores = {}
            for i in remaining:
                rel = float(query_scores[i])
                # 선택된 결과 중 최대 유사도 (중복 페널티)
                sim_to_selected = float((selected_vecs @ vecs[i]).max())
                mmr_scores[i] = lambda_param * rel - (1 - lambda_param) * sim_to_selected
            best = max(remaining, key=lambda i: mmr_scores[i])

        selected_indices.append(best)
        remaining.remove(best)

    return [candidates[i] for i in selected_indices]


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------

class VectorStore:
    """ChromaDB 기반 FAQ 문서 벡터 저장소 (컬렉션 분리 지원)."""

    def __init__(self) -> None:
        self._client: chromadb.PersistentClient | None = None
        self._collections: dict[str, chromadb.Collection] = {}  # 컬렉션 캐시
        self._embedding_fn = BGEM3EmbeddingFunction(
            model_name=settings.embedding_model_name
        )

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _get_collection(self, collection_name: str = COLLECTION_DOCUMENTS) -> chromadb.Collection:
        """컬렉션 가져오기 (없으면 생성).
        
        Args:
            collection_name: 컬렉션 이름 (기본값: faq_documents)
        """
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=str(settings.chroma_dir)
            )
        
        if collection_name not in self._collections:
            self._collections[collection_name] = self._client.get_or_create_collection(
                name=collection_name,
                embedding_function=self._embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("컬렉션 초기화: {}", collection_name)
        
        return self._collections[collection_name]

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def add_documents(
        self,
        chunks: list[dict],
        document_id: str,
        collection_name: str = COLLECTION_DOCUMENTS,
    ) -> int:
        """청크 리스트를 벡터 DB에 저장.

        Args:
            chunks:      document_parser.chunk() 반환값
                         각 원소: {"text": str, "metadata": dict}
            document_id: 문서 고유 식별자 (UUID)
            collection_name: 컬렉션 이름 (기본값: faq_documents)

        Returns:
            저장된 청크 수
        """
        if not chunks:
            return 0

        collection = self._get_collection(collection_name)
        ids = [f"{document_id}__chunk__{i}" for i in range(len(chunks))]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                **c["metadata"],
                "document_id": document_id,
                "chunk_index": i,
            }
            for i, c in enumerate(chunks)
        ]

        self._delete_by_doc_id(document_id, collection_name)
        collection.add(documents=texts, ids=ids, metadatas=metadatas)
        logger.info("벡터 저장 완료 | collection={} | doc_id={} | chunks={}", 
                   collection_name, document_id, len(chunks))
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_id: str | None = None,
        doc_type: str | None = None,
        use_mmr: bool = True,
        mmr_lambda: float = 0.5,
        fetch_k: int | None = None,
        collection_name: str = COLLECTION_DOCUMENTS,
    ) -> list[dict]:
        """의미 유사도 검색 (MMR 리랭킹 옵션 포함).

        Args:
            query:      검색 쿼리 (한·중·영 모두 지원)
            top_k:      반환할 최대 결과 수
            doc_id:     특정 문서 내 검색 필터
            doc_type:   문서 유형 필터
            use_mmr:    MMR 리랭킹 사용 여부 (기본 True)
            mmr_lambda: MMR 관련성/다양성 균형 파라미터 (0~1)
            fetch_k:    MMR 후보 수 (기본 top_k * 3)
            collection_name: 컬렉션 이름 (기본값: faq_documents)

        Returns:
            [{"text": str, "metadata": dict, "score": float}, ...]
            score: 0~1 (1에 가까울수록 유사)
        """
        # 성능 메트릭 수집
        timer = Timer()
        success = True
        error_msg = None
        result_count = 0
        
        try:
            with timer:
                collection = self._get_collection(collection_name)
                count = collection.count()
                if count == 0:
                    return []

                where: dict | None = None
                filters: list[dict] = []
                if doc_id:
                    filters.append({"document_id": {"$eq": doc_id}})
                if doc_type:
                    filters.append({"doc_type": {"$eq": doc_type}})

                if len(filters) == 1:
                    where = filters[0]
                elif len(filters) > 1:
                    where = {"$and": filters}

                # MMR 사용 시 후보를 더 많이 가져옴
                n_fetch = min(fetch_k or top_k * 3, count)

                results = collection.query(
                    query_texts=[query],
                    n_results=n_fetch,
                    where=where,
                    include=["documents", "metadatas", "distances", "embeddings"],
                )

                documents  = results.get("documents",  [[]])[0]
                metadatas  = results.get("metadatas",  [[]])[0]
                distances  = results.get("distances",  [[]])[0]
                embeddings = results.get("embeddings", [[]])[0]

                logger.debug("검색 결과: documents={}, embeddings 타입={}", len(documents), type(embeddings))
                
                candidates = [
                    {
                        "text":     doc,
                        "metadata": meta,
                        "score":    round(1 - dist, 4),
                        "_vec":     emb if emb is not None else [],
                    }
                    for doc, meta, dist, emb in zip(documents, metadatas, distances, embeddings)
                ]

                if use_mmr and len(embeddings) > 0 and len(candidates) > top_k:
                    query_vec = self._embedding_fn([query])[0]
                    candidates = _mmr_rerank(query_vec, candidates, top_k=top_k, lambda_param=mmr_lambda)
                    logger.debug("MMR 리랭킹: {}→{}건", n_fetch, len(candidates))
                else:
                    candidates = candidates[:top_k]

                # 내부 필드 제거 후 반환
                final_results = [
                    {"text": c["text"], "metadata": c["metadata"], "score": c["score"]}
                    for c in candidates
                ]
                result_count = len(final_results)
                return final_results
                
        except Exception as e:
            success = False
            error_msg = str(e)
            logger.error("검색 오류: {}", e)
            raise
        
        finally:
            # 메트릭 기록
            try:
                metrics_collector.record_search(SearchMetric(
                    timestamp=datetime.now().isoformat(),
                    query=query[:50],  # 처음 50자만 저장
                    collection=collection_name,
                    top_k=top_k,
                    duration_ms=timer.get_elapsed_ms(),
                    result_count=result_count,
                    use_mmr=use_mmr,
                    success=success,
                    error=error_msg,
                ))
            except Exception as metric_error:
                logger.warning("검색 메트릭 기록 실패: {}", metric_error)

    def delete_collection(self, doc_id: str, collection_name: str = COLLECTION_DOCUMENTS) -> int:
        """특정 문서의 모든 청크를 벡터 DB에서 삭제."""
        return self._delete_by_doc_id(doc_id, collection_name)

    def get_context(self, query: str, top_k: int = 3, collection_name: str = COLLECTION_DOCUMENTS) -> str:
        """RAG 프롬프트용 컨텍스트 문자열 반환."""
        results = self.search(query, top_k=top_k, collection_name=collection_name)
        return "\n\n---\n\n".join(r["text"] for r in results)

    def get_chunks_by_doc_id(self, doc_id: str, collection_name: str = COLLECTION_DOCUMENTS) -> list[dict]:
        """특정 문서의 모든 청크를 metadata 포함해서 반환 (chunk_index 순)."""
        collection = self._get_collection(collection_name)
        raw = collection.get(
            where={"document_id": {"$eq": doc_id}},
            include=["documents", "metadatas"],
        )
        pairs = list(zip(raw.get("documents", []), raw.get("metadatas", [])))
        pairs.sort(key=lambda x: int(x[1].get("chunk_index", 0)))
        return [{"text": doc, "metadata": meta} for doc, meta in pairs]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """BGE-M3로 텍스트를 임베딩해 벡터 목록 반환 (중복 제거용)."""
        return self._embedding_fn(texts)

    def collection_count(self, collection_name: str = COLLECTION_DOCUMENTS) -> int:
        """컬렉션 내 전체 벡터(청크) 수 반환."""
        collection = self._get_collection(collection_name)
        return int(collection.count())

    def health_snapshot(self) -> dict[str, int | str]:
        """벡터 저장소 상태 스냅샷."""
        return {
            "persist_dir": str(settings.chroma_dir),
            "faq_count": self.collection_count(COLLECTION_FAQ),
            "document_count": self.collection_count(COLLECTION_DOCUMENTS),
        }

    # ------------------------------------------------------------------
    # 내부: 문서 삭제
    # ------------------------------------------------------------------

    def _delete_by_doc_id(self, doc_id: str, collection_name: str = COLLECTION_DOCUMENTS) -> int:
        collection = self._get_collection(collection_name)
        existing = collection.get(where={"document_id": {"$eq": doc_id}})
        ids_to_delete = existing.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.info("청크 삭제 | collection={} | doc_id={} | count={}", 
                       collection_name, doc_id, len(ids_to_delete))
        return len(ids_to_delete)
    
    def delete_by_faq_id(self, faq_id: str, collection_name: str = COLLECTION_FAQ) -> int:
        """특정 FAQ ID의 모든 청크를 벡터 DB에서 삭제 (증분 업데이트용).
        
        Args:
            faq_id: FAQ 고유번호
            collection_name: 컬렉션 이름 (기본값: faq_knowledge)
            
        Returns:
            삭제된 청크 수
        """
        collection = self._get_collection(collection_name)
        existing = collection.get(where={"faq_id": {"$eq": faq_id}})
        ids_to_delete = existing.get("ids", [])
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            logger.debug("FAQ 청크 삭제 | faq_id={} | count={}", faq_id, len(ids_to_delete))
        return len(ids_to_delete)


# ---------------------------------------------------------------------------
# 파일 업로드 → 파싱 → 청킹 → 벡터 저장 파이프라인
# ---------------------------------------------------------------------------

class IngestionPipeline:
    """문서 수집(ingest) 파이프라인: 파일 → 벡터 저장."""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def ingest(
        self,
        file_path: str,
        document_id: str,
        doc_type: DocType = DocType.GUIDE,
    ) -> tuple[int, "ParsedDocument"]:
        """파일을 파싱·청킹하여 벡터 DB에 저장.

        Returns:
            (저장된 청크 수, ParsedDocument)
        """
        logger.info("문서 수집 시작: {} | doc_id={}", file_path, document_id)
        parsed = document_parser.parse(file_path)
        chunks = document_parser.chunk(parsed, doc_type=doc_type)
        num_chunks = self._store.add_documents(chunks, document_id=document_id)
        logger.info("문서 수집 완료: {} chunks | doc_id={}", num_chunks, document_id)
        return num_chunks, parsed


vector_store = VectorStore()
ingestion_pipeline = IngestionPipeline(vector_store)
