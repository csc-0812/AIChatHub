"""
Agent 基类
提供所有 Agent 通用的基础功能和接口定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .models import AgentConfig, AgentMessage, AgentResponse, AgentRole


class BaseAgent(ABC):
    """
    Agent 基类
    
    提供所有 Agent 的通用功能：
    - 消息格式转换
    - 直接调用 LLM 回答
    - 上下文管理（从外部传入）
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
    
    def _convert_messages(self, messages: List[AgentMessage]) -> List[Any]:
        """转换消息格式为 LangChain 格式"""
        langchain_messages = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            else:
                langchain_messages.append(HumanMessage(content=msg.content))
        return langchain_messages
    
    def _convert_dict_messages(self, messages: List[Dict[str, str]]) -> List[Any]:
        """转换字典格式消息为 LangChain 格式"""
        langchain_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                langchain_messages.append(HumanMessage(content=content))
        return langchain_messages
    
    async def _direct_answer(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """直接调用 LLM 回答（无工具调用时的降级方案）"""
        from shared.utils.llm_client import llm_client
        
        messages = [{"role": "system", "content": self.config.system_prompt}]
        
        if context:
            history = context[-self.config.context_window:]
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        response = await llm_client.achat(messages)
        return AgentResponse(
            content=response,
            thinking=None,
            agent_name=self.config.name,
            role=self.config.role
        )
    
    async def _stream_direct_answer(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[str, None]:
        """流式直接调用 LLM 回答"""
        from shared.utils.llm_client import llm_client
        
        messages = [{"role": "system", "content": self.config.system_prompt}]
        
        if context:
            history = context[-self.config.context_window:]
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        async for chunk in llm_client.stream_chat(messages):
            yield chunk
    
    @abstractmethod
    async def process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """处理消息（子类必须实现）"""
        pass
    
    @abstractmethod
    async def stream_process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理消息（子类必须实现）"""
        pass
    
    @property
    def name(self) -> str:
        """获取 Agent 名称"""
        return self.config.name
    
    @property
    def role(self) -> AgentRole:
        """获取 Agent 角色"""
        return self.config.role
    
    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "description": self.config.description,
            "tools": self.config.tools
        }