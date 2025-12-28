from typing import List, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import inspect as sqlalchemy_inspect
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import File, Folder, User
from app.schemas import FileResponseModel, FolderResponse
from app.services.security import get_current_user
from app.services.storage import delete_file as delete_file_storage
from app.services.storage import get_public_url

router = APIRouter(prefix="/api/v1/recycle", tags=["Recycle Bin"])


class RestoreRequest(BaseModel):
    file_ids: List[str] = []
    folder_ids: List[str] = []


class DeleteRequest(BaseModel):
    file_ids: List[str] = []
    folder_ids: List[str] = []


@router.get("/items")
async def list_recycle_bin_items(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    # Get deleted folders
    folder_stmt = select(Folder).where(
        Folder.user_id == current_user.id, Folder.is_deleted == 1
    )
    folder_res = await db.execute(folder_stmt)
    folders = folder_res.scalars().all()

    # Get deleted files
    file_stmt = select(File).where(
        File.user_id == current_user.id, File.is_deleted == 1
    )
    file_res = await db.execute(file_stmt)
    files = file_res.scalars().all()

    return {
        "folders": folders,
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "size": f.size,
                "storage_path": f.storage_path,
                "download_url": get_public_url(f.storage_path)
                or f"/api/v1/files/download/{f.id}/{f.filename}",
                "mime_type": f.mime_type,
                "created_at": f.created_at,
            }
            for f in files
        ],
    }


@router.post("/restore")
async def restore_items(
    request: RestoreRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if request.file_ids:
        stmt = select(File).where(
            File.id.in_(request.file_ids), File.user_id == current_user.id
        )
        result = await db.execute(stmt)
        files = result.scalars().all()
        for file in files:
            file.is_deleted = 0
            file.deleted_at = None

    if request.folder_ids:
        stmt = select(Folder).where(
            Folder.id.in_(request.folder_ids), Folder.user_id == current_user.id
        )
        result = await db.execute(stmt)
        folders = result.scalars().all()
        for folder in folders:
            folder.is_deleted = 0
            folder.deleted_at = None

    await db.commit()
    return {"message": "Items restored"}


@router.delete("/permanent")
async def permanent_delete_items(
    request: DeleteRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    # Delete files
    if request.file_ids:
        stmt = select(File).where(
            File.id.in_(request.file_ids), File.user_id == current_user.id
        )
        result = await db.execute(stmt)
        files = result.scalars().all()
        for file in files:
            if file in db:
                await db.delete(file)
                # Physical delete
                try:
                    delete_file_storage(file.storage_path)
                except Exception as e:
                    print(f"Error deleting file {file.id}: {e}")

        # Flush file deletes
        if files:
            await db.flush()

    # Delete folders (recursive)
    if request.folder_ids:
        # Helper for recursive delete
        async def delete_folder_recursive(folder_to_delete: Folder):
            # Check if object is in valid state before proceeding
            if folder_to_delete not in db:
                return

            # Find and delete all child folders
            child_folders_stmt = select(Folder).where(
                Folder.parent_id == folder_to_delete.id
            )
            child_folders_result = await db.execute(child_folders_stmt)
            child_folders = child_folders_result.scalars().all()

            for child_folder in child_folders:
                await delete_folder_recursive(child_folder)

            # Flush to ensure child deletes are processed
            await db.flush()

            # Delete all files in this folder
            files_stmt = select(File).where(File.folder_id == folder_to_delete.id)
            files_result = await db.execute(files_stmt)
            files = files_result.scalars().all()

            for file in files:
                if file in db:
                    await db.delete(file)
                    try:
                        delete_file_storage(file.storage_path)
                    except Exception as e:
                        print(f"Error deleting file {file.id}: {e}")

            # Flush file deletes before deleting folder
            await db.flush()

            # Check again before deleting the folder itself
            if folder_to_delete in db:
                await db.delete(folder_to_delete)

        stmt = select(Folder).where(
            Folder.id.in_(request.folder_ids), Folder.user_id == current_user.id
        )
        result = await db.execute(stmt)
        folders = result.scalars().all()
        for folder in folders:
            await delete_folder_recursive(folder)

    await db.commit()
    return {"message": "Items permanently deleted"}
