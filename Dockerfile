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
COPY api/ ./

ENV PATH="/app/.venv/bin:$PATH"

# 拷贝数据目录（确保 sqlite 文件目录存在）  在容器中的数据保存目录为 /app/data
# 安装后端依赖
RUN mkdir -p data && pip install uv && uv sync

# 拷贝前端静态文件到 FastAPI
COPY --from=frontend-builder /app/web/dist ./app/static

EXPOSE 8000

# Uvicorn 启动 FastAPI
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
