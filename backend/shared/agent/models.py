"""
Agent 数据模型
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """智能体角色类型"""
    COORDINATOR = "coordinator"      # 协调者，负责任务分配
    RESEARCHER = "researcher"        # 研究者，负责信息收集
    ANALYZER = "analyzer"            # 分析者，负责数据分析
    WRITER = "writer"                # 写作者，负责内容生成
    REVIEWER = "reviewer"            # 审查者，负责质量检查
    CUSTOM = "custom"                # 自定义角色


class AgentConfig(BaseModel):
    """智能体配置"""
    role: AgentRole = AgentRole.COORDINATOR
    name: str = "Assistant"
    description: str = ""
    system_prompt: str = """
你是一个 helpful 的AI助手。在回答问题时，请先展示你的思考过程，
然后用 <answer> 标签包裹最终答案。

格式如下：
<thinking>
1. 分析问题...
2. 考虑可能的方案...
3. 评估最佳答案...
</thinking>

<answer>
最终答案内容
</answer>
"""
    temperature: float = 0.7
    max_tokens: int = 2048
    enable_thinking: bool = True
    context_window: int = 10
    tools: List[str] = Field(default_factory=list)


class AgentMessage(BaseModel):
    """智能体消息"""
    role: str                                    # user/assistant/system
    content: str
    agent_name: Optional[str] = None            # 发送消息的智能体名称
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """智能体响应"""
    content: str
    thinking: Optional[str] = None
    agent_name: str
    role: AgentRole
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TeamConfig(BaseModel):
    """团队配置"""
    name: str = "Default Team"
    description: str = ""
    agents: List[AgentConfig] = Field(default_factory=list)
    workflow: str = "sequential"                 # sequential/parallel/consensus
    max_rounds: int = 5                          # 最大对话轮数
