# 🔍 FAQ 로딩 문제 디버깅 가이드

## 📊 현재 상태

### ✅ 백엔드
- FastAPI 서버: **정상 작동** (포트 8002)
- FAQ 조회 테스트: **성공** (비자관련 2개 FAQ 확인)
- API 엔드포인트: **정상**

```bash
# 백엔드 테스트 성공 결과
curl "http://localhost:8002/api/v1/faqs?category_major=비자/체류&category_minor=비자관련&lang=ko"
# → 2개 FAQ 반환 확인
```

### 🔧 프론트엔드
- Vite 개발 서버: **실행 중** (포트 5174)
- **디버깅 로그 추가 완료** ✅

---

## 🧪 지금 바로 테스트하기

### 1단계: 브라우저 접속
```
http://localhost:5174
```

### 2단계: 개발자 도구 열기
- **Windows/Linux**: `F12` 또는 `Ctrl + Shift + I`
- **Mac**: `Cmd + Option + I`

### 3단계: Console 탭 선택
브라우저 개발자 도구에서 **Console** 탭을 클릭합니다.

### 4단계: FAQ 카테고리 클릭
1. 언어 선택 (한국어)
2. "비자/체류" 클릭
3. "비자관련" 또는 "체류관련" 클릭

### 5단계: 콘솔 로그 확인
다음과 같은 로그가 출력됩니다:

```
=== FAQ 조회 시작 ===
대분류: 비자/체류
중분류: 비자관련
언어: ko
API 요청 URL: http://localhost:8002/api/v1/faqs?category_major=비자%2F체류&category_minor=비자관련&lang=ko
API_BASE_URL: http://localhost:8002
API 응답 상태: 200 OK
API 응답 데이터: {items: Array(2), total: 2, language: 'ko'}
조회된 FAQ 개수: 2
FAQ 목록: [...]
=== FAQ 조회 완료 ===
```

---

## 🔍 예상 문제 및 해결 방법

### 문제 1: "Failed to fetch" 오류

**증상**:
```
=== FAQ 조회 오류 ===
에러: Failed to fetch
```

**원인**: CORS 또는 네트워크 연결 문제

**해결**:
```bash
# 1. FastAPI 서버 재시작
lsof -ti :8002 | xargs kill -9
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# 2. 서버 로그 확인
tail -f /tmp/fastapi_ready.log
```

---

### 문제 2: "API_BASE_URL이 undefined"

**증상**:
```
API_BASE_URL: undefined
API 요청 URL: undefined/api/v1/faqs?...
```

**원인**: `.env` 파일이 로드되지 않음

**해결**:
```bash
# 1. .env 파일 확인
cat /Users/kdh/Documents/GitHub/faq생성기/faq-generator/public/.env

# 2. Vite 개발 서버 재시작 (Ctrl+C로 종료 후)
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator/public
npm run dev
```

---

### 문제 3: "404 Not Found" 또는 "500 Internal Server Error"

**증상**:
```
API 응답 상태: 404 Not Found
또는
API 응답 상태: 500 Internal Server Error
```

**해결**:
```bash
# 백엔드 로그 확인
tail -50 /tmp/fastapi_ready.log

# 또는 직접 curl로 테스트
curl -v "http://localhost:8002/api/v1/faqs?category_major=비자/체류&category_minor=비자관련&lang=ko"
```

---

### 문제 4: "조회된 FAQ 개수: 0"

**증상**:
```
=== FAQ 조회 완료 ===
조회된 FAQ 개수: 0
FAQ 목록: []
```

**원인 1**: 카테고리 이름이 Google Sheets와 정확히 일치하지 않음

**해결**:
```bash
# 캐시 삭제 후 다시 조회
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -c "
from app.services.sheet_manager import faq_sheet_manager
faq_sheet_manager._invalidate_cache()
print('✅ 캐시 삭제')
"
```

**원인 2**: Google Sheets 데이터 확인

1. Google Sheets 열기: https://docs.google.com/spreadsheets/d/1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo/edit
2. `FAQ_Master` 시트 확인
3. **대분류(B열)**, **중분류(C열)** 값 확인
4. **게시여부(J열)** = "예" 확인

---

### 문제 5: FAQ는 조회되는데 화면에 표시되지 않음

**증상**:
```
조회된 FAQ 개수: 2
FAQ 목록: [{...}, {...}]
```
하지만 화면에는 버튼이 보이지 않음

**원인**: 프론트엔드 렌더링 로직 문제

**확인 사항**:
1. `faqCards`가 Message에 제대로 전달되었는지 확인
2. FAQ 렌더링 부분이 있는지 확인

---

## 📋 체크리스트

### 서버 상태 확인
```bash
# FastAPI 서버
curl http://localhost:8002/health
# 예상 출력: {"status":"ok","version":"1.0.0"}

# Vite 서버
curl http://localhost:5174
# 예상 출력: <!doctype html>...
```

### 환경 변수 확인
```bash
cat /Users/kdh/Documents/GitHub/faq생성기/faq-generator/public/.env
# 예상 출력: VITE_API_BASE_URL=http://localhost:8002
```

### API 직접 테스트
```bash
curl "http://localhost:8002/api/v1/faqs?category_major=비자/체류&category_minor=비자관련&lang=ko" | python3 -m json.tool
# 예상 출력: {"items": [...], "total": 2, "language": "ko"}
```

---

## 🎯 다음 단계

1. ✅ **브라우저 개발자 콘솔 열기** (`F12` 또는 `Cmd+Option+I`)
2. ✅ **http://localhost:5174 접속**
3. ✅ **"비자/체류" → "비자관련" 클릭**
4. ✅ **콘솔 로그 캡처**
5. 📸 **스크린샷 공유** (필요 시)

---

## 📝 로그 샘플

### 정상 동작 시
```javascript
=== FAQ 조회 시작 ===
대분류: 비자/체류
중분류: 비자관련
언어: ko
API 요청 URL: http://localhost:8002/api/v1/faqs?category_major=%EB%B9%84%EC%9E%90%2F%EC%B2%B4%EB%A5%98&category_minor=%EB%B9%84%EC%9E%90%EA%B4%80%EB%A0%A8&lang=ko
API_BASE_URL: http://localhost:8002
API 응답 상태: 200 OK
API 응답 데이터: {
  items: [
    {faq_id: ' test-055', question: '비자 연장 ', ...},
    {faq_id: ' test-056', question: '비자연장에 필요한 서류 ', ...}
  ],
  total: 2,
  language: 'ko'
}
조회된 FAQ 개수: 2
FAQ 목록: (2) [{…}, {…}]
=== FAQ 조회 완료 ===
```

### 오류 발생 시
```javascript
=== FAQ 조회 오류 ===
에러 상세: TypeError: Failed to fetch
에러 메시지: Failed to fetch
```

---

**준비 완료!** 이제 브라우저에서 테스트하고 콘솔 로그를 확인해주세요! 🚀
