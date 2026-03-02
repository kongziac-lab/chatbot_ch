# 📝 Google Sheets 서식 가이드

## 🎯 개요

Google Sheets의 **볼드체**와 **하이퍼링크**를 프론트엔드에서 표시하는 기능이 구현되었습니다!

## 📋 사용 방법

### 방법 1: 마크다운 직접 입력 (✅ 바로 사용 가능)

Google Sheets의 답변 열에 **마크다운 형식**으로 입력하세요:

#### 볼드체
```
**중요한 텍스트**
```
→ <strong>중요한 텍스트</strong>

#### 링크
```
[계명대학교](https://www.kmu.ac.kr)
```
→ <a href="https://www.kmu.ac.kr" target="_blank">계명대학교</a>

#### 이탤릭
```
*강조 텍스트*
```
→ <em>강조 텍스트</em>

#### 밑줄
```
__밑줄 텍스트__
```
→ <u>밑줄 텍스트</u>

#### 취소선
```
~~취소 텍스트~~
```
→ <del>취소 텍스트</del>

#### 복합 예시
```
**EDWARD 포털**에 접속하려면 [이 링크](https://portal.kmu.ac.kr)를 클릭하세요.
```

---

### 방법 2: 자동 서식 변환 (⚙️ 설정 필요)

Google Sheets에서 **일반적인 방법**으로 서식을 적용하면 자동으로 마크다운으로 변환됩니다.

#### 필요한 설정

**1. Python 패키지 설치**
```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
pip3 install google-api-python-client==2.160.0
```

**2. 서버 재시작**
```bash
# 기존 서버 종료
lsof -ti :8002 | xargs kill -9

# 서버 시작
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002
```

**3. 확인**
```bash
# 로그에서 "서식 정보 가져오기 실패" 메시지가 없으면 성공
tail -20 /tmp/fastapi_format_test.log | grep "서식"
```

#### Google Sheets에서 작업

1. **볼드체 적용**
   - 텍스트 선택 → Ctrl+B (Mac: Cmd+B)
   - 또는 툴바의 **B** 버튼 클릭

2. **링크 추가**
   - 텍스트 선택 → Ctrl+K (Mac: Cmd+K)
   - URL 입력 → 확인
   - 또는 `=HYPERLINK("URL", "텍스트")` 함수 사용

---

## 🎨 프론트엔드 렌더링 예시

### Before (일반 텍스트)
```
신청사이트: EDWARD 포털 (https://portal.kmu.ac.kr)
중요: 수강신청 기간 확인
```

### After (서식 적용)
**신청사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)  
**중요**: 수강신청 기간 확인

---

## 📊 현재 상태

### ✅ 완료된 기능
- [x] 마크다운 → HTML 변환 유틸리티 (`app/utils/text_formatter.py`)
- [x] Google Sheets 서식 파싱 로직 (`sheet_manager.py`)
- [x] 프론트엔드 HTML 렌더링 (`ChatPage.tsx`)
- [x] 링크 안전 처리 (`target="_blank" rel="noopener noreferrer"`)

### 🔧 지원되는 서식
| 서식 | 마크다운 | HTML |
|------|----------|------|
| **볼드** | `**텍스트**` | `<strong>텍스트</strong>` |
| *이탤릭* | `*텍스트*` | `<em>텍스트</em>` |
| <u>밑줄</u> | `__텍스트__` | `<u>텍스트</u>` |
| ~~취소선~~ | `~~텍스트~~` | `<del>텍스트</del>` |
| [링크](https://kmu.ac.kr) | `[텍스트](URL)` | `<a href="URL">텍스트</a>` |

---

## 🧪 테스트 방법

### 1. Google Sheets에서 테스트 FAQ 작성
```
질문: 포털 접속 방법
답변: **EDWARD 포털**에 접속하려면 [이 링크](https://portal.kmu.ac.kr)를 클릭하세요.
```

### 2. API 테스트
```bash
curl -s "http://localhost:8002/api/v1/faqs?lang=ko" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['items'][0]['answer'])
"
```

**기대 결과**:
```
**EDWARD 포털**에 접속하려면 [이 링크](https://portal.kmu.ac.kr)를 클릭하세요.
```

### 3. 브라우저 테스트
1. http://localhost:5174 또는 http://localhost:8002 접속
2. 카테고리 선택 → FAQ 선택
3. 답변에서 **볼드체**와 **링크** 확인

---

## 🔍 문제 해결

### "서식 정보 가져오기 실패" 로그
**원인**: `google-api-python-client` 패키지 미설치

**해결**:
```bash
pip3 install google-api-python-client==2.160.0
# 또는
cd faq-generator
pip3 install -r requirements.txt
```

### 링크가 작동하지 않음
**확인사항**:
1. URL이 `http://` 또는 `https://`로 시작하는지 확인
2. 마크다운 형식이 정확한지 확인: `[텍스트](URL)`
3. 괄호나 공백이 잘못 입력되지 않았는지 확인

### 볼드가 표시되지 않음
**확인사항**:
1. 마크다운 형식 확인: `**텍스트**` (별표 2개)
2. 별표 앞뒤에 공백이 없어야 함
3. 닫는 별표를 빠뜨리지 않았는지 확인

---

## 📚 예시 FAQ 템플릿

### 수강신청 FAQ
```markdown
**신청 사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)

**신청 기간**: 수강신청 2주 전 홈페이지 공지
- 확인 경로: 대학생활 > 학사안내 > 학사공지

**대상자**: 재학생, 휴학생(해당 학기 복학예정자)

**신청 가능 학점**: 본인의 이수허용 학점과 동일

**주의사항**:
1. 수강신청 기간 엄수
2. ~~잘못된 정보~~ → 정확한 정보 확인
3. *궁금한 사항*은 학사지원팀(☎ 053-580-XXXX)으로 문의
```

### 비자 FAQ
```markdown
**외국인 등록증 신청 안내**

[출입국관리사무소](https://www.hikorea.go.kr)에서 신청하세요.

**준비 서류**:
- 여권
- 증명사진 2매
- __재학증명서__
- 수수료 30,000원

**문의**: [국제교류처](https://international.kmu.ac.kr)
```

---

## 🎯 권장 사항

### 방법 1 (마크다운 직접 입력)을 추천하는 경우
- ✅ 빠른 구현이 필요한 경우
- ✅ 서식이 많지 않은 경우
- ✅ Google Sheets에서 복사/붙여넣기가 많은 경우

### 방법 2 (자동 변환)를 추천하는 경우
- ✅ 많은 FAQ에 서식이 필요한 경우
- ✅ 관리자가 마크다운에 익숙하지 않은 경우
- ✅ Google Sheets의 일반 편집 기능을 선호하는 경우

---

## 📞 지원

문제가 발생하거나 추가 기능이 필요한 경우:
1. 로그 확인: `tail -50 /tmp/fastapi_format_test.log`
2. API 테스트: `curl http://localhost:8002/api/v1/faqs?lang=ko`
3. 코드 확인: `app/utils/text_formatter.py`, `app/services/sheet_manager.py`

---

**마지막 업데이트**: 2026-03-01  
**버전**: 1.6.0  
**상태**: ✅ 마크다운 방식 사용 가능, ⚙️ 자동 변환 설정 필요
