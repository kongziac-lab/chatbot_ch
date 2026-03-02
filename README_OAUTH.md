# OAuth 2.0 사용자 인증 설정 가이드

서비스 계정 키 대신 **OAuth 2.0 사용자 인증**을 사용하여 Google Sheets API에 접근하는 방법입니다.

---

## 🎯 OAuth 2.0을 사용하는 이유

| 항목 | 서비스 계정 키 | OAuth 2.0 사용자 인증 |
|------|---------------|---------------------|
| **키 파일** | JSON 파일 필요 | 필요 없음 |
| **보안** | 키 유출 위험 | 더 안전함 |
| **권한** | 서비스 계정에 부여 | 사용자 계정 권한 사용 |
| **조직 정책** | 생성 차단될 수 있음 | 차단되지 않음 |
| **최초 설정** | 간단 | 브라우저 인증 필요 |

---

## 📋 사전 준비

1. Google 계정
2. Google Cloud 프로젝트
3. Google Sheets API 활성화

---

## 🔧 설정 단계

### 1단계: Google Cloud Console에서 OAuth 2.0 클라이언트 ID 생성

#### 1-1. Google Cloud Console 접속

https://console.cloud.google.com 접속

#### 1-2. 프로젝트 선택 또는 생성

- 상단에서 프로젝트 선택
- 또는 **새 프로젝트** 생성

#### 1-3. Google Sheets API 활성화

1. 왼쪽 메뉴 → **API 및 서비스** → **라이브러리**
2. "Google Sheets API" 검색
3. **사용 설정** 클릭

#### 1-4. OAuth 동의 화면 구성 (최초 1회)

1. 왼쪽 메뉴 → **API 및 서비스** → **OAuth 동의 화면**
2. 사용자 유형: **외부** 선택 (조직 계정이면 **내부** 가능)
3. **만들기** 클릭
4. 필수 정보 입력:
   - 앱 이름: `FAQ 생성기`
   - 사용자 지원 이메일: 본인 이메일
   - 개발자 연락처 정보: 본인 이메일
5. **저장 후 계속** 클릭
6. 범위 추가 (선택사항) - 건너뛰기
7. 테스트 사용자 추가 - 본인 이메일 추가
8. **저장 후 계속** 클릭

#### 1-5. OAuth 2.0 클라이언트 ID 생성

1. 왼쪽 메뉴 → **API 및 서비스** → **사용자 인증 정보**
2. 상단 **+ 사용자 인증 정보 만들기** → **OAuth 클라이언트 ID** 선택
3. 애플리케이션 유형: **데스크톱 앱** 선택
4. 이름: `FAQ 생성기` (또는 원하는 이름)
5. **만들기** 클릭

#### 1-6. JSON 파일 다운로드

1. 생성된 클라이언트 ID 우측의 **다운로드** 버튼 클릭
2. JSON 파일 다운로드됨 (예: `client_secret_xxxxx.json`)

---

### 2단계: OAuth 클라이언트 ID 파일 배치

다운로드한 JSON 파일을 프로젝트 폴더에 복사:

```bash
# 프로젝트 디렉터리로 이동
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator

# 다운로드한 파일을 oauth_client_secret.json으로 복사
cp ~/Downloads/client_secret_xxxxx.json oauth_client_secret.json
```

---

### 3단계: .env 파일 확인

`.env` 파일이 다음과 같이 설정되어 있는지 확인:

```dotenv
# OAuth 2.0 클라이언트 ID JSON 파일 경로
OAUTH_CLIENT_SECRETS_PATH=./oauth_client_secret.json

# OAuth 2.0 액세스 토큰 저장 경로 (자동 생성)
OAUTH_TOKEN_PATH=./token.json

# Google 스프레드시트 ID
SPREADSHEET_ID=1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo
```

---

### 4단계: 초기 인증 실행

OAuth 2.0 초기 인증 스크립트를 실행합니다:

```bash
python3 oauth_setup.py
```

**동작**:

1. OAuth 클라이언트 ID 파일 검증
2. 브라우저가 자동으로 열림
3. Google 계정 로그인
4. FAQ 생성기 앱에 권한 부여
5. `token.json` 파일에 액세스 토큰 저장
6. Google Sheets 연결 테스트

**화면 예시**:

```
======================================================================
FAQ 생성기 - OAuth 2.0 초기 인증
======================================================================

📋 설정 확인:
  - OAuth 클라이언트 ID: ./oauth_client_secret.json
  - 토큰 저장 경로: ./token.json
  - 스프레드시트 ID: 1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3...

🔍 OAuth 2.0 클라이언트 ID 검증 중...
   ✅ OAuth 2.0 클라이언트 ID 설정이 올바릅니다.

🔐 OAuth 2.0 인증 시작...

👉 잠시 후 브라우저가 열립니다.
   1. Google 계정으로 로그인
   2. 'FAQ 생성기' 앱에 권한 부여
   3. '계속' 또는 '허용' 클릭

준비되었으면 Enter 키를 누르세요...
```

---

### 5단계: 서비스 실행

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

## 🔄 토큰 갱신

OAuth 2.0 액세스 토큰은 다음과 같이 자동 관리됩니다:

- **최초 인증**: 브라우저에서 수동 인증 (1회)
- **이후 실행**: `token.json`에서 자동 로드
- **토큰 만료**: 자동으로 갱신 (브라우저 인증 불필요)
- **토큰 무효화**: 재인증 필요 (다시 `python3 oauth_setup.py` 실행)

---

## 🔒 보안 주의사항

### OAuth 파일 보호

**절대 Git에 커밋하지 마세요!**

```.gitignore
# OAuth 2.0 인증 파일
oauth_client_secret.json
token.json
```

### 파일 권한 설정

```bash
# OAuth 클라이언트 ID 파일 권한 제한
chmod 600 oauth_client_secret.json

# 토큰 파일 권한 제한
chmod 600 token.json
```

---

## ❓ 문제 해결

### 문제 1: "OAuth 2.0 클라이언트 ID 파일을 찾을 수 없습니다"

**원인**: `oauth_client_secret.json` 파일이 없음

**해결**:
1. Google Cloud Console에서 OAuth 클라이언트 ID 다운로드
2. 파일을 `oauth_client_secret.json`으로 저장
3. 프로젝트 루트 디렉터리에 배치

---

### 문제 2: "This app isn't verified" 경고

**원인**: Google이 앱을 검증하지 않음 (개발 단계에서 정상)

**해결**:
1. "Advanced" 또는 "고급" 클릭
2. "Go to FAQ 생성기 (unsafe)" 클릭
3. "Continue" 또는 "계속" 클릭

⚠️ 본인이 만든 앱이므로 안전합니다.

---

### 문제 3: 스프레드시트 접근 실패

**원인**: OAuth 인증한 계정이 스프레드시트에 접근 권한이 없음

**해결**:
1. Google Sheets 열기
2. **공유** 버튼 클릭
3. OAuth 인증한 Google 계정 이메일 추가
4. 권한: **편집자** 선택
5. **전송** 클릭

---

### 문제 4: 토큰 갱신 실패

**원인**: Refresh token이 만료되거나 무효화됨

**해결**:
```bash
# 기존 토큰 삭제
rm token.json

# 재인증
python3 oauth_setup.py
```

---

## 🔄 서비스 계정 키 방식으로 되돌리기

OAuth 2.0 대신 다시 서비스 계정 키를 사용하려면:

1. **Git에서 이전 버전 복원**:
   ```bash
   git checkout HEAD~1 -- app/config.py app/services/sheet_manager.py
   ```

2. **`.env` 파일 수정**:
   ```dotenv
   GOOGLE_SHEETS_CREDENTIALS_PATH=./secrets/google-credentials.json
   SPREADSHEET_ID=your_spreadsheet_id
   ```

3. **서비스 계정 키 파일 배치**:
   ```bash
   mkdir -p secrets
   cp ~/google-credentials.json secrets/
   ```

---

## 📚 참고 자료

- [Google OAuth 2.0 개요](https://developers.google.com/identity/protocols/oauth2)
- [Google Sheets API 문서](https://developers.google.com/sheets/api)
- [gspread 라이브러리](https://docs.gspread.org/)

---

## ✅ 체크리스트

설정이 완료되었는지 확인하세요:

- [ ] Google Cloud 프로젝트 생성
- [ ] Google Sheets API 활성화
- [ ] OAuth 동의 화면 구성
- [ ] OAuth 2.0 클라이언트 ID 생성
- [ ] `oauth_client_secret.json` 파일 다운로드 및 배치
- [ ] `.env` 파일 설정
- [ ] `python3 oauth_setup.py` 실행 및 인증 완료
- [ ] `token.json` 파일 생성 확인
- [ ] Google Sheets 연결 테스트 성공
- [ ] `.gitignore`에 OAuth 파일 추가 확인

---

**문의**: 문제가 발생하면 `oauth_setup.py`의 에러 메시지를 확인하거나 README.md를 참고하세요.
