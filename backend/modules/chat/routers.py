"""
聊天模块路由
提供会话管理和SSE流式聊天接口
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, List
from .models import (
    ChatRequest,
    CreateSessionRequest,
    CreateSessionResponse,
    SessionListResponse,
    RenameSessionRequest,
    RenameSessionResponse,
    FileUploadResponse
)
from .services import chat_service
from modules.auth.routers import get_current_user
from modules.auth.models import User
from shared.utils.file_handler import file_handler
from shared.utils.logger import chat_logger, set_trace_id, log_with_trace


router = APIRouter(prefix="/chat", tags=["聊天"])


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    创建新会话
    
    - **title**: 会话标题（可选）
    - **max_context_length**: 最大上下文消息数（默认10条）
    """
    try:
        session = chat_service.session_manager.create_session(
            user_id=current_user.username,
            title=request.title,
            max_context_length=request.max_context_length
        )
        return CreateSessionResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有会话列表"""
    try:
        sessions = chat_service.session_manager.get_user_sessions(current_user.username)
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取会话详情"""
    session = chat_service.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查权限
    if session.user_id and session.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="无权访问此会话")
    
    # 序列化消息，兼容新版结构化content
    serialized_messages = []
    for msg in session.messages:
        msg_dict = {
            "id": msg.id,
            "role": msg.role.value,
            "timestamp": msg.timestamp.isoformat()
        }
        # 结构化内容序列化
        if isinstance(msg.content, list):
            msg_dict["content"] = [
                block.model_dump() if hasattr(block, 'model_dump') else block
                for block in msg.content
            ]
        else:
            msg_dict["content"] = [{"kind": "texts", "texts": [msg.content]}]
        
        # reasoning_content
        if msg.reasoning_content:
            msg_dict["reasoning_content"] = msg.reasoning_content
        
        serialized_messages.append(msg_dict)
    
    return {
        "session_id": session.session_id,
        "title": session.title,
        "max_context_length": session.max_context_length,
        "model_id": session.model_id,
        "messages": serialized_messages,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat()
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除会话"""
    session = chat_service.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查权限
    if session.user_id and session.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="无权删除此会话")
    
    success = chat_service.session_manager.delete_session(
        session_id, 
        user_id=current_user.username
    )
    if success:
        return {"message": "会话已删除"}
    else:
        raise HTTPException(status_code=500, detail="删除会话失败")


@router.post("/sessions/{session_id}/clear")
async def clear_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """清空会话消息"""
    session = chat_service.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查权限
    if session.user_id and session.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    
    updated_session = chat_service.session_manager.clear_session_messages(session_id)
    if updated_session:
        return {"message": "会话消息已清空"}
    else:
        raise HTTPException(status_code=500, detail="清空会话消息失败")


@router.put("/sessions/{session_id}/rename", response_model=RenameSessionResponse)
async def rename_session(
    session_id: str,
    request: RenameSessionRequest,
    current_user: User = Depends(get_current_user)
):
    """重命名会话"""
    session = chat_service.session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 检查权限
    if session.user_id and session.user_id != current_user.username:
        raise HTTPException(status_code=403, detail="无权操作此会话")
    
    updated_session = chat_service.session_manager.rename_session(
        session_id, 
        request.title
    )
    if updated_session:
        return RenameSessionResponse(
            session_id=session_id,
            title=request.title
        )
    else:
        raise HTTPException(status_code=500, detail="重命名会话失败")


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    流式聊天接口
    
    参考IFA: 使用SSE（Server-Sent Events）方式返回大模型的思考过程和回答
    
    **参数**:
    - **session_id**: 会话ID（必填）
    - **message**: 用户消息（必填）
    - **stream**: 是否使用流式输出（默认true）
    
    **SSE 事件类型**:
    - session_created: 新会话创建（如果session_id不存在）
    - update_user_message: 用户消息已保存，含消息ID
    - reasoning_content_chunk: Agent推理过程片段（工具调用日志等）
    - content_chunk: 答案内容片段 {kind: "texts", texts: [...]}
    - update_assistant_message: AI消息已保存，含真实消息ID
    - done: 全部完成
    - error: 错误信息
    
    **前端使用示例**:
    ```javascript
    const response = await fetch('/api/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ... },
        body: JSON.stringify({ session_id, message, stream: true })
    })
    // 通过 ReadableStream 读取 SSE 事件
    ```
    """
    # 生成 trace_id 用于追踪整个请求链路
    trace_id = set_trace_id()

    log_with_trace(chat_logger, logging.INFO,
        f"← 接收前端消息: user={current_user.username}, "
        f"session_id={request.session_id}, "
        f"message_preview={request.message[:50]}{'...' if len(request.message) > 50 else ''}, "
        f"model_id={request.model_id}")

    try:
        # 检查会话是否存在，如果不存在则创建新会话
        session = chat_service.session_manager.get_session(request.session_id)
        if session and session.user_id and session.user_id != current_user.username:
            log_with_trace(chat_logger, logging.WARNING,
                f"权限拒绝: user={current_user.username} 试图访问 session={request.session_id} "
                f"(owner={session.user_id})")
            raise HTTPException(status_code=403, detail="无权访问此会话")
        
        return StreamingResponse(
            chat_service.chat_stream(
                session_id=request.session_id,
                message=request.message,
                user_id=current_user.username,
                model_id=request.model_id
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log_with_trace(chat_logger, logging.ERROR,
            f"聊天接口异常: user={current_user.username}, error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件（图片或文档）
    
    - **file**: 要上传的文件
    - 支持图片: jpeg, png, gif, webp, bmp
    - 支持文档: txt, md, pdf, json, csv, docx, xlsx
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 保存文件
        file_info = file_handler.save_file(
            content=content,
            content_type=file.content_type or "application/octet-stream",
            filename=file.filename
        )
        
        return FileUploadResponse(
            file_id=file_info["file_id"],
            filename=file_info["filename"],
            file_type=file_info["file_type"],
            content_type=file_info["content_type"],
            size=file_info["size"],
            url=file_info["url"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.get("/health")
async def chat_health():
    """聊天服务健康检查"""
    return {"status": "healthy", "service": "chat"}
