from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.schemas import NoteCreate, NoteResponse, NoteUpdate


class FileIdsRequest(BaseModel):
    file_ids: List[str]


class FolderIdsRequest(BaseModel):
    folder_ids: List[str]


from app.models import File, Folder, Note, User
from app.services.security import get_current_user

router = APIRouter(prefix="/api/v1/notes", tags=["Notes"])


@router.post("/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    new_note = Note(
        title=note.title,
        content=note.content,
        user_id=current_user.id,
        visibility=note.visibility,
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note


@router.get("/")
async def list_notes(
    q: Optional[str] = None,
    file_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页条数，默认10"),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的笔记列表（分页）"""

    # 计算偏移量
    offset = (page - 1) * page_size

    # 基础查询
    stmt = (
        select(Note)
        .where(Note.user_id == current_user.id)
        .options(selectinload(Note.files).selectinload(File.notes))
        .options(selectinload(Note.folders))
    )

    if file_id:
        stmt = stmt.join(Note.files).where(File.id == file_id)

    if folder_id:
        stmt = stmt.join(Note.folders).where(Folder.id == folder_id)

    if q:
        # 在标题或内容中搜索
        stmt = stmt.where((Note.title.ilike(f"%{q}%")) | (Note.content.ilike(f"%{q}%")))

    # 分页查询
    query = stmt.offset(offset).limit(page_size).order_by(Note.updated_at.desc())

    # 获取总数
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 获取分页数据
    result = await db.execute(query)
    notes = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "data": [
            {
                "id": note.id,
                "user_id": note.user_id,
                "title": note.title,
                "content": note.content,
                "visibility": note.visibility,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
                "files": [
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
                    }
                    for f in note.files
                ],
                "folders": [
                    {
                        "id": folder.id,
                        "name": folder.name,
                        "parent_id": folder.parent_id,
                        "created_at": folder.created_at,
                        "updated_at": folder.updated_at,
                    }
                    for folder in note.folders
                ],
            }
            for note in notes
        ],
    }


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(Note)
        .options(selectinload(Note.files).selectinload(File.notes))
        .options(selectinload(Note.folders))
        .where((Note.id == note_id) & (Note.user_id == current_user.id))
    )
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}")
async def update_note(
    note_id: str,
    note_update: NoteUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id))
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content

    await db.commit()
    await db.refresh(note)
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id))
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()
    return {"message": "Note deleted"}


@router.post("/{note_id}/attach")
async def attach_files(
    note_id: str,
    request: FileIdsRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    file_ids = request.file_ids
    # Fetch note
    query = (
        select(Note)
        .options(selectinload(Note.files))
        .where((Note.id == note_id) & (Note.user_id == current_user.id))
    )
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Fetch files
    files_result = await db.execute(select(File).where(File.id.in_(file_ids)))
    files_to_attach = files_result.scalars().all()

    # Append new files (avoiding duplicates if already attached is generic set logic,
    # but SQLAlchemy relationships might handle duplications or we should check)
    # A simple way involves using a set of IDs or letting sqlalchemy handle the merge if configured,
    # but explicit check is safer for basic List add.

    current_ids = {f.id for f in note.files}
    for f in files_to_attach:
        if f.id not in current_ids:
            note.files.append(f)

    await db.commit()
    return {"message": "Files attached", "file_count": len(note.files)}


@router.post("/{note_id}/detach")
async def detach_files(
    note_id: str,
    request: FileIdsRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    file_ids = request.file_ids
    query = (
        select(Note)
        .options(selectinload(Note.files))
        .where((Note.id == note_id) & (Note.user_id == current_user.id))
    )
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.files = [f for f in note.files if f.id not in file_ids]
    await db.commit()
    return {"message": "Files detached"}


@router.post("/{note_id}/attach-folders")
async def attach_folders(
    note_id: str,
    request: FolderIdsRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    folder_ids = request.folder_ids
    # Fetch note
    query = (
        select(Note)
        .options(selectinload(Note.folders))
        .where((Note.id == note_id) & (Note.user_id == current_user.id))
    )
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Fetch folders
    folders_result = await db.execute(
        select(Folder).where(
            Folder.id.in_(folder_ids) & (Folder.user_id == current_user.id)
        )
    )
    folders_to_attach = folders_result.scalars().all()

    # Append new folders (avoiding duplicates)
    current_ids = {f.id for f in note.folders}
    for folder in folders_to_attach:
        if folder.id not in current_ids:
            note.folders.append(folder)

    await db.commit()
    return {"message": "Folders attached", "folder_count": len(note.folders)}


@router.post("/{note_id}/detach-folders")
async def detach_folders(
    note_id: str,
    request: FolderIdsRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    folder_ids = request.folder_ids
    query = (
        select(Note)
        .options(selectinload(Note.folders))
        .where((Note.id == note_id) & (Note.user_id == current_user.id))
    )
    result = await db.execute(query)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.folders = [f for f in note.folders if f.id not in folder_ids]
    await db.commit()
    return {"message": "Folders detached"}
