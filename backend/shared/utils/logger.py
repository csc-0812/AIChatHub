"""
日志工具模块
提供统一的日志记录功能
"""
import logging
import sys

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
