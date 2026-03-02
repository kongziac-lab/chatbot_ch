# OAuth 2.0 빠른 시작 가이드

## 🚀 3단계로 시작하기

### 1단계: OAuth 2.0 클라이언트 ID 생성 (5분)

#### 1. Google Cloud Console 접속
👉 https://console.cloud.google.com

#### 2. 프로젝트 선택 또는 생성
- 조직 계정이 아닌 **개인 Gmail 계정**으로 로그인 권장
- 상단에서 프로젝트 선택 또는 **새 프로젝트** 생성

#### 3. Google Sheets API 활성화
1. 왼쪽 메뉴 → **API 및 서비스** → **라이브러리**
2. "Google Sheets API" 검색
3. **사용 설정** 클릭

#### 4. OAuth 동의 화면 구성
1. 왼쪽 메뉴 → **API 및 서비스** → **OAuth 동의 화면**
2. 사용자 유형: **외부** 선택
3. **만들기** 클릭
4. 필수 정보 입력:
   - 앱 이름: `FAQ 생성기`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처: 본인 이메일
5. **저장 후 계속** (3번 클릭하여 완료)

#### 5. OAuth 2.0 클라이언트 ID 생성
1. 왼쪽 메뉴 → **API 및 서비스** → **사용자 인증 정보**
2. **+ 사용자 인증 정보 만들기** → **OAuth 클라이언트 ID**
3. 애플리케이션 유형: **데스크톱 앱**
4. 이름: `FAQ 생성기`
5. **만들기** 클릭
6. **JSON 다운로드** 버튼 클릭

---

### 2단계: OAuth 클라이언트 ID 파일 배치 (1분)

터미널에서 실행:

```bash
# 프로젝트 디렉터리로 이동
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator

# 다운로드한 JSON 파일을 oauth_client_secret.json으로 복사
cp ~/Downloads/client_secret_*.json oauth_client_secret.json

# 파일 확인
ls -la oauth_client_secret.json
```

---

### 3단계: OAuth 2.0 인증 실행 (2분)

```bash
# 초기 인증 스크립트 실행
python3 oauth_setup.py
```

**동작**:
1. 브라우저가 자동으로 열림
2. Google 계정 로그인
3. **"This app isn't verified"** 경고가 나오면:
   - "Advanced" 클릭
   - "Go to FAQ 생성기 (unsafe)" 클릭
   - ⚠️ 본인이 만든 앱이므로 안전합니다
4. 권한 승인
5. `token.json` 파일 자동 생성

---

## 🎉 완료!

인증이 완료되면 이제 서비스를 실행할 수 있습니다:

```bash
# Streamlit 대시보드
streamlit run dashboard/app.py

# FastAPI 서버
uvicorn app.main:app --reload

# Docker Compose
./deploy.sh up
```

---

## ⚠️ 주의사항

### Google Sheets 공유 필수

OAuth 인증한 계정으로 Google Sheets에 접근하려면:

1. Google Sheets 열기: https://docs.google.com/spreadsheets/d/1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo/edit
2. **공유** 버튼 클릭
3. OAuth 인증한 Google 계정 이메일 추가
4. 권한: **편집자** 선택
5. **전송** 클릭

---

## 🔧 문제 해결

### 문제: "OAuth 2.0 클라이언트 ID 파일을 찾을 수 없습니다"

**해결**:
```bash
# 파일 위치 확인
ls -la oauth_client_secret.json

# 파일이 없으면 다시 다운로드하고 복사
cp ~/Downloads/client_secret_*.json oauth_client_secret.json
```

---

### 문제: "This app isn't verified" 경고

**해결**: 정상입니다. 개발 단계에서 발생하는 경고입니다.

1. **"Advanced"** 또는 **"고급"** 클릭
2. **"Go to FAQ 생성기 (unsafe)"** 클릭
3. **"Continue"** 클릭

---

### 문제: 스프레드시트 접근 실패

**해결**: OAuth 인증한 계정이 스프레드시트에 접근 권한이 없습니다.

Google Sheets에서 해당 계정에 **편집자 권한** 부여 필요.

---

## 📚 더 자세한 가이드

상세한 내용은 `README_OAUTH.md` 파일을 참고하세요.

---

## ✅ 체크리스트

- [ ] Google Cloud Console에 OAuth 2.0 클라이언트 ID 생성
- [ ] `oauth_client_secret.json` 파일 다운로드 및 배치
- [ ] `python3 oauth_setup.py` 실행
- [ ] 브라우저에서 Google 로그인 및 권한 승인
- [ ] `token.json` 파일 생성 확인
- [ ] Google Sheets에 OAuth 계정 공유
- [ ] 서비스 실행 성공

모두 완료되면 FAQ 생성기를 사용할 수 있습니다! 🎉
