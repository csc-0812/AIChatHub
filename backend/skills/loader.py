"""
技能加载器
从文件或目录加载技能定义
"""
import os
from typing import Dict, List, Optional
from .parser import parse_skill_markdown, SkillDefinition


_skills_cache: Dict[str, SkillDefinition] = {}


def load_skill(file_path: str) -> Optional[SkillDefinition]:
    """
    从文件加载技能定义
    
    Args:
        file_path: markdown 文件路径
        
    Returns:
        SkillDefinition 对象，如果加载失败返回 None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        skill = parse_skill_markdown(content)
        
        if skill.name:
            _skills_cache[skill.name] = skill
            return skill
        
        return None
    except Exception as e:
        print(f"加载技能失败 {file_path}: {e}")
        return None


def load_skills_from_directory(directory: str) -> List[SkillDefinition]:
    """
    从目录加载所有技能定义
    
    Args:
        directory: 技能目录路径
        
    Returns:
        技能定义列表
    """
    skills = []
    
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
        return skills
    
    for filename in os.listdir(directory):
        if filename.endswith('.md'):
            file_path = os.path.join(directory, filename)
            skill = load_skill(file_path)
            if skill:
                skills.append(skill)
    
    return skills


def get_skill(name: str) -> Optional[SkillDefinition]:
    """获取已加载的技能"""
    return _skills_cache.get(name)


def get_all_skills() -> List[SkillDefinition]:
    """获取所有已加载的技能"""
    return list(_skills_cache.values())


def create_skill_template(directory: str, skill_name: str) -> bool:
    """
    创建技能模板文件
    
    Args:
        directory: 目标目录
        skill_name: 技能名称
        
    Returns:
        是否创建成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, f"{skill_name.lower().replace(' ', '_')}.md")
        
        template = f"""# Skill: {skill_name}

## Description
{skill_name} 的描述信息

## Metadata
- Author: 
- Version: 1.0.0
- Category: general
- Enabled: true

## Parameters
- name: input
  type: string
  description: 输入内容
  required: true

## System Prompt
你是一个专业的助手，擅长处理 {skill_name} 相关任务。

## User Prompt
请处理以下请求：
{{input}}

## Script (可选)
```python
# 在此添加 Python 脚本
# 可用变量: parameters (参数字典), context (上下文信息)
# 返回值将作为技能执行结果

result = f"执行 {skill_name}，参数: {{parameters}}"
return result
```

## Actions (可选)
- action1
- action2
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        return True
    except Exception as e:
        print(f"创建技能模板失败: {e}")
        return False


def create_skill(
    name: str,
    description: str,
    category: str = "general",
    parameters: List[dict] = None,
    system_prompt: str = "",
    user_prompt: str = "",
    script: str = ""
) -> SkillDefinition:
    """
    创建新技能（内存中）
    
    Args:
        name: 技能名称
        description: 技能描述
        category: 技能分类
        parameters: 参数列表
        system_prompt: 系统提示词
        user_prompt: 用户提示词
        script: Python脚本
        
    Returns:
        创建的技能定义
    """
    if not name:
        raise ValueError("技能名称不能为空")
    
    if get_skill(name):
        raise ValueError(f"技能 '{name}' 已存在")
    
    skill = SkillDefinition()
    skill.name = name
    skill.description = description
    skill.category = category
    skill.enabled = True
    skill.parameters = parameters or []
    skill.system_prompt = system_prompt
    skill.user_prompt = user_prompt
    skill.script = script
    
    _skills_cache[name] = skill
    return skill


def update_skill(
    name: str,
    new_name: str = None,
    description: str = None,
    category: str = None,
    parameters: List[dict] = None,
    system_prompt: str = None,
    user_prompt: str = None,
    script: str = None
) -> Optional[SkillDefinition]:
    """
    更新技能（内存中）
    
    Args:
        name: 当前技能名称
        new_name: 新技能名称
        description: 新描述
        category: 新分类
        parameters: 新参数列表
        system_prompt: 新系统提示词
        user_prompt: 新用户提示词
        script: 新脚本
        
    Returns:
        更新后的技能定义，如果不存在返回 None
    """
    skill = get_skill(name)
    if not skill:
        return None
    
    if new_name and new_name != name:
        if get_skill(new_name):
            raise ValueError(f"技能 '{new_name}' 已存在")
        del _skills_cache[name]
        skill.name = new_name
    
    if description is not None:
        skill.description = description
    
    if category is not None:
        skill.category = category
    
    if parameters is not None:
        skill.parameters = parameters
    
    if system_prompt is not None:
        skill.system_prompt = system_prompt
    
    if user_prompt is not None:
        skill.user_prompt = user_prompt
    
    if script is not None:
        skill.script = script
    
    _skills_cache[skill.name] = skill
    return skill


def delete_skill(name: str) -> bool:
    """
    删除技能（内存中）
    
    Args:
        name: 技能名称
        
    Returns:
        是否删除成功
    """
    if name in _skills_cache:
        del _skills_cache[name]
        return True
    return False


def toggle_skill(name: str) -> bool:
    """
    切换技能启用/禁用状态（内存中）
    
    Args:
        name: 技能名称
        
    Returns:
        是否切换成功
    """
    skill = get_skill(name)
    if not skill:
        return False
    
    skill.enabled = not skill.enabled
    return True