# 后端服务

## 项目结构

```
backend/
├── api/             # API 路由层
│   └── v1/          # API 版本 v1
├── modules/         # 业务模块
│   ├── auth/        # 认证模块
│   ├── chat/        # 聊天模块
│   ├── admin/       # 管理员模块
│   └── models_config/ # 模型配置模块
├── shared/          # 共享组件
│   ├── agent/       # 智能体模块
│   └── utils/       # 工具类
├── uploads/         # 上传文件目录
├── logs/            # 日志目录
├── scripts/         # 脚本目录
├── main.py          # 应用入口
└── pyproject.toml   # 依赖配置
```

## 功能特性

- 用户认证（注册/登录/JWT）
- 会话管理（创建/列表/删除/重命名/清空）
- 流式聊天（SSE）
- 智能体架构（支持扩展多角色协作）
- 管理员功能（用户管理）
- 模型配置管理
- 文件上传功能

## 技术栈

- FastAPI - Web 框架
- Redis - 数据存储
- LangChain - LLM 集成
- JWT - 身份认证
- Pydantic - 数据验证
- PyYAML - 配置管理

## 快速开始

### 环境要求
- Python 3.14+
- Redis 服务器

### 安装依赖

```bash
uv sync
```

### 启动服务

```bash
uv run uvicorn main:app --reload
```

服务将在 http://localhost:8000 运行

## API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 配置

配置文件位于 `config/config.yaml`，包含以下配置项：

- LLM 配置（API 密钥、模型、温度等）
- 数据库配置（Redis 连接信息）
- 认证配置（JWT 密钥）

## 脚本

### 创建超级管理员

```bash
uv run python scripts/make_super_admin.py
```

## 开发说明

### 代码规范
- 使用 PEP 8 编码规范
- 使用类型提示
- 使用 FastAPI 的依赖注入系统

### 目录结构
- `api/` - API 路由层，处理 HTTP 请求
- `modules/` - 业务模块，包含具体业务逻辑
- `shared/` - 共享组件，包含工具类和智能体
- `scripts/` - 脚本目录，包含维护脚本
