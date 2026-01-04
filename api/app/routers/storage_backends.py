"""
存储后端管理路由
"""

import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models import StorageBackendConfig, User
from app.schemas import (
    StorageBackendCreate,
    StorageBackendResponse,
    StorageBackendType,
    StorageBackendUpdate,
)
from app.services.security import get_current_user

router = APIRouter(prefix="/api/v1/storage-backends", tags=["storage-backends"])


def _config_to_dict(backend: StorageBackendConfig) -> dict:
    """将配置从JSON字符串转换为字典"""
    try:
        return json.loads(backend.config_json)
    except:
        return {}


def _backend_to_response(backend: StorageBackendConfig) -> StorageBackendResponse:
    """将数据库模型转换为响应模型"""
    return StorageBackendResponse(
        id=str(backend.id),
        name=str(backend.name),
        backend_type=str(backend.backend_type),
        is_active=bool(backend.is_active),
        is_default=bool(backend.is_default),
        config=_config_to_dict(backend),
        description=str(backend.description) if backend.description else None,
        created_at=backend.created_at,
        updated_at=backend.updated_at,
        created_by=str(backend.created_by) if backend.created_by else None,
    )


@router.post(
    "", response_model=StorageBackendResponse, status_code=status.HTTP_201_CREATED
)
async def create_storage_backend(
    backend_data: StorageBackendCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """创建新的存储后端配置"""
    # 检查名称是否已存在
    stmt = select(StorageBackendConfig).where(
        StorageBackendConfig.name == backend_data.name
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"存储后端名称 '{backend_data.name}' 已存在",
        )

    # 如果设置为默认，取消其他默认配置
    if backend_data.is_default:
        stmt = select(StorageBackendConfig).where(StorageBackendConfig.is_default == 1)
        result = await db.execute(stmt)
        for b in result.scalars():
            b.is_default = False

    # 创建新配置
    new_backend = StorageBackendConfig(
        name=backend_data.name,
        backend_type=backend_data.backend_type.value,
        config_json=backend_data.config.model_dump_json(),
        description=backend_data.description,
        is_active=backend_data.is_default,  # 默认后端自动激活
        is_default=backend_data.is_default,
        created_by=current_user.id,
    )

    db.add(new_backend)
    await db.commit()
    await db.refresh(new_backend)

    return _backend_to_response(new_backend)


@router.get("", response_model=List[StorageBackendResponse])
async def list_storage_backends(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取所有存储后端配置"""
    stmt = select(StorageBackendConfig).order_by(
        StorageBackendConfig.is_default.desc(), StorageBackendConfig.created_at.desc()
    )
    result = await db.execute(stmt)
    backends = result.scalars().all()

    return [_backend_to_response(backend) for backend in backends]


@router.get("/{backend_id}", response_model=StorageBackendResponse)
async def get_storage_backend(
    backend_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """获取指定存储后端配置"""
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
    result = await db.execute(stmt)
    backend = result.scalar_one_or_none()

    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="存储后端不存在"
        )

    return _backend_to_response(backend)


@router.put("/{backend_id}", response_model=StorageBackendResponse)
async def update_storage_backend(
    backend_id: str,
    backend_data: StorageBackendUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """更新存储后端配置"""
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
    result = await db.execute(stmt)
    backend = result.scalar_one_or_none()

    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="存储后端不存在"
        )

    # 更新字段
    if backend_data.name is not None:
        # 检查新名称是否已被其他后端使用
        stmt = select(StorageBackendConfig).where(
            StorageBackendConfig.name == backend_data.name,
            StorageBackendConfig.id != backend_id,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"存储后端名称 '{backend_data.name}' 已被使用",
            )
        backend.name = backend_data.name

    if backend_data.config is not None:
        backend.config_json = backend_data.config.model_dump_json()

    if backend_data.description is not None:
        backend.description = backend_data.description

    if backend_data.is_active is not None:
        backend.is_active = backend_data.is_active

    if backend_data.is_default is not None:
        if backend_data.is_default:
            # 取消其他默认配置
            stmt = select(StorageBackendConfig).where(
                StorageBackendConfig.id != backend_id,
                StorageBackendConfig.is_default == 1,
            )
            result = await db.execute(stmt)
            for b in result.scalars():
                b.is_default = False

            backend.is_default = True
            backend.is_active = True  # 默认后端自动激活
        else:
            # 不能取消最后一个默认配置
            stmt = select(StorageBackendConfig).where(
                StorageBackendConfig.is_default == 1
            )
            result = await db.execute(stmt)
            default_backends = result.scalars().all()

            if len(default_backends) == 1 and str(default_backends[0].id) == str(
                backend.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="至少需要保留一个默认存储后端",
                )
            backend.is_default = False

    await db.commit()
    await db.refresh(backend)

    return _backend_to_response(backend)


@router.delete("/{backend_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_storage_backend(
    backend_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """删除存储后端配置"""
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
    result = await db.execute(stmt)
    backend = result.scalar_one_or_none()

    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="存储后端不存在"
        )

    # 不能删除默认后端
    if backend.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除默认存储后端，请先设置其他后端为默认",
        )

    await db.delete(backend)
    await db.commit()

    return None


@router.post("/{backend_id}/set-default", response_model=StorageBackendResponse)
async def set_default_backend(
    backend_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """将指定后端设置为默认"""
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
    result = await db.execute(stmt)
    backend = result.scalar_one_or_none()

    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="存储后端不存在"
        )

    # 取消其他默认配置
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id != backend_id)
    result = await db.execute(stmt)
    for b in result.scalars():
        b.is_default = False

    # 设置为默认并激活
    backend.is_default = True
    backend.is_active = True

    await db.commit()
    await db.refresh(backend)

    return _backend_to_response(backend)


@router.post("/{backend_id}/test", status_code=status.HTTP_200_OK)
async def test_storage_backend(
    backend_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """测试存储后端连接"""
    stmt = select(StorageBackendConfig).where(StorageBackendConfig.id == backend_id)
    result = await db.execute(stmt)
    backend = result.scalar_one_or_none()

    if not backend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="存储后端不存在"
        )

    try:
        # 根据类型测试连接
        config = json.loads(backend.config_json)

        if backend.backend_type == StorageBackendType.LOCAL.value:
            from app.services.storage_backend import LocalStorageBackend

            test_backend = LocalStorageBackend(**config)
            # 检查目录是否存在或可创建
            import os

            if not os.path.exists(test_backend.base_dir):
                os.makedirs(test_backend.base_dir, exist_ok=True)
            return {"status": "success", "message": "本地存储测试成功"}

        elif backend.backend_type == StorageBackendType.S3.value:
            from app.services.storage_backend import S3StorageBackend

            test_backend = S3StorageBackend(**config)
            # 尝试列出桶（测试连接）
            test_backend.s3_client.head_bucket(Bucket=config["bucket_name"])
            return {"status": "success", "message": "S3存储连接测试成功"}

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的存储类型: {backend.backend_type}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"存储后端测试失败: {str(e)}",
        )


@router.get("/export/config")
async def export_storage_config(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """导出所有存储后端配置为 JSON 格式"""
    stmt = select(StorageBackendConfig).order_by(StorageBackendConfig.created_at)
    result = await db.execute(stmt)
    backends = result.scalars().all()

    export_data = {
        "version": "1.0",
        "export_time": datetime.utcnow().isoformat(),
        "total_count": len(backends),
        "backends": [
            {
                "name": backend.name,
                "backend_type": backend.backend_type,
                "config": _config_to_dict(backend),
                "description": backend.description,
                "is_active": bool(backend.is_active),
                "is_default": bool(backend.is_default),
            }
            for backend in backends
        ],
    }

    filename = f"storage_config_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    return JSONResponse(
        content=export_data,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import/config")
async def import_storage_config(
    file: UploadFile = File(...),
    replace_existing: bool = False,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """从 JSON 文件导入存储后端配置

    Args:
        file: JSON 配置文件
        replace_existing: 是否替换现有同名配置（默认 False，跳过同名配置）
    """
    try:
        # 读取文件内容
        content = await file.read()
        import_data = json.loads(content)

        # 验证数据格式
        if "backends" not in import_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的配置文件格式，缺少 'backends' 字段",
            )

        backends_to_import = import_data["backends"]
        if not isinstance(backends_to_import, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="'backends' 必须是数组"
            )

        # 统计信息
        stats = {
            "total": len(backends_to_import),
            "imported": 0,
            "skipped": 0,
            "updated": 0,
            "errors": [],
        }

        # 获取现有配置
        stmt = select(StorageBackendConfig)
        result = await db.execute(stmt)
        existing_backends = {b.name: b for b in result.scalars().all()}

        # 如果要设置新的默认后端，先取消所有现有默认
        has_new_default = any(b.get("is_default") for b in backends_to_import)
        if has_new_default:
            for backend in existing_backends.values():
                backend.is_default = False

        # 导入配置
        for idx, backend_data in enumerate(backends_to_import):
            try:
                # 验证必需字段
                if not all(
                    k in backend_data for k in ["name", "backend_type", "config"]
                ):
                    stats["errors"].append(
                        f"配置 #{idx + 1}: 缺少必需字段 (name, backend_type, config)"
                    )
                    stats["skipped"] += 1
                    continue

                name = backend_data["name"]
                backend_type = backend_data["backend_type"]
                config = backend_data["config"]

                # 验证后端类型
                if backend_type not in ["local", "s3"]:
                    stats["errors"].append(
                        f"配置 '{name}': 不支持的存储类型 '{backend_type}'"
                    )
                    stats["skipped"] += 1
                    continue

                # 检查是否存在同名配置
                if name in existing_backends:
                    if replace_existing:
                        # 更新现有配置
                        backend = existing_backends[name]
                        backend.backend_type = backend_type
                        backend.config_json = json.dumps(config)
                        backend.description = backend_data.get("description")
                        backend.is_active = backend_data.get("is_active", False)
                        backend.is_default = backend_data.get("is_default", False)
                        backend.updated_at = datetime.utcnow()
                        stats["updated"] += 1
                    else:
                        stats["errors"].append(f"配置 '{name}': 已存在，跳过")
                        stats["skipped"] += 1
                        continue
                else:
                    # 创建新配置
                    new_backend = StorageBackendConfig(
                        id=str(uuid.uuid4()),
                        name=name,
                        backend_type=backend_type,
                        config_json=json.dumps(config),
                        description=backend_data.get("description"),
                        is_active=backend_data.get("is_active", False),
                        is_default=backend_data.get("is_default", False),
                        created_by=current_user.id,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.add(new_backend)
                    stats["imported"] += 1

            except Exception as e:
                stats["errors"].append(
                    f"配置 #{idx + 1} ('{backend_data.get('name', 'unknown')}'): {str(e)}"
                )
                stats["skipped"] += 1

        # 提交更改
        await db.commit()

        return {
            "status": "success",
            "message": f"导入完成: {stats['imported']} 个新增, {stats['updated']} 个更新, {stats['skipped']} 个跳过",
            "stats": stats,
        }

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的 JSON 文件"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}",
        )
