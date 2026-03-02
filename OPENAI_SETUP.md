# OpenAI API 설정 가이드

Anthropic Claude에서 OpenAI GPT로 전환되었습니다.

---

## ✅ 완료된 변경 사항

### 1. 수정된 파일

- ✅ `requirements.txt` - openai 패키지 추가
- ✅ `app/config.py` - OPENAI_API_KEY 설정 추가
- ✅ `app/services/chat_service.py` - OpenAI GPT로 변경
- ✅ `app/services/translator.py` - OpenAI GPT로 변경
- ✅ `app/services/faq_generator.py` - OpenAI GPT로 변경
- ✅ `.env` - OPENAI_API_KEY 환경 변수 추가
- ✅ `.env.example` - 예시 업데이트

### 2. 사용 모델

| 용도 | 모델 | 비용 (1M 토큰) |
|------|------|---------------|
| **챗봇 응답** | gpt-4o-mini | $0.15 (입력) / $0.60 (출력) |
| **FAQ 생성** | gpt-4o | $2.50 (입력) / $10.00 (출력) |
| **번역** | gpt-4o-mini | $0.15 (입력) / $0.60 (출력) |
| **질문 추출** | gpt-4o-mini | $0.15 (입력) / $0.60 (출력) |

---

## 🚀 설정 단계

### 1단계: OpenAI API 키 발급

1. **OpenAI 플랫폼 접속**:
   https://platform.openai.com

2. **로그인** (Google 계정 또는 이메일)

3. **API Keys 메뉴**:
   - 왼쪽 메뉴 → **"API keys"**
   - 또는 직접: https://platform.openai.com/api-keys

4. **새 키 생성**:
   - **"+ Create new secret key"** 클릭
   - 이름: `FAQ Generator`
   - **"Create secret key"** 클릭
   - **⚠️ 생성된 키를 즉시 복사** (다시 볼 수 없음!)
   
5. **크레딧 확인**:
   - 무료 tier: $5 크레딧 (3개월)
   - 유료 tier: 신용카드 등록 후 사용량 과금

---

### 2단계: .env 파일에 API 키 추가

`.env` 파일을 열고 다음 줄을 수정:

```bash
# .env 파일 편집
nano /Users/kdh/Documents/GitHub/faq생성기/faq-generator/.env
```

**수정할 부분**:

```dotenv
# ── OpenAI ────────────────────────────────────────────────────────
OPENAI_API_KEY=sk-proj-여기에-복사한-OpenAI-API-키-붙여넣기
```

---

### 3단계: OpenAI 패키지 설치

터미널에서 실행:

```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator

# 패키지 설치
pip3 install openai==1.54.0

# 또는 전체 재설치
pip3 install -r requirements.txt
```

---

### 4단계: 서버 재시작

```bash
# 기존 서버 종료 (Ctrl+C)

# 서버 재시작
uvicorn app.main:app --reload --port 8002
```

**성공 메시지**:
```
INFO: Application startup complete.
INFO: FAQ 생성기 API v1.0.0 시작
```

---

### 5단계: 챗봇 테스트

**브라우저에서**: http://localhost:8002/docs

**POST /api/v1/chat** 엔드포인트 테스트:

```json
{
  "message": "수강신청은 어떻게 하나요?",
  "session_id": null
}
```

---

## 💰 비용 비교

### Anthropic Claude vs OpenAI GPT

| 항목 | Claude 3.5 Sonnet | GPT-4o | GPT-4o-mini |
|------|------------------|--------|-------------|
| **입력 (1M 토큰)** | $3.00 | $2.50 | **$0.15** |
| **출력 (1M 토큰)** | $15.00 | $10.00 | **$0.60** |
| **품질** | 매우 높음 | 매우 높음 | 높음 |
| **속도** | 빠름 | 매우 빠름 | 매우 빠름 |

**💡 GPT-4o-mini가 가장 경제적입니다!** (Claude 대비 약 1/20 가격)

---

## 🔍 모델 변경 (필요시)

더 높은 품질이 필요하면 `.py` 파일에서 모델명 변경:

### chat_service.py (챗봇)
```python
# 현재 (가장 저렴)
model="gpt-4o-mini"

# 고품질 필요 시
model="gpt-4o"
```

### faq_generator.py (FAQ 생성)
```python
# 질문 추출 (현재)
model="gpt-4o-mini"  # 라인 533

# FAQ 생성 (현재)
model="gpt-4o"  # 라인 303 - 높은 품질 필요
```

---

## ✅ 설치 체크리스트

- [ ] OpenAI 계정 생성
- [ ] API 키 발급
- [ ] `.env` 파일에 `OPENAI_API_KEY` 추가
- [ ] `pip3 install openai==1.54.0` 실행
- [ ] 서버 재시작
- [ ] 챗봇 테스트 성공

---

## ❓ 문제 해결

### 문제 1: "Invalid API key"

**원인**: API 키가 잘못되었거나 비어있음

**해결**:
1. `.env` 파일에서 `OPENAI_API_KEY` 확인
2. OpenAI 플랫폼에서 키 재발급
3. 키 복사 후 `.env`에 붙여넣기

---

### 문제 2: "You exceeded your current quota"

**원인**: OpenAI 크레딧 부족

**해결**:
1. https://platform.openai.com/settings/organization/billing 접속
2. **"Add payment method"** 또는 **"Add to credit balance"**
3. 신용카드 등록 또는 크레딧 구매

---

### 문제 3: 서버 시작 오류

**원인**: openai 패키지 미설치

**해결**:
```bash
pip3 install openai==1.54.0
```

---

## 🎉 다음 단계

1. **OpenAI API 키 발급** (지금!)
2. **`.env` 파일 수정**
3. **패키지 설치**: `pip3 install openai`
4. **서버 재시작**
5. **챗봇 테스트**: http://localhost:8002/docs

---

**OpenAI는 더 저렴하고 빠릅니다!** 🚀
