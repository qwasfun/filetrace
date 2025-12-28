from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import File, Folder, User
from app.schemas import (
    BatchFolderMove,
    BatchFolderOperation,
    FolderCreate,
    FolderResponse,
    FolderUpdate,
)
from app.services.security import get_current_user
from app.services.storage import delete_file

router = APIRouter(prefix="/api/v1/folders", tags=["Folders"])


@router.post("/", response_model=FolderResponse)
async def create_folder(
    folder: FolderCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    new_folder = Folder(
        user_id=current_user.id,
        name=folder.name,
        parent_id=folder.parent_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder


@router.get("/", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Folder).where(
        Folder.user_id == current_user.id, Folder.is_deleted == 0
    )
    if parent_id:
        stmt = stmt.where(Folder.parent_id == parent_id)
    else:
        stmt = stmt.where(Folder.parent_id.is_(None))

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Folder).where(
        Folder.id == folder_id, Folder.user_id == current_user.id
    )
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: str,
    folder_update: FolderUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Folder).where(
        Folder.id == folder_id, Folder.user_id == current_user.id
    )
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    if folder_update.name is not None:
        folder.name = folder_update.name
    if folder_update.parent_id is not None:
        # Check if parent exists and belongs to user
        parent_stmt = select(Folder).where(
            Folder.id == folder_update.parent_id, Folder.user_id == current_user.id
        )
        parent_res = await db.execute(parent_stmt)
        if not parent_res.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Parent folder not found")
        folder.parent_id = folder_update.parent_id

    folder.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(folder)
    return folder


@router.delete("/{folder_id}")
async def delete_folder(
    folder_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Folder).where(
        Folder.id == folder_id, Folder.user_id == current_user.id
    )
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    folder.is_deleted = 1
    folder.deleted_at = datetime.utcnow()
    await db.commit()
    return {"message": "Folder moved to recycle bin"}


@router.post("/batch/move")
async def batch_move_folders(
    batch_move: BatchFolderMove,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if batch_move.parent_id:
        parent_stmt = select(Folder).where(
            Folder.id == batch_move.parent_id, Folder.user_id == current_user.id
        )
        parent_res = await db.execute(parent_stmt)
        if not parent_res.scalar_one_or_none():
            raise HTTPException(
                status_code=400, detail="Target parent folder not found"
            )

    stmt = select(Folder).where(
        Folder.id.in_(batch_move.folder_ids), Folder.user_id == current_user.id
    )
    result = await db.execute(stmt)
    folders = result.scalars().all()

    for folder in folders:
        # Prevent moving a folder into itself or its children (basic check)
        if folder.id == batch_move.parent_id:
            continue  # Skip invalid move
        folder.parent_id = batch_move.parent_id

    await db.commit()
    return {"message": f"Moved {len(folders)} folders"}


@router.post("/batch/delete")
async def batch_delete_folders(
    batch_op: BatchFolderOperation,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Folder).where(
        Folder.id.in_(batch_op.folder_ids), Folder.user_id == current_user.id
    )
    result = await db.execute(stmt)
    folders = result.scalars().all()

    for folder in folders:
        folder.is_deleted = 1
        folder.deleted_at = datetime.utcnow()

    await db.commit()
    return {"message": f"Moved {len(folders)} folders to recycle bin"}
