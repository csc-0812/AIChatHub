"""
技能管理模块 - 数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class SkillParameter(BaseModel):
    name: str = Field(..., description="参数名称")
    type: str = Field("string", description="参数类型")
    description: str = Field("", description="参数描述")
    required: bool = Field(True, description="是否必填")
    default: Optional[str] = Field(None, description="默认值")


class SkillInfo(BaseModel):
    name: str = Field(..., description="技能名称")
    description: str = Field("", description="技能描述")
    version: str = Field("1.0.0", description="技能版本")
    category: str = Field("general", description="技能分类")
    enabled: bool = Field(True, description="是否启用")
    parameters: List[SkillParameter] = Field([], description="参数列表")
    system_prompt: str = Field("", description="系统提示词")
    user_prompt: str = Field("", description="用户提示词")


class CreateSkillRequest(BaseModel):
    name: str = Field(..., description="技能名称")
    description: str = Field("", description="技能描述")
    category: str = Field("general", description="技能分类")
    parameters: List[SkillParameter] = Field([], description="参数列表")
    system_prompt: str = Field("", description="系统提示词")
    user_prompt: str = Field("", description="用户提示词")
    script: str = Field("", description="Python脚本")


class UpdateSkillRequest(BaseModel):
    name: Optional[str] = Field(None, description="新技能名称")
    description: Optional[str] = Field(None, description="新描述")
    category: Optional[str] = Field(None, description="新分类")
    parameters: Optional[List[SkillParameter]] = Field(None, description="新参数列表")
    system_prompt: Optional[str] = Field(None, description="新系统提示词")
    user_prompt: Optional[str] = Field(None, description="新用户提示词")
    script: Optional[str] = Field(None, description="新脚本")


class SkillExecuteRequest(BaseModel):
    skill_name: str = Field(..., description="技能名称")
    parameters: dict = Field({}, description="技能参数")


class SkillExecuteResponse(BaseModel):
    success: bool = Field(..., description="是否成功")
    output: Optional[str] = Field(None, description="输出结果")
    error: Optional[str] = Field(None, description="错误信息")


class SkillListResponse(BaseModel):
    skills: List[SkillInfo] = Field(..., description="技能列表")
    total: int = Field(..., description="技能总数")