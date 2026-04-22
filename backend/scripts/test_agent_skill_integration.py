"""
测试融合方案：LangChain Agent + OpenClaw Skill

测试内容：
1. RouterAgent 使用 LangChain AgentExecutor
2. 子 Agent 作为工具调用
3. OpenClaw 技能作为工具调用
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import RouterAgent, AgentConfig, AgentRole


async def test_router_with_langchain():
    """测试路由智能体使用 LangChain AgentExecutor"""
    print("=== 测试路由智能体 (LangChain 集成) ===")
    
    router_agent = RouterAgent()
    
    print("\n1. 查看智能体配置:")
    config = router_agent.config
    print(f"路由智能体: {config.name} ({config.role.value})")
    
    print("\n2. 查看可用资源:")
    resources = router_agent.get_available_resources()
    print(f"可用工具数量: {len(resources.get('tools', []))}")
    for tool in resources.get('tools', []):
        print(f"  - {tool['name']}: {tool['description'][:30]}...")
    
    print(f"\n可用子智能体: {[a['name'] for a in resources.get('agents', [])]}")
    
    print("\n3. 测试直接回答:")
    response = await router_agent.chat("你好，介绍一下你自己")
    print(f"   响应内容: {response.content}")
    print(f"   思考过程: {response.thinking}")


async def test_sub_agent_as_tool():
    """测试子 Agent 作为工具调用"""
    print("\n=== 测试子 Agent 作为工具 ===")
    
    router_agent = RouterAgent()
    
    print("\n1. 添加自定义子智能体:")
    custom_config = AgentConfig(
        role=AgentRole.CUSTOM,
        name="MathExpert",
        description="数学专家，擅长解决数学问题",
        system_prompt="你是一个数学专家，擅长解决各种数学问题。"
    )
    agent_id = router_agent.add_sub_agent(custom_config)
    print(f"   已添加智能体 MathExpert，ID: {agent_id}")
    
    print("\n2. 查看更新后的资源:")
    resources = router_agent.get_available_resources()
    tool_names = [t['name'] for t in resources.get('tools', [])]
    print(f"   工具列表: {tool_names}")


async def test_skill_as_tool():
    """测试 OpenClaw 技能作为工具调用"""
    print("\n=== 测试 OpenClaw 技能作为工具 ===")
    
    print("\n1. 加载技能作为工具:")
    from skills import load_skills_as_tools
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills", "skills_dir")
    skill_tools = load_skills_as_tools(skills_dir)
    print(f"   已加载技能工具数量: {len(skill_tools)}")
    for tool in skill_tools:
        print(f"   - {tool.name}: {tool.description}")
    
    print("\n2. 测试技能工具执行:")
    if skill_tools:
        weather_tool = next((t for t in skill_tools if 'weather' in t.name.lower()), None)
        if weather_tool:
            result = await weather_tool.arun(city="北京")
            print(f"   天气查询结果: {result}")


if __name__ == "__main__":
    asyncio.run(test_router_with_langchain())
    asyncio.run(test_sub_agent_as_tool())
    asyncio.run(test_skill_as_tool())