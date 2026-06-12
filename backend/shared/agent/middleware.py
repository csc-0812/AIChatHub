"""
Agent Middleware Module
提供智能体使用的中间件定义

参考IFA: Middleware 通过 get_stream_writer() 发送 custom 事件，
前端以 reasoning_content_chunk 类型接收，用于展示推理过程。
"""
import json
import logging
from typing import Any, Optional
from datetime import datetime

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents.middleware.summarization import SummarizationMiddleware

from shared.utils.logger import get_logger, log_with_trace, get_trace_id

logger = get_logger("agent.middleware")


def _try_get_stream_writer():
    """
    安全获取 LangGraph stream_writer
    参考IFA: get_stream_writer() 是 LangGraph 的上下文感知流写入器，
    在 astream() 调用内部会把事件写入当前的 SSE 流。
    如果不在流上下文中则返回 None。
    """
    try:
        from langgraph.config import get_stream_writer
        return get_stream_writer()
    except (ImportError, RuntimeError):
        return None


def _emit_reasoning_chunk(message: str):
    """
    通过 stream_writer 发送推理日志 chunk
    前端以 reasoning_content_chunk 事件接收
    """
    writer = _try_get_stream_writer()
    if writer:
        # custom 事件格式：在 router_agent.stream() 中被解析为 reasoning_content_chunk
        writer({"event_type": "reasoning", "reasoning": message})


class AgentLoggingMiddleware(AgentMiddleware):
    """
    智能体日志记录中间件
    参考IFA: 拦截 Agent/工具/模型调用事件，通过 get_stream_writer() 
    将推理日志推送到前端 SSE 流。
    """

    def __init__(self, agent_name: str = "Agent"):
        self.agent_name = agent_name

    async def abefore_agent(self, state, runtime):
        """Agent 开始执行"""
        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] Agent 开始执行")
        msg = f"🔍 {self.agent_name} 开始分析..."
        _emit_reasoning_chunk(msg)

    async def aafter_agent(self, state, runtime):
        """Agent 结束执行"""
        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] Agent 执行结束")
        msg = f"✅ {self.agent_name} 分析完成"
        _emit_reasoning_chunk(msg)

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler
    ) -> ModelResponse:
        """异步包装模型调用，记录请求和响应"""
        start_time = datetime.now()

        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 模型调用开始 (消息数={len(request.messages)})")

        try:
            response = await handler(request)
            duration = (datetime.now() - start_time).total_seconds()

            # 记录 token 使用情况
            usage_info = ""
            if hasattr(response, 'response_metadata'):
                usage = response.response_metadata.get('token_usage', {})
                if usage:
                    usage_info = f" (输入={usage.get('input_tokens', '?')} tokens, 输出={usage.get('output_tokens', '?')} tokens)"
            
            log_with_trace(logger, logging.INFO, 
                f"[{self.agent_name}] 模型调用完成 (耗时={duration:.2f}s{usage_info})")

            return response

        except Exception as e:
            log_with_trace(logger, logging.ERROR, f"[{self.agent_name}] 模型调用失败: {str(e)}")
            raise

    async def awrap_tool_call(self, request, handler):
        """异步包装工具调用，记录工具调用信息并推送到前端"""
        tool_name = request.tool_call.get('name', 'unknown')
        tool_args = request.tool_call.get('args', {})
        start_time = datetime.now()

        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 工具调用: {tool_name}")

        # 参考IFA: 向SSE流推送工具调用开始事件
        args_preview = json.dumps(tool_args, ensure_ascii=False)
        if len(args_preview) > 200:
            args_preview = args_preview[:200] + "..."
        _emit_reasoning_chunk(f"⚙️ 调用工具: {tool_name}\n参数: {args_preview}")

        try:
            response = await handler(request)
            duration = (datetime.now() - start_time).total_seconds()

            log_with_trace(logger, logging.INFO, 
                f"[{self.agent_name}] 工具调用完成: {tool_name} (耗时={duration:.2f}s)")

            # 参考IFA: 向SSE流推送工具调用完成事件
            result_preview = ""
            if isinstance(response, dict):
                result_preview = json.dumps(response, ensure_ascii=False)
            elif hasattr(response, 'content'):
                result_preview = str(response.content)
            if len(result_preview) > 300:
                result_preview = result_preview[:300] + "..."
            _emit_reasoning_chunk(f"✅ 工具 [{tool_name}] 执行完成 (耗时={duration:.2f}s)")

            return response
        except Exception as e:
            log_with_trace(logger, logging.ERROR, f"[{self.agent_name}] 工具调用失败 [{tool_name}]: {str(e)}")
            _emit_reasoning_chunk(f"❌ 工具 [{tool_name}] 执行失败: {str(e)}")
            raise


def create_default_middleware(
    agent_name: str = "Agent",
    summarization_model=None,
    max_tokens_before_summary: int = 16384
) -> list:
    """
    创建默认中间件列表
    
    Args:
        agent_name: 智能体名称
        summarization_model: 摘要模型
        max_tokens_before_summary: 触发摘要的最大token数
        
    Returns:
        中间件列表
    """
    middleware = []
    
    if summarization_model:
        middleware.append(
            SummarizationMiddleware(
                model=summarization_model,
                max_tokens_before_summary=max_tokens_before_summary
            )
        )
    
    middleware.append(AgentLoggingMiddleware(agent_name))
    
    return middleware
