from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .models import LoginRequest, LoginResponse, User, Token, UserRole
from .services import auth_service
from shared.utils.auth_utils import decode_token
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """用户登录"""
    try:
        access_token, role = auth_service.login(login_data.username, login_data.password)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            username=login_data.username,
            role=role
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=dict)
async def register(user: User):
    """用户注册"""
    # 检查用户是否已存在
    existing_user = auth_service.get_user(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建新用户（默认角色为普通用户）
    created_user = auth_service.create_user(user)
    return {
        "username": created_user.username,
        "email": created_user.email,
        "full_name": created_user.full_name,
        "role": created_user.role.value,
        "message": "注册成功"
    }


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    role_str: str = payload.get("role", "user")
    session_id: str = payload.get("session_id")
    if username is None:
        raise credentials_exception

    user = auth_service.get_user(username)
    if user is None:
        raise credentials_exception

    # 检查用户是否被禁用
    if user.disabled:
        raise HTTPException(
            status_code=403,
            detail="用户已被禁用，请联系管理员"
        )

    # 验证会话是否有效（检查是否被挤出）
    if not session_id:
        # 没有session_id的token是旧版token，要求重新登录
        raise HTTPException(
            status_code=401,
            detail="登录已过期，请重新登录"
        )
    if not auth_service.validate_session(username, session_id):
        raise HTTPException(
            status_code=401,
            detail="账号已在其他地方登录"
        )

    # 更新用户角色（从token中获取最新角色）
    user.role = UserRole(role_str)

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """获取当前管理员用户"""
    if not auth_service.is_admin(current_user.username):
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )
    return current_user


async def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级管理员用户"""
    if not auth_service.is_super_admin(current_user.username):
        raise HTTPException(
            status_code=403,
            detail="需要超级管理员权限"
        )
    return current_user


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "disabled": current_user.disabled,
        "role": current_user.role.value
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """用户退出登录"""
    auth_service.logout(current_user.username)
    return {"message": "退出登录成功"}
