# AIChatHub

基于 **FastAPI + Vue 3** 的智能聊天应用，面向制造业「计划一体化平台」场景，提供数据查询、报表生成、结果推演和根因分析的 AI 助手能力。支持会话管理、流式响应、LangGraph 智能体协作、管理员功能和模型动态配置。

## 业务场景

本项目模拟一个拥有 5 条产线、5 类产品、多种物料和 5 个管理部门的制造场景，AI 智能体可通过自然语言回答以下典型问题：

- **计划报表**：产能分析、进度跟踪、物料需求、质量分析等
- **结果推演**：产能调整、订单插单、物料延迟、资源调配的 What-if 分析
- **根因分析**：工期延误、产能瓶颈、物料短缺、质量波动的根因下钻

返回结果包含 Markdown 表格和 Chart.js 可视化图表，前端自动渲染。

> 更多测试用例请参考 [docs/test-questions.md](docs/test-questions.md)。

## 项目结构

```
AIChatHub/
├── backend/                    # 后端代码 (FastAPI + LangGraph)
│   ├── api/v1/                 # API v1 路由聚合
│   ├── modules/                # 业务模块
│   │   ├── auth/               # 认证模块
│   │   ├── chat/               # 聊天模块（会话 + 流式）
│   │   ├── admin/              # 管理员模块
│   │   └── models_config/      # 模型配置模块
│   ├── shared/
│   │   ├── agent/              # LangGraph 智能体核心
│   │   │   ├── router_agent.py # RouterAgent（三工具路由）
│   │   │   ├── tools.py        # 报表/推演/根因三大工具
│   │   │   └── tools_data.py   # 模拟制造数据
│   │   └── utils/              # 工具类（Redis/JWT/LLM/配置）
│   ├── scripts/                # 维护脚本
│   ├── main.py                 # FastAPI 入口
│   └── pyproject.toml          # Python 依赖（uv 管理）
├── frontend/                   # 前端代码 (Vue 3 + Vite)
│   ├── src/
│   │   ├── modules/            # 业务模块
│   │   │   ├── auth/           # 登录注册
│   │   │   ├── chat/           # 聊天界面（核心）
│   │   │   └── admin/          # 管理员界面
│   │   ├── components/         # 通用组件
│   │   │   ├── ChartRenderer.vue      # Chart.js 图表渲染
│   │   │   ├── MarkdownRenderer.vue   # Markdown 渲染
│   │   │   └── ContentRenderer.vue    # 混合内容渲染
│   │   ├── utils/              # 工具（SSE/配置/格式化）
│   │   ├── App.vue             # 根组件
│   │   └── main.js             # 入口
│   ├── public/config.json      # 前端配置
│   └── package.json            # 依赖配置
├── config/
│   └── config.yaml             # 全局配置（LLM/Redis/JWT）
├── docker/
│   └── docker-compose.yml      # Docker Compose 编排配置
├── scripts/
│   ├── deploy.sh               # 一键部署脚本 (Linux/Mac/WSL)
│   └── deploy.ps1              # 一键部署脚本 (Windows)
└── docs/
    └── test-questions.md       # 测试问题集
```

## 功能特性

### 核心功能

- [x] **用户认证** — 注册 / 登录 / JWT Token，支持角色（user / admin / super_admin）和挤出登录
- [x] **会话管理** — 创建 / 列表 / 删除 / 重命名 / 清空消息
- [x] **流式聊天** — SSE 实时流式输出，支持 `<thinking>` 思考过程展示
- [x] **AI 智能体** — LangGraph RouterAgent，自动路由到报表生成 / 结果推演 / 根因分析三大工具
- [x] **可视化图表** — AI 返回内嵌 `<chart>` 标签，前端通过 Chart.js 渲染柱状图/饼图/折线图
- [x] **Markdown 渲染** — AI 回复支持 Markdown 格式，自动前端的格式化和展示
- [x] **上下文记忆** — 可配置上下文窗口长度
- [x] **文件上传** — 支持图片和文档上传
- [x] **管理员功能** — 用户列表 / 角色编辑 / 禁用启用 / 强制下线
- [x] **模型配置** — 动态配置多个 LLM 模型，运行时切换无需重启

## 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| FastAPI | Web 框架，自动生成 OpenAPI 文档 |
| LangChain + LangGraph | LLM 集成 + Agent 状态图编排 |
| Redis | 用户/会话/消息存储 |
| JWT (python-jose) | 身份认证 |
| Pydantic | 数据验证 |
| PyYAML | 配置管理 |
| uv | Python 包管理器 |

### 前端

| 技术 | 用途 |
|------|------|
| Vue 3 | 前端框架 (Options API) |
| Vite | 构建工具 |
| Chart.js + vue-chartjs | 图表渲染（柱状图/饼图/折线图） |
| markdown-it | Markdown 渲染 |
| 原生 CSS | 样式（暗色主题） |

## 快速开始

### 方式一：Docker 一键部署（推荐）

无需安装 Python/Node/Redis，只需 Docker 即可启动全部服务。

```bash
# Windows
.\scripts\deploy.ps1

# Linux / Mac / WSL
bash scripts/deploy.sh
```

部署完成后：

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:3000 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

```bash
# 创建超级管理员（首次使用）
docker compose -f docker/docker-compose.yml exec backend uv run python scripts/make_super_admin.py

# 常用命令
docker compose -f docker/docker-compose.yml logs -f     # 查看日志
docker compose -f docker/docker-compose.yml down         # 停止服务
docker compose -f docker/docker-compose.yml up -d --build  # 重新构建
```

> 模型配置在系统内通过管理面板动态配置，无需在部署时设置 API Key。如需自定义前端端口，创建 `.env` 文件写入 `FRONTEND_PORT=8080` 即可。

### 方式二：本地开发启动

#### 环境要求

- Python 3.12+
- Node.js 18+
- Redis 服务器

#### 1. 克隆项目

```bash
git clone <repository-url>
cd AIChatHub
```

#### 2. 配置

编辑 `config/config.yaml`：

```yaml
llm:
  openai:
    api_key: "your-api-key"            # 或设置环境变量 OPENAI_API_KEY
    base_url: "https://api.openai.com/v1"
    model: "gpt-3.5-turbo"
    temperature: 0.2
    max_tokens: 2048

backend:
  database:
    host: "localhost"
    port: 6379
    password: null
  auth:
    secret_key: "your-secret-key"      # 或设置环境变量 JWT_SECRET_KEY
```

> 支持通过环境变量覆盖配置：`OPENAI_API_KEY`、`JWT_SECRET_KEY`、`REDIS_HOST`、`REDIS_PORT`。

#### 3. 启动后端

```bash
cd backend

# 安装依赖
uv sync

# 启动服务
uv run uvicorn main:app --reload
```

后端服务：http://localhost:8000  
API 文档：http://localhost:8000/docs

#### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务：http://localhost:5173

#### 5. 创建超级管理员（可选）

```bash
cd backend
uv run python scripts/make_super_admin.py
```

## API 文档

启动后端后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | `POST` | `/api/v1/auth/register` | 用户注册 |
| 认证 | `POST` | `/api/v1/auth/login` | 用户登录 |
| 认证 | `GET` | `/api/v1/auth/me` | 获取当前用户 |
| 聊天 | `POST` | `/api/v1/chat/sessions` | 创建会话 |
| 聊天 | `GET` | `/api/v1/chat/sessions` | 会话列表 |
| 聊天 | `GET` | `/api/v1/chat/sessions/{id}` | 会话详情 |
| 聊天 | `DELETE` | `/api/v1/chat/sessions/{id}` | 删除会话 |
| 聊天 | `PUT` | `/api/v1/chat/sessions/{id}/rename` | 重命名会话 |
| 聊天 | `POST` | `/api/v1/chat/sessions/{id}/clear` | 清空消息 |
| 聊天 | `POST` | `/api/v1/chat/stream` | 流式聊天 (SSE) |
| 管理员 | `GET` | `/api/v1/admin/users` | 用户列表 |
| 管理员 | `PUT` | `/api/v1/admin/users/{id}` | 更新用户 |
| 管理员 | `DELETE` | `/api/v1/admin/users/{id}` | 删除用户 |
| 模型 | `GET` | `/api/v1/models` | 模型列表 |
| 模型 | `POST` | `/api/v1/models` | 创建模型配置 |
| 模型 | `PUT` | `/api/v1/models/{id}` | 更新模型配置 |
| 模型 | `DELETE` | `/api/v1/models/{id}` | 删除模型配置 |

## 架构说明

### 智能体架构

项目采用 **LangGraph RouterAgent** 处理用户消息，位于 `backend/shared/agent/`：

- **RouterAgent** — 基于 LangGraph 的智能路由 Agent，根据用户意图自动选择工具
- **三大工具**：
  - `generate_plan_report` — 报表生成（产能/物料/进度/质量分析）
  - `simulate_plan_scenario` — 结果推演（产能调整/插单/物料延迟/资源调配）
  - `analyze_root_cause` — 根因分析（延误/瓶颈/短缺/波动/超预算的下钻分析）
- **BaseAgent** — 基础智能体，处理单轮对话和流式输出
- **AgentRole** — 角色枚举（协调者、研究者、分析者等）

### 数据流

```
用户消息 → Chat Router → Chat Service → RouterAgent (LangGraph)
          │              │               │
          v              v               v
      Session        TeamAgent      工具调用 → LLM 生成
      Manager        Instance       报表/推演/根因
          │                           │
          │              ┌────────────┘
          v              v
      SSE 响应 ← Markdown 文本 + <chart> 图表数据
          │
          v
      前端渲染: MarkdownRenderer + ChartRenderer
```

## Docker 部署

项目已内置完整的 Docker 部署方案，包含 Redis + 后端 + 前端三个服务，Nginx 反向代理统一入口。

```
浏览器 → localhost:3000 (Nginx)
              ├── /           → Vue 静态页面
              ├── /api/*      → 代理到 backend:8000
              └── /uploads/*  → 代理到 backend:8000
```

### 一键部署

```bash
# Windows
.\scripts\deploy.ps1

# Linux / Mac / WSL
bash scripts/deploy.sh
```

### 手动部署

```bash
# 构建并启动
docker compose -f docker/docker-compose.yml up -d --build

# 查看状态
docker compose -f docker/docker-compose.yml ps

# 停止服务
docker compose -f docker/docker-compose.yml down
```

### 文件说明

| 文件 | 作用 |
|------|------|
| `docker/docker-compose.yml` | 服务编排配置 |
| `backend/Dockerfile` | 后端镜像（Python 3.13 + uv） |
| `frontend/Dockerfile` | 前端镜像（Node 构建 → Nginx 运行） |
| `frontend/nginx.conf` | Nginx 配置（API 代理 + SSE 支持） |
| `scripts/deploy.sh` | Linux/Mac/WSL 一键部署 |
| `scripts/deploy.ps1` | Windows 一键部署 |

## 开发计划

- [x] 用户认证与会话管理
- [x] 流式聊天与思考过程展示
- [x] LangGraph 智能体与工具调用
- [x] 可视化图表渲染
- [x] 文件上传
- [x] 管理员功能
- [x] 模型动态配置
- [ ] 多智能体协作模式
- [ ] 知识库/RAG 检索增强
- [ ] 对话导出 (PDF/Markdown)
- [ ] 多语言支持
- [ ] 主题定制（亮色/暗色切换）

## 许可证

MIT
