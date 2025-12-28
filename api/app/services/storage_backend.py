"""
存储后端抽象基类和具体实现
支持本地存储和 S3 兼容存储
"""

import mimetypes
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime
from typing import BinaryIO, Tuple
from urllib.parse import quote

import boto3
import shortuuid
from botocore.exceptions import ClientError
from fastapi import UploadFile

from .file_type_detector import FileTypeDetector


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def save(self, file: UploadFile, user_id: str = None) -> Tuple[str, int, dict]:
        """
        保存文件

        Args:
            file: 上传的文件对象
            user_id: 用户ID（可选，用于组织文件结构）

        Returns:
            Tuple[storage_path, size, file_type_info]
            file_type_info: {
                'category': 'text' | 'document' | 'image' | 'video' | 'binary',
                'mime_type': str,
                'confidence': 'high' | 'medium' | 'low'
            }
        """
        pass

    @abstractmethod
    def delete(self, storage_path: str) -> bool:
        """
        删除文件

        Args:
            storage_path: 文件存储路径

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def exists(self, storage_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            storage_path: 文件存储路径

        Returns:
            文件是否存在
        """
        pass

    @abstractmethod
    def get_download_info(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ) -> dict:
        """
        获取文件下载信息

        Args:
            storage_path: 文件存储路径

        Returns:
            包含下载所需信息的字典
        """
        pass

    def get_public_url(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ):
        pass


class LocalStorageBackend(StorageBackend):
    """本地文件存储后端"""

    def __init__(self, base_dir: str = "data/files"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _normalize_path_to_url(self, filepath: str) -> str:
        """将本地文件路径转换为URL友好的格式（使用/作为分隔符）"""
        return filepath.replace("\\", "/")

    def save(self, file: UploadFile, user_id: str = None) -> Tuple[str, int, dict]:
        """保存文件到本地磁盘"""
        # 生成日期和时间
        now = datetime.now()
        date_dir = now.strftime("%Y%m%d")

        # 构建路径：userid/日期/uuid.ext
        if user_id:
            target_dir = os.path.join(self.base_dir, user_id, date_dir)
        else:
            target_dir = os.path.join(self.base_dir, "anonymous", date_dir)
        os.makedirs(target_dir, exist_ok=True)

        # 使用 UUID 生成文件名
        file_ext = os.path.splitext(file.filename)[1]
        new_filename = f"{shortuuid.uuid()}{file_ext}"
        filepath = os.path.join(target_dir, new_filename)

        # 读取文件内容用于类型检测（读取前8KB用于魔术字节检测）
        file_content = file.file.read(8192)
        file.file.seek(0)  # 重置文件指针

        # 保存文件
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 获取文件信息
        size = os.path.getsize(filepath)
        storage_path = self._normalize_path_to_url(filepath)

        # 检测文件类型
        file_type_info = FileTypeDetector.detect(
            filename=file.filename,
            file_content=file_content,
            mime_hint=file.content_type,
        )

        return storage_path, size, file_type_info

    def delete(self, storage_path: str) -> bool:
        """从本地磁盘删除文件"""
        try:
            if os.path.exists(storage_path):
                os.remove(storage_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    def exists(self, storage_path: str) -> bool:
        """检查本地文件是否存在"""
        return os.path.exists(storage_path)

    def get_download_info(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ) -> dict:
        """获取本地文件下载信息"""
        return {"type": "local", "path": storage_path}

    def get_public_url(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ) -> str:
        """
        本地存储不支持公共 URL，返回 None
        """
        return None


class S3StorageBackend(StorageBackend):
    """S3 兼容存储后端（支持 AWS S3, MinIO, 阿里云 OSS 等）"""

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str = None,
        region_name: str = "us-east-1",
        public_url: str = None,
    ):
        """
        初始化 S3 存储后端

        Args:
            bucket_name: S3 桶名称
            access_key: 访问密钥 ID
            secret_key: 访问密钥
            endpoint_url: S3 端点 URL（用于 MinIO 等兼容服务）
            region_name: 区域名称
            public_url: 公共访问 URL（可选，用于直接下载）
        """
        self.bucket_name = bucket_name
        self.public_url = public_url
        self.endpoint_url = endpoint_url
        self.region_name = region_name

        # 创建 S3 配置
        # 禁用分块传输以兼容更多 S3 服务（如阿里云 OSS）
        # https://help.aliyun.com/zh/oss/developer-reference/use-aws-sdks-to-access-oss
        config = boto3.session.Config(
            signature_version="s3", s3={"addressing_style": "virtual"}
        )

        # 创建 S3 客户端
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region_name,
            config=config,
        )

        # 确保桶存在
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """确保 S3 桶存在，不存在则创建"""
        try:
            # 检查桶是否存在
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"S3 桶 '{self.bucket_name}' 已存在")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")

            # 如果是 404 错误，说明桶不存在，尝试创建
            if error_code == "404":
                try:
                    # 根据是否有自定义端点判断创建方式
                    if self.endpoint_url:
                        # 对于 MinIO 等自定义端点，直接创建
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        # 对于 AWS S3，需要考虑区域
                        # us-east-1 不需要 LocationConstraint
                        if (
                            hasattr(self, "region_name")
                            and self.region_name != "us-east-1"
                        ):
                            self.s3_client.create_bucket(
                                Bucket=self.bucket_name,
                                CreateBucketConfiguration={
                                    "LocationConstraint": self.region_name
                                },
                            )
                        else:
                            self.s3_client.create_bucket(Bucket=self.bucket_name)
                    print(f"S3 桶 '{self.bucket_name}' 创建成功")
                except ClientError as create_error:
                    error_msg = str(create_error)
                    # 如果错误是因为需要使用虚拟主机样式或桶已存在，可以忽略
                    if (
                        "SecondLevelDomainForbidden" in error_msg
                        or "BucketAlreadyExists" in error_msg
                        or "BucketAlreadyOwnedByYou" in error_msg
                    ):
                        print(
                            f"S3 桶 '{self.bucket_name}' 可能已存在或需要手动创建: {error_msg}"
                        )
                    else:
                        print(f"创建 S3 桶失败: {error_msg}")
            else:
                # 其他错误，如权限问题等
                print(f"检查 S3 桶时出错: {e}")

    def _generate_s3_key(self, filename: str, user_id: str = None) -> str:
        """
        生成 S3 对象键
        格式：userid/日期/uuid.ext

        Args:
            filename: 文件名
            user_id: 用户ID

        Returns:
            S3 对象键
        """
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")

        file_ext = os.path.splitext(filename)[1]
        new_filename = f"{shortuuid.uuid()}{file_ext}"

        if user_id:
            return f"{user_id}/{date_str}/{new_filename}"
        return f"anonymous/{date_str}/{new_filename}"

    def save(self, file: UploadFile, user_id: str = None) -> Tuple[str, int, dict]:
        """保存文件到 S3"""
        # 生成 S3 键
        s3_key = self._generate_s3_key(file.filename, user_id)

        # 读取文件内容
        file_content = file.file.read()
        size = len(file_content)

        # 检测文件类型（使用完整内容或前8KB）
        detection_content = (
            file_content[:8192] if len(file_content) > 8192 else file_content
        )
        file_type_info = FileTypeDetector.detect(
            filename=file.filename,
            file_content=detection_content,
            mime_hint=file.content_type,
        )

        # 上传到 S3
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file_type_info.get("mime_type"),
                ContentLength=size,  # 显式设置内容长度，避免 chunked 编码
            )
        except Exception as e:
            raise Exception(f"上传文件到 S3 失败: {e}")

        # 重置文件指针（如果需要再次读取）
        file.file.seek(0)

        return s3_key, size, file_type_info

    def delete(self, storage_path: str) -> bool:
        """从 S3 删除文件"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=storage_path)
            return True
        except Exception as e:
            print(f"从 S3 删除文件失败: {e}")
            return False

    def exists(self, storage_path: str) -> bool:
        """检查 S3 文件是否存在"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=storage_path)
            return True
        except ClientError:
            return False

    def get_download_info(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ) -> dict:
        """获取 S3 文件下载信息"""
        # 生成预签名 URL（有效期 1 小时）
        try:
            params = {"Bucket": self.bucket_name, "Key": storage_path}

            if filename:
                encoded_filename = quote(filename)
                params["ResponseContentDisposition"] = (
                    f"{disposition}; filename*=UTF-8''{encoded_filename}"
                )

            presigned_url = self.s3_client.generate_presigned_url(
                "get_object", Params=params, ExpiresIn=3600  # 1 小时
            )
            return {
                "type": "s3",
                "presigned_url": presigned_url,
                "bucket": self.bucket_name,
                "key": storage_path,
            }
        except Exception as e:
            raise Exception(f"生成预签名 URL 失败: {e}")

    def get_public_url(
        self, storage_path: str, filename: str = None, disposition: str = "attachment"
    ) -> str:
        """
        生成签名后的公共 URL

        Args:
            storage_path: S3 对象键
            filename: 文件名（可选，用于设置 Content-Disposition）
            disposition: Content-Disposition 类型 (attachment 或 inline)

        Returns:
            签名后的公共 URL
        """
        # 如果配置了公共 URL，使用自定义端点生成签名 URL
        if self.public_url:
            # 使用自定义端点创建临时客户端
            public_client = boto3.client(
                "s3",
                aws_access_key_id=self.s3_client._request_signer._credentials.access_key,
                aws_secret_access_key=self.s3_client._request_signer._credentials.secret_key,
                endpoint_url=(
                    f"https://{self.public_url}"
                    if not self.public_url.startswith("http")
                    else self.public_url
                ),
                region_name=self.region_name,
                config=boto3.session.Config(
                    signature_version="s3", s3={"addressing_style": "virtual"}
                ),
            )
            try:
                params = {"Bucket": self.bucket_name, "Key": storage_path}

                if filename:
                    encoded_filename = quote(filename)
                    params["ResponseContentDisposition"] = (
                        f"{disposition}; filename*=UTF-8''{encoded_filename}"
                    )

                presigned_url = public_client.generate_presigned_url(
                    "get_object", Params=params, ExpiresIn=3600  # 1 小时
                )
                return presigned_url
            except Exception as e:
                print(f"使用公共 URL 生成签名 URL 失败: {e}，回退到默认方式")

        # 默认使用标准签名 URL
        return self.get_download_info(storage_path, filename, disposition)[
            "presigned_url"
        ]

    def get_object(self, storage_path: str) -> bytes:
        """
        获取 S3 对象内容

        Args:
            storage_path: S3 对象键

        Returns:
            文件内容
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=storage_path
            )
            return response["Body"].read()
        except Exception as e:
            raise Exception(f"从 S3 获取文件失败: {e}")
