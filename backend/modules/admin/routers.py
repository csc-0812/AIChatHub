"""
管理员路由
提供用户管理和系统配置API
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from modules.auth.models import User, UserRole
from modules.auth.routers import get_current_admin, get_current_super_admin
from .models import (
    UserListResponse, UpdateUserRoleRequest, UpdateUserRoleResponse,
    ToggleUserResponse, ResetPasswordRequest, ResetPasswordResponse,
    DeleteUserResponse, LLMConfigUpdate, LLMConfigResponse,
    SystemStatusResponse, CreateUserRequest, CreateUserResponse,
    UpdateUserRequest, UpdateUserResponse
)
from .services import admin_service

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", response_model=dict)
async def list_users(
    current_user: User = Depends(get_current_admin)
):
    """获取所有用户列表（管理员权限）"""
    result = admin_service.get_all_users()
    return result


@router.post("/users", response_model=CreateUserResponse)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(get_current_admin)
):
    """
    管理员创建新用户
    管理员可以创建普通用户，超级管理员可以创建任何角色的用户
    """
    # 普通管理员只能创建普通用户
    if current_user.role == UserRole.ADMIN and request.role != UserRole.USER:
        raise HTTPException(status_code=403, detail="普通管理员只能创建普通用户")
    
    try:
        result = admin_service.create_user(
            username=request.username,
            password=request.password,
            email=request.email,
            full_name=request.full_name,
            role=request.role
        )
        return CreateUserResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{username}", response_model=UpdateUserResponse)
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user: User = Depends(get_current_admin)
):
    """更新用户信息（管理员权限）"""
    # 检查目标用户
    target_user = admin_service.auth_service.get_user(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 普通管理员不能修改管理员信息
    if current_user.role == UserRole.ADMIN and target_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="权限不足")
    
    success = admin_service.update_user_info(
        username=username,
        email=request.email,
        full_name=request.full_name
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UpdateUserResponse(
        username=username,
        email=request.email,
        full_name=request.full_name
    )


@router.put("/users/{username}/role", response_model=UpdateUserRoleResponse)
async def update_user_role(
    username: str,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_super_admin)
):
    """
    更新用户角色（超级管理员权限）
    只有超级管理员可以修改用户角色
    """
    # 不能修改自己的角色
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    
    # 不能修改其他管理员的角色（除非是超级管理员修改普通管理员）
    target_user = admin_service.auth_service.get_user(username)
    if target_user and target_user.role == UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="不能修改超级管理员的角色")
    
    success = admin_service.update_user_role(username, request.role)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UpdateUserRoleResponse(username=username, role=request.role)


@router.post("/users/{username}/toggle", response_model=ToggleUserResponse)
async def toggle_user(
    username: str,
    current_user: User = Depends(get_current_admin)
):
    """
    切换用户禁用状态（管理员权限）
    管理员不能禁用其他管理员或超级管理员
    """
    # 不能禁用自己
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    
    # 检查目标用户角色
    target_user = admin_service.auth_service.get_user(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 普通管理员不能禁用管理员
    if current_user.role == UserRole.ADMIN and target_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="权限不足，无法禁用管理员账号")
    
    new_status = admin_service.toggle_user_disabled(username)
    if new_status is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return ToggleUserResponse(
        username=username,
        disabled=new_status,
        message="用户已禁用" if new_status else "用户已启用"
    )


@router.post("/users/{username}/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    username: str,
    request: ResetPasswordRequest,
    current_user: User = Depends(get_current_admin)
):
    """重置用户密码（管理员权限）"""
    success = admin_service.reset_user_password(username, request.new_password)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return ResetPasswordResponse(username=username)


@router.delete("/users/{username}", response_model=DeleteUserResponse)
async def delete_user(
    username: str,
    current_user: User = Depends(get_current_super_admin)
):
    """
    删除用户（超级管理员权限）
    不能删除管理员账号
    """
    # 不能删除自己
    if username == current_user.username:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    
    # 检查目标用户角色
    target_user = admin_service.auth_service.get_user(username)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能删除管理员
    if target_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="不能删除管理员账号，请先降级为普通用户")
    
    success = admin_service.delete_user(username)
    if not success:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return DeleteUserResponse(username=username)


@router.get("/system/status", response_model=dict)
async def system_status(
    current_user: User = Depends(get_current_admin)
):
    """获取系统状态统计（管理员权限）"""
    status = admin_service.get_system_status()
    return status


@router.get("/config/llm", response_model=dict)
async def get_llm_config(
    current_user: User = Depends(get_current_admin)
):
    """获取LLM配置（管理员权限，API密钥已隐藏）"""
    config = admin_service.get_llm_config()
    return {
        **config,
        "message": "配置获取成功"
    }


@router.put("/config/llm", response_model=dict)
async def update_llm_config(
    config_update: LLMConfigUpdate,
    current_user: User = Depends(get_current_admin)
):
    """
    更新LLM配置（管理员权限）
    注意：此操作只更新内存中的配置，服务重启后会恢复为配置文件中的值
    """
    update_data = config_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供要更新的配置项")
    
    success = admin_service.update_llm_config(update_data)
    if not success:
        raise HTTPException(status_code=500, detail="配置更新失败")
    
    return {
        "message": "配置更新成功（内存中，重启后恢复）",
        "updated_fields": list(update_data.keys())
    }


@router.get("/dashboard", response_model=dict)
async def admin_dashboard(
    current_user: User = Depends(get_current_admin)
):
    """管理员仪表盘数据"""
    system_status = admin_service.get_system_status()
    users_info = admin_service.get_all_users()
    
    return {
        "welcome": f"欢迎回来，{current_user.username}",
        "your_role": current_user.role.value,
        "system_status": system_status,
        "user_statistics": {
            "total": users_info["total"],
            "active": users_info["active"],
            "disabled": users_info["disabled"],
            "admins": users_info["admins"]
        }
    }



