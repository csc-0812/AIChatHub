"""
团队智能体
管理多个智能体，支持协作模式
"""
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from .models import AgentRole, AgentConfig, AgentMessage, AgentResponse, TeamConfig
from .base_agent import BaseAgent


class TeamAgent:
    """
    团队智能体 - 管理多个智能体协作
    """
    
    def __init__(self, team_config: Optional[TeamConfig] = None):
        self.team_config = team_config or TeamConfig()
        self.agents: Dict[str, BaseAgent] = {}
        self.message_history: List[AgentMessage] = []
        self.session_id: Optional[str] = None
        
        # 初始化默认智能体
        self._initialize_default_agents()
    
    def _initialize_default_agents(self):
        """初始化默认智能体"""
        if not self.team_config.agents:
            # 创建默认协调者
            default_config = AgentConfig(
                role=AgentRole.COORDINATOR,
                name="Coordinator",
                description="负责协调和分配任务"
            )
            self.add_agent(default_config)
        else:
            for config in self.team_config.agents:
                self.add_agent(config)
    
    def add_agent(self, config: AgentConfig) -> str:
        """
        添加智能体到团队
        
        Args:
            config: 智能体配置
            
        Returns:
            智能体ID
        """
        agent_id = str(uuid.uuid4())
        self.agents[agent_id] = BaseAgent(config)
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)
    
    def get_primary_agent(self) -> BaseAgent:
        """获取主智能体（第一个或协调者）"""
        # 优先返回协调者
        for agent in self.agents.values():
            if agent.config.role == AgentRole.COORDINATOR:
                return agent
        # 否则返回第一个
        return next(iter(self.agents.values()))
    
    async def chat(
        self, 
        message: str, 
        agent_id: Optional[str] = None
    ) -> AgentResponse:
        """
        单轮对话
        
        Args:
            message: 用户消息
            agent_id: 指定智能体ID（可选）
            
        Returns:
            AgentResponse
        """
        # 选择智能体
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            agent = self.get_primary_agent()
        
        # 处理消息
        response = await agent.process(message, self.message_history)
        
        # 保存到历史
        self.message_history.append(AgentMessage(
            role="user",
            content=message
        ))
        self.message_history.append(AgentMessage(
            role="assistant",
            content=response.content,
            agent_name=response.agent_name
        ))
        
        return response
    
    async def stream_chat(
        self, 
        message: str, 
        agent_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式对话
        
        Args:
            message: 用户消息
            agent_id: 指定智能体ID（可选）
            
        Yields:
            流式事件数据
        """
        # 选择智能体
        if agent_id and agent_id in self.agents:
            agent = self.agents[agent_id]
        else:
            agent = self.get_primary_agent()
        
        # 保存用户消息到历史
        self.message_history.append(AgentMessage(
            role="user",
            content=message
        ))
        
        # 收集完整响应
        full_content = ""
        agent_name = agent.config.name
        
        async for event in agent.stream_process(message, self.message_history[:-1]):
            if event["event"] == "done":
                full_content = event["data"].get("answer", "")
            yield event
        
        # 保存助手消息到历史
        if full_content:
            self.message_history.append(AgentMessage(
                role="assistant",
                content=full_content,
                agent_name=agent_name
            ))
    
    def get_history(self) -> List[AgentMessage]:
        """获取对话历史"""
        return self.message_history.copy()
    
    def clear_history(self):
        """清空对话历史"""
        self.message_history.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "team_config": self.team_config.model_dump(),
            "agents": [
                {
                    "id": agent_id,
                    "name": agent.config.name,
                    "role": agent.config.role.value,
                    "description": agent.config.description
                }
                for agent_id, agent in self.agents.items()
            ],
            "message_count": len(self.message_history)
        }
