"""
聊天模块数据模型
"""
import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ContentBlock(BaseModel):
    """结构化内容块
    content = [{kind: "texts"/"files"/"images", ...}]
    """
    kind: str  # "texts", "files", "images"
    texts: Optional[List[str]] = None
    files: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None


class ChatMessage(BaseModel):
    """聊天消息
    消息包含 id、role、content(结构化数组)、reasoning_content
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: Union[str, List[ContentBlock]] = ""  # 支持纯文本(向后兼容)或结构化内容
    reasoning_content: Optional[str] = None  # Agent推理过程
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def get_plain_content(self) -> str:
        """获取纯文本内容（用于LLM上下文构建）"""
        if isinstance(self.content, str):
            return self.content
        # 结构化内容：提取所有 texts
        parts = []
        for block in self.content:
            if block.kind == "texts" and block.texts:
                parts.append("\n".join(block.texts))
        return "\n".join(parts)


class ChatSession(BaseModel):
    """聊天会话"""
    session_id: str
    user_id: Optional[str] = None
    title: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    max_context_length: int = 10  # 最大保留的上下文消息数
    model_id: Optional[str] = None  # 该会话使用的模型ID
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(
        self, 
        role: MessageRole, 
        content: Union[str, List[ContentBlock]], 
        reasoning_content: Optional[str] = None
    ):
        """添加消息并维护上下文长度"""
        message = ChatMessage(
            role=role, 
            content=content,
            reasoning_content=reasoning_content
        )
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
            {
                "role": msg.role.value, 
                "content": msg.get_plain_content()
            }
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
    model_id: Optional[str] = None  # 指定使用的模型ID，不传则使用默认启用的模型


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


class DeleteMessageResponse(BaseModel):
    """删除消息响应"""
    session_id: str
    deleted_count: int
    message: str = "消息删除成功"


class ChatAttachment(BaseModel):
    """聊天附件"""
    file_id: str
    filename: str
    file_type: str
    content_type: str
    url: str
    content: Optional[str] = None  # 文本文件的内容
