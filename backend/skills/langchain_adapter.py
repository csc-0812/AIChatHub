"""
OpenClaw Skill 到 LangChain Tool 的适配器 - 基于 OpenClaw SDK

将 OpenClaw Skill 转换为 LangChain Tool，
使 LangChain Agent 能够调用 OpenClaw 技能。
"""
import os
import asyncio
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from .executor import execute_skill
from .loader import load_skills_from_directory, get_skill


class SkillToolArgs(BaseModel):
    """技能调用参数模型"""
    skill_name: str = Field(..., description="技能名称")
    parameters: Dict[str, Any] = Field(default={}, description="技能参数")


class OpenClawSkillTool(BaseTool):
    """
    OpenClaw Skill 适配为 LangChain Tool
    
    将 OpenClaw 的 SKILL.md 格式技能转换为 LangChain Tool，
    支持同步和异步调用。
    """
    
    name: str = "openclaw_skill"
    description: str = "执行 OpenClaw 技能，支持各种自定义功能"
    args_schema: Type[BaseModel] = SkillToolArgs
    
    def _run(
        self,
        skill_name: str,
        parameters: Dict[str, Any] = {},
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """同步执行 OpenClaw 技能"""
        loop = asyncio.get_event_loop()
        result = loop.run_in_executor(None, self._execute_sync, skill_name, parameters)
        return result
    
    async def _arun(
        self,
        skill_name: str,
        parameters: Dict[str, Any] = {},
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步执行 OpenClaw 技能"""
        return await self._execute(skill_name, parameters)
    
    def _execute_sync(self, skill_name: str, parameters: Dict[str, Any]) -> str:
        """同步执行（用于线程池）"""
        import asyncio
        return asyncio.run(self._execute(skill_name, parameters))
    
    async def _execute(self, skill_name: str, parameters: Dict[str, Any]) -> str:
        """执行技能"""
        result = await execute_skill(skill_name, **parameters)
        if result.success:
            return str(result.output)
        else:
            return f"技能执行失败: {result.error}"


class IndividualSkillTool(BaseTool):
    """
    将单个 OpenClaw Skill 封装为独立的 LangChain Tool
    
    每个技能成为一个独立的 Tool，便于 Agent 进行工具选择。
    """
    
    skill_name: str
    
    def __init__(self, skill):
        skill_name = getattr(skill, 'name', 'unknown')
        description = getattr(skill, 'description', '')
        
        super().__init__(
            name=skill_name.lower().replace(' ', '_'),
            description=description,
            args_schema=self._create_args_schema(skill)
        )
        self.skill_name = skill_name
    
    def _create_args_schema(self, skill) -> Type[BaseModel]:
        """根据技能参数动态创建 args_schema"""
        fields = {}
        if hasattr(skill, 'parameters'):
            for param in skill.parameters:
                param_name = param.get("name")
                param_type = param.get("type", "string")
                param_desc = param.get("description", "")
                
                py_type = str
                if param_type.lower() == "int":
                    py_type = int
                elif param_type.lower() == "float":
                    py_type = float
                elif param_type.lower() == "bool":
                    py_type = bool
                
                fields[param_name] = (py_type, Field(description=param_desc))
        
        if not fields:
            fields["input"] = (str, Field(description="输入内容"))
        
        return type(f"{self.skill_name}Args", (BaseModel,), fields)
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """同步执行技能"""
        loop = asyncio.get_event_loop()
        result = loop.run_in_executor(None, self._execute_sync, kwargs)
        return result
    
    async def _arun(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """异步执行技能"""
        return await self._execute(kwargs)
    
    def _execute_sync(self, parameters: Dict[str, Any]) -> str:
        """同步执行"""
        import asyncio
        return asyncio.run(self._execute(parameters))
    
    async def _execute(self, parameters: Dict[str, Any]) -> str:
        """执行技能"""
        result = await execute_skill(self.skill_name, **parameters)
        if result.success:
            return str(result.output)
        else:
            return f"技能执行失败: {result.error}"


def load_skills_as_tools(skills_dir: Optional[str] = None) -> List[BaseTool]:
    """
    从目录加载所有技能并转换为 LangChain Tool
    
    Args:
        skills_dir: 技能目录路径，默认为 skills/skills_dir
    
    Returns:
        LangChain Tool 列表
    """
    if skills_dir is None:
        skills_dir = os.path.join(os.path.dirname(__file__), "skills_dir")
        skills_dir = os.path.abspath(skills_dir)
    
    skills = load_skills_from_directory(skills_dir)
    tools = []
    
    for skill in skills:
        enabled = getattr(skill, 'enabled', True)
        skill_name = getattr(skill, 'name', '')
        if enabled and skill_name:
            tools.append(IndividualSkillTool(skill))
    
    return tools


def get_skill_tool(skill_name: str) -> Optional[IndividualSkillTool]:
    """
    获取指定技能的 LangChain Tool
    
    Args:
        skill_name: 技能名称
    
    Returns:
        IndividualSkillTool 实例，如果技能不存在返回 None
    """
    skill = get_skill(skill_name)
    if skill:
        return IndividualSkillTool(skill)
    return None