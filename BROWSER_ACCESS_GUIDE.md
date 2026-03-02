# 🌐 브라우저 접속 가이드

## ✅ 서버 상태: 정상 작동 중

```
FastAPI 서버: http://127.0.0.1:8002
프론트엔드: 정적 파일 제공 중
로고 이미지: 정상 로드
FAQ API: 정상 작동 (99개 FAQ)
```

---

## 🎯 올바른 접속 방법

### 1단계: 정확한 URL 사용

**올바른 URL**:
```
http://localhost:8002
```

또는

```
http://127.0.0.1:8002
```

**❌ 잘못된 URL**:
- ~~http://localhost:8000~~
- ~~http://localhost:5173~~
- ~~http://localhost:5174~~

---

### 2단계: 브라우저 캐시 삭제

브라우저가 오래된 버전을 캐싱하고 있을 수 있습니다.

#### 방법 1: 강제 새로고침
```
Mac: Cmd + Shift + R
Windows/Linux: Ctrl + Shift + R
```

#### 방법 2: 개발자 도구에서 캐시 삭제
1. **F12** (개발자 도구 열기)
2. **Application** 또는 **저장소** 탭
3. **Clear storage** 또는 **저장소 지우기**
4. **Clear site data** 클릭
5. 페이지 새로고침

#### 방법 3: 시크릿/프라이빗 모드
```
Chrome/Edge: Cmd/Ctrl + Shift + N
Safari: Cmd + Shift + N
Firefox: Cmd/Ctrl + Shift + P
```

---

### 3단계: 브라우저 콘솔 확인

1. **F12** (개발자 도구)
2. **Console** 탭
3. 빨간색 에러 메시지 확인

**자주 나오는 에러**:

#### 에러 1: "Failed to fetch"
```
원인: 서버가 실행 중이 아니거나 URL이 잘못됨
해결: http://localhost:8002 확인
```

#### 에러 2: "404 Not Found"
```
원인: 잘못된 경로
해결: http://localhost:8002/ (루트 경로)
```

#### 에러 3: "net::ERR_CONNECTION_REFUSED"
```
원인: 서버가 실행 중이 아님
해결: 아래 서버 재시작 가이드 참조
```

---

## 🔧 서버 재시작 (필요 시)

### FastAPI 서버 재시작
```bash
# 1. 기존 서버 종료
lsof -ti :8002 | xargs kill -9

# 2. 서버 시작
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

### 서버 상태 확인
```bash
curl http://localhost:8002/health
```

**정상 응답**:
```json
{"status":"ok","version":"1.0.0"}
```

---

## 📱 다른 브라우저로 테스트

현재 브라우저에서 문제가 계속되면 다른 브라우저로 테스트:

- **Chrome**: http://localhost:8002
- **Safari**: http://localhost:8002
- **Firefox**: http://localhost:8002
- **Edge**: http://localhost:8002

---

## 🔍 네트워크 확인

### 1. 로컬호스트 확인
```bash
ping localhost
```

### 2. 포트 확인
```bash
lsof -ti :8002
```

출력이 있으면 서버가 실행 중입니다.

### 3. 프론트엔드 파일 확인
```bash
ls -la /Users/kdh/Documents/GitHub/faq생성기/faq-generator/public/dist/
```

`index.html`과 `assets/` 폴더가 있어야 합니다.

---

## 🎯 단계별 체크리스트

### ✅ 1단계: 서버 확인
```bash
curl http://localhost:8002/health
```
- ✅ 정상: `{"status":"ok",...}` 출력
- ❌ 오류: 서버 재시작 필요

### ✅ 2단계: 브라우저 접속
```
http://localhost:8002
```

### ✅ 3단계: 강제 새로고침
```
Cmd/Ctrl + Shift + R
```

### ✅ 4단계: 로고 확인
- 랜딩 페이지에 새 로고 표시
- 채팅 페이지에 새 로고 표시

---

## 🆘 여전히 안 되는 경우

### 방법 1: 완전 재시작
```bash
# 1. 모든 서버 종료
lsof -ti :8002 | xargs kill -9
lsof -ti :5173 | xargs kill -9
lsof -ti :5174 | xargs kill -9

# 2. 프로젝트 디렉토리로 이동
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator

# 3. 프론트엔드 재빌드
cd public
npm run build

# 4. FastAPI 서버 시작
cd ..
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload

# 5. 브라우저 접속 (시크릿 모드)
open -na "Google Chrome" --args --incognito http://localhost:8002
```

### 방법 2: 터미널에서 직접 열기
```bash
# Mac
open http://localhost:8002

# 브라우저가 자동으로 열립니다
```

---

## 📊 현재 서버 로그 (정상)

```
✅ FastAPI 서버 실행 중: http://127.0.0.1:8002
✅ 프론트엔드 파일 제공 중: /public/dist
✅ 로고 이미지 로드 성공: kmu-logo-BhuQDC7e.png
✅ API 정상 작동: 99개 FAQ
✅ Google Sheets 연결 정상
```

---

## 💡 자주 묻는 질문

### Q: "This site can't be reached" 에러
**A**: URL을 `http://localhost:8002`로 정확히 입력했는지 확인

### Q: 페이지가 로드되지만 로고/스타일이 안 보임
**A**: 강제 새로고침 (`Cmd+Shift+R` 또는 `Ctrl+Shift+R`)

### Q: 이전 로고가 계속 보임
**A**: 브라우저 캐시 삭제 또는 시크릿 모드 사용

### Q: 포트 8002를 다른 프로그램이 사용 중
**A**: 
```bash
lsof -ti :8002 | xargs kill -9
```

---

**도움이 필요하면 F12 개발자 도구의 Console과 Network 탭을 확인하세요!**
