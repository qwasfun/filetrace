from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String)
    nickname = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class File(Base):
    __tablename__ = "files"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    path = Column(String)
    mimetype = Column(String)
    note = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    __tablename__ = "notes"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    title = Column(String)
    content = Column(Text)
    # visibility: PRIVATE / PROTECTED / PUBLIC, default PRIVATE
    visibility = Column(String, default="PRIVATE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class NoteFile(Base):
    __tablename__ = "note_files"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    note_id = Column(String(36), ForeignKey("notes.id"))
    file_id = Column(String(36), ForeignKey("files.id"), nullable=True)
    source_type = Column(String)  # local / immich
    external_id = Column(String)  # immich asset id
