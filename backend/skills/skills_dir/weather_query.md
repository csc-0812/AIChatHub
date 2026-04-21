# Skill: WeatherQuery

## Description
查询指定城市的天气信息

## Metadata
- Author: System
- Version: 1.0.0
- Category: general
- Enabled: true

## Parameters
- name: city
  type: string
  description: 城市名称
  required: true
- name: days
  type: int
  description: 查询天数
  required: false
  default: 1

## System Prompt
你是一个专业的天气查询助手，提供准确的天气信息。

## User Prompt
请查询 {city} 未来 {days} 天的天气情况。

## Script
```python
city = parameters.get('city', '')
days = parameters.get('days', 1)

result = f"天气查询结果：\n城市: {city}\n今日天气: 晴转多云\n温度: 25°C\n湿度: 60%\n未来{days}天预报: 天气良好"
return result
```

## Actions
- 查询天气API
- 解析天气数据
- 返回格式化结果