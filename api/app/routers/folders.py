from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_async_session
from app.models import Folder, User
from app.schemas import FolderCreate, FolderUpdate, FolderResponse
from app.services.security import get_current_user
from datetime import datetime
from app.models import File
from app.services.storage import delete_file

router = APIRouter(prefix="/api/v1/folders", tags=["Folders"])

@router.post("/", response_model=FolderResponse)
async def create_folder(
    folder: FolderCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    new_folder = Folder(
        user_id=current_user.id,
        name=folder.name,
        parent_id=folder.parent_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_folder)
    await db.commit()
    await db.refresh(new_folder)
    return new_folder

@router.get("/", response_model=List[FolderResponse])
async def list_folders(
    parent_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Folder).where(Folder.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user)
):
    stmt = select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user)
):
    stmt = select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    if folder_update.name is not None:
        folder.name = folder_update.name
    if folder_update.parent_id is not None:
        # Check if parent exists and belongs to user
        parent_stmt = select(Folder).where(Folder.id == folder_update.parent_id, Folder.user_id == current_user.id)
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
    current_user: User = Depends(get_current_user)
):
    stmt = select(Folder).where(Folder.id == folder_id, Folder.user_id == current_user.id)
    result = await db.execute(stmt)
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    
    # Recursively delete all child folders and files
    async def delete_folder_recursive(folder_to_delete: Folder):
        # Find and delete all child folders
        child_folders_stmt = select(Folder).where(Folder.parent_id == folder_to_delete.id)
        child_folders_result = await db.execute(child_folders_stmt)
        child_folders = child_folders_result.scalars().all()
        
        for child_folder in child_folders:
            await delete_folder_recursive(child_folder)
        
        # Delete all files in this folder (assuming File model exists)
        files_stmt = select(File).where(File.folder_id == folder_to_delete.id)
        files_result = await db.execute(files_stmt)
        files = files_result.scalars().all()
        
        for file in files:
            await db.delete(file)
            # Delete from storage backend
            delete_file(file.storage_path)
        
        # Delete the folder itself
        await db.delete(folder_to_delete)
    
    await delete_folder_recursive(folder)
    await db.commit()
    return {"message": "Folder deleted"}
