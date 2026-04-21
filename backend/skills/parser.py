"""
技能解析器
解析 markdown 格式的技能定义文件
"""
import re
from typing import Dict, Any, Optional


class SkillDefinition:
    """技能定义对象"""
    
    def __init__(self):
        self.name = ""
        self.description = ""
        self.author = ""
        self.version = "1.0.0"
        self.category = "general"
        self.enabled = True
        self.parameters = []
        self.system_prompt = ""
        self.user_prompt = ""
        self.script = ""
        self.actions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "category": self.category,
            "enabled": self.enabled,
            "parameters": self.parameters,
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "script": self.script,
            "actions": self.actions
        }


def parse_skill_markdown(content: str) -> SkillDefinition:
    """
    解析 markdown 格式的技能定义
    
    Markdown 格式示例:
    ```markdown
    # Skill: 技能名称
    
    ## Description
    技能描述
    
    ## Metadata
    - Author: 作者
    - Version: 1.0.0
    - Category: general
    
    ## Parameters
    - name: 参数名
      type: string
      description: 参数描述
      required: true
    
    ## System Prompt
    系统提示词内容
    
    ## User Prompt
    用户提示词模板
    
    ## Script (可选)
    ```python
    # 脚本代码
    ```
    
    ## Actions (可选)
    - action1
    - action2
    ```
    
    Args:
        content: markdown 内容
        
    Returns:
        SkillDefinition 对象
    """
    skill = SkillDefinition()
    
    lines = content.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        if line.startswith('# Skill:'):
            skill.name = line.replace('# Skill:', '').strip()
        elif line.startswith('## '):
            if current_section and section_content:
                _parse_section(skill, current_section, '\n'.join(section_content))
            current_section = line.replace('## ', '').strip()
            section_content = []
        else:
            if current_section:
                section_content.append(line)
    
    if current_section and section_content:
        _parse_section(skill, current_section, '\n'.join(section_content))
    
    return skill


def _parse_section(skill: SkillDefinition, section_name: str, content: str):
    """解析各个 section"""
    content = content.strip()
    
    if section_name == "Description":
        skill.description = content
    
    elif section_name == "Metadata":
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- Author:'):
                skill.author = line.replace('- Author:', '').strip()
            elif line.startswith('- Version:'):
                skill.version = line.replace('- Version:', '').strip()
            elif line.startswith('- Category:'):
                skill.category = line.replace('- Category:', '').strip()
            elif line.startswith('- Enabled:'):
                skill.enabled = line.replace('- Enabled:', '').strip().lower() == 'true'
    
    elif section_name == "Parameters":
        params = []
        lines = content.split('\n')
        current_param = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('- name:'):
                if current_param:
                    params.append(current_param)
                current_param = {"name": line.replace('- name:', '').strip()}
            elif line.startswith('  type:'):
                current_param["type"] = line.replace('  type:', '').strip()
            elif line.startswith('  description:'):
                current_param["description"] = line.replace('  description:', '').strip()
            elif line.startswith('  required:'):
                current_param["required"] = line.replace('  required:', '').strip().lower() == 'true'
            elif line.startswith('  default:'):
                current_param["default"] = line.replace('  default:', '').strip()
        
        if current_param:
            params.append(current_param)
        
        skill.parameters = params
    
    elif section_name == "System Prompt":
        skill.system_prompt = content
    
    elif section_name == "User Prompt":
        skill.user_prompt = content
    
    elif section_name == "Script":
        match = re.search(r'```(\w+)?\n(.+?)```', content, re.DOTALL)
        if match:
            skill.script = match.group(2).strip()
    
    elif section_name == "Actions":
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                skill.actions.append(line[2:])