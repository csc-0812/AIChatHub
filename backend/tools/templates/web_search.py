"""
搜索工具模板
用于查询网络信息
"""
from typing import Optional
from langchain_core.tools import tool


@tool("web_search", description="用于搜索网络信息，获取最新数据和知识")
def web_search(query: str) -> str:
    """
    搜索工具 - 查询网络信息
    
    Args:
        query: 搜索查询词
        
    Returns:
        搜索结果字符串
    """
    return f"搜索结果: 关于 '{query}' 的信息（模拟搜索结果）"