# 🧪 Google Sheets 서식 자동 변환 테스트 가이드

## ✅ 설치 완료!

자동 서식 변환 시스템이 성공적으로 설치되었습니다!

```
✅ google-api-python-client 설치 완료
✅ OAuth 인증 성공
✅ Google Sheets API v4 연결 성공
✅ FastAPI 서버 실행 중 (포트 8002)
✅ Vite 개발 서버 실행 중 (포트 5174)
```

---

## 🎨 Google Sheets에서 테스트하기

### 1단계: Google Sheets 열기

브라우저에서 FAQ 시트를 엽니다:
```
https://docs.google.com/spreadsheets/d/1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo/edit
```

---

### 2단계: FAQ 찾기

**테스트할 FAQ** (예시):
- 시트: `FAQ_Master`
- 질문: "수강꾸러미 신청방법" 또는 "수강신청 방법"

---

### 3단계: 볼드체 적용

**답변(한국어)** 열(E열)에서:

1. **중요한 텍스트** 선택 (예: "EDWARD 포털")
2. **Ctrl+B** (Mac: **Cmd+B**) 또는 툴바의 **B** 버튼 클릭
3. 텍스트가 **굵게** 표시됨

**예시**:
```
Before:
신청사이트: 학교 홈페이지 상단 EDWARD 포털(https://portal.kmu.ac.kr)

After (EDWARD 포털 볼드 적용):
신청사이트: 학교 홈페이지 상단 **EDWARD 포털**(https://portal.kmu.ac.kr)
```

---

### 4단계: 링크 추가

**답변(한국어)** 열(E열)에서:

1. **링크로 만들 텍스트** 선택 (예: "EDWARD 포털")
2. **Ctrl+K** (Mac: **Cmd+K**) 또는 툴바의 링크 버튼 클릭
3. URL 입력: `https://portal.kmu.ac.kr`
4. **적용** 클릭
5. 텍스트가 **파란색** 링크로 표시됨

**결과**:
```
신청사이트: 학교 홈페이지 상단 [EDWARD 포털](https://portal.kmu.ac.kr)
```

---

### 5단계: 저장 및 대기

1. Google Sheets 자동 저장 (몇 초 대기)
2. **5분 대기** (캐시 TTL)
   - 또는 캐시 즉시 갱신: API 호출

---

### 6단계: 브라우저에서 확인

#### 방법 A: Vite 개발 서버
```
http://localhost:5174
```

#### 방법 B: FastAPI (프로덕션 빌드)
```
http://localhost:8002
```

**테스트 흐름**:
1. 언어 선택 (한국어)
2. "학사/수업" 선택
3. "수강신청" 선택
4. "수강꾸러미 신청방법" FAQ 클릭
5. **답변 확인**:
   - "EDWARD 포털"이 **굵게** 표시되는지 확인
   - 링크를 **클릭**할 수 있는지 확인
   - 새 탭에서 열리는지 확인

---

## 🧪 빠른 테스트 (캐시 우회)

### API 직접 호출로 즉시 확인

```bash
# 캐시 무시하고 최신 데이터 가져오기
curl -X POST "http://localhost:8002/api/v1/sync-vector-db?full_sync=true"

# 또는 Python으로 직접 테스트
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator
python3 << 'EOF'
from app.services.sheet_manager import faq_sheet_manager
faq_sheet_manager._invalidate_cache()  # 캐시 지우기
faqs = faq_sheet_manager.get_published_faqs(category_minor="수강신청")
print(f"FAQ 개수: {len(faqs)}")
if faqs:
    print(f"첫 FAQ 답변: {faqs[0]['답변(한국어)'][:200]}")
EOF
```

---

## 📊 실제 예시

### Google Sheets 입력 (서식 적용)

**답변(한국어)** 셀:
```
**신청 사이트**: EDWARD 포털

**접속 방법**:
1. [학교 홈페이지](https://www.kmu.ac.kr) 접속
2. 상단의 **EDWARD 포털** 클릭
3. [포털 사이트](https://portal.kmu.ac.kr) 이동

**신청 기간**: 수강신청 2주 전 공지 확인
- 경로: 대학생활 > 학사안내 > 학사공지

**대상자**: 재학생, 휴학생(복학 예정자)

*문의*: 학사지원팀 ☎ 053-580-XXXX
```

### 브라우저 렌더링 결과

**신청 사이트**: EDWARD 포털

**접속 방법**:
1. [학교 홈페이지](https://www.kmu.ac.kr) 접속
2. 상단의 **EDWARD 포털** 클릭
3. [포털 사이트](https://portal.kmu.ac.kr) 이동

**신청 기간**: 수강신청 2주 전 공지 확인
- 경로: 대학생활 > 학사안내 > 학사공지

**대상자**: 재학생, 휴학생(복학 예정자)

*문의*: 학사지원팀 ☎ 053-580-XXXX

---

## 🔍 문제 해결

### Q1: 서식이 적용되지 않음
**원인**: 캐시 TTL (5분)

**해결**:
```bash
# 방법 1: 5분 대기
sleep 300

# 방법 2: 캐시 즉시 갱신 (개발 중)
python3 -c "
from app.services.sheet_manager import faq_sheet_manager
faq_sheet_manager._invalidate_cache()
print('✅ 캐시 삭제 완료')
"
```

### Q2: 로그에 "서식 정보 가져오기 실패"
**원인**: 이미 수정되었습니다!

**확인**:
```bash
tail -30 /tmp/fastapi_ready.log | grep "서식"
# "서식 정보 가져오기 실패" 메시지가 없어야 정상
```

### Q3: 링크 클릭이 안 됨
**확인사항**:
- URL이 `http://` 또는 `https://`로 시작하는지
- 브라우저 콘솔에서 JavaScript 오류 확인
- 개발자 도구 → Elements에서 `<a>` 태그 확인

---

## 📝 권장 FAQ 작성 방법

### 템플릿 1: 신청 안내
```
**신청 사이트**: [EDWARD 포털](https://portal.kmu.ac.kr)

**신청 기간**:
- 수강신청 2주 전 홈페이지 공지
- 확인: [학사공지](https://www.kmu.ac.kr/notice)

**대상자**: 재학생, 휴학생(복학 예정자)

**문의**: 학사지원팀 ☎ 053-580-XXXX
```

### 템플릿 2: 서류 안내
```
**제출 서류**

__필수 서류__:
1. 여권 원본 및 사본
2. **재학증명서** ([발급 사이트](https://portal.kmu.ac.kr))
3. 증명사진 2매

__선택 서류__:
- 거주관계증명서
- 임대차계약서

**제출처**: 국제교류처 (본관 3층)
```

### 템플릿 3: 링크 모음
```
**관련 사이트**

*학생 포털*:
- [EDWARD 포털](https://portal.kmu.ac.kr) - 수강신청, 성적조회
- [학교 홈페이지](https://www.kmu.ac.kr) - 공지사항

*외부 사이트*:
- [하이코리아](https://www.hikorea.go.kr) - 비자/체류
- [건강보험공단](https://www.nhis.or.kr) - 보험가입
```

---

## 🎯 다음 단계

### 즉시 테스트
1. **Google Sheets 열기**
2. **답변 열에서 텍스트 선택**
3. **Ctrl+B** (볼드) 또는 **Ctrl+K** (링크) 적용
4. **5분 대기** 또는 캐시 삭제
5. **브라우저에서 확인**: http://localhost:5174

### 실전 적용
1. 중요한 FAQ부터 서식 적용
2. 자주 참조하는 링크 추가
3. 카테고리별로 일관된 스타일 사용

---

## 📊 현재 상태

| 항목 | 상태 |
|------|------|
| google-api-python-client | ✅ 설치 완료 |
| OAuth 인증 | ✅ 정상 |
| Google Sheets API v4 | ✅ 연결 성공 |
| 서식 파싱 시스템 | ✅ 작동 중 |
| FastAPI 서버 | ✅ 실행 중 (8002) |
| Vite 개발 서버 | ✅ 실행 중 (5174) |
| 프론트엔드 렌더링 | ✅ 준비 완료 |

---

## 🚀 지금 바로 테스트!

```bash
# 1. Google Sheets에서 FAQ 선택
# 2. 텍스트에 볼드/링크 적용
# 3. 브라우저 접속
open http://localhost:5174  # Mac
# 또는
start http://localhost:5174  # Windows
# 또는
xdg-open http://localhost:5174  # Linux

# 4. FAQ 확인
```

---

**모든 시스템 준비 완료!** 🎉  
이제 Google Sheets에서 서식을 적용하고 브라우저에서 확인하세요!
