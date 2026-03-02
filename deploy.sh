#!/usr/bin/env bash
# deploy.sh — Docker Compose 기반 배포 스크립트
# 사용법: ./deploy.sh [build|up|down|logs|restart|status]
set -euo pipefail

COMPOSE="docker compose"
ENV_FILE=".env"
SECRETS_DIR="./secrets"
CREDS_FILE="${SECRETS_DIR}/google-credentials.json"

# ── 색상 출력 ────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 사전 검사 ────────────────────────────────────────────────────
check_prerequisites() {
  command -v docker  >/dev/null 2>&1 || error "Docker가 설치되어 있지 않습니다."
  docker compose version >/dev/null 2>&1 || error "Docker Compose v2가 필요합니다."

  [[ -f "$ENV_FILE" ]] || error ".env 파일이 없습니다. .env.example을 복사해 작성하세요."
  [[ -f "$CREDS_FILE" ]] || warn "Google 서비스 계정 키($CREDS_FILE)가 없습니다."

  # 필수 환경 변수 확인
  source "$ENV_FILE" 2>/dev/null || true
  [[ -n "${SPREADSHEET_ID:-}" ]]    || error "SPREADSHEET_ID가 설정되지 않았습니다."
  [[ -n "${ANTHROPIC_API_KEY:-}" ]] || error "ANTHROPIC_API_KEY가 설정되지 않았습니다."

  info "사전 검사 완료"
}

# ── 빌드 ─────────────────────────────────────────────────────────
cmd_build() {
  check_prerequisites
  info "이미지 빌드 시작 (BGE-M3 다운로드 포함, 시간이 걸릴 수 있습니다)…"
  $COMPOSE build --pull
  info "빌드 완료"
}

# ── 서비스 시작 ──────────────────────────────────────────────────
cmd_up() {
  check_prerequisites
  info "서비스 시작…"
  $COMPOSE up -d
  info "서비스 시작 완료"
  echo ""
  echo "  🌐 FAQ 페이지    : http://localhost:${FRONTEND_PORT:-3000}"
  echo "  📊 관리 대시보드  : http://localhost:${STREAMLIT_PORT:-8501}"
  echo "  🔧 API 서버      : http://localhost:${API_PORT:-8000}"
  echo "  📖 API 문서      : http://localhost:${API_PORT:-8000}/docs"
}

# ── 서비스 중지 ──────────────────────────────────────────────────
cmd_down() {
  info "서비스 중지…"
  $COMPOSE down
  info "서비스 중지 완료"
}

# ── 로그 ─────────────────────────────────────────────────────────
cmd_logs() {
  local service="${2:-}"
  if [[ -n "$service" ]]; then
    $COMPOSE logs -f "$service"
  else
    $COMPOSE logs -f
  fi
}

# ── 재시작 ───────────────────────────────────────────────────────
cmd_restart() {
  local service="${2:-}"
  if [[ -n "$service" ]]; then
    info "재시작: $service"
    $COMPOSE restart "$service"
  else
    info "전체 재시작"
    $COMPOSE restart
  fi
}

# ── 상태 확인 ────────────────────────────────────────────────────
cmd_status() {
  $COMPOSE ps
}

# ── 메인 ─────────────────────────────────────────────────────────
CMD="${1:-help}"
case "$CMD" in
  build)   cmd_build   ;;
  up)      cmd_up      ;;
  down)    cmd_down    ;;
  logs)    cmd_logs    "$@" ;;
  restart) cmd_restart "$@" ;;
  status)  cmd_status  ;;
  *)
    echo "사용법: $0 {build|up|down|logs [service]|restart [service]|status}"
    echo ""
    echo "  build    이미지 빌드 (BGE-M3 모델 포함)"
    echo "  up       모든 서비스 시작"
    echo "  down     모든 서비스 중지"
    echo "  logs     로그 출력 (로그 [서비스명])"
    echo "  restart  서비스 재시작"
    echo "  status   서비스 상태 확인"
    ;;
esac
