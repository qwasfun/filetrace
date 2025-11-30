from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI()


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
