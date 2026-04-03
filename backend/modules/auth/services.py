from typing import Optional, List
from .models import User, UserInDB, UserRole, UserResponse
from shared.utils.redis_client import redis_client
from shared.utils.auth_utils import verify_password, get_password_hash, create_access_token, generate_session_id
from shared.utils.logger import auth_logger
import json


class AuthService:
    def __init__(self):
        self.redis_client = redis_client
    
    def get_user(self, username: str) -> Optional[UserInDB]:
        """从Redis获取用户信息"""
        user_data = self.redis_client.hgetall(f"user:{username}")
        if not user_data:
            return None
        
        return UserInDB(
            username=user_data.get("username"),
            password="",  # 不返回密码
            email=user_data.get("email"),
            full_name=user_data.get("full_name"),
            disabled=user_data.get("disabled", "false").lower() == "true",
            role=UserRole(user_data.get("role", "user")),
            hashed_password=user_data.get("hashed_password")
        )
    
    def get_user_response(self, username: str) -> Optional[UserResponse]:
        """获取用户响应信息（不包含敏感数据）"""
        user = self.get_user(username)
        if not user:
            return None
        return UserResponse(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            disabled=user.disabled,
            role=user.role
        )
    
    def create_user(self, user: User) -> UserInDB:
        """创建用户并存储到Redis"""
        hashed_password = get_password_hash(user.password)
        user_data = {
            "username": user.username,
            "email": user.email or "",
            "full_name": user.full_name or "",
            "disabled": str(user.disabled),
            "role": user.role.value,
            "hashed_password": hashed_password
        }
        
        # 存储用户信息到Redis
        for key, value in user_data.items():
            if value is not None:
                self.redis_client.hset(f"user:{user.username}", key, value)
        
        return UserInDB(
            **user.model_dump(),
            hashed_password=hashed_password
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """认证用户"""
        user = self.get_user(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        if user.disabled:
            return None
        return user

    def check_user_disabled(self, username: str) -> Optional[bool]:
        """检查用户是否被禁用"""
        user = self.get_user(username)
        if not user:
            return None
        return user.disabled

    def login(self, username: str, password: str) -> tuple:
        """用户登录，返回访问令牌和用户信息"""
        user = self.get_user(username)
        if not user:
            raise ValueError("用户名或密码错误")
        if not verify_password(password, user.hashed_password):
            raise ValueError("用户名或密码错误")
        if user.disabled:
            raise ValueError("用户已被禁用，请联系管理员")

        # 生成新的会话ID，实现同用户登录挤出
        session_id = generate_session_id()
        session_key = f"user_session:{username}"

        # 存储用户当前会话ID到Redis，设置过期时间（与token过期时间一致）
        self.redis_client.set(session_key, session_id, expire=30*60)

        auth_logger.info(f"用户登录: {username}, 会话ID: {session_id}")

        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value, "session_id": session_id}
        )
        return access_token, user.role

    def validate_session(self, username: str, session_id: str) -> bool:
        """验证用户会话是否有效（检查是否被挤出）"""
        session_key = f"user_session:{username}"
        stored_session = self.redis_client.get(session_key)
        auth_logger.debug(f"验证会话: 用户={username}, 传入session_id={session_id}, 存储session_id={stored_session}")
        if stored_session is None:
            # 会话不存在，可能是已过期
            auth_logger.warning(f"会话不存在或已过期: 用户={username}")
            return False
        is_valid = stored_session == session_id
        if not is_valid:
            auth_logger.warning(f"会话验证失败(可能已被挤出): 用户={username}")
        return is_valid

    def logout(self, username: str) -> bool:
        """用户退出登录，清除会话"""
        self.redis_client.delete(f"user_session:{username}")
        return True
    
    def get_all_users(self) -> List[UserResponse]:
        """获取所有用户列表"""
        # 从Redis获取所有用户键
        user_keys = self.redis_client.client.keys("user:*")
        users = []
        for key in user_keys:
            username = key.decode().split(":")[1] if isinstance(key, bytes) else key.split(":")[1]
            user = self.get_user_response(username)
            if user:
                users.append(user)
        return users
    
    def update_user_role(self, username: str, role: UserRole) -> bool:
        """更新用户角色"""
        user_key = f"user:{username}"
        if not self.redis_client.exists(user_key):
            return False
        self.redis_client.hset(user_key, "role", role.value)
        return True
    
    def toggle_user_disabled(self, username: str) -> Optional[bool]:
        """切换用户禁用状态"""
        user = self.get_user(username)
        if not user:
            return None
        new_status = not user.disabled
        self.redis_client.hset(f"user:{username}", "disabled", str(new_status))
        return new_status
    
    def reset_user_password(self, username: str, new_password: str) -> bool:
        """重置用户密码"""
        user_key = f"user:{username}"
        if not self.redis_client.exists(user_key):
            return False
        hashed_password = get_password_hash(new_password)
        self.redis_client.hset(user_key, "hashed_password", hashed_password)
        return True
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        user_key = f"user:{username}"
        if not self.redis_client.exists(user_key):
            return False
        self.redis_client.delete(user_key)
        return True
    
    def is_admin(self, username: str) -> bool:
        """检查用户是否为管理员"""
        user = self.get_user(username)
        if not user:
            return False
        return user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]
    
    def is_super_admin(self, username: str) -> bool:
        """检查用户是否为超级管理员"""
        user = self.get_user(username)
        if not user:
            return False
        return user.role == UserRole.SUPER_ADMIN


# 创建认证服务实例
auth_service = AuthService()
