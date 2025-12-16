from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, UploadFile, Depends, HTTPException, File as FastAPIFile, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.database import get_async_session
from app.models import File, Folder
from app.services.security import get_current_user
from app.schemas import FileResponseModel, FileMove
from fastapi.responses import FileResponse
from app.models import User
from datetime import datetime
from app.services.storage import save_file, delete_file, file_exists, get_storage, get_public_url
from app.services.storage_backend import S3StorageBackend

router = APIRouter(prefix="/api/v1/files", tags=["Files"])

UPLOAD_DIR = "data/uploads"


@router.post("/", response_model=List[FileResponseModel])
async def upload_files(
        folder_id: Optional[str] = Query(None),
        files: List[UploadFile] = FastAPIFile(...),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    results = []
    for file in files:
        # 保存文件（传递 user_id 用于组织文件结构）
        storage_path, mime_type, size = save_file(file, str(current_user.id))

        # Save to DB
        new_file = File(
            user_id=current_user.id,
            folder_id=folder_id,
            filename=file.filename,
            storage_path=storage_path,
            mime_type=mime_type,
            size=size,
            created_at=datetime.now()
        )
        db.add(new_file)
        results.append(new_file)
        # Flush to get ID if needed immediately, but we commit at the end of loop or batched?
        # Actually commit each for safety in MVP or gathered. Let's add to session.

    await db.commit()
    for result in results:
        await db.refresh(result)
    return results


@router.put("/{file_id}/move", response_model=FileResponseModel)
async def move_file(
    file_id: str,
    file_move: FileMove,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(File).where(File.id == file_id, File.user_id == current_user.id)
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file_move.folder_id:
        folder_stmt = select(Folder).where(Folder.id == file_move.folder_id, Folder.user_id == current_user.id)
        folder_res = await db.execute(folder_stmt)
        if not folder_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Target folder not found")

    file.folder_id = file_move.folder_id
    await db.commit()
    await db.refresh(file)
    return file


@router.get("/")
async def list_files(
        folder_id: Optional[str] = None,
        q: Optional[str] = None,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数，默认10"),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    """获取当前用户的文件列表（分页）"""

    # 计算偏移量
    offset = (page - 1) * page_size

    stmt = select(File).where(File.user_id == current_user.id)

    if folder_id:
        stmt = stmt.where(File.folder_id == folder_id)
    else:
        stmt = stmt.where(File.folder_id.is_(None))

    if q:
        stmt = stmt.where(File.filename.ilike(f"%{q}%"))

    query = stmt.offset(offset).limit(page_size).order_by(
        File.created_at.desc()
    )

    # 获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 获取分页数据

    result = await db.execute(query)
    files = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": [
            {
                "id": f.id,
                "filename": f.filename,
                "size": f.size,
                "storage_path": f.storage_path,
                "download_url": get_public_url(f.storage_path) or f"/api/v1/files/download/{f.id}/{f.filename}",
                "mime_type": f.mime_type,
                "created_at": f.created_at
            }
            for f in files
        ]
    }


@router.get("/{file_id}", response_model=FileResponseModel)
async def get_file_metadata(file_id: str, db: AsyncSession = Depends(get_async_session),
                            current_user: User = Depends(get_current_user)):
    result = await db.execute(select(File).where((File.id == file_id) & (File.user_id == current_user.id)))
    file = result.scalar_one_or_none()
    file.download_url = f"/api/v1/files/download/{file.id}/{file.filename}",
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/{file_id}")
async def delete(file_id: str, db: AsyncSession = Depends(get_async_session),
                      current_user: User = Depends(get_current_user)):
    result = await db.execute(select(File).where((File.id == file_id) & (File.user_id == current_user.id)))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from storage backend
    delete_file(file.storage_path)

    # Delete from DB
    await db.delete(file)
    await db.commit()
    return {"message": "File deleted"}


@router.get("/download/{file_id}/{filename}")
async def download_file(
        file_id: str,
        filename: Optional[str] = None,
        session: AsyncSession = Depends(get_async_session),
):
    """下载文件"""

    # 查询文件
    stmt = select(File).where(
        (File.id == file_id)
    )
    result = await session.execute(stmt)
    file_record = result.scalar_one_or_none()

    if not file_record:
        raise HTTPException(status_code=404, detail="文件不存在或无权限访问")

    # 检查文件是否存在
    storage_path = file_record.storage_path
    if not file_exists(storage_path):
        raise HTTPException(status_code=404, detail="文件在存储中不存在")

    # 获取存储后端实例
    storage = get_storage()
    
    # 检查是否为 S3 存储
    if isinstance(storage, S3StorageBackend):
        # S3 存储：返回文件内容
        try:
            file_content = storage.get_object(storage_path)
            
            # 对文件名进行URL编码以支持中文等非ASCII字符
            encoded_filename = quote(file_record.filename)
            
            # 如果是PDF文件，使用inline方式在浏览器中显示
            if file_record.mime_type == "application/pdf":
                from fastapi.responses import Response
                return Response(
                    content=file_content,
                    media_type=file_record.mime_type,
                    headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
                )
            
            # 其他文件类型
            from fastapi.responses import Response
            return Response(
                content=file_content,
                media_type=file_record.mime_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"从 S3 获取文件失败: {str(e)}")
    else:
        # 本地存储：使用 FileResponse
        # 如果是PDF文件,使用inline方式在浏览器中显示
        if file_record.mime_type == "application/pdf":
            # 对文件名进行URL编码以支持中文等非ASCII字符
            encoded_filename = quote(file_record.filename)
            return FileResponse(
                path=storage_path,
                filename=file_record.filename,
                media_type=file_record.mime_type,
                headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
            )
        
        return FileResponse(
            path=storage_path,
            filename=file_record.filename,
            media_type=file_record.mime_type
        )
