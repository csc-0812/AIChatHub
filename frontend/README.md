# 前端应用

## 项目结构

```
frontend/
├── src/                # 源代码
│   ├── modules/        # 业务模块
│   │   ├── auth/       # 登录模块
│   │   ├── chat/       # 聊天模块
│   │   └── admin/      # 管理员模块
│   ├── utils/          # 工具类
│   ├── assets/         # 静态资源
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── public/             # 公共文件
├── dist/               # 构建输出
├── vite-plugins/       # Vite 插件
└── package.json        # 依赖配置
```

## 功能特性

- 用户登录/注册界面
- 聊天界面（支持流式响应）
- 会话管理（创建/列表/删除/重命名）
- 管理员界面（用户管理）
- 响应式设计

## 技术栈

- Vue 3 - 框架
- Vite - 构建工具
- 原生 CSS - 样式

## 快速开始

### 环境要求
- Node.js 18+

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

服务将在 http://localhost:5173 运行

### 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录

## 开发说明

### 目录结构
- `src/modules/` - 业务模块，包含不同功能的页面组件
- `src/utils/` - 工具类，包含 API 调用、配置管理等
- `src/assets/` - 静态资源，包含图片、图标等
- `vite-plugins/` - Vite 插件，包含配置加载等功能

### 组件说明
- `Auth/Login.vue` - 登录组件
- `Chat/Chat.vue` - 聊天主组件
- `Admin/Admin.vue` - 管理员组件

### API 调用

前端通过以下 API 与后端交互：
- 认证 API：`/api/v1/auth/*`
- 聊天 API：`/api/v1/chat/*`
- 管理员 API：`/api/v1/admin/*`
- 模型配置 API：`/api/v1/models/*`

## 配置

前端配置文件位于 `public/config.json`，包含 API 基础 URL 等配置项。

