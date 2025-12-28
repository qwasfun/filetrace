"""
文件存储服务
支持本地存储和 S3 存储
"""
import os
from typing import Tuple
from fastapi import UploadFile
from .storage_backend import StorageBackend, LocalStorageBackend, S3StorageBackend


def get_storage_backend() -> StorageBackend:
    """
    根据环境变量获取存储后端
    
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
            public_url=os.getenv("S3_PUBLIC_URL") or None
        )
    else:
        # 默认使用本地存储
        base_dir = os.getenv("LOCAL_STORAGE_DIR", "data/files")
        return LocalStorageBackend(base_dir=base_dir)


# 全局存储后端实例
_storage_backend = None


def get_storage() -> StorageBackend:
    """获取全局存储后端实例（单例模式）"""
    global _storage_backend
    if _storage_backend is None:
        _storage_backend = get_storage_backend()
    return _storage_backend


def save_file(file: UploadFile, user_id: str = None) -> Tuple[str, str, int, dict]:
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


def get_download_info(storage_path: str, filename: str = None, disposition: str = 'attachment') -> dict:
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


def get_public_url(storage_path: str, filename: str = None, disposition: str = 'attachment') -> str:
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

