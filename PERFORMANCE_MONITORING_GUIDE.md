# 성능 모니터링 가이드

## 📊 개요

FAQ 생성기의 **동기화 시간**, **검색 성능**, **챗봇 응답 시간**을 실시간으로 모니터링하는 시스템입니다.

---

## ✨ 주요 기능

### 1️⃣ 자동 메트릭 수집
- ✅ **동기화 성능**: 소요 시간, FAQ 수, 청크 수, 증분 vs 전체
- ✅ **검색 성능**: 응답 시간, 결과 수, 컬렉션별 통계
- ✅ **챗봇 성능**: 전체/검색/LLM 시간, 신뢰도 분포

### 2️⃣ REST API
- ✅ 최근 메트릭 조회 (실시간)
- ✅ 통계 집계 (1-168시간)
- ✅ 전체 메트릭 요약

### 3️⃣ Streamlit 대시보드
- ✅ 실시간 모니터링 UI
- ✅ 인터랙티브 차트 (Plotly)
- ✅ 상세 로그 테이블

---

## 🚀 빠른 시작

### 1단계: FastAPI 서버 실행

```bash
cd faq-generator
uvicorn app.main:app --port 8002
```

### 2단계: 성능 대시보드 실행

```bash
streamlit run dashboard/performance.py --server.port 8503
```

### 3단계: 대시보드 접속

```
http://localhost:8503
```

---

## 📁 파일 구조

```
faq-generator/
├── app/
│   ├── utils/
│   │   └── metrics.py          # 메트릭 수집 모듈 ✨
│   ├── routers/
│   │   ├── chat.py             # 챗봇 메트릭 통합
│   │   ├── faq.py              # 동기화 메트릭 통합
│   │   ├── metrics.py          # 메트릭 API ✨
│   ├── services/
│   │   ├── rag_engine.py       # 검색 메트릭 통합
│   │   └── chat_service.py     # 챗봇 메트릭 통합
├── dashboard/
│   └── performance.py          # Streamlit 대시보드 ✨
├── metrics/                    # 메트릭 데이터 저장 (자동 생성)
│   ├── sync_metrics.jsonl      # 동기화 메트릭
│   ├── search_metrics.jsonl    # 검색 메트릭
│   └── chat_metrics.jsonl      # 챗봇 메트릭
```

---

## 📊 대시보드 화면

### 전체 메트릭 요약

| 메트릭 | 내용 |
|--------|------|
| 🔄 총 동기화 횟수 | 증분/전체 동기화 통계 |
| ⏱️ 평균 동기화 시간 | 성능 추이 |
| 🔍 총 검색 횟수 | 검색 빈도 |
| ⏱️ 평균 검색 시간 | 응답 속도 |
| 💬 총 챗봇 응답 | 대화 수 |
| ⏱️ 평균 응답 시간 | 사용자 경험 |

### 동기화 성능

**차트**:
- 증분 vs 전체 동기화 비율 (파이 차트)
- 최근 동기화 로그 (타임라인)

**통계**:
- 성공률
- 평균 처리 시간
- FAQ/청크 수

### 검색 성능

**차트**:
- 검색 응답 시간 추이 (산점도)
- 컬렉션별 성능 비교

**통계**:
- 평균 검색 시간
- 평균 결과 수
- 컬렉션별 통계

### 챗봇 성능

**차트**:
- 검색 vs LLM 시간 비교 (막대 차트)
- 응답 시간 추이 (선 그래프)
- 신뢰도 분포 (파이 차트)

**통계**:
- 평균 전체/검색/LLM 시간
- 신뢰도별 분포
- 평균 청크 수

---

## 🔧 API 사용법

### 기본 URL
```
http://localhost:8002/api/v1/metrics
```

### 1️⃣ 동기화 메트릭

#### 최근 동기화 조회
```bash
GET /api/v1/metrics/sync/recent?limit=10
```

**응답 예시**:
```json
[
  {
    "timestamp": "2026-02-28T15:30:45.123",
    "sync_type": "incremental",
    "duration_ms": 523.4,
    "faq_count": 3,
    "chunk_count": 6,
    "deleted_count": 6,
    "success": true,
    "error": null
  }
]
```

#### 동기화 통계
```bash
GET /api/v1/metrics/sync/stats?hours=24
```

**응답 예시**:
```json
{
  "period_hours": 24,
  "total_syncs": 15,
  "incremental_syncs": 12,
  "full_syncs": 3,
  "success_rate": 1.0,
  "avg_duration_ms": 487.3
}
```

### 2️⃣ 검색 메트릭

#### 최근 검색 조회
```bash
GET /api/v1/metrics/search/recent?limit=10
```

#### 검색 통계
```bash
GET /api/v1/metrics/search/stats?hours=24
```

### 3️⃣ 챗봇 메트릭

#### 최근 챗봇 조회
```bash
GET /api/v1/metrics/chat/recent?limit=10
```

#### 챗봇 통계
```bash
GET /api/v1/metrics/chat/stats?hours=24
```

### 4️⃣ 전체 메트릭 요약

```bash
GET /api/v1/metrics/summary?hours=24
```

**응답 예시**:
```json
{
  "period_hours": 24,
  "sync": {
    "total_syncs": 15,
    "success_rate": 1.0,
    "avg_duration_ms": 487.3
  },
  "search": {
    "total_searches": 234,
    "success_rate": 0.99,
    "avg_duration_ms": 45.2
  },
  "chat": {
    "total_chats": 89,
    "success_rate": 1.0,
    "avg_total_duration_ms": 3821.5,
    "avg_search_duration_ms": 153.4,
    "avg_llm_duration_ms": 3668.1,
    "confidence_distribution": {
      "high": 67,
      "medium": 18,
      "low": 4
    }
  }
}
```

---

## 📈 메트릭 데이터 구조

### 동기화 메트릭 (SyncMetric)
```python
{
    "timestamp": str,         # ISO 8601 형식
    "sync_type": str,         # "full" or "incremental"
    "duration_ms": float,     # 소요 시간 (밀리초)
    "faq_count": int,         # 처리된 FAQ 수
    "chunk_count": int,       # 생성된 청크 수
    "deleted_count": int,     # 삭제된 청크 수
    "success": bool,          # 성공 여부
    "error": str | null       # 에러 메시지
}
```

### 검색 메트릭 (SearchMetric)
```python
{
    "timestamp": str,
    "query": str,             # 검색 쿼리 (50자 제한)
    "collection": str,        # 컬렉션 이름
    "top_k": int,             # 요청한 결과 수
    "duration_ms": float,
    "result_count": int,      # 실제 반환된 결과 수
    "use_mmr": bool,          # MMR 리랭킹 사용 여부
    "success": bool,
    "error": str | null
}
```

### 챗봇 메트릭 (ChatMetric)
```python
{
    "timestamp": str,
    "message": str,           # 사용자 메시지 (100자 제한)
    "language": str,          # "ko" or "zh"
    "duration_ms": float,     # 전체 소요 시간
    "search_duration_ms": float,   # 검색 시간
    "llm_duration_ms": float,      # LLM 호출 시간
    "confidence": str,        # "high", "medium", "low"
    "chunk_count": int,       # 검색된 청크 수
    "success": bool,
    "error": str | null
}
```

---

## 🔍 성능 분석 예시

### 시나리오 1: 동기화 성능 저하

**증상**:
- 증분 업데이트 평균 시간 > 1000ms

**분석**:
```bash
GET /api/v1/metrics/sync/recent?limit=20
```

**원인 파악**:
- FAQ 수가 급증했나?
- 청크 수가 비정상적으로 많나?
- 에러가 발생했나?

**해결**:
- FAQ 수 제한 또는 배치 처리
- 동기화 간격 조정

### 시나리오 2: 챗봇 응답 느림

**증상**:
- 평균 응답 시간 > 5000ms

**분석**:
```bash
GET /api/v1/metrics/chat/stats?hours=1
```

**원인 파악**:
1. **검색 시간 > 500ms**: 벡터 DB 성능 문제
   - 컬렉션 크기 확인
   - 인덱스 최적화
   
2. **LLM 시간 > 4000ms**: OpenAI API 응답 느림
   - 모델 변경 (gpt-4o → gpt-4o-mini)
   - 프롬프트 길이 단축
   
3. **검색 + LLM 모두 느림**: 시스템 리소스 부족
   - CPU/메모리 사용률 확인
   - 서버 스케일업

### 시나리오 3: 검색 정확도 저하

**증상**:
- 평균 결과 수 < 1
- Confidence "low" 비율 증가

**분석**:
```bash
GET /api/v1/metrics/chat/recent?limit=50
```

**원인 파악**:
- FAQ 벡터 동기화 실패?
- 임베딩 모델 문제?
- 쿼리 품질 문제?

**해결**:
- 전체 동기화 재실행
- FAQ 품질 검수
- 쿼리 전처리 개선

---

## 📝 로그 파일 관리

### 저장 위치
```
/faq-generator/metrics/
├── sync_metrics.jsonl      # 동기화 로그
├── search_metrics.jsonl    # 검색 로그
└── chat_metrics.jsonl      # 챗봇 로그
```

### 파일 형식
- **JSONL** (JSON Lines): 한 줄당 하나의 JSON 객체
- 추가 전용 (Append-only)
- 디스크 I/O 최소화

### 보관 주기 (권장)
- **개발**: 7일
- **운영**: 30일
- **아카이브**: 90일 (압축)

### 수동 정리
```bash
# 30일 이전 로그 삭제
find metrics/ -name "*.jsonl" -mtime +30 -delete

# 압축 아카이브
gzip metrics/*_metrics.jsonl
```

### 자동 정리 (Cron)
```bash
# 매일 오전 3시 실행
0 3 * * * find /path/to/faq-generator/metrics/ -name "*.jsonl" -mtime +30 -delete
```

---

## 🚨 알림 설정 (옵션)

### 1. 성능 저하 알림

**기준**:
- 동기화 시간 > 5초
- 검색 시간 > 1초
- 챗봇 응답 시간 > 10초

**구현 예시** (Python):
```python
import requests

def check_performance():
    response = requests.get("http://localhost:8002/api/v1/metrics/summary?hours=1")
    data = response.json()
    
    # 동기화 체크
    if data['sync']['avg_duration_ms'] > 5000:
        send_alert("동기화 성능 저하: {:.1f}초".format(
            data['sync']['avg_duration_ms'] / 1000
        ))
    
    # 챗봇 체크
    if data['chat']['avg_total_duration_ms'] > 10000:
        send_alert("챗봇 응답 느림: {:.1f}초".format(
            data['chat']['avg_total_duration_ms'] / 1000
        ))

def send_alert(message):
    # Slack, Email, SMS 등으로 알림
    print(f"[ALERT] {message}")
```

---

## 🔧 트러블슈팅

### Q1. 대시보드가 "API 서버에 연결할 수 없습니다" 에러

**원인**: FastAPI 서버가 실행되지 않음

**해결**:
```bash
# 서버 상태 확인
curl http://localhost:8002/health

# 서버 실행
uvicorn app.main:app --port 8002
```

### Q2. 메트릭 데이터가 표시되지 않음

**원인**: 아직 메트릭이 수집되지 않음

**해결**:
1. FAQ 동기화 실행
   ```bash
   curl -X POST http://localhost:8002/api/v1/faq/sync-vector-db
   ```

2. 챗봇 테스트
   ```bash
   curl -X POST http://localhost:8002/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "졸업 요건은?", "session_id": null}'
   ```

3. 대시보드 새로고침

### Q3. metrics 폴더가 생성되지 않음

**원인**: 쓰기 권한 문제

**해결**:
```bash
# 폴더 수동 생성
mkdir -p faq-generator/metrics

# 권한 부여
chmod 755 faq-generator/metrics
```

---

## 📊 성능 벤치마크

### 목표 지표 (운영 환경)

| 메트릭 | 목표 값 | 현재 값 (예시) | 상태 |
|--------|---------|---------------|------|
| 증분 동기화 시간 | < 1초 | 0.5초 | ✅ 양호 |
| 전체 동기화 시간 | < 60초 | 33초 | ✅ 양호 |
| 검색 응답 시간 | < 100ms | 45ms | ✅ 우수 |
| 챗봇 응답 시간 | < 5초 | 3.8초 | ✅ 양호 |
| 동기화 성공률 | > 99% | 100% | ✅ 완벽 |
| 챗봇 High 신뢰도 | > 70% | 75% | ✅ 양호 |

---

## 🎯 다음 단계

### Phase 1: 완료 ✅
- [x] 메트릭 수집 시스템
- [x] REST API
- [x] Streamlit 대시보드

### Phase 2: 고도화 (옵션)
- [ ] Prometheus/Grafana 통합
- [ ] 알림 시스템 (Slack/Email)
- [ ] 성능 트렌드 분석 (ML)
- [ ] 자동 최적화 제안

### Phase 3: 스케일링 (대규모 운영)
- [ ] InfluxDB/TimescaleDB로 전환
- [ ] 분산 모니터링
- [ ] 리얼타임 대시보드 (WebSocket)

---

## 📚 참고 자료

- **Plotly 차트**: https://plotly.com/python/
- **Streamlit**: https://docs.streamlit.io/
- **FastAPI**: https://fastapi.tiangolo.com/
- **성능 최적화**: [PERFORMANCE_OPTIMIZATION.md](./PERFORMANCE_OPTIMIZATION.md)

---

**작성일**: 2026-02-28  
**버전**: v1.2.0  
**작성자**: FAQ 생성기 시스템
