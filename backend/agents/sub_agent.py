"""
子智能体模板
作为路由智能体的子节点，处理特定领域的任务
"""
from typing import List, Dict, Any, Optional, AsyncGenerator

from .base_agent import BaseAgent
from .models import AgentConfig, AgentResponse
from tools import get_tool_instances


class SubAgent(BaseAgent):
    """
    子智能体模板
    
    自定义子智能体可以继承此类并扩展功能。
    """
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._tools = []
        self._agent = None
        
        self._initialize_tools()
        self._initialize_langchain_agent()
    
    def _initialize_tools(self):
        """初始化工具"""
        if self.config.tools:
            self._tools = get_tool_instances(self.config.tools)
    
    def _initialize_langchain_agent(self):
        """初始化 LangChain Agent（如果有工具）"""
        if not self._tools:
            self._agent = None
            return
        
        from shared.utils.llm_client import llm_client
        
        llm_client._ensure_model_initialized()
        llm = llm_client._model
        
        if not llm:
            self._agent = None
            return
        
        from langchain.agents import create_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self._agent = create_agent(llm=llm, tools=self._tools, prompt=prompt)
    
    async def process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """处理消息"""
        if self._agent and context:
            try:
                chat_history = context[-self.config.context_window:]
                langchain_history = self._convert_dict_messages(chat_history)
                
                response = await self._agent.ainvoke({
                    "input": message,
                    "chat_history": langchain_history
                })
                answer = response.get("output", response.get("content", ""))
                return AgentResponse(
                    content=answer,
                    thinking=None,
                    agent_name=self.config.name,
                    role=self.config.role
                )
            except Exception:
                pass
        
        return await self._direct_answer(message, context)
    
    async def stream_process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理消息"""
        yield {
            "event": "start",
            "data": {"agent": self.config.name, "role": self.config.role.value}
        }
        
        full_content = ""
        async for chunk in self._stream_direct_answer(message, context):
            full_content += chunk
            yield {
                "event": "answer_chunk",
                "data": {"chunk": chunk}
            }
        
        yield {
            "event": "done",
            "data": {
                "thinking": None,
                "answer": full_content,
                "agent": self.config.name,
                "role": self.config.role.value
            }
        }
    
    def get_tools(self) -> List[str]:
        """获取工具列表"""
        return [getattr(t, 'name', t.__name__) for t in self._tools]
    
    def add_tool(self, tool_name: str):
        """添加工具"""
        if tool_name not in self.config.tools:
            self.config.tools.append(tool_name)
            self._initialize_tools()
            self._initialize_langchain_agent()
    
    def remove_tool(self, tool_name: str):
        """移除工具"""
        if tool_name in self.config.tools:
            self.config.tools.remove(tool_name)
            self._initialize_tools()
            self._initialize_langchain_agent()
    
    def has_tools(self) -> bool:
        """是否有工具"""
        return len(self._tools) > 0