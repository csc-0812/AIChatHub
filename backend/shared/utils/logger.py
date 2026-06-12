"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import sys
import uuid
from contextvars import ContextVar

# 配置日志格式
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(log_format, date_format))

# 创建根日志记录器
root_logger = logging.getLogger("demo")
root_logger.setLevel(logging.INFO)
root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志记录器"""
    return logging.getLogger(f"demo.{name}")


# 导出常用日志记录器
auth_logger = get_logger("auth")
chat_logger = get_logger("chat")
admin_logger = get_logger("admin")
models_logger = get_logger("models")
llm_logger = get_logger("llm")
agent_logger = get_logger("agent")

# trace_id 上下文变量，用于跨模块追踪单次请求
_trace_id: ContextVar = ContextVar("trace_id", default=None)


def set_trace_id(trace_id: str = None) -> str:
    """设置当前请求的 trace_id，若未提供则自动生成"""
    if trace_id is None:
        trace_id = str(uuid.uuid4())[:8]
    _trace_id.set(trace_id)
    return trace_id


def get_trace_id() -> str:
    """获取当前请求的 trace_id"""
    return _trace_id.get()


def clear_trace_id():
    """清除 trace_id"""
    _trace_id.set(None)


def log_with_trace(logger: logging.Logger, level: int, msg: str, *args, **kwargs):
    """带 trace_id 的日志记录"""
    trace_id = get_trace_id()
    prefix = f"[trace={trace_id}] " if trace_id else ""
    logger.log(level, f"{prefix}{msg}", *args, **kwargs)
