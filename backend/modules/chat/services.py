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
        user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天，返回SSE格式数据
        使用 RouterAgent 处理消息
        
        Args:
            session_id: 会话ID
            message: 用户消息
            user_id: 用户ID（可选）
            
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
        
        session.add_message(MessageRole.USER, message)
        
        messages = self._build_messages(session)
        
        agent = self.session_manager.get_router_agent(session_id)
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
