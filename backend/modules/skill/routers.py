"""
技能管理模块 - API 路由
"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from .models import (
    SkillInfo, CreateSkillRequest, UpdateSkillRequest, 
    SkillExecuteRequest, SkillExecuteResponse, SkillListResponse
)
from .services import skill_service


router = APIRouter(
    prefix="/skills",
    tags=["技能管理"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=SkillListResponse, summary="获取技能列表")
async def get_skills():
    return skill_service.load_skills()


@router.get("/{name}", response_model=Optional[SkillInfo], summary="获取技能详情")
async def get_skill(name: str):
    skill = skill_service.get_skill_info(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能 '{name}' 不存在")
    return skill


@router.post("/", response_model=SkillInfo, status_code=status.HTTP_201_CREATED, summary="创建技能")
async def create_skill(request: CreateSkillRequest):
    return skill_service.create_skill(request)


@router.put("/{name}", response_model=Optional[SkillInfo], summary="更新技能")
async def update_skill(name: str, request: UpdateSkillRequest):
    skill = skill_service.update_skill(name, request)
    if not skill:
        raise HTTPException(status_code=404, detail=f"技能 '{name}' 不存在")
    return skill


@router.delete("/{name}", summary="删除技能")
async def delete_skill(name: str):
    success = skill_service.delete_skill(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"技能 '{name}' 不存在")
    return {"message": f"技能 '{name}' 删除成功"}


@router.patch("/{name}/toggle", summary="切换技能状态")
async def toggle_skill_status(name: str):
    success = skill_service.toggle_skill(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"技能 '{name}' 不存在")
    return {"message": f"技能 '{name}' 状态已切换"}


@router.post("/template/{name}", summary="创建技能模板")
async def create_skill_template(name: str):
    success = skill_service.create_skill_template(name)
    if not success:
        raise HTTPException(status_code=500, detail=f"创建技能模板失败")
    return {"message": f"技能模板 '{name}' 创建成功"}


@router.post("/execute", response_model=SkillExecuteResponse, summary="执行技能")
async def execute_skill(request: SkillExecuteRequest):
    return await skill_service.execute_skill(request.skill_name, request.parameters)