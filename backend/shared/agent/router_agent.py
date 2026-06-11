"""
Router Agent Module
基于LangGraph构建的流式智能路由器智能体
负责用户意图识别和简单聊天
"""
from typing import Optional, Any, AsyncGenerator, Dict, List
from langchain.agents import create_agent, AgentState
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from .tools import BASIC_TOOLS
from .prompts import router_prompt
from .middleware import create_default_middleware


class RouterAgent:
    """
    Router智能体
    基于LangGraph构建的流式智能agent
    兼顾用户意图识别和简单聊天功能
    """
    
    def __init__(self, chat_model=None):
        self._agent = None
        self._chat_model = chat_model
    
    def _init_model(self):
        """初始化聊天模型"""
        if self._chat_model:
            return self._chat_model
        
        from ..utils.llm_client import llm_client
        llm_client._ensure_model_initialized()
        return llm_client._model
    
    def build(self) -> CompiledStateGraph:
        """
        构建Router智能体
        
        Returns:
            编译后的状态图
        """
        if self._agent is None:
            chat_model = self._init_model()
            
            middleware = create_default_middleware(
                agent_name="Router Agent",
                summarization_model=chat_model,
                max_tokens_before_summary=16384
            )
            
            self._agent = create_agent(
                chat_model,
                tools=BASIC_TOOLS,
                middleware=middleware,
                system_prompt=router_prompt
            )
        
        return self._agent
    
    def get_agent(self) -> Optional[CompiledStateGraph]:
        """获取已构建的智能体"""
        return self._agent
    
    async def run(
        self, 
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        运行智能体（非流式）
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Returns:
            智能体响应
        """
        agent = self.build()
        
        state: AgentState = {
            "messages": [
                HumanMessage(content=msg["content"]) 
                if msg["role"] == "user" 
                else AIMessage(content=msg["content"])
                for msg in messages
            ]
        }
        
        result = await agent.ainvoke(state, **kwargs)
        return self._format_response(result)
    
    async def stream(
        self, 
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式运行智能体
        
        Args:
            messages: 消息列表
            **kwargs: 其他参数
            
        Yields:
            流式响应事件
        """
        agent = self.build()
        
        state: AgentState = {
            "messages": [
                HumanMessage(content=msg["content"]) 
                if msg["role"] == "user" 
                else AIMessage(content=msg["content"])
                for msg in messages
            ]
        }
        
        async for event in agent.astream(state, **kwargs):
            formatted = self._format_stream_event(event)
            if formatted:
                yield formatted
    
    def _format_response(self, result: AgentState) -> Dict[str, Any]:
        """格式化智能体响应"""
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, AIMessage):
                return {
                    "content": last_message.content,
                    "tool_calls": last_message.tool_calls or [],
                    "role": "assistant"
                }
        return {"content": "", "role": "assistant"}
    
    def _format_stream_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """格式化流式事件"""
        if not isinstance(event, dict):
            return None
        
        for key, value in event.items():
            if isinstance(value, AIMessage):
                return {
                    "content": value.content,
                    "role": "assistant",
                    "tool_calls": value.tool_calls or []
                }
            elif isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if messages and isinstance(messages[-1], AIMessage):
                    last_msg = messages[-1]
                    return {
                        "content": last_msg.content,
                        "role": "assistant",
                        "tool_calls": last_msg.tool_calls or []
                    }
        
        return None


def create_router_agent(chat_model=None) -> RouterAgent:
    """创建Router智能体实例"""
    return RouterAgent(chat_model)
