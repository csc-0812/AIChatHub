"""
工具注册表
提供工具注册和查询功能
"""
from typing import List, Dict, Any


_tools_registry: Dict[str, Any] = {}


def register_tool(tool: Any) -> Any:
    """注册工具到全局注册表"""
    name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
    if name:
        _tools_registry[name] = tool
    return tool


def get_tool(tool_name: str) -> Any:
    """获取已注册的工具"""
    return _tools_registry.get(tool_name)


def get_all_tools() -> List[Any]:
    """获取所有已注册的工具"""
    return list(_tools_registry.values())


def get_tool_instances(tool_names: List[str]) -> List[Any]:
    """根据工具名称获取工具实例列表"""
    instances = []
    for name in tool_names:
        tool = get_tool(name)
        if tool:
            if isinstance(tool, type):
                instances.append(tool())
            else:
                instances.append(tool)
    return instances