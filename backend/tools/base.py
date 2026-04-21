"""
工具基类
所有自定义工具都需要继承此类
"""
from typing import Dict, Any, Optional
from langchain_core.tools import BaseTool as LangChainBaseTool


class BaseTool(LangChainBaseTool):
    """
    工具基类
    
    自定义工具需要：
    1. 继承此类
    2. 设置 name 和 description 属性
    3. 实现 _run 和 _arun 方法
    """
    
    name: str = "base_tool"
    description: str = "基础工具"
    
    def _run(self, **kwargs) -> str:
        raise NotImplementedError("子类必须实现 _run 方法")
    
    async def _arun(self, **kwargs) -> str:
        return self._run(**kwargs)