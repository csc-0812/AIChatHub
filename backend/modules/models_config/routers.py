"""
模型配置路由
提供LLM模型配置管理API
"""
from fastapi import APIRouter, Depends, HTTPException

from modules.auth.models import User
from modules.auth.routers import get_current_admin
from .models import (
    LLMModelCreateRequest, LLMModelUpdateRequest
)
from .services import models_config_service

router = APIRouter(prefix="/models-config", tags=["模型配置"])


@router.get("/llm-models", response_model=dict)
async def list_llm_models(
    current_user: User = Depends(get_current_admin)
):
    """获取所有LLM模型配置（管理员权限）"""
    result = models_config_service.get_all_models()
    return result


@router.post("/llm-models", response_model=dict)
async def create_llm_model(
    request: LLMModelCreateRequest,
    current_user: User = Depends(get_current_admin)
):
    """创建新的LLM模型配置（管理员权限）"""
    try:
        model = models_config_service.create_model(request.model_dump())
        return {
            "id": model.id,
            "name": model.name,
            "provider": model.provider,
            "model": model.model,
            "base_url": model.base_url,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
            "is_active": model.is_active,
            "description": model.description,
            "message": "模型配置创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put("/llm-models/{model_id}", response_model=dict)
async def update_llm_model(
    model_id: str,
    request: LLMModelUpdateRequest,
    current_user: User = Depends(get_current_admin)
):
    """更新LLM模型配置（管理员权限）"""
    update_data = request.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有提供要更新的配置项")
    
    model = models_config_service.update_model(model_id, update_data)
    if not model:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return {
        "id": model.id,
        "name": model.name,
        "provider": model.provider,
        "model": model.model,
        "base_url": model.base_url,
        "temperature": model.temperature,
        "max_tokens": model.max_tokens,
        "is_active": model.is_active,
        "description": model.description,
        "message": "模型配置更新成功"
    }


@router.delete("/llm-models/{model_id}", response_model=dict)
async def delete_llm_model(
    model_id: str,
    current_user: User = Depends(get_current_admin)
):
    """删除LLM模型配置（管理员权限）"""
    success = models_config_service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return {"message": "模型配置删除成功"}


@router.post("/llm-models/{model_id}/activate", response_model=dict)
async def activate_llm_model(
    model_id: str,
    current_user: User = Depends(get_current_admin)
):
    """设置启用的LLM模型（管理员权限）"""
    success = models_config_service.set_active_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    
    return {"message": "模型启用成功", "active_model_id": model_id}


@router.get("/llm-models/active", response_model=dict)
async def get_active_llm_model(
    current_user: User = Depends(get_current_admin)
):
    """获取当前启用的LLM模型（管理员权限）"""
    model = models_config_service.get_active_model()
    if not model:
        raise HTTPException(status_code=404, detail="没有启用的模型配置")

    return {
        "id": model.id,
        "name": model.name,
        "provider": model.provider,
        "model": model.model,
        "base_url": model.base_url,
        "temperature": model.temperature,
        "max_tokens": model.max_tokens,
        "is_active": model.is_active,
        "description": model.description
    }


@router.post("/llm-models/reset", response_model=dict)
async def reset_llm_models(
    current_user: User = Depends(get_current_admin)
):
    """重置模型配置，从配置文件重新初始化（管理员权限）"""
    try:
        # 清除Redis中的模型配置
        models_config_service.redis.delete(models_config_service.models_key)
        models_config_service.redis.delete(models_config_service.active_model_key)

        # 从配置文件重新初始化
        default_model = models_config_service._init_default_model_from_config()

        if default_model:
            return {
                "message": "模型配置已重置",
                "model": {
                    "id": default_model.id,
                    "name": default_model.name,
                    "provider": default_model.provider,
                    "model": default_model.model
                }
            }
        else:
            return {"message": "模型配置已重置，但未找到配置文件中的默认模型"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")
