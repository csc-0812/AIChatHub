"""
路由智能体
作为核心路由中心，负责问题解析和任务分发
"""
import uuid
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from .models import AgentRole, AgentConfig, AgentMessage, AgentResponse, RouteDecision
from .sub_agent import SubAgent
from tools import get_all_tools, get_tool_instances
from skills import load_skills_from_directory, execute_skill, get_skill


class RouterAgent:
    """
    路由智能体 - 作为核心路由中心
    
    架构设计：
    - 接收用户问题
    - 解析问题意图
    - 根据可用资源做出路由决策
    - 分发到工具、子智能体或技能
    """
    
    def __init__(self):
        self.sub_agents: Dict[str, SubAgent] = {}
        self.message_history: List[AgentMessage] = []
        self.session_id: str = str(uuid.uuid4())
        
        self._tools_info: List[Dict[str, Any]] = []
        self._skills_info: List[Dict[str, Any]] = []
        
        self._load_resources()
        self._initialize_default_sub_agents()
    
    def _load_resources(self):
        """加载可用资源"""
        # 加载工具
        tools = get_all_tools()
        for tool in tools:
            tool_name = getattr(tool, 'name', None)
            if tool_name is None:
                tool_name = getattr(tool, '__name__', 'unknown')
            self._tools_info.append({
                "name": tool_name,
                "description": getattr(tool, 'description', '')
            })
        
        # 加载技能
        import os
        skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills", "skills_dir")
        skills_dir = os.path.abspath(skills_dir)
        skills = load_skills_from_directory(skills_dir)
        for skill in skills:
            self._skills_info.append({
                "name": skill.name,
                "description": skill.description
            })
    
    def _initialize_default_sub_agents(self):
        """初始化默认子智能体"""
        researcher_config = AgentConfig(
            role=AgentRole.RESEARCHER,
            name="Researcher",
            description="负责信息收集和研究任务",
            tools=["web_search"],
            system_prompt="你是一个专业的研究者，擅长收集和整理信息。"
        )
        self.add_sub_agent(researcher_config)
        
        analyzer_config = AgentConfig(
            role=AgentRole.ANALYZER,
            name="Analyzer",
            description="负责数据分析和计算任务",
            tools=["calculator"],
            system_prompt="你是一个专业的数据分析专家，擅长数学计算和数据分析。"
        )
        self.add_sub_agent(analyzer_config)
    
    def add_sub_agent(self, config: AgentConfig) -> str:
        """添加子智能体"""
        agent_id = str(uuid.uuid4())
        self.sub_agents[agent_id] = SubAgent(config)
        return agent_id
    
    def remove_sub_agent(self, agent_id: str) -> bool:
        """移除子智能体"""
        if agent_id in self.sub_agents:
            del self.sub_agents[agent_id]
            return True
        return False
    
    def get_sub_agent_by_name(self, name: str) -> Optional[SubAgent]:
        """根据名称获取子智能体"""
        for agent in self.sub_agents.values():
            if agent.config.name == name:
                return agent
        return None
    
    def _build_router_prompt(self) -> ChatPromptTemplate:
        """构建路由决策提示词"""
        tools_str = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self._tools_info
        ])
        
        agents_str = "\n".join([
            f"- {agent.config.name} ({agent.config.role.value}): {agent.config.description}"
            for agent in self.sub_agents.values()
        ])
        
        skills_str = "\n".join([
            f"- {skill['name']}: {skill['description']}"
            for skill in self._skills_info
        ])
        
        system_prompt = """
你是一个智能路由助手，负责根据用户的问题选择最合适的处理方式。

## 可用工具：
{tools_str}

## 可用子智能体：
{agents_str}

## 可用技能：
{skills_str}

## 路由规则：
1. 需要实时信息 → 调用工具
2. 需要专业知识 → 调用子智能体
3. 需要特定功能 → 调用技能
4. 简单问题 → 直接回答

## 输出格式（JSON）：
请输出严格的JSON格式，例如：
{"target_type":"direct","target_name":"direct_answer","confidence":0.8,"reasoning":"直接回答用户问题","parameters":{"question":"用户的问题"}}
"""

        system_prompt = system_prompt.format(
            tools_str=tools_str if tools_str else '无',
            agents_str=agents_str if agents_str else '无',
            skills_str=skills_str if skills_str else '无'
        )
        
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{question}")
        ])
    
    async def _make_decision(self, question: str) -> RouteDecision:
        """做出路由决策"""
        from shared.utils.llm_client import llm_client
        import json
        
        llm_client._ensure_model_initialized()
        llm = llm_client._model
        
        if not llm:
            return RouteDecision(
                target_type="direct",
                target_name="direct_answer",
                confidence=0.5,
                reasoning="LLM未初始化"
            )
        
        try:
            prompt = self._build_router_prompt()
            chain = prompt | llm
            
            raw_result = await chain.ainvoke({"question": question})
            
            content = raw_result if isinstance(raw_result, str) else getattr(raw_result, 'content', str(raw_result))
            
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    result = json.loads(content.strip())
                
                return RouteDecision(**result)
            except json.JSONDecodeError:
                return RouteDecision(
                    target_type="direct",
                    target_name="direct_answer",
                    confidence=0.3,
                    reasoning=f"JSON解析失败，降级为直接回答"
                )
        except Exception as e:
            return RouteDecision(
                target_type="direct",
                target_name="direct_answer",
                confidence=0.3,
                reasoning=f"决策失败: {str(e)}"
            )
    
    async def _execute_decision(self, decision: RouteDecision) -> AgentResponse:
        """执行路由决策"""
        target_type = decision.target_type
        target_name = decision.target_name
        parameters = decision.parameters
        
        if target_type == "tool":
            return await self._execute_tool(target_name, parameters)
        elif target_type == "agent":
            return await self._execute_agent(target_name, parameters)
        elif target_type == "skill":
            return await self._execute_skill(target_name, parameters)
        else:
            return await self._execute_direct(parameters)
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> AgentResponse:
        """执行工具调用"""
        for agent in self.sub_agents.values():
            if tool_name in agent.get_tools():
                input_text = f"使用工具 {tool_name}，参数: {parameters}"
                response = await agent.process(input_text, self.message_history)
                response.thinking = f"调用工具: {tool_name}"
                return response
        
        return AgentResponse(
            content=f"未找到支持工具 '{tool_name}' 的智能体",
            thinking=f"工具不可用",
            agent_name="Router",
            role=AgentRole.ROUTER
        )
    
    async def _execute_agent(self, agent_name: str, parameters: Dict[str, Any]) -> AgentResponse:
        """调用子智能体"""
        agent = self.get_sub_agent_by_name(agent_name)
        if agent:
            question = parameters.get("question", "") or parameters.get("input", "")
            response = await agent.process(question, self.message_history)
            response.thinking = f"转发给: {agent_name}"
            return response
        
        return AgentResponse(
            content=f"未找到智能体 '{agent_name}'",
            thinking=f"智能体不存在",
            agent_name="Router",
            role=AgentRole.ROUTER
        )
    
    async def _execute_skill(self, skill_name: str, parameters: Dict[str, Any]) -> AgentResponse:
        """执行技能"""
        result = await execute_skill(skill_name, **parameters)
        
        if result.success:
            return AgentResponse(
                content=str(result.output),
                thinking=f"执行技能: {skill_name}",
                agent_name="Router",
                role=AgentRole.ROUTER
            )
        else:
            return AgentResponse(
                content=f"技能执行失败: {result.error}",
                thinking=f"技能执行失败",
                agent_name="Router",
                role=AgentRole.ROUTER
            )
    
    async def _execute_direct(self, parameters: Dict[str, Any]) -> AgentResponse:
        """直接回答"""
        from shared.utils.llm_client import llm_client
        
        question = parameters.get("question", "") or parameters.get("input", "")
        
        messages = [{"role": "system", "content": "你是一个 helpful 的AI助手。"}]
        for msg in self.message_history[-self.config.context_window:]:
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": question})
        
        response = await llm_client.achat(messages)
        return AgentResponse(
            content=response,
            thinking="直接回答",
            agent_name="Router",
            role=AgentRole.ROUTER
        )
    
    async def chat(self, message: str) -> AgentResponse:
        """处理用户消息"""
        decision = await self._make_decision(message)
        response = await self._execute_decision(decision)
        
        self.message_history.append(AgentMessage(role="user", content=message))
        self.message_history.append(AgentMessage(
            role="assistant",
            content=response.content,
            agent_name=response.agent_name,
            metadata={"route_decision": decision.dict()}
        ))
        
        return response
    
    async def stream_chat(self, message: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式处理用户消息"""
        decision = await self._make_decision(message)
        
        yield {
            "event": "route_decision",
            "data": decision.dict()
        }
        
        self.message_history.append(AgentMessage(role="user", content=message))
        
        if decision.target_type == "agent":
            agent = self.get_sub_agent_by_name(decision.target_name)
            if agent:
                async for event in agent.stream_process(message, self.message_history[:-1]):
                    yield event
        else:
            response = await self._execute_decision(decision)
            yield {
                "event": "done",
                "data": {
                    "thinking": response.thinking,
                    "answer": response.content,
                    "agent": response.agent_name,
                    "role": response.role.value
                }
            }
    
    @property
    def config(self):
        """获取配置（路由智能体自身配置）"""
        return AgentConfig(
            role=AgentRole.ROUTER,
            name="Router",
            description="路由智能体，负责任务分发"
        )
    
    def get_history(self) -> List[AgentMessage]:
        """获取对话历史"""
        return self.message_history.copy()
    
    def clear_history(self):
        """清空对话历史"""
        self.message_history.clear()
    
    def get_available_resources(self) -> Dict[str, Any]:
        """获取可用资源"""
        return {
            "tools": self._tools_info,
            "agents": [
                {"name": agent.config.name, "role": agent.config.role.value}
                for agent in self.sub_agents.values()
            ],
            "skills": self._skills_info
        }