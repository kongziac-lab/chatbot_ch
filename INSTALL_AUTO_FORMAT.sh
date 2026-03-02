#!/bin/bash
# Google Sheets 자동 서식 변환 활성화 스크립트

echo "=========================================="
echo "📝 Google Sheets 자동 서식 변환 설치"
echo "=========================================="
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 현재 디렉토리 확인
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt를 찾을 수 없습니다.${NC}"
    echo "faq-generator 폴더에서 실행하세요."
    exit 1
fi

echo "📦 1단계: google-api-python-client 설치 중..."
echo ""

# 2. 패키지 설치
pip3 install google-api-python-client==2.160.0 --user

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 패키지 설치 완료!${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  설치 중 경고가 있었지만 계속 진행합니다.${NC}"
fi

echo ""
echo "🔍 2단계: 설치 확인 중..."
python3 -c "import googleapiclient; print('✅ googleapiclient 모듈 import 성공')" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 설치 확인 완료!${NC}"
else
    echo -e "${RED}❌ 모듈을 찾을 수 없습니다. 다시 시도해주세요.${NC}"
    exit 1
fi

echo ""
echo "🔄 3단계: 서버 재시작 중..."
echo ""

# 3. 기존 서버 종료
lsof -ti :8002 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   - 기존 서버 종료 완료"
    sleep 2
fi

# 4. 서버 시작
nohup python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8002 > /tmp/fastapi_auto_format.log 2>&1 &
sleep 4

# 5. 서버 확인
curl -s http://localhost:8002/health > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   - 서버 시작 완료!${NC}"
else
    echo -e "${RED}   - 서버 시작 실패. 로그를 확인하세요: tail -50 /tmp/fastapi_auto_format.log${NC}"
    exit 1
fi

echo ""
echo "🧪 4단계: 자동 서식 변환 테스트 중..."
echo ""

# 6. 로그에서 서식 관련 메시지 확인
sleep 2
grep -q "서식 정보 가져오기 실패" /tmp/fastapi_auto_format.log

if [ $? -eq 0 ]; then
    echo -e "${RED}❌ 자동 변환 실패: googleapiclient 모듈을 찾을 수 없습니다.${NC}"
    echo ""
    echo "다음 명령어로 직접 설치해보세요:"
    echo "  pip3 install --user google-api-python-client==2.160.0"
    exit 1
else
    echo -e "${GREEN}✅ 자동 서식 변환 활성화 완료!${NC}"
fi

echo ""
echo "=========================================="
echo "🎉 설치 완료!"
echo "=========================================="
echo ""
echo "📋 다음 단계:"
echo ""
echo "1. Google Sheets에서 FAQ 작성"
echo "   - 볼드: Ctrl+B (Mac: Cmd+B)"
echo "   - 링크: Ctrl+K (Mac: Cmd+K)"
echo ""
echo "2. 브라우저에서 확인"
echo "   - 개발: http://localhost:5174"
echo "   - 프로덕션: http://localhost:8002"
echo ""
echo "3. 로그 확인 (문제 발생 시)"
echo "   - tail -50 /tmp/fastapi_auto_format.log"
echo ""
echo "📚 자세한 사용법: FORMATTING_GUIDE.md 참고"
echo ""
