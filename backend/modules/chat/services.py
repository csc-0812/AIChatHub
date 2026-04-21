"""
聊天服务
处理智能体对话逻辑
"""
import json
from typing import AsyncGenerator, Dict, Any, Optional

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
        # 获取或创建会话
        session = self.session_manager.get_session(session_id)
        if not session:
            # 如果会话不存在，创建新会话
            session = self.session_manager.create_session(
                user_id=user_id,
                max_context_length=10
            )
            session_id = session.session_id
            yield self._format_sse_event("session_created", {
                "session_id": session_id,
                "title": session.title
            })
        
        # 获取 RouterAgent
        router_agent = self.session_manager.get_router_agent(session_id)
        if not router_agent:
            raise RuntimeError("无法创建 RouterAgent")
        
        # 添加用户消息到会话（用于兼容现有数据模型）
        session.add_message(MessageRole.USER, message)
        
        # 使用 RouterAgent 进行流式对话
        full_content = ""
        thinking_content = ""
        
        try:
            async for event in router_agent.stream_chat(message):
                event_type = event["event"]
                event_data = event["data"]
                
                # 转换 TeamAgent 事件为前端兼容格式
                if event_type == "start":
                    yield self._format_sse_event("start", {
                        "message": f"开始生成回答 - {event_data.get('agent', 'AI助手')}"
                    })
                
                elif event_type == "thinking":
                    thinking_content = event_data.get("content", "")
                    yield self._format_sse_event("thinking", event_data)
                
                elif event_type == "thinking_chunk":
                    yield self._format_sse_event("thinking_chunk", event_data)
                
                elif event_type == "answer":
                    full_content = event_data.get("content", "")
                    yield self._format_sse_event("answer", event_data)
                
                elif event_type == "answer_chunk":
                    yield self._format_sse_event("answer_chunk", event_data)
                
                elif event_type == "done":
                    full_content = event_data.get("answer", "")
                    thinking_content = event_data.get("thinking", "")
                    yield self._format_sse_event("done", {
                        "session_id": session_id,
                        "thinking": thinking_content,
                        "answer": full_content
                    })
                
                elif event_type == "error":
                    yield self._format_sse_event("error", event_data)
            
            # 保存AI回复到会话
            if full_content:
                session.add_message(MessageRole.ASSISTANT, full_content)
                self.session_manager._save_session(session)
            
        except Exception as e:
            yield self._format_sse_event("error", {"message": str(e)})
    
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


# 创建全局聊天服务实例
chat_service = ChatService()
