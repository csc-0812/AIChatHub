"""
子智能体模板
作为路由智能体的子节点，处理特定领域的任务
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from .models import AgentConfig, AgentMessage, AgentResponse
from tools import get_tool_instances


class SubAgent:
    """
    子智能体模板
    
    自定义子智能体可以继承此类并扩展功能。
    
    使用示例：
    ```python
    class MyAgent(SubAgent):
        def __init__(self):
            config = AgentConfig(
                name="MyAgent",
                role=AgentRole.CUSTOM,
                description="自定义智能体",
                tools=["web_search"]
            )
            super().__init__(config)
    ```
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._tools = []
        self._agent = None
        
        self._initialize_tools()
    
    def _initialize_tools(self):
        """初始化工具"""
        if self.config.tools:
            self._tools = get_tool_instances(self.config.tools)
    
    def _initialize_langchain_agent(self):
        """初始化 LangChain Agent"""
        if not self._tools:
            self._agent = None
            return
        
        from shared.utils.llm_client import llm_client
        
        llm_client._ensure_model_initialized()
        llm = llm_client._model
        
        if not llm:
            return
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        from langchain.agents import create_agent
        self._agent = create_agent(llm=llm, tools=self._tools, prompt=prompt)
    
    def _convert_messages(self, messages: List[AgentMessage]) -> List[Any]:
        """转换消息格式"""
        langchain_messages = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            else:
                langchain_messages.append(HumanMessage(content=msg.content))
        return langchain_messages
    
    async def process(self, message: str, context: Optional[List[AgentMessage]] = None) -> AgentResponse:
        """处理消息"""
        chat_history = context[:self.config.context_window] if context else []
        
        if self._agent:
            try:
                response = await self._agent.ainvoke({
                    "input": message,
                    "chat_history": self._convert_messages(chat_history)
                })
                answer = response.get("output", response.get("content", ""))
                return AgentResponse(
                    content=answer,
                    thinking=None,
                    agent_name=self.config.name,
                    role=self.config.role
                )
            except Exception as e:
                pass
        
        return await self._direct_answer(message, chat_history)
    
    async def _direct_answer(self, message: str, chat_history: List[AgentMessage]) -> AgentResponse:
        """直接调用LLM回答"""
        from shared.utils.llm_client import llm_client
        
        messages = [{"role": "system", "content": self.config.system_prompt}]
        for msg in chat_history:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})
        
        response = await llm_client.achat(messages)
        return AgentResponse(
            content=response,
            thinking=None,
            agent_name=self.config.name,
            role=self.config.role
        )
    
    async def stream_process(self, message: str, context: Optional[List[AgentMessage]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理消息"""
        yield {
            "event": "start",
            "data": {"agent": self.config.name, "role": self.config.role.value}
        }
        
        from shared.utils.llm_client import llm_client
        
        messages = [{"role": "system", "content": self.config.system_prompt}]
        if context:
            for msg in context[-self.config.context_window:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": message})
        
        full_content = ""
        async for chunk in llm_client.stream_chat(messages):
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