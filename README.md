# AIChatHub

一个基于 FastAPI + Vue 3 的智能聊天应用，支持会话管理、流式响应、智能体协作、管理员功能和模型配置。

## 项目结构

```
AIChatHub/
├── backend/              # 后端代码 (FastAPI)
│   ├── api/             # API 路由层
│   │   └── v1/          # API 版本 v1
│   ├── modules/         # 业务模块
│   │   ├── auth/        # 认证模块
│   │   ├── chat/        # 聊天模块
│   │   ├── admin/       # 管理员模块
│   │   └── models_config/ # 模型配置模块
│   ├── shared/          # 共享组件
│   │   ├── agent/       # 智能体模块
│   │   └── utils/       # 工具类
│   ├── uploads/         # 上传文件目录
│   ├── logs/            # 日志目录
│   ├── scripts/         # 脚本目录
│   ├── main.py          # 应用入口
│   └── pyproject.toml   # 依赖配置
├── frontend/            # 前端代码 (Vue 3)
│   ├── src/
│   │   ├── modules/     # 业务模块
│   │   │   ├── auth/    # 登录模块
│   │   │   ├── chat/    # 聊天模块
│   │   │   └── admin/   # 管理员模块
│   │   ├── utils/       # 工具类
│   │   ├── assets/      # 静态资源
│   │   ├── App.vue      # 根组件
│   │   └── main.js      # 入口文件
│   ├── public/          # 公共文件
│   ├── dist/            # 构建输出
│   └── package.json     # 依赖配置
└── config/              # 配置文件
    └── config.yaml      # 应用配置
```

## 功能特性

### 已实现功能

- [x] 用户认证（注册/登录/JWT）
- [x] 会话管理（创建/列表/删除/重命名/清空）
- [x] 流式聊天（SSE）
- [x] 思考过程展示
- [x] 上下文记忆（可配置长度）
- [x] 智能体架构（支持扩展多角色协作）
- [x] 管理员功能（用户管理）
- [x] 模型配置管理
- [x] 文件上传功能

### 技术栈

**后端**

- FastAPI - Web 框架
- Redis - 数据存储
- LangChain - LLM 集成
- JWT - 身份认证
- Pydantic - 数据验证
- PyYAML - 配置管理

**前端**

- Vue 3 - 框架
- Vite - 构建工具
- 原生 CSS - 样式

## 快速开始

### 环境要求

- Python 3.14+
- Node.js 18+
- Redis 服务器

### 1. 克隆项目

```bash
git clone <repository-url>
cd AIChatHub
```

### 2. 配置

编辑 `config/config.yaml`：

```yaml
llm:
  openai:
    api_key: "your-api-key"
    base_url: "https://api.openai.com/v1"  # 可选，用于第三方 API
    model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 2048

backend:
  database:
    host: "localhost"
    port: 6379
    password: null
  auth:
    secret_key: "your-secret-key"
```

### 3. 启动后端

```bash
cd backend

# 使用 uv 安装依赖
uv sync

# 启动服务
uv run uvicorn main:app --reload
```

后端服务将在 <http://localhost:8000> 运行

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务将在 <http://localhost:5173> 运行

## API 文档

启动后端后访问：

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### 主要接口

**认证**

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户

**聊天**

- `POST /api/v1/chat/sessions` - 创建会话
- `GET /api/v1/chat/sessions` - 获取会话列表
- `GET /api/v1/chat/sessions/{id}` - 获取会话详情
- `DELETE /api/v1/chat/sessions/{id}` - 删除会话
- `PUT /api/v1/chat/sessions/{id}/rename` - 重命名会话
- `POST /api/v1/chat/sessions/{id}/clear` - 清空会话
- `POST /api/v1/chat/stream` - 流式聊天

**管理员**

- `GET /api/v1/admin/users` - 获取用户列表
- `PUT /api/v1/admin/users/{id}` - 更新用户信息
- `DELETE /api/v1/admin/users/{id}` - 删除用户

**模型配置**

- `GET /api/v1/models` - 获取模型列表
- `POST /api/v1/models` - 创建模型配置
- `PUT /api/v1/models/{id}` - 更新模型配置
- `DELETE /api/v1/models/{id}` - 删除模型配置

## 架构说明

### 智能体架构

项目采用智能体（Agent）架构处理消息，位于 `shared/agent/`：

- `TeamAgent` - 团队智能体，管理多个智能体
- `BaseAgent` - 基础智能体，处理单轮对话
- `AgentRole` - 智能体角色枚举（协调者、研究者、分析者等）

当前每个会话默认创建一个协调者智能体，后续可扩展为：

- 多智能体协作
- 角色专业化（研究、分析、写作等）
- 工作流编排（顺序、并行、共识）

### 数据流

```
用户消息 -> Chat Router -> Chat Service -> TeamAgent -> LLM
                |              |              |
                v              v              v
            Session      TeamAgent       Response
            Manager      Instance        Stream
```

## 开发计划

- [ ] 多智能体协作模式
- [ ] 工具调用（搜索、计算等）
- [ ] 文件上传/知识库
- [ ] 对话导出
- [ ] Docker 部署
- [ ] 多语言支持
- [ ] 主题定制

## 许可证

MI
