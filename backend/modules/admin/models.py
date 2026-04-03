"""
管理员模块数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from modules.auth.models import UserRole


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[dict]
    total: int


class UpdateUserRoleRequest(BaseModel):
    """更新用户角色请求"""
    role: UserRole


class UpdateUserRoleResponse(BaseModel):
    """更新用户角色响应"""
    username: str
    role: UserRole
    message: str = "角色更新成功"


class ToggleUserResponse(BaseModel):
    """切换用户状态响应"""
    username: str
    disabled: bool
    message: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    new_password: str = Field(..., min_length=6)


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    username: str
    message: str = "密码重置成功"


class DeleteUserResponse(BaseModel):
    """删除用户响应"""
    username: str
    message: str = "用户删除成功"


class LLMConfigUpdate(BaseModel):
    """LLM配置更新"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    model: str
    base_url: str
    temperature: float
    max_tokens: int
    message: str = "配置获取成功"


class SystemStatusResponse(BaseModel):
    """系统状态响应"""
    total_users: int
    active_users: int
    disabled_users: int
    admin_count: int
    total_sessions: int
    timestamp: datetime


class CreateUserRequest(BaseModel):
    """创建用户请求（管理员）"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER


class CreateUserResponse(BaseModel):
    """创建用户响应"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: UserRole
    message: str = "用户创建成功"


class UpdateUserRequest(BaseModel):
    """更新用户信息请求"""
    email: Optional[str] = None
    full_name: Optional[str] = None


class UpdateUserResponse(BaseModel):
    """更新用户信息响应"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    message: str = "用户信息更新成功"



