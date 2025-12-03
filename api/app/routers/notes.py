from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from api.app.database import get_async_session
from api.app.models import Note, User
from api.app.schemas import NoteCreate, NoteUpdate, NoteResponse
from api.app.services.security import get_current_user

router = APIRouter(prefix="/api/v1/notes", tags=["Notes"])


@router.get("/", response_model=list[NoteResponse])
async def get_notes(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有笔记"""
    stmt = select(Note).where(Note.user_id == current_user.id)
    result = await session.execute(stmt)
    notes = result.scalars().all()
    return notes


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """获取指定笔记"""
    stmt = select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id))
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


@router.post("/", response_model=NoteResponse)
async def create_note(
    note_data: NoteCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """创建新笔记"""
    note = Note(
        user_id=current_user.id,
        title=note_data.title,
        content=note_data.content
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.put("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: int,
    note_data: NoteUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """更新笔记"""
    stmt = select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id))
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    if note_data.title is not None:
        note.title = note_data.title
    if note_data.content is not None:
        note.content = note_data.content
    note.updated_at = datetime.utcnow()
    
    session.add(note)
    await session.commit()
    await session.refresh(note)
    return note


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """删除笔记"""
    stmt = select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id))
    result = await session.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    await session.delete(note)
    await session.commit()
    return {"message": "Note deleted successfully"}
