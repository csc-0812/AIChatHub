"""
基础智能体
提供单智能体的核心功能
"""
from typing import List, Dict, Any, Optional, AsyncGenerator

from ..utils.llm_client import llm_client
from .models import AgentConfig, AgentMessage, AgentResponse


class BaseAgent:
    """基础智能体类 - 处理单轮对话"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.llm_client = llm_client
        self.message_history: List[AgentMessage] = []
    
    async def process(
        self, 
        message: str, 
        context: Optional[List[AgentMessage]] = None
    ) -> AgentResponse:
        """
        处理消息
        
        Args:
            message: 用户输入
            context: 上下文消息
            
        Returns:
            AgentResponse
        """
        # 构建消息列表
        messages = []
        
        # 添加系统提示词
        messages.append({
            "role": "system", 
            "content": self.config.system_prompt
        })
        
        # 添加上下文
        if context:
            for msg in context[-self.config.context_window:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 调用LLM
        response = await self.llm_client.achat(messages)
        
        # 解析响应
        thinking, answer = self._parse_response(response)
        
        return AgentResponse(
            content=answer,
            thinking=thinking if self.config.enable_thinking else None,
            agent_name=self.config.name,
            role=self.config.role
        )
    
    async def stream_process(
        self, 
        message: str, 
        context: Optional[List[AgentMessage]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理消息
        
        Args:
            message: 用户输入
            context: 上下文消息
            
        Yields:
            流式事件数据
        """
        # 构建消息列表
        messages = []
        
        # 添加系统提示词
        messages.append({
            "role": "system", 
            "content": self.config.system_prompt
        })
        
        # 添加上下文
        if context:
            for msg in context[-self.config.context_window:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 添加当前消息
        messages.append({"role": "user", "content": message})
        
        # 发送开始事件
        yield {
            "event": "start",
            "data": {"agent": self.config.name, "role": self.config.role.value}
        }
        
        # 流式调用LLM
        full_content = ""
        thinking_content = ""
        answer_content = ""
        is_in_thinking = False
        is_in_answer = False
        
        try:
            async for chunk in self.llm_client.stream_chat(messages):
                full_content += chunk
                
                # 解析思考过程和答案
                if "<thinking>" in full_content and not is_in_thinking:
                    is_in_thinking = True
                    thinking_start = full_content.find("<thinking>") + len("<thinking>")
                
                if "</thinking>" in full_content and is_in_thinking:
                    is_in_thinking = False
                    thinking_end = full_content.find("</thinking>")
                    thinking_content = full_content[thinking_start:thinking_end].strip()
                    yield {
                        "event": "thinking",
                        "data": {"content": thinking_content, "done": True}
                    }
                
                if "<answer>" in full_content and not is_in_answer:
                    is_in_answer = True
                    answer_start = full_content.find("<answer>") + len("<answer>")
                
                if "</answer>" in full_content and is_in_answer:
                    answer_end = full_content.find("</answer>")
                    answer_content = full_content[answer_start:answer_end].strip()
                    yield {
                        "event": "answer",
                        "data": {"content": answer_content, "done": True}
                    }
                elif is_in_answer and chunk:
                    yield {
                        "event": "answer_chunk",
                        "data": {"chunk": chunk}
                    }
                elif is_in_thinking and chunk:
                    yield {
                        "event": "thinking_chunk",
                        "data": {"chunk": chunk}
                    }
            
            # 发送完成事件
            final_answer = answer_content or full_content.replace("<thinking>", "").replace("</thinking>", "").replace("<answer>", "").replace("</answer>", "").strip()
            
            yield {
                "event": "done",
                "data": {
                    "thinking": thinking_content,
                    "answer": final_answer,
                    "agent": self.config.name,
                    "role": self.config.role.value
                }
            }
            
        except Exception as e:
            yield {
                "event": "error",
                "data": {"message": str(e)}
            }
    
    def _parse_response(self, response: str) -> tuple:
        """解析响应，提取思考过程和答案"""
        thinking = ""
        answer = response
        
        if "<thinking>" in response and "</thinking>" in response:
            thinking_start = response.find("<thinking>") + len("<thinking>")
            thinking_end = response.find("</thinking>")
            thinking = response[thinking_start:thinking_end].strip()
        
        if "<answer>" in response and "</answer>" in response:
            answer_start = response.find("<answer>") + len("<answer>")
            answer_end = response.find("</answer>")
            answer = response[answer_start:answer_end].strip()
        
        return thinking, answer
