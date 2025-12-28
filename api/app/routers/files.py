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
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

router = APIRouter(prefix="/api/v1/files", tags=["Files"])

UPLOAD_DIR = "data/uploads"

# 创建线程池执行器用于处理同步IO操作（文件保存）
# max_workers 设置原则：
# - IO密集型任务：推荐 CPU核心数 × (2-5)
# - 本地存储：CPU核心数 × 2-3
# - 网络存储(S3)：CPU核心数 × 3-5
# - 可通过环境变量 FILE_UPLOAD_WORKERS 自定义
_cpu_count = os.cpu_count() or 4
_max_workers = int(os.getenv('FILE_UPLOAD_WORKERS', str(_cpu_count * 3)))
_file_io_executor = ThreadPoolExecutor(
    max_workers=_max_workers, 
    thread_name_prefix="file_io"
)


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
        original_created_at: Optional[List[datetime]] = Query(None),
        original_updated_at: Optional[List[datetime]] = Query(None),
        db: AsyncSession = Depends(get_async_session),
        current_user: User = Depends(get_current_user)
):
    """优化的文件上传：先处理文件IO，再批量插入数据库"""
    loop = asyncio.get_event_loop()
    
    # 第一阶段：并行处理文件夹结构和文件保存（IO密集）
    # 这部分不持有数据库连接，避免阻塞其他请求
    file_data_list = []
    folder_cache = {}  # 缓存已创建的文件夹ID
    
    # 先单独处理文件夹结构（需要数据库操作）
    for i, file in enumerate(files):
        relative_path = file.filename or ""
        dir_path = os.path.dirname(relative_path) if relative_path else ""
        
        if dir_path and dir_path not in folder_cache:
            target_folder_id = await get_or_create_folder_by_path(
                db, str(current_user.id), folder_id, dir_path
            )
            folder_cache[dir_path] = target_folder_id
    
    # 提交文件夹创建（快速释放连接）
    await db.commit()
    
    # 第二阶段：并行保存文件到存储（不持有数据库连接）
    async def save_file_async(file: UploadFile, index: int):
        """在线程池中异步保存文件"""
        relative_path = file.filename or ""
        actual_filename = os.path.basename(relative_path) if relative_path else file.filename
        dir_path = os.path.dirname(relative_path) if relative_path else ""
        
        target_folder_id = folder_cache.get(dir_path) if dir_path else folder_id
        
        # 在线程池中执行同步IO
        storage_path, size, file_type_info = await loop.run_in_executor(
            _file_io_executor,
            save_file,
            file,
            str(current_user.id)
        )
        
        # 处理时间戳
        created_at = datetime.utcnow()
        if original_created_at and index < len(original_created_at) and original_created_at[index]:
            created_at = original_created_at[index]
            if created_at.tzinfo is not None:
                created_at = created_at.utctimetuple()
                created_at = datetime(*created_at[:6])
        
        updated_at = datetime.utcnow()
        if original_updated_at and index < len(original_updated_at) and original_updated_at[index]:
            updated_at = original_updated_at[index]
            if updated_at.tzinfo is not None:
                updated_at = updated_at.utctimetuple()
                updated_at = datetime(*updated_at[:6])
        
        return {
            'user_id': str(current_user.id),
            'folder_id': target_folder_id,
            'filename': actual_filename,
            'storage_path': storage_path,
            'mime_type': file_type_info.get('mime_type'),
            'size': size,
            'file_type': file_type_info.get('category'),
            'file_type_confidence': file_type_info.get('confidence'),
            'original_created_at': created_at,
            'original_updated_at': updated_at,
        }
    
    # 并行保存所有文件
    file_data_list = await asyncio.gather(
        *[save_file_async(file, i) for i, file in enumerate(files)]
    )
    
    # 第三阶段：批量插入数据库（快速操作）
    # 使用bulk_insert_mappings进行高效批量插入
    if file_data_list:
        # 添加创建时间、更新时间和ID
        now = datetime.utcnow()
        for data in file_data_list:
            data['id'] = str(uuid.uuid4())
            data['created_at'] = now
            data['updated_at'] = now
            data['is_deleted'] = 0
        
        # 批量插入（非常快）
        # 使用 File.__mapper__ 来获取正确的 mapper 对象
        from sqlalchemy import inspect
        file_mapper = inspect(File)
        await db.run_sync(
            lambda session: session.bulk_insert_mappings(file_mapper, file_data_list)
        )
        await db.commit()
    
    # 查询返回插入的记录（可选优化：如果不需要立即返回完整对象，可以只返回基本信息）
    if file_data_list:
        # 获取刚插入的文件（通过storage_path匹配）
        storage_paths = [data['storage_path'] for data in file_data_list]
        stmt = select(File).where(
            File.storage_path.in_(storage_paths),
            File.user_id == current_user.id
        ).order_by(File.created_at.desc())
        result = await db.execute(stmt)
        results = result.scalars().all()
        return list(results)[:len(files)]  # 返回对应数量的结果
    
    return []


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
                "original_created_at": f.original_created_at,
                "original_updated_at": f.original_updated_at,
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
