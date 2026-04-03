"""
聊天模块数据模型
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """聊天消息"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    max_context_length: int = 10  # 最大保留的上下文消息数
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str):
        """添加消息并维护上下文长度"""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        
        # 保留最近的 max_context_length 条消息（不包括系统消息）
        non_system_messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]
        if len(non_system_messages) > self.max_context_length:
            # 只保留最近的 max_context_length 条非系统消息
            messages_to_keep = non_system_messages[-self.max_context_length:]
            # 保留系统消息和需要保留的消息
            system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            self.messages = system_messages + messages_to_keep
        
        self.updated_at = datetime.now()
    
    def get_context_messages(self) -> List[Dict[str, str]]:
        """获取用于LLM的上下文消息"""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ]


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    title: Optional[str] = None
    max_context_length: int = 10


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str
    title: Optional[str]
    created_at: datetime


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: str  # 会话ID
    message: str     # 用户消息
    stream: bool = True  # 是否使用流式输出


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    reasoning: Optional[str] = None  # 思考过程
    done: bool = False


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: List[Dict[str, Any]]


class SSEEvent(BaseModel):
    """SSE事件"""
    event: str
    data: Dict[str, Any]


class RenameSessionRequest(BaseModel):
    """重命名会话请求"""
    title: str


class RenameSessionResponse(BaseModel):
    """重命名会话响应"""
    session_id: str
    title: str
    message: str = "会话重命名成功"


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    file_id: str
    filename: str
    file_type: str
    content_type: str
    size: int
    url: str
    message: str = "文件上传成功"


class ChatAttachment(BaseModel):
    """聊天附件"""
    file_id: str
    filename: str
    file_type: str
    content_type: str
    url: str
    content: Optional[str] = None  # 文本文件的内容
