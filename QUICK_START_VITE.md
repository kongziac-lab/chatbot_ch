# 🚀 Vite 프론트엔드 빠른 시작 가이드

## 1️⃣ 서버 시작 (2분)

### FastAPI 백엔드
```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

### Vite 개발 서버 (개발 중)
```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator/public
npm run dev
```

## 2️⃣ 접속

### 개발 환경
- **프론트엔드**: http://localhost:5173
- **백엔드 API**: http://localhost:8002/docs

### 프로덕션 환경
```bash
# 빌드
cd public && npm run build

# 접속: http://localhost:8002
```

## 3️⃣ 테스트 체크리스트

- [ ] 언어 선택 (한국어/중국어)
- [ ] 채팅 입력
- [ ] 챗봇 응답 확인
- [ ] 네트워크 탭에서 API 호출 확인
- [ ] 오류 처리 테스트 (FastAPI 중단 후)

## 4️⃣ 성능 모니터링 (선택)

```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
streamlit run dashboard/performance.py
```

접속: http://localhost:8501

## ⚠️ 문제 발생 시

```bash
# 포트 충돌 해결
lsof -ti :8002 | xargs kill -9  # FastAPI
lsof -ti :5173 | xargs kill -9  # Vite

# 캐시 정리
cd public
rm -rf node_modules/.vite dist
npm install
npm run dev
```

## 📝 주요 파일

| 파일 | 역할 |
|------|------|
| `public/src/components/ChatPage.tsx` | 채팅 UI |
| `public/src/lib/api.ts` | API 클라이언트 |
| `public/.env` | 프론트엔드 환경 변수 |
| `app/main.py` | FastAPI 서버 + 정적 파일 제공 |

## 🎯 다음 단계

1. ✅ **완료**: 프론트엔드-백엔드 연동
2. 🔜 **TODO**: 카테고리 기반 FAQ 검색 추가
3. 🔜 **TODO**: 관련 FAQ 표시 UI
4. 🔜 **TODO**: 다국어 번역 UI

---

**전체 문서**: [VITE_FRONTEND_INTEGRATION_GUIDE.md](./VITE_FRONTEND_INTEGRATION_GUIDE.md)
