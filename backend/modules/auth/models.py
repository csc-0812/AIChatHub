from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    """用户角色"""
    USER = "user"           # 普通用户
    ADMIN = "admin"         # 管理员
    SUPER_ADMIN = "super_admin"  # 超级管理员


class User(BaseModel):
    """用户模型（内部使用，不做密码字段限制，兼容管理后台等渠道）"""
    username: str
    password: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False
    role: UserRole = UserRole.USER  # 默认普通用户


class RegisterRequest(BaseModel):
    """注册请求模型（前端注册专用，有密码强度和验证码校验）"""
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=18, description="密码长度6-18位")
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    captcha_id: str = Field(..., description="验证码ID")
    captcha_text: str = Field(..., description="验证码输入")


class UserInDB(User):
    """数据库中的用户模型"""
    hashed_password: str


class UserResponse(BaseModel):
    """用户响应模型（不包含密码）"""
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    disabled: bool = False
    role: UserRole = UserRole.USER


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str
    username: str
    role: UserRole


class CaptchaResponse(BaseModel):
    """验证码响应模型"""
    captcha_id: str
    captcha_text: str  # 验证码明文，前端展示用
    message: str = "验证码获取成功"
