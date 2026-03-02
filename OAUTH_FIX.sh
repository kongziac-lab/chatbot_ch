#!/bin/bash
# OAuth 클라이언트 ID 파일 교체 스크립트

echo "=================================================="
echo "OAuth 클라이언트 ID 파일 교체"
echo "=================================================="
echo ""

# 다운로드 폴더에서 가장 최근 client_secret 파일 찾기
LATEST_FILE=$(ls -t ~/Downloads/client_secret*.json 2>/dev/null | head -1)

if [ -z "$LATEST_FILE" ]; then
    echo "❌ 다운로드 폴더에 client_secret 파일이 없습니다."
    echo ""
    echo "Google Cloud Console에서 OAuth 클라이언트 ID를 다운로드하세요:"
    echo "1. https://console.cloud.google.com/apis/credentials"
    echo "2. OAuth 클라이언트 ID 생성 (타입: 데스크톱 앱)"
    echo "3. JSON 다운로드"
    echo ""
    exit 1
fi

echo "📥 최근 다운로드 파일: $(basename "$LATEST_FILE")"
echo ""

# 파일 타입 확인
CLIENT_TYPE=$(python3 -c "import json; data=json.load(open('$LATEST_FILE')); print('installed' if 'installed' in data else 'web')")

echo "🔍 클라이언트 타입: $CLIENT_TYPE"
echo ""

if [ "$CLIENT_TYPE" != "installed" ]; then
    echo "❌ 잘못된 클라이언트 타입입니다!"
    echo ""
    echo "이 파일은 '$([ "$CLIENT_TYPE" = "web" ] && echo "웹 애플리케이션" || echo "알 수 없음")' 타입입니다."
    echo ""
    echo "Google Cloud Console에서:"
    echo "1. OAuth 클라이언트 ID 생성 시"
    echo "2. 애플리케이션 유형을 '데스크톱 앱'으로 선택하세요"
    echo "   (웹 애플리케이션이 아닙니다!)"
    echo ""
    exit 1
fi

# 백업
if [ -f "./secrets/oauth_client_secret.json" ]; then
    cp ./secrets/oauth_client_secret.json ./secrets/oauth_client_secret.json.backup
    echo "💾 기존 파일 백업됨: oauth_client_secret.json.backup"
fi

# 새 파일 복사
cp "$LATEST_FILE" ./secrets/oauth_client_secret.json
echo "✅ 새 OAuth 클라이언트 파일 복사 완료"
echo ""

# 검증
echo "🧪 파일 검증 중..."
python3 -c "
from app.services.google_oauth import validate_oauth_setup
valid, msg = validate_oauth_setup('./secrets/oauth_client_secret.json')
print(f'   {msg}')
if not valid:
    exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ OAuth 클라이언트 ID 교체 완료!"
    echo "=================================================="
    echo ""
    echo "이제 다시 인증을 시도하세요:"
    echo "  python3 oauth_setup.py"
    echo ""
else
    echo ""
    echo "❌ 파일 검증 실패"
    exit 1
fi
