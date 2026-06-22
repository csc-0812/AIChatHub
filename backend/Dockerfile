# ============================================
# AIChatHub Backend Dockerfile
# FastAPI + LangGraph + Redis
# 构建上下文: 项目根目录
# ============================================

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

# 将包安装到系统 Python 环境（非虚拟环境）
ENV UV_SYSTEM_PYTHON=1

# 先复制依赖文件，利用 Docker 缓存层
COPY backend/pyproject.toml backend/uv.lock ./

# 安装 Python 依赖
RUN uv sync --frozen

# 复制后端源码
COPY backend/ .

# 复制全局配置到镜像内
COPY config/config.yaml /app/config/config.yaml

# 创建上传文件目录
RUN mkdir -p uploads/documents uploads/images

EXPOSE 8000

# 启动 FastAPI 服务
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
