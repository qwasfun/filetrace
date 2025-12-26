from typing import List, Optional
from urllib.parse import quote
from fastapi import APIRouter, UploadFile, Depends, HTTPException, File as FastAPIFile, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from app.database import get_async_session
from app.models import File, Folder
from app.services.security import get_current_user
from app.schemas import FileResponseModel, FileMove, FileRename, BatchFileMove, BatchFileOperation
from fastapi.responses import FileResponse, RedirectResponse
from app.models import User
from datetime import datetime
from app.services.storage import save_file, delete_file, file_exists, get_storage, get_public_url
from app.services.storage_backend import S3StorageBackend
import os

router = APIRouter(prefix="/api/v1/files", tags=["Files"])

UPLOAD_DIR = "data/uploads"


async def get_or_create_folder_by_path(
    db: AsyncSession,
    user_id: str,
    parent_folder_id: Optional[str],
    folder_path: str
) -> Optional[str]:
    """
    根据路径创建或获取文件夹，返回最终文件夹的ID
    folder_path: 相对路径，如 "folder1/folder2"
    """
    if not folder_path:
        return parent_folder_id
    
    # 分割路径
    path_parts = folder_path.split('/')
    current_parent_id = parent_folder_id
    
    for folder_name in path_parts:
        if not folder_name:
            continue
            
        # 查找是否已存在该文件夹
        stmt = select(Folder).where(
            Folder.user_id == user_id,
            Folder.name == folder_name,
            Folder.is_deleted == 0
        )
        
        if current_parent_id is not None:
            stmt = stmt.where(Folder.parent_id == current_parent_id)
        else:
            stmt = stmt.where(Folder.parent_id.is_(None))
        
        result = await db.execute(stmt)
        folder = result.scalar_one_or_none()
        
        if not folder:
            # 创建新文件夹
            folder = Folder(
                user_id=user_id,
                parent_id=current_parent_id,
                name=folder_name,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(folder)
            await db.flush()  # 立即获取ID
        
        current_parent_id = folder.id
    
    return current_parent_id


@router.post("/", response_model=List[FileResponseModel])
async def upload_files(
        folder_id: Optional[str] = Query(None),
        files: List[UploadFile] = FastAPIFile(...),
        relative_paths: Optional[List[str]] = Form(None),
        original_created_at: Optional[List[datetime]] = Query(None),
        original_updated_at: Optional[List[datetime]] = Query(None),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    results = []
    for i, file in enumerate(files):
        # 获取相对路径
        relative_path = ""
        if relative_paths and i < len(relative_paths):
            relative_path = relative_paths[i]
        
        # 解析文件夹路径和文件名
        target_folder_id = folder_id
        actual_filename = file.filename  # 默认使用原始文件名
        
        if relative_path:
            # 从相对路径中提取目录部分和文件名
            dir_path = os.path.dirname(relative_path)
            actual_filename = os.path.basename(relative_path)  # 提取纯文件名
            
            if dir_path:
                # 创建或获取文件夹结构
                target_folder_id = await get_or_create_folder_by_path(
                    db, str(current_user.id), folder_id, dir_path
                )
        
        # 保存文件（传递 user_id 用于组织文件结构）
        storage_path, mime_type, size = save_file(file, str(current_user.id))

        # Determine timestamps
        created_at = datetime.utcnow()
        if original_created_at and i < len(original_created_at) and original_created_at[i]:
            created_at = original_created_at[i]
            # 如果 datetime 带有时区信息，转换为 UTC 并移除时区信息
            if created_at.tzinfo is not None:
                created_at = created_at.utctimetuple()
                created_at = datetime(*created_at[:6])

        updated_at = datetime.utcnow()
        if original_updated_at and i < len(original_updated_at) and original_updated_at[i]:
            updated_at = original_updated_at[i]
            # 如果 datetime 带有时区信息，转换为 UTC 并移除时区信息
            if updated_at.tzinfo is not None:
                updated_at = updated_at.utctimetuple()
                updated_at = datetime(*updated_at[:6])

        # Save to DB
        new_file = File(
            user_id=current_user.id,
            folder_id=target_folder_id,
            filename=actual_filename,  # 使用提取的纯文件名
            storage_path=storage_path,
            mime_type=mime_type,
            size=size,
            original_created_at=created_at,
            original_updated_at=updated_at,
        )
        db.add(new_file)
        results.append(new_file)

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


@router.put("/{file_id}/rename", response_model=FileResponseModel)
async def rename_file(
    file_id: str,
    file_rename: FileRename,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(File).where(File.id == file_id, File.user_id == current_user.id)
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.filename = file_rename.filename
    await db.commit()
    await db.refresh(file)
    return file


@router.get("/")
async def list_files(
        folder_id: Optional[str] = None,
        q: Optional[str] = None,
        file_type: Optional[str] = Query(None, description="文件类型过滤: image, video, audio, document, pdf"),
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数，默认10"),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    """获取当前用户的文件列表（分页）"""

    # 计算偏移量
    offset = (page - 1) * page_size

    stmt = select(File).where(File.user_id == current_user.id, File.is_deleted == 0)

    if folder_id:
        stmt = stmt.where(File.folder_id == folder_id)
    else:
        stmt = stmt.where(File.folder_id.is_(None))

    if q:
        stmt = stmt.where(File.filename.ilike(f"%{q}%"))

    if file_type:
        if file_type == 'image':
            stmt = stmt.where(File.mime_type.like("image/%"))
        elif file_type == 'video':
            stmt = stmt.where(File.mime_type.like("video/%"))
        elif file_type == 'audio':
            stmt = stmt.where(File.mime_type.like("audio/%"))
        elif file_type == 'pdf':
            stmt = stmt.where(File.mime_type == "application/pdf")
        elif file_type == 'document':
            stmt = stmt.where(or_(File.mime_type.like("%document%"), File.mime_type.like("%word%")))

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
                "download_url": f.download_url,
                "preview_url": f.preview_url,
                "notes_count": f.notes_count,
                "mime_type": f.mime_type,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
                "original_created_at":f.original_created_at,
                "original_updated_at":f.original_updated_at,
            }
            for f in files
        ]
    }


@router.get("/{file_id}", response_model=FileResponseModel)
async def get_file_metadata(file_id: str, db: AsyncSession = Depends(get_async_session),
                            current_user: User = Depends(get_current_user)):
    result = await db.execute(select(File).where((File.id == file_id) & (File.user_id == current_user.id)))
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

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
        # S3 存储：重定向到预签名 URL
        try:
            url = storage.get_public_url(storage_path, filename=file_record.filename, disposition='attachment')
            return RedirectResponse(url=url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取 S3 下载链接失败: {str(e)}")
    else:
        # 本地存储：使用 FileResponse
        # 对文件名进行URL编码以支持中文等非ASCII字符
        encoded_filename = quote(file_record.filename)

        return FileResponse(
            path=storage_path,
            filename=file_record.filename,
            media_type=file_record.mime_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )


@router.get("/preview/{file_id}/{filename}")
async def preview_file(
        file_id: str,
        filename: Optional[str] = None,
        session: AsyncSession = Depends(get_async_session),
):
    """预览文件"""

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
        # S3 存储：重定向到预签名 URL
        try:
            url = storage.get_public_url(storage_path, filename=file_record.filename, disposition='inline')
            return RedirectResponse(url=url)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取 S3 预览链接失败: {str(e)}")
    else:
        # 本地存储：使用 FileResponse
        # 对文件名进行URL编码以支持中文等非ASCII字符
        encoded_filename = quote(file_record.filename)

        return FileResponse(
            path=storage_path,
            filename=file_record.filename,
            media_type=file_record.mime_type,
            headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
        )


@router.delete("/{file_id}")
async def delete_file_soft(
    file_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(File).where(File.id == file_id, File.user_id == current_user.id)
    result = await db.execute(stmt)
    file = result.scalar_one_or_none()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.is_deleted = 1
    file.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "File moved to recycle bin"}


@router.post("/batch/move")
async def batch_move_files(
    batch_move: BatchFileMove,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    if batch_move.folder_id:
        folder_stmt = select(Folder).where(Folder.id == batch_move.folder_id, Folder.user_id == current_user.id)
        folder_res = await db.execute(folder_stmt)
        if not folder_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Target folder not found")

    stmt = select(File).where(File.id.in_(batch_move.file_ids), File.user_id == current_user.id)
    result = await db.execute(stmt)
    files = result.scalars().all()
    
    for file in files:
        file.folder_id = batch_move.folder_id
    
    await db.commit()
    return {"message": f"Moved {len(files)} files"}


@router.post("/batch/delete")
async def batch_delete_files(
    batch_op: BatchFileOperation,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(File).where(File.id.in_(batch_op.file_ids), File.user_id == current_user.id)
    result = await db.execute(stmt)
    files = result.scalars().all()
    
    for file in files:
        file.is_deleted = 1
        file.deleted_at = datetime.utcnow()
    
    await db.commit()
    return {"message": f"Moved {len(files)} files to recycle bin"}
