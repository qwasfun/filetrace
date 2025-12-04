from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.app.services.storage import save_file
from api.app.database import get_async_session
from api.app.models import File as FileModel, User

from api.app.services.security import get_current_user

from datetime import datetime

router = APIRouter(prefix="/api/v1/files", tags=["Files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...),
                      session: AsyncSession = Depends(get_async_session),
                      current_user: User = Depends(get_current_user)
                      ):
    path, mimetype = save_file(file)
    db_file = FileModel(filename=file.filename, path=path, mimetype=mimetype, user_id=current_user.id)
    session.add(db_file)
    await session.commit()
    await  session.refresh(db_file)
    return {"id": db_file.id, "filename": db_file.filename, "path": db_file.path, "mimetype": db_file.mimetype}


@router.get("/")
async def get_files(
        session: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
        ):
    """获取当前用户的所有文件"""

    stmt = select(FileModel).where(FileModel.user_id == current_user.id)
    result = await session.execute(stmt)
    files = result.scalars().all()
    return files
