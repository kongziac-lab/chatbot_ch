# Vite 프론트엔드 통합 가이드

## 📋 개요

Vite + React + TypeScript 기반의 현대적인 프론트엔드가 FastAPI 백엔드와 완전히 통합되었습니다.

## 🏗️ 프로젝트 구조

```
faq생성기/faq-generator/
├── app/                    # FastAPI 백엔드
│   ├── main.py            # 정적 파일 제공 설정 포함
│   ├── routers/
│   │   └── chat.py        # 챗봇 API 엔드포인트
│   └── services/
│       └── rag_engine.py  # RAG 엔진
└── public/                # Vite 프론트엔드
    ├── src/
    │   ├── components/
    │   │   ├── LanguageSelector.tsx  # 랜딩 페이지
    │   │   └── ChatPage.tsx          # 채팅 페이지
    │   └── lib/
    │       └── api.ts                # FastAPI 클라이언트
    ├── dist/              # 프로덕션 빌드 (정적 파일)
    ├── .env               # 환경 변수
    └── package.json
```

## 🚀 실행 방법

### 1. 개발 환경 (개발 중)

**터미널 1: FastAPI 서버**
```bash
cd faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

**터미널 2: Vite 개발 서버**
```bash
cd faq생성기/faq-generator/public
npm run dev
```

**접속:**
- 프론트엔드: http://localhost:5173 (또는 자동 할당된 포트)
- 백엔드 API: http://localhost:8002
- API 문서: http://localhost:8002/docs

### 2. 프로덕션 환경 (배포)

**빌드:**
```bash
cd public
npm run build
# → public/dist/ 폴더에 빌드 결과 생성
```

**FastAPI 단독 실행:**
```bash
cd faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

**접속:**
- 전체 서비스: http://localhost:8002/
- API: http://localhost:8002/api/v1/
- API 문서: http://localhost:8002/docs

> FastAPI가 자동으로 `public/dist/` 폴더의 정적 파일을 루트(`/`)에서 제공합니다.

## 🔧 환경 변수 설정

### FastAPI (.env)
```env
# CORS 설정
ALLOWED_ORIGINS=http://localhost:8002,http://localhost:8501,http://localhost:5173
```

### Vite (public/.env)
```env
# VITE_ 접두사 필수!
VITE_API_BASE_URL=http://localhost:8002
```

## 📡 API 연동

### 챗봇 메시지 전송
```typescript
import { chatApi } from '@/lib/api';

// 메시지 전송
const response = await chatApi.sendMessage("안녕하세요", sessionId);
console.log(response.answer);       // 챗봇 응답
console.log(response.session_id);   // 세션 ID
console.log(response.confidence);   // 신뢰도 (high/medium/low)
```

### 피드백 전송
```typescript
await chatApi.sendFeedback({
  message: "안녕하세요",
  answer: "도움이 되었나요?",
  helpful: true,
  comment: "매우 유용했습니다"
});
```

### 헬스 체크
```typescript
const health = await chatApi.healthCheck();
console.log(health.status);   // "ok"
console.log(health.version);  // "1.0.0"
```

## 🧪 테스트

### 1. API 직접 테스트
```bash
# 헬스 체크
curl http://localhost:8002/health

# 챗봇 테스트
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요"}'
```

### 2. 브라우저 테스트

**개발 환경:**
1. http://localhost:5173 접속
2. 언어 선택 (한국어/중국어)
3. 채팅 시작
4. 메시지 입력 및 응답 확인
5. 브라우저 개발자 도구 → Network 탭에서 API 호출 확인

**프로덕션 환경:**
1. `npm run build` 실행
2. FastAPI 서버만 시작
3. http://localhost:8002 접속
4. 동일하게 테스트

## 📊 성능 모니터링

챗봇 성능은 자동으로 수집됩니다:

```bash
# 성능 대시보드 실행
cd faq생성기/faq-generator
streamlit run dashboard/performance.py --server.port 8501
```

**모니터링 항목:**
- 채팅 응답 시간 (검색 + LLM)
- 신뢰도 분포
- 오류율
- 시간대별 사용량

## 🛠️ 문제 해결

### 포트 충돌
```bash
# 포트 사용 중인 프로세스 종료
lsof -ti :8002 | xargs kill -9  # FastAPI
lsof -ti :5173 | xargs kill -9  # Vite
```

### CORS 오류
`.env` 파일의 `ALLOWED_ORIGINS`에 프론트엔드 주소가 포함되어 있는지 확인:
```env
ALLOWED_ORIGINS=http://localhost:8002,http://localhost:5173
```

### API 연결 실패
1. FastAPI 서버가 실행 중인지 확인
2. `public/.env`의 `VITE_API_BASE_URL` 확인
3. 브라우저 콘솔에서 네트워크 오류 확인

### 느린 첫 응답
첫 챗봇 호출 시 BGE-M3 임베딩 모델 로드로 15-20초 소요됩니다. 이후 호출은 빠릅니다.

## 🎯 주요 기능

### 1. 랜딩 페이지 (LanguageSelector)
- 한국어/중국어 선택
- 깔끔한 UI/UX
- 반응형 디자인

### 2. 채팅 페이지 (ChatPage)
- 실시간 메시지 전송
- 타이핑 인디케이터
- 세션 관리
- 오류 처리
- 자동 스크롤

### 3. API 클라이언트 (api.ts)
- 타입 안전한 API 호출
- 자동 에러 처리
- 환경 변수 기반 설정

## 📚 관련 문서

- [성능 모니터링 가이드](./PERFORMANCE_MONITORING_GUIDE.md)
- [자동 동기화 가이드](./QUICK_START_AUTO_SYNC.md)
- [증분 업데이트 가이드](./INCREMENTAL_UPDATE_GUIDE.md)
- [개선 사항 요약](./IMPROVEMENT_SUMMARY.md)

## 🔄 업데이트 히스토리

- **2026-02-28**: Vite 프론트엔드 통합 완료
  - React 19 + TypeScript
  - TailwindCSS + Radix UI
  - FastAPI 정적 파일 제공
  - 실시간 API 연동
  - 세션 관리
  - 오류 처리
