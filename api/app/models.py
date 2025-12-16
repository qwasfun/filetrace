from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import uuid


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String)
    nickname = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


# Many-to-Many Association Table
file_note_association = Table(
    "file_note_association",
    Base.metadata,
    Column("file_id", String(36), ForeignKey("files.id", ondelete="CASCADE"), primary_key=True),
    Column("note_id", String(36), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
)


class File(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    filename: Mapped[str] = mapped_column(String, index=True)
    storage_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship to Notes
    notes: Mapped[List["Note"]] = relationship(
        secondary=file_note_association,
        back_populates="files",
        lazy="selectin"
    )


class Note(Base):
    __tablename__ = "notes"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # visibility: PRIVATE / PROTECTED / PUBLIC, default PRIVATE
    visibility = Column(String, default="PRIVATE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to Files
    files: Mapped[List["File"]] = relationship(
        secondary=file_note_association,
        back_populates="notes",
        lazy="selectin"
    )
