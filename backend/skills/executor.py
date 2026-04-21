"""
技能执行器
执行已加载的技能
"""
import asyncio
import time
from typing import Dict, Any, Optional
from .parser import SkillDefinition
from .loader import get_skill


class SkillExecutionResult:
    """技能执行结果"""
    
    def __init__(self):
        self.success = False
        self.output = None
        self.error = None
        self.skill_name = ""
        self.execution_time = 0.0
        self.metadata: Dict[str, Any] = {}


async def execute_skill(skill_name: str, **kwargs) -> SkillExecutionResult:
    """
    执行指定技能
    
    Args:
        skill_name: 技能名称
        **kwargs: 技能参数
        
    Returns:
        SkillExecutionResult 对象
    """
    result = SkillExecutionResult()
    result.skill_name = skill_name
    start_time = time.time()
    
    skill = get_skill(skill_name)
    if not skill:
        result.error = f"技能 '{skill_name}' 未找到"
        return result
    
    if not skill.enabled:
        result.error = f"技能 '{skill_name}' 已禁用"
        return result
    
    try:
        await _validate_parameters(skill, kwargs)
        
        if skill.script:
            output = await _execute_script(skill, kwargs)
        elif skill.user_prompt:
            output = await _execute_prompt(skill, kwargs)
        else:
            output = f"技能 '{skill_name}' 执行成功"
        
        result.success = True
        result.output = output
        
    except Exception as e:
        result.error = str(e)
    
    result.execution_time = time.time() - start_time
    return result


async def _validate_parameters(skill: SkillDefinition, parameters: Dict[str, Any]) -> None:
    """验证参数"""
    for param in skill.parameters:
        name = param.get("name")
        required = param.get("required", True)
        
        if required and name not in parameters:
            raise ValueError(f"缺少必需参数: {name}")


async def _execute_script(skill: SkillDefinition, parameters: Dict[str, Any]) -> Any:
    """执行脚本"""
    try:
        exec_globals = {
            'parameters': parameters,
            'context': {}
        }
        
        script_lines = skill.script.split('\n')
        indented_lines = ['    ' + line for line in script_lines]
        indented_script = '\n'.join(indented_lines)
        
        script_wrapper = f'def _skill_execution_func():\n{indented_script}\n\n_result = _skill_execution_func()'
        
        exec(script_wrapper, exec_globals)
        
        if '_result' in exec_globals:
            return exec_globals['_result']
        if 'result' in exec_globals:
            return exec_globals['result']
        return f"脚本执行完成"
    except Exception as e:
        raise RuntimeError(f"脚本执行失败: {e}")


async def _execute_prompt(skill: SkillDefinition, parameters: Dict[str, Any]) -> str:
    """执行提示词模板"""
    try:
        user_prompt = skill.user_prompt.format(**parameters)
        return f"系统提示词已应用\n\n用户提示:\n{user_prompt}"
    except KeyError as e:
        raise ValueError(f"提示词模板缺少参数: {e}")