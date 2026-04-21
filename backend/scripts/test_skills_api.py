"""
技能API测试脚本
验证技能管理API是否正常工作
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills import (
    load_skills_from_directory, get_all_skills, 
    create_skill, get_skill, update_skill, delete_skill, toggle_skill
)
import asyncio
from skills.executor import execute_skill


def test_skill_loading():
    """测试技能加载"""
    print("=== 测试技能加载 ===")
    
    # 加载技能
    skills_dir = os.path.join(os.path.dirname(__file__), "..", "skills", "skills_dir")
    skills = load_skills_from_directory(skills_dir)
    
    print(f"已加载技能数量: {len(skills)}")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")
    
    return skills


def test_skill_operations():
    """测试技能操作"""
    print("\n=== 测试技能操作 ===")
    
    # 创建技能
    skill = create_skill(
        name="TestSkill",
        description="测试技能",
        category="general",
        parameters=[
            {"name": "input", "type": "string", "description": "输入内容", "required": True}
        ],
        script="result = f'测试技能执行，输入: {parameters.get(\"input\", \"\")}'\nreturn result"
    )
    print(f"创建技能: {skill.name}")
    
    # 获取技能
    retrieved = get_skill("TestSkill")
    print(f"获取技能: {retrieved.name}")
    
    # 更新技能
    updated = update_skill(
        name="TestSkill",
        description="更新后的测试技能",
        category="productivity"
    )
    print(f"更新技能: {updated.name}, 描述: {updated.description}")
    
    # 切换状态
    toggle_skill("TestSkill")
    toggled = get_skill("TestSkill")
    print(f"切换状态后: enabled={toggled.enabled}")
    
    # 删除技能
    delete_skill("TestSkill")
    deleted = get_skill("TestSkill")
    print(f"删除后获取: {deleted}")


async def test_skill_execution():
    """测试技能执行"""
    print("\n=== 测试技能执行 ===")
    
    # 创建一个可执行的技能
    create_skill(
        name="Calculator",
        description="简单计算器",
        category="general",
        parameters=[
            {"name": "num1", "type": "int", "description": "第一个数字", "required": True},
            {"name": "num2", "type": "int", "description": "第二个数字", "required": True},
            {"name": "operation", "type": "string", "description": "操作: add, subtract, multiply, divide", "required": True}
        ],
        script="""
num1 = parameters.get('num1', 0)
num2 = parameters.get('num2', 0)
operation = parameters.get('operation', 'add')

if operation == 'add':
    result = num1 + num2
elif operation == 'subtract':
    result = num1 - num2
elif operation == 'multiply':
    result = num1 * num2
elif operation == 'divide':
    if num2 == 0:
        result = '错误: 除数不能为零'
    else:
        result = num1 / num2
else:
    result = f'未知操作: {operation}'

return f'{num1} {operation} {num2} = {result}'
"""
    )
    
    # 执行技能
    result = await execute_skill("Calculator", num1=10, num2=5, operation="add")
    print(f"执行加法: 10 + 5 = {result.output}")
    
    result = await execute_skill("Calculator", num1=10, num2=5, operation="multiply")
    print(f"执行乘法: 10 * 5 = {result.output}")
    
    # 清理
    delete_skill("Calculator")


if __name__ == "__main__":
    test_skill_loading()
    test_skill_operations()
    asyncio.run(test_skill_execution())
    print("\n=== 所有测试完成 ===")