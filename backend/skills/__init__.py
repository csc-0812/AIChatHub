"""
技能模块
支持 markdown-based 的技能定义（类似 OpenClaw）
"""
from .loader import (
    load_skill, load_skills_from_directory, get_skill, get_all_skills, 
    create_skill_template, create_skill, update_skill, delete_skill, toggle_skill
)
from .executor import execute_skill
from .parser import parse_skill_markdown

__all__ = [
    "load_skill",
    "load_skills_from_directory",
    "get_skill",
    "get_all_skills",
    "create_skill_template",
    "create_skill",
    "update_skill",
    "delete_skill",
    "toggle_skill",
    "execute_skill",
    "parse_skill_markdown"
]