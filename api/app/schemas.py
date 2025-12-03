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
