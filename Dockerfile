# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: 의존성 설치 + BGE-M3 모델 사전 다운로드
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# 시스템 빌드 의존성 (C 확장, PDF 처리 등)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# requirements 먼저 복사 → 레이어 캐시 활용
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# BGE-M3 모델은 빌드 시 포함하지 않음
# → 볼륨(/app/models)에 첫 시작 시 1회 다운로드 후 캐시
ARG EMBEDDING_MODEL=BAAI/bge-m3


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: 런타임 이미지 (최소화)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# 런타임 전용 라이브러리
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# site-packages 복사 (builder 스테이지에서)
COPY --from=builder /usr/local/lib/python3.11/site-packages \
                    /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 모델은 영속 볼륨(/app/models)에서 로드
# 첫 시작 시 없으면 자동 다운로드, 이후 재사용
ENV SENTENCE_TRANSFORMERS_HOME=/app/models \
    HF_HOME=/app/models \
    # Python 버퍼링 해제 (로그 즉시 출력)
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 앱 소스 복사 (credentials 제외)
COPY app /app/app

# 비루트 사용자 실행 (보안)
RUN groupadd -r appuser && useradd -r -g appuser appuser \
 && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", \"8000\")}/health')"

# Zeabur 포함 PaaS 환경: PORT 환경 변수 사용 (미설정 시 8000)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --log-level info"]
