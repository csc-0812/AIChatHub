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
    max_context_length: int = 10
    summary: Optional[str] = None
    summary_timestamp: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str):
        """添加消息并维护上下文（不含摘要，同步方法）"""
        self.messages.append(ChatMessage(role=role, content=content))
        self.updated_at = datetime.now()
        
        non_system_messages = [m for m in self.messages if m.role != MessageRole.SYSTEM]
        if len(non_system_messages) > self.max_context_length:
            messages_to_keep = non_system_messages[-self.max_context_length:]
            system_messages = [m for m in self.messages if m.role == MessageRole.SYSTEM]
            self.messages = system_messages + messages_to_keep
    
    async def add_message_with_summary(self, role: MessageRole, content: str):
        """添加消息并维护上下文（含智能摘要，异步方法）"""
        self.messages.append(ChatMessage(role=role, content=content))
        self.updated_at = datetime.now()
        
        if len(self.messages) > self.max_context_length * 2:
            await self._generate_summary()
    
    async def _generate_summary(self):
        """生成对话摘要"""
        from shared.utils.llm_client import llm_client
        
        messages_to_summarize = self.messages[:-self.max_context_length]
        
        history_text = "\n".join([
            f"{m.role.value}: {m.content}" 
            for m in messages_to_summarize
        ])
        
        prompt = f"""请对以下对话历史进行简洁摘要，保留关键信息和决策点，不超过500字：\n\n{history_text}"""
        
        self.summary = await llm_client.achat([{"role": "user", "content": prompt}])
        self.summary_timestamp = datetime.now()
        
        self.messages = self.messages[-self.max_context_length:]
    
    def get_context_messages(self) -> List[Dict[str, str]]:
        """获取用于LLM的上下文消息（包含摘要）"""
        context = []
        
        if self.summary:
            context.append({
                "role": "system", 
                "content": f"对话摘要：{self.summary}"
            })
        
        context.extend([
            {"role": msg.role.value, "content": msg.content}
            for msg in self.messages
        ])
        
        return context
    
    def get_context_for_agent(self) -> List[Dict[str, str]]:
        """获取用于Agent的上下文（不含摘要，保持兼容性）"""
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
    session_id: str
    message: str
    stream: bool = True


class ChatResponse(BaseModel):
    """聊天响应"""
    content: str
    reasoning: Optional[str] = None
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
    content: Optional[str] = None