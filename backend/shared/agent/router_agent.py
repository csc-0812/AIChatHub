"""
Router Agent Module
基于LangGraph构建的流式智能路由器智能体
负责用户意图识别和简单聊天
"""
import json
import logging
import time
from typing import Optional, Any, AsyncGenerator, Dict, List
from langchain.agents import create_agent, AgentState
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, ToolMessage
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
          - "messages": 拦截 LLM 流式输出，每 token 触发一次，实现真正的逐字流式
          - "custom":   获取 Middleware 推送的自定义事件（工具调用日志等）

        messages 模式 chunk 格式: (AIMessageChunk, metadata) 元组
          其中 AIMessageChunk.content 为当前 token 的增量文本
        
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

        # 令牌缓冲区：避免逐 token 发 SSE（频率过高），攒够一批再发送
        CONTENT_CHUNK_SIZE = 100    # 每攒 100 个字符发送一次
        text_buffer = ""            # 令牌缓冲区
        event_count = 0
        reasoning_buffer = []       # 收集推理内容
        final_text = ""             # 最终收集的文本
        _seen_tool_ids = set()      # 已发送过 reasoning 的 tool_call id（去重）

        def _flush_content_buffer():
            """清空令牌缓冲区，发送一个 content_chunk 事件"""
            nonlocal text_buffer
            if text_buffer:
                yield {
                    "event_type": "content_chunk",
                    "content": [{"kind": "texts", "texts": [text_buffer]}]
                }
                text_buffer = ""

        # messages 模式: LLM 每输出一个 token 即触发，真正 token 级流式
        # custom 模式: Middleware 通过 get_stream_writer() 推送的事件
        async for sm, chunk in agent.astream(
            state, 
            stream_mode=["messages", "custom"],
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

            elif sm == "messages":
                # messages 模式: (message, metadata) 元组
                # 从 messages 流中同时提取推理事件（工具调用/返回）和答案内容
                # 避免依赖 middleware custom 事件（可能被 LangGraph 批量缓冲）
                msg = chunk[0] if isinstance(chunk, tuple) and len(chunk) >= 1 else chunk
                
                # 检测工具调用：Agent 决定使用工具时产生含 tool_calls 的 AIMessage
                # 注意：messages 流式模式会逐步流出 AIMessageChunk，同一工具调用会出现多次
                # 策略：跳过空参数的中间状态 + 按 id 去重，只发送完整的一次
                if isinstance(msg, (AIMessage, AIMessageChunk)) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tc_id = tc.get('id', '')
                        name = tc.get('name', 'unknown')
                        args = tc.get('args', {})

                        # 跳过空参数（中间流式状态，tool_calls 还没构建完）
                        if not args:
                            continue

                        # 去重：同一个 tool_call 只发一次 reasoning
                        if tc_id and tc_id in _seen_tool_ids:
                            continue
                        if tc_id:
                            _seen_tool_ids.add(tc_id)

                        args_str = json.dumps(args, ensure_ascii=False)
                        if len(args_str) > 200:
                            args_str = args_str[:200] + '...'
                        reasoning = f"⚙️ 调用工具: {name}\n参数: {args_str}"
                        yield {"event_type": "reasoning_content_chunk", "content": reasoning}
                        reasoning_buffer.append(reasoning)
                
                # 检测工具返回结果
                if isinstance(msg, ToolMessage):
                    tool_name = msg.name if hasattr(msg, 'name') else 'unknown'
                    content_str = str(msg.content)
                    if len(content_str) > 300:
                        content_str = content_str[:300] + '...'
                    reasoning = f"✅ 工具 [{tool_name}] 返回结果"
                    yield {"event_type": "reasoning_content_chunk", "content": reasoning}
                    reasoning_buffer.append(reasoning)
                
                # 处理文本内容（跳过仅有 tool_calls 无内容的 AIMessage）
                if (isinstance(msg, (AIMessage, AIMessageChunk)) 
                        and msg.content 
                        and isinstance(msg.content, str)):
                    # 跳过纯 tool_calls 消息（其 content 通常为空）
                    if hasattr(msg, 'tool_calls') and msg.tool_calls and not msg.content.strip():
                        continue
                    token = msg.content
                    final_text += token
                    text_buffer += token
                    
                    # 缓冲区达到阈值时刷新发送
                    if len(text_buffer) >= CONTENT_CHUNK_SIZE:
                        for evt in _flush_content_buffer():
                            yield evt

        # 发送缓冲区残留在尾部
        for evt in _flush_content_buffer():
            yield evt

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
