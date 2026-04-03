#!/usr/bin/env python3
"""
将指定用户设置为超级管理员
用法: python make_super_admin.py <用户名>
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.redis_client import redis_client


def make_super_admin(username: str):
    """将用户设置为超级管理员"""
    user_key = f"user:{username}"
    
    # 检查用户是否存在
    if not redis_client.exists(user_key):
        print(f"错误: 用户 '{username}' 不存在")
        return False
    
    # 修改角色
    redis_client.hset(user_key, "role", "super_admin")
    
    # 验证
    role = redis_client.hget(user_key, "role")
    print(f"成功! 用户 '{username}' 的角色已更改为: {role}")
    return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python make_super_admin.py <用户名>")
        print("示例: python make_super_admin.py admin")
        sys.exit(1)
    
    username = sys.argv[1]
    make_super_admin(username)
