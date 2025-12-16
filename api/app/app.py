from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database import create_db_and_tables

from contextlib import asynccontextmanager

from app.routers import users, auth, files, notes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(notes.router)


# app.include_router(immich.router)

@app.get("/api/hello")
async def hello():
    return {"message": "Hello World"}


# 前端静态目录
dist_path = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")


# SPA 路由 fallback，保证前端路由可用
@app.get("/{full_path:path}")
def spa(full_path: str):
    index = dist_path / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"error": "index.html not found"}
