"""
会话管理器
负责聊天会话的创建、查询、更新和删除
支持工具配置和技能管理
"""
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from agents import RouterAgent, AgentConfig, AgentRole
from tools import get_all_tools, get_tool
from shared.utils.redis_client import redis_client
from .models import ChatMessage, ChatSession, MessageRole


class SessionManager:
    """会话管理器 - 管理聊天会话的生命周期"""
    
    def __init__(self):
        self.redis = redis_client
        self.session_prefix = "chat:session:"
        self.user_sessions_prefix = "chat:user_sessions:"
        # 内存中缓存 RouterAgent 实例
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
        
        # 保存到Redis
        self._save_session(session)
        
        # 添加到用户的会话列表
        if user_id:
            self._add_session_to_user_list(user_id, session_id)
        
        # 创建对应的 RouterAgent
        self._create_router_agent(session_id)
        
        return session
    
    def _create_router_agent(self, session_id: str):
        """为会话创建 RouterAgent"""
        router_agent = RouterAgent()
        router_agent.session_id = session_id
        
        self._router_agents[session_id] = router_agent
        return router_agent
    
    def get_router_agent(self, session_id: str) -> Optional[RouterAgent]:
        """获取会话的 RouterAgent"""
        # 先从内存获取
        if session_id in self._router_agents:
            return self._router_agents[session_id]
        
        # 获取会话信息
        session = self.get_session(session_id)
        if not session:
            return None
        
        # 重新创建 RouterAgent
        return self._create_router_agent(session_id)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        session_data = self.redis.get(self._get_session_key(session_id))
        if not session_data:
            return None
        
        return ChatSession.model_validate_json(session_data)
    
    def _save_session(self, session: ChatSession):
        """保存会话到Redis"""
        session_key = self._get_session_key(session.session_id)
        self.redis.set(
            session_key, 
            session.model_dump_json(),
            expire=7 * 24 * 3600  # 7天过期
        )
    
    def _add_session_to_user_list(self, user_id: str, session_id: str):
        """添加会话到用户的会话列表"""
        user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
        # 使用Redis集合存储用户的会话ID
        self.redis.client.sadd(user_sessions_key, session_id)
        # 设置过期时间
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
        
        # 按更新时间排序
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str, user_id: Optional[str] = None) -> bool:
        """删除会话"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        # 删除会话数据
        self.redis.delete(self._get_session_key(session_id))
        
        # 从内存中移除 RouterAgent
        if session_id in self._router_agents:
            del self._router_agents[session_id]
        
        # 从用户的会话列表中移除
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
        
        # 同时清空 RouterAgent 的历史
        router_agent = self.get_router_agent(session_id)
        if router_agent:
            router_agent.clear_history()
        
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
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """获取所有可用的工具列表"""
        tools = get_all_tools()
        return [
            {
                "name": getattr(tool, 'name', tool.__name__),
                "description": getattr(tool, 'description', '')
            }
            for tool in tools
        ]
    
    def get_session_agent_tools(self, session_id: str) -> Dict[str, Any]:
        """获取会话中智能体的工具配置"""
        router_agent = self.get_router_agent(session_id)
        if not router_agent:
            return {}
        
        return router_agent.get_available_resources()
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """获取所有会话（管理员功能）"""
        pattern = f"{self.session_prefix}*"
        keys = self.redis.client.keys(pattern)
        
        sessions = []
        for key in keys:
            session_id = key.decode('utf-8').replace(self.session_prefix, '')
            session = self.get_session(session_id)
            if session:
                sessions.append({
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "message_count": len(session.messages)
                })
        
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions


# 创建会话管理器实例
session_manager = SessionManager()