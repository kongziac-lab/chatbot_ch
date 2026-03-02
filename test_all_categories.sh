#!/bin/bash

echo "=========================================="
echo "🧪 전체 FAQ 카테고리 테스트"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8002/api/v1/faqs"

test_category() {
    local major=$1
    local minor=$2
    local expected=$3
    
    local url="${BASE_URL}?category_major=$(echo -n "$major" | python3 -c "import sys; from urllib.parse import quote; print(quote(sys.stdin.read()))")&category_minor=$(echo -n "$minor" | python3 -c "import sys; from urllib.parse import quote; print(quote(sys.stdin.read()))")&lang=ko"
    
    local count=$(curl -s "$url" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('total', 0))" 2>/dev/null)
    
    if [ "$count" = "$expected" ]; then
        echo -e "${GREEN}✅ $major > $minor: ${count}개 (예상: ${expected})${NC}"
    else
        echo -e "${YELLOW}⚠️  $major > $minor: ${count}개 (예상: ${expected}) - 불일치!${NC}"
    fi
}

echo -e "${BLUE}📚 학사/수업${NC}"
test_category "학사/수업" "수강신청" "12"
test_category "학사/수업" "성적관련" "4"
test_category "학사/수업" "학적변동" "3"
test_category "학사/수업" "학생등록" "3"
test_category "학사/수업" "장학금" "2"
test_category "학사/수업" "출결처리" "3"

echo ""
echo -e "${BLUE}🎓 입학/졸업${NC}"
test_category "입학/졸업" "입학전형" "7"
test_category "입학/졸업" "입학원서" "2"
test_category "입학/졸업" "졸업이수" "9"
test_category "입학/졸업" "도착보고" "1"

echo ""
echo -e "${BLUE}🛂 비자/체류${NC}"
test_category "비자/체류" "비자관련" "2"
test_category "비자/체류" "체류관련" "1"
test_category "비자/체류" "외국인등록증" "7"

echo ""
echo -e "${BLUE}🏠 생활/숙박${NC}"
test_category "생활/숙박" "기숙사" "16"
test_category "생활/숙박" "보험생활" "4"
test_category "생활/숙박" "아르바이트" "1"
test_category "생활/숙박" "질병건강" "6"
test_category "생활/숙박" "은행카드" "2"
test_category "생활/숙박" "운전면허증" "10"
test_category "생활/숙박" "휴대폰" "1"
test_category "생활/숙박" "도착보고" "1"
test_category "생활/숙박" "방학생활" "2"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ 전체 카테고리 테스트 완료!${NC}"
echo "=========================================="
