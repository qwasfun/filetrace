from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class Visibility(str, Enum):
    PRIVATE = "PRIVATE"
    PROTECTED = "PROTECTED"
    PUBLIC = "PUBLIC"


class NoteCreate(BaseModel):
    title: str
    content: str
    visibility: Visibility | None = Visibility.PRIVATE


class NoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    visibility: Visibility | None = None


class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str
    content: str
    visibility: Visibility
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FileResponseModel(BaseModel):
    id: str
    user_id: str
    folder_id: str | None = None
    filename: str
    storage_path: str
    mime_type: str
    size: int
    created_at: datetime

    class Config:
        from_attributes = True


class FileMove(BaseModel):
    folder_id: str | None


class FolderBase(BaseModel):
    name: str
    parent_id: str | None = None


class FolderCreate(FolderBase):
    pass


class FolderUpdate(BaseModel):
    name: str | None = None
    parent_id: str | None = None


class FolderResponse(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
