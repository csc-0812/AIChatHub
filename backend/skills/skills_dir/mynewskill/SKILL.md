---
name: MyNewSkill
description: MyNewSkill 的描述信息
version: 1.0.0
category: general
enabled: true
---

# MyNewSkill

## Description
MyNewSkill 的详细描述

## Parameters
- name: input
  type: string
  description: 输入内容
  required: true

## System Prompt
你是一个专业的助手，擅长处理 MyNewSkill 相关任务。

## User Prompt
请处理以下请求：
{input}

## Script
```python
# 在此添加 Python 脚本
# 可用变量: parameters (参数字典), skill_dir (技能目录路径)
# 返回值: result

result = f"执行 MyNewSkill，参数: {parameters}"
```
