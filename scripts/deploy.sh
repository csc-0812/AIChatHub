#!/bin/bash
# ============================================
# AIChatHub Docker 一键部署脚本 (Linux/Mac/WSL)
# 用法: bash scripts/deploy.sh
# ============================================
set -e

COMPOSE_FILE="docker/docker-compose.yml"
DOCKER_COMPOSE="docker compose -f $COMPOSE_FILE"

echo "============================================"
echo "  AIChatHub Docker 本地部署脚本"
echo "============================================"
echo ""

# ---------- 1. 环境检查 ----------
echo "[1/5] 检查 Docker 环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    echo "   下载地址: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null 2>&1; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "  ✓ Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1)"
echo "  ✓ Docker Compose $(docker compose version --short)"
echo ""

# ---------- 2. 环境变量 ----------
echo "[2/5] 加载环境变量..."

if [ -f .env ]; then
    set -a
    source .env
    set +a
    echo "  ✓ 已加载 .env 文件"
else
    echo "  ⚠ 未找到 .env 文件，使用 docker-compose.yml 中的默认值"
fi
echo ""

# ---------- 3. 构建镜像 ----------
echo "[3/5] 构建 Docker 镜像..."
$DOCKER_COMPOSE build --parallel
echo ""

# ---------- 4. 启动服务 ----------
echo "[4/5] 启动服务..."
$DOCKER_COMPOSE up -d
echo ""

# ---------- 5. 等待就绪 ----------
echo "[5/5] 等待服务就绪..."
sleep 3

# 健康检查
echo ""
echo "📊 服务状态:"
$DOCKER_COMPOSE ps
echo ""

# 检查后端健康
echo "🔍 检查后端健康状态..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "  ✓ 后端服务正常"
else
    echo "  ⚠ 后端服务可能尚未就绪，请稍后检查"
fi

echo ""
echo "============================================"
echo "  ✅ 部署完成!"
echo "============================================"
echo ""
echo "  前端访问:  http://localhost:${FRONTEND_PORT:-3000}"
echo "  后端 API:  http://localhost:8000"
echo "  API 文档:  http://localhost:8000/docs"
echo "  健康检查:  http://localhost:8000/health"
echo ""
echo "  常用命令:"
echo "    查看日志:    $DOCKER_COMPOSE logs -f [backend|frontend|redis]"
echo "    停止服务:    $DOCKER_COMPOSE down"
echo "    重启服务:    $DOCKER_COMPOSE restart"
echo "    重新构建:    $DOCKER_COMPOSE up -d --build"
echo "    进入后端容器: $DOCKER_COMPOSE exec backend sh"
echo ""
echo "  创建超级管理员（首次使用）:"
echo "    $DOCKER_COMPOSE exec backend uv run python scripts/make_super_admin.py"
echo ""
