# ArchiveNote
## 新功能: 动态存储后端管理

现在支持通过API动态添加、删除和管理多个存储后端配置！

### 特性

- ✅ 支持本地存储和S3兼容存储（AWS S3, MinIO, 阿里云OSS等）
- ✅ 通过Web API动态添加/删除/切换存储后端
- ✅ 支持测试存储后端连接
- ✅ 热更新配置，无需重启服务
- ✅ 优先从数据库加载配置，回退到环境变量
- ✅ 完整的REST API接口

### 快速开始

1. **运行数据库迁移**
   ```bash
   cd api
   alembic upgrade head
   ```

2. **使用API管理存储后端**

   查看完整的API文档：[STORAGE_BACKEND_MANAGEMENT.md](STORAGE_BACKEND_MANAGEMENT.md)

3. **测试功能**
   ```bash
   # 修改test_storage_backend.py中的用户名和密码
   python test_storage_backend.py
   ```

### API端点

- `POST /api/v1/storage-backends` - 创建存储后端
- `GET /api/v1/storage-backends` - 列出所有后端
- `GET /api/v1/storage-backends/{id}` - 获取指定后端
- `PUT /api/v1/storage-backends/{id}` - 更新后端配置
- `DELETE /api/v1/storage-backends/{id}` - 删除后端
- `POST /api/v1/storage-backends/{id}/set-default` - 设置为默认
- `POST /api/v1/storage-backends/{id}/test` - 测试连接

### 示例

```bash
# 创建本地存储后端
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "本地存储",
    "backend_type": "local",
    "config": {
      "base_dir": "data/files"
    },
    "is_default": true
  }'

# 创建S3存储后端
curl -X POST "http://localhost:8000/api/v1/storage-backends" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AWS S3",
    "backend_type": "s3",
    "config": {
      "bucket_name": "my-bucket",
      "access_key": "YOUR_ACCESS_KEY",
      "secret_key": "YOUR_SECRET_KEY",
      "region_name": "us-east-1"
    },
    "is_default": false
  }'
```

查看更多详情：[STORAGE_BACKEND_MANAGEMENT.md](STORAGE_BACKEND_MANAGEMENT.md)

---
