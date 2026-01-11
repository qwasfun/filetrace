import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import run_migrations
from app.routers import (
    auth,
    files,
    folders,
    notes,
    recycle,
    stats,
    storage_backends,
    users,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run migrations on startup
    await asyncio.to_thread(run_migrations)
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(notes.router)
app.include_router(folders.router)
app.include_router(recycle.router)
app.include_router(stats.router)
app.include_router(storage_backends.router)


# app.include_router(immich.router)


@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}


# 前端静态目录
dist_path = Path(__file__).parent / "static"

# 挂载静态资源目录（如果存在 assets 等静态文件）
assets_path = dist_path / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=assets_path), name="assets")


# 处理根路径的静态文件（favicon.ico 等）
@app.get("/favicon.ico")
async def favicon():
    favicon_path = dist_path / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    return {"error": "favicon not found"}


# SPA 路由 fallback - 捕获所有非 API 路由，返回 index.html（支持 Vue History 模式）
@app.get("/{full_path:path}")
async def spa(full_path: str):
    # 如果请求的是实际存在的静态文件，直接返回
    file_path = dist_path / full_path
    if file_path.is_file():
        return FileResponse(file_path)

    # 否则返回 index.html，让 Vue Router 处理
    index_path = dist_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"error": "index.html not found"}
