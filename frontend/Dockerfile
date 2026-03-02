# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: 의존성 설치
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: 빌드
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 빌드 타임 환경 변수 (런타임에는 NEXT_PUBLIC_API_BASE로 덮어쓸 수 있음)
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

RUN npm run build


# ─────────────────────────────────────────────────────────────────────────────
# Stage 3: 런타임 이미지 (standalone 출력 사용)
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# standalone 빌드 결과물만 복사 (최소 이미지)
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static    ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public           ./public

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
