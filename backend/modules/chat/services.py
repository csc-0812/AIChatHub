"""
聊天服务
处理智能体对话逻辑

SSE 事件流模式
  update_user_message → reasoning_content_chunk* → content_chunk* 
  → update_assistant_message → done
"""
import json
import logging
import time
import traceback
from typing import AsyncGenerator, Dict, Any, Optional, List

from .session_manager import SessionManager
from .models import MessageRole, ContentBlock
from shared.utils.logger import chat_logger, log_with_trace


class ChatService:
    """聊天服务 - 使用 RouterAgent 处理消息"""
    
    def __init__(self):
        self.session_manager = SessionManager()
    
    async def chat_stream(
        self, 
        session_id: str,
        message: str,
        user_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天，返回SSE格式数据
        使用 RouterAgent 处理消息

        SSE 事件流：
          1. session_created (仅新建会话时)
          2. update_user_message (用户消息持久化确认，含消息ID)
          3. reasoning_content_chunk* (Agent推理过程，流式增量)
          4. content_chunk* (答案内容，结构化：{kind: "texts", texts: [...]})
          5. update_assistant_message (AI消息持久化确认，用真实ID替换临时ID)
          6. done (null)
        
        Args:
            session_id: 会话ID
            message: 用户消息
            user_id: 用户ID（可选）
            model_id: 模型ID（可选），指定使用的模型
            
        Yields:
            SSE格式的事件数据
        """
        request_start = time.time()
        log_with_trace(chat_logger, logging.INFO,
            f"聊天请求开始: user={user_id}, session_id={session_id}, "
            f"message_len={len(message)}, model_id={model_id}")

        # ── 1. 检查/创建会话 ──
        is_new_session = False
        session = self.session_manager.get_session(session_id)
        if not session:
            log_with_trace(chat_logger, logging.INFO, f"会话不存在，创建新会话: session_id={session_id}")
            session = self.session_manager.create_session(
                user_id=user_id,
                max_context_length=10
            )
            session_id = session.session_id
            is_new_session = True
            yield self._format_sse_event("session_created", {
                "session_id": session_id,
                "title": session.title
            })
        
        # 记录该会话使用的模型ID
        if model_id:
            session.model_id = model_id
        
        # ── 2. 保存用户消息并发送 update_user_message 事件 ──
        session.add_message(MessageRole.USER, message)
        # 获取刚添加的最后一条消息的ID
        user_message_id = session.messages[-1].id if session.messages else ""
        
        yield self._format_sse_event("update_user_message", {
            "id": user_message_id,
            "role": "user",
            "content": [{"kind": "texts", "texts": [message]}],
            "timestamp": session.messages[-1].timestamp.isoformat()
        })
        
        # ── 3. 构建上下文并获取 Agent ──
        messages = self._build_messages(session)
        log_with_trace(chat_logger, logging.INFO, f"上下文消息数: {len(messages)}, 最大={session.max_context_length}")
        
        agent = self.session_manager.get_router_agent(session_id)
        
        # 如果指定了 model_id，则使用对应模型的配置创建 RouterAgent
        if model_id:
            log_with_trace(chat_logger, logging.INFO, f"使用指定模型: model_id={model_id}")
            from modules.models_config.services import models_config_service
            from shared.agent import create_router_agent
            from shared.utils.llm_client import LLMClient
            
            model_config = models_config_service.get_model_by_id(model_id)
            if model_config:
                temp_llm = LLMClient()
                temp_llm._initialize_model_with_config({
                    "model": model_config.model,
                    "model_provider": model_config.provider,
                    "api_key": model_config.api_key,
                    "base_url": model_config.base_url,
                    "temperature": model_config.temperature,
                    "max_tokens": model_config.max_tokens,
                    "timeout": temp_llm.config.get("request_timeout", 60),
                    "max_retries": temp_llm.config.get("max_retries", 3)
                })
                agent = create_router_agent(chat_model=temp_llm._model)
            else:
                log_with_trace(chat_logger, logging.WARNING, f"模型未找到: model_id={model_id}, 回退到默认模型")
        
        if not agent:
            log_with_trace(chat_logger, logging.ERROR, "无法创建 RouterAgent")
            yield self._format_sse_event("error", {"message": "无法创建智能体"})
            return

        # ── 4. 流式执行 Agent ──
        full_content_text = ""
        full_reasoning = ""

        try:
            log_with_trace(chat_logger, logging.INFO, "开始 Agent 流式调用...")
            stream_start = time.time()
            chunk_count = 0

            async for event in agent.stream(messages):
                event_type = event.get("event_type", "")

                if event_type == "reasoning_content_chunk":
                    # Agent推理日志增量
                    reasoning_text = event.get("content", "")
                    full_reasoning += reasoning_text
                    yield self._format_sse_event("reasoning_content_chunk", reasoning_text)
                    chunk_count += 1

                elif event_type == "content_chunk":
                    # 答案内容增量
                    content_blocks = event.get("content", [])
                    full_content_text += self._extract_text_from_blocks(content_blocks)
                    yield self._format_sse_event("content_chunk", {
                        "kind": "texts",
                        "texts": [self._extract_text_from_blocks(content_blocks)]
                    })
                    chunk_count += 1

                elif event_type == "agent_summary":
                    # Agent 执行完成的汇总事件
                    final_text = event.get("content", "")
                    final_reasoning = event.get("reasoning", "")
                    if final_text and final_text != full_content_text:
                        full_content_text = final_text
                    if final_reasoning:
                        full_reasoning = final_reasoning

            stream_elapsed = time.time() - stream_start
            log_with_trace(chat_logger, logging.INFO,
                f"Agent 流式调用完成 (耗时={stream_elapsed:.2f}s, chunk数={chunk_count}, 响应长度={len(full_content_text)})")

            # ── 5. 保存 AI 消息并发送 update_assistant_message 事件 ──
            # 构建结构化内容
            structured_content = [
                ContentBlock(kind="texts", texts=[full_content_text])
            ]

            # 创建临时ID（前端用这个做替换）
            import uuid
            temp_id = str(uuid.uuid4())

            if full_content_text:
                session.add_message(
                    MessageRole.ASSISTANT, 
                    structured_content,
                    reasoning_content=full_reasoning
                )
                self.session_manager._save_session(session)

                # 获取持久化后的真实消息ID
                real_msg = session.messages[-1]
                yield self._format_sse_event("update_assistant_message", {
                    "id": real_msg.id,
                    "temp_id": temp_id,
                    "role": "assistant",
                    "content": [
                        {"kind": "texts", "texts": [full_content_text]}
                    ],
                    "reasoning_content": full_reasoning,
                    "timestamp": real_msg.timestamp.isoformat()
                })

            # ── 6. 发送 done 事件 (data=null) ──
            yield self._format_sse_event("done", None)

            total_elapsed = time.time() - request_start
            log_with_trace(chat_logger, logging.INFO,
                f"聊天请求完成: user={user_id}, session_id={session_id}, "
                f"总耗时={total_elapsed:.2f}s, 响应长度={len(full_content_text)}, "
                f"推理长度={len(full_reasoning)}, 会话消息总数={len(session.messages)}")
            
        except Exception as e:
            log_with_trace(chat_logger, logging.ERROR,
                f"聊天请求异常: user={user_id}, session_id={session_id}, "
                f"error={str(e)}\n{traceback.format_exc()}")
            yield self._format_sse_event("error", {"message": str(e)})
    
    def _extract_text_from_blocks(self, blocks: List) -> str:
        """从结构化内容块中提取纯文本"""
        if not blocks:
            return ""
        texts = []
        for block in blocks:
            if isinstance(block, dict):
                if block.get("kind") == "texts" and block.get("texts"):
                    texts.extend(block["texts"])
            elif hasattr(block, "kind") and block.kind == "texts" and block.texts:
                texts.extend(block.texts)
        return "\n".join(texts)
    
    def _build_messages(self, session) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []
        for msg in session.messages[-session.max_context_length:]:
            messages.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.get_plain_content()
            })
        return messages
    
    def _format_sse_event(self, event: str, data: Any) -> str:
        """
        格式化SSE事件

        标准 SSE 格式 `event: xxx\ndata: {...}\n\n`
        当 data 为 None 时，data 字段输出 null（如 done 事件）。

        Args:
            event: 事件类型
            data: 事件数据（dict/list/str/None）

        Returns:
            SSE格式字符串
        """
        data_str = json.dumps(data, ensure_ascii=False) if data is not None else "null"
        return f"event: {event}\ndata: {data_str}\n\n"


chat_service = ChatService()
