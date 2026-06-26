# 后端服务

基于 **FastAPI + LangGraph** 的智能聊天后端，为「计划一体化平台」提供 AI 助手 API。

## 项目结构

```
backend/
├── api/
│   ├── __init__.py
│   └── v1/__init__.py         # API v1 路由聚合
├── modules/                   # 业务模块
│   ├── auth/                  # 认证模块（注册/登录/JWT）
│   │   ├── models.py          # 数据模型
│   │   ├── routers.py         # 路由处理
│   │   └── services.py        # 业务逻辑
│   ├── chat/                  # 聊天模块（核心）
│   │   ├── models.py          # 会话/消息数据模型
│   │   ├── routers.py         # 流式聊天 + 会话 CRUD
│   │   ├── services.py        # SSE 流式响应生成
│   │   └── session_manager.py # Redis 会话 + Agent 管理
│   ├── admin/                 # 管理员模块（用户管理）
│   │   ├── models.py
│   │   ├── routers.py
│   │   └── services.py
│   └── models_config/         # 模型配置模块（动态 LLM 切换）
│       ├── models.py
│       ├── routers.py
│       └── services.py
├── shared/
│   ├── agent/                 # LangGraph 智能体核心
│   │   ├── __init__.py        # 统一导出
│   │   ├── models.py          # Agent 数据模型
│   │   ├── base_agent.py      # 基础智能体（流式 + 思考过程解析）
│   │   ├── router_agent.py    # LangGraph RouterAgent（工具路由）
│   │   ├── prompts.py         # 系统提示词（计划一体化平台）
│   │   ├── tools.py           # 报表/推演/根因三大工具
│   │   ├── tools_data.py      # 模拟制造数据生成器
│   │   └── middleware.py      # 日志 + 上下文摘要中间件
│   └── utils/                 # 共享工具类
│       ├── config_loader.py   # YAML 配置加载器（单例）
│       ├── llm_client.py      # LangChain LLM 客户端封装
│       ├── redis_client.py    # Redis 客户端
│       ├── auth_utils.py      # JWT 工具
│       ├── file_handler.py    # 文件上传处理
│       └── logger.py          # 日志工具
├── scripts/
│   └── make_super_admin.py    # 创建超级管理员
├── uploads/                   # 上传文件目录
├── logs/                      # 日志目录
├── main.py                    # FastAPI 应用入口
├── Dockerfile                 # 后端镜像构建文件
├── pyproject.toml             # Python 依赖配置
└── uv.lock                    # 依赖版本锁定
```

## 功能特性

- **用户认证** — 注册/登录/JWT Token，支持角色体系和挤出登录
- **会话管理** — 会话的完整 CRUD，消息持久化到 Redis
- **流式聊天** — SSE (Server-Sent Events) 实时推送，支持 `<thinking>` 思考过程展示
- **LangGraph 智能体** — RouterAgent 根据用户意图自动路由到对应工具
  - 报表生成：产能分析、进度跟踪、物料需求、质量分析
  - 结果推演：产能调整、订单插单、物料延迟、资源调配
  - 根因分析：工期延误、产能瓶颈、物料短缺、质量波动
- **上下文记忆** — 可配置历史消息窗口长度
- **文件上传** — 支持图片和文档上传
- **管理员功能** — 用户管理（角色编辑/禁用/强制下线）
- **模型动态配置** — 运行时添加/切换 LLM 模型，无需重启

## 技术栈

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架，自动生成 Swagger/ReDoc API 文档 |
| LangChain + LangGraph | LLM 集成 + Agent 状态图编排 |
| Redis | 数据存储（用户/会话/消息/配置） |
| JWT (python-jose) | 无状态身份认证 |
| Pydantic | 数据模型验证 |
| PyYAML | 配置文件解析 |
| uv | Python 包管理 |

## 快速开始

### 环境要求

- Python 3.14+
- Redis 服务器（默认端口 6379）

### 1. 配置

编辑项目根目录 `config/config.yaml`，确保 LLM API Key 和 Redis 连接信息正确。也可以通过环境变量覆盖：

| 环境变量 | 说明 |
|----------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `REDIS_HOST` | Redis 主机地址 |
| `REDIS_PORT` | Redis 端口 |

### 2. 安装依赖

```bash
uv sync
```

### 3. 启动服务

```bash
uv run uvicorn main:app --reload
```

服务运行在 http://localhost:8000

### 4. 创建超级管理员

```bash
uv run python scripts/make_super_admin.py
```

## API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs — 交互式 API 文档
- **ReDoc**: http://localhost:8000/redoc — 结构化文档

### 主要 API 端点

#### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/register` | 用户注册 |
| `POST` | `/login` | 用户登录，返回 JWT Token |
| `GET` | `/me` | 获取当前用户信息 |

#### 聊天 `/api/v1/chat`

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/sessions` | 创建新会话 |
| `GET` | `/sessions` | 获取会话列表 |
| `GET` | `/sessions/{id}` | 获取会话详情（含消息历史） |
| `DELETE` | `/sessions/{id}` | 删除会话 |
| `PUT` | `/sessions/{id}/rename` | 重命名会话 |
| `POST` | `/sessions/{id}/clear` | 清空会话消息 |
| `POST` | `/stream` | SSE 流式聊天 |

#### 管理员 `/api/v1/admin`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/users` | 用户列表（分页+搜索） |
| `PUT` | `/users/{id}` | 更新用户角色/状态 |
| `DELETE` | `/users/{id}` | 删除用户 |

#### 模型配置 `/api/v1/models`

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 模型列表 |
| `POST` | `/` | 添加模型配置 |
| `PUT` | `/{id}` | 更新模型配置 |
| `DELETE` | `/{id}` | 删除模型配置 |

## 架构详解

### RouterAgent 工作流程

```
用户消息
  │
  ▼
RouterAgent (LangGraph)
  │
  ├── 意图识别
  │     ├── 报表查询 → generate_plan_report()
  │     ├── 推演分析 → simulate_plan_scenario()
  │     └── 根因分析 → analyze_root_cause()
  │
  ├── 工具调用 → 返回结构化数据（Markdown + <chart>）
  │
  └── LLM 总结 → SSE 流式输出
```

### 模块分层

- **API 层** (`api/`) — 路由注册和版本管理
- **业务层** (`modules/`) — 具体的业务逻辑实现
- **共享层** (`shared/`) — 可复用的智能体、工具、中间件
- **工具层** (`shared/utils/`) — 基础设施（Redis/LLM/配置/日志）

## Docker 部署

```bash
# 在项目根目录执行
docker compose -f docker/docker-compose.yml up -d backend redis
```

后端 Dockerfile 基于 `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` 镜像构建，使用 uv 管理依赖。

### 单独构建后端镜像

```bash
cd backend
docker build -t planaskdemo-backend .
```

## 开发说明

### 代码规范

- 遵循 PEP 8 编码规范
- 使用类型提示 (Type Hints)
- 使用 FastAPI 依赖注入系统管理服务实例

### 添加新工具

1. 在 `shared/agent/tools.py` 中添加新的工具函数
2. 在 `shared/agent/tools_data.py` 中添加所需模拟数据
3. 在 `shared/agent/prompts.py` 中更新系统提示词
4. 工具会自动被 RouterAgent 发现和路由

### 日志

日志文件输出到 `logs/` 目录，请求/响应通过 Agent 中间件自动记录。
