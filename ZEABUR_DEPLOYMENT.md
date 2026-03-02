# Zeabur 배포 가이드 (Lark Base + ChromaDB)

## 1) Zeabur 서비스 생성
- 레포지토리 연결 후 `Dockerfile` 기반으로 배포
- Start Command는 별도 지정 없이 Docker `CMD` 사용

## 2) 필수 환경변수
- `PORT` (Zeabur가 자동 주입)
- `OPENAI_API_KEY`
- `LARK_APP_ID`
- `LARK_APP_SECRET`
- `LARK_BASE_APP_TOKEN`
- `LARK_FAQ_TABLE_ID`

필수값 설정 후 사전 점검:
```bash
python3 scripts/lark_preflight.py
python3 scripts/chroma_preflight.py
# 또는 한번에:
./scripts/run_preflight_all.sh
```

## 3) 선택 환경변수
- `LARK_FEEDBACK_TABLE_ID`
- `LARK_SOURCE_DOC_TABLE_ID`
- `ALLOWED_ORIGINS`
- `WEBHOOK_SECRET`
- `CHROMA_PERSIST_DIR` (기본 `./chroma_db`)
- `CACHE_TTL_SECONDS` (기본 `300`)
- `EMBEDDING_MODEL_NAME` (기본 `BAAI/bge-m3`)

## 4) 스토리지 권장
- ChromaDB 영속화를 위해 Volume 마운트 권장
- 예: `/app/chroma_db`, `/app/models`
- 환경변수 `CHROMA_PERSIST_DIR=/app/chroma_db`
- 점검:
```bash
python3 scripts/chroma_preflight.py
```

## 5) 헬스체크
- `GET /health`
- `GET /admin/vector-health` (Chroma 카운트 확인)
- `GET /admin/preflight` (Lark 토큰/필드/Chroma 통합 점검)
- `GET /admin/lark-field-compat` (Lark FAQ 필드 호환성만 점검)

## 6) FAQ 운영 방식
- FAQ 생성/수정/게시 상태 관리는 Lark Base에서 수동 수행
- API는 Lark Base 데이터를 읽고, 벡터 동기화(`/api/v1/faq/sync-vector-db`)만 수행

## 7) 배포 후 점검 순서
1. `GET /health` 확인
2. `python3 scripts/lark_preflight.py` 실행 (필드/토큰/읽기 점검)
3. `python3 scripts/chroma_preflight.py` 실행 (디렉터리/쓰기/컬렉션 접근 점검)
4. 최초 전체 동기화:
```bash
python3 scripts/test_sync_flow.py --base-url https://<your-service-domain> --full-sync
```
5. 이후 증분 동기화:
```bash
python3 scripts/test_sync_flow.py --base-url https://<your-service-domain>
```
