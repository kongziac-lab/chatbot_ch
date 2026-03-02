# 🚀 Google Sheets 자동 서식 변환 빠른 시작

## ⚡ 5분 안에 시작하기

### 1단계: 자동 설치 스크립트 실행 (2분)

```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
./INSTALL_AUTO_FORMAT.sh
```

**이 스크립트가 자동으로 수행하는 작업**:
- ✅ `google-api-python-client` 패키지 설치
- ✅ 설치 확인
- ✅ FastAPI 서버 재시작
- ✅ 자동 변환 기능 테스트

---

### 2단계: Google Sheets에서 FAQ 작성 (1분)

#### 볼드체 적용
1. 텍스트 선택
2. **Ctrl+B** (Mac: **Cmd+B**)

**예시**:
```
EDWARD 포털에서 수강신청을 진행하세요.
         ↓
**EDWARD 포털**에서 수강신청을 진행하세요.
```

#### 링크 추가
1. 텍스트 선택
2. **Ctrl+K** (Mac: **Cmd+K**)
3. URL 입력: `https://portal.kmu.ac.kr`
4. 확인 클릭

**결과**: `[EDWARD 포털](https://portal.kmu.ac.kr)`

---

### 3단계: 브라우저에서 확인 (1분)

```bash
# 브라우저 열기
# - 개발 환경: http://localhost:5174
# - 프로덕션: http://localhost:8002

# 1. 카테고리 선택
# 2. FAQ 선택
# 3. 볼드와 링크 확인
```

---

## 🔍 설치 확인

### 성공 메시지
```
✅ 패키지 설치 완료!
✅ googleapiclient 모듈 import 성공
✅ 서버 시작 완료!
✅ 자동 서식 변환 활성화 완료!
🎉 설치 완료!
```

### 실패 시 수동 설치
```bash
# 방법 1: 직접 설치
pip3 install --user google-api-python-client==2.160.0

# 방법 2: requirements.txt 사용
pip3 install --user -r requirements.txt

# 서버 재시작
lsof -ti :8002 | xargs kill -9
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

---

## 📊 동작 확인

### 로그 확인
```bash
# 서식 변환 로그 확인
tail -30 /tmp/fastapi_auto_format.log | grep "서식"

# ✅ 성공 예시:
# "Sheets 조회 완료: 99건 (게시중, 서식 포함)"

# ❌ 실패 예시:
# "서식 정보 가져오기 실패, 일반 텍스트 사용: No module named 'googleapiclient'"
```

### API 테스트
```bash
# FAQ 데이터 확인
curl -s "http://localhost:8002/api/v1/faqs?lang=ko" | python3 -c "
import sys, json
data = json.load(sys.stdin)
answer = data['items'][0]['answer']
print('첫 FAQ 답변:')
print(answer[:200])
print()
if '**' in answer or '[' in answer and '](' in answer:
    print('✅ 마크다운 서식 포함!')
else:
    print('ℹ️  일반 텍스트')
"
```

---

## 🎨 Google Sheets 작업 예시

### Before (일반 텍스트)
```
신청 사이트: EDWARD 포털 (https://portal.kmu.ac.kr)
대상자: 재학생
신청 기간: 2주 전 공지
```

### After (서식 적용)
1. "EDWARD 포털" 선택 → **Ctrl+B**
2. "EDWARD 포털" 선택 → **Ctrl+K** → URL 입력
3. "신청 기간" 선택 → **Ctrl+B**

**결과 (마크다운)**:
```
**신청 사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)
대상자: 재학생
**신청 기간**: 2주 전 공지
```

**렌더링 결과**:
- **신청 사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)
- 대상자: 재학생
- **신청 기간**: 2주 전 공지

---

## 🛠️ 문제 해결

### Q1: "No module named 'googleapiclient'" 오류
**해결**:
```bash
pip3 install --user google-api-python-client==2.160.0
# 또는
pip3 install --user google-api-core google-api-python-client
```

### Q2: 링크가 작동하지 않음
**확인사항**:
- ✅ Google Sheets에서 링크가 파란색으로 표시되는지 확인
- ✅ URL이 `http://` 또는 `https://`로 시작하는지 확인
- ✅ 캐시 지우기: 서버 재시작 후 5분 대기

### Q3: 볼드가 표시되지 않음
**확인사항**:
- ✅ Google Sheets에서 텍스트가 굵게 표시되는지 확인
- ✅ 브라우저 개발자 도구 → Elements에서 `<strong>` 태그 확인
- ✅ 캐시 지우기: Ctrl+Shift+R (Mac: Cmd+Shift+R)

### Q4: 서버 시작 실패
**해결**:
```bash
# 로그 확인
tail -50 /tmp/fastapi_auto_format.log

# 포트 충돌 확인
lsof -i :8002

# 포트 강제 종료
lsof -ti :8002 | xargs kill -9

# 서버 재시작
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

---

## 📋 체크리스트

### 설치 확인
- [ ] `./INSTALL_AUTO_FORMAT.sh` 실행
- [ ] "✅ 설치 완료!" 메시지 확인
- [ ] 서버 실행 확인: `curl http://localhost:8002/health`

### Google Sheets 작업
- [ ] FAQ 시트 열기
- [ ] 답변 열에서 텍스트 볼드 적용
- [ ] 답변 열에서 링크 추가
- [ ] 저장

### 브라우저 확인
- [ ] http://localhost:5174 또는 http://localhost:8002 접속
- [ ] 카테고리 → FAQ 선택
- [ ] 볼드 텍스트 표시 확인
- [ ] 링크 클릭 가능 확인
- [ ] 링크가 새 탭에서 열리는지 확인

---

## 🎯 추가 기능

### 지원되는 서식
| Google Sheets | 마크다운 | 단축키 |
|---------------|----------|--------|
| **볼드** | `**텍스트**` | Ctrl+B |
| *이탤릭* | `*텍스트*` | Ctrl+I |
| [링크](URL) | `[텍스트](URL)` | Ctrl+K |

### 고급 기능
```markdown
**중요 공지**: [학사공지](https://www.kmu.ac.kr/notice)를 확인하세요.

*주의사항*:
1. **기한 엄수**
2. 서류 준비
3. *문의*: 학사지원팀
```

---

## 📞 지원

### 로그 위치
- FastAPI: `/tmp/fastapi_auto_format.log`
- Vite: 터미널 출력

### 명령어 모음
```bash
# 서버 상태 확인
curl http://localhost:8002/health

# 서버 재시작
./INSTALL_AUTO_FORMAT.sh

# 로그 실시간 보기
tail -f /tmp/fastapi_auto_format.log

# FAQ 데이터 확인
curl -s "http://localhost:8002/api/v1/faqs?lang=ko" | python3 -m json.tool | head -50
```

---

**설치 시간**: 2-5분  
**난이도**: ⭐ (매우 쉬움)  
**자동화**: ✅ 스크립트 제공  
**상태**: 🚀 프로덕션 준비 완료

---

**관련 문서**:
- [FORMATTING_GUIDE.md](./FORMATTING_GUIDE.md) - 완전한 가이드
- [CHANGELOG.md](./CHANGELOG.md) - 변경 이력
