"""
管理员服务
提供用户管理和系统配置功能
"""
from typing import Dict, Any, Optional
from datetime import datetime

from modules.auth.services import auth_service
from modules.auth.models import UserRole, User
from shared.utils.config_loader import config_loader
from shared.utils.redis_client import redis_client
from shared.utils.logger import admin_logger


class AdminService:
    """管理员服务"""
    
    def __init__(self):
        self.auth_service = auth_service
        self.redis = redis_client
    
    def get_all_users(self) -> Dict[str, Any]:
        """获取所有用户信息"""
        users = self.auth_service.get_all_users()
        total = len(users)
        active = sum(1 for u in users if not u.disabled)
        disabled = sum(1 for u in users if u.disabled)
        admins = sum(1 for u in users if u.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        
        return {
            "users": [
                {
                    "username": u.username,
                    "email": u.email,
                    "full_name": u.full_name,
                    "disabled": u.disabled,
                    "role": u.role.value
                }
                for u in users
            ],
            "total": total,
            "active": active,
            "disabled": disabled,
            "admins": admins
        }
    
    def update_user_role(self, username: str, role: UserRole) -> bool:
        """更新用户角色"""
        return self.auth_service.update_user_role(username, role)
    
    def toggle_user_disabled(self, username: str) -> Optional[bool]:
        """切换用户禁用状态"""
        return self.auth_service.toggle_user_disabled(username)
    
    def reset_user_password(self, username: str, new_password: str) -> bool:
        """重置用户密码"""
        return self.auth_service.reset_user_password(username, new_password)
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        return self.auth_service.delete_user(username)
    
    def create_user(self, username: str, password: str, email: str = None, full_name: str = None, role: UserRole = UserRole.USER) -> dict:
        """管理员创建新用户"""
        # 检查用户是否已存在
        existing_user = self.auth_service.get_user(username)
        if existing_user:
            raise ValueError("用户名已存在")
        
        # 创建新用户
        new_user = User(
            username=username,
            password=password,
            email=email,
            full_name=full_name,
            role=role,
            disabled=False
        )
        
        created_user = self.auth_service.create_user(new_user)
        
        return {
            "username": created_user.username,
            "email": created_user.email,
            "full_name": created_user.full_name,
            "role": created_user.role.value
        }
    
    def update_user_info(self, username: str, email: str = None, full_name: str = None) -> bool:
        """更新用户信息（邮箱、全名）"""
        user_key = f"user:{username}"
        if not self.redis.exists(user_key):
            return False
        
        if email is not None:
            self.redis.hset(user_key, "email", email)
        if full_name is not None:
            self.redis.hset(user_key, "full_name", full_name)
        
        return True
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态统计"""
        users = self.auth_service.get_all_users()
        total_users = len(users)
        active_users = sum(1 for u in users if not u.disabled)
        disabled_users = sum(1 for u in users if u.disabled)
        admin_count = sum(1 for u in users if u.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        
        # 获取会话数量
        session_keys = self.redis.client.keys("chat:session:*")
        total_sessions = len(session_keys)
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "disabled_users": disabled_users,
            "admin_count": admin_count,
            "total_sessions": total_sessions,
            "timestamp": datetime.now()
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取当前LLM配置（隐藏API密钥）"""
        llm_config = config_loader.get_llm_config()
        openai_config = llm_config.get("openai", {})
        
        return {
            "model": openai_config.get("model", "gpt-3.5-turbo"),
            "base_url": openai_config.get("base_url", ""),
            "temperature": openai_config.get("temperature", 0.7),
            "max_tokens": openai_config.get("max_tokens", 2048),
            "request_timeout": llm_config.get("request_timeout", 60),
            "max_retries": llm_config.get("max_retries", 3)
        }
    
    def update_llm_config(self, config_update: Dict[str, Any]) -> bool:
        """
        更新LLM配置
        注意：这里只更新内存中的配置，重启后会恢复
        如需持久化，需要修改config.yaml文件
        """
        try:
            # 获取当前配置
            llm_config = config_loader.get_llm_config()
            openai_config = llm_config.get("openai", {})
            
            # 更新配置
            if "model" in config_update:
                openai_config["model"] = config_update["model"]
            if "base_url" in config_update:
                openai_config["base_url"] = config_update["base_url"]
            if "temperature" in config_update:
                openai_config["temperature"] = config_update["temperature"]
            if "max_tokens" in config_update:
                openai_config["max_tokens"] = config_update["max_tokens"]
            if "api_key" in config_update:
                openai_config["api_key"] = config_update["api_key"]
            if "request_timeout" in config_update:
                llm_config["request_timeout"] = config_update["request_timeout"]
            if "max_retries" in config_update:
                llm_config["max_retries"] = config_update["max_retries"]
            
            llm_config["openai"] = openai_config
            config_loader._config["llm"] = llm_config
            
            return True
        except Exception as e:
            admin_logger.error(f"更新LLM配置失败: {e}")
            return False


    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        config = config_loader.get_config()
        
        return {
            "site_name": config.get("app", {}).get("site_name", "AI Chat Hub"),
            "max_context_length": config.get("app", {}).get("max_context_length", 10),
            "default_temperature": config.get("llm", {}).get("openai", {}).get("temperature", 0.7),
            "max_tokens": config.get("llm", {}).get("openai", {}).get("max_tokens", 2048),
            "enable_streaming": config.get("app", {}).get("enable_streaming", True),
            "session_expire_days": config.get("app", {}).get("session_expire_days", 7)
        }
    
    def update_system_config(self, config_data: Dict[str, Any]) -> bool:
        """更新系统配置"""
        try:
            config = config_loader.get_config()
            
            if "site_name" in config_data:
                if "app" not in config:
                    config["app"] = {}
                config["app"]["site_name"] = config_data["site_name"]
            
            if "max_context_length" in config_data:
                if "app" not in config:
                    config["app"] = {}
                config["app"]["max_context_length"] = config_data["max_context_length"]
            
            if "default_temperature" in config_data:
                if "llm" not in config:
                    config["llm"] = {}
                if "openai" not in config["llm"]:
                    config["llm"]["openai"] = {}
                config["llm"]["openai"]["temperature"] = config_data["default_temperature"]
            
            if "max_tokens" in config_data:
                if "llm" not in config:
                    config["llm"] = {}
                if "openai" not in config["llm"]:
                    config["llm"]["openai"] = {}
                config["llm"]["openai"]["max_tokens"] = config_data["max_tokens"]
            
            if "enable_streaming" in config_data:
                if "app" not in config:
                    config["app"] = {}
                config["app"]["enable_streaming"] = config_data["enable_streaming"]
            
            if "session_expire_days" in config_data:
                if "app" not in config:
                    config["app"] = {}
                config["app"]["session_expire_days"] = config_data["session_expire_days"]
            
            config_loader._config = config
            return True
        except Exception as e:
            admin_logger.error(f"更新系统配置失败: {e}")
            return False


# 创建管理员服务实例
admin_service = AdminService()
