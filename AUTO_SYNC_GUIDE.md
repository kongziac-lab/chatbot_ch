# FAQ 자동 동기화 설정 가이드

## 🎯 개요

Google Sheets에서 FAQ 상태가 **"게시중"**으로 변경되면 자동으로 벡터 DB에 동기화됩니다.

---

## ✅ 구현된 기능

### 1. **자동 동기화 트리거**

| 상황 | 동작 |
|------|------|
| FAQ 상태 → "게시중" 변경 | ✅ 자동 벡터화 |
| "게시중" → 다른 상태 변경 | ✅ 자동 벡터화 (삭제 반영) |
| FAQ 질문/답변 수정 | ❌ 수동 동기화 필요* |

\* Phase 3에서 개선 예정

### 2. **보안**

- ✅ Webhook Secret으로 인증
- ✅ 잘못된 Secret → 401 Unauthorized
- ✅ 백그라운드 실행 (즉시 응답)

---

## 🚀 설정 방법

### 1단계: Google Apps Script 설치

1. **Google Sheets 열기**
   - FAQ_Master 스프레드시트 접속

2. **Apps Script 편집기 열기**
   - 메뉴: **확장 프로그램** → **Apps Script**

3. **코드 붙여넣기**
   - `/apps-script/faq_manager.gs` 파일 전체 내용 복사
   - Apps Script 편집기에 붙여넣기

4. **상수 수정**
   ```javascript
   var ADMIN_EMAIL   = "your-admin@example.com";     // 실제 이메일
   var MANAGER_EMAIL = "your-manager@example.com";   // 실제 이메일
   var API_BASE_URL  = "http://localhost:8002";       // FastAPI 서버 주소
   var WEBHOOK_SECRET = "faq-auto-sync-secret-2026";  // .env의 WEBHOOK_SECRET
   ```

5. **setup() 함수 실행**
   - 함수 선택: `setup`
   - **실행** 버튼 클릭
   - 권한 승인 (Google 계정 인증)

6. **트리거 확인**
   - 왼쪽 메뉴: **트리거** (시계 아이콘)
   - `onEdit`, `sendDailyReport` 트리거 생성 확인

---

### 2단계: FastAPI 서버 설정

#### `.env` 파일에 Webhook Secret 추가 (✅ 이미 완료)

```bash
# ── Webhook ───────────────────────────────────────────────────────
WEBHOOK_SECRET=faq-auto-sync-secret-2026
```

---

## 🧪 테스트 방법

### 1. 수동 Webhook 호출 테스트

```bash
curl -X POST "http://localhost:8002/api/v1/faq/webhook/auto-sync" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: faq-auto-sync-secret-2026"
```

**성공 응답**:
```json
{
  "status": "accepted",
  "message": "FAQ 자동 동기화 작업이 백그라운드에서 실행됩니다."
}
```

**실패 응답** (잘못된 Secret):
```json
{
  "detail": "Unauthorized: Invalid webhook secret"
}
```

### 2. Google Sheets에서 테스트

1. **FAQ_Master 시트 열기**
2. **임의의 FAQ 선택** (자동생성 상태인 것)
3. **상태 컬럼(I열)을 "게시중"으로 변경**
4. **서버 로그 확인**:
   ```
   📢 Webhook 수신: FAQ 자동 동기화 시작
   ✅ Webhook 동기화 완료: 99건
   ```

---

## 📊 자동 동기화 플로우

```
┌─────────────────────────────────────────────────────────┐
│              Google Sheets FAQ_Master                    │
└─────────────────────────────────────────────────────────┘
                          ↓
          담당자가 상태를 "게시중"으로 변경
                          ↓
┌─────────────────────────────────────────────────────────┐
│           Apps Script onEdit 트리거                      │
│  1. 수정일 자동 업데이트                                  │
│  2. 이메일 알림 발송                                      │
│  3. _triggerAutoSync() 호출 ← 신규!                     │
└─────────────────────────────────────────────────────────┘
                          ↓
                 HTTP POST with Secret
                          ↓
┌─────────────────────────────────────────────────────────┐
│    FastAPI: POST /api/v1/faq/webhook/auto-sync         │
│  1. Secret 검증                                          │
│  2. 즉시 202 응답 반환                                   │
│  3. 백그라운드에서 동기화 실행                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              백그라운드 동기화 작업                       │
│  1. Google Sheets에서 게시중 FAQ 조회                    │
│  2. 청크 형식으로 변환                                    │
│  3. ChromaDB faq_knowledge 컬렉션에 저장                 │
└─────────────────────────────────────────────────────────┘
                          ↓
                  챗봇이 즉시 사용 가능!
```

---

## 🔧 고급 설정

### API 서버 외부 접근 설정

로컬이 아닌 서버에서 실행 중이라면:

```javascript
// apps-script/faq_manager.gs
var API_BASE_URL = "https://your-domain.com";  // 실제 도메인으로 변경
```

```bash
# .env
WEBHOOK_SECRET=your-production-webhook-secret-here  # 강력한 비밀키로 변경
```

---

## 📈 성능 모니터링

### 로그 확인

```bash
# 서버 로그에서 자동 동기화 확인
tail -f /path/to/server.log | grep "Webhook"
```

**성공 로그**:
```
2026-02-28 21:53:48 | INFO | 📢 Webhook 수신: FAQ 자동 동기화 시작
2026-02-28 21:54:18 | INFO | ✅ Webhook 동기화 완료: 99건
```

**실패 로그**:
```
2026-02-28 21:53:48 | WARNING | Webhook 인증 실패: 잘못된 secret
```

---

## ⚠️ 주의사항

### 1. **Apps Script 실행 제한**

- Google Apps Script는 **6분 타임아웃** 제한이 있습니다
- Webhook 호출이 실패해도 사용자의 Sheets 작업에는 영향 없음
- 실패 시 로그만 기록되고 조용히 종료됨

### 2. **네트워크 접근**

- Apps Script에서 `localhost` 접근 불가!
- **프로덕션 환경**: 실제 도메인 사용 필요
- **개발 환경**: ngrok 등으로 로컬 서버 외부 노출

### 3. **동기화 지연**

- Webhook은 **백그라운드**에서 실행됨
- 즉시 응답(202 Accepted) 후 비동기 처리
- 실제 동기화 완료까지 약 **20-30초** 소요

---

## 🛠️ 개발 환경 설정 (ngrok 사용)

로컬에서 Google Apps Script 테스트를 하려면:

### 1. ngrok 설치 및 실행

```bash
# ngrok 설치 (Homebrew)
brew install ngrok

# 포트 8002 터널링
ngrok http 8002
```

**출력 예시**:
```
Forwarding: https://abc123.ngrok.io -> http://localhost:8002
```

### 2. Apps Script 수정

```javascript
var API_BASE_URL = "https://abc123.ngrok.io";  // ngrok URL 사용
```

### 3. 테스트

Google Sheets에서 FAQ 상태 변경 → 자동 동기화 확인!

---

## ✅ 체크리스트

### FastAPI 서버
- [x] `.env`에 `WEBHOOK_SECRET` 추가
- [x] `app/config.py`에 webhook_secret 설정 추가
- [x] `app/routers/faq.py`에 webhook 엔드포인트 구현
- [x] 백그라운드 동기화 작업 구현
- [x] Secret 인증 로직 구현

### Google Apps Script
- [x] `API_BASE_URL` 상수 추가
- [x] `WEBHOOK_SECRET` 상수 추가
- [x] `_triggerAutoSync()` 함수 구현
- [x] `onEdit` 트리거에 webhook 호출 추가
- [ ] 프로덕션 서버 URL로 변경 (배포 시)
- [ ] 관리자 이메일 변경

### 테스트
- [x] Webhook 수동 호출 테스트
- [x] Secret 인증 테스트
- [x] 백그라운드 동기화 테스트
- [ ] Google Sheets에서 실제 FAQ 변경 테스트 (ngrok 필요)

---

## 🎉 완료!

**자동 동기화 시스템이 완성되었습니다!**

이제 Google Sheets에서 FAQ 상태를 "게시중"으로 변경하면:
1. ✅ 수정일 자동 업데이트
2. ✅ 이메일 알림 발송
3. ✅ **벡터 DB 자동 동기화** ← 신규!
4. ✅ 챗봇이 즉시 최신 FAQ 사용

**작성일**: 2026-02-28  
**버전**: v1.1.0 (자동 동기화 추가)
