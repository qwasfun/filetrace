"""
文件存储服务
支持本地存储和 S3 存储，支持从数据库动态加载配置
"""

import json
import os
from typing import Tuple

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .storage_backend import LocalStorageBackend, S3StorageBackend, StorageBackend


def _get_default_local_storage() -> StorageBackend:
    """
    获取默认本地存储后端（回退方案）

    Returns:
        LocalStorageBackend 实例
    """
    return LocalStorageBackend(base_dir="data/files")


async def get_storage_backend_by_id(
    session: AsyncSession, backend_id: str | None = None
) -> StorageBackend:
    """
    根据ID获取存储后端 (异步)
    如果ID为None，返回默认本地存储后端（兼容旧数据）
    """
    if not backend_id:
        return _get_default_local_storage()

    try:
        # 延迟导入以避免循环依赖
        from app.models import StorageBackendConfig

        stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
        result = await session.execute(stmt)
        backend_config = result.scalar_one_or_none()

        if backend_config:
            config = json.loads(backend_config.config_json)

            if backend_config.backend_type == "s3":
                return S3StorageBackend(**config)
            elif backend_config.backend_type == "local":
                return LocalStorageBackend(**config)
    except Exception as e:
        print(f"从数据库加载存储后端配置失败: {e}")

    # 如果找不到或出错，回退到默认本地存储
    return _get_default_local_storage()


async def get_default_storage_backend(
    session: AsyncSession,
) -> Tuple[StorageBackend, str | None]:
    """
    获取默认存储后端 (异步)

    Returns:
        (StorageBackend实例, backend_id)
    """
    try:
        from app.models import StorageBackendConfig

        stmt = select(StorageBackendConfig).where(
            StorageBackendConfig.is_default == 1,
            StorageBackendConfig.is_active == 1,
        )
        result = await session.execute(stmt)
        backend_config = result.scalar_one_or_none()

        if backend_config:
            config = json.loads(backend_config.config_json)
            backend = None

            if backend_config.backend_type == "s3":
                backend = S3StorageBackend(**config)
            elif backend_config.backend_type == "local":
                backend = LocalStorageBackend(**config)

            if backend:
                return backend, str(backend_config.id)
    except Exception as e:
        print(f"从数据库加载默认存储后端配置失败: {e}")

    # 回退到默认本地存储
    return _get_default_local_storage(), None


def save_file(
    file: UploadFile, backend: StorageBackend, user_id: str | None = None
) -> Tuple[str, int, dict]:
    """
    保存文件 (同步，需在线程池运行)

    Args:
        file: 上传的文件对象
        backend: 存储后端实例
        user_id: 用户ID（可选）

    Returns:
        Tuple[storage_path, size, file_type_info]
    """
    return backend.save(file, user_id)


def delete_file(storage_path: str, backend: StorageBackend) -> bool:
    """
    删除文件

    Args:
        storage_path: 文件存储路径
        backend: 存储后端实例

    Returns:
        是否删除成功
    """
    return backend.delete(storage_path)


def file_exists(storage_path: str, backend: StorageBackend) -> bool:
    """
    检查文件是否存在

    Args:
        storage_path: 文件存储路径
        backend: 存储后端实例

    Returns:
        文件是否存在
    """
    return backend.exists(storage_path)


def get_download_info(
    storage_path: str,
    backend: StorageBackend,
    filename: str | None = None,
    disposition: str = "attachment",
) -> dict:
    """
    获取文件下载信息

    Args:
        storage_path: 文件存储路径
        backend: 存储后端实例
        filename: 文件名（可选）
        disposition: Content-Disposition 类型 (attachment 或 inline)

    Returns:
        包含下载所需信息的字典
    """
    return backend.get_download_info(storage_path, filename, disposition)


def get_public_url(
    storage_path: str,
    backend: StorageBackend,
    filename: str | None = None,
    disposition: str = "attachment",
) -> str | None:
    """
    获取文件的公共 URL（签名后）

    Args:
        storage_path: 文件存储路径
        backend: 存储后端实例
        filename: 文件名（可选，用于设置 Content-Disposition）
        disposition: Content-Disposition 类型 (attachment 或 inline)

    Returns:
        公共 URL 或 None
    """
    return backend.get_public_url(storage_path, filename, disposition)
