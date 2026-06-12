"""
Router Agent Module
基于LangGraph构建的流式智能路由器智能体
负责用户意图识别和简单聊天
"""
import logging
import time
from typing import Optional, Any, AsyncGenerator, Dict, List
from langchain.agents import create_agent, AgentState
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.state import CompiledStateGraph

from shared.utils.logger import get_logger, log_with_trace
from .tools import BASIC_TOOLS
from .prompts import router_prompt
from .middleware import create_default_middleware

logger = get_logger("agent.router")


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
            build_start = time.time()
            log_with_trace(logger, logging.INFO, "开始构建 RouterAgent...")

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

            elapsed = time.time() - build_start
            log_with_trace(logger, logging.INFO,
                f"RouterAgent 构建完成 (耗时={elapsed:.2f}s, 工具数={len(BASIC_TOOLS)}, "
                f"中间件数={len(middleware)}, system_prompt长度={len(str(router_prompt))})")
        
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

        使用双流模式:
          - "values":  获取状态快照（含完整的 messages 列表）
          - "custom":  获取 Middleware 推送的自定义事件（工具调用日志等）

        LangGraph stream_mode="values" 的 chunk 格式为:
          {"messages": [HumanMessage, AIMessage, ToolMessage, ...], ...}
          即完整的状态字典，"messages" 的值是消息列表
        
        事件类型:
          - reasoning_content_chunk: Agent推理/工具调用日志（string增量）
          - content_chunk: 答案内容块 {kind: "texts", texts: [...]}

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Yields:
            流式响应事件
        """
        stream_start = time.time()
        log_with_trace(logger, logging.INFO, f"Agent 流式执行开始 (消息数={len(messages)})")

        agent = self.build()

        state: AgentState = {
            "messages": [
                HumanMessage(content=msg["content"]) 
                if msg["role"] == "user" 
                else AIMessage(content=msg["content"])
                for msg in messages
            ]
        }

        event_count = 0
        reasoning_buffer = []       # 收集推理内容
        prev_text = ""              # 用于增量文本对比
        final_text = ""             # 最终收集的文本

        # 记录初始消息数量，用于过滤本轮之前的旧消息
        # values 模式返回完整状态快照，内含所有历史消息
        # 仅从本轮新增的消息中提取内容，避免拿到上一轮的 AIMessage
        initial_msg_count = len(state["messages"])

        # values 模式: 每个 chunk 是完整状态 {"messages": [...]}
        # custom 模式: Middleware 通过 get_stream_writer() 推送的事件
        async for sm, chunk in agent.astream(
            state, 
            stream_mode=["values", "custom"],
            **kwargs
        ):
            event_count += 1

            if sm == "custom":
                # custom 事件：来自 Middleware 的推理日志
                if isinstance(chunk, dict):
                    reasoning = chunk.get("reasoning", "")
                    if reasoning:
                        yield {
                            "event_type": "reasoning_content_chunk",
                            "content": reasoning
                        }
                        reasoning_buffer.append(reasoning)

            elif sm == "values":
                # values 事件：完整状态快照 {"messages": [msg_list], ...}
                # 只从本轮新增的消息中提取内容
                text = self._extract_content_from_values(chunk, skip_count=initial_msg_count)
                if text:
                    # 只发送增量部分，token 级别流式
                    if len(text) > len(prev_text):
                        incremental = text[len(prev_text):]
                        if incremental:
                            yield {
                                "event_type": "content_chunk",
                                "content": [{"kind": "texts", "texts": [incremental]}]
                            }
                    prev_text = text
                    final_text = text

        elapsed = time.time() - stream_start
        
        log_with_trace(logger, logging.INFO, 
            f"Agent 流式执行完成 (耗时={elapsed:.2f}s, 总事件数={event_count}, "
            f"响应长度={len(final_text)}, 推理长度={len(reasoning_buffer)})")

        # 返回最终汇总
        yield {
            "event_type": "agent_summary",
            "content": final_text,
            "reasoning": "\n".join(reasoning_buffer)
        }
    
    def _extract_content_from_values(self, chunk: Any, skip_count: int = 0) -> str:
        """
        从 stream_mode="values" 的 chunk 中提取 AIMessage 文本内容
        
        values chunk 格式为完整状态字典:
          {"messages": [HumanMessage, AIMessage("工具结果..."), AIMessage("最终答案")], ...}
        
        遍历 messages 列表，找到最后一条有文本内容的 AIMessage。
        
        Args:
            chunk: values 模式的 chunk 数据
            skip_count: 跳过前 N 条消息（过滤本轮之前的历史消息）
        """
        if chunk is None:
            return ""
            
        # 格式1: 直接是 dict {"messages": [...]} — values 模式的标准格式
        if isinstance(chunk, dict):
            msgs = chunk.get("messages", [])
            if isinstance(msgs, list):
                # 只扫描本轮新增的消息，避免拿到上一轮 AIMessage 的内容
                new_msgs = msgs[skip_count:] if skip_count > 0 else msgs
                for msg in reversed(new_msgs):
                    if isinstance(msg, AIMessage) and msg.content:
                        return msg.content
            # 也兼容 {node_name: AIMessage} 格式
            for key, value in chunk.items():
                if isinstance(value, AIMessage) and value.content:
                    return value.content
        
        # 格式2: AIMessage 直接传来
        if isinstance(chunk, AIMessage) and chunk.content:
            return chunk.content
        
        # 格式3: 元组 (node_name, value)
        if isinstance(chunk, tuple) and len(chunk) >= 1:
            inner = chunk[0] if len(chunk) == 1 else chunk[1]
            if isinstance(inner, dict):
                return self._extract_content_from_values(inner, skip_count)
            if isinstance(inner, AIMessage) and inner.content:
                return inner.content
                
        return ""
    
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
        """
        格式化流式事件（保留向后兼容：默认 stream_mode 的 {node: value} 格式）
        """
        if not isinstance(event, dict):
            return None

        for key, value in event.items():
            if isinstance(value, AIMessage):
                return {
                    "content": value.content,
                    "role": "assistant",
                    "tool_calls": value.tool_calls or []
                }
            # value 是 dict 包含 messages
            if isinstance(value, dict) and "messages" in value:
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
