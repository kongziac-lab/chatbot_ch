#!/bin/bash
# Vite 프론트엔드 + FastAPI 백엔드 통합 테스트 스크립트

set -e

echo "=========================================="
echo "📋 FAQ 시스템 통합 테스트"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_api() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "테스트: $name... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $status_code, expected $expected_status)"
        ((FAILED++))
        return 1
    fi
}

# 1. FastAPI 헬스 체크
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  FastAPI 백엔드 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_api "헬스 체크" "http://localhost:8002/health"
test_api "API 문서" "http://localhost:8002/docs"
test_api "메트릭 요약" "http://localhost:8002/api/v1/metrics/summary"
echo ""

# 2. 챗봇 API 테스트
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  챗봇 API 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "테스트: 챗봇 메시지 전송... "

response=$(curl -s -X POST http://localhost:8002/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "테스트"}' \
  -w "\n%{http_code}")

status_code=$(echo "$response" | tail -1)
body=$(echo "$response" | sed '$d')

if [ "$status_code" -eq "200" ] && echo "$body" | grep -q "answer"; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  응답: $(echo "$body" | python3 -c "import sys, json; print(json.load(sys.stdin)['answer'][:50] + '...')" 2>/dev/null || echo "OK")"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $status_code)"
    ((FAILED++))
fi
echo ""

# 3. 정적 파일 제공 테스트
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  프론트엔드 정적 파일 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_api "루트 페이지 (index.html)" "http://localhost:8002/"
test_api "Vite 빌드 에셋" "http://localhost:8002/assets/" 404  # 404는 정상 (디렉토리 리스팅 없음)
echo ""

# 4. CORS 테스트
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  CORS 설정 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -n "테스트: CORS Preflight (OPTIONS)... "

cors_header=$(curl -s -X OPTIONS http://localhost:8002/api/v1/chat \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -i | grep -i "access-control-allow-origin")

if echo "$cors_header" | grep -q "*\|http://localhost:5173"; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  CORS 헤더: $cors_header"
    ((FAILED++))
fi
echo ""

# 5. Vite 개발 서버 테스트 (선택)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Vite 개발 서버 테스트 (선택)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    test_api "Vite 개발 서버" "http://localhost:5173"
else
    echo -e "${YELLOW}⊘ SKIP${NC} (Vite 개발 서버 실행 안 됨)"
fi
echo ""

# 결과 요약
echo "=========================================="
echo "📊 테스트 결과"
echo "=========================================="
echo -e "통과: ${GREEN}$PASSED${NC}"
echo -e "실패: ${RED}$FAILED${NC}"
echo "총 테스트: $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ 모든 테스트 통과!${NC}"
    echo ""
    echo "다음 단계:"
    echo "  1. 브라우저에서 http://localhost:8002 접속"
    echo "  2. 언어 선택 후 채팅 테스트"
    echo "  3. 성능 대시보드: streamlit run dashboard/performance.py"
    exit 0
else
    echo -e "${RED}✗ 일부 테스트 실패${NC}"
    echo ""
    echo "문제 해결:"
    echo "  1. FastAPI 서버 실행 확인: ps aux | grep uvicorn"
    echo "  2. 로그 확인: tail -f /tmp/fastapi.log"
    echo "  3. 포트 충돌: lsof -i :8002"
    exit 1
fi
