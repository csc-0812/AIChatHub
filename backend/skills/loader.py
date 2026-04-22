"""
技能加载器 - 基于 OpenClaw SDK

从文件或目录加载 OpenClaw Skill 定义。
支持 OpenClaw 标准目录结构：每个技能一个文件夹，包含 SKILL.md 文件。
"""
import os
import re
from typing import Dict, List, Optional

try:
    from openclaw import Skill
except ImportError:
    class Skill:
        def __init__(self):
            self.name = ""
            self.description = ""
            self.version = "1.0.0"
            self.category = "general"
            self.enabled = True
            self.parameters = []
            self.system_prompt = ""
            self.user_prompt = ""
            self.script = ""
            self.skill_dir = ""
        
        @classmethod
        def from_file(cls, file_path: str):
            skill = cls()
            skill.skill_dir = os.path.dirname(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.startswith('---'):
                    end_idx = content.find('\n---\n')
                    if end_idx > 0:
                        yaml_content = content[4:end_idx]
                        content = content[end_idx+5:]
                        
                        for line in yaml_content.split('\n'):
                            line = line.strip()
                            if line.startswith('name:'):
                                skill.name = line[5:].strip()
                            elif line.startswith('description:'):
                                skill.description = line[12:].strip()
                            elif line.startswith('version:'):
                                skill.version = line[8:].strip()
                            elif line.startswith('category:'):
                                skill.category = line[10:].strip()
                            elif line.startswith('enabled:'):
                                skill.enabled = line[9:].strip().lower() == 'true'
                
                if not skill.name:
                    match = re.search(r'^#\s*([^\n]+)', content)
                    if match:
                        skill.name = match.group(1).strip()
                
                params_match = re.search(r'##\s*Parameters\s*\n([\s\S]*?)(?=\n##\s|$)', content)
                if params_match:
                    params_content = params_match.group(1)
                    params = []
                    current_param = {}
                    for line in params_content.split('\n'):
                        line = line.strip()
                        if line.startswith('- name:'):
                            if current_param:
                                params.append(current_param)
                            current_param = {'name': line[7:].strip()}
                        elif line.startswith('type:'):
                            current_param['type'] = line[5:].strip()
                        elif line.startswith('description:'):
                            current_param['description'] = line[12:].strip()
                        elif line.startswith('required:'):
                            current_param['required'] = line[9:].strip().lower() == 'true'
                        elif line.startswith('default:'):
                            current_param['default'] = line[8:].strip()
                    if current_param:
                        params.append(current_param)
                    skill.parameters = params
                
                sys_prompt_match = re.search(r'##\s*System Prompt\s*\n([\s\S]*?)(?=\n##\s|$)', content)
                if sys_prompt_match:
                    skill.system_prompt = sys_prompt_match.group(1).strip()
                
                user_prompt_match = re.search(r'##\s*User Prompt\s*\n([\s\S]*?)(?=\n##\s|$)', content)
                if user_prompt_match:
                    skill.user_prompt = user_prompt_match.group(1).strip()
                
                script_match = re.search(r'```python\s*\n([\s\S]*?)\n```', content)
                if script_match:
                    skill.script = script_match.group(1)
            
            except Exception as e:
                print(f"解析技能文件失败 {file_path}: {e}")
            
            return skill
        
        async def execute(self, parameters):
            if self.script:
                exec_globals = {'parameters': parameters, 'result': '', 'skill_dir': self.skill_dir}
                try:
                    exec(self.script, exec_globals)
                    return {'success': True, 'output': exec_globals.get('result', '执行完成')}
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            return {'success': True, 'output': f"技能 '{self.name}' 执行成功"}


_skills_cache: Dict[str, Skill] = {}


def load_skill(file_path: str) -> Optional[Skill]:
    """
    从文件加载技能定义
    
    Args:
        file_path: SKILL.md 文件路径
        
    Returns:
        Skill 对象，如果加载失败返回 None
    """
    try:
        skill = Skill.from_file(file_path)
        
        if skill.name:
            _skills_cache[skill.name] = skill
            return skill
        
        return None
    except Exception as e:
        print(f"加载技能失败 {file_path}: {e}")
        return None


def load_skills_from_directory(directory: str) -> List[Skill]:
    """
    从目录加载所有技能定义
    
    OpenClaw 标准结构：每个技能一个文件夹，包含 SKILL.md 文件
    skills_dir/
    ├── weather_query/
    │   └── SKILL.md
    ├── pdf_analyzer/
    │   └── SKILL.md
    └── ...
    
    Args:
        directory: 技能目录路径
        
    Returns:
        技能定义列表
    """
    skills = []
    
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)
        return skills
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            skill_file = os.path.join(item_path, 'SKILL.md')
            if os.path.isfile(skill_file):
                skill = load_skill(skill_file)
                if skill:
                    skills.append(skill)
    
    return skills


def get_skill(name: str) -> Optional[Skill]:
    """获取已加载的技能"""
    return _skills_cache.get(name)


def get_all_skills() -> List[Skill]:
    """获取所有已加载的技能"""
    return list(_skills_cache.values())


def create_skill_template(directory: str, skill_name: str) -> bool:
    """
    创建技能模板文件（OpenClaw 标准格式）
    
    Args:
        directory: 目标目录
        skill_name: 技能名称
        
    Returns:
        是否创建成功
    """
    try:
        os.makedirs(directory, exist_ok=True)
        
        skill_dir_name = skill_name.lower().replace(' ', '_').replace('-', '_')
        skill_dir = os.path.join(directory, skill_dir_name)
        os.makedirs(skill_dir, exist_ok=True)
        
        file_path = os.path.join(skill_dir, 'SKILL.md')
        
        template = f"""---
name: {skill_name}
description: {skill_name} 的描述信息
version: 1.0.0
category: general
enabled: true
---

# {skill_name}

## Description
{skill_name} 的详细描述

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

## Script
```python
# 在此添加 Python 脚本
# 可用变量: parameters (参数字典), skill_dir (技能目录路径)
# 返回值: result

result = f"执行 {skill_name}，参数: {{parameters}}"
```
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
) -> Skill:
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
    
    skill = Skill()
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
) -> Optional[Skill]:
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