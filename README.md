# FAQ 생성기 운영 가이드

> **대상 독자**: 국제교류처 담당자 및 시스템 운영자
> **시스템**: 계명대학교 외국인 유학생 FAQ 자동 생성·관리 플랫폼

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [시작·중지 방법](#2-시작중지-방법)
3. [새 문서 업로드 및 FAQ 생성 절차](#3-새-문서-업로드-및-faq-생성-절차)
4. [Google Sheets에서 FAQ 검수하는 방법](#4-google-sheets에서-faq-검수하는-방법)
5. [자주 발생하는 문제 및 해결법](#5-자주-발생하는-문제-및-해결법)
6. [API 키 갱신 방법](#6-api-키-갱신-방법)
7. [백업 및 복구 절차](#7-백업-및-복구-절차)

---

## 1. 시스템 개요

```
┌─────────────────────────────────────────────────────────────┐
│                        FAQ 생성기 구성                        │
├──────────────────┬──────────────────┬───────────────────────┤
│  FAQ 페이지       │  관리자 대시보드   │  API 서버              │
│  (Next.js)       │  (Streamlit)     │  (FastAPI)            │
│  :3000           │  :8501           │  :8000                │
└──────────────────┴──────────────────┴───────────────────────┘
         ↕                   ↕                   ↕
    외국인 유학생        운영 담당자          내부 처리
                                              │
                    ┌─────────────────────────┤
                    ↓                         ↓
             Google Sheets             ChromaDB (벡터 DB)
             (FAQ_Master 등)           (문서 임베딩 저장)
```

### 서비스 URL

| 서비스 | URL | 용도 |
|--------|-----|------|
| FAQ 페이지 | `http://서버IP:3000` | 유학생 FAQ 열람·챗봇 |
| 관리자 대시보드 | `http://서버IP:8501` | 문서 업로드·FAQ 검수·통계 |
| API 문서 | `http://서버IP:8000/docs` | API 명세 확인·테스트 |

### 핵심 Google Sheets 시트

| 시트명 | 역할 |
|--------|------|
| `FAQ_Master` | FAQ 원본 데이터 (16열) |
| `Source_Documents` | 업로드된 문서 목록 |
| `Generation_Log` | FAQ 자동 생성 이력 |
| `FAQ_Feedback` | 도움됨/안됨 원본 기록 |
| `User_Feedback` | 유학생 피드백 상세 |

---

## 2. 시작·중지 방법

### 사전 준비 (최초 1회)

```bash
# 1. 프로젝트 디렉터리로 이동
cd /opt/faq-generator          # 실제 배포 경로에 맞게 수정

# 2. 환경 변수 파일 작성
cp .env.example .env
nano .env                      # 아래 "필수 환경 변수" 참고

# 3. Google 서비스 계정 키 배치
mkdir -p secrets
cp ~/google-credentials.json secrets/

# 4. 실행 권한 부여
chmod +x deploy.sh
```

**필수 환경 변수 (.env)**

```dotenv
SPREADSHEET_ID=1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_CREDENTIALS_FILE=./secrets/google-credentials.json
```

---

### 전체 서비스 시작

```bash
# 빌드 (최초 또는 코드 변경 후)
./deploy.sh build

# 서비스 시작
./deploy.sh up
```

정상 시작 확인:

```
  🌐 FAQ 페이지    : http://localhost:3000
  📊 관리 대시보드  : http://localhost:8501
  🔧 API 서버      : http://localhost:8000
  📖 API 문서      : http://localhost:8000/docs
```

---

### 서비스 중지

```bash
./deploy.sh down
```

> **주의**: `down` 명령은 컨테이너만 중지하며 ChromaDB 볼륨 데이터는 보존됩니다.

---

### 개별 서비스 제어

```bash
# 상태 확인
./deploy.sh status

# 특정 서비스만 재시작 (app / streamlit / frontend)
./deploy.sh restart app
./deploy.sh restart streamlit

# 실시간 로그 확인
./deploy.sh logs            # 전체
./deploy.sh logs app        # API 서버만
./deploy.sh logs streamlit  # 대시보드만
```

---

### 서비스 헬스 체크

```bash
# API 서버 정상 여부 확인
curl http://localhost:8000/health
# 정상 응답: {"status": "ok", "version": "1.0.0"}
```

---

## 3. 새 문서 업로드 및 FAQ 생성 절차

> 전체 소요 시간: 문서 크기에 따라 **3~15분**

### 방법 A — 관리자 대시보드 (권장)

1. 브라우저에서 `http://서버IP:8501` 접속
2. 왼쪽 메뉴 **"문서 관리"** 클릭
3. **파일 선택** 버튼 → PDF 또는 DOCX 파일 선택
4. **문서 유형** 선택:
   - `규정` — 학칙, 내규 등 법규 성격
   - `공지` — 기간 한정 공지사항
   - `안내` — 일반 안내문 (기본값)
5. **업로더** 입력 (예: `국제교류처 홍길동`)
6. **"업로드 및 인덱싱"** 버튼 클릭 → 완료 메시지 확인
7. 화면에 표시된 **문서 ID** 복사 (FAQ 생성에 필요)
8. **대분류 / 중분류** 입력 (예: `학사` / `수강신청`)
9. **"FAQ 자동 생성 시작"** 버튼 클릭
10. **진행 상태 확인** → `completed` 표시 후 Google Sheets 확인

---

### 방법 B — API 직접 호출

#### 1단계: 문서 업로드

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@./학사안내.pdf" \
  -F "doc_type=안내" \
  -F "uploader=국제교류처"
```

응답 예시:

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "학사안내.pdf",
  "total_pages": 12,
  "num_chunks": 38,
  "message": "'학사안내.pdf' 업로드 및 인덱싱 완료 (38개 청크)."
}
```

#### 2단계: FAQ 자동 생성 파이프라인 시작

```bash
curl -X POST http://localhost:8000/api/v1/faq/pipeline/generate \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "550e8400-e29b-41d4-a716-446655440000",
    "department": "국제교류처",
    "category_major": "학사",
    "category_minor": "수강신청"
  }'
```

응답: `{"job_id": "abc123...", "status": "pending"}`

#### 3단계: 진행 상태 확인

```bash
curl http://localhost:8000/api/v1/faq/pipeline/status/abc123...
```

| `status` 값 | 의미 |
|-------------|------|
| `pending` | 대기 중 |
| `running` | 처리 중 |
| `completed` | 완료 — Google Sheets 확인 |
| `failed` | 실패 — `error` 필드 확인 후 재시도 |

---

### FAQ 생성 후 확인 체크리스트

- [ ] Google Sheets `FAQ_Master` 시트에 새 행 추가됨
- [ ] `상태` 열이 `자동생성`으로 설정됨
- [ ] 한국어 질문/답변 내용 확인
- [ ] 중국어 번역 품질 확인
- [ ] `Generation_Log` 시트에 성공 기록 확인

---

## 4. Google Sheets에서 FAQ 검수하는 방법

### FAQ_Master 시트 열 구조

| 열 | 헤더 | 설명 |
|----|------|------|
| A | 고유번호 | UUID (자동 생성, 수정 금지) |
| B | 카테고리(대분류) | 학사 / 생활 / 장학금 등 |
| C | 카테고리(중분류) | 수강신청 / 등록금 등 |
| D | 질문(한국어) | **검수 필수** |
| E | 답변(한국어) | **검수 필수** |
| F | 질문(중국어) | **번역 검수 필수** |
| G | 답변(중국어) | **번역 검수 필수** |
| H | 출처 | 원본 문서명 |
| **I** | **상태** | **`자동생성` → `게시중`으로 변경** |
| J | 생성부서 | 자동 입력 |
| K | 적용범위 | 전체 / 학부 / 대학원 등 |
| L | 생성일 | 자동 입력 |
| M | 수정일 | 자동 업데이트 |
| N | 우선순위 | 숫자 낮을수록 위에 표시 (기본 5) |
| O | 조회수 | 자동 집계 |
| P | 도움됨비율 | 피드백 기반 자동 계산 |

---

### 검수 절차 (단계별)

#### 1단계: 새로 생성된 FAQ 필터링

1. `FAQ_Master` 시트 열기
2. **I열 (상태)** 헤더 클릭 → 필터 아이콘 → **`자동생성`만 체크**
3. 미검수 FAQ 목록 확인

#### 2단계: 내용 검토 기준

| 항목 | 확인 사항 |
|------|-----------|
| 질문(D열) | 유학생이 실제로 물어볼 법한 질문인가? |
| 답변(E열) | 내용이 정확하고 최신인가? 모호하거나 오해 소지 없는가? |
| 질문_중(F열) | 번역이 자연스러운가? 오타/어색한 표현 없는가? |
| 답변_중(G열) | 번역이 정확한가? 한국식 행정 용어가 중국어로 올바르게 변환되었는가? |
| 카테고리(B,C열) | 적절한 분류인가? |
| 우선순위(N열) | 중요도에 따라 조정 (1=최우선, 10=낮음) |

#### 3단계: 검수 결과 처리

**승인**: I열 값을 `자동생성` → **`게시중`** 으로 변경
→ Apps Script가 자동으로 행 색상(초록)을 변경하고 이메일 알림 발송

**반려 (수정 후 게시)**: D~G열 직접 수정 → I열을 `게시중`으로 변경

**삭제**: I열 값을 `삭제` 로 변경 (행을 직접 삭제하지 말 것)

> **중요**: A열(고유번호)은 절대 수정하지 마세요. FAQ 조회수, 피드백과 연결된 고유 키입니다.

---

### 검수 관련 단축 작업

**전체 선택 후 일괄 승인** (Apps Script 메뉴 사용):

1. Sheets 메뉴 → **FAQ 관리** → **필터: 자동생성만 보기**
2. 내용 확인 후 I열을 드래그 선택
3. `Ctrl+H` → `자동생성` → `게시중` 으로 일괄 변환

---

## 5. 자주 발생하는 문제 및 해결법

### 문제 1. 서비스가 시작되지 않는다

**증상**: `./deploy.sh up` 후 컨테이너가 바로 종료됨

```bash
# 원인 확인
./deploy.sh logs app
```

| 오류 메시지 | 원인 | 해결 |
|-------------|------|------|
| `SPREADSHEET_ID 가 비어 있습니다` | .env 미설정 | `.env` 파일에 `SPREADSHEET_ID` 입력 |
| `FileNotFoundError: credentials.json` | 서비스 계정 키 없음 | `secrets/google-credentials.json` 배치 |
| `anthropic.AuthenticationError` | Anthropic API 키 오류 | `ANTHROPIC_API_KEY` 재확인 |
| `Port already in use` | 포트 충돌 | `.env`에서 `API_PORT` 등 변경 |

---

### 문제 2. 문서 업로드는 됐는데 FAQ가 생성되지 않는다

**확인 순서**:

```bash
# 1. 파이프라인 로그 확인
./deploy.sh logs app | grep -E "(ERROR|WARNING|pipeline)"

# 2. Generation_Log 시트에서 status=failed 행 확인
# → error_message 열에서 원인 파악
```

| 원인 | 해결 |
|------|------|
| `청크가 없습니다` | 문서 텍스트 추출 실패 → 스캔 PDF 여부 확인 (스캔본은 OCR 후 업로드) |
| `Anthropic RateLimitError` | API 요청 한도 초과 → 1분 후 재시도 |
| `질문을 추출할 수 없습니다` | 문서 내용이 너무 짧음 → 청크 수 확인 (최소 3개 이상 권장) |

**파이프라인 재시도**:

```bash
curl -X POST http://localhost:8000/api/v1/faq/pipeline/generate \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "이전_문서_ID", "department": "국제교류처"}'
```

---

### 문제 3. Google Sheets 연결 오류

**증상**: 로그에 `gspread.exceptions.APIError` 반복

```bash
./deploy.sh logs app | grep "Sheets API"
```

| 원인 | 해결 |
|------|------|
| 서비스 계정 권한 없음 | Sheets를 서비스 계정 이메일(`...@...iam.gserviceaccount.com`)과 공유 확인 |
| API 할당량 초과 | [Google Cloud Console](https://console.cloud.google.com) → APIs → Sheets API 할당량 확인 |
| 시크릿 파일 마운트 실패 | `docker compose exec app cat /run/secrets/google_credentials` 로 내용 확인 |

---

### 문제 4. 챗봇 답변이 "관련 정보를 찾을 수 없습니다"만 나온다

**원인**: 벡터 DB에 문서가 없거나 검색 품질 저하

```bash
# 벡터 DB 문서 수 확인
curl http://localhost:8000/api/v1/faq/search \
  -H "Content-Type: application/json" \
  -d '{"query": "수강신청", "top_k": 3}'
```

- 결과가 비어 있으면 → **문서를 다시 업로드**
- 결과는 있으나 답변이 부적절하면 → 문서 유형(`doc_type`) 재확인 후 재업로드

---

### 문제 5. 중국어 번역이 이상하다

**즉시 수정**: Google Sheets `FAQ_Master`에서 F, G열 직접 수정 후 저장

**재번역 요청** (대시보드):

1. 관리자 대시보드 → **"FAQ 검수"** 탭
2. 해당 FAQ 선택 → **"재번역"** 버튼 클릭

**API로 재번역**:

```bash
curl -X POST http://localhost:8000/api/v1/translate/qa \
  -H "Content-Type: application/json" \
  -d '{
    "question_ko": "수강신청은 어떻게 하나요?",
    "answer_ko": "포털시스템에서 개강 2주 전에 신청하세요."
  }'
```

---

### 문제 6. 서버가 느리다 / 응답 시간이 길다

```bash
# 컨테이너 리소스 사용량 확인
docker stats

# 캐시 초기화 (필요 시)
curl -X POST http://localhost:8000/admin/flush-view-counts
```

| 느린 부분 | 원인 | 해결 |
|-----------|------|------|
| 최초 기동 | BGE-M3 모델 로드 (~30초) | 정상 동작, 기다리면 됨 |
| FAQ 목록 조회 | Sheets 캐시 만료 | `CACHE_TTL_SECONDS` 늘리기 (기본 300초) |
| FAQ 생성 | Claude API 응답 지연 | 네트워크 확인, API 상태 페이지 확인 |

---

## 6. API 키 갱신 방법

### Anthropic API 키 갱신

1. [console.anthropic.com](https://console.anthropic.com) 로그인
2. **API Keys** → **Create Key** → 새 키 복사
3. 서버에서:

```bash
# .env 파일 수정
nano .env
# ANTHROPIC_API_KEY=sk-ant-api03-새키입력

# API 서버만 재시작 (다운타임 최소화)
./deploy.sh restart app

# 키 적용 확인
curl http://localhost:8000/health
```

> 이전 키는 Anthropic 콘솔에서 즉시 비활성화하세요.

---

### Google 서비스 계정 키 갱신

> **키 갱신 권장 주기**: 12개월 (보안 정책에 따라 조정)

1. [Google Cloud Console](https://console.cloud.google.com) → **IAM 및 관리자** → **서비스 계정**
2. 해당 서비스 계정 클릭 → **키** 탭 → **키 추가** → **새 키 만들기** → JSON 다운로드
3. 서버에서:

```bash
# 기존 키 백업
cp secrets/google-credentials.json secrets/google-credentials.json.bak

# 새 키 배치
cp ~/새키파일.json secrets/google-credentials.json

# Docker secret이 파일을 직접 마운트하므로 재시작 필요
./deploy.sh restart app

# 연결 테스트
curl http://localhost:8000/api/v1/faq/list | head -c 200
```

4. 정상 동작 확인 후 Google Cloud Console에서 **이전 키 삭제**

---

### API 키 보안 점검 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] `secrets/` 폴더가 `.gitignore`에 포함되어 있는가?
- [ ] Git 저장소에 키가 커밋되어 있지 않은가?
  ```bash
  git log --all --full-history -- "*.json" "*.env"
  ```
- [ ] 서비스 계정의 권한이 최소 필요 범위로 제한되어 있는가?
  - 필요 권한: `Google Sheets API` (편집자)

---

## 7. 백업 및 복구 절차

### 백업 대상 및 주기

| 대상 | 위치 | 권장 주기 | 중요도 |
|------|------|-----------|--------|
| Google Sheets | 클라우드 자동 저장 | 매일 수동 내보내기 | 최상 |
| ChromaDB 벡터 데이터 | `chroma_data` Docker 볼륨 | 주 1회 | 상 |
| 환경 설정 파일 | `.env`, `secrets/` | 변경 시마다 | 상 |
| 업로드 원본 문서 | `./uploads/` (임시) | 별도 문서 서버 보관 | 중 |

---

### Google Sheets 백업

**방법 1 — 자동 내보내기 (Google Drive)**

Google Sheets는 Google Drive에 자동 저장됩니다.
버전 기록: Sheets → **파일** → **버전 기록** → **버전 기록 보기**

**방법 2 — CSV 수동 백업**

```bash
# 스크립트 실행 (API 활용)
curl "http://localhost:8000/api/v1/faq/list" \
  | python3 -c "
import json, csv, sys
from datetime import datetime
data = json.load(sys.stdin)
fn = f'faq_backup_{datetime.now():%Y%m%d}.csv'
with open(fn, 'w', newline='', encoding='utf-8-sig') as f:
    if data:
        w = csv.DictWriter(f, fieldnames=data[0].keys())
        w.writeheader()
        w.writerows(data)
print(f'저장: {fn}')
"
```

---

### ChromaDB 벡터 데이터 백업

```bash
# 볼륨 위치 확인
docker volume inspect faq-generator_chroma_data

# 볼륨 백업 (tar 압축)
docker run --rm \
  -v faq-generator_chroma_data:/data \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czf /backup/chroma_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

echo "백업 완료: ./backups/"
ls -lh ./backups/
```

---

### ChromaDB 복구

```bash
# 1. 서비스 중지
./deploy.sh down

# 2. 기존 볼륨 삭제 (주의: 되돌릴 수 없음)
docker volume rm faq-generator_chroma_data

# 3. 새 볼륨 생성 후 복구
docker run --rm \
  -v faq-generator_chroma_data:/data \
  -v $(pwd)/backups:/backup \
  alpine \
  tar xzf /backup/chroma_20250101_120000.tar.gz -C /data

# 4. 서비스 재시작
./deploy.sh up
```

---

### 전체 시스템 재구축 절차

> 서버 교체 또는 재설치 시

```bash
# 1. 새 서버에 Docker 설치
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 2. 프로젝트 복원
git clone <저장소_URL> /opt/faq-generator
cd /opt/faq-generator

# 3. 설정 파일 복원
cp /백업경로/.env .env
mkdir -p secrets
cp /백업경로/google-credentials.json secrets/

# 4. ChromaDB 볼륨 복원 (백업이 있는 경우)
mkdir -p backups
cp /백업경로/chroma_*.tar.gz backups/

# 5. 이미지 빌드 및 서비스 시작
./deploy.sh build
./deploy.sh up

# 6. ChromaDB 복구 (볼륨 복원)
#    위의 "ChromaDB 복구" 절차 참고

# 7. 동작 확인
curl http://localhost:8000/health
```

---

### 백업 자동화 (cron)

```bash
# crontab 편집
crontab -e

# 매일 새벽 3시 ChromaDB 백업, 30일 이상 된 파일 삭제
0 3 * * * cd /opt/faq-generator && \
  docker run --rm \
    -v faq-generator_chroma_data:/data \
    -v $(pwd)/backups:/backup \
    alpine \
    tar czf /backup/chroma_$(date +\%Y\%m\%d).tar.gz -C /data . && \
  find ./backups -name "chroma_*.tar.gz" -mtime +30 -delete \
  >> /var/log/faq-backup.log 2>&1
```

---

## 부록

### 유용한 명령어 모음

```bash
# 컨테이너 내부 접속 (디버깅)
docker compose exec app bash

# ChromaDB 문서 수 확인
docker compose exec app python3 -c "
import chromadb
c = chromadb.PersistentClient('/app/chroma_db')
col = c.get_or_create_collection('faq_documents')
print('저장된 청크 수:', col.count())
"

# 조회수 버퍼 즉시 반영
curl -X POST http://localhost:8000/admin/flush-view-counts

# API 서버 로그 (최근 100줄)
docker compose logs --tail=100 app

# 전체 이미지·컨테이너 정리 (주의: 사용 중인 것 제외)
docker system prune -f
```

### 문의 및 지원

| 구분 | 연락처 |
|------|--------|
| 시스템 오류 | 정보통신처 시스템 담당 |
| FAQ 내용 오류 | 국제교류처 담당자 |
| API 키 / 보안 | 정보보안 담당자 |

---

*최종 수정일: 2025년*
*작성: 국제교류처 시스템 운영팀*
