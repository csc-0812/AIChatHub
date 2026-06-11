# ============================================
# AIChatHub Frontend Dockerfile
# Vue 3 + Vite 构建 → Nginx 静态服务
# ============================================

# ---- 构建阶段 ----
FROM node:22-alpine AS build

WORKDIR /app

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制前端源码
COPY frontend/ .

# 复制全局配置文件（Vite 插件构建时需要 ../config/config.yaml）
COPY config/ ../config/

# 构建生产版本
RUN npm run build


# ---- 运行阶段 ----
FROM nginx:alpine

# 复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 复制 Nginx 配置
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
