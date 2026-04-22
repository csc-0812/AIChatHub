"""
技能API测试脚本
测试技能加载、执行和管理功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.loader import (
    load_skills_from_directory,
    get_all_skills,
    get_skill,
    create_skill,
    update_skill,
    delete_skill,
    toggle_skill,
    create_skill_template
)
from skills.executor import execute_skill


async def test_load_skills():
    """测试加载技能"""
    print("=== 测试加载技能 ===")
    
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "skills_dir")
    skills = load_skills_from_directory(skills_dir)
    
    print(f"从目录加载的技能数量: {len(skills)}")
    for skill in skills:
        print(f"\n技能名称: {skill.name}")
        print(f"描述: {skill.description}")
        print(f"版本: {skill.version}")
        print(f"分类: {skill.category}")
        print(f"启用: {skill.enabled}")
        print(f"参数: {skill.parameters}")
        print(f"技能目录: {skill.skill_dir}")


async def test_execute_skill():
    """测试执行技能"""
    print("\n=== 测试执行技能 ===")
    
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "skills_dir")
    load_skills_from_directory(skills_dir)
    
    result = await execute_skill("WeatherQuery", city="北京", days=3)
    print(f"执行结果 - 成功: {result.success}")
    if result.success:
        print(f"输出内容:\n{result.output}")
    else:
        print(f"错误信息: {result.error}")


async def test_skill_management():
    """测试技能管理功能"""
    print("\n=== 测试技能管理 ===")
    
    print("\n1. 创建技能（内存中）:")
    skill = create_skill(
        name="TestSkill",
        description="测试技能",
        category="test",
        parameters=[{"name": "input", "type": "string", "required": True}]
    )
    print(f"   创建成功: {skill.name}")
    
    print("\n2. 获取技能:")
    skill = get_skill("TestSkill")
    print(f"   获取成功: {skill.name}")
    
    print("\n3. 更新技能:")
    updated = update_skill("TestSkill", description="更新后的描述")
    print(f"   更新成功: {updated.description}")
    
    print("\n4. 切换状态:")
    toggle_skill("TestSkill")
    skill = get_skill("TestSkill")
    print(f"   当前状态: {skill.enabled}")
    
    print("\n5. 删除技能:")
    success = delete_skill("TestSkill")
    print(f"   删除成功: {success}")
    
    print("\n6. 验证删除:")
    skill = get_skill("TestSkill")
    print(f"   技能是否存在: {skill is not None}")


async def test_create_template():
    """测试创建技能模板"""
    print("\n=== 测试创建技能模板 ===")
    
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "skills_dir")
    success = create_skill_template(skills_dir, "MyNewSkill")
    print(f"创建模板成功: {success}")
    
    template_path = os.path.join(skills_dir, "my_new_skill", "SKILL.md")
    if os.path.exists(template_path):
        print(f"模板文件已创建: {template_path}")


if __name__ == "__main__":
    asyncio.run(test_load_skills())
    asyncio.run(test_execute_skill())
    asyncio.run(test_skill_management())
    asyncio.run(test_create_template())