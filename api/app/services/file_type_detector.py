"""
文件类型检测器
综合使用多种方法识别文件类型：文件扩展名、MIME类型、文件头魔术字节、UTF-8解码
"""

import mimetypes
import os
from typing import BinaryIO, Tuple


class FileTypeDetector:
    """文件类型检测器"""

    # 文件头魔术字节签名（前8字节）
    MAGIC_BYTES = {
        # 图片格式
        b"\xff\xd8\xff": ("image", "image/jpeg"),
        b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a": ("image", "image/png"),
        b"\x47\x49\x46\x38": ("image", "image/gif"),
        b"\x42\x4d": ("image", "image/bmp"),
        b"\x49\x49\x2a\x00": ("image", "image/tiff"),
        b"\x4d\x4d\x00\x2a": ("image", "image/tiff"),
        b"\x52\x49\x46\x46": ("image", "image/webp"),  # 需要进一步检查 WEBP 字符串
        b"\x00\x00\x01\x00": ("image", "image/x-icon"),
        # 视频格式
        b"\x00\x00\x00\x18\x66\x74\x79\x70": ("video", "video/mp4"),
        b"\x00\x00\x00\x20\x66\x74\x79\x70": ("video", "video/mp4"),
        b"\x00\x00\x00\x1c\x66\x74\x79\x70": ("video", "video/mp4"),
        b"\x1a\x45\xdf\xa3": ("video", "video/webm"),
        b"\x66\x4c\x61\x43": ("video", "video/x-flv"),
        # 文档格式
        b"\x25\x50\x44\x46": ("document", "application/pdf"),
        b"\x50\x4b\x03\x04": ("document", "application/zip"),  # ZIP/DOCX/XLSX/PPTX 等
        b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": (
            "document",
            "application/msword",
        ),  # DOC/XLS/PPT
        b"\x7b\x5c\x72\x74\x66": ("document", "application/rtf"),
        # 压缩格式
        b"\x1f\x8b": ("binary", "application/gzip"),
        b"\x42\x5a\x68": ("binary", "application/x-bzip2"),
        b"\x52\x61\x72\x21\x1a\x07": ("binary", "application/x-rar-compressed"),
        b"\x37\x7a\xbc\xaf\x27\x1c": ("binary", "application/x-7z-compressed"),
        # 可执行文件
        b"\x4d\x5a": ("binary", "application/x-msdownload"),  # EXE
        b"\x7f\x45\x4c\x46": ("binary", "application/x-executable"),  # ELF
        # 音频格式
        b"\x49\x44\x33": ("binary", "audio/mpeg"),  # MP3
        b"\xff\xfb": ("binary", "audio/mpeg"),
        b"\xff\xf3": ("binary", "audio/mpeg"),
        b"\xff\xf2": ("binary", "audio/mpeg"),
    }

    # MIME 类型映射
    MIME_CATEGORIES = {
        "text": [
            "text/plain",
            "text/html",
            "text/css",
            "text/javascript",
            "text/xml",
            "text/csv",
            "text/markdown",
            "text/x-python",
            "text/x-java",
            "text/x-c",
            "text/x-c++",
            "text/x-csharp",
            "application/json",
            "application/xml",
            "application/javascript",
            "application/x-yaml",
            "application/x-toml",
        ],
        "image": [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/bmp",
            "image/webp",
            "image/svg+xml",
            "image/tiff",
            "image/x-icon",
        ],
        "video": [
            "video/mp4",
            "video/mpeg",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-flv",
            "video/webm",
            "video/x-matroska",
        ],
        "document": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # XLSX
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # PPTX
            "application/rtf",
            "application/vnd.oasis.opendocument.text",  # ODT
            "application/vnd.oasis.opendocument.spreadsheet",  # ODS
            "application/vnd.oasis.opendocument.presentation",  # ODP
        ],
    }

    # 扩展名映射（补充 mimetypes 可能缺失的类型）
    EXT_CATEGORIES = {
        "text": [
            ".txt",
            ".md",
            ".markdown",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".html",
            ".htm",
            ".css",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".py",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".pl",
            ".sh",
            ".bat",
            ".ps1",
            ".sql",
            ".log",
            ".ini",
            ".cfg",
            ".conf",
            ".toml",
            ".env",
        ],
        "image": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".webp",
            ".svg",
            ".ico",
            ".tiff",
            ".tif",
            ".heic",
            ".heif",
        ],
        "video": [
            ".mp4",
            ".avi",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".mkv",
            ".m4v",
            ".mpg",
            ".mpeg",
            ".3gp",
        ],
        "document": [
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".odt",
            ".ods",
            ".odp",
            ".rtf",
            ".epub",
        ],
    }

    # 扩展名到 MIME 的补充映射
    EXT_MIME_OVERRIDES = {
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
        ".ts": "text/x-typescript",
        ".tsx": "text/x-typescript",
        ".jsx": "text/javascript",
        ".sass": "text/x-sass",
        ".scss": "text/x-scss",
        ".manifest": "text/cache-manifest",
        ".map": "application/json",
    }

    @classmethod
    def detect_by_magic_bytes(cls, file_content: bytes) -> Tuple[str, str]:
        """
        通过文件头魔术字节检测文件类型

        Args:
            file_content: 文件内容（至少前几百字节）

        Returns:
            (category, mime_type) 或 (None, None)
        """
        if not file_content:
            return None, None

        # 检查已知的魔术字节签名
        for magic, (category, mime_type) in cls.MAGIC_BYTES.items():
            if file_content.startswith(magic):
                # 特殊处理 ZIP 格式（可能是 DOCX/XLSX/PPTX）
                if magic == b"\x50\x4b\x03\x04":
                    # 尝试检测 Office 文档
                    if b"word/" in file_content[:1000]:
                        return (
                            "document",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )
                    elif b"xl/" in file_content[:1000]:
                        return (
                            "document",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                    elif b"ppt/" in file_content[:1000]:
                        return (
                            "document",
                            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        )
                    # 否则就是普通 ZIP
                    return "binary", "application/zip"

                # 特殊处理 RIFF 格式（可能是 WEBP 或 AVI）
                if magic == b"\x52\x49\x46\x46":
                    if len(file_content) > 12 and file_content[8:12] == b"WEBP":
                        return "image", "image/webp"
                    elif len(file_content) > 12 and file_content[8:12] == b"AVI ":
                        return "video", "video/x-msvideo"

                return category, mime_type

        return None, None

    @classmethod
    def detect_by_extension(cls, filename: str) -> Tuple[str, str]:
        """
        通过文件扩展名检测类型

        Args:
            filename: 文件名

        Returns:
            (category, mime_type) 或 (None, None)
        """
        ext = os.path.splitext(filename)[1].lower()

        if not ext:
            return None, None

        # 先检查扩展名分类
        for category, extensions in cls.EXT_CATEGORIES.items():
            if ext in extensions:
                # 优先使用手动覆盖的 MIME
                mime_type = cls.EXT_MIME_OVERRIDES.get(ext)
                if not mime_type:
                    mime_type = mimetypes.guess_type(filename)[0]
                if not mime_type:
                    mime_type = f"{category}/unknown"
                return category, mime_type

        # 使用 mimetypes 尝试识别
        mime_type = mimetypes.guess_type(filename)[0]
        if mime_type:
            category = cls.get_category_from_mime(mime_type)
            return category, mime_type

        return None, None

    @classmethod
    def get_category_from_mime(cls, mime_type: str) -> str:
        """
        从 MIME 类型获取分类

        Args:
            mime_type: MIME 类型

        Returns:
            分类：text, image, video, document, binary
        """
        if not mime_type:
            return "binary"

        # 精确匹配
        for category, mime_list in cls.MIME_CATEGORIES.items():
            if mime_type in mime_list:
                return category

        # 前缀匹配
        mime_prefix = mime_type.split("/")[0]
        if mime_prefix in ["text", "image", "video"]:
            return mime_prefix

        return "binary"

    @classmethod
    def is_text_content(cls, file_content: bytes, sample_size: int = 8192) -> bool:
        """
        通过 UTF-8 解码测试判断是否为文本文件

        Args:
            file_content: 文件内容
            sample_size: 采样大小

        Returns:
            是否为文本文件
        """
        if not file_content:
            return False

        # 取样本进行测试
        sample = file_content[:sample_size]

        try:
            # 尝试 UTF-8 解码
            decoded = sample.decode("utf-8")

            # 检查是否包含过多不可打印字符
            printable_count = sum(c.isprintable() or c.isspace() for c in decoded)
            printable_ratio = printable_count / len(decoded) if decoded else 0

            # 如果可打印字符比例超过 85%，认为是文本文件
            return printable_ratio > 0.85
        except UnicodeDecodeError:
            # UTF-8 解码失败，不是文本文件
            return False

    @classmethod
    def detect(
        cls, filename: str, file_content: bytes = None, mime_hint: str = None
    ) -> dict:
        """
        综合检测文件类型

        Args:
            filename: 文件名
            file_content: 文件内容（可选，用于魔术字节检测）
            mime_hint: MIME 类型提示（可选，来自上传时的 Content-Type）

        Returns:
            {
                'category': 'text' | 'document' | 'image' | 'video' | 'binary',
                'mime_type': str,
                'confidence': 'high' | 'medium' | 'low'
            }
        """
        detected_category = None
        detected_mime = None
        confidence = "low"

        # 1. 优先使用魔术字节检测（最可靠）
        if file_content:
            category, mime_type = cls.detect_by_magic_bytes(file_content)
            if category:
                detected_category = category
                detected_mime = mime_type
                confidence = "high"

        # 2. 使用扩展名检测
        if not detected_category:
            category, mime_type = cls.detect_by_extension(filename)
            if category:
                detected_category = category
                detected_mime = mime_type
                confidence = "medium"

        # 3. 使用提示的 MIME 类型
        if not detected_category and mime_hint:
            category = cls.get_category_from_mime(mime_hint)
            detected_category = category
            detected_mime = mime_hint
            confidence = "low"

        # 4. UTF-8 解码测试（作为文本文件的最后验证）
        if detected_category == "binary" and file_content:
            if cls.is_text_content(file_content):
                detected_category = "text"
                detected_mime = detected_mime or "text/plain"
                confidence = "medium"

        # 5. 默认分类
        if not detected_category:
            detected_category = "binary"
            detected_mime = detected_mime or "application/octet-stream"

        return {
            "category": detected_category,
            "mime_type": detected_mime or "application/octet-stream",
            "confidence": confidence,
        }
