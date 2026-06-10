"""
Agent 数据模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """智能体角色类型"""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    WRITER = "writer"
    REVIEWER = "reviewer"
    CUSTOM = "custom"


class AgentConfig(BaseModel):
    """智能体配置"""
    role: AgentRole = AgentRole.COORDINATOR
    name: str = "Assistant"
    description: str = ""
    system_prompt: str = """
你是一个 helpful 的AI助手，请友好地回答用户的问题。
"""
    temperature: float = 0.7
    max_tokens: int = 2048
    enable_thinking: bool = True
    context_window: int = 10
    tools: List[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    """智能体消息"""
    role: str
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
    metadata: Dict[str, Any] = Field(default_factory=dict)
