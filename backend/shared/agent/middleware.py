"""
Agent Middleware Module
提供智能体使用的中间件定义
"""
import logging
from typing import Any, Optional
from datetime import datetime

from langchain.agents.middleware.types import AgentMiddleware, ModelRequest, ModelResponse
from langchain.agents.middleware.summarization import SummarizationMiddleware

from shared.utils.logger import get_logger, log_with_trace, get_trace_id

logger = get_logger("agent.middleware")


class AgentLoggingMiddleware(AgentMiddleware):
    """
    智能体日志记录中间件
    记录智能体的所有操作和响应
    """

    def __init__(self, agent_name: str = "Agent"):
        self.agent_name = agent_name

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler
    ) -> ModelResponse:
        """异步包装模型调用，记录请求和响应"""
        start_time = datetime.now()
        trace_id = get_trace_id()

        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 模型调用开始 (消息数={len(request.messages)})")
        logger.debug(f"[{self.agent_name}] Request messages: {request.messages}")

        try:
            response = await handler(request)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 模型调用完成 (耗时={duration:.2f}s)")
            logger.debug(f"[{self.agent_name}] Response: {response}")

            return response

        except Exception as e:
            log_with_trace(logger, logging.ERROR, f"[{self.agent_name}] 模型调用失败: {str(e)}")
            raise

    async def awrap_tool_call(self, request, handler):
        """异步包装工具调用，记录工具调用信息"""
        tool_name = request.tool_call.get('name', 'unknown')
        log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 工具调用: {tool_name}")
        logger.debug(f"[{self.agent_name}] Tool args: {request.tool_call.get('args')}")

        try:
            response = await handler(request)
            log_with_trace(logger, logging.INFO, f"[{self.agent_name}] 工具调用完成: {tool_name}")
            return response
        except Exception as e:
            log_with_trace(logger, logging.ERROR, f"[{self.agent_name}] 工具调用失败 [{tool_name}]: {str(e)}")
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
