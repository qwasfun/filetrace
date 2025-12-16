from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_async_session

from app.models import User
from app.schemas import UserResponse
from app.services.security import get_password_hash, verify_password, get_current_user

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post("/", response_model=UserResponse)
async def create_user(username: str, password: str, session: AsyncSession = Depends(get_async_session)):
    hashed = get_password_hash(password)
    user = User(username=username, password=hashed)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/me", response_model=UserResponse)
async def get_me(session: AsyncSession = Depends(get_async_session),
                 current_user: User = Depends(get_current_user)
                 ):
    result = await session.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    return user
