#!/usr/bin/env python3
"""
存储后端管理测试脚本
演示如何使用API管理存储后端
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "your_username"
PASSWORD = "your_password"

# 获取访问令牌
def get_token():
    """登录并获取访问令牌"""
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={
            "username": USERNAME,
            "password": PASSWORD
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]


def list_backends(token):
    """列出所有存储后端"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/storage-backends",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def create_local_backend(token, name="本地存储1", base_dir="data/files", is_default=True):
    """创建本地存储后端"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "backend_type": "local",
        "config": {
            "base_dir": base_dir
        },
        "description": "本地文件存储",
        "is_default": is_default
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/storage-backends",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()


def create_s3_backend(token, name, bucket_name, access_key, secret_key,
                     endpoint_url=None, region_name="us-east-1", is_default=False):
    """创建S3存储后端"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": name,
        "backend_type": "s3",
        "config": {
            "bucket_name": bucket_name,
            "access_key": access_key,
            "secret_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": region_name
        },
        "description": "S3对象存储",
        "is_default": is_default
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/storage-backends",
        headers=headers,
        json=data
    )
    response.raise_for_status()
    return response.json()


def test_backend(token, backend_id):
    """测试存储后端连接"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/storage-backends/{backend_id}/test",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def set_default_backend(token, backend_id):
    """设置默认存储后端"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/v1/storage-backends/{backend_id}/set-default",
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def update_backend(token, backend_id, **kwargs):
    """更新存储后端"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.put(
        f"{BASE_URL}/api/v1/storage-backends/{backend_id}",
        headers=headers,
        json=kwargs
    )
    response.raise_for_status()
    return response.json()


def delete_backend(token, backend_id):
    """删除存储后端"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        f"{BASE_URL}/api/v1/storage-backends/{backend_id}",
        headers=headers
    )
    response.raise_for_status()
    print(f"后端 {backend_id} 已删除")


def main():
    """主函数 - 演示完整流程"""
    print("=== 存储后端管理测试 ===\n")

    # 1. 登录获取令牌
    print("1. 登录获取访问令牌...")
    try:
        token = get_token()
        print("✓ 登录成功\n")
    except Exception as e:
        print(f"✗ 登录失败: {e}")
        return

    # 2. 列出现有后端
    print("2. 列出现有存储后端...")
    try:
        backends = list_backends(token)
        print(f"✓ 找到 {len(backends)} 个存储后端")
        for b in backends:
            print(f"  - {b['name']} ({b['backend_type']}) - 默认: {b['is_default']}, 激活: {b['is_active']}")
        print()
    except Exception as e:
        print(f"✗ 列出失败: {e}\n")

    # 3. 创建本地存储后端
    print("3. 创建本地存储后端...")
    try:
        local_backend = create_local_backend(token, "测试本地存储", "data/files_test", True)
        print(f"✓ 创建成功: {local_backend['name']} (ID: {local_backend['id']})\n")
        local_id = local_backend['id']
    except Exception as e:
        print(f"✗ 创建失败: {e}\n")
        return

    # 4. 测试本地存储连接
    print("4. 测试本地存储连接...")
    try:
        test_result = test_backend(token, local_id)
        print(f"✓ 测试结果: {test_result['message']}\n")
    except Exception as e:
        print(f"✗ 测试失败: {e}\n")

    # 5. 创建S3存储后端（示例 - 需要真实凭证）
    print("5. 创建S3存储后端（如果需要）...")
    try:
        # 取消注释并填入真实的S3配置
        # s3_backend = create_s3_backend(
        #     token,
        #     name="测试S3存储",
        #     bucket_name="my-bucket",
        #     access_key="YOUR_ACCESS_KEY",
        #     secret_key="YOUR_SECRET_KEY",
        #     endpoint_url="https://s3.amazonaws.com",
        #     is_default=False
        # )
        # print(f"✓ 创建成功: {s3_backend['name']} (ID: {s3_backend['id']})\n")
        # s3_id = s3_backend['id']
        print("⊘ 跳过 S3 后端创建（需要真实凭证）\n")
    except Exception as e:
        print(f"✗ 创建失败: {e}\n")

    # 6. 更新后端配置
    print("6. 更新后端配置...")
    try:
        updated = update_backend(
            token,
            local_id,
            description="更新后的描述信息"
        )
        print(f"✓ 更新成功: {updated['description']}\n")
    except Exception as e:
        print(f"✗ 更新失败: {e}\n")

    # 7. 最终列出所有后端
    print("7. 最终列出所有存储后端...")
    try:
        backends = list_backends(token)
        print(f"✓ 共有 {len(backends)} 个存储后端:")
        for b in backends:
            default_mark = "⭐" if b['is_default'] else "  "
            active_mark = "✓" if b['is_active'] else "✗"
            print(f"  {default_mark} [{active_mark}] {b['name']} ({b['backend_type']})")
            print(f"      描述: {b.get('description', 'N/A')}")
            print(f"      ID: {b['id']}")
        print()
    except Exception as e:
        print(f"✗ 列出失败: {e}\n")

    # 8. 清理（可选）
    # print("8. 清理测试后端...")
    # try:
    #     delete_backend(token, local_id)
    #     print("✓ 清理完成\n")
    # except Exception as e:
    #     print(f"✗ 清理失败: {e}\n")

    print("=== 测试完成 ===")


if __name__ == "__main__":
    main()
