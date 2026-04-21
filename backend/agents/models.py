"""
Agent 数据模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """智能体角色类型"""
    ROUTER = "router"          # 路由智能体，负责任务分发
    RESEARCHER = "researcher"  # 研究者
    ANALYZER = "analyzer"      # 分析者
    WRITER = "writer"          # 写作者
    CUSTOM = "custom"          # 自定义角色


class RouteDecision(BaseModel):
    """路由决策结果"""
    target_type: str  # tool / agent / skill / direct
    target_name: str  # 目标名称
    confidence: float  # 置信度 0-1
    reasoning: str  # 决策理由
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """智能体配置"""
    role: AgentRole = AgentRole.ROUTER
    name: str = "Assistant"
    description: str = ""
    system_prompt: str = "你是一个 helpful 的AI助手。"
    temperature: float = 0.7
    max_tokens: int = 2048
    context_window: int = 10
    tools: List[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    """智能体消息"""
    role: str  # user/assistant/system
    content: str
    agent_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """智能体响应"""
    content: str
    thinking: Optional[str] = None
    agent_name: str
    role: AgentRole
    timestamp: datetime = Field(default_factory=datetime.now)