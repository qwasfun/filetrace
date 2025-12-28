from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import File, Note, User
from app.services.security import get_current_user

router = APIRouter(prefix="/api/v1/stats", tags=["Stats"])


class StatsResponse(BaseModel):
    storage_usage: int
    file_count: int
    note_count: int
    today_activity: int


@router.get("/", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    # Calculate file stats (count and total size)
    # Filter by user_id and ensure not deleted
    file_query = select(func.count(File.id), func.sum(File.size)).where(
        File.user_id == current_user.id, File.is_deleted == 0
    )

    file_result = await session.execute(file_query)
    file_count, storage_usage = file_result.one()

    # Handle None for sum if no files exist
    storage_usage = storage_usage or 0

    # Calculate note stats
    note_query = select(func.count(Note.id)).where(Note.user_id == current_user.id)
    note_result = await session.execute(note_query)
    note_count = note_result.scalar() or 0

    # Calculate today's activity
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    today_files_query = select(func.count(File.id)).where(
        File.user_id == current_user.id, File.is_deleted == 0, File.created_at >= today
    )
    today_files_count = (await session.execute(today_files_query)).scalar() or 0

    today_notes_query = select(func.count(Note.id)).where(
        Note.user_id == current_user.id,
        or_(Note.created_at >= today, Note.updated_at >= today),
    )
    today_notes_count = (await session.execute(today_notes_query)).scalar() or 0

    today_activity = today_files_count + today_notes_count

    return StatsResponse(
        storage_usage=int(storage_usage),
        file_count=file_count,
        note_count=note_count,
        today_activity=today_activity,
    )
