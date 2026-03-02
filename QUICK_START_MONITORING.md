# 성능 모니터링 Quick Start

## 🚀 3분 설정 가이드

### 1️⃣ 패키지 설치 (1분)

```bash
cd faq-generator
pip3 install plotly==5.24.1
```

또는 전체 재설치:
```bash
pip3 install -r requirements.txt
```

---

### 2️⃣ FastAPI 서버 실행 (1분)

```bash
# 서버 시작
uvicorn app.main:app --port 8002

# 또는 백그라운드 실행
nohup uvicorn app.main:app --port 8002 &
```

**확인**:
```bash
curl http://localhost:8002/health
# {"status":"ok","version":"1.0.0"}
```

---

### 3️⃣ 메트릭 생성 (1분)

#### Step 1: FAQ 동기화
```bash
curl -X POST http://localhost:8002/api/v1/faq/sync-vector-db
```

#### Step 2: 챗봇 테스트
```bash
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "졸업 요건은?", "session_id": null}'
```

#### Step 3: 메트릭 확인
```bash
curl http://localhost:8002/api/v1/metrics/summary?hours=1
```

---

### 4️⃣ 대시보드 실행 (즉시)

**새 터미널 열기**:
```bash
cd faq-generator
streamlit run dashboard/performance.py --server.port 8503
```

**접속**:
```
http://localhost:8503
```

---

## ✅ 완료!

이제 실시간 성능 모니터링 대시보드에서:
- 🔄 동기화 성능
- 🔍 검색 성능
- 💬 챗봇 응답 시간
- 📊 실시간 차트

모두 확인 가능합니다! 🎉

---

## 📊 대시보드 미리보기

### 전체 메트릭
- 총 동기화 횟수 및 성공률
- 평균 동기화/검색/챗봇 시간
- 신뢰도 분포

### 차트
- 동기화 유형 분포 (파이 차트)
- 검색 응답 시간 추이 (산점도)
- 챗봇 응답 시간 (선 그래프)
- 신뢰도 분포 (파이 차트)

### 로그
- 최근 20개 동기화/검색/챗봇 로그
- 필터링 및 정렬 가능

---

## 🔧 트러블슈팅

### ❌ "API 서버에 연결할 수 없습니다"
```bash
# 서버 확인
curl http://localhost:8002/health

# 서버 재시작
uvicorn app.main:app --port 8002
```

### ❌ "메트릭 데이터가 없습니다"
```bash
# FAQ 동기화로 데이터 생성
curl -X POST http://localhost:8002/api/v1/faq/sync-vector-db

# 챗봇 테스트로 데이터 생성
curl -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### ❌ plotly 관련 에러
```bash
# plotly 설치
pip3 install plotly==5.24.1

# 대시보드 재시작
streamlit run dashboard/performance.py --server.port 8503
```

---

## 📚 상세 가이드

더 자세한 내용은:
- **PERFORMANCE_MONITORING_GUIDE.md**: 완벽 가이드
- **CHANGELOG.md**: v1.3.0 업데이트 내역

---

**버전**: v1.3.0  
**작성일**: 2026-02-28
