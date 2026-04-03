"""
模型配置数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class LLMModelConfig(BaseModel):
    """LLM模型配置"""
    id: Optional[str] = None
    name: str  # 显示名称
    provider: str  # 提供商：openai, azure, anthropic等
    model: str  # 模型名称
    base_url: str
    api_key: str
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1, le=8192)
    is_active: bool = False  # 是否启用
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LLMModelCreateRequest(BaseModel):
    """创建LLM模型配置请求"""
    name: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1)
    base_url: str = Field(..., min_length=1)
    api_key: str = Field(..., min_length=1)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    description: Optional[str] = None


class LLMModelUpdateRequest(BaseModel):
    """更新LLM模型配置请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1)
    base_url: Optional[str] = Field(None, min_length=1)
    api_key: Optional[str] = Field(None, min_length=1)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    description: Optional[str] = None


class LLMModelResponse(BaseModel):
    """LLM模型配置响应（隐藏API密钥）"""
    id: str
    name: str
    provider: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int
    is_active: bool
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LLMModelListResponse(BaseModel):
    """LLM模型列表响应"""
    models: List[LLMModelResponse]
    active_model_id: Optional[str] = None


class SetActiveModelRequest(BaseModel):
    """设置活跃模型请求"""
    model_id: str
