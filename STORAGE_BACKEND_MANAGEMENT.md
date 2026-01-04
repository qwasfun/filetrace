# 存储后端动态管理功能

## 功能概述

本功能允许管理员通过API动态添加、删除和管理多个存储后端配置，支持本地存储和S3兼容存储。系统会优先从数据库加载默认存储后端配置，如果数据库中没有配置，则回退到环境变量。

## API接口

### 1. 创建存储后端

**POST** `/api/v1/storage-backends`

创建新的存储后端配置。

**请求体示例 - 本地存储：**
```json
{
  "name": "本地存储1",
  "backend_type": "local",
  "config": {
    "base_dir": "data/files"
  },
  "description": "主要的本地文件存储",
  "is_default": true
}
```

**请求体示例 - S3存储：**
```json
{
  "name": "S3存储1",
  "backend_type": "s3",
  "config": {
    "bucket_name": "my-bucket",
    "access_key": "YOUR_ACCESS_KEY",
    "secret_key": "YOUR_SECRET_KEY",
    "endpoint_url": "https://s3.amazonaws.com",
    "region_name": "us-east-1",
    "public_url": null
  },
  "description": "AWS S3 存储",
  "is_default": false
}
```

**响应：** 201 Created
```json
{
  "id": "uuid",
  "name": "本地存储1",
  "backend_type": "local",
  "is_active": true,
  "is_default": true,
  "config": {
    "base_dir": "data/files"
  },
  "description": "主要的本地文件存储",
  "created_at": "2025-12-31T00:00:00",
  "updated_at": "2025-12-31T00:00:00",
  "created_by": "user_id"
}
```

### 2. 获取所有存储后端

**GET** `/api/v1/storage-backends`

获取所有存储后端配置列表。

**响应：** 200 OK
```json
[
  {
    "id": "uuid1",
    "name": "本地存储1",
    "backend_type": "local",
    "is_active": true,
    "is_default": true,
    "config": {...},
    "description": "主要的本地文件存储",
    "created_at": "2025-12-31T00:00:00",
    "updated_at": "2025-12-31T00:00:00",
    "created_by": "user_id"
  },
  {
    "id": "uuid2",
    "name": "S3存储1",
    "backend_type": "s3",
    "is_active": false,
    "is_default": false,
    "config": {...},
    "description": "AWS S3 存储",
    "created_at": "2025-12-31T00:00:00",
    "updated_at": "2025-12-31T00:00:00",
    "created_by": "user_id"
  }
]
```

### 3. 获取指定存储后端

**GET** `/api/v1/storage-backends/{backend_id}`

获取指定ID的存储后端配置。

**响应：** 200 OK
```json
{
  "id": "uuid",
  "name": "本地存储1",
  "backend_type": "local",
  "is_active": true,
  "is_default": true,
  "config": {...},
  "description": "主要的本地文件存储",
  "created_at": "2025-12-31T00:00:00",
  "updated_at": "2025-12-31T00:00:00",
  "created_by": "user_id"
}
```

### 4. 更新存储后端

**PUT** `/api/v1/storage-backends/{backend_id}`

更新存储后端配置。

**请求体示例：**
```json
{
  "name": "本地存储-更新",
  "config": {
    "base_dir": "data/files_new"
  },
  "description": "更新后的描述",
  "is_active": true,
  "is_default": false
}
```

**响应：** 200 OK

### 5. 删除存储后端

**DELETE** `/api/v1/storage-backends/{backend_id}`

删除指定的存储后端配置。

**注意：** 不能删除标记为默认的存储后端。

**响应：** 204 No Content

### 6. 设置默认存储后端

**POST** `/api/v1/storage-backends/{backend_id}/set-default`

将指定的存储后端设置为默认。

**响应：** 200 OK
```json
{
  "id": "uuid",
  "name": "S3存储1",
  "backend_type": "s3",
  "is_active": true,
  "is_default": true,
  "config": {...},
  ...
}
```

### 7. 测试存储后端连接

**POST** `/api/v1/storage-backends/{backend_id}/test`

测试存储后端的连接是否正常。

**响应：** 200 OK
```json
{
  "status": "success",
  "message": "本地存储测试成功"
}
```

或

```json
{
  "status": "success",
  "message": "S3存储连接测试成功"
}
```

**错误响应：** 500 Internal Server Error
```json
{
  "detail": "存储后端测试失败: 连接超时"
}
```

## 使用流程

### 1. 初始配置

首次运行时，系统会使用环境变量中的配置。你可以通过以下步骤迁移到数据库配置：

1. 创建一个新的存储后端配置（通过API）
2. 将其设置为默认
3. 系统会自动重新加载配置

### 2. 添加新的存储后端

```bash
# 示例：添加S3存储
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "阿里云OSS",
    "backend_type": "s3",
    "config": {
      "bucket_name": "my-bucket",
      "access_key": "YOUR_ACCESS_KEY",
      "secret_key": "YOUR_SECRET_KEY",
      "endpoint_url": "https://oss-cn-beijing.aliyuncs.com",
      "region_name": "oss-cn-beijing"
    },
    "description": "阿里云对象存储",
    "is_default": false
  }'
```

### 3. 测试连接

在切换到新的存储后端之前，建议先测试连接：

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends/{backend_id}/test" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 切换默认存储后端

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends/{backend_id}/set-default" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

系统会自动重新加载配置，所有新上传的文件将使用新的存储后端。

### 5. 删除不用的存储后端

```bash
curl -X DELETE "http://localhost:8000/api/v1/storage-backends/{backend_id}" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 数据库迁移

运行以下命令应用数据库迁移：

```bash
cd api
alembic upgrade head
```

或者重启应用，系统会自动运行迁移。

## 配置参数说明

### 本地存储配置 (LocalStorageConfig)

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| base_dir | string | 否 | "data/files" | 本地存储的基础目录 |

### S3存储配置 (S3StorageConfig)

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| bucket_name | string | 是 | - | S3桶名称 |
| access_key | string | 是 | - | 访问密钥ID |
| secret_key | string | 是 | - | 访问密钥 |
| endpoint_url | string | 否 | null | S3端点URL（用于MinIO等） |
| region_name | string | 否 | "us-east-1" | 区域名称 |
| public_url | string | 否 | null | 公共访问URL |

## 注意事项

1. **默认后端规则**：
   - 系统必须有且仅有一个默认存储后端
   - 设置新的默认后端时，会自动取消其他后端的默认标记
   - 默认后端会自动激活

2. **删除限制**：
   - 不能删除标记为默认的存储后端
   - 删除前需要先设置其他后端为默认

3. **配置热更新**：
   - 修改默认后端后，系统会自动重新加载配置
   - 无需重启应用

4. **配置优先级**：
   - 优先使用数据库中的配置
   - 如果数据库没有配置或加载失败，回退到环境变量

5. **安全性**：
   - 所有API接口都需要认证
   - 敏感配置（如密钥）存储在数据库中，建议加密
   - 建议使用HTTPS保护API通信

## 故障排查

### 问题：创建存储后端时报错"名称已存在"

**原因**：存储后端名称必须唯一。

**解决**：使用不同的名称或先删除/重命名现有的后端。

### 问题：测试S3连接失败

**原因**：可能是配置错误、网络问题或权限不足。

**解决**：
1. 检查access_key和secret_key是否正确
2. 检查bucket_name是否存在
3. 检查endpoint_url是否正确
4. 检查网络连接
5. 检查IAM权限

### 问题：切换默认后端后上传文件仍使用旧后端

**原因**：可能是缓存问题。

**解决**：重启应用或检查数据库中的is_default字段。

## 前端集成示例

```javascript
// 获取所有存储后端
const backends = await fetch('/api/v1/storage-backends', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
}).then(res => res.json());

// 创建新的存储后端
const newBackend = await fetch('/api/v1/storage-backends', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '本地存储',
    backend_type: 'local',
    config: {
      base_dir: 'data/files'
    },
    description: '本地文件存储',
    is_default: true
  })
}).then(res => res.json());

// 设置默认后端
await fetch(`/api/v1/storage-backends/${backendId}/set-default`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// 测试连接
const testResult = await fetch(`/api/v1/storage-backends/${backendId}/test`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  }
}).then(res => res.json());

// 删除后端
await fetch(`/api/v1/storage-backends/${backendId}`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```
