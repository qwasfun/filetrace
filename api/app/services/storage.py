"""
文件存储服务
支持本地存储和 S3 存储，支持从数据库动态加载配置
"""

import json
import os
from typing import Tuple

from fastapi import UploadFile
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from .storage_backend import LocalStorageBackend, S3StorageBackend, StorageBackend


def _get_sync_engine():
    """获取同步数据库引擎"""
    from dotenv import load_dotenv

    load_dotenv()

    # 从环境变量获取数据库URL
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    if raw_db_url:
        # 将异步URL转换为同步URL
        if "sqlite+aiosqlite" in raw_db_url:
            db_url = raw_db_url.replace("sqlite+aiosqlite", "sqlite")
        elif "postgresql+asyncpg" in raw_db_url:
            db_url = raw_db_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
        else:
            db_url = raw_db_url
    else:
        db_url = "sqlite:///./data/app.sqlite"

    if db_url.startswith("sqlite"):
        return create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        return create_engine(db_url)


def get_storage_backend_from_db() -> StorageBackend:
    """
    从数据库获取默认存储后端配置

    Returns:
        StorageBackend 实例，如果数据库没有配置则回退到环境变量
    """
    try:
        from app.models import StorageBackendConfig

        engine = _get_sync_engine()
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        try:
            # 查找默认的存储后端配置
            stmt = select(StorageBackendConfig).where(
                StorageBackendConfig.is_default == 1,
                StorageBackendConfig.is_active == 1,
            )
            result = db.execute(stmt)
            backend_config = result.scalar_one_or_none()

            if backend_config:
                config = json.loads(backend_config.config_json)

                if backend_config.backend_type == "s3":
                    return S3StorageBackend(**config)
                elif backend_config.backend_type == "local":
                    return LocalStorageBackend(**config)
        finally:
            db.close()
    except Exception as e:
        print(f"从数据库加载存储后端配置失败: {e}，使用环境变量配置")

    # 回退到环境变量配置
    return get_storage_backend_from_env()


def get_storage_backend_from_env() -> StorageBackend:
    """
    从环境变量获取存储后端（回退方案）

    Returns:
        StorageBackend 实例
    """
    storage_type = os.getenv("STORAGE_TYPE", "local").lower()

    if storage_type == "s3":
        # S3 存储配置
        return S3StorageBackend(
            bucket_name=os.getenv("S3_BUCKET_NAME", ""),
            access_key=os.getenv("S3_ACCESS_KEY", ""),
            secret_key=os.getenv("S3_SECRET_KEY", ""),
            endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
            region_name=os.getenv("S3_REGION_NAME", "us-east-1"),
            public_url=os.getenv("S3_PUBLIC_URL") or None,
        )
    else:
        # 默认使用本地存储
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "data/files")
        return LocalStorageBackend(base_dir=base_dir)


def get_storage_backend() -> StorageBackend:
    """
    获取存储后端，优先从数据库加载，失败则使用环境变量

    Returns:
        StorageBackend 实例
    """
    return get_storage_backend_from_db()


# 全局存储后端实例
_storage_backend = None


def get_storage() -> StorageBackend:
    """获取全局存储后端实例（单例模式）"""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = get_storage_backend()
    return _storage_backend


def reload_storage_backend():
    """重新加载存储后端配置"""
    global _storage_backend
    _storage_backend = get_storage_backend()
    print("存储后端已重新加载")


def save_file(file: UploadFile, user_id: str = None) -> Tuple[str, int, dict]:
    """
    保存文件

    Args:
        file: 上传的文件对象
        user_id: 用户ID（可选）

    Returns:
        Tuple[storage_path, mime_type, size, file_type_info]
        file_type_info: {
            'category': 'text' | 'document' | 'image' | 'video' | 'binary',
            'mime_type': str,
            'confidence': 'high' | 'medium' | 'low'
        }
    """
    storage = get_storage()
    return storage.save(file, user_id)


def delete_file(storage_path: str) -> bool:
    """
    删除文件

    Args:
        storage_path: 文件存储路径

    Returns:
        是否删除成功
    """
    storage = get_storage()
    return storage.delete(storage_path)


def file_exists(storage_path: str) -> bool:
    """
    检查文件是否存在

    Args:
        storage_path: 文件存储路径

    Returns:
        文件是否存在
    """
    storage = get_storage()
    return storage.exists(storage_path)


def get_download_info(
    storage_path: str, filename: str = None, disposition: str = "attachment"
) -> dict:
    """
    获取文件下载信息

    Args:
        storage_path: 文件存储路径
        filename: 文件名（可选）
        disposition: Content-Disposition 类型 (attachment 或 inline)

    Returns:
        包含下载所需信息的字典
    """
    storage = get_storage()
    return storage.get_download_info(storage_path, filename, disposition)


def get_public_url(
    storage_path: str, filename: str = None, disposition: str = "attachment"
) -> str:
    """
    获取文件的公共 URL（签名后）

    Args:
        storage_path: 文件存储路径
        filename: 文件名（可选，用于设置 Content-Disposition）
        disposition: Content-Disposition 类型 (attachment 或 inline)

    Returns:
        公共 URL 或 None
    """
    storage = get_storage()
    return storage.get_public_url(storage_path, filename, disposition)
