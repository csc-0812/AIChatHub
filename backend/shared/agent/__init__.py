"""
Agent Module - 计划一体化平台
提供智能体功能，支持Router路由模式
"""
from .models import AgentRole, AgentConfig, AgentMessage, AgentResponse
from .base_agent import BaseAgent
from .router_agent import RouterAgent, create_router_agent
from .tools import BASIC_TOOLS, get_all_tools
from .tools import (
    PlanReportTool,
    PlanSimulationTool,
    RootCauseTool,
    REPORT_TYPE_MAP,
    SIMULATION_TYPE_MAP,
    RCA_TYPE_MAP,
)
from .prompts import router_prompt
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
    # 工具类
    "BASIC_TOOLS",
    "get_all_tools",
    "PlanReportTool",
    "PlanSimulationTool",
    "RootCauseTool",
    # 类型映射
    "REPORT_TYPE_MAP",
    "SIMULATION_TYPE_MAP",
    "RCA_TYPE_MAP",
    # 提示词
    "router_prompt",
    "DEFAULT_SYSTEM_PROMPT",
    # 中间件
    "AgentLoggingMiddleware",
    "create_default_middleware",
]
