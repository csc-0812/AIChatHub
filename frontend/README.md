# 前端应用

基于 **Vue 3 + Vite** 的智能聊天前端，支持流式对话、Markdown 渲染和 Chart.js 可视化图表。

## 项目结构

```
frontend/
├── src/
│   ├── modules/                # 业务模块
│   │   ├── auth/               # 登录模块
│   │   │   ├── Login.vue       # 登录/注册界面
│   │   │   ├── authApi.js      # 认证 API
│   │   │   └── useAuth.js      # 认证状态管理
│   │   ├── chat/               # 聊天模块（核心）
│   │   │   ├── Chat.vue        # 聊天主界面
│   │   │   ├── chatApi.js      # 聊天 API
│   │   │   └── useChat.js      # 聊天状态管理
│   │   └── admin/              # 管理员模块
│   │       ├── Admin.vue       # 管理员界面
│   │       ├── adminApi.js     # 管理 API
│   │       └── useAdmin.js     # 管理状态管理
│   ├── components/             # 通用组件
│   │   ├── ChartRenderer.vue   # Chart.js 图表渲染器（bar/pie/line）
│   │   ├── MarkdownRenderer.vue # Markdown 渲染器
│   │   ├── ContentRenderer.vue # 混合内容渲染器
│   │   └── ThemeToggle.vue     # 主题切换组件
│   ├── themes/                 # 主题配置
│   │   ├── theme.js            # 主题切换逻辑
│   │   └── variables.css       # CSS 变量（深色/浅色/琥珀三主题）
│   ├── utils/                  # 工具类
│   │   ├── config.js           # 配置加载器
│   │   ├── sse.js              # SSE 流式数据解析
│   │   ├── format.js           # 格式化工具
│   │   └── pdfExport.js        # PDF 导出（html2canvas + jsPDF）
│   ├── assets/                 # 静态资源
│   ├── App.vue                 # 根组件（路由切换）
│   ├── main.js                 # 入口文件
│   └── style.css               # 全局样式
├── vite-plugins/               # Vite 自定义插件
│   └── config-loader.js        # 配置文件自动加载（YAML → JSON）
├── public/
│   ├── config.json             # 前端配置（由 vite 插件自动生成）
│   ├── favicon.svg             # 站点图标
│   └── icons.svg               # SVG 图标集
├── index.html                  # HTML 入口
├── vite.config.js              # Vite 构建配置
├── nginx.conf                  # Nginx 配置（API 代理 + SSE 支持）
├── Dockerfile                  # 前端镜像构建（多阶段：Node → Nginx）
└── package.json                # 依赖配置
```

## 功能特性

### 用户界面

- **登录/注册** — 支持普通用户和管理员两种身份
- **聊天界面** — 会话列表、消息展示、流式输入、文件上传
- **流式响应** — 实时接收 SSE 事件流，支持思考过程展开/折叠
- **Markdown 渲染** — AI 回复中的 Markdown 表格、代码块、列表自动渲染
- **图表可视化** — AI 返回的 `<chart>` 标签自动解析为 Chart.js 图表（柱状图/饼图/折线图）
- **思考过程展示** — 展开查看 AI 的 `<thinking>` 推理过程
- **文件预览** — 上传的图片/文档在聊天界面直接预览
- **对话导出** — 支持对话导出为 PDF 格式
- **管理员界面** — 用户表格管理、角色编辑、禁用/启用、强制下线
- **多主题切换** — 支持深色/浅色/琥珀三款主题，CSS 变量驱动
- **响应式设计** — 适配桌面端和移动端

## 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5 | 前端框架 (Options API) |
| Vite | ^8.0 | 构建工具 + 开发服务器 |
| Chart.js | ^4.5 | 图表渲染 |
| vue-chartjs | ^5.3 | Vue 3 的 Chart.js 封装 |
| markdown-it | ^14.2 | Markdown 解析渲染 |
| html2canvas | ^1.4 | HTML 转 Canvas（PDF 导出） |
| jsPDF | ^4.2 | PDF 文档生成 |
| js-yaml | ^4.1 | YAML 配置解析（vite 插件用） |
| 原生 CSS | — | 样式方案（三主题 CSS 变量） |

## 快速开始

### 环境要求

- Node.js 18+

### 1. 配置

前端配置由 Vite 插件 `vite-plugins/config-loader.js` 在开发/构建时从项目根目录的 `config/config.yaml` 自动生成，写入 `public/config.json`。生成后内容如下：

```json
{
  "api_base_url": "/api/v1",
  "app_name": "PlanAskDemo"
}
```

- `api_base_url` — 后端 API 基础路径。开发时指向 `http://localhost:8000/api/v1`，Docker 部署时通过 Nginx 代理为 `/api/v1`
- `app_name` — 应用名称，显示在页面标题中

> 如需修改默认配置，编辑项目根目录的 `config/config.yaml` 中 `frontend` 和 `app` 字段即可。

### 2. 安装依赖

```bash
npm install
```

### 3. 启动开发服务器

```bash
npm run dev
```

服务运行在 http://localhost:5174

### 4. 构建生产版本

```bash
npm run build
```

构建产物输出到 `dist/` 目录，可直接部署到静态服务器或 Nginx。

### 5. 预览构建产物

```bash
npm run preview
```

## 组件说明

### 核心组件

| 组件 | 路径 | 说明 |
|------|------|------|
| `Chat.vue` | `src/modules/chat/` | 聊天主界面：会话切换、消息列表、输入发送 |
| `ChartRenderer.vue` | `src/components/` | 解析 AI 返回的 `<chart>` 标签，渲染为交互式图表 |
| `MarkdownRenderer.vue` | `src/components/` | 将 Markdown 文本渲染为 HTML，支持表格/代码/列表 |
| `ContentRenderer.vue` | `src/components/` | 混合内容渲染器，协调 Markdown + Chart 的渲染顺序 |
| `ThemeToggle.vue` | `src/components/` | 主题切换按钮，支持深色/浅色/琥珀三主题 |
| `Admin.vue` | `src/modules/admin/` | 用户管理表格，支持搜索、分页、角色编辑 |
| `Login.vue` | `src/modules/auth/` | 登录/注册表单，支持切换模式 |

### SSE 流式处理

`src/utils/sse.js` 负责解析后端推送的 SSE 事件流：

```
事件类型:
  - thinking    → AI 思考过程文本
  - token       → AI 回复的 token 片段
  - done        → 流式回复结束
  - error       → 错误信息
```

前端实时累加 token 文本，解析其中的 Markdown 和 `<chart>` 标签，动态渲染到界面。

## API 调用

前端通过各模块的 `*Api.js` 文件与后端 API 交互：

```
authApi.js   → /api/v1/auth/*     (登录/注册/用户信息)
chatApi.js   → /api/v1/chat/*     (会话管理/流式聊天/文件上传)
adminApi.js  → /api/v1/admin/*    (用户管理)
```

请求自动携带 JWT Token，401 时自动跳转登录页。

## Docker 部署

前端采用多阶段 Docker 构建：
- **构建阶段**：基于 `node:22-alpine`，通过 Vite 构建生产包
- **运行阶段**：基于 `nginx:alpine`，使用 `nginx.conf` 配置反向代理和 SSE 支持

```bash
# 只启动前端
docker compose -f docker/docker-compose.yml up -d frontend

# 一键启动全部服务
bash scripts/deploy.sh
```

### 单独构建前端镜像

```bash
cd frontend
docker build -t planaskdemo-frontend .
```

## 开发说明

### 目录约定

- `src/modules/` — 业务模块，每个模块内部包含 `.vue` 组件、API 封装和 composable 状态管理
- `src/components/` — 跨模块复用的通用组件
- `src/utils/` — 纯工具函数，不依赖 Vue 响应式系统
- `src/themes/` — 主题定义（`theme.js` 为切换逻辑，`variables.css` 为 CSS 变量）
- `vite-plugins/` — Vite 自定义插件（配置加载器等）

### 配置自动加载

`vite-plugins/config-loader.js` 在 Vite 开发/构建时读取 `config/config.yaml`，提取 `frontend` 和 `app` 节点自动生成 `public/config.json`，前端运行时通过 `src/utils/config.js` 加载使用。

### 添加新图表类型

在 `ChartRenderer.vue` 中扩展 `renderChart()` 方法，支持新的 `chartType`：

```javascript
// 当前支持: bar, pie, line
// 扩展时添加对应的 Chart.js 配置即可
```

### 添加新主题

1. 在 `src/themes/variables.css` 中新增主题 CSS 变量块
2. 在 `src/themes/theme.js` 中注册新主题名称
