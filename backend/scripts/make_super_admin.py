#!/usr/bin/env python3
"""
创建或升级超级管理员
用法:
  python make_super_admin.py <用户名> [密码]
  python make_super_admin.py <用户名>            # 交互式输入密码（新用户时）
  python make_super_admin.py                    # 交互式输入用户名和密码

示例:
  python make_super_admin.py admin Admin123!
"""

import sys
import os
import getpass

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.redis_client import redis_client
from shared.utils.auth_utils import get_password_hash


def make_super_admin(username: str, password: str = None):
    """创建超级管理员或升级已有用户"""
    user_key = f"user:{username}"

    if redis_client.exists(user_key):
        # 用户已存在，直接升级角色
        redis_client.hset(user_key, "role", "super_admin")
        role = redis_client.hget(user_key, "role")
        print(f"[成功] 用户 '{username}' 已升级为: {role}")
        return True

    # 用户不存在，需要创建新用户
    if not password:
        print(f"用户 '{username}' 不存在，需要创建新用户。")
        password = getpass.getpass("请输入密码: ")
        password_confirm = getpass.getpass("请再次输入密码: ")
        if password != password_confirm:
            print("[错误] 两次输入的密码不一致")
            return False
        if not password:
            print("[错误] 密码不能为空")
            return False

    # 创建用户数据（与 auth/services.py 中 create_user 字段一致）
    user_data = {
        "username": username,
        "email": "",
        "full_name": "",
        "disabled": "False",
        "role": "super_admin",
        "hashed_password": get_password_hash(password),
    }

    for key, value in user_data.items():
        redis_client.hset(user_key, key, value)

    # 验证创建结果
    created_role = redis_client.hget(user_key, "role")
    print(f"[成功] 超级管理员 '{username}' 已创建，角色: {created_role}")
    return True


if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 2:
        # python make_super_admin.py admin Admin123!
        username, password = args[0], args[1]
    elif len(args) == 1:
        # python make_super_admin.py admin
        username, password = args[0], None
    else:
        # 交互式模式
        username = input("请输入用户名: ").strip()
        password_input = getpass.getpass("请输入密码（可选，已有用户可留空）: ").strip()
        password = password_input if password_input else None

    if not username:
        print("[错误] 用户名不能为空")
        sys.exit(1)

    success = make_super_admin(username, password)
    sys.exit(0 if success else 1)
