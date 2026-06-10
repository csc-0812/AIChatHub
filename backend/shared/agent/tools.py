"""
Agent Tools Module
提供智能体可用的工具定义
"""
from typing import List
from langchain_core.tools import BaseTool


BUILTIN_TOOLS: List[BaseTool] = []


def get_all_tools() -> List[BaseTool]:
    """获取所有可用工具"""
    return BUILTIN_TOOLS
