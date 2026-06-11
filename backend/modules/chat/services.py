"""
聊天服务
处理智能体对话逻辑
"""
import json
from typing import AsyncGenerator, Dict, Any, Optional, List

from .session_manager import SessionManager
from .models import MessageRole


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
        
        Args:
            session_id: 会话ID
            message: 用户消息
            user_id: 用户ID（可选）
            model_id: 模型ID（可选），指定使用的模型
            
        Yields:
            SSE格式的事件数据
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            session = self.session_manager.create_session(
                user_id=user_id,
                max_context_length=10
            )
            session_id = session.session_id
            yield self._format_sse_event("session_created", {
                "session_id": session_id,
                "title": session.title
            })
        
        # 记录该会话使用的模型ID
        if model_id:
            session.model_id = model_id
        
        session.add_message(MessageRole.USER, message)
        
        messages = self._build_messages(session)
        
        agent = self.session_manager.get_router_agent(session_id)
        
        # 如果指定了 model_id，则使用对应模型的配置创建 RouterAgent
        if model_id:
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
        
        if not agent:
            yield self._format_sse_event("error", {"message": "无法创建智能体"})
            return
        
        full_content = ""
        prev_content_len = 0

        try:
            async for event in agent.stream(messages):
                if "content" in event:
                    content = event["content"]
                    # 只发送增量部分，避免前端重复拼接
                    if len(content) > prev_content_len:
                        incremental = content[prev_content_len:]
                        yield self._format_sse_event("answer_chunk", {"chunk": incremental})
                    prev_content_len = len(content)
                    full_content = content
            
            yield self._format_sse_event("done", {
                "session_id": session_id,
                "thinking": "",
                "answer": full_content
            })
            
            if full_content:
                session.add_message(MessageRole.ASSISTANT, full_content)
                self.session_manager._save_session(session)
            
        except Exception as e:
            yield self._format_sse_event("error", {"message": str(e)})
    
    def _build_messages(self, session) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []
        for msg in session.messages[-session.max_context_length:]:
            messages.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.content
            })
        return messages
    
    def _format_sse_event(self, event: str, data: Dict[str, Any]) -> str:
        """
        格式化SSE事件
        
        Args:
            event: 事件类型
            data: 事件数据
            
        Returns:
            SSE格式字符串
        """
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


chat_service = ChatService()
