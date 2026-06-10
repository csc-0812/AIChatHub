"""
Agent Module
提供智能体功能，支持Router路由模式
"""
from .models import AgentRole, AgentConfig, AgentMessage, AgentResponse
from .base_agent import BaseAgent
from .router_agent import RouterAgent, create_router_agent
from .tools import BUILTIN_TOOLS, get_all_tools
from .prompts import router_prompt, DEFAULT_SYSTEM_PROMPT
from .middleware import AgentLoggingMiddleware, create_default_middleware

__all__ = [
    # 数据模型
    "AgentRole",
    "AgentConfig",
    "AgentMessage",
    "AgentResponse",
    # 智能体类
    "BaseAgent",
    "RouterAgent",
    # Router Agent 工厂函数
    "create_router_agent",
    # 工具
    "BUILTIN_TOOLS",
    "get_all_tools",
    # 提示词
    "router_prompt",
    "DEFAULT_SYSTEM_PROMPT",
    # 中间件
    "AgentLoggingMiddleware",
    "create_default_middleware",
]
