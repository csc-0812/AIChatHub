"""
路由功能测试脚本
测试 RouterAgent 作为路由中心的功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import RouterAgent
from skills import load_skills_from_directory, execute_skill, get_all_skills


async def test_router_agent():
    """测试路由智能体"""
    print("=== 测试路由智能体 ===")
    
    router_agent = RouterAgent()
    
    print("\n1. 查看智能体配置:")
    config = router_agent.config
    print(f"路由智能体: {config.name} ({config.role.value})")
    
    print("\n2. 查看可用资源:")
    resources = router_agent.get_available_resources()
    print(f"可用工具: {[t['name'] for t in resources.get('tools', [])]}")
    print(f"可用子智能体: {[a['name'] for a in resources.get('agents', [])]}")
    
    print("\n3. 测试对话:")
    response = await router_agent.chat("你好")
    print(f"   响应内容: {response.content}")


async def test_skill_system():
    """测试技能系统"""
    print("\n=== 测试技能系统 ===")
    
    load_skills_from_directory("backend/skills/skills_dir")
    skills = get_all_skills()
    print(f"已加载技能数量: {len(skills)}")
    for skill in skills:
        print(f"  - {skill.name}: {skill.description}")
    
    print("\n测试执行天气查询技能:")
    result = await execute_skill("WeatherQuery", city="北京", days=3)
    print(f"  成功: {result.success}")
    print(f"  输出:\n{result.output}")
    if result.error:
        print(f"  错误: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_router_agent())
    asyncio.run(test_skill_system())