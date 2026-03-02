# FAQ 수정 자동 동기화 Quick Start

## 🚀 5분 설정 가이드

### 1️⃣ Apps Script 코드 업데이트 (2분)

1. **Google Sheets 열기**
   - FAQ_Master 시트 접속

2. **Apps Script 편집기**
   - 메뉴: **확장 프로그램 → Apps Script**

3. **코드 업데이트**
   - `faq_manager.gs` 파일 전체 교체
   - 소스: `/apps-script/faq_manager.gs`

4. **설정 확인**
   ```javascript
   var API_BASE_URL = "http://localhost:8002";  // 서버 주소
   var WEBHOOK_SECRET = "faq-auto-sync-secret-2026";  // 인증 키
   ```

---

### 2️⃣ 트리거 설정 (1분)

**Apps Script 편집기에서 실행**:

```javascript
// 기본 설정 (실시간 동기화만)
setup()

// 또는 시간 기반 동기화 포함 (대규모 FAQ 운영)
setupWithScheduledSync()
```

**실행 방법**:
1. 함수 선택 (상단 드롭다운)
2. 실행 버튼 클릭 (▶️)
3. 권한 허용

---

### 3️⃣ 테스트 (2분)

#### Step 1: FAQ 수정
```
1. 게시중 상태 FAQ 선택
2. 질문 또는 답변 수정
3. Enter 입력
```

#### Step 2: 수정일 확인
```
M열(수정일)이 자동으로 업데이트되었나요? ✅
```

#### Step 3: 서버 로그 확인
```bash
# 터미널에서 확인
tail -f server.log | grep "증분 동기화"

# 예상 출력:
# 📢 Webhook 수신: FAQ 증분 동기화 시작
# ✅ Webhook 증분 동기화 완료 | FAQ=1건 | 청크=2건
```

#### Step 4: 챗봇 테스트
```bash
curl -X POST "http://localhost:8002/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "수정한 질문 내용"}'

# 수정된 답변이 반영되어야 함 ✅
```

---

## ✅ 완료!

이제 Google Sheets에서 FAQ를 수정하면:
- ✅ **0.5초 내** 자동 동기화
- ✅ **즉시 챗봇 반영**
- ✅ **수동 작업 불필요**

---

## 🎯 작동 조건

### 자동 동기화가 실행되는 경우

| 조건 | 동작 |
|------|------|
| 상태 → "게시중" | ✅ 벡터 추가 |
| "게시중" → 다른 상태 | ✅ 벡터 제거 |
| **질문(D열) 수정 (게시중)** | ✅ **증분 업데이트** ⚡ |
| **답변(E열) 수정 (게시중)** | ✅ **증분 업데이트** ⚡ |
| 질문/답변 수정 (임시저장) | ❌ 동기화 안 함 |

---

## 🔧 트러블슈팅

### ❌ 수정일이 자동 업데이트 안 돼요
**해결**: Apps Script 권한 확인 → `setup()` 재실행

### ❌ 챗봇에 반영이 안 돼요
**체크리스트**:
1. FAQ 상태가 "게시중"인가요?
2. FastAPI 서버가 실행 중인가요?
3. Webhook Secret이 일치하나요?

**빠른 진단**:
```bash
# 서버 상태 확인
curl http://localhost:8002/health

# 수동 동기화 테스트
curl -X POST http://localhost:8002/api/v1/faq/sync-vector-db
```

---

## 📚 상세 가이드

더 자세한 내용은 다음 문서를 참고하세요:

- **FAQ_EDIT_AUTO_SYNC_GUIDE.md**: 상세 설정 및 고급 옵션
- **INCREMENTAL_UPDATE_GUIDE.md**: 증분 업데이트 기술 문서
- **AUTO_SYNC_GUIDE.md**: 자동 동기화 기본 가이드

---

**버전**: v1.2.0  
**작성일**: 2026-02-28
