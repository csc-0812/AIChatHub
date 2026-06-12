"""
会话管理器
负责聊天会话的创建、查询、更新和删除
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from shared.agent import create_router_agent, RouterAgent
from shared.utils.redis_client import redis_client
from shared.utils.logger import chat_logger, log_with_trace, get_trace_id
from .models import ChatMessage, ChatSession, MessageRole


class SessionManager:
    """会话管理器 - 管理聊天会话的生命周期"""
    
    def __init__(self):
        self.redis = redis_client
        self.session_prefix = "chat:session:"
        self.user_sessions_prefix = "chat:user_sessions:"
        self._router_agents: Dict[str, RouterAgent] = {}
    
    def _get_session_key(self, session_id: str) -> str:
        """获取会话在Redis中的key"""
        return f"{self.session_prefix}{session_id}"
    
    def create_session(
        self, 
        user_id: Optional[str] = None, 
        title: Optional[str] = None,
        max_context_length: int = 10
    ) -> ChatSession:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            title=title or f"新会话 {datetime.now().strftime('%m-%d %H:%M')}",
            max_context_length=max_context_length
        )
        
        self._save_session(session)
        
        if user_id:
            self._add_session_to_user_list(user_id, session_id)
        
        self._create_router_agent(session_id)

        log_with_trace(chat_logger, logging.INFO,
            f"会话创建: session_id={session_id}, user={user_id}, title={session.title}, max_context={max_context_length}")

        return session
    
    def _create_router_agent(self, session_id: str):
        """为会话创建RouterAgent"""
        log_with_trace(chat_logger, logging.INFO, f"创建 RouterAgent: session_id={session_id}")
        agent = create_router_agent()
        self._router_agents[session_id] = agent
        return agent
    
    def get_router_agent(self, session_id: str) -> Optional[RouterAgent]:
        """获取会话的RouterAgent"""
        if session_id in self._router_agents:
            return self._router_agents[session_id]
        
        session = self.get_session(session_id)
        if not session:
            log_with_trace(chat_logger, logging.WARNING, f"RouterAgent 不存在且会话未找到: session_id={session_id}")
            return None
        
        log_with_trace(chat_logger, logging.INFO, f"RouterAgent 内存中不存在，重建: session_id={session_id}")
        return self._create_router_agent(session_id)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        session_data = self.redis.get(self._get_session_key(session_id))
        if not session_data:
            log_with_trace(chat_logger, logging.DEBUG, f"会话未命中缓存: session_id={session_id}")
            return None
        
        return ChatSession.model_validate_json(session_data)
    
    def _save_session(self, session: ChatSession):
        """保存会话到Redis"""
        session_key = self._get_session_key(session.session_id)
        log_with_trace(chat_logger, logging.DEBUG, f"持久化会话: session_id={session.session_id}, 消息数={len(session.messages)}")
        self.redis.set(
            session_key, 
            session.model_dump_json(),
            expire=7 * 24 * 3600
        )
    
    def _add_session_to_user_list(self, user_id: str, session_id: str):
        """添加会话到用户的会话列表"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        self.redis.client.sadd(user_sessions_key, session_id)
        self.redis.client.expire(user_sessions_key, 7 * 24 * 3600)
    
    def add_message_to_session(
        self, 
        session_id: str, 
        role: MessageRole, 
        content: str
    ) -> Optional[ChatSession]:
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.add_message(role, content)
        self._save_session(session)
        return session
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有会话"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        session_ids = self.redis.client.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": len(session.messages)
                })
        
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """删除会话"""
        session = self.get_session(session_id)
        if not session:
            log_with_trace(chat_logger, logging.WARNING, f"删除会话失败(不存在): session_id={session_id}")
            return False

        log_with_trace(chat_logger, logging.INFO, f"删除会话: session_id={session_id}, user={user_id}")

        self.redis.delete(self._get_session_key(session_id))
        
        if session_id in self._router_agents:
            del self._router_agents[session_id]
        
        if user_id:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            self.redis.client.srem(user_sessions_key, session_id)
        
        return True
    
    def clear_session_messages(self, session_id: str) -> Optional[ChatSession]:
        """清空会话消息"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.messages = []
        session.updated_at = datetime.now()
        self._save_session(session)
        
        return session
    
    def rename_session(self, session_id: str, new_title: str) -> Optional[ChatSession]:
        """重命名会话"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.title = new_title
        session.updated_at = datetime.now()
        self._save_session(session)
        return session


session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return session_manager
