# 증분 업데이트 가이드

## 개요

FAQ 벡터 DB 동기화 시 **변경된 FAQ만 업데이트**하는 증분 업데이트(Incremental Update) 기능입니다.

전체 FAQ를 재벡터화하는 대신, 마지막 동기화 이후 수정된 FAQ만 감지하여 효율적으로 업데이트합니다.

---

## 작동 원리

### 1. 동기화 시간 추적

- **파일**: `sync_state.json` (자동 생성)
- **내용**: 마지막 동기화 시간 (ISO 8601 형식)
- **위치**: `/faq-generator/sync_state.json`

```json
{
  "last_sync_time": "2026-02-28T15:30:45.123456",
  "updated_at": "2026-02-28T15:30:45.123456"
}
```

### 2. 증분 조회 로직

Google Sheets의 **"수정일"** 컬럼을 기준으로 변경된 FAQ를 필터링합니다.

```python
# app/services/sheet_manager.py
def get_modified_faqs(self, since: datetime | None = None) -> list[dict]:
    """마지막 동기화 이후 수정된 FAQ만 조회"""
    all_faqs = self.get_published_faqs()
    
    if since is None:
        return all_faqs  # 전체 동기화
    
    # 수정일이 since 이후인 FAQ만 필터링
    return [faq for faq in all_faqs if parse_date(faq["수정일"]) > since]
```

### 3. 벡터 업데이트 프로세스

```
1. 마지막 동기화 시간 조회 (sync_state.json)
   ↓
2. Google Sheets에서 변경된 FAQ만 조회
   ↓
3. 각 FAQ의 기존 벡터 삭제 (faq_id 기준)
   ↓
4. 새로운 벡터 생성 및 추가
   ↓
5. 동기화 시간 업데이트 (sync_state.json)
```

---

## API 사용법

### 1. 증분 업데이트 (기본)

```bash
curl -X POST http://localhost:8002/api/v1/faq/sync-vector-db
```

**응답 예시**:
```json
{
  "success": true,
  "message": "FAQ 벡터화 완료 (컬렉션: faq_knowledge)",
  "sync_type": "incremental",
  "updated_faqs": 3,
  "synced_count": 6,
  "deleted_count": 6,
  "collection": "faq_knowledge"
}
```

### 2. 전체 동기화 (강제)

첫 실행 또는 전체 재구축이 필요한 경우:

```bash
curl -X POST "http://localhost:8002/api/v1/faq/sync-vector-db?full_sync=true"
```

**응답 예시**:
```json
{
  "success": true,
  "sync_type": "full",
  "updated_faqs": 50,
  "synced_count": 100,
  "deleted_count": 0
}
```

---

## 자동 동기화와의 통합

### Webhook (증분 업데이트 자동 적용)

Google Apps Script `onEdit` 트리거 → Webhook 호출 시 자동으로 증분 업데이트가 실행됩니다.

```javascript
// apps-script/faq_manager.gs
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  const row = e.range.getRow();
  const col = e.range.getColumn();
  
  // 상태 컬럼(Col.I = 9) 변경 감지
  if (col === 9) {
    _triggerAutoSync();  // 증분 동기화 자동 실행
  }
}
```

**Webhook 엔드포인트**: `/api/v1/faq/webhook/auto-sync`

---

## 성능 비교

### 시나리오: 전체 100개 FAQ 중 3개 수정

| 방식 | FAQ 조회 | 벡터 삭제 | 벡터 생성 | 총 처리 시간 |
|------|---------|----------|----------|-------------|
| **전체 동기화** | 100개 | 200청크 | 200청크 | ~8초 |
| **증분 업데이트** | 3개 | 6청크 | 6청크 | ~0.5초 |

**효율성 개선**: 약 **16배 빠름** ⚡

---

## 동기화 상태 확인

### 마지막 동기화 시간 조회

```python
from app.utils.sync_state import get_last_sync_time

last_sync = get_last_sync_time()
if last_sync:
    print(f"마지막 동기화: {last_sync.isoformat()}")
else:
    print("동기화 기록 없음")
```

### 동기화 상태 초기화 (전체 동기화 강제)

```python
from app.utils.sync_state import reset_sync_state

reset_sync_state()  # sync_state.json 삭제
```

---

## 주의사항

### 1. Google Sheets "수정일" 컬럼 필수

증분 업데이트는 **"수정일"** 컬럼의 자동 업데이트에 의존합니다.

**Apps Script에서 자동 관리**:
```javascript
function _updateModifiedDate(row) {
  const sheet = SpreadsheetApp.getActiveSheet();
  const now = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");
  sheet.getRange(row, 13).setValue(now);  // Col.M = 수정일
}
```

### 2. sync_state.json 백업

`sync_state.json`이 삭제되면 다음 동기화가 **전체 동기화**로 실행됩니다.

- `.gitignore`에 포함되어 있으므로 Git으로 관리되지 않습니다.
- 운영 환경에서는 정기적으로 백업하세요.

### 3. 시간대 일치

- Google Sheets: `Asia/Seoul` (KST)
- Python datetime: UTC → KST 변환 필요 시 처리

현재 구현은 **로컬 시간(KST)** 기준으로 동작합니다.

---

## 트러블슈팅

### Q1. 변경된 FAQ가 감지되지 않아요

**체크리스트**:
1. Google Sheets "수정일" 컬럼이 자동 업데이트되는지 확인
2. Apps Script `onEdit` 트리거가 정상 작동하는지 확인
3. `sync_state.json`의 `last_sync_time`이 올바른지 확인

**해결책**: 전체 동기화 강제 실행
```bash
curl -X POST "http://localhost:8002/api/v1/faq/sync-vector-db?full_sync=true"
```

### Q2. 동기화 시간이 계속 초기화돼요

**원인**: `sync_state.json` 파일이 삭제되거나 권한 문제

**해결책**:
```bash
# 파일 권한 확인
ls -la sync_state.json

# 쓰기 권한 부여 (필요 시)
chmod 644 sync_state.json
```

### Q3. 특정 FAQ가 업데이트되지 않아요

**원인**: `faq_id` 불일치 또는 벡터 삭제 실패

**디버깅**:
```python
# app/services/rag_engine.py 로그 확인
logger.debug("FAQ 청크 삭제 | faq_id={} | count={}", faq_id, len(ids_to_delete))
```

**해결책**: 해당 FAQ를 수동으로 재벡터화
```bash
# 1. 특정 FAQ ID의 벡터 삭제
# 2. 전체 동기화 실행
curl -X POST "http://localhost:8002/api/v1/faq/sync-vector-db?full_sync=true"
```

---

## 구현 파일

| 파일 | 역할 |
|------|------|
| `app/utils/sync_state.py` | 동기화 시간 추적 유틸리티 |
| `app/services/sheet_manager.py` | 증분 FAQ 조회 로직 |
| `app/services/rag_engine.py` | FAQ ID 기반 벡터 삭제 메서드 |
| `app/routers/faq.py` | 증분 업데이트 API 엔드포인트 |
| `sync_state.json` | 동기화 상태 저장 (자동 생성) |

---

## 다음 개선 사항 (옵션)

1. **삭제된 FAQ 감지**: "게시중" → "임시저장" 변경 시 벡터 자동 삭제
2. **동기화 로그 저장**: 각 동기화 기록을 DB에 저장하여 히스토리 추적
3. **벡터 버전 관리**: 임베딩 모델 변경 시 전체 재벡터화 자동 감지
4. **배치 처리 최적화**: 대량 FAQ 수정 시 배치 크기 조정

---

## 참고 자료

- [COLLECTION_IMPROVEMENT.md](./COLLECTION_IMPROVEMENT.md) - 컬렉션 분리 개선안
- [AUTO_SYNC_GUIDE.md](./AUTO_SYNC_GUIDE.md) - 자동 동기화 가이드
- [CHANGELOG.md](./CHANGELOG.md) - 버전별 변경 이력
