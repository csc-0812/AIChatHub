"""
路由智能体 - 基于 LangChain Agent

作为核心路由中心，负责问题解析和任务分发。
支持将子 Agent 和 OpenClaw Skill 作为工具调用。

架构设计：
- 使用 LangChain create_agent 作为核心执行引擎
- 将子 Agent、工具、技能统一作为 Tool 注册
- LLM 自动决定调用哪个工具/Agent/技能

支持的工具类型：
1. 原生工具（calculator, web_search 等）
2. 子智能体（Researcher, Analyzer 等）
3. OpenClaw 技能（通过技能目录加载）
"""
import uuid
import os
from typing import List, Dict, Any, Optional, AsyncGenerator

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from .base_agent import BaseAgent
from .models import AgentConfig, AgentResponse, AgentRole
from .sub_agent import SubAgent
from .langchain_adapter import SubAgentTool
from tools import get_all_tools, get_tool_instances
from skills import load_skills_as_tools


class RouterAgent(BaseAgent):
    """
    路由智能体 - 基于 LangChain Agent
    
    核心职责：
    - 解析用户问题
    - 选择最合适的工具/子agent/技能
    - 执行并返回结果
    
    扩展机制：
    - 支持动态注册子agent
    - 支持动态添加工具
    - 支持加载 OpenClaw 技能
    
    上下文管理：
    - 使用外部传入的 context（来自 ChatSession）
    - 不再维护内部的 message_history
    """
    
    def __init__(self):
        config = AgentConfig(
            role=AgentRole.ROUTER,
            name="Router",
            description="路由智能体，负责任务分发",
            system_prompt="你是一个 helpful 的AI助手。",
            context_window=10
        )
        super().__init__(config)
        
        self.sub_agents: Dict[str, SubAgent] = {}
        self.session_id: str = str(uuid.uuid4())
        
        self._native_tools: List[Any] = []
        self._skill_tools: List[Any] = []
        
        self._agent = None
        self._sub_agent_tool: SubAgentTool = SubAgentTool()
        
        self._load_resources()
        self._initialize_default_sub_agents()
        self._build_agent()
    
    def _load_resources(self):
        """加载可用资源：工具和技能"""
        self._native_tools = get_tool_instances(get_all_tools())
        
        skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills", "skills_dir")
        skills_dir = os.path.abspath(skills_dir)
        self._skill_tools = load_skills_as_tools(skills_dir)
    
    def _initialize_default_sub_agents(self):
        """初始化默认子智能体"""
        researcher_config = AgentConfig(
            role=AgentRole.RESEARCHER,
            name="Researcher",
            description="负责信息收集和研究任务，擅长网络搜索和信息整理",
            tools=["web_search"],
            system_prompt="你是一个专业的研究者，擅长收集和整理信息。"
        )
        self.register_sub_agent(researcher_config)
        
        analyzer_config = AgentConfig(
            role=AgentRole.ANALYZER,
            name="Analyzer",
            description="负责数据分析和计算任务，擅长数学计算和数据分析",
            tools=["calculator"],
            system_prompt="你是一个专业的数据分析专家，擅长数学计算和数据分析。"
        )
        self.register_sub_agent(analyzer_config)
    
    @property
    def _all_tools(self) -> List[Any]:
        """获取所有工具（原生工具 + 技能工具 + 子agent工具）"""
        return [self._sub_agent_tool] + self._native_tools + self._skill_tools
    
    def _build_tool_descriptions(self) -> str:
        """构建工具描述字符串（用于系统提示）"""
        tool_descriptions = []
        
        for tool in self._all_tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', 'unknown')
            tool_desc = getattr(tool, 'description', '')
            tool_descriptions.append(f"- {tool_name}: {tool_desc}")
        
        registered_agents = self._sub_agent_tool.get_registered_agents()
        if registered_agents:
            tool_descriptions.append(f"\n可用子智能体: {', '.join(registered_agents)}")
        
        return "\n".join(tool_descriptions)
    
    def _build_agent(self):
        """构建 Agent"""
        from shared.utils.llm_client import llm_client
        
        llm_client._ensure_model_initialized()
        llm = llm_client._model
        
        if not llm:
            self._agent = None
            return
        
        system_prompt = """
你是一个智能路由助手，负责根据用户的问题选择最合适的工具或智能体来处理。

## 你的任务：
分析用户的问题，选择最合适的工具/智能体/技能来解决问题。

## 可用工具：
{tool_descriptions}

## 输出格式：
请直接根据工具的格式要求输出，不要添加额外的解释。

## 注意：
1. 如果需要实时信息，使用 web_search 工具
2. 如果需要计算，使用 calculator 工具
3. 如果需要专业知识，调用 sub_agent 工具并指定子智能体名称（如 Researcher, Analyzer）
4. 如果需要特定功能，调用对应的技能
5. 如果不需要工具，可以直接回答用户的问题
"""
        
        formatted_prompt = system_prompt.format(tool_descriptions=self._build_tool_descriptions())
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", formatted_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self._agent = create_agent(llm=llm, tools=self._all_tools, prompt=prompt)
    
    def register_sub_agent(self, config: AgentConfig) -> str:
        """注册子智能体（作为工具使用）"""
        agent_id = str(uuid.uuid4())
        sub_agent = SubAgent(config)
        self.sub_agents[agent_id] = sub_agent
        self._sub_agent_tool.register_agent(sub_agent)
        
        self._build_agent()
        return agent_id
    
    def unregister_sub_agent(self, agent_id: str) -> bool:
        """注销子智能体"""
        if agent_id in self.sub_agents:
            agent = self.sub_agents[agent_id]
            self._sub_agent_tool.unregister_agent(agent.config.name)
            del self.sub_agents[agent_id]
            self._build_agent()
            return True
        return False
    
    def get_sub_agent_by_name(self, name: str) -> Optional[SubAgent]:
        """根据名称获取子智能体"""
        for agent in self.sub_agents.values():
            if agent.config.name == name:
                return agent
        return None
    
    def add_tool(self, tool):
        """添加自定义工具"""
        self._native_tools.append(tool)
        self._build_agent()
    
    def remove_tool(self, tool_name: str):
        """移除工具"""
        self._native_tools = [
            t for t in self._native_tools 
            if getattr(t, 'name', '') != tool_name
        ]
        self._build_agent()
    
    async def process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """处理消息（使用外部传入的上下文）"""
        if self._agent and context:
            try:
                chat_history = context[-self.config.context_window:]
                langchain_history = self._convert_dict_messages(chat_history)
                
                response = await self._agent.ainvoke({
                    "input": message,
                    "chat_history": langchain_history
                })
                
                answer = response.get("output", response.get("content", str(response)))
                
                return AgentResponse(
                    content=answer,
                    thinking="通过 LangChain Agent 处理",
                    agent_name=self.config.name,
                    role=self.config.role
                )
            except Exception:
                pass
        
        return await self._direct_answer(message, context)
    
    async def chat(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AgentResponse:
        """处理用户消息（兼容旧接口，需要传入上下文）"""
        return await self.process(message, context)
    
    async def stream_process(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理消息（使用外部传入的上下文）"""
        yield {
            "event": "start",
            "data": {"agent": self.config.name, "role": self.config.role.value}
        }
        
        if self._agent and context:
            try:
                chat_history = context[:-1] if context else []
                langchain_history = self._convert_dict_messages(chat_history)
                
                final_answer = ""
                async for chunk in self._agent.astream({
                    "input": message,
                    "chat_history": langchain_history
                }):
                    if isinstance(chunk, dict) and "output" in chunk:
                        final_answer = chunk["output"]
                        yield {
                            "event": "answer_chunk",
                            "data": {"chunk": chunk["output"]}
                        }
                    elif isinstance(chunk, dict) and "agent_action" in chunk:
                        action = chunk["agent_action"]
                        yield {
                            "event": "tool_call",
                            "data": {
                                "tool": action.tool,
                                "parameters": action.tool_input
                            }
                        }
                    else:
                        chunk_str = str(chunk)
                        final_answer += chunk_str
                        yield {
                            "event": "answer_chunk",
                            "data": {"chunk": chunk_str}
                        }
                
                yield {
                    "event": "done",
                    "data": {
                        "thinking": "通过 LangChain Agent 处理",
                        "answer": final_answer,
                        "agent": self.config.name,
                        "role": self.config.role.value
                    }
                }
                return
            except Exception:
                pass
        
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
                "thinking": "直接回答",
                "answer": full_content,
                "agent": self.config.name,
                "role": self.config.role.value
            }
        }
    
    async def stream_chat(self, message: str, context: Optional[List[Dict[str, str]]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理用户消息（兼容旧接口，需要传入上下文）"""
        async for event in self.stream_process(message, context):
            yield event
    
    def get_available_resources(self) -> Dict[str, Any]:
        """获取可用资源"""
        tool_info = []
        for tool in self._all_tools:
            tool_info.append({
                "name": getattr(tool, 'name', None) or getattr(tool, '__name__', 'unknown'),
                "description": getattr(tool, 'description', '')
            })
        
        return {
            "tools": tool_info,
            "agents": [
                {"name": agent.config.name, "role": agent.config.role.value}
                for agent in self.sub_agents.values()
            ]
        }