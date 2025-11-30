################################
# 1. Build Vue Frontend
################################
FROM node:24-alpine AS frontend-builder
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

WORKDIR /app/web
COPY web/. ./
RUN corepack enable pnpm
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile  \
    && pnpm run build


################################
# 2. Build FastAPI Backend
################################
FROM python:3.13-slim

WORKDIR /app

# 拷贝后端
COPY api/ ./api

ENV PATH="/app/api/.venv/bin:$PATH"

# 安装后端依赖
RUN cd api && pip install uv && uv sync

# 拷贝前端静态文件到 FastAPI
COPY --from=frontend-builder /app/web/dist ./api/app/static

EXPOSE 8000

# Uvicorn 启动 FastAPI
CMD ["uvicorn", "api.app.app:app", "--host", "0.0.0.0", "--port", "8000"]
