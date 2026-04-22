"""
Agent 到 LangChain Tool 的适配器

将子 Agent 封装为 LangChain Tool，使 Router Agent 能够将子 Agent 作为工具调用。
"""
import asyncio
from typing import Any, Dict, List, Optional, Type

from langchain.tools import BaseTool
from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from .models import AgentResponse
from .sub_agent import SubAgent


class AgentToolArgs(BaseModel):
    """Agent 调用参数模型"""
    agent_name: str = Field(..., description="子智能体名称")
    question: str = Field(..., description="要询问子智能体的问题")


class SubAgentTool(BaseTool):
    """
    将多个子 Agent 封装为统一的 LangChain Tool
    
    使 Router Agent 能够通过单一工具调用不同的子智能体。
    通过 agent_name 参数指定要调用的子智能体。
    """
    
    name: str = "sub_agent"
    description: str = "调用子智能体处理特定领域任务。参数: agent_name (子智能体名称), question (问题)"
    args_schema: Type[BaseModel] = AgentToolArgs
    
    def __init__(self):
        super().__init__()
        self._agents: Dict[str, SubAgent] = {}
    
    def register_agent(self, agent: SubAgent):
        """注册子智能体"""
        self._agents[agent.config.name] = agent
    
    def unregister_agent(self, agent_name: str):
        """注销子智能体"""
        if agent_name in self._agents:
            del self._agents[agent_name]
    
    def get_registered_agents(self) -> List[str]:
        """获取已注册的智能体列表"""
        return list(self._agents.keys())
    
    def _run(
        self,
        agent_name: str,
        question: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """同步调用子智能体"""
        if agent_name not in self._agents:
            return f"智能体 '{agent_name}' 未找到"
        
        agent = self._agents[agent_name]
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(self._call_agent(agent, question))
        loop.close()
        return result
    
    async def _arun(
        self,
        agent_name: str,
        question: str,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """异步调用子智能体"""
        if agent_name not in self._agents:
            return f"智能体 '{agent_name}' 未找到"
        
        agent = self._agents[agent_name]
        return await self._call_agent(agent, question)
    
    async def _call_agent(self, agent: SubAgent, question: str) -> str:
        """调用子智能体"""
        response = await agent.process(question)
        return response.content