# ⚠️ OAuth 오류 해결: redirect_uri_mismatch

## 문제 원인

OAuth 클라이언트 ID 타입이 **"웹 애플리케이션"**으로 생성되어 있습니다.
로컬 데스크톱 애플리케이션에서는 **"데스크톱 앱"** 타입이 필요합니다.

---

## ✅ 해결 방법

### 1단계: Google Cloud Console 접속

https://console.cloud.google.com/apis/credentials

### 2단계: 올바른 OAuth 클라이언트 ID 생성

#### ⚠️ 중요: 타입을 정확히 선택하세요!

1. **상단 "+ 사용자 인증 정보 만들기"** 클릭
2. **"OAuth 클라이언트 ID"** 선택
3. **애플리케이션 유형 선택:**
   
   ❌ **웹 애플리케이션** (X)
   ✅ **데스크톱 앱** (O)  ← 이것을 선택하세요!

4. 이름: `FAQ 생성기 Desktop`
5. **"만들기"** 클릭
6. **JSON 다운로드** 버튼 클릭

### 3단계: 새 파일로 교체

터미널에서 실행:

```bash
cd /Users/kdh/Documents/GitHub/faq생성기/faq-generator

# 자동 교체 스크립트 실행
./OAUTH_FIX.sh
```

스크립트가 자동으로:
- 최근 다운로드한 client_secret 파일 찾기
- 타입 검증 (데스크톱 앱인지 확인)
- 기존 파일 백업
- 새 파일로 교체
- 검증

### 4단계: OAuth 인증 재시도

```bash
python3 oauth_setup.py
```

---

## 📸 스크린샷 가이드

### ✅ 올바른 설정

```
애플리케이션 유형
○ 웹 애플리케이션
○ Android
○ Chrome 앱
○ iOS
● 데스크톱 앱          ← 이것을 선택!
○ 유니버설 Windows 플랫폼(UWP)
○ TV 및 입력이 제한된 기기
```

### ❌ 잘못된 설정

```
애플리케이션 유형
● 웹 애플리케이션      ← 이것은 오류 발생!
○ Android
○ Chrome 앱
...
```

---

## 🔍 타입 확인 방법

다운로드한 JSON 파일을 열어서 확인:

### ✅ 올바른 파일 (데스크톱 앱)

```json
{
  "installed": {
    "client_id": "...",
    "client_secret": "...",
    ...
  }
}
```

### ❌ 잘못된 파일 (웹 애플리케이션)

```json
{
  "web": {
    "client_id": "...",
    "client_secret": "...",
    "redirect_uris": ["..."],
    ...
  }
}
```

---

## ❓ 자주 묻는 질문

### Q: 왜 "웹 애플리케이션"은 안 되나요?

**A**: 웹 애플리케이션은 특정 URL로 리디렉션이 필요합니다.
로컬 데스크톱 앱은 `http://localhost`로 리디렉션하므로 타입이 달라야 합니다.

### Q: 기존 "웹" 클라이언트를 수정할 수 있나요?

**A**: 아니요. OAuth 클라이언트 타입은 생성 후 변경할 수 없습니다.
새로 만들어야 합니다.

### Q: 여러 개의 OAuth 클라이언트 ID를 만들어도 되나요?

**A**: 네, 문제없습니다. 용도별로 여러 개 만들 수 있습니다.

---

## ✅ 체크리스트

- [ ] Google Cloud Console 접속
- [ ] OAuth 동의 화면 구성 완료 (최초 1회)
- [ ] **"데스크톱 앱"** 타입으로 OAuth 클라이언트 ID 생성
- [ ] JSON 파일 다운로드
- [ ] `./OAUTH_FIX.sh` 실행하여 파일 교체
- [ ] `python3 oauth_setup.py` 실행
- [ ] 브라우저에서 Google 로그인 및 권한 승인
- [ ] `secrets/token.json` 파일 생성 확인

---

## 🆘 여전히 문제가 있나요?

다음 정보를 확인하세요:

```bash
# 현재 OAuth 클라이언트 타입 확인
python3 -c "
import json
data = json.load(open('./secrets/oauth_client_secret.json'))
client_type = 'installed' if 'installed' in data else 'web'
print(f'현재 타입: {client_type}')
print(f'필요 타입: installed')
print(f'상태: {'✅ 정상' if client_type == 'installed' else '❌ 오류'}')
"
```

문제가 계속되면:
1. `secrets/oauth_client_secret.json` 파일을 다시 확인
2. Google Cloud Console에서 "데스크톱 앱" 타입으로 다시 생성
3. `./OAUTH_FIX.sh` 스크립트로 파일 교체

---

**준비되었으면 다음 단계로 진행하세요!** 🚀
