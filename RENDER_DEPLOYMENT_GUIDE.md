# Render 배포 가이드

FAQ 생성기 백엔드(FastAPI)를 Render에 배포하는 방법과 Vercel 프론트엔드 연동을 안내합니다.

---

## 1. Render MCP 설정 (Cursor)

Cursor에서 Render 서비스를 직접 관리하려면 MCP를 설정합니다.

### 1-1. Render API 키 생성

1. [Render Dashboard](https://dashboard.render.com/) → **Account Settings** → **API Keys**
2. **Create API Key** 클릭
3. 생성된 키 복사 (한 번만 표시됨)

### 1-2. Cursor MCP 설정

`~/.cursor/mcp.json`에 Render MCP가 이미 추가되어 있습니다. **YOUR_RENDER_API_KEY**를 실제 API 키로 교체하세요:

```json
"render": {
  "url": "https://mcp.render.com/mcp",
  "headers": {
    "Authorization": "Bearer rnd_xxxxxxxxxxxx"
  }
}
```

### 1-3. 워크스페이스 지정

Cursor 채팅에서 다음처럼 입력하여 워크스페이스를 지정합니다:

```
Set my Render workspace to [워크스페이스 이름]
```

이후 `List my Render services`, `Pull logs for faq-generator-api` 등으로 서비스를 관리할 수 있습니다.

---

## 2. Render 백엔드 배포

### 2-1. Blueprint로 배포 (권장)

1. [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
2. GitHub 저장소 연결 후 `render.yaml`이 있는 저장소 선택
3. **Apply** 클릭

### 2-2. 수동 Web Service 생성

1. **New** → **Web Service**
2. 저장소 연결
3. 설정:
   - **Name**: faq-generator-api
   - **Region**: Oregon (또는 가까운 지역)
   - **Branch**: main
   - **Root Directory**: (비워두기, 프로젝트 루트)
   - **Runtime**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Instance Type**: Free

---

## 3. 환경 변수 설정

Render 대시보드 → 서비스 → **Environment** 탭에서 다음 변수를 설정합니다.

### 필수

| 변수 | 설명 | 예시 |
|------|------|------|
| `SPREADSHEET_ID` | Google 스프레드시트 ID (URL `/d/<ID>/edit` 부분) | `1abc...xyz` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` |

### 권장

| 변수 | 설명 | 예시 |
|------|------|------|
| `ALLOWED_ORIGINS` | CORS 허용 오리진 (콤마 구분) | `https://your-app.vercel.app,https://your-domain.com` |
| `WEBHOOK_SECRET` | Google Apps Script Webhook 인증 키 | `faq-auto-sync-secret-2026` |
| `CHROMA_PERSIST_DIR` | ChromaDB 저장 경로 | `/data/chroma_db` (디스크 마운트 시) |

### 선택

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `EMBEDDING_MODEL_NAME` | 임베딩 모델 | `BAAI/bge-m3` |
| `CACHE_TTL_SECONDS` | 캐시 TTL (초) | `300` |

---

## 4. OAuth 파일 (Google Sheets 연동)

Google Sheets API는 OAuth 2.0 인증이 필요합니다. Render에서는 **Secret Files**로 JSON 파일을 업로드합니다.

### 4-1. Secret Files 업로드

1. 서비스 → **Environment** → **Secret Files**
2. **Add Secret File** 클릭
3. **Filename**: `oauth_client_secret.json`
4. **Contents**: Google Cloud Console에서 다운로드한 OAuth 클라이언트 JSON 내용 붙여넣기

### 4-2. 환경 변수로 경로 지정

Secret File 업로드 시 Render는 `/etc/secrets/` 아래에 파일을 배치합니다. 환경 변수 추가:

| 변수 | 값 |
|------|-----|
| `OAUTH_CLIENT_SECRETS_PATH` | `/etc/secrets/oauth_client_secret.json` |
| `OAUTH_TOKEN_PATH` | `/data/token.json` (디스크 사용 시) 또는 `/tmp/token.json` |

> **참고**: `token.json`은 최초 OAuth 인증 후 생성됩니다. 로컬에서 인증 후 `token.json`을 Secret File로 업로드하거나, 배포 후 한 번 수동 인증이 필요할 수 있습니다.

---

## 5. 디스크 (ChromaDB 영구 저장)

Free 플랜은 디스크를 지원하지 않습니다. ChromaDB 데이터는 재배포 시 초기화됩니다.

**Starter 플랜 이상**에서 디스크 사용:

1. 서비스 → **Disks** → **Add Disk**
2. **Name**: chroma-data
3. **Mount Path**: /data
4. **Size**: 1 GB

`render.yaml`의 `disk` 주석을 해제하고 `CHROMA_PERSIST_DIR=/data/chroma_db`로 설정합니다.

---

## 6. Vercel 프론트엔드 연동

Render 배포가 완료되면 서비스 URL(예: `https://faq-generator-api.onrender.com`)이 발급됩니다.

### Vercel 환경 변수

Vercel 프로젝트 → **Settings** → **Environment Variables**:

| 변수 | 값 |
|------|-----|
| `VITE_API_BASE_URL` | `https://faq-generator-api.onrender.com` |

### Render ALLOWED_ORIGINS

Render 환경 변수 `ALLOWED_ORIGINS`에 Vercel URL 추가:

```
https://your-vercel-app.vercel.app
```

---

## 7. 체크리스트

- [ ] Render API 키 생성 및 Cursor MCP에 설정
- [ ] Render Web Service 배포 (Blueprint 또는 수동)
- [ ] `SPREADSHEET_ID`, `OPENAI_API_KEY` 환경 변수 설정
- [ ] `ALLOWED_ORIGINS`에 Vercel URL 추가
- [ ] OAuth Secret File 업로드 (`oauth_client_secret.json`)
- [ ] Vercel `VITE_API_BASE_URL`에 Render URL 설정
- [ ] (선택) Starter 플랜에서 디스크 추가 후 ChromaDB 경로 설정

---

## 8. 트러블슈팅

### "열린 포트가 감지되지 않았습니다"

앱이 8000 포트에 바인딩되어 Render의 PORT(10000)와 맞지 않을 때 발생합니다.

**해결**: Render 대시보드 → 서비스 → **Settings** → **Build & Deploy** → **Start Command**에 다음 설정:

```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Blueprint 사용 시 `render.yaml`의 `dockerCommand`가 자동 적용됩니다.

### Cold Start

Render Free 플랜은 15분 비활성 시 슬립합니다. 첫 요청 시 30초~1분 정도 지연될 수 있습니다.

### OAuth 인증 실패

- `OAUTH_CLIENT_SECRETS_PATH`가 올바른지 확인
- Google Cloud Console에서 OAuth 동의 화면 및 리디렉션 URI 설정 확인

### CORS 오류

- `ALLOWED_ORIGINS`에 프론트엔드 URL이 정확히 포함되었는지 확인
- 프로토콜(`https://`) 및 후행 슬래시 없이 입력
