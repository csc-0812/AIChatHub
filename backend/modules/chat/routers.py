"""
聊天模块路由
提供会话管理和SSE流式聊天接口
"""
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
    
    return {
        "session_id": session.session_id,
        "title": session.title,
        "max_context_length": session.max_context_length,
        "model_id": session.model_id,
        "messages": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in session.messages
        ],
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
    
    使用SSE（Server-Sent Events）方式返回大模型的思考过程和回答
    
    **参数**:
    - **session_id**: 会话ID（必填）
    - **message**: 用户消息（必填）
    - **stream**: 是否使用流式输出（默认true）
    
    **事件类型**:
    - session_created: 新会话创建（如果session_id不存在）
    - start: 开始生成
    - thinking: 思考过程完成
    - thinking_chunk: 思考过程片段（实时）
    - answer: 最终答案完成
    - answer_chunk: 答案片段（实时）
    - done: 全部完成
    - error: 错误信息
    
    **前端使用示例**:
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream');
    eventSource.addEventListener('thinking', (e) => {
        console.log('思考过程:', JSON.parse(e.data).content);
    });
    eventSource.addEventListener('answer', (e) => {
        console.log('最终答案:', JSON.parse(e.data).content);
    });
    ```
    """
    try:
        # 检查会话是否存在，如果不存在则创建新会话
        session = chat_service.session_manager.get_session(request.session_id)
        if session and session.user_id and session.user_id != current_user.username:
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
