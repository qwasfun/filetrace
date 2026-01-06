from datetime import datetime
from enum import Enum

from pydantic import BaseModel


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


class FileResponseModel(BaseModel):
    id: str
    user_id: str
    folder_id: str | None = None
    filename: str
    storage_path: str
    storage_backend_id: str | None = None
    mime_type: str
    size: int
    file_type: str | None = None  # text, document, image, video, binary
    file_type_confidence: str | None = None  # high, medium, low
    original_created_at: datetime | None = None
    original_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool | int = False
    deleted_at: datetime | None = None
    notes_count: int = 0
    download_url: str | None = None
    preview_url: str | None = None

    class Config:
        from_attributes = True


class FolderBasicInfo(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteResponse(BaseModel):
    id: str
    user_id: str
    title: str | None
    content: str
    visibility: Visibility
    created_at: datetime
    updated_at: datetime
    files: list[FileResponseModel] = []
    folders: list[FolderBasicInfo] = []

    class Config:
        from_attributes = True


class FileMove(BaseModel):
    folder_id: str | None


class FileRename(BaseModel):
    filename: str


class BatchFileOperation(BaseModel):
    file_ids: list[str]


class BatchFileMove(BatchFileOperation):
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
    is_deleted: bool | int = False
    deleted_at: datetime | None = None

    class Config:
        from_attributes = True


class FolderResponseWithNotes(FolderBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool | int = False
    deleted_at: datetime | None = None
    notes: list["NoteResponse"] = []

    class Config:
        from_attributes = True


class BatchFolderOperation(BaseModel):
    folder_ids: list[str]


class BatchFolderMove(BatchFolderOperation):
    parent_id: str | None


class UserResponse(BaseModel):
    id: str
    username: str
    nickname: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StorageBackendType(str, Enum):
    LOCAL = "local"
    S3 = "s3"


class LocalStorageConfig(BaseModel):
    """本地存储配置"""

    base_dir: str = "data/files"


class S3StorageConfig(BaseModel):
    """S3存储配置"""

    bucket_name: str
    access_key: str
    secret_key: str
    endpoint_url: str | None = None
    region_name: str = "us-east-1"
    public_url: str | None = None


class StorageBackendCreate(BaseModel):
    """创建存储后端"""

    name: str
    backend_type: StorageBackendType
    config: LocalStorageConfig | S3StorageConfig
    description: str | None = None
    is_default: bool = False


class StorageBackendUpdate(BaseModel):
    """更新存储后端"""

    name: str | None = None
    config: LocalStorageConfig | S3StorageConfig | None = None
    description: str | None = None
    is_active: bool | None = None
    is_default: bool | None = None


class StorageBackendResponse(BaseModel):
    """存储后端响应"""

    id: str
    name: str
    backend_type: str
    is_active: bool
    is_default: bool
    config: dict
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None

    class Config:
        from_attributes = True
