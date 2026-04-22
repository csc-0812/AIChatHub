"""
Router 级别工具
这些工具可以被 RouterAgent 直接调用
"""
from langchain_core.tools import tool


@tool("calculator", description="用于执行数学计算，支持加减乘除等基本运算")
def calculator(expression: str) -> str:
    """
    计算器工具 - 执行数学计算
    
    Args:
        expression: 数学表达式，如 '2 + 3 * 4'
        
    Returns:
        计算结果字符串
    """
    try:
        result = eval(expression)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


ROUTER_TOOLS = [calculator]