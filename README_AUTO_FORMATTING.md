# 🎨 Google Sheets 자동 서식 변환 시스템

## ✅ 설치 완료!

모든 시스템이 정상적으로 작동합니다!

```
✅ google-api-python-client 설치 완료
✅ Google Sheets API v4 연결 성공
✅ OAuth 인증 정상
✅ 서식 파싱 시스템 작동 중
✅ FastAPI 서버 실행 중 (포트 8002)
✅ Vite 개발 서버 실행 중 (포트 5174)
✅ 프론트엔드 렌더링 준비 완료
```

---

## 🚀 바로 사용하기

### 🎯 Google Sheets에서 서식 적용

#### 1. Google Sheets 열기
```
https://docs.google.com/spreadsheets/d/1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo/edit
```

#### 2. FAQ 선택
- 시트: `FAQ_Master`
- 예시 FAQ: "수강꾸러미 신청방법" 또는 "수강신청 방법"
- 열: `답변(한국어)` (E열)

#### 3. 서식 적용

**볼드체**:
1. 텍스트 선택 (예: "EDWARD 포털")
2. **Ctrl+B** (Mac: **Cmd+B**)
3. 텍스트가 **굵게** 표시됨

**링크**:
1. 텍스트 선택 (예: "EDWARD 포털")
2. **Ctrl+K** (Mac: **Cmd+K**)
3. URL 입력: `https://portal.kmu.ac.kr`
4. **적용** 클릭
5. 텍스트가 **파란색 링크**로 표시됨

#### 4. 저장 및 대기
- Google Sheets는 자동 저장됩니다
- **5분 대기** (캐시 TTL)
- 또는 아래 명령어로 캐시 즉시 갱신:

```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -c "from app.services.sheet_manager import faq_sheet_manager; faq_sheet_manager._invalidate_cache(); print('✅ 캐시 갱신')"
```

---

### 🌐 브라우저에서 확인

#### 개발 환경
```
http://localhost:5174
```

#### 프로덕션 환경
```
http://localhost:8002
```

**테스트 흐름**:
1. 언어 선택 (한국어)
2. "학사/수업" 선택
3. "수강신청" 선택
4. FAQ 클릭 (예: "수강꾸러미 신청방법")
5. **답변 확인**:
   - ✅ 볼드 텍스트가 **굵게** 표시
   - ✅ 링크를 **클릭** 가능
   - ✅ 링크가 **새 탭**에서 열림

---

## 📝 서식 작성 예시

### 예시 1: 기본 안내
```
**신청 사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)

**신청 기간**:
- 수강신청 2주 전 홈페이지 공지
- 확인 경로: 대학생활 > 학사안내 > [학사공지](https://www.kmu.ac.kr/notice)

**대상자**: 재학생, 휴학생(복학 예정자)

**문의**: 학사지원팀 ☎ 053-580-XXXX
```

### 예시 2: 단계별 안내
```
**1단계: 포털 접속**
[EDWARD 포털](https://portal.kmu.ac.kr)에 로그인

**2단계: 메뉴 선택**
상단 메뉴 > **수업** > 수강신청

**3단계: 신청**
희망 과목 검색 후 *장바구니에 담기*

__주의__: 정원 마감 전에 신청하세요!
```

### 예시 3: 링크 모음
```
**관련 사이트**

*학생 포털*:
- [EDWARD 포털](https://portal.kmu.ac.kr) - 수강신청, 성적조회
- [학교 홈페이지](https://www.kmu.ac.kr) - 공지사항
- [도서관](https://library.kmu.ac.kr) - 자료 검색

*외부 사이트*:
- [하이코리아](https://www.hikorea.go.kr) - 비자/체류
- [건강보험공단](https://www.nhis.or.kr) - 보험
```

---

## 🎨 지원되는 서식

| Google Sheets 작업 | 마크다운 | 브라우저 렌더링 |
|-------------------|----------|----------------|
| Ctrl+B (볼드) | `**텍스트**` | **텍스트** |
| Ctrl+I (이탤릭) | `*텍스트*` | *텍스트* |
| Ctrl+K (링크) | `[텍스트](URL)` | [텍스트](URL) |
| 직접 입력 (밑줄) | `__텍스트__` | <u>텍스트</u> |
| 직접 입력 (취소선) | `~~텍스트~~` | ~~텍스트~~ |

---

## 🧪 즉시 테스트 방법

### 빠른 테스트 (3분)

```bash
# 1. 통합 테스트 실행
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
./test_formatting_complete.sh

# 2. Google Sheets에서 서식 적용
#    (브라우저로 이동하여 직접 작업)

# 3. 캐시 갱신 (즉시 확인)
python3 -c "from app.services.sheet_manager import faq_sheet_manager; faq_sheet_manager._invalidate_cache(); print('✅ 캐시 갱신')"

# 4. 브라우저 접속
open http://localhost:5174  # Mac
```

---

## 📊 시스템 상태

### 현재 실행 중
| 서비스 | 포트 | URL | 상태 |
|--------|------|-----|------|
| FastAPI | 8002 | http://localhost:8002 | ✅ |
| Vite Dev | 5174 | http://localhost:5174 | ✅ |

### 구현 완료
| 기능 | 파일 | 상태 |
|------|------|------|
| 서식 파싱 | `app/utils/text_formatter.py` | ✅ |
| Google Sheets 통합 | `app/services/sheet_manager.py` | ✅ |
| 마크다운 변환 | `public/src/lib/api.ts` | ✅ |
| HTML 렌더링 | `public/src/components/ChatPage.tsx` | ✅ |

---

## 🔧 유용한 명령어

### 캐시 관리
```bash
# 캐시 즉시 갱신 (5분 대기 없이)
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -c "from app.services.sheet_manager import faq_sheet_manager; faq_sheet_manager._invalidate_cache(); print('✅')"
```

### 서버 관리
```bash
# 서버 재시작
lsof -ti :8002 | xargs kill -9
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002

# 로그 확인
tail -f /tmp/fastapi_ready.log
```

### 디버깅
```bash
# API 직접 테스트
curl -s "http://localhost:8002/api/v1/faqs?lang=ko" | python3 -m json.tool | head -80

# 서식 변환 테스트
python3 -c "
from app.utils.text_formatter import markdown_to_html
text = '**볼드** 텍스트와 [링크](https://kmu.ac.kr)'
html = markdown_to_html(text)
print(html)
"
```

---

## 📚 문서

- ✅ **TEST_FORMATTING.md** - 서식 테스트 가이드
- ✅ **FORMATTING_GUIDE.md** - 완전한 서식 가이드
- ✅ **INSTALL_AUTO_FORMAT.sh** - 자동 설치 스크립트
- ✅ **test_formatting_complete.sh** - 통합 테스트 스크립트

---

## 🎯 지금 바로 테스트!

**1. Google Sheets에서 서식 적용** (2분)
   ```
   1. 시트 열기
   2. FAQ 선택
   3. Ctrl+B (볼드), Ctrl+K (링크) 적용
   ```

**2. 브라우저에서 확인** (1분)
   ```
   http://localhost:5174 또는 http://localhost:8002
   ```

---

**상태**: ✅ 프로덕션 준비 완료  
**버전**: 1.6.0  
**설치 완료 시간**: 2026-03-01 00:49

🚀 **모든 시스템 준비 완료! 지금 바로 Google Sheets에서 테스트하세요!**
