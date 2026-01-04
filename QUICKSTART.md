# 存储后端管理 - 快速开始

## 步骤 1: 运行数据库迁移

```bash
cd api
alembic upgrade head
```

输出示例：
```
INFO  [alembic.runtime.migration] Running upgrade 26278111e923 -> c8f9d5e23a1b, add_storage_backends_table
```

## 步骤 2: 启动应用

```bash
cd api
python -m uvicorn main:app --reload
```

或者：
```bash
cd api
fastapi dev main.py
```

## 步骤 3: 登录获取令牌

使用你的用户名和密码登录：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_USERNAME&password=YOUR_PASSWORD"
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

将token保存到环境变量：
```bash
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## 步骤 4: 创建第一个存储后端

### 方式A: 创建本地存储后端

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "本地存储",
    "backend_type": "local",
    "config": {
      "base_dir": "data/files"
    },
    "description": "本地文件存储",
    "is_default": true
  }'
```

### 方式B: 创建S3存储后端

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AWS S3",
    "backend_type": "s3",
    "config": {
      "bucket_name": "my-bucket",
      "access_key": "YOUR_ACCESS_KEY",
      "secret_key": "YOUR_SECRET_KEY",
      "endpoint_url": "https://s3.amazonaws.com",
      "region_name": "us-east-1"
    },
    "description": "AWS S3存储",
    "is_default": true
  }'
```

### MinIO示例

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MinIO本地",
    "backend_type": "s3",
    "config": {
      "bucket_name": "filetrace",
      "access_key": "minioadmin",
      "secret_key": "minioadmin",
      "endpoint_url": "http://localhost:9000",
      "region_name": "us-east-1"
    },
    "description": "本地MinIO存储",
    "is_default": true
  }'
```

### 阿里云OSS示例

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer $TOKEN" \
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
    "is_default": true
  }'
```

## 步骤 5: 测试存储后端

从步骤4的响应中获取backend_id，然后测试：

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends/{backend_id}/test" \
  -H "Authorization: Bearer $TOKEN"
```

成功响应：
```json
{
  "status": "success",
  "message": "本地存储测试成功"
}
```

## 步骤 6: 列出所有存储后端

```bash
curl -X GET "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer $TOKEN"
```

## 步骤 7: 上传文件测试

现在上传的文件将使用你配置的默认存储后端：

```bash
curl -X POST "http://localhost:8000/api/v1/files/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "files=@test.txt"
```

## 常用操作

### 切换默认存储后端

```bash
curl -X POST "http://localhost:8000/api/v1/storage-backends/{backend_id}/set-default" \
  -H "Authorization: Bearer $TOKEN"
```

### 更新存储后端配置

```bash
curl -X PUT "http://localhost:8000/api/v1/storage-backends/{backend_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "更新后的描述",
    "is_active": true
  }'
```

### 删除存储后端

```bash
curl -X DELETE "http://localhost:8000/api/v1/storage-backends/{backend_id}" \
  -H "Authorization: Bearer $TOKEN"
```

注意：不能删除默认后端，需要先设置其他后端为默认。

## 使用Python测试脚本

1. 修改 `test_storage_backend.py` 中的用户名密码：

```python
USERNAME = "your_username"
PASSWORD = "your_password"
```

2. 运行脚本：

```bash
python test_storage_backend.py
```

## 故障排查

### 问题1: "存储后端名称已存在"

**解决方案**：使用不同的名称或先删除现有的后端。

### 问题2: S3连接测试失败

**检查项**：
1. access_key和secret_key是否正确
2. bucket_name是否存在
3. endpoint_url是否正确
4. 网络连接是否正常
5. IAM权限是否足够

### 问题3: 迁移失败

```bash
# 检查迁移状态
cd api
alembic current

# 查看迁移历史
alembic history

# 如果需要，降级后重新升级
alembic downgrade -1
alembic upgrade head
```

## 下一步

- 查看完整文档: [STORAGE_BACKEND_MANAGEMENT.md](STORAGE_BACKEND_MANAGEMENT.md)
- 了解实现细节: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- 开发前端界面来管理存储后端
- 配置自动备份策略

## 环境变量（可选）

如果数据库没有配置，系统会回退到环境变量：

```bash
# 本地存储
export STORAGE_TYPE=local
export LOCAL_STORAGE_DIR=data/files

# 或 S3存储
export STORAGE_TYPE=s3
export S3_BUCKET_NAME=my-bucket
export S3_ACCESS_KEY=your_access_key
export S3_SECRET_KEY=your_secret_key
export S3_ENDPOINT_URL=https://s3.amazonaws.com
export S3_REGION_NAME=us-east-1
```

但推荐使用数据库配置，因为更灵活且支持动态切换。
