from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Table, Column, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from app.database import Base
from app.services.storage import get_public_url
import uuid


class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String)
    nickname = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Folder(Base):
    __tablename__ = "folders"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    parent_id = Column(String(36), ForeignKey("folders.id"), nullable=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = Column(Integer, default=0)  # 0: False, 1: True. Using Integer for boolean behavior in some DBs or just standardizing
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    files = relationship("File", back_populates="folder")
    subfolders = relationship("Folder", backref=backref("parent", remote_side=[id]))


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
    folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String, index=True)
    storage_path: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0)
    original_created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    original_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_deleted: Mapped[bool] = mapped_column(Integer, default=0)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Relationship to Folder
    folder = relationship("Folder", back_populates="files")

    # Relationship to Notes
    notes: Mapped[List["Note"]] = relationship(
        secondary=file_note_association,
        back_populates="files",
        lazy="selectin"
    )

    @property
    def notes_count(self) -> int:
        return len(self.notes)

    @property
    def download_url(self) -> str:
        return get_public_url(self.storage_path) or f"/api/v1/files/download/{self.id}/{self.filename}"


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
