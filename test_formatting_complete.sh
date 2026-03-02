#!/bin/bash
echo "=========================================="
echo "🧪 Google Sheets 서식 변환 통합 테스트"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 서버 상태
echo "1️⃣  서버 상태 확인"
curl -s http://localhost:8002/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ FastAPI 서버 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  FastAPI 서버 실행 필요${NC}"
fi

curl -s http://localhost:5174 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Vite 개발 서버 실행 중${NC}"
else
    echo -e "${YELLOW}⚠️  Vite 개발 서버 실행 필요${NC}"
fi
echo ""

# 2. 패키지 확인
echo "2️⃣  패키지 설치 확인"
python3 -c "import googleapiclient; print('✅ google-api-python-client 설치됨')" 2>/dev/null || echo "❌ 패키지 미설치"
echo ""

# 3. Google Sheets API 연결
echo "3️⃣  Google Sheets API 연결"
python3 -c "
from googleapiclient.discovery import build
from app.services.google_oauth import get_oauth_credentials
from app.config import settings

creds = get_oauth_credentials(
    client_secrets_path=settings.oauth_client_secrets_path,
    token_path=settings.oauth_token_path
)
service = build('sheets', 'v4', credentials=creds)
print('✅ Google Sheets API v4 연결 성공')
" 2>/dev/null || echo "❌ API 연결 실패"
echo ""

# 4. FAQ API 테스트
echo "4️⃣  FAQ API 응답 확인"
response=$(curl -s "http://localhost:8002/api/v1/faqs?category_minor=%EC%88%98%EA%B0%95%EC%8B%A0%EC%B2%AD&lang=ko")
count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null)

if [ ! -z "$count" ] && [ "$count" -gt 0 ]; then
    echo -e "${GREEN}✅ FAQ API 정상 (${count}개 FAQ)${NC}"
else
    echo "❌ FAQ API 오류"
fi
echo ""

# 5. 다음 단계 안내
echo "=========================================="
echo "🎯 다음 단계: Google Sheets에서 테스트"
echo "=========================================="
echo ""
echo "1. Google Sheets 열기"
echo "   https://docs.google.com/spreadsheets/d/1b8eFp_EmTkKhwqXos_2fedLZzz1zSai90o6Aqe3WZbo/edit"
echo ""
echo "2. FAQ 찾기 (예: '수강꾸러미 신청방법')"
echo ""
echo "3. 답변(한국어) 열에서 서식 적용"
echo "   - 볼드: Ctrl+B (Mac: Cmd+B)"
echo "   - 링크: Ctrl+K (Mac: Cmd+K)"
echo ""
echo "4. 저장 후 5분 대기 (캐시 TTL)"
echo ""
echo "5. 브라우저에서 확인"
echo "   - 개발: http://localhost:5174"
echo "   - 프로덕션: http://localhost:8002"
echo ""
echo "📚 자세한 가이드: TEST_FORMATTING.md"
echo ""
