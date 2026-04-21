"""
工具模块
提供 Agent 可用的工具定义和注册机制
"""
from .registry import register_tool, get_tool, get_all_tools, get_tool_instances
from .base import BaseTool
from .templates.web_search import web_search
from .templates.calculator import calculator

register_tool(web_search)
register_tool(calculator)

__all__ = [
    "register_tool",
    "get_tool",
    "get_all_tools",
    "get_tool_instances",
    "BaseTool",
    "web_search",
    "calculator"
]