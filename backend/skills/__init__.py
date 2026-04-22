"""
技能模块 - 基于 OpenClaw SDK

使用 OpenClaw SDK 实现技能加载和执行，
支持将 OpenClaw Skills 作为 LangChain Tool 使用。
"""
from .loader import (
    load_skill, load_skills_from_directory, get_skill, get_all_skills,
    create_skill_template, create_skill, update_skill, delete_skill, toggle_skill
)
from .executor import execute_skill

try:
    from .langchain_adapter import (
        OpenClawSkillTool, IndividualSkillTool, load_skills_as_tools, get_skill_tool
    )
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
        "OpenClawSkillTool",
        "IndividualSkillTool",
        "load_skills_as_tools",
        "get_skill_tool"
    ]
except ImportError:
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
        "execute_skill"
    ]